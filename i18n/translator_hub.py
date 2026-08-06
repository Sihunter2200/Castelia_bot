from fluentogram import TranslatorHub, FluentTranslator
from fluent_compiler.bundle import FluentBundle

def create_translator_hub() -> TranslatorHub:
    translator_hub = TranslatorHub(
        # Указываем только русский язык
        locales_map={
            'ru': ('ru', 'en')
        },
        translators=[
            FluentTranslator(
                locale='ru',
                translator=FluentBundle.from_files(
                    locale='ru-RU',
                    filenames=['locales/ru/LC_MESSAGES/txt.ftl']
                )
            ),
            FluentTranslator(
                locale='en',
                translator=FluentBundle.from_files(
                    locale='en-EN',
                    filenames=['locales/en/LC_MESSAGES/txt.ftl']
                )
            )
        ]
    )
    return translator_hub