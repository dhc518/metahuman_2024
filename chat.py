import argparse
import uuid

import conversation
import apiaccess


APP_ID = ""
APP_KEY = ""




def get_auth_string():
    """Retrieves authentication string from user input during runtime.

    Returns:
        str: Authentication string in the form "APP_ID:APP_KEY".

    """
    print("Please enter your Infermedica API credentials.")
    # app_id = input("Enter APP_ID: ")
    # app_key = input("Enter APP_KEY: ")
    app_id = APP_ID
    app_key = APP_KEY
    return f"{app_id}:{app_key}"


def new_case_id():
    """Generates an identifier unique to a new session.

    Returns:
        str: Unique identifier in hexadecimal form.

    """
    return uuid.uuid4().hex


def parse_args():
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Namespace containing one optional attribute:
            1. model (str) - chosen language model.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",
                        help="use non-standard Infermedica model/language, "
                             "e.g. infermedica-es")
    args = parser.parse_args()
    return args


def run():
    """Runs the main application."""
    args = parse_args()

    # Obtain the authentication string during runtime
    auth_string = get_auth_string()
    case_id = new_case_id()

    # Read patient's age and sex; required by /diagnosis endpoint.
    # Alternatively, this could be done after learning patient's complaints
    age, sex = conversation.read_age_sex()
    print(f"Ok, {age} year old {sex}.")
    age = {'value': age, 'unit': 'year'}

    # Query for all observation names and store them.
    naming = apiaccess.get_observation_names(age, auth_string, case_id, args.model)

    # Read patient's complaints by using /parse endpoint.
    mentions = conversation.read_complaints(age, sex, auth_string, case_id, args.model)

    # Keep asking diagnostic questions until stop condition is met
    evidence = apiaccess.mentions_to_evidence(mentions)
    evidence, diagnoses, triage = conversation.conduct_interview(evidence, age,
                                                                 sex, case_id,
                                                                 auth_string,
                                                                 args.model)

    # Add `name` field to each piece of evidence to get a human-readable summary.
    apiaccess.name_evidence(evidence, naming)

    # Print out all that we've learnt about the case and finish.
    print()
    conversation.summarise_all_evidence(evidence)
    conversation.summarise_diagnoses(diagnoses)
    conversation.summarise_triage(triage)


if __name__ == "__main__":
    run()
