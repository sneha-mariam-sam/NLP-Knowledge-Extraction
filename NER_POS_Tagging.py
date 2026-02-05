import spacy
import re
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# -------------------------
# Text Cleaning Function
# -------------------------

def clean_text(raw_text):

    text = BeautifulSoup(raw_text, "lxml").text

    text = text.replace("\n\n", "")
    text = text.replace("[", "").replace("]", "")

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"==.*?==+", "", text)
    text = re.sub(r"\{.*\}", "", text)
    text = re.sub(r"[\,\'\"\*\=:\(\)|]", "", text)

    return text

# -------------------------
# Named Entity Extraction
# -------------------------

def extract_named_entities(doc, title):

    entities = [ent.text for ent in doc.ents]

    freq = Counter(entities)

    entity_data = [(title, entity, count)
                   for entity, count in freq.items()]

    df = pd.DataFrame(
        entity_data,
        columns=["Title", "Named Entity", "Frequency"]
    )

    return df

# -------------------------
# POS Extraction
# -------------------------

def extract_pos_frequency(doc, title):

    pos_words = [
        token.text
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and token.pos_ in ["VERB", "ADJ"]
    ]

    freq = Counter(pos_words)

    pos_data = [(title, word, count)
                for word, count in freq.items()]

    df = pd.DataFrame(
        pos_data,
        columns=["Title", "Word", "Frequency"]
    )

    return df

# -------------------------
# Main Execution
# -------------------------

filename = "./wikipedia_dump/1.txt"

with open(filename, "r", encoding="utf8") as file:

    title = file.readline().strip()

    raw_text = file.read()

cleaned_text = clean_text(raw_text)

doc = nlp(cleaned_text)

entity_df = extract_named_entities(doc, title)

pos_df = extract_pos_frequency(doc, title)

# Save results
entity_df.to_csv(f"{title}.csv", index=False)

pos_df.to_csv("pos_frequency.csv", index=False)

print("Named entities extracted:", len(entity_df))
print("POS frequency extracted:", len(pos_df))

#References used to solve the problems:
#https://realpython.com/natural-language-processing-spacy-python/
#https://monkeylearn.com/blog/text-cleaning/
#https://stackoverflow.com/questions/36850550/split-the-result-of-counter
#https://www.javatpoint.com/how-to-create-a-dataframes-in-python
#https://stackoverflow.com/questions/37253326/how-to-find-the-most-common-words-using-spacy
