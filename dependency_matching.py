'''
Created on Nov 8, 2019
Sample structure of run file run.py

@author: cxchu
'''

import sys

import spacy 
import nltk

from spacy.matcher import DependencyMatcher 
#from spacy import displacy 
from nltk.corpus import wordnet as wn

def your_typing_function(input_file, result_file):

    nlp = spacy.load("en_core_web_sm")
    matcher = DependencyMatcher(nlp.vocab)

    pattern = [
        [
            {"RIGHT_ID": "anchor_root", "RIGHT_ATTRS": {"LEMMA": "be"}},
            {"LEFT_ID": "anchor_root", "REL_OP": ">", "RIGHT_ID": "root_attr", "RIGHT_ATTRS": {"DEP": "attr"}}
        ],
        [
            {"RIGHT_ID": "root_include", "RIGHT_ATTRS": {"LEMMA": "include"}},
            {"LEFT_ID": "root_include", "REL_OP": ">", "RIGHT_ID": "include_dobj", "RIGHT_ATTRS": {"DEP": {"IN": ["dobj", "nsubj"]}}}
        ]
    ]

    matcher.add("typing_patterns", pattern)

    with open(input_file, 'r', encoding='utf8') as fin, \
         open(result_file, 'w', encoding='utf8') as fout:

        for line in fin:

            comps = line.rstrip().split("\t")

            if len(comps) != 3:
                continue

            sent_id = int(comps[0])
            entity = comps[1]
            sentence = comps[2]

            doc = nlp(sentence)

            types = []

            matches = matcher(doc)

            for match_id, tokens in matches:
                for token_index in tokens[1:]:
                    types.append(doc[token_index].lemma_)

            types = list(set(types))

            fout.write(str(sent_id) + "\t" + str(types) + "\n")

    
    
'''
*** other code if needed
'''    
    
    
'''
main function
'''
if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError('Expected exactly 2 argument: input file and result file')
    your_typing_function(sys.argv[1], sys.argv[2])

#References:
#https://spacy.io/usage/rule-based-matching
#https://www.youtube.com/watch?v=gUbMI52bIMY
#https://github.com/explosion/spaCy/discussions/10396
#https://sp1819.github.io/wordnet_spacy.pdf
