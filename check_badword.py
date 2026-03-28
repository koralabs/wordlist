import re
import json
import sys
import requests

# ================================================
# CONFIGURATION
# ================================================

WORDS_URL = "https://raw.githubusercontent.com/koralabs/kora-labs-common/refs/heads/master/src/protectedWords/protectedWords.ts"

# ================================================
# LOADING & CLEANING PROTECTED WORDS
# ================================================

def aggressive_js_to_json_clean(raw: str) -> str:
    """Convert messy/minified JS/TS array to valid JSON"""

    # 1. Remove all JS comments (// and /* */)
    raw = re.sub(r'//.*', '', raw)
    raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)

    # 2. Find the start of the actual data array.
    # We look for the first '[' that is followed by a '{' (the start of the first object)
    match = re.search(r'\[\s*\{', raw)
    if not match:
        raise ValueError("Could not find the start of the word objects array")

    start_index = match.start()
    end_index = raw.rfind(']')

    if start_index == -1 or end_index == -1:
        raise ValueError("Could not find a valid array structure (missing [ or ])")

    raw = raw[start_index:end_index + 1]

    # 3. Clean up JS-isms to make it valid JSON
    # Quote unquoted keys (word: -> "word":)
    raw = re.sub(r'([\{,]\s*)(\w+)(\s*:)', r'\1"\2":', raw)
    # Single quotes to double quotes
    raw = raw.replace("'", '"')
    # JS booleans !0/!1
    raw = raw.replace('!0', 'true').replace('!1', 'false')
    # Remove trailing commas before closing braces/brackets
    raw = re.sub(r',\s*([}\]])', r'\1', raw)

    # 4. Final whitespace normalization
    raw = ' '.join(raw.split())

    return raw


def load_protected_words():
    print(f"Fetching protected words from {WORDS_URL}...")
    try:
        response = requests.get(WORDS_URL, timeout=10)
        response.raise_for_status() # Raise error for 404/500
        raw = response.text.strip()
    except Exception as e:
        print(f"Error fetching online file: {e}")
        sys.exit(1)

    try:
        cleaned = aggressive_js_to_json_clean(raw)
        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Parsed data is not a list")
        print(f"Successfully loaded {len(data)} protected words.")
        return data
    except json.JSONDecodeError as e:
        print("Parsing failed. The content might be too complex for the regex cleaner.")
        print("Error snippet:", cleaned[max(0, e.pos-40):e.pos+40] + "...")
        sys.exit(1)

PROTECTED_WORDS = []

try:
    PROTECTED_WORDS = load_protected_words()

except Exception as e:
    print(f"Critical error during initialization: {e}")
    sys.exit(1)

# ================================================
# HELPERS
# ================================================

HANDLE_REGEX = re.compile(r'^[a-z0-9_.-]{1,15}$')
SEGMENT_REGEX = re.compile(r'([0-9a-z]+)[@_.-]*')

def normalize_singular(word: str) -> str:
    """Basic English plural → singular"""
    if len(word) > 3:
        if word.endswith('ies'):
            return word[:-3] + 'y'
        if word.endswith('ves'):
            return word[:-3] + 'f'
        if word.endswith('s') and not word.endswith(('ss', 'us', 'is')):
            return word[:-1]
    return word


def is_badword_in_text(text: str, entry) -> bool:
    """Check if a specific entry matches in text (with singular/plural)"""
    word = entry['word'].lower()
    singular = normalize_singular(word)
    plural = word + 's' if not word.endswith('s') else word

    return (
        word in text or
        singular in text or
        plural in text
    )


def check_handle(handle: str) -> tuple[bool, str]:
    handle_lower = handle.lower().strip()

    if not HANDLE_REGEX.match(handle_lower):
        return False, "Invalid format (1-15 chars, only a-z0-9_.-)"

    # Split into meaningful segments
    segments = [m.group(1) for m in SEGMENT_REGEX.finditer(handle_lower) if m.group(1)]

    # Join segments with spaces for easier "contains" checking
    text_to_check = ' '.join(segments)

    for entry in PROTECTED_WORDS:
        word = entry.get('word', '').lower()
        if not word:
            continue

        algorithms = entry.get('algorithms', [])
        position = entry.get('position', 'exact')
        exceptions = [e.lower() for e in entry.get('exceptions', [])]
        can_be_positive = entry.get('canBePositive', False)

        # Skip obvious safe ones
        if can_be_positive and len(algorithms) == 1 and 'modifier' in algorithms:
            continue

        matched = False

        if position == 'exact':
            if any(s == word for s in segments):
                matched = True
        elif position == 'any':
            if is_badword_in_text(text_to_check, entry):
                matched = True
        elif position == 'beginswith':
            if any(s.startswith(word) for s in segments):
                matched = True

        if matched:
            # Check exceptions
            if any(exc in text_to_check or any(s == exc for s in segments) for exc in exceptions):
                continue

            # If it's a modifier-only, be cautious (you can make stricter)
            return False, f"Flagged: {word} ({', '.join(algorithms)})"

    return True, "OK"


# ================================================
# MAIN
# ================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_badword.py <handles_file.txt>")
        print("       (one handle per line)")
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            handles = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Cannot read file: {e}")
        sys.exit(1)

    print(f"\nChecking {len(handles)} handles...\n")
    print(f"{'HANDLE':<20} {'STATUS':<10} REASON")
    print("-" * 60)

    for h in handles:
        ok, reason = check_handle(h)
        status = "OK" if ok else "FLAGGED"
        print(f"{h:<20} {status:<10} {reason}")
