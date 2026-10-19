"""Design-system guard: the stylesheets may only use the sizes, tracking and radii defined in tokens.css.

These are static checks (no database, no browser). The responsive overflow check lives in scripts/qa/sweep.mjs
because it needs a real browser.
"""
import re
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "css"
COMPONENT_FILES = ("site.css", "components.css", "pages.css", "characters.css", "garage.css", "garage_concept.css", "vehicle_detail.css", "regions.css")
RADII = {"var(--r-card)", "var(--r-tile)", "var(--r-pill)", "50%", "0", "inherit"}
SIZE_TOKENS = {"micro", "small", "body", "lead", "h4", "h3", "h2", "h1", "display", "numeral"}


def read(name):
    return (CSS_DIR / name).read_text(encoding="utf-8")


def declarations(css, prop):
    """Every value assigned to a property, ignoring custom-property definitions and comments."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.findall(r"(?<![-\w])" + re.escape(prop) + r"\s*:\s*([^;}]+)", css)


def test_tokens_define_exactly_the_type_scale():
    tokens = read("tokens.css")
    names = set(re.findall(r"--t-([a-z0-9]+)\s*:", tokens))
    assert names == SIZE_TOKENS
    smallest = re.search(r"--t-micro:\s*([\d.]+)rem", tokens)
    assert smallest and float(smallest.group(1)) * 16 >= 12, "nothing on the site may be smaller than 12 px"


def test_every_font_size_is_a_token():
    offenders = []
    for name in COMPONENT_FILES:
        css = read(name)
        for value in declarations(css, "font-size"):
            if not re.fullmatch(r"var\(--t-[a-z0-9]+\)|inherit", value.strip()):
                offenders.append(f"{name}: font-size: {value.strip()}")
        for value in declarations(css, "font"):
            value = value.strip()
            if value == "inherit":
                continue
            if not re.search(r"var\(--t-[a-z0-9]+\)", value):
                offenders.append(f"{name}: font: {value}")
    assert not offenders, "font sizes outside the scale:\n" + "\n".join(offenders)


def test_every_letter_spacing_is_a_token():
    offenders = []
    for name in COMPONENT_FILES:
        for value in declarations(read(name), "letter-spacing"):
            value = value.strip()
            if value not in {"0", "normal"} and not re.fullmatch(r"var\(--track-[a-z]+\)", value):
                offenders.append(f"{name}: letter-spacing: {value}")
    assert not offenders, "letter-spacing outside the scale:\n" + "\n".join(offenders)


def test_radii_are_card_tile_or_pill():
    offenders = []
    for name in COMPONENT_FILES:
        for value in declarations(read(name), "border-radius"):
            if value.strip() not in RADII:
                offenders.append(f"{name}: border-radius: {value.strip()}")
    assert not offenders, "radii outside the system:\n" + "\n".join(offenders)


def test_no_italics_and_no_serif():
    for name in COMPONENT_FILES + ("tokens.css",):
        css = read(name)
        assert "italic" not in re.sub(r"/\*.*?\*/", "", css, flags=re.S), f"{name} uses italics"
        assert not re.search(r"font-family:[^;]*\bserif\b(?!.*sans)", css), f"{name} uses a serif family"


def test_every_token_used_by_components_is_defined():
    tokens = read("tokens.css")
    defined = set(re.findall(r"(--[\w-]+)\s*:", tokens))
    used = set()
    for name in COMPONENT_FILES:
        used |= set(re.findall(r"var\((--[\w-]+)", read(name)))
    local = {"--r-chip", "--edge", "--g-gap", "--h", "--lineup-h", "--px", "--py", "--pxn", "--pyn", "--tint", "--from", "--mx", "--my", "--z", "--console", "--zx", "--zy", "--cat", "--dock", "--band", "--chapter", "--ox", "--oy", "--col", "--dp", "--lap", "--at", "--fx", "--fy", "--zf", "--dx", "--dy"}  # custom properties a component sets for itself
    undefined = {u for u in used if u not in defined and u not in local}
    # properties set inline by templates or JS (focus points, progress) are allowed
    undefined -= {"--p", "--progress", "--x", "--y", "--auto-ms", "--z", "--tx", "--ty", "--ov-x", "--ov-y", "--px", "--py", "--pxn", "--pyn"}   # set per element: layer travel; the overlap of the second picture
    assert not undefined, f"undefined custom properties: {sorted(undefined)}"
