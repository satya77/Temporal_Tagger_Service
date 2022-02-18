# Temporal Tagger API

This repository contains code for a Flask API that adds temporal annotations to raw text. The input is a raw text, where the paragraphs are seperated by `\n`. And the output is an XML tagged text with TIMEX3 tags.

## How to start:
Install the requirements form `requirements.txt`.
You need to install the python wrapper for [HeidelTime](https://github.com/PhilipEHausner/python_heideltime/blob/master/README.md) and [SUTime](https://github.com/FraBle/python-sutime) from their respective github repository. 
Finally run: 

`python main.py --port PORT_NUMBER`

This will start a server on localhost, port `PORT_NUMBER`. The default port is set to `8001`.

## Send a request:

The requests can be sent using `http://localhost:PORT_NUMBER/time_tag`
Note that this has to be a `POST` request, and not a simle `GET` request.  
The request parameters are as follows (in JSON):

```
{
"model_type": type of the model used for temporal tagging,
"input": the text input, where paragraphs are separated by \n ,
"date": (only required for classifier_date), the creation date of the document
}
```

`model_type` can take 9 values and contains transfomer based models for English and German, [HeidelTime](https://github.com/HeidelTime/heideltime) (english and german) form the [python wrapper](https://github.com/PhilipEHausner/python_heideltime) and [SUTime](https://github.com/FraBle/python-sutime) (english).

**Tranformer models** are two types: **Token classifiers** and **seq2seq** models. Token classifiers have the prefix of `classifier` and the seq2seq models have the prefix of `seq2seq`. The model choices are:

* `classifier_normal`
* `classifier_date`
* `classifier_crf`
* `seq2seq2_bert`
* `seq2seq_roberta`
* `classifier_german`

For the model `classifier_date` there should be an additional parameter provided, specifying the date of the document in this format: `yyyy-mm-dd`.
  Two examples are as follows:

```
{
"model_type": "seq2seq_roberta",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",
}
```

Or:

```
{
"model_type": "classifier_date",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",``
"date":"2020-02-02"
}
```


**HeidelTime** has similar input and output. The model choices are: 

* `heideltime_en_NARRATIVE`
* `heideltime_de_NARRATIVE`
* `heideltime_en_SCIENTIFIC`
* `heideltime_de_SCIENTIFIC`
* `heideltime_en_COLLOQUIAL`
* `heideltime_de_COLLOQUIAL`
* `heideltime_en_NEWS`
* `heideltime_de_NEWS`

Where the final part of the model name, specifies the "Mode" of HeidelTime, all modes are available for both English and German. HeidelTime also allows the inclusion of 
reference date and one can also specify using the date argument: 

```
{
"model_type": "classifier_date",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",``
"date":"2020-02-02"
}
```
without the specification of the date, the model automatically assumes the current date as the reference. 

**Sutime**, we also include the python implementation of sutime for the English language. Similar to HeidelTime, SUTime allows the inclusion of
reference date. 


The output of all models is the XML-tagged text, for example:

```
{
"tagged_text": " <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2015-03-23\">today</TIMEX3> is sunny\n  <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2013-03-23\">tomorrow</TIMEX3> will be windy\n  <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2013-11-01\">tomorrow</TIMEX3> is 5th of November"
}
```
