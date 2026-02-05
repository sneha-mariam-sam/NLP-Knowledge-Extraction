"""
Barebone code created by: Tuan-Phong Nguyen
Date: 2022-06-03
"""

import logging
from typing import Dict, List, Tuple

from collections import Counter

import spacy
from spacy.matcher import Matcher

logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

def your_solution(animal: str, doc_list: List[Dict[str, str]]) -> List[Tuple[str, int]]:
    """
    Extract foods eaten by the given animal from documents.

    :param animal: Animal name.
    :param doc_list: List of documents, each a dict with keys "text", "url", "title".
    :return: List of (food_item, frequency) tuples.
    """

    # Define patterns for Matcher
    matcher = Matcher(nlp.vocab)

    patterns = [
        # Pattern: animal eats NOUN
        [{"LEMMA": "eat"}, {"POS": "NOUN"}],
        # Pattern: animal feeds on NOUN
        [{"LEMMA": "feed"}, {"POS": "ADP", "OP":"*"}, {"POS": "NOUN"}],
        # Pattern: animal munches NOUN/ADJ
        [{"LEMMA": {"IN": ["munch", "consume"]}}, {"POS": "ADJ", "OP":"*"}, {"POS": "NOUN"}],
        # Pattern: optional animal name + eat/feeds + object
        [{"LOWER": {"IN": [animal.lower(), animal.lower()+"s"]}}, {"LEMMA": {"IN": ["eat","feed"]}}, {"POS": "NOUN"}],
    ]

    matcher.add("DietPatterns", patterns)

    diets = []

    for doc_dict in doc_list:
        text = doc_dict["text"]
        doc = nlp(text)
        matches = matcher(doc)

        for match_id, start, end in matches:
            span = doc[start:end]
            # Clean the span text and remove punctuation
            food = span.text.lower().strip()
            food = "".join([c for c in food if c.isalnum() or c.isspace()])
            if food and food != animal.lower():
                diets.append(food)

    # Count frequency
    return Counter(diets).most_common()
