"""
Wrapper for SUTime.
"""

from typing import List, Union, Tuple, Dict
from functools import lru_cache
from datetime import datetime

from sutime import SUTime

SUTIME_LANGUAGES = {"en", "es"}
sutime_cache = {"SUTime": SUTime(mark_time_ranges=True, include_range=True)}


@lru_cache(maxsize=24)
def sutime_prediction(texts: List[str], language: str, processed_date: Union[None, str] = None) -> Tuple[Dict, int]:
    # Also join texts for SUTime for fewer JVM startups
    complete_text = '\n'.join(texts)

    if processed_date:
        reference_date = datetime.strptime(processed_date, '%Y-%M-%d')
        json_doc = sutime_cache["SUTime"].parse('\n'.join(complete_text), reference_date.isoformat())
    else:
        json_doc = sutime_cache["SUTime"].parse(complete_text)
    previous_end = 0
    new_text = ""

    for annotation in json_doc:
        if "timex-value" in annotation:
            annotation_format = '<TIMEX3 type="{}" value="{}" >{}</TIMEX3>'.format(annotation["type"],
                                                                                   annotation["timex-value"],
                                                                                   annotation["text"])
        else:
            annotation_format = '<TIMEX3 type="{}" >{}</TIMEX3>'.format(annotation["type"], annotation["text"])
        new_text = new_text + complete_text[previous_end:annotation["start"]] + annotation_format
        previous_end = annotation["end"]
    new_text = new_text + complete_text[previous_end:]

    return {"tagged_text": new_text}, 200
