"""
Wrapper for Timexy: https://github.com/paulrinckens/timexy
"""
from typing import List, Tuple, Dict
from functools import lru_cache

import spacy
from timexy import Timexy

TIMEXY_LANGUAGES = {"en", "fr", "de"}


def get_spacy_model(model_name: str) -> spacy.language.Language:
    return spacy.load(model_name, disable=("ner",))


@lru_cache(maxsize=4)
def get_timexy_model(language: str) -> spacy.language.Language:
    if language == "de":
        model = "de_core_news_sm"
    elif language == "en":
        model = "en_core_web_sm"
    elif language == "fr":
        model = "fr_core_news_sm"
    else:
        raise ValueError(f"Unsupported language '{language}' for Timexy supplied!")
    nlp = get_spacy_model(model)
    config = {
        "kb_id_type": "timex3",  # possible values: 'timex3'(default), 'timestamp'
        "label": "timexy",  # default: 'timexy'
        "overwrite": False  # default: False
    }
    nlp.add_pipe("timexy", config=config, before="ner")

    return nlp


timexy_cache = {"en": get_timexy_model("en"), "de": get_timexy_model("de"), "fr": get_timexy_model("fr")}


@lru_cache(maxsize=24)
def timexy_prediction(texts: List[str], language: str) -> Tuple[Dict, int]:

    texts = "\n".join(texts)

    nlp = timexy_cache[language]

    annotated_doc = nlp(texts)

    # Add annotations in TIMEX3 format, for consistency
    result_string = ""
    previous_end = 0
    for tag in annotated_doc.ents:
        result_string += f"{texts[previous_end:tag.start_char]}<{tag.kb_id_}>{tag.text}</TIMEX3>"
        previous_end = tag.end_char

    # Add the remaining text back
    result_string += texts[previous_end:]

    return {"tagged_text": result_string}, 200
