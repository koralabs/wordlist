import re
import json
import sys

# ================================================
# CONFIGURATION
# ================================================

WORDS_FILE = "t.words"          # Verbatim copy-paste of JS array from handle.me site from t.words = to },

#[{
#            word: "69",
#            algorithms: ["suggestive"],
#            position: "exact"
#        }, {
#            word: "zulu",
#            algorithms: ["hatespeech"],
#            position: "exact"
#        }]

# ================================================
# LOADING & CLEANING PROTECTED WORDS
# ================================================

def aggressive_js_to_json_clean(raw: str) -> str:
    """Convert messy/minified JS array to valid JSON"""
    raw = re.sub(r'^\s*(?:t\.)?words\s*=\s*', '', raw, flags=re.I)
    raw = raw.strip()

    if not (raw.startswith('[') and raw.endswith(']')):
        raise ValueError("Array must start with [ and end with ]")

    # Quote unquoted keys
    raw = re.sub(r'([\{,]\s*)(\w+)(\s*:)', r'\1"\2":', raw)
    # Single → double quotes
    raw = raw.replace("'", '"')
    # JS booleans
    raw = raw.replace('!0', 'true').replace('!1', 'false')
    # Trailing commas
    raw = re.sub(r',\s*([}\]])', r'\1', raw)
    # Normalize whitespace
    raw = ' '.join(raw.split())

    return raw


def load_protected_words():
    try:
        with open(WORDS_FILE, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
    except FileNotFoundError:
        print(f"Error: '{WORDS_FILE}' not found.")
        sys.exit(1)

    try:
        cleaned = aggressive_js_to_json_clean(raw)
        data = json.loads(cleaned)
        if not isinstance(data, list):
            raise ValueError("Not a list")
        print(f"Loaded {len(data)} protected words.")
        return data
    except json.JSONDecodeError as e:
        print("Parsing failed:", str(e))
        print("Around error:", cleaned[max(0, e.pos-60):e.pos+60] + "...")
        sys.exit(1)


# Load once
try:
    PROTECTED_WORDS = load_protected_words()
except Exception as e:
    print("Critical error:", str(e))
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
