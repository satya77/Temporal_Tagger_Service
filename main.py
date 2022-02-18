import os
from argparse import ArgumentParser
from functools import lru_cache

from flask import Flask
from flask_restful import Resource, Api, reqparse
from transformers import AutoTokenizer, EncoderDecoderModel, BertForTokenClassification,AutoModelForTokenClassification
from bs4 import BeautifulSoup
import torch

from helper_functions import merge_tokens, insert_tags_in_raw_text, find_timex_in_text, clean_predictions
from temporal_models.BERTWithDateLayerTokenClassification import BERTWithDateLayerTokenClassification
from temporal_models.NumBertTokenizer import NumBertTokenizer
from temporal_models.BERTWithCRF import BERT_CRF_NER
from python_heideltime import Heideltime
from flask import abort, request
import json
from sutime import SUTime
from datetime import datetime

# Fix for running on MacOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

app = Flask(__name__)
api = Api(app)

print("Caching models...")
cache = {}
device = "cuda:0" if torch.cuda.is_available() else "cpu"
cache["classifier_with_date"] = BERTWithDateLayerTokenClassification.from_pretrained(
    "satyaalmasian/temporal_tagger_DATEBERT_tokenclassifier").to(device)
cache["date_tokenizer"] = NumBertTokenizer("./temporal_models/vocab_date.txt")
cache["classifier_base"] = BertForTokenClassification.from_pretrained("satyaalmasian/temporal_tagger_BERT_tokenclassifier").to(device)
cache["classifier_crf"] = BERT_CRF_NER.from_pretrained("satyaalmasian/temporal_tagger_BERTCRF_tokenclassifier").to(device)
cache["classifier_tokenizer"] = AutoTokenizer.from_pretrained("satyaalmasian/temporal_tagger_BERT_tokenclassifier",
                                                              use_fast=False)
cache["id2label"] = {v: k for k, v in cache["classifier_base"].config.label2id.items()}
cache["tokenizer_roberta"] = AutoTokenizer.from_pretrained("satyaalmasian/temporal_tagger_roberta2roberta")
cache["seq2seq_roberta"] = EncoderDecoderModel.from_pretrained("satyaalmasian/temporal_tagger_roberta2roberta").to(device)
cache["tokenizer_bert"] = AutoTokenizer.from_pretrained("satyaalmasian/temporal_tagger_bert2bert")
cache["seq2seq_bert"] = EncoderDecoderModel.from_pretrained("satyaalmasian/temporal_tagger_bert2bert").to(device)

cache["classifier_german"] = AutoModelForTokenClassification.from_pretrained("satyaalmasian/temporal_tagger_German_GELECTRA").to(device)
cache["classifier_german_tokenizer"] = AutoTokenizer.from_pretrained("satyaalmasian/temporal_tagger_German_GELECTRA", use_fast=False)
cache["heideltime"] = Heideltime()
cache["sutime"]= SUTime(mark_time_ranges=True, include_range=True)


