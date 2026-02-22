def normalize_word(word: str | None) -> str:
    return (word or '').strip().lower()


def is_valid_word(word: str, max_len: int = 15) -> bool:
    token = normalize_word(word)
    if not token:
        return False
    if len(token) > max_len:
        return False
    return token.replace('-', '').isalpha()


def classify_word(word: str) -> str:
    token = normalize_word(word)
    if not token:
        return 'empty'
    if '-' in token:
        return 'hyphenated'
    if token.isalpha():
        return 'alpha'
    return 'other'
