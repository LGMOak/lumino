# new dependency; pip install deep-translator
# documentation: https://pypi.org/project/deep-translator/
# many options for translating, Google Translate currently used.
from deep_translator import GoogleTranslator
from deepl import Translator

#get api key from environment variable
import os
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

# Choose model. Google Translate for development, DeepL for final.
model = 'google'
# model = 'deepl'

def __googletranslate(source='auto', target='en', text=''):
    # https://pypi.org/project/deep-translator/#google-translate-1
    return GoogleTranslator(source=source, target=target).translate(text)


def __deeptranslate(source=None, target='en-us', text='', context=None, split_sentences=0, preserve_formatting=False, formality='prefer_less',glossary_id=None):
    # https://developers.deepl.com/docs/api-reference/translate
    # possible glossary implementation
    if DEEPL_API_KEY is not None:
        translator = Translator(auth_key=DEEPL_API_KEY)
    else:
        raise ValueError(f"No API key set. \n Please set your DeepL API key in your environment config as the 'DEEPL_API_KEY' variable")

    return translator.translate_text(source_lang=source,
                                     target_lang=target,
                                     text=text,
                                     context=context,
                                     split_sentences=split_sentences,
                                     preserve_formatting=preserve_formatting,
                                     formality=formality).text


# Current translator in use. Typically set to Google Translate to avoid spending character tokens.
# Only import this translate function.
def translate(source=None, target='en', text='', context=None, split_sentences=0, preserve_formatting=False, formality='prefer_less',glossary_id=None):
    if model == 'google':
        return __googletranslate(source='auto', target=target, text=text)
    elif model == 'deepl':
        return __deeptranslate(source=source, target=target, text=text, context=context, split_sentences=split_sentences, preserve_formatting=preserve_formatting, formality=formality,glossary_id=glossary_id)
    else:
        print(f'Choose a valid model')

if __name__ == '__main__':
    #expect: Hola, esto es una prueba.
    #works
    print(translate(source='en', target='es', text='Hello, this is a test.'))

    #expect: How are you? This is a test.
    #works
    print(translate(text='你好吗。这是一个测试。'))

    #expect: Today Mom died. Or maybe yesterday, I don't know.
    #works
    print(translate(text="Aujourd'hui Maman est morte. Ou peut-être hier, je ne sais pas"))