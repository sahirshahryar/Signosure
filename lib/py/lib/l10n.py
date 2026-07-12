from typing import Any, Dict, List

translations: Dict[str, Dict[str, Any]] = dict()
languages: List[str] = list()
default_locale: str = "en-US"


def set_default_locale(new_default: str):
    global default_locale
    default_locale = new_default


def load_languages(folder: str):
    pass


def t(key: str, substitutions: Dict, locale: str | None = None) -> str:
    return key
