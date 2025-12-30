from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import numpy as np
from preprocessing import normalize_text, sentence_tokenize_persian, word_tokenize_persian

def calculate_similarity_matrix(sentences):
    """
    محاسبه ماتریس شباهت با TF-IDF
    
    Args:
        sentences (list): لیست جملات
    
    Returns:
        numpy.ndarray: ماتریس شباهت n x n
    """
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
    """
    ساخت گراف شباهت
    
    Args:
        similarity_matrix (numpy.ndarray): ماتریس شباهت
        threshold (float): حد آستانه شباهت (پیش‌فرض: 0.1)
    
    Returns:
        networkx.Graph: گراف شباهت
    """
    graph = nx.Graph()
    n = len(similarity_matrix)
    
    for i in range(n):
        for j in range(i + 1, n):
            if similarity_matrix[i][j] > threshold:
                graph.add_edge(i, j, weight=similarity_matrix[i][j])
    
    return graph

def textrank_summarize(text, summary_ratio=0.3, num_sentences=None):
    """
    خلاصه‌سازی با الگوریتم TextRank
    
    Args:
        text (str): متن ورودی
        summary_ratio (float): نسبت خلاصه به متن اصلی (0.0 تا 1.0)
        num_sentences (int): تعداد جملات خلاصه (اختیاری)
    
    Returns:
        dict: خلاصه و اطلاعات مرتبط
    """
    # نرمال‌سازی و جمله‌بندی
    text = normalize_text(text)
    sentences = sentence_tokenize_persian(text)
    
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
    
    # تعیین تعداد جملات خلاصه
    if num_sentences is None:
        num_summary = max(1, int(num_original * summary_ratio))
    else:
        num_summary = min(num_sentences, num_original)
    
    # محاسبه ماتریس شباهت
    similarity_matrix = calculate_similarity_matrix(sentences)
    
    # ساخت گراف
    graph = build_similarity_graph(similarity_matrix)
    
    # محاسبه PageRank
    try:
        scores = nx.pagerank(graph, max_iter=100)
    except:
        # fallback: اگر گراف خالی باشد
        scores = {i: 1.0 / num_original for i in range(num_original)}
    
    # مرتب‌سازی جملات بر اساس امتیاز
    ranked_sentences = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # انتخاب top جملات
    selected_indices = sorted([idx for idx, score in ranked_sentences[:num_summary]])
    
    # ساخت خلاصه
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

if __name__ == "__main__":
    # تست
    sample = """
    هوش مصنوعی یکی از مهم‌ترین فناوری‌های قرن بیست و یکم است.
    این فناوری در حال تغییر دنیا است.
    کاربردهای آن بسیار گسترده است.
    محققان در سراسر جهان روی آن کار می‌کنند.
    آینده هوش مصنوعی بسیار روشن است.
    """
    
    result = textrank_summarize(sample, summary_ratio=0.4)
    print("خلاصه:", result["summary"])
    print("تعداد جملات اصلی:", result["num_original_sentences"])
    print("تعداد جملات خلاصه:", result["num_summary_sentences"])
