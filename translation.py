from googletrans import Translator

translator = Translator()

def ENtoKR(txt):
    result = translator.translate(txt, dest='ko',src='en')
    return result.text




def KRtoEN(txt):
    result = translator.translate(txt, dest='en',src='ko')
    return result.text