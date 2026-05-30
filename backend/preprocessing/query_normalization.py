"""
Since the query in question is a social media post we propose the following

-> removing emoticons and hashtags
-> social media relevant stopwords ("omg","ngl",...,etc.)
-> removing elongation (e.g. "I lovee")

"""

import unicodedata
import emoji
import re
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords', quiet=True)

ENGLISH_STOPWORDS = set(stopwords.words('english'))

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
    "link", "bio", "dm",

    # social media post openers that add no retrieval signal
    "just", "turns", "out", "whoa", "wow",
    "heard", "saw", "learned", "read", "found",
    "did", "you", "know", "apparently", "wait",
    "wild", "mind", "blown", "guys", "everyone",
}

ALL_STOPWORDS = ENGLISH_STOPWORDS | SOCIAL_STOPWORDS

def clean_unicode_and_layout(text: str) -> str:
    # Normalize unicode (handles hidden formatting tokens)
    text = unicodedata.normalize('NFKC', text)
    # Strip URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Strip Twitter/X style artifacts like pipes used for layout
    text = re.sub(r'\|', ' ', text)
    # Narrow no-break space (\u202f) and other exotic whitespace to regular space
    text = re.sub(r'[\u00a0\u202f\u2009\u200b\u2060]', ' ', text)
    return text

def remove_emojis(text: str) -> str:
    text = emoji.replace_emoji(text, "")
    return re.sub(r'\s+', ' ', text)

def translate_emojis(text: str) -> str:
    text = emoji.demojize(text, delimiters=("", " "))
    return re.sub(r'\s+', ' ', text)

def remove_elongation(query: str) -> str:

    # we check for occurrences of a character more than two times
    # we reduce to one if more than two times
    # if only two times we don't change anything
    # basing this heuristic on an observation since elongation is hardly ever done through a single repetition

    length = len(query)
    modified = []
    prev = None
    for i, ch in enumerate(query):
        if ch != prev:
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

def normalize_query(query: str) -> list:

    # converting everything to lowercase
    query = query.lower()

    # removing hashtags and mentions
    query = re.sub(r'[#@]\w+', '', query)

    # remove elongation
    query = remove_elongation(query)

    # normalize non-standard dashes and hyphens to a space (not hyphen)
    # catches em-dash (—), en-dash (–), non-breaking hyphen (‑), minus (−)
    # using space so "whoa—by" splits to "whoa by" instead of "whoa-by"
    query = re.sub(r'[\u2012\u2013\u2014\u2015\u2212\u2011\-]', ' ', query)

    # strip tilde approximation prefix from numbers (~67% → 67%)
    query = re.sub(r'~\s*', '', query)

    # detach units glued to numbers but preserve decimals (2.3M → 2.3 m, NOT 13.8 → 13. 8)
    # only split when a letter directly follows digits (no dot between them)
    query = re.sub(r'(\d)([a-zA-Z°×])', r'\1 \2', query)
    query = re.sub(r'([a-zA-Z°×])(\d)', r'\1 \2', query)

    # strip standalone special symbols that carry no lexical meaning for BM25
    query = re.sub(r'[×°≥≤→←✅⚡★•·%$^*\\+=<>]', ' ', query)

    # remove emojis
    query = remove_emojis(query)

    # removing stray formatting/layout characters
    query = clean_unicode_and_layout(query)

    # punctuation cleanup — strip punctuation attached to token boundaries
    # removes trailing/leading punctuation from tokens (yay! → yay, cancer, → cancer)
    query = re.sub(r'[.,!?;:\'\"]+([\s]|$)', r'\1', query)
    query = re.sub(r'(^|[\s])[.,!?;:\'\"]+', r'\1', query)

    # ensure space after punctuation if followed by letters/digits (fixes yep.there)
    query = re.sub(r'([.,!?])(?=[A-Za-z])', r'\1 ', query)

    # clean up edge cases like words directly touching parenthetical boundaries
    query = re.sub(r'(?<=\w)\)', r') ', query)

    # strip remaining standalone punctuation tokens
    query = re.sub(r'\s[.,!?;:\-\'\"]\s', ' ', query)

    # stripping end spaces and removing multiple spaces
    query = re.sub(r'\s+', ' ', query)
    query = query.strip()

    # splitting into tokens
    tokens = query.split(' ')

    # filter empty strings that can result from aggressive regex substitution
    tokens = [token for token in tokens if token]

    # filter both english stopwords and social media stopwords
    tokens = [token for token in tokens if token not in ALL_STOPWORDS]

    # normalization log
    print("NORMALIZED QUERY: ", tokens)

    return tokens

if __name__ == '__main__':
    print(normalize_query("ngl twin COVID vaccines workkkk 💉🦠🔥 yay!"))
    print(normalize_query("Turns out ~67% efficacy after two weeks – even severe cases down ~77% 😷 #VaccinesWork"))
    print(normalize_query("Whoa—by 2050 we could have 13.8M Americans 65+ with Alzheimer's 😱 #Aging"))