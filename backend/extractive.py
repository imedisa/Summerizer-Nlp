from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import numpy as np
from preprocessing import normalize_text_language, sentence_tokenize

def calculate_similarity_matrix(sentences):
    if len(sentences) < 2:
        return np.zeros((len(sentences), len(sentences)))
    
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        return similarity_matrix
    except Exception as e:
        print(f"خطا در محاسبه شباهت: {e}")
        return np.zeros((len(sentences), len(sentences)))

def build_similarity_graph(similarity_matrix, threshold=0.1):
    graph = nx.Graph()
    n = len(similarity_matrix)
    
    for i in range(n):
        for j in range(i + 1, n):
            if similarity_matrix[i][j] > threshold:
                graph.add_edge(i, j, weight=similarity_matrix[i][j])
    
    return graph

def textrank_summarize(text, summary_ratio=0.3, num_sentences=None, lang="fa"):
    text = normalize_text_language(text, lang=lang, remove_punct=False, replace_halfspace=False)
    sentences = sentence_tokenize(text, lang=lang)
    
    num_original = len(sentences)
    
    if num_original == 0:
        return {
            "summary": "",
            "original_text": text,
            "num_original_sentences": 0,
            "num_summary_sentences": 0,
            "summary_ratio": 0,
            "selected_indices": [],
            "scores": {}
        }
    
    if num_original == 1:
        return {
            "summary": sentences[0],
            "original_text": text,
            "num_original_sentences": 1,
            "num_summary_sentences": 1,
            "summary_ratio": 1.0,
            "selected_indices": [0],
            "scores": {0: 1.0}
        }
    
    if num_sentences is None:
        num_summary = max(1, int(num_original * summary_ratio))
    else:
        num_summary = min(num_sentences, num_original)
    
    similarity_matrix = calculate_similarity_matrix(sentences)
    
    graph = build_similarity_graph(similarity_matrix)
    
    try:
        scores = nx.pagerank(graph, max_iter=100)
    except:
        scores = {i: 1.0 / num_original for i in range(num_original)}
    
    ranked_sentences = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    selected_indices = sorted([idx for idx, score in ranked_sentences[:num_summary]])
    

    summary = " ".join([sentences[i] for i in selected_indices])
    
    return {
        "summary": summary,
        "original_text": text,
        "num_original_sentences": num_original,
        "num_summary_sentences": num_summary,
        "summary_ratio": num_summary / num_original,
        "selected_indices": selected_indices,
        "scores": scores
    }
