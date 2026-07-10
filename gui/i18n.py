import json
import os
from pathlib import Path

LOCALE_CONFIG_PATH = Path("data/config/locale_config.json")
TR_DICT_PATH = Path("data/locales/tr.json")

def load_locale_preference() -> str:
    if LOCALE_CONFIG_PATH.exists():
        try:
            with open(LOCALE_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("lang", "en")
        except Exception:
            pass
    return "en"

def set_locale_preference(lang: str):
    LOCALE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCALE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({"lang": lang}, f, indent=4)

CURRENT_LANG = load_locale_preference()
_translations = {}

def load_translations():
    global _translations
    if CURRENT_LANG == "tr":
        if TR_DICT_PATH.exists():
            try:
                with open(TR_DICT_PATH, 'r', encoding='utf-8') as f:
                    _translations = json.load(f)
            except Exception as e:
                print(f"Failed to load translations: {e}")
        else:
            print("tr.json not found.")
            
load_translations()

def tr(text: str) -> str:
    """Translate text to the current language."""
    if CURRENT_LANG == "en":
        return text
    return _translations.get(text, text)
