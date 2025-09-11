import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

def normalize_text(text: str) -> str:
    """Normalize unicode and lowercase"""
    if not text:
        return ""
    return unicodedata.normalize("NFKC", text).strip().lower()

def transliterate_text(text: str):
    """Return both Hindi + English forms for better matching"""
    try:
        if any("\u0900" <= c <= "\u097F" for c in text):  # Hindi script
            eng = transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
            return {"hindi": text, "english": eng.lower()}
        else:
            hindi = transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
            return {"hindi": hindi, "english": text.lower()}
    except Exception:
        return {"hindi": text, "english": text.lower()}