from langdetect import detect, DetectorFactory

# Make detection deterministic
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """Detect whether text is English or French. Returns 'en' or 'fr'."""
    if not text or len(text.strip()) < 20:
        return "en"
    try:
        lang = detect(text)
        return "fr" if lang == "fr" else "en"
    except Exception:
        return "en"
