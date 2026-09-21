import os
from pathlib import Path
from typing import List

import yaml

languages = {}
languages_present = {}

# Resolve the language directory from this file instead of relying on the
# process working directory.  This also prevents non-YAML marker files (for
# example the project's NOBITA marker) from being treated as languages.
LANG_DIR = Path(__file__).resolve().parent / "langs"


def get_string(lang: str):
    return languages.get(lang, languages["en"])


def _load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Language file {path.name} must contain a YAML mapping")
    return data


# English is the base language and must always be loaded first.
_en_path = LANG_DIR / "en.yml"
if not _en_path.is_file():
    raise FileNotFoundError(f"Missing base language file: {_en_path}")

languages["en"] = _load_yaml(_en_path)
languages_present["en"] = languages["en"].get("name", "🇺🇸 English")

# Load only actual .yml language files.  Ignore marker/metadata files.
for path in sorted(LANG_DIR.glob("*.yml")):
    language_name = path.stem
    if language_name == "en":
        continue

    try:
        language_data = _load_yaml(path)
    except Exception as exc:
        # A broken optional translation must not prevent the bot from starting.
        print(f"Warning: unable to load language file {path.name}: {exc}. Skipping it.")
        continue

    # Fill missing strings from English so older translations remain usable.
    for item, value in languages["en"].items():
        language_data.setdefault(item, value)

    languages[language_name] = language_data
    languages_present[language_name] = language_data.get(
        "name", languages["en"].get("name", language_name)
    )
