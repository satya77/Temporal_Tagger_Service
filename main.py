from argparse import ArgumentParser

import torch
from flask import Flask
from flask_restful import Resource, Api, reqparse

from transformers_wrapper import transformer_prediction
from heideltime_wrapper import heideltime_prediction
from sutime_wrapper import sutime_prediction


app = Flask(__name__)
api = Api(app)

device = "cuda:0" if torch.cuda.is_available() else "cpu"

print("Caching models...")


class TimeTag(Resource):

    def post(self):

        parser = reqparse.RequestParser()  # initialize
        parser.add_argument("model_type", required=True, type=str)  # add args
        parser.add_argument("input", required=True, type=str)
        parser.add_argument("date", required=False, type=str)

        args = parser.parse_args()  # parse arguments to dictionary
        # Make model name more robust against spelling differences
        args["model_type"] = args["model_type"].lower()
        # Force as tuple to allow for LRU transformers_cache
        input_texts = tuple(args["input"].split("\n"))
        return self.annotate_texts(input_texts, args)

    @staticmethod
    def annotate_texts(texts, args):
        if args["model_type"].startswith("classifier"):
            classifier_type = args["model_type"].split("_")[1]
            return transformer_prediction(texts, classifier_type, args["date"])
        elif args["model_type"].startswith("heideltime"):
            if len(args["model_type"].split("_")) < 3:
                return {"tagged_text":
                        "Error: Please specify text as 'COLLOQUIAL', 'SCIENTIFIC', 'NEWS', or 'NARRATIVE'!"}, 409
            heideltime_lang = args["model_type"].split("_")[1]
            heideltime_mode = args["model_type"].split("_")[2]
            return heideltime_prediction(texts, heideltime_lang, heideltime_mode, args["date"])
        elif args["model_type"].startswith("sutime"):
            return sutime_prediction(texts, args["date"])
        else:
            return {"tagged_text": "Error: Unspecified model detected!"}, 409


api.add_resource(TimeTag, "/time_tag")  # add endpoints

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8001, help="The port for the server to run on. (Default: 8001)")
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port)
