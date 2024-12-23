import re
import sys

import apiaccess
import constants

from translation import KRtoEN, ENtoKR

import os
import time

Debugmode = False


class AmbiguousAnswerException(Exception):
    pass


def export_to_client(text):
    text = ENtoKR(text)
    current_dir = 'E:/Epic Games/Unreal Projects/chatting_AI'
    file_path = current_dir + '/bot.txt'

    try:
        with open(file_path, 'w', encoding='utf-8') as file:  # 쓰기 모드로 파일 열기
            file.write(text)
        print(f"'{file_path}' 파일이 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"파일 생성 중 오류가 발생했습니다: {e}")


def import_from_client():
    current_dir = 'E:/Epic Games/Unreal Projects/chatting_AI'
    file_path = current_dir + '/client.txt'
    while(True):
        if os.path.exists(file_path):
            #print(f"'{file_path}' 파일이 존재합니다.")
            # 파일 내용 읽기
            try:
                with open(file_path, "r", encoding='utf-16-le') as file:# 파일 열기
                    content = file.read()  # 파일 내용 읽기
            except Exception as e:
                print(f"파일을 읽는 중 오류가 발생했습니다: {e}")
            print("파일 내용:")
            #print(content)  # 출력
            os.remove(file_path)
            return content
        #else: print(print(f"'{file_path}' 파일이 존재하지 않습니다."))
        time.sleep(0.5)



def read_input(prompt):
    """Displays appropriate prompt and reads the input.

    Args:
        prompt (str): String to be displayed.

    Returns:
        str: Stripped users input.

    """
    if prompt.endswith('?'):
        prompt = prompt + ' '
    else:
        prompt = prompt + ': '


    print(ENtoKR(prompt), end='', flush=True)   #챗봇의 질문들을 한국어로 번역
    return sys.stdin.readline().strip()


def read_age_sex():
    """Reads age and sex specification such as "30 male".

    This is very crude. This is because reading answers to simple questions is
    not the main scope of this example. In real chatbots, either use some real
    intent+slot recogniser such as snips_nlu, or at least write a number of
    regular expressions to capture most typical patterns for a given language.
    Also, age below 12 should be rejected as our current knowledge doesn't
    support paediatrics (it's being developed but not delivered yet).

    Returns:
        int, str: Age and sex.

    """
    export_to_client("Patient age and sex (e.g., 30 male)")             # 봇 to 클라이언트
    if Debugmode == True:
        answer = read_input("Patient age and sex (e.g., 30 male)")  # 기존 시스템 직접 입력
    else:
        answer = import_from_client()                                       # 클라이언트 to 봇

    try:
        age = int(extract_age(answer))
        sex = extract_sex(answer, constants.SEX_NORM)
        if age < constants.MIN_AGE:
            export_to_client("Ages below 12 are not yet supported.")    # 봇 to 클라이언트
            raise ValueError("Ages below 12 are not yet supported.")
        if age > constants.MAX_AGE:
            export_to_client("Maximum possible age is 130.")            # 봇 to 클라이언트
            raise ValueError("Maximum possible age is 130.")
    except (AmbiguousAnswerException, ValueError) as e:
        print("{} Please repeat.".format(e))
        export_to_client("{} Please repeat.".format(e))                 # 봇 to 클라이언트
        return read_age_sex()
    return age, sex


def read_complaint_portion(age, sex, auth_string, case_id, context, language_model=None):
    """Reads user input and calls the /parse endpoint of Infermedica API to
    extract conditions found in text.

    Args:
        age (dict): Patients age in {'value': int, 'unit': str} format.
        sex (str): Patients sex.
        auth_string (str): Authentication string.
        case_id (str): Case ID.
        context (list): List previous complaints.
        language_model (str): Chosen language model.

    Returns:
        dict: Response from /parse endpoint.

    """
    export_to_client('Describe your complaints')
    if Debugmode == True:
        text = read_input('Describe your complaints')  # 기존 시스템 입력
    else:
        text = import_from_client()  # 사용자의 불만 사항을 받는 곳

    if(text != ""):
        text = KRtoEN(text)                 # 입력받는 한국어를 영어로 번역

    if not text:
        return None
    resp = apiaccess.call_parse(age, sex, text, auth_string, case_id, context,
                                language_model=language_model)
    return resp.get('mentions', [])


def mention_as_text(mention):
    """Represents the given mention structure as simple textual summary.

    Args:
        mention (dict): Response containing information about medical concept.

    Returns:
        str: Formatted name of the reported medical concept, e.g. +Dizziness,
            -Headache.

    """
    _modality_symbol = {"present": "+", "absent": "-", "unknown": "?"}
    name = mention["name"]
    symbol = _modality_symbol[mention["choice_id"]]
    return "{}{}".format(symbol, name)


def context_from_mentions(mentions):
    """Returns IDs of medical concepts that are present."""
    return [m['id'] for m in mentions if m['choice_id'] == 'present']


def summarise_mentions(mentions):
    """Prints noted mentions."""
    print("Noting: {}".format(", ".join(mention_as_text(m) for m in mentions)))


def read_complaints(age, sex, auth_string, case_id, language_model=None):
    """Keeps reading complaint-describing messages from user until empty
    message is read (or just read the story if given). Will call the /parse
    endpoint and return mentions captured there.

    Args:
        age (dict): Patients age in {'value': int, 'unit': str} format.
        sex (str): Patients sex.
        auth_string (str): Authentication string.
        case_id (str): Case ID.
        lanugage_model (str): Chosen language model.

    Returns:
        list: Mentions extracted from user answers.

    """
    mentions = []
    context = []  # List of ids of present symptoms in the order of reporting.
    while True:
        portion = read_complaint_portion(age, sex, auth_string, case_id, context,
                                         language_model=language_model)
        if portion:
            summarise_mentions(portion)
            mentions.extend(portion)
            # Remember the mentions understood as context for next /parse calls
            context.extend(context_from_mentions(portion))
        if mentions and portion is None:
            # User said there's nothing more but we've already got at least one
            # complaint.
            return mentions


def read_single_question_answer(question_text):
    """Primitive implementation of understanding user's answer to a
    single-choice question. Prompt the user with question text, read user's
    input and convert it to one of the expected evidence statuses: present,
    absent or unknown. Return None if no answer provided."""

    export_to_client(question_text)     # 봇 to 클라이언트
    if Debugmode == True:
        answer = read_input(question_text)
    else:
        answer = import_from_client()       # 클라이언트 to 봇

    answer = KRtoEN(answer)
    if not answer:
        return None

    try:
        return extract_decision(answer, constants.ANSWER_NORM)
    except (AmbiguousAnswerException, ValueError) as e:
        print("{} Please repeat.".format(e))
        export_to_client("{} Please repeat.".format(e))
        return read_single_question_answer(question_text)


def conduct_interview(evidence, age, sex, case_id, auth, language_model=None):
    """Keep asking questions until API tells us to stop or the user gives an
    empty answer."""
    while True:
        resp = apiaccess.call_diagnosis(evidence, age, sex, case_id, auth,
                                        language_model=language_model)
        question_struct = resp['question']
        diagnoses = resp['conditions']
        should_stop_now = resp['should_stop']
        if should_stop_now:
            # Triage recommendation must be obtained from a separate endpoint,
            # call it now and return all the information together.
            triage_resp = apiaccess.call_triage(evidence, age, sex, case_id,
                                                auth,
                                                language_model=language_model)
            return evidence, diagnoses, triage_resp
        new_evidence = []
        if question_struct['type'] == 'single':
            # If you're calling /diagnosis in "disable_groups" mode, you'll
            # only get "single" questions. These are simple questions that
            # require a simple answer -- whether the observation being asked
            # for is present, absent or unknown.
            question_items = question_struct['items']
            assert len(question_items) == 1  # this is a single question
            question_item = question_items[0]
            observation_value = read_single_question_answer(
                question_text=question_struct['text'])
            if observation_value is not None:
                new_evidence.extend(apiaccess.question_answer_to_evidence(
                    question_item, observation_value))
        else:
            # You'd need a rich UI to handle group questions gracefully.
            # There are two types of group questions: "group_single" (radio
            # buttons) and "group_multiple" (a bunch of single questions
            # gathered under one caption). Actually you can try asking
            # sequentially for each question item from "group_multiple"
            # question and then adding the evidence coming from all these
            # answers. For "group_single" there should be only one present
            # answer. It's recommended to include only this chosen answer as
            # present symptom in the new evidence. For more details, please
            # consult:
            # https://developer.infermedica.com/docs/diagnosis#group_single
            raise NotImplementedError("Group questions not handled in this"
                                      "example")
        # Important: always update the evidence gathered so far with the new
        # answers
        evidence.extend(new_evidence)


def summarise_some_evidence(evidence, header):
    print(header + ':')
    for idx, piece in enumerate(evidence):
        print('{:2}. {}'.format(idx + 1, ENtoKR(mention_as_text(piece))))
    print()


def summarise_all_evidence(evidence):
    reported = []
    answered = []
    for piece in evidence:
        (reported if piece.get('initial') else answered).append(piece)
    summarise_some_evidence(reported, '불만 내용')
    summarise_some_evidence(answered, '증상 내용')


def summarise_diagnoses(diagnoses):
    print('진단 결과:')
    result = ""
    for idx, diag in enumerate(diagnoses):
        print('{:2}. {:.2f} {}'.format(idx + 1, diag['probability'],
                                       ENtoKR(diag['name'])))
        result +=f"{idx + 1}. {diag['probability']}  {ENtoKR(diag['name'])} \n"
    export_to_client(result)
    print()


def summarise_triage(triage_resp):
    print('Triage level: {}'.format(triage_resp['triage_level']))
    teleconsultation_applicable = triage_resp.get(
        'teleconsultation_applicable')
    if teleconsultation_applicable is not None:
        print('Teleconsultation applicable: {}'
              .format(teleconsultation_applicable))
    print()


def extract_keywords(text, keywords):
    """Extracts keywords from text.

    Args:
        text (str): Text from which the keywords will be extracted.
        keywords (list): Keywords to look for.

    Returns:
        list: All keywords found in text.

    """
    # Construct an alternative regex pattern for each keyword (speeds up the
    # search). Note that keywords must me escaped as they could potentialy
    # contain regex-specific symbols, e.g. ?, *.
    pattern = r"|".join(r"\b{}\b".format(re.escape(keyword))
                        for keyword in keywords)
    mentions_regex = re.compile(pattern, flags=re.I)
    return mentions_regex.findall(text)


def extract_decision(text, mapping):
    """Extracts decision keywords from text.

    Args:
        text (str): Text from which the keywords will be extracted.
        mapping (dict): Mapping from keyword to decision.

    Returns:
        str: Single decision (one of `mapping` values).

    Raises:
        AmbiguousAnswerException: If `text` contains keywords mapping to two
            or more different distinct decision.
        ValueError: If no keywords can be found in `text`.

    """
    decision_keywrods = set(extract_keywords(text, mapping.keys()))
    if len(decision_keywrods) == 1:
        return mapping[decision_keywrods.pop().lower()]
    elif len(decision_keywrods) > 1:
        raise AmbiguousAnswerException("The decision seemed ambiguous.")
    else:
        raise ValueError("No decision found.")


def extract_sex(text, mapping):
    """Extracts sex keywords from text.

    Args:
        text (str): Text from which the keywords will be extracted.
        mapping (dict): Mapping from keyword to sex.

    Returns:
        str: Single decision (one of `mapping` values).

    Raises:
        AmbiguousAnswerException: If `text` contains keywords mapping to two
            or more different distinct sexes.
        ValueError: If no keywords can be found in `text`.

    """
    sex_keywords = set(extract_keywords(text, mapping.keys()))
    if len(sex_keywords) == 1:
        return mapping[sex_keywords.pop().lower()]
    elif len(sex_keywords) > 1:
        raise AmbiguousAnswerException("I understood multiple sexes.")
    else:
        raise ValueError("No sex found.")


def extract_age(text):
    """Extracts age from text.

    Args:
        text (str): Text from which the keywords will be extracted.

    Returns:
        str: Found number (as a string).

    Raises:
        AmbiguousAnswerException: If `text` contains two or more numbers.
        ValueError: If no numbers can be found in `text`.

    """
    ages = set(re.findall(r"\b\d+\b", text))
    if len(ages) == 1:
        return ages.pop()
    elif len(ages) > 1:
        raise AmbiguousAnswerException("I understood multiple ages.")
    else:
        raise ValueError("No age found.")