class TimeTag(Resource):

    def post(self):

        parser = reqparse.RequestParser()  # initialize
        parser.add_argument("model_type", required=True, type=str)  # add args
        parser.add_argument("input", required=True, type=str)
        parser.add_argument("date", required=False, type=str)

        args = parser.parse_args()  # parse arguments to dictionary
        # Force as tuple to allow for LRU cache
        input_texts = tuple(args["input"].split("\n"))
        annotated_texts = self.annotate_texts(input_texts, args)

        return {"tagged_text": "\n".join(annotated_texts)}, 200

    def annotate_texts(self, texts, args):
        annotated_texts = []
        if args["model_type"].startswith("classifier"):
            classifier_type = args["model_type"].split("_")[1]
            if classifier_type == "date":
                if args["date"] is None:
                    return {"For the dateBERT model you need to specify a reference date."}, 409

                processed_date = torch.LongTensor(
                    cache["date_tokenizer"]([args["date"].replace("-", " ")],
                                            add_special_tokens=False)["input_ids"]).to(device)
            else:
                processed_date = None

            return self.tagger_prediction(texts, classifier_type, processed_date)

        if args["model_type"].startswith("seq2seq"):
            seq2seq_type = args["model_type"].split("_")[1]
            return self.seq2seq_prediction(texts, seq2seq_type, args["model_type"])

        if args["model_type"].startswith("heideltime"):
            heideltime_lang = args["model_type"].split("_")[1]
            heideltime_mode = args["model_type"].split("_")[2]
            return self.heideltime_prediction(texts, heideltime_lang,heideltime_mode, args["date"])
        if args["model_type"].startswith("sutime"):
            return self.sutime_prediction(texts, args["date"])





    @staticmethod
    @lru_cache(maxsize=24)
    def seq2seq_prediction(texts, seq2seq_type, model_type):
        annotated_texts = []
        for input_text in texts:
            model_inputs = cache[f"tokenizer_{seq2seq_type}"](input_text, truncation=True, return_tensors="pt").to(device)

            # Model forward pass; generate automatically disables activations
            out = cache[model_type].generate(**model_inputs)
            decoded_preds = cache[f"tokenizer_{seq2seq_type}"].batch_decode(out, skip_special_tokens=True)

            # Alignment of tokens and post-processing
            pred_soup = BeautifulSoup(clean_predictions(decoded_preds[0]), "lxml")
            timex_preds = pred_soup.findAll("timex3")
            new_text = find_timex_in_text(timex_preds, input_text, seq2seq_type)
            annotated_texts.append(new_text)
        return annotated_texts


    @staticmethod
    @lru_cache(maxsize=24)
    def heideltime_prediction(texts, heideltime_lang,heideltime_mode,date):
        # NARRATIVES, NEWS, COLLOQUIAL and SCIENTIFIC.
        lang ="ENGLISH" if heideltime_lang=="en" else "GERMAN"
        if heideltime_mode=="COLLOQUIAL" and heideltime_lang=="en":
            lang="ENGLISHCOLL"
        if heideltime_mode=="SCIENTIFIC" and heideltime_lang=="en":
            lang="ENGLISHSCI"
        cache["heideltime"].set_document_type(heideltime_mode)
        cache["heideltime"].set_language(lang)
        if date:
            cache["heideltime"].set_document_time(date)

        annotated_texts=[]
        for text in texts:
            doc=cache["heideltime"].parse(text)
            doc = doc.replace('<?xml version="1.0"?>\n<!DOCTYPE TimeML SYSTEM "TimeML.dtd">\n<TimeML>\n', '')
            doc = doc.replace('\n</TimeML>\n\n', '')
            annotated_texts.append(doc)
        return annotated_texts

    @staticmethod
    @lru_cache(maxsize=24)
    def sutime_prediction(texts,processed_date=None):
        if processed_date:
            reference_date = datetime.strptime(processed_date, '%Y-%M-%d')
        annotated_texts=[]
        for text in texts:
            if processed_date:
                json_doc=cache["sutime"].parse(text, reference_date.isoformat())
            else:
                json_doc=cache["sutime"].parse(text)
            pervious_end=0
            new_text=""
            for annotation in json_doc:
                if "timex-value" in annotation:
                    annotation_format='<TIMEX3 type="{}" value="{}" >{}</TIMEX3>'.format(annotation["type"], annotation["timex-value"],annotation["text"])
                else:
                    annotation_format='<TIMEX3 type="{}" >{}</TIMEX3>'.format(annotation["type"], annotation["text"])
                new_text=new_text+ text[pervious_end:annotation["start"]]+annotation_format
                pervious_end=annotation["end"]
            new_text=new_text+text[pervious_end:]
            annotated_texts.append(new_text)
        return annotated_texts


    @staticmethod
    @lru_cache(maxsize=24)
    def tagger_prediction(texts, classifier_type, processed_date):
        annotated_texts = []
        if classifier_type=="german":
            text_tokenizer = cache["classifier_german_tokenizer"]
        else:
            text_tokenizer = cache["classifier_tokenizer"]
        annotation_id = 1
        for input_text in texts:
            processed_text = text_tokenizer(input_text, return_tensors="pt").to(device)

            # Preprocess inputs depending on model type
            if classifier_type == "date":
                processed_text["input_date_ids"] = processed_date
                model_name = "classifier_with_date"
            elif classifier_type == "normal":
                model_name = "classifier_base"
            elif classifier_type=="crf":
                processed_text["inference_mode"] = True
                model_name = "classifier_crf"
            else:
                model_name="classifier_german"

            # Compute forward pass without activations
            with torch.no_grad():
                result = cache[model_name](**processed_text)

            # Decode results based on model
            if classifier_type != "crf":
                classification = torch.argmax(result[0], dim=2)[0]
                id2label = cache["id2label"]
            else:
                classification = result[0][0]
                id2label = {v: k for k, v in cache["classifier_crf"].config.label2id.items()}

            # Alignment of tokens and post-processing
            merged_tokens = merge_tokens(processed_text["input_ids"][0], classification, id2label, text_tokenizer)
            annotated_text, annotation_id = insert_tags_in_raw_text(input_text, merged_tokens, annotation_id)
            annotated_texts.append(annotated_text)

        return annotated_texts


api.add_resource(TimeTag, "/time_tag")  # add endpoints

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in ['129.206.61.24','129.206.61.70']:
        abort(403)  # Forbidden

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8001, help="The port for the server to run on. (Default: 8001)")
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port)
