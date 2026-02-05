'''
Created on Nov 25, 2019
Sample structure of run file run.py

@author: cxchu
'''

import sys
import spacy

from spacy.matcher import Matcher
from spacy.util import filter_spans

nlp = spacy.load("en_core_web_sm")

def your_extracting_function(input_file: str, result_file: str):
    """
    Reads sentences from input_file and extracts SPO triples.
    Writes results to result_file.
    """
    with open(result_file, "w", encoding="utf8") as fout, open(input_file, "r", encoding="utf8") as fin:
        line_id = 1
        for line in fin:
            line = line.strip()
            if not line:
                continue

            doc = nlp(line)
            verbs = {}

            # Extract predicates (verbs)
            predicates = get_predicates(doc)
            if not predicates:
                continue

            # Choose the longest predicate as main
            full_predicate = get_full_predicate(predicates)
            key = str(full_predicate.root)
            if key not in verbs:
                verbs[key] = {"subject": "", "object": ""}

            noun_chunks = list(doc.noun_chunks)

            subject = get_subject(full_predicate, noun_chunks)
            object_ = get_object(full_predicate, noun_chunks)

            verbs[key]["subject"] = str(subject)
            verbs[key]["object"] = str(object_)

            # Format output compatible with OIE reader
            if subject and object_:
                fout.write(line + "\n")
                for k, v in verbs.items():
                    fout.write(f'{line_id}\t"{v["subject"]}"\t"{k}"\t"{v["object"]}"\t0\n')
                line_id += 1


# -------------------------
# Helper Functions
# -------------------------
def get_root(doc) -> spacy.tokens.Token:
    """Return the root verb of the sentence."""
    for token in doc:
        if token.dep_ == "ROOT":
            return token


def check_root(predicate, root) -> bool:
    """Check if the root verb is in the predicate span."""
    return root.i >= predicate.start and root.i <= predicate.end


def get_predicates(doc) -> List[spacy.tokens.Span]:
    """
    Match verb phrases in the sentence using SpaCy Matcher patterns.
    Returns a list of predicate spans.
    """
    root = get_root(doc)

    patterns = [
        [{"POS": "AUX"}, {"POS": "VERB"}, {"POS": "ADP"}],
        [{"POS": "NOUN"}, {"POS": "VERB"}, {"POS": "ADP", "OP": "*"}],
        [{"POS": "NOUN", "OP": "*"}, {"POS": "SCONJ"}, {"POS": "VERB"}, {"POS": "ADP"}, {"POS": "DET", "OP": "*"}],
        [{"POS": "VERB"}, {"POS": "NOUN", "OP": "*"}, {"POS": "ADP", "OP": "*"}, {"POS": "DET", "OP": "*"}],
        [{"POS": "SCONJ"}, {"POS": "VERB"}, {"POS": "ADP"}],
        [{"POS": "ADV"}, {"POS": "VERB"}, {"POS": "PRON", "OP": "*"}],
        [{"POS": "VERB", "OP": "?"}, {"POS": "ADV", "OP": "*"}, {"POS": "VERB", "OP": "+"}]
    ]

    matcher = Matcher(nlp.vocab)
    matcher.add("VerbPhrase", patterns)

    matches = matcher(doc)
    spans = [doc[start:end] for _, start, end in matches]

    # Filter overlapping spans and check root presence
    predicates = [span for span in filter_spans(spans) if check_root(span, root)]
    return predicates


def get_full_predicate(predicates: List[spacy.tokens.Span]) -> spacy.tokens.Span:
    """Return the longest predicate span."""
    return max(predicates, key=len)


def get_subject(predicate: spacy.tokens.Span, noun_chunks: List[spacy.tokens.Span]):
    """Return the noun chunk before the predicate as the subject."""
    for chunk in noun_chunks:
        if chunk.end <= predicate.start:
            return chunk
    return None


def get_object(predicate: spacy.tokens.Span, noun_chunks: List[spacy.tokens.Span]):
    """Return the noun chunk after the predicate as the object."""
    for chunk in noun_chunks:
        if chunk.start >= predicate.end:
            return chunk
    return None

'''
baseline implementation
'''
def spo_baseline(line):
    verbs = {}
    doc = nlp(line)
    for token in doc:
        key=token.head.text;
        if(token.head.pos_ == "VERB" and key not in verbs.keys()):
            verbs[key] = {"subject":"","object":""};
        if(token.dep_ == "nsubj" and token.head.pos_ == "VERB"):
            verbs[key]["subject"] = token.text;
        elif(token.dep_ == "dobj" and token.head.pos_ == "VERB"):
            verbs[key]["object"] = token.text;
    return verbs
      
'''
main function
'''
if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError('Expected exactly 2 argument: input file and result file')
    your_extracting_function(sys.argv[1], sys.argv[2])


#References:
#https://spacy.io/
#https://spacy.io/api/token
#https://stackoverflow.com/questions/47856247/extract-verb-phrases-using-spacy
#https://stackoverflow.com/questions/58844962/match-the-last-noun-before-a-particular-word
#https://subscription.packtpub.com/book/data/9781838987312/2/ch02lvl1sec14/extracting-noun-chunks
#https://subscription.packtpub.com/book/data/9781838987312/2/ch02lvl1sec15/extracting-entities-and-relations
