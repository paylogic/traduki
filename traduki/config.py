"""Configuration for i18n."""


def LANGUAGE_CALLBACK():
    """Current language callback."""
    return 'en'


def LANGUAGE_CHAIN_CALLBACK():
    """Language chain callback."""
    return {'*': LANGUAGE_CALLBACK()}

LANGUAGES = ['en']
