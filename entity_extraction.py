'''
Created on Nov 25, 2019
Sample structure of run file run.py

@author: cxchu
@editor: ghoshs
'''
import sys
import csv

import re
import spacy

from spacy.matcher import Matcher
from dateutil.parser import parse

nlp = spacy.load('en_core_web_sm')

def your_extracting_function(input_file, result_file):
    """
    Reads an input CSV file and extracts structured information about entities.
    Saves the results to result_file in CSV format.
    """

    # Prepare CSV output
    with open(result_file, 'w', encoding='utf8', newline="") as fout:
        headers = ['entity','dateOfBirth','nationality','almaMater','awards','workPlaces']
        writer = csv.writer(fout)
        writer.writerow(headers)

        with open(input_file, 'r', encoding='utf8') as fin:
            reader = csv.reader(fin)
            next(reader)  # skip header row

            for row in reader:
                entity, abstract = row[0], row[1]

                doc = nlp(abstract)

                # Extract information using refactored functions
                dateOfBirth = extract_dob(doc)
                nationality = extract_nationality(doc)
                almaMater = extract_almamater(doc)
                awards = extract_awards(doc)
                workPlaces = extract_workplace(doc)

                # Write comma-separated values; 'NA' if no data found
                writer.writerow([
                    entity,
                    ",".join(dateOfBirth) if dateOfBirth else "NA",
                    ",".join(nationality) if nationality else "NA",
                    ",".join(almaMater) if almaMater else "NA",
                    ",".join(awards) if awards else "NA",
                    ",".join(workPlaces) if workPlaces else "NA"
                ])

# -------------------------
# Extract Date of Birth
# -------------------------
def extract_dob(doc):
    dob = []
    matcher = Matcher(nlp.vocab)

    patterns = [
        [{'LOWER':'born'}, {'POS':'NUM'}, {'POS':'PROPN'}, {'POS':'NUM'}],
        [{'LOWER':'born'}, {'POS':'PROPN'}, {'POS':'NUM'}, {'POS':'PUNCT','OP':'*'}, {'POS':'NUM'}]
    ]
    matcher.add("DOB", patterns)
    matches = matcher(doc)

    for _, start, end in matches:
        span = doc[start:end]
        try:
            date = parse(span.text)
            dob.append(date.strftime('%Y-%m-%d'))
        except:
            continue

    return list(set(dob))

# -------------------------
# Extract Nationality
# -------------------------
def extract_nationality(doc):
    nationality = []
    matcher = Matcher(nlp.vocab)

    # Load country dictionary (demonyms -> countries)
    country_dict = {}
    try:
        with open('demonyms.txt', encoding='utf8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    country_dict[row[0].strip()] = row[1].strip()
    except FileNotFoundError:
        print("Warning: demonyms.txt not found. Nationality extraction may be incomplete.")

    # Patterns to identify nationality in sentences
    patterns = [
        [{'LEMMA':'be'}, {'ORTH': {'IN': ['a','an']}}, {'POS':'ADJ'}],
        [{'LOWER':'born'}, {'LOWER':'in'}, {'POS':'PROPN'}, {'POS':'ADP','OP':'*'}]
    ]
    matcher.add("Nationality", patterns)
    matches = matcher(doc)

    for _, start, end in matches:
        span = doc[start:end]
        for word in span.text.split():
            if word[0].isupper() and word.lower() != 'born':
                nationality.append(country_dict.get(word, word))

    return list(set(nationality))

# -------------------------
# Extract Alma Mater
# -------------------------
def extract_almamater(doc):
    almaMater = []
    keywords = ['graduated', 'educated', 'study', 'studied', 'degree', 'doctorate', 'scholarship', 'PhD', 'honorary', 'B.A.', 'B.S.']

    for sent in doc.sents:
        sent_text = sent.text.lower()
        if any(k.lower() in sent_text for k in keywords):
            for ent in sent.ents:
                if ent.label_ == "ORG":
                    almaMater.append(ent.text.replace("the","").strip())

    return list(set(almaMater))

# -------------------------
# Extract Awards
# -------------------------
def extract_awards(doc):
    awards = []
    keywords = ['award','prize','medal','fellowship','emeritus','doctorate','preis']

    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        if any(k.lower() in chunk_text for k in keywords):
            awards.append(chunk.text.replace("the","").strip())

    return list(set(awards))

# -------------------------
# Extract Workplaces
# -------------------------
def extract_workplace(doc):
    workPlace = []
    keywords = ['work','worked','working','position','professor','lecturer','founder','university','college','laboratory','institute']

    for ent in doc.ents:
        ent_text = ent.text.lower()
        if any(k.lower() in ent_text for k in keywords) and ent.label_ == "ORG":
            workPlace.append(ent.text.replace("the","").strip())

    return list(set(workPlace))


'''
main function
'''
if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError('Expected exactly 2 argument: input file and result file')
    your_extracting_function(sys.argv[1], sys.argv[2])


#References:
#https://spacy.io/usage/rule-based-matching
#https://www.analyticsvidhya.com/blog/2020/06/nlp-project-information-extraction/
#https://github.com/knowitall/chunkedextractor/blob/master/src/main/resources/edu/knowitall/chunkedextractor/demonyms.csv
#https://stackoverflow.com/questions/6740918/creating-a-dictionary-from-a-csv-file
#https://stackoverflow.com/questions/2265357/parse-date-string-and-change-format
