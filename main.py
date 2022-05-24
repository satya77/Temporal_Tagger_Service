from argparse import ArgumentParser
from typing import Tuple, Dict

import torch
from flask import Flask
from flask_restful import Resource, Api, reqparse

from transformers_wrapper import transformer_prediction, TRANSFORMERS_LANGUAGES
from heideltime_wrapper import heideltime_prediction, HEIDELTIME_LANGUAGES
from sutime_wrapper import sutime_prediction, SUTIME_LANGUAGES
from timexy_wrapper import timexy_prediction, TIMEXY_LANGUAGES


app = Flask(__name__)
api = Api(app)

# Automatically uses GPU, if available.
device = "cuda:0" if torch.cuda.is_available() else "cpu"


def unsupported_language_response(model: str, supported_langs: str) -> Tuple[Dict, int]:
    return {"tagged_text": f"Unsupported language for model {model} specified. "
                           f"This model only supports the following languages: {supported_langs}"}, 409


class TimeTag(Resource):

    def post(self):

        parser = reqparse.RequestParser()  # initialize
        # add individual expected arguments
        parser.add_argument("model_type", required=True, type=str)
        parser.add_argument("language", required=True, type=str)
        parser.add_argument("input", required=True, type=str)
        parser.add_argument("date", required=False, type=str)

        # parse arguments to dictionary
        args = parser.parse_args()

        # Make model name more robust against spelling mistakes
        args["model_type"] = args["model_type"].lower()
        args["language"] = args["language"].lower()

        # Force input text as tuple to allow for LRU caching
        input_texts = tuple(args["input"].split("\n"))

        return self.annotate_texts(input_texts, args)

    @staticmethod
    def annotate_texts(texts, args):
        if args["model_type"].startswith("classifier"):
            if args["language"] not in TRANSFORMERS_LANGUAGES:
                return unsupported_language_response(args["model_type"], TRANSFORMERS_LANGUAGES)

            if len(args["model_type"].split("_")) > 1:
                classifier_type = args["model_type"].split("_")[1]
            else:
                classifier_type = "classifier"

            return transformer_prediction(texts, args["language"], classifier_type, args["date"])
        elif args["model_type"].startswith("heideltime"):
            if args["language"] not in HEIDELTIME_LANGUAGES:
                return unsupported_language_response(args["model_type"], HEIDELTIME_LANGUAGES)

            if len(args["model_type"].split("_")) > 1:
                heideltime_mode = args["model_type"].split("_")[1]
            else:
                # If no mode is specified, default to NARRATIVES as per Heideltime docs
                heideltime_mode = "NARRATIVES"
            return heideltime_prediction(texts, args["language"], heideltime_mode, args["date"])
        elif args["model_type"].startswith("sutime"):
            if args["language"] not in SUTIME_LANGUAGES:
                return unsupported_language_response(args["model_type"], SUTIME_LANGUAGES)

            return sutime_prediction(texts, args["language"], args["date"])
        elif args["model_type"].startswith("timexy"):
            if args["language"] not in TIMEXY_LANGUAGES:
                return unsupported_language_response(args["model_type"], TIMEXY_LANGUAGES)

            return timexy_prediction(texts, args["language"])
        else:
            return {"tagged_text": "Error: Unsupported model type specified!"}, 409


api.add_resource(TimeTag, "/time_tag")  # add endpoints


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8001, help="The port for the server to run on. (Default: 8001)")
    args = parser.parse_args()

    app.run(host="0.0.0.0", port=args.port)
