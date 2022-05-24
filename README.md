# Temporal Tagger API
Dennis Aumiller*, Satya Almasian*, David Pohl, Michael Gertz  
Heidelberg University, 2022  
Currently under submission as a demonstration paper at SIGIR 2022.

This repository contains code for a Flask-RESTful API that adds temporal annotations to raw text.
The input is a raw text, where the paragraphs are seperated by `\n`. The output is an XML-tagged text with TIMEX3 tags.

## Installation:
Start with the requirements for Python by running `python3 -m pip install -r requirements.txt` from the project root folder.
You need to manually install the python wrapper for [HeidelTime](https://github.com/PhilipEHausner/python_heideltime/) 
and additional Java dependencies for [SUTime](https://github.com/FraBle/python-sutime) from their respective Github repositories.
In both cases, you might need to install additional languages manually to ensure full support.
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

## Querying the API

The requests can be sent using `http://localhost:PORT_NUMBER/time_tag`
Note that this has to be a `POST` request, and not a simle `GET` request.  
The request parameters are as follows (in JSON):

```
{
"model_type": "type of the model used for temporal tagging (see below for options)",
"input": "the text input, where paragraphs are separated by \n",
"language": "the language in which the text is in",
"date": "the creation date of the document"
}
```

`model_type` can take different values, depending on the model architecture you want to use.
Each of the models also supports a different number of languages, so please make sure to check out the individual wrappers.

### Transformer-based Token Classifiers
Token classifiers have the prefix of `Classifier`. The model choices are:

* `Classifier`
* `Classifier_DATE`
* `Classifier_CRF`

The base `Classifier` is available in German (`DE`) and English (`EN`), all other transformer-based models are only for English.

For the model `Classifier_DATE` there should be an additional parameter provided, 
specifying the date of the document in this format: `yyyy-mm-dd`.
Two examples are as follows:

```
{
"model_type": "Classifier",
"language": "EN",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",
}
```

Or:

```
{
"model_type": "Classifier_DATE",
"language": "EN",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",``
"date": "2020-02-02"
}
```

### HeidelTime
**HeidelTime** has similar input and output. The model choices are more varied: 

* `HeidelTime_NARRATIVE`
* `HeidelTime_SCIENTIFIC`
* `HeidelTime_COLLOQUIAL`
* `HeidelTime_NEWS`

If you only provide `HeidelTime`, the default processing mode will be `NARRATIVE`.
Generally, the following languages are included for HeidelTime: English, German, Dutch, Spanish, Italian, French, Estonian and Portuguese.
Some of the modes (`SCIENTIFIC` and `COLLOQUIAL`) were only designed for English, and might thus not work with other languages.
HeidelTime also allows the inclusion of  reference date and one can also specify using the date argument: 

```
{
"model_type": "Heideltime",
"language": "EN",
"input": "today is sunny\n tomorrow will be windy\n tomorrow is 5th of November",
"date": "2020-02-02"
}
```
without the specification of the date, the model automatically assumes today's date as the reference. 


### SUTime
**SUTime** does not differentiate between any domain, and is currently only available in our API for English and Spanish.
SUTime also allows the inclusion of a reference date, and will similarly default to today as the reference date if left unspecified.
The model choices are:

* `SUTime`

### Timexy
We also support the spaCy extension [**Timexy**](https://github.com/paulrinckens/timexy),
however, we cannot guarantee for the performance of this particular package.
It is available for English, German and French. The usage is the same as for the simple `Classifier` models,
and further specifications of the reference date does not help.

### Response Structure
The output of all models is XML-like tagged text, for example:

```
{
"tagged_text": " <TIMEX3 tid=\"t1\" type=\"DATE\" value=\"2015-03-23\">Today</TIMEX3> is sunny\n  <TIMEX3 tid=\"t2\" type=\"DATE\" value=\"2013-03-23\">Tomorrow</TIMEX3> will be windy\n  <TIMEX3 tid=\"t3\" type=\"DATE\" value=\"2013-11-01\">Tomorrow</TIMEX3> is a public holiday."
}
```

## Extending the API:
You can check out `heideltime_wrapper.py` or `sutime_wrapper.py` to see a minimal processing script for external libraries.
In the `main.py` script, the corresponding wrapper is called, based on the provided model name in the API request.

Feel free to open an issue or PR for the inclusion of further models (or languages).
