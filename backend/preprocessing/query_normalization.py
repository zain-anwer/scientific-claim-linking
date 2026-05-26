"""
Since the query in question is a social media post we propose the following

-> removing emoticons and hashtags
-> social media relevant stopwords ("omg","ngl",...,etc.)
-> removing elongation (e.g. "I lovee")

"""

import unicodedata
import emoji
import re

SOCIAL_STOPWORDS = {
    # agreement / filler
    "yeah", "yep", "yup", "nah", "nope",
    "ok", "okay", "alright", "bro", "bruh",
    "fam", "homie", "dude", "man", "girl",
    "twin", "bestie",

    # slang
    "omg", "ngl", "lol", "lmao", "brb",
    "idk", "imo", "imho", "btw", "smh",
    "tbh", "rofl", "ikr", "fr",

    # reactions
    "lol", "lmao", "lmfao", "rofl",
    "haha", "hehe", "yay", "omg",
    "wtf", "fr", "frfr", "ong",
    "deadass", "lowkey", "highkey",

    # emphasis noise
    "literally", "actually", "seriously",
    "basically", "honestly",

    # engagement bait
    "subscribe", "follow", "retweet",
    "repost", "share", "like",

    # internet fillers
    "idk", "imo", "imho", "tbh",
    "btw", "ngl", "asap",

    # vague positivity
    "fire", "lit", "cool", "awesome",
    "amazing", "nice", "crazy",

    # emotional noise
    "ugh", "oof", "yikes",

    # conversational clutter
    "uh", "umm", "hmm",

    # elongated affirmations
    "ya", "yo",

    # common spam/social tokens
    "link", "bio", "dm"
}

def clean_unicode_and_layout(text: str) -> str:
    # Normalize unicode (handles hidden formatting tokens)
    text = unicodedata.normalize('NFKC', text)
    # Strip URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Strip Twitter/X style artifacts like pipes used for layout
    text = re.sub(r'\|', ' ', text)
    return text

def remove_emojis(text : str) -> str:
    text = emoji.replace_emoji(text,"")
    return re.sub(r'\s+',' ',text)

def translate_emojis(text : str) -> str:
    text = emoji.demojize(text,delimiters=(""," "))
    return re.sub(r'\s+',' ',text)
    
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

    # removing hashtags and mentions
    query = re.sub(r'[#@]\w+','',query)

    # remove elongation
    query = remove_elongation(query)

    # remove emojis
    query = remove_emojis(query)

    # removing stray formatting/layout characters
    query = clean_unicode_and_layout(query)
    
    # punctuation cleanup 
    # Ensure space after punctuation if followed by letters/digits (fixes yep.there)
    query = re.sub(r'([.,!?])(?=[A-Za-z0-9])', r'\1 ', query)
    # Clean up edge cases like words directly touching parenthetical boundaries
    query = re.sub(r'(?<=\w)\)', r') ', query)

    # stripping end spaces and removing multiple spaces
    query = re.sub(r'\s+',' ',query)
    query = query.strip()

    # splitting into tokens
    tokens = query.split(' ')

    tokens = [token for token in tokens if token not in SOCIAL_STOPWORDS]

    # normalization log
    print("NORMALIZED QUERY: ",tokens)

    return tokens

print(normalize_query("ngl twin COVID vaccines workkkk 💉🦠🔥 yay!"))
