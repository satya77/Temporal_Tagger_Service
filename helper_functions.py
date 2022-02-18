import re
from typing import List, Tuple
from temporal_models.BERTWithDateLayerTokenClassification import BERTWithDateLayerTokenClassification
from temporal_models.NumBertTokenizer import NumBertTokenizer
from temporal_models.BERTWithCRF import BERT_CRF_NER
from collections import Counter
from transformers import AutoTokenizer, BertForTokenClassification

def find_timex_in_text(timex_preds, input_text, model_type):
    if model_type == "bert":
        original_paragraph = input_text.lower()
    else:
        original_paragraph = input_text
    end_previous_timex = 0
    previous_timex_cleaned_text = ""
    new_text = ""
    index = 0
    for timex in timex_preds:
        cleaned_text = timex.text.replace("<", "").replace(">", "").replace("\"", "").strip()
        # sometimes the cleaninng has leftovers
        if cleaned_text.startswith("- "):
            cleaned_text = cleaned_text[2:]

        if len(cleaned_text) < 2:
            continue;
        beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
        if cleaned_text == "day" and beginning_timex != -1 and original_paragraph[
                                                               beginning_timex - 2:beginning_timex] == "to":
            cleaned_text = "today"
            beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
        # if the model predicted full year instead of the last two digits
        if beginning_timex == -1 and len(cleaned_text) == 4 and cleaned_text.isdigit():
            beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text[2:])
            cleaned_text = cleaned_text[2:].strip()

        # if the model predicted full year with an extra repeation
        if beginning_timex == -1 and len(cleaned_text) == 6 and cleaned_text.isdigit():
            beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text[:-2])
            cleaned_text = cleaned_text[:-2].strip()

        # if the first word is repeating
        elif beginning_timex == -1 and len(cleaned_text.split(" ")) > 1 and cleaned_text.split(" ")[0] == \
                cleaned_text.split(" ")[1]:
            cleaned_text = ' '.join(cleaned_text.split(" ")[:-1])
            beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)

        # if the first and last word is repeating
        elif beginning_timex == -1 and len(cleaned_text.split(" ")) > 1 and cleaned_text.split(" ")[0] == \
                cleaned_text.split(" ")[-1]:
            cleaned_text = ' '.join(cleaned_text.split(" ")[1:])
            beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
        # if its single word separated by "-"
        elif beginning_timex == -1 and len(cleaned_text.split(" ")) < 2 and len(
                cleaned_text.split("-")) > 1:
            for word in cleaned_text.split("-"):
                if word in original_paragraph[end_previous_timex:]:
                    cleaned_text = word
                    beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
                    break;
        # more than one words the first one is a digit
        elif beginning_timex == -1 and len(cleaned_text.split(" ")) < 2 and len(
                cleaned_text) > 2 and not cleaned_text[:1].isdigit() and cleaned_text[-1].isdigit():
            word = cleaned_text[:-1]
            if word.lower() in original_paragraph[end_previous_timex:].lower():
                cleaned_text = word
                beginning_timex = original_paragraph[end_previous_timex:].lower().find(cleaned_text.lower())
                break;
        # if its just a single word
        elif beginning_timex == -1 and len(cleaned_text.split(" ")) < 2 and len(cleaned_text) > 2 and not \
                cleaned_text[0].isdigit() and cleaned_text[-1].isdigit():
            for i in range(2, len(cleaned_text)):
                word = cleaned_text[:i]
                if " " + word + " " in original_paragraph[
                                       end_previous_timex:] or " " + word + "." in original_paragraph[
                                                                                   end_previous_timex:] or " " + word + "," in original_paragraph[
                                                                                                                               end_previous_timex:]:
                    cleaned_text = word
                    beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
                    break;

        # if its just a single word ending with digits
        if beginning_timex == -1 and len(cleaned_text.split(" ")) < 2:
            for i in range(2, len(cleaned_text)):
                word = cleaned_text[:i]
                if " " + word + " " in original_paragraph[
                                       end_previous_timex:] or " " + word + "." in original_paragraph[
                                                                                   end_previous_timex:] or " " + word + "," in original_paragraph[
                                                                                                                               end_previous_timex:]:
                    cleaned_text = word
                    beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
                    break;
        # if you can not find it, see if you can match the first word in the multi word one
        if beginning_timex == -1 and len(cleaned_text.split(" ")) > 1:
            for word in cleaned_text.split(" "):
                if word in original_paragraph[end_previous_timex:] and word not in ["a", "-", ".", "the",
                                                                                    "in", "then", "'s",
                                                                                    "have", "at", "be"]:
                    cleaned_text = word
                    beginning_timex = original_paragraph[end_previous_timex:].find(cleaned_text)
                    break;

        if beginning_timex == -1 and cleaned_text.lower() in original_paragraph[
                                                             end_previous_timex:].lower():
            beginning_timex = original_paragraph[end_previous_timex:].lower().find(cleaned_text.lower())

        # avoid tag repetion
        if cleaned_text == previous_timex_cleaned_text:
            continue

        previous_timex_cleaned_text = cleaned_text

        if beginning_timex == -1:  # if you still do not find a match, just forget it.
            continue

        index = index + 1
        beginning_timex = beginning_timex + end_previous_timex
        # if the word ended with one of these symbols do not put a space after timex tag
        if original_paragraph[beginning_timex - 1:beginning_timex] in ["\n", "'", "-", ",", "\"",
                                                                       "("] or original_paragraph[
                                                                               beginning_timex - 1:beginning_timex].isdigit():
            new_text += f'{input_text[end_previous_timex:beginning_timex]}<TIMEX3 tid="t{index + 1}" ' \
                        f'type="{timex.attrs["type"].upper()}" value="{timex.attrs["value"].strip().replace("</timex3>", "").replace("<", "").replace(">", "").replace(" ", "").upper()}">{input_text[beginning_timex:beginning_timex + len(cleaned_text)]}</TIMEX3>'

        else:  # otherwises put a space
            new_text += f'{input_text[end_previous_timex:beginning_timex]} <TIMEX3 tid="t{index + 1}" ' \
                        f'type="{timex.attrs["type"].upper()}" value="{timex.attrs["value"].strip().replace("</timex3>", "").replace("<", "").replace(">", "").replace(" ", "").upper()}">{input_text[beginning_timex:beginning_timex + len(cleaned_text)]}</TIMEX3>'

        end_previous_timex = beginning_timex + len(cleaned_text)

    new_text = new_text + input_text[end_previous_timex:]
    return new_text

