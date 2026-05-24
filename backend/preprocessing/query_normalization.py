"""
Since the query in question is a social media post we propose the following

-> removing emoticons and hashtags
-> social media relevant stopwords ("omg","ngl",...,etc.)
-> removing elongation (e.g. "I lovee")
"""

import re

SLANG = {
    "omg", "ngl", "lol", "lmao", "brb",
    "idk", "imo", "imho", "btw", "smh",
    "tbh", "rofl", "ikr", "fr"
}

def remove_elongation(query : str) -> str:
    
    # we check for occurrences of a character more than two times
    # we reduce to one if more than two times
    # if only two times we don't change anything
    # basing this heuristic on an observation since elongation is hardly ever done through a single repetition

    length = len(query)
    modified = []
    prev = None
    for i,ch in enumerate(query):
        if ch != prev:
            # starting character of a potential elongation
            count = 0
            while i < length:
                if query[i] != ch:
                    break
                count += 1
                i += 1
            if count == 2:
                modified.append(ch)
                modified.append(ch)
            else:
                modified.append(ch)
        prev = ch

    return "".join(modified)

def normalize_query(query : str) -> list:
    
    # converting everything to lowercase
    query = query.lower()

    # remove elongation
    query = remove_elongation(query)

    # removing hashtags and mentions
    query = re.sub(r'[#@]\w+','',query)

    # stripping end spaces and removing multiple spaces
    query = re.sub(r'\s+',' ',query)
    query = query.strip()

    # splitting into tokens
    tokens = query.split(' ')

    tokens = [token for token in tokens if token not in SLANG]

    # normalization log
    print("NORMALIZED QUERY: ",tokens)

    return tokens



# sample program:
normalize_query("I hellooo don'ttt omggg #blacklivesmatter fr lmao know @maybe I laugh haha omg")
