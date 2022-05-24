"""
Wrapper for Heideltime.
"""

from typing import Tuple, Dict, Optional
from functools import lru_cache
from python_heideltime import Heideltime

heideltime_cache = {"heideltime": Heideltime()}

HEIDELTIME_LANGUAGES = {"en", "de", "es", "ar", "fr"}
LANGUAGE_MAPPING = {"en": "ENGLISH", "de": "GERMAN", "es": "SPANISH", "ar": "ARABIC", "fr": "FRENCH"}
AVAILABLE_MODES = {"COLLOQUIAL", "SCIENTIFIC", "NEWS", "NARRATIVE"}


@lru_cache(maxsize=24)
def heideltime_prediction(texts: Tuple[str], language: str, heideltime_mode: str, date: Optional[str]) \
        -> Tuple[Dict, int]:

    # Special language considerations for English colloquial and scientific texts
    if heideltime_mode == "colloquial" and language == "en":
        heideltime_language_tag = "ENGLISHCOLL"
    elif heideltime_mode == "scientific" and language == "en":
        heideltime_language_tag = "ENGLISHSCI"
    else:
        heideltime_language_tag = determine_language(language)

    # Set document parameters
    heideltime_cache["heideltime"].set_document_type(heideltime_mode.upper())
    heideltime_cache["heideltime"].set_language(heideltime_language_tag)
    if date:
        heideltime_cache["heideltime"].set_document_time(date)

    # Join texts back together before processing, as Heideltime can use this to cross-reference date anchors.
    # Also, spinning up Heideltime takes some overhead time, so reducing the number of calls is advantageous, too.
    doc = heideltime_cache["heideltime"].parse('\n'.join(texts))
    doc = strip_xml_wrapper(doc)

    return {"tagged_text": doc}, 200


def determine_language(lang: str) -> str:
    return LANGUAGE_MAPPING[lang]


def strip_xml_wrapper(text: str) -> str:
    text = text.replace('<?xml version="1.0"?>\n<!DOCTYPE TimeML SYSTEM "TimeML.dtd">\n<TimeML>\n', '')
    text = text.replace('\n</TimeML>\n\n', '')
    return text
