"""Create a local .env with freshly generated random secrets. Prints no secret values.

    python -m scripts.make_env

Refuses to overwrite an existing .env. The file is ignored by Git.
"""
import re
import secrets
import sys

from scripts.schema_info import ROOT

GENERATED = ("SECRET_KEY", "DB_PASSWORD", "MIGRATE_DB_PASSWORD")


def main():
    target, template = ROOT / ".env", ROOT / ".env.example"
    if target.exists():
        print(".env already exists. Nothing was changed.", file=sys.stderr)
        return 1
    text = template.read_text(encoding="utf-8")
    for key in GENERATED:
        text = re.sub(rf"^{key}=.*$", f"{key}={secrets.token_urlsafe(24)}", text, flags=re.MULTILINE)
    target.write_text(text, encoding="utf-8")
    print(f"Created .env with random values for: {', '.join(GENERATED)} (values not displayed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
