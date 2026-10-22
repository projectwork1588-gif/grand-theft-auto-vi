"""Form-cleaning helpers shared by the admin editors (Stories, Places): one place for the rules about text, addresses and database error codes, so every editor
treats them the same way. Pure Python, no database access and no Flask."""
import re
import unicodedata
from urllib.parse import urlsplit

SOURCE_MAX = 500
DUPLICATE_ENTRY = 1062                 # MySQL: a UNIQUE key was violated
FOREIGN_KEY_FAILED = (1216, 1452)      # a child row names a parent that does not exist (the connector reports 1216 or 1452)


def slugify(title):
    """'The Quiet Water' -> 'the-quiet-water' (accents dropped, anything else that is not a letter or digit becomes one hyphen)."""
    plain = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")[:80].strip("-")


def clean_text(form, name, errors, label, maximum, *, minimum=1, multiline=False):
    """The trimmed value of a text field, or '' after recording a problem. Control characters are refused (a line break and tab are fine in a long text)."""
    value = (form.get(name) or "").strip()
    if multiline:
        value = value.replace("\r\n", "\n").replace("\r", "\n")
    allowed = "\n\t" if multiline else ""
    if any(unicodedata.category(c) == "Cc" and c not in allowed for c in value):
        errors[name] = f"{label} contains a character that is not allowed."
        return ""
    if len(value) < minimum:
        errors[name] = f"{label} is required." if minimum <= 1 else f"{label} needs at least {minimum} characters."
        return ""
    if len(value) > maximum:
        errors[name] = f"{label} can have at most {maximum} characters."
        return ""
    return value


def clean_source_url(form, errors):
    """The optional source address: None when empty, otherwise a plain https address (no credentials, no spaces or control characters, at most SOURCE_MAX)."""
    value = (form.get("source_url") or "").strip()
    if not value:
        return None
    parts = urlsplit(value)
    if len(value) > SOURCE_MAX or parts.scheme != "https" or not parts.netloc or "@" in parts.netloc or any(c.isspace() or unicodedata.category(c) == "Cc" for c in value):
        errors["source_url"] = f"The source address must be a plain https address of at most {SOURCE_MAX} characters."
        return None
    return value
