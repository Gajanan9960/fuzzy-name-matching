from rapidfuzz import fuzz
import textdistance

def phonetic_code(name: str) -> str:
    """Basic Soundex-like phonetic encoding for Hindi/English"""
    name = name.lower()
    vowels = "aeiou"
    code = name[0] if name else ""
    for ch in name[1:]:
        if ch not in vowels:
            code += ch
    return code[:6]  # simple truncation

def fuzzy_match(name_a, name_b):
    """Return final similarity score (0–100) combining multiple methods"""
    if not name_a or not name_b:
        return 0

    # 1. Levenshtein (edit distance)
    lev_score = fuzz.ratio(name_a, name_b)

    # 2. Jaro-Winkler
    jw_score = textdistance.jaro_winkler.normalized_similarity(name_a, name_b) * 100

    # 3. Phonetic (boost if codes match)
    phonetic_boost = 10 if phonetic_code(name_a) == phonetic_code(name_b) else 0

    # Weighted fusion
    final_score = (0.5 * lev_score + 0.4 * jw_score) + phonetic_boost
    return min(final_score, 100)