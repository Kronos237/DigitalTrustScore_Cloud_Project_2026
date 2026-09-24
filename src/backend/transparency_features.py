"""Best-effort transparency signals from retrieved HTML, never reputation claims."""

from html.parser import HTMLParser


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs).get("href", "").lower())

    def handle_data(self, data):
        self.text.append(data.lower())


def collect(html: str, available: bool) -> dict:
    if not available:
        return {name: "unknown" for name in ("privacy_policy", "contact_page", "about_page", "terms_page", "email_address", "phone_number")}
    parser = _TextParser()
    parser.feed(html)
    joined = " ".join(parser.text) + " " + " ".join(parser.links)
    return {
        "privacy_policy": "detected" if any(term in joined for term in ("privacy", "data protection")) else "not_detected",
        "contact_page": "detected" if "contact" in joined else "not_detected",
        "about_page": "detected" if "about" in joined else "not_detected",
        "terms_page": "detected" if any(term in joined for term in ("terms", "conditions")) else "not_detected",
        "email_address": "detected" if "mailto:" in joined or "@" in joined else "not_detected",
        "phone_number": "detected" if any(character.isdigit() for character in joined) and "phone" in joined else "not_detected",
    }