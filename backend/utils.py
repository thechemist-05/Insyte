import re
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 42

_HINGLISH_MARKERS = {
    # Core verbs & auxiliaries
    "hai", "hain", "tha", "thi", "the", "hoga", "hogi", "hoge",
    "kar", "karo", "karna", "karta", "karti", "karte", "kiya", "kiye",
    "ho", "hona", "hua", "hui", "hue", "raha", "rahi", "rahe",
    "ja", "jao", "jana", "jata", "jati", "jate", "gaya", "gayi",
    "le", "lena", "leta", "leti", "lete", "liya", "liye",
    "de", "dena", "deta", "deti", "dete", "diya", "diye",
    "aa", "aana", "aata", "aati", "aate", "aaya", "aayi",
    "bana", "banao", "banana", "banta", "banti", "bante",
    "mil", "milna", "milta", "milti", "milte", "mila", "mili",
    "sun", "suno", "sunna", "sunta", "sunti", "sunte",
    "dekh", "dekho", "dekhna", "dekhta", "dekhti", "dekhte",
    "bol", "bolo", "bolna", "bolta", "bolti", "bolte",
    "ruk", "ruko", "rukna",

    # Negation & question words
    "nahi", "nahin", "mat", "na", "kya", "kyun", "kyunki",
    "kaise", "kab", "kahan", "kaun", "kitna", "kitni", "kitne",
    "koi", "kuch", "sab", "sabhi",

    # Pronouns & possessives
    "mein", "main", "mera", "meri", "mere", "hum", "humara",
    "tera", "teri", "tere", "tum", "tumhara", "tumhari",
    "aap", "aapka", "aapki", "aapke",
    "yeh", "ye", "yeh", "woh", "wo", "unka", "unki", "unke",
    "iska", "iski", "iske", "uska", "uski", "uske",
    "inhe", "unhe", "mujhe", "tumhe", "use",

    # Conjunctions & connectors
    "aur", "ya", "lekin", "magar", "par", "toh", "phir",
    "isliye", "tabhi", "jab", "tab", "agar", "to", "bhi",
    "sirf", "bas", "hi", "bhi",

    # Common adjectives & adverbs
    "accha", "acchi", "achha", "bahut", "bada", "badi", "bade",
    "chota", "choti", "chhota", "chhoti", "naya", "nayi", "naye",
    "purana", "purani", "purane", "sahi", "galat", "thoda",
    "thodi", "zyada", "kam", "aisa", "aisi", "aise",
    "waise", "waisa", "bilkul", "ekdum", "seedha", "jaldi",
    "abhi", "pehle", "baad", "andar", "bahar", "upar", "neeche",

    # People & relations
    "log", "banda", "bande", "ladka", "ladki", "bhai", "dost",
    "yaar", "behen", "maa", "baap", "beta", "beti",

    # Sentiment & slang
    "mast", "bakwas", "zabardast", "bekar", "shandaar", "kamaal",
    "shandar", "maja", "maza", "takleef", "dikkat", "mushkil",
    "asaan", "mushkil", "faida", "nuksan", "fayda",
    "shukriya", "dhanyawad", "maafi", "please", "sorry",
    "matlab", "samajh", "pata", "maloom", "yaad",
    "pasand", "napasand", "pyaar", "nafrat", "gussa",
    "khush", "dukhi", "pareshan", "tension",

    # Everyday objects & actions
    "kaam", "paisa", "paise", "cheez", "cheezein", "jagah",
    "waqt", "samay", "din", "raat", "subah", "sham",
    "ghar", "bahar", "dukan", "school", "college",
    "khana", "peena", "sona", "uthna", "chalana",
    "likho", "padho", "bolo", "suno",
}

def detect_language(text: str) -> str:
    clean = text.strip()

    if not clean:
        return "unknown"

    if re.search(r'[\u0900-\u097F]', clean):
        return "hi"

    tokens = set(re.findall(r'\b[a-z]+\b', clean.lower()))

    if len(tokens & _HINGLISH_MARKERS) >= 2:
        return "hinglish"

    try:
        lang = detect(clean)
        return lang if lang in ("en", "hi") else "other"
    except Exception:
        return "unknown"


def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#(\w+)", r"\1", text)
    text = re.sub(r"[^\w\s.,!?'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def preprocess(items: list[dict]) -> list[dict]:
    processed = []

    for item in items:
        cleaned = clean_text(item.get("text", ""))

        if len(cleaned) < 20:
            continue

        processed.append({
            **item,
            "text": cleaned,
            "lang": detect_language(cleaned),
        })

    return processed