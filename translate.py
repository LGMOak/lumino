# new dependency; pip install deep-translator
# documentation: https://pypi.org/project/deep-translator/
# many options for translating, Google Translate currently used.
from deep_translator import GoogleTranslator


def translate(source='auto', target='en', text=''):
    '''Translates text using Google Translator.
    
    Parameters:
        source (str): Source language (default is auto-detect).
        target (str): Target language (default is English).
        text (str): Text to be translated.
    
    Returns:
        str: Translated text.
    '''
    return GoogleTranslator(source=source, target=target).translate(text)