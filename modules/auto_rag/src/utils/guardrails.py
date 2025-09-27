import re

# A simple list of keywords. In a real application, this would be a more
# sophisticated model or API call (e.g., OpenAI's Moderation endpoint).
BANNED_KEYWORDS = [
    "illegal", "self-harm", "violence", "hate speech", "explicit"
]

def content_filter(text: str) -> bool:
    """
    A basic content filter. Returns True if harmful content is detected, False otherwise.
    """
    text_lower = text.lower()
    for keyword in BANNED_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            return True
    return False