def clean_predictions(decoded_preds):
    """
    clean the seq2seq predictions
    :param decoded_preds: the raw predictionss
    :return: cleaned text
    """

    # take care of tag formatiing

    decoded_preds = decoded_preds.replace("&gt;", ">").replace("&lt;", "<")
    decoded_preds = decoded_preds.replace(" < / timex3  ", " </timex3") \
        .replace("< timex3 ", "<timex3 ") \
        .replace("< / timex3 >", "</timex3>") \
        .replace("/ timex3 >", "</timex3>") \
        .replace(" </timex>", " </timex3>") \
        .replace("</timex3></timex3>", "</timex3>") \
        .replace("timex&gt;", "</timex3>") \
        .replace("timex ", "</timex3> ").replace("</time x3>","</timex3>")
    decoded_preds = re.sub(r"([a-z])timex3>", "\g<1> </timex3>", decoded_preds)
    decoded_preds = re.sub(r"</timex3></timex3>", "</timex3>", decoded_preds)
    decoded_preds = re.sub(r"timex>", "</timex3>", decoded_preds)
    decoded_preds = re.sub(r" </ </timex3>", "</timex3>", decoded_preds)

    # remove the most prominent hallucinations.
    decoded_preds = decoded_preds.replace('type="D"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type="DATEATION"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type="DUR"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type="S"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="S"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="TIMEATE"', 'type="TIME"')
    decoded_preds = decoded_preds.replace('type="TIMEATEATION"', 'type="TIME"')
    decoded_preds = decoded_preds.replace('type="TIMEURATION"', 'type="TIME"')
    decoded_preds = decoded_preds.replace('value="PENT_REF"', 'value="PRESENT_REF"')
    decoded_preds = decoded_preds.replace('value="PRESXD"', 'value="PRESENT_REF"')
    decoded_preds = decoded_preds.replace('value="PRESENTD"', 'value="PRESENT_REF"')
    decoded_preds = decoded_preds.replace('type="SETURY"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="SETATEY"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="SETATE"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="DATEATE"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type="2018ATE"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type="SETURATION"', 'type="DURATION"')
    decoded_preds = decoded_preds.replace('type="SETATEATION"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="SETSETY"', 'type="SET"')
    decoded_preds = decoded_preds.replace('fre="SET"', 'type="SET"')
    decoded_preds = decoded_preds.replace('fre="D"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type="2014ATE"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('quan = " set "', 'type="SET"')
    decoded_preds = decoded_preds.replace('quant="D"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('quan=" duration "', 'type="DURATION"')
    decoded_preds = decoded_preds.replace('quan = " duration "', 'type="DURATION"')
    decoded_preds = decoded_preds.replace('fr=" date "', 'type="DATE"')
    decoded_preds = decoded_preds.replace('nowENT', 'now"')
    decoded_preds = decoded_preds.replace('WeekEND', 'Weekends"')
    decoded_preds = decoded_preds.replace('yesterdayENT', 'yesterday"')
    decoded_preds = decoded_preds.replace('yesterdayXX', 'yesterday"')
    decoded_preds = decoded_preds.replace('type = "date"', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type = " date "', 'type="DATE"')
    decoded_preds = decoded_preds.replace('type = "set"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type = " set "', 'type="SET"')
    decoded_preds = decoded_preds.replace('type = " duration "', 'type="DURATION"')
    decoded_preds = decoded_preds.replace('type = "duration"', 'type="DURATION"')
    decoded_preds = decoded_preds.replace('type = "time"', 'type="TIME"')
    decoded_preds = decoded_preds.replace('type = " time "', 'type="TIME"')
    decoded_preds = decoded_preds.replace('type = "setate"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type="SETVERY"', 'type="SET"')
    decoded_preds = decoded_preds.replace('type=""', 'type="DATE"')
    decoded_preds = decoded_preds.replace('quant="SET"', 'type="SET""')
    decoded_preds = decoded_preds.replace('fr = " set "', 'type="SET""')
    decoded_preds = decoded_preds.replace('fre="D" "', 'type="DATE""')
    decoded_preds = decoded_preds.replace('2014timex3', '2014</timex3>')
    decoded_preds = decoded_preds.replace('yesterdayterday', 'yesterday')
    decoded_preds = decoded_preds.replace('tomorrowENT', 'tomorrow')
    decoded_preds = decoded_preds.replace('tomorroworrow', 'tomorrow')
    decoded_preds = decoded_preds.replace('tomorrowXX', 'tomorrow')
    decoded_preds = decoded_preds.replace('todayorrow', 'tomorrow')
    decoded_preds = decoded_preds.replace('summermer', 'summer')
    decoded_preds = decoded_preds.replace('summerUT', 'summer')
    decoded_preds = decoded_preds.replace('summerSU', 'summer')
    decoded_preds = decoded_preds.replace('tomXX', 'tomorrow')
    decoded_preds = decoded_preds.replace('tom60', 'tomorrow')
    decoded_preds = re.sub('<timex3>', '</timex3>', decoded_preds)
    decoded_preds = decoded_preds.replace('<timex3 > = " date "', '<timex3  type="DATE"')
    decoded_preds = decoded_preds.replace('<timex3> = " date "', '<timex3  type="DATE"')
    decoded_preds = decoded_preds.replace('quan=" duration "', 'type="DURATION"')
    decoded_preds = decoded_preds.replace('fr =" date "', 'type="DATE"')
    decoded_preds = decoded_preds.replace('fr = " date "', 'type="DATE"')

    # some more tag formating
    decoded_preds = decoded_preds.replace(':">">">', '')
    decoded_preds = decoded_preds.replace('>>', '>')
    decoded_preds = decoded_preds.replace('":">', '">')
    decoded_preds = decoded_preds.replace('P3:">:">-', 'P3')
    decoded_preds = decoded_preds.replace('</ ', '')
    decoded_preds = re.sub(r"\"\>[\w\:\-]+\"\>", '">', decoded_preds)
    decoded_preds = re.sub(r"\<\/[\w\-\:]+\<\/", '</', decoded_preds)
    decoded_preds = re.sub(r"\"\>XX\-", '">', decoded_preds)
    decoded_preds = re.sub(r'\">:\">', '">', decoded_preds)
    decoded_preds = re.sub(r':timex3>.', '</timex3>', decoded_preds)
    decoded_preds = re.sub('\w+timex3\stype', '<timex3 type', decoded_preds)
    decoded_preds = re.sub('\d+timex3\stype', '<timex3 type', decoded_preds)
    decoded_preds = re.sub('<timex3>', '</timex3>', decoded_preds)
    decoded_preds = re.sub('--timex3>', '</timex3>', decoded_preds)
    decoded_preds = decoded_preds.replace('<timex3> = " date "', '<timex3  type="DATE"')
    truncated_values = re.findall(r'value=\"[\w\-\:]+\s', decoded_preds)
    for v in truncated_values:
        decoded_preds = decoded_preds.replace(v, v + '">')

    concatanated_value = re.findall(r'\w+\-timex3\>', decoded_preds)
    for v in concatanated_value:
        decoded_preds = decoded_preds.replace(v, v.split("-")[0] + '"<' + v.split("-")[1])

    additional_white_space = re.findall(r'value=\"[\d\w\:\-\_]+\s\"', decoded_preds)
    for v in additional_white_space:
        decoded_preds = decoded_preds.replace(v, v.replace(" ", ""))

    double_end = re.findall(r'\"\>[\w]+\"\>', decoded_preds)
    for v in double_end:
        decoded_preds = decoded_preds.replace(v, v[2:])

    strange_values = re.findall(r'\"\:\"\>', decoded_preds)
    for v in strange_values:
        decoded_preds = decoded_preds.replace(v, '">')

    decoded_preds = re.sub(r' <\n', '\n', decoded_preds)
    decoded_preds = re.sub(r'  ', ' ', decoded_preds)

    decoded_preds = re.sub(r'\b(\w+)( \1\b)+', r'\1', decoded_preds)


    return decoded_preds



def preprocess_group(annotation_group: str) -> str:
    # Fix border cases of inconsistent tokens
    if "-" in annotation_group:
        annotation_group = annotation_group.replace(" - ", "-")
        annotation_group = annotation_group.replace("- ", "-")
        annotation_group = annotation_group.replace(" -", "-")
        annotation_group = annotation_group.replace("13 february-", "13 february -")
        annotation_group = annotation_group.replace("run-morning", "run - morning")
        annotation_group = annotation_group.replace("-morning", "- Morning")
        annotation_group = annotation_group.replace("next year-", "next year -")
        annotation_group = annotation_group.replace("the night of 13 february -14 february", "the night of 13 february - 14 february")
        annotation_group = annotation_group.replace("a 50-mile ( 80 km", "a 50-mile (80 km")

    if ":" in annotation_group:
        annotation_group = annotation_group.replace(" : ", ":")
        annotation_group = annotation_group.replace(": ", ":")
        annotation_group = annotation_group.replace(" :", ":")
    if "." in annotation_group:
        annotation_group = annotation_group.replace(" . ", ". ")
        annotation_group = annotation_group.replace("7. 30", "7.30")  # manual fix of
        annotation_group = annotation_group.replace(" .", ".")
        annotation_group = annotation_group.replace(". s.", ".s.")
        annotation_group = annotation_group.replace(". 2", ".2")
        annotation_group = annotation_group.replace(". 1bn", ".1bn")
        annotation_group = annotation_group.replace(". 8", ".8")
        annotation_group = annotation_group.replace(". 5", ".5")
        annotation_group = annotation_group.replace(". 6", ".6")
        annotation_group = annotation_group.replace(". d. p", ".d.p")
        annotation_group = annotation_group.replace(". 4", ".4")
        annotation_group = annotation_group.replace(". b. m.", ".b.m.")
        annotation_group = annotation_group.replace("4. 30am", "4.30am")
        annotation_group = annotation_group.replace("23. 03.2015", "23.03.2015")
        annotation_group = annotation_group.replace("feb.28", "feb. 28")
        annotation_group = annotation_group.replace(". 30am", ".30am")

    if "," in annotation_group:
        annotation_group = annotation_group.replace(" , ", ", ")
        annotation_group = annotation_group.replace(" ,", ",")
        annotation_group = annotation_group.replace("1, 460", "1,460")
        annotation_group = annotation_group.replace(", 460", ",460")
        annotation_group = annotation_group.replace(", 000", ",000")
        annotation_group = annotation_group.replace(", 445", ",445")
        annotation_group = annotation_group.replace(", 109", ",109")

    if "'" in annotation_group:
        annotation_group = annotation_group.replace("' ", "'")
        annotation_group = annotation_group.replace("day 's", "day's")
        annotation_group = annotation_group.replace("japan '", "japan'")
        annotation_group = annotation_group.replace("day '", "day'")
        annotation_group = annotation_group.replace("mussolini 's", "mussolini's")
        annotation_group = annotation_group.replace("mussolini '", "mussolini'")
        annotation_group = annotation_group.replace("five years '", "five years'")

    if "\"" in annotation_group:
        annotation_group = annotation_group.replace("\" black period", "\"black period")
        annotation_group = annotation_group.replace("black period \"", "black period\"")
        annotation_group = annotation_group.replace("period \" of the war", "period\" of the war")
        annotation_group = annotation_group.replace("the \" black", "the \"black")

    if "/" in annotation_group:
        annotation_group = annotation_group.replace(" / ", "/")
        annotation_group = annotation_group.replace("/ ", "/")
        annotation_group = annotation_group.replace("/ 2", "/2")
    if "(" in annotation_group:
        annotation_group = annotation_group.replace("( ", "(")
    if ")" in annotation_group:
        annotation_group = annotation_group.replace(" )", ")")
    if "\\" in annotation_group:
        annotation_group = annotation_group.replace(" \\ ", "\\")
    return annotation_group


def get_vote_type(votes: List[str]) -> str:
    # Since Python 3.7, Counter maintains insertion order.
    # Since we want to preserve the first label in case of ties, we need to reverse the votes,
    # as we previously recorded them backwards.
    votes = [get_pred_type(vote) for vote in reversed(votes)]
    majority = Counter(votes).most_common(1)
    majority_label = majority[0][0]

    return majority_label


def get_pred_type(prediction: str) -> str:

    if prediction == "O" or prediction=="[PAD]" or prediction=="[SEP]":
        return prediction
    else:
        return prediction.split("-")[1]

def get_model_and_tokenizers(args):
    if args.model_type == "date":
        model = BERTWithDateLayerTokenClassification.from_pretrained(args.model_dir)
        date_tokenizer = NumBertTokenizer("./data/vocab_date.txt")
    elif args.model_type == "normal":
        model = BertForTokenClassification.from_pretrained(args.model_dir)
        date_tokenizer = None
    elif args.model_type == "crf":
        model = BERT_CRF_NER.from_pretrained(args.model_dir)
        date_tokenizer = None
    elif args.model_type == "german":
        model = AutoModelForTokenClassification.from_pretrained(args.model_dir)
        date_tokenizer = None
    else:
        raise ValueError("Incorrect model type specified")

    text_tokenizer = AutoTokenizer.from_pretrained(args.model_dir, use_fast=False)

    return model, date_tokenizer, text_tokenizer


def place_timex_tag(raw_text, tagged_text, annotation_group, annotation_id, annotation_type):
    annotation_group = preprocess_group(annotation_group)

    # Assert correct location irrespective of casing
    start_idx = raw_text.lower().find(annotation_group.lower())
    if start_idx == -1:
        print(f"Remaining raw text: {raw_text}")
        raise ValueError(f"Could not find current annotation group \"{annotation_group}\" in text.")
    # Cannot directly write out annotation_group due to potentially different casing
    tagged_text = f"{tagged_text}{raw_text[:start_idx]}" \
                  f"<TIMEX3 tid=\"t{annotation_id}\" type=\"{annotation_type}\" value=\"\">" \
                  f"{raw_text[start_idx:start_idx+len(annotation_group)]}" \
                  f"</TIMEX3>"
    raw_text = raw_text[start_idx + len(annotation_group):]

    return raw_text, tagged_text, annotation_id+1



def merge_tokens(bpe_text, bpe_predictions, id2label, tokenizer) -> List[Tuple[str, str]]:
    """
    BPEs are merged into single tokens in this step, where corresponding predictions get aggregated
    into a single token by virtue of majority voting.
    Even breaks (e.g., something like "me ##ssa ##ge | B-DATE, O, I-DURATION") will be decided by the first tag result,
    in this case "DATE" because of the tag of "me". If there is no B-tag in the current instance at all,
    the first token still decides. Note that there are no ambiguities about the B/I distinction here, since we only
    look at multi-BPE tokens, and not at tags spanning multiple *full-word* tokens.
    TODO: Note that this function gets rid of the B/I distinction for downstream tasks as well currently!
      This can be changed by not abstracting the vote to the type only, and still carrying the B-/I- prefix with it.
    :param bpe_text:
    :param bpe_predictions:
    :param id2label: Turning predicted ids back to the actual labels
    :param tokenizer: Tokenizer required to translate token ids back to the words themselves.
    :return: List of tuples containing (token, type_label) pairs.
    """
    merged_tokens = []
    prev_multi_instance = False
    current_multi_vote = []
    current_multi_token = ""
    # Iterate in reverse to immediately see when we deal with a multi-BPE instance and start voting
    for token_id, pred_id, in zip(reversed(bpe_text), reversed(bpe_predictions)):
        token = tokenizer.ids_to_tokens[int(token_id)]

        pred = id2label[int(pred_id)]

        # Skip special tokens
        if token in ("[PAD]", "[CLS]", "[SEP]"):
            continue

        # Instance for multi-BPE token
        if token.startswith("##"):
            current_multi_token = f"{token[2:]}{current_multi_token}"
            current_multi_vote.append(pred)
        else:
            # Need to merge votes
            if current_multi_token:
                current_multi_token = f"{token}{current_multi_token}"
                current_multi_vote.append(pred)
                merged_tokens.append((current_multi_token, get_vote_type(current_multi_vote)))
                current_multi_token = ""
                current_multi_vote = []
            # Previous token was single word anyways
            else:
                merged_tokens.append((token, get_pred_type(pred)))

    # Bring back into right order for later processing
    merged_tokens.reverse()
    return merged_tokens


def insert_tags_in_raw_text(raw_text: str, merged_tokens: List[Tuple[str, str]], annotation_id: int = 1):
    """
    This takes the original raw text, and iterates over it to insert the predicted tags at the right positions.
    :param raw_text:
    :param merged_tokens:
    :param annotation_id
    :return:
    """
    tagged_text = ""
    prev_tag = "O"
    current_annotation_group = ""

    for token, tag in merged_tokens:
        # If we still have the same tag, then we either just extend the annotation (not "O"), or just leave it ("O").
        if tag == prev_tag:
            if tag != "O" and tag !="[PAD]":
                current_annotation_group += f" {token}"
            continue

        else:
            # This means we're just opening an annotation, e.g., "O DATE"
            if prev_tag != "O" and prev_tag!="[PAD]":
                raw_text, tagged_text, annotation_id = place_timex_tag(raw_text, tagged_text, current_annotation_group,
                                                                       annotation_id, prev_tag)
                # Immediately store the next token, as it is also tagged, but in a different group
                if tag != "O" and prev_tag!="[PAD]" :
                    current_annotation_group = token
                else:
                    current_annotation_group = ""
            else:
                current_annotation_group = token

            prev_tag = tag

    tagged_text += raw_text
    return tagged_text, annotation_id



