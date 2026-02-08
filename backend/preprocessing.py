from hazm import Normalizer, sent_tokenize, word_tokenize as hazm_word_tokenize
import re

def normalize_text(text, remove_punct=False, replace_halfspace=False):
    normalizer = Normalizer()
    text = normalizer.normalize(text)
    
    if replace_halfspace:
        text = text.replace("‌", " ")
        text = text.replace("\u200c", " ")
    text = text.replace("\xa0", " ")
    
    if remove_punct:
        text = re.sub(r'[،؛:!؟\-]+', ' ', text)
    
    text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    return text

def sentence_tokenize_persian(text):
    text = normalize_text(text, remove_punct=False, replace_halfspace=False)
    sentences = sent_tokenize(text)
    return sentences

def word_tokenize_persian(text):
    text = normalize_text(text, remove_punct=True, replace_halfspace=True)
    words = hazm_word_tokenize(text)
    return words

def normalize_text_language(text, lang="fa", remove_punct=False, replace_halfspace=False):
    if lang == "fa":
        return normalize_text(text, remove_punct=remove_punct, replace_halfspace=replace_halfspace)

    text = text.replace("\xa0", " ")
    if remove_punct:
        text = re.sub(r"[.,;:!?\\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def sentence_tokenize(text, lang="fa"):
    if lang == "fa":
        return sentence_tokenize_persian(text)

    text = normalize_text_language(text, lang=lang, remove_punct=False, replace_halfspace=False)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def word_tokenize(text, lang="fa"):
    if lang == "fa":
        return word_tokenize_persian(text)

    text = normalize_text_language(text, lang=lang, remove_punct=True, replace_halfspace=False)
    return re.findall(r"[A-Za-z0-9']+", text)
