import datetime
import json
import os

import requests
from flask import render_template, request
from langdetect import DetectorFactory
from langdetect import detect
from lxml import etree

from app import app

DetectorFactory.seed = 0
detect('init')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('main.html', values=True)
    if request.method == 'POST':
        return


@app.route('/examples', methods=['GET'])
def examples():
    with open(os.path.join(app.static_folder, 'data', 'examples.json'), 'r', encoding='utf-8') as f:
        return json.dumps(json.load(f))


@app.route('/process', methods=['POST'])
def process():
    temporal_api_host = "HOST_API"

    if request.json['model_type'] == 'Classifier_DATE':
        if request.json['date'] == "--":
            return 'Reference date is missing.', 500
        try:
            datetime.datetime.strptime(request.json['date'], '%Y-%m-%d')
        except KeyError:
            return 'Reference date is missing.', 500
        except ValueError:
            return 'The format of the date input is incorrect!', 500
    if request.json['model_type'].startswith("HeidelTime"):
        if request.json['model_type'].split("_")[1] not in ["NEWS", "NARRATIVES", "SCIENTIFIC", "COLLOQUIAL"]:
            return 'Please choose a mode for the HeidelTime model.', 500
    if 'date' in request.json:
        if request.json['date'] == "--":
            request.json['date'] = None
    if request.json['input'] == "":
        return 'The input is empty.', 500
    if request.json['model_type'] == "Tagging Models":
        return 'Please choose a model first. ', 500
    try:
        doc = etree.XML(request.json['input'])
        text = etree.tostring(doc.find('.//TEXT'), method='text').decode('utf-8')
        if text:
            if text == '':
                return 'The input is empty.', 500
            # elif detect(text) not in ['en','de']:
            #     return 'Unsupported language (English and German only).', 500
            else:
                request.json['input'] = text
                tagged_text = requests.post(temporal_api_host + '/time_tag', request.json).json()['tagged_text']
                tagged_text = tagged_text.replace('\n', '').strip()
                return json.dumps({'tagged_text': tagged_text})
        else:
            return 'The xml input is invalid.', 500
    except (etree.XMLSyntaxError, etree.ParseError):
        if request.json['input'] == '':
            return 'the input is empty.', 500
        # if detect(request.json['input'])  not in ['en','de']:
        #     return 'Unsupported language (English and German only).', 500

        result = json.loads(requests.post(temporal_api_host + '/time_tag', request.json).text)
        print(result)
        return result
