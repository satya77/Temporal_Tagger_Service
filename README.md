# Temporal Tagger API

This repository provides the source code for the following demo paper:  


### Oline DATEing: A Web Interface for Temporal Annotations
Dennis Aumiller*, Satya Almasian*, David Pohl, Michael Gertz  
Institute of Computer Science, Heidelberg University  
To be presented at SIGIR 2022.  
(`*` indicates equal contribution)

**You can try out a demo of this interface online: https://onlinedating.ifi.uni-heidelberg.de/**

---------------------------------------------

This repository contains code for a Flask-RESTful API that adds temporal annotations to raw text.
The input is a raw text, where the paragraphs are seperated by `\n`. The output is an XML-tagged text with TIMEX3 tags.

## Installation:
Start with the requirements for Python by running `python3 -m pip install -r requirements.txt` from the project root folder.
You need to manually install the python wrapper for [HeidelTime](https://github.com/PhilipEHausner/python_heideltime/) 
and additional Java dependencies for [SUTime](https://github.com/FraBle/python-sutime) from their respective Github repositories.  
For HeidelTime, after cloning the Python wrapper's repository, run
```bash
chmod +x install_heideltime_standalone.sh
./install_heideltime_standalone.sh
```
For SUTime, you need to install the Java runtime with Maven, according to their [repository's instructions](https://github.com/FraBle/python-sutime#installation):
```bash
# Optionally install Maven with `sudo apt-get install maven` first
mvn dependency:copy-dependencies -DoutputDirectory=./jars -f $(python3 -c 'import importlib; import pathlib; print(pathlib.Path(importlib.util.find_spec("sutime").origin).parent / "pom.xml")')
# Install English resources
mvn dependency:copy-dependencies -DoutputDirectory=./jars -f $(python -c 'import importlib; import pathlib; print(pathlib.Path(importlib.util.find_spec("sutime").origin).parent / "pom.xml")') -P english
```
For our test environment, this is guaranteed to work with Java 11 under Ubuntu, and similarly under MacOS.  
You can run the backend by calling:
```
python main.py --port PORT_NUMBER
```

This will start a server on localhost, port `PORT_NUMBER`. The default port is set to `8001`.

## Send a request:

The requests can be sent using `http://localhost:PORT_NUMBER/time_tag`
Note that this has to be a `POST` request, and not a simle `GET` request.  
The request parameters are as follows (in JSON):

```
{
"model_type": "type of the model used for temporal tagging (see below for options)",
"input": "the text input, where paragraphs are separated by \n",
"date": "the creation date of the document"
}
```

`model_type` can take 7 values and contains Transformer-based models for English and German, 
[HeidelTime](https://github.com/HeidelTime/heideltime) (English and German) form the [python wrapper](https://github.com/PhilipEHausner/python_heideltime) 
and [SUTime](https://github.com/FraBle/python-sutime) (English only for now).

Token classifiers have the prefix of `Classifier`. The model choices are:

* `Classifier_EN`
* `Classifier_DATE_EN`
* `Classifier_CRF_EN`
* `Classifier_DE`

For the model `Classifier_DATE_EN` there should be an additional parameter provided, 
specifying the date of the document in this format: `yyyy-mm-dd`.
Two examples are as follows:

```
{
"model_type": "Classifier_EN",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",
}
```

Or:

```
{
"model_type": "Classifier_DATE_EN",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",``
"date": "2020-02-02"
}
```


**HeidelTime** has similar input and output. The model choices are: 

* `HeidelTime_EN_NARRATIVE`
* `HeidelTime_DE_NARRATIVE`
* `HeidelTime_EN_SCIENTIFIC`
* `HeidelTime_DE_SCIENTIFIC`
* `HeidelTime_EN_COLLOQUIAL`
* `HeidelTime_DE_COLLOQUIAL`
* `HeidelTime_EN_NEWS`
* `HeidelTime_DE_NEWS`

Where the final part of the model name specifies the text's domain for HeidelTime.
All modes are available for both English and German.
HeidelTime also allows the inclusion of  reference date and one can also specify using the date argument: 

```
{
"model_type": "Classifier_DATE_EN",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",``
"date":"2020-02-02"
}
```
without the specification of the date, the model automatically assumes today's date as the reference. 

**SUTime** does not differentiate between any domain, and is currently only available in our API for English.
SUTime also allows the inclusion of a reference date, and will similarly default to today as the reference date if left unspecified.
The model choices are:

* `SUTime_EN`

The output of all models is XML-like tagged text, for example:

```
{
"tagged_text": " <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2015-03-23\">Today</TIMEX3> is sunny\n  <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2013-03-23\">Tomorrow</TIMEX3> will be windy\n  <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2013-11-01\">Tomorrow</TIMEX3> is a public holiday."
}
```

## Extending the API:
You can check out `heideltime_wrapper.py` or `sutime_wrapper.py` to see a minimal processing script for external libraries.
In the `main.py` script, the corresponding wrapper is called, based on the provided model name in the API request.

Feel free to open an issue or PR for the inclusion of further models (or languages).
