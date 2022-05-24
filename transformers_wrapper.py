"""
Wrapper for all supported Transformer-based models.
"""
from typing import List, Tuple, Union, Dict
from functools import lru_cache
import logging
import os

import torch
from transformers import AutoTokenizer, BertForTokenClassification, AutoModelForTokenClassification

from temporal_models.BERTWithDateLayerTokenClassification import BERTWithDateLayerTokenClassification
from temporal_models.NumBertTokenizer import NumBertTokenizer
from temporal_models.BERTWithCRF import BERT_CRF_NER
from helper_functions import merge_tokens, insert_tags_in_raw_text

# Fix for running transformers inference on MacOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

TRANSFORMERS_LANGUAGES = {"de", "en"}

device = "cuda:0" if torch.cuda.is_available() else "cpu"

transformers_cache = {}
# Tokenizers for English tokenizers
transformers_cache["classifier_tokenizer"] = AutoTokenizer.from_pretrained("satyaalmasian/temporal_tagger_BERT_tokenclassifier", use_fast=False)
transformers_cache["date_tokenizer"] = NumBertTokenizer("./temporal_models/vocab_date.txt")

# English classification models
# transformers_cache["classifier_date_en"] = BERTWithDateLayerTokenClassification.from_pretrained("satyaalmasian/temporal_tagger_DATEBERT_tokenclassifier").to(device)
transformers_cache["classifier_en"] = BertForTokenClassification.from_pretrained("satyaalmasian/temporal_tagger_BERT_tokenclassifier").to(device)
# transformers_cache["classifier_crf_en"] = BERT_CRF_NER.from_pretrained("satyaalmasian/temporal_tagger_BERTCRF_tokenclassifier").to(device)
#
# # German tokenization models
# transformers_cache["classifier_de"] = AutoModelForTokenClassification.from_pretrained("satyaalmasian/temporal_tagger_German_GELECTRA").to(device)
# transformers_cache["classifier_de_tokenizer"] = AutoTokenizer.from_pretrained("satyaalmasian/temporal_tagger_German_GELECTRA", use_fast=False)
#
# # ID to label dictionary for model predictions
transformers_cache["id2label"] = {v: k for k, v in transformers_cache["classifier_en"].config.label2id.items()}


@lru_cache(maxsize=48)
def transformer_prediction(texts: List[str], language: str, classifier_type: str, date: Union[None, str]) \
        -> Tuple[Dict, int]:
    annotated_texts = []
    if language == "de":
        text_tokenizer = transformers_cache["classifier_de_tokenizer"]
    elif language == "en":
        text_tokenizer = transformers_cache["classifier_tokenizer"]
    else:
        raise ValueError("Unsupported language passed to transformers pipeline!")
    annotation_id = 1

    # Embed date, if relevant
    if classifier_type == "date":
        if date is None:
            return {"tagged_text": "Reference date required for the date classifier!"}, 409
        processed_date = torch.LongTensor(
            transformers_cache["date_tokenizer"]([date.replace("-", " ")], add_special_tokens=False)["input_ids"]
        ).to(device)
    else:
        processed_date = None

    # Process individual text segments.
    for input_text in texts:
        processed_text = text_tokenizer(input_text, return_tensors="pt").to(device)

        # Preprocess inputs depending on model type
        if classifier_type == "date" and language == "en":
            processed_text["input_date_ids"] = processed_date
            model_name = "classifier_date_en"
        elif classifier_type == "classifier" and language == "en":
            model_name = "classifier_en"
        elif classifier_type == "crf" and language == "en":
            processed_text["inference_mode"] = True
            model_name = "classifier_crf_en"
        elif classifier_type == "de":
            model_name = "classifier_de"
        else:
            return {"tagged_text": f"Error: Unrecognized combination of model type '{classifier_type}' and "
                                   f"language '{language}' for tagging methods!"}, 409

        # Compute forward pass without activations
        with torch.no_grad():
            result = transformers_cache[model_name](**processed_text)

        # Decode results based on model
        if classifier_type != "crf":
            classification = torch.argmax(result[0], dim=2)[0]
            id2label = transformers_cache["id2label"]
        else:
            classification = result[0][0]
            id2label = {v: k for k, v in transformers_cache["classifier_crf_en"].config.label2id.items()}

        # Alignment of tokens and post-processing
        merged_tokens = merge_tokens(processed_text["input_ids"][0], classification, id2label, text_tokenizer)
        annotated_text, annotation_id = insert_tags_in_raw_text(input_text, merged_tokens, annotation_id)
        annotated_texts.append(annotated_text)

    return {"tagged_text": "\n".join(annotated_texts)}, 200
