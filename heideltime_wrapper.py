"""
Wrapper for Heideltime.
"""

from typing import Tuple, Dict
from functools import lru_cache
from python_heideltime import Heideltime

heideltime_cache = {"heideltime": Heideltime()}


@lru_cache(maxsize=24)
def heideltime_prediction(texts: Tuple[str], heideltime_lang: str, heideltime_mode: str, date: str) -> Tuple[Dict, int]:

    # Determine language type: NARRATIVES, NEWS, COLLOQUIAL and SCIENTIFIC.
    lang = "ENGLISH" if heideltime_lang == "en" else "GERMAN"

    if heideltime_mode == "colloquial" and heideltime_lang == "EN":
        lang = "ENGLISHCOLL"
    if heideltime_mode == "scientific" and heideltime_lang == "EN":
        lang = "ENGLISHSCI"
    heideltime_cache["heideltime"].set_document_type(heideltime_mode.upper())
    heideltime_cache["heideltime"].set_language(lang)
    if date:
        heideltime_cache["heideltime"].set_document_time(date)

    # Join texts before processing, as heideltime can use this to cross-reference date anchors.
    doc = heideltime_cache["heideltime"].parse('\n'.join(texts))

    # Remove Heideltime's weird XML header.
    doc = doc.replace('<?xml version="1.0"?>\n<!DOCTYPE TimeML SYSTEM "TimeML.dtd">\n<TimeML>\n', '')
    doc = doc.replace('\n</TimeML>\n\n', '')

    return {"tagged_text": doc}, 200
