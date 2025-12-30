from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import numpy as np
from preprocessing import normalize_text, sentence_tokenize_persian, word_tokenize_persian


def calculate_similarity_matrix(sentences):
    """
    محاسبه ماتریس شباهت بین جملات با استفاده از TF-IDF و شباهت کسینوسی
    
    Args:
        sentences (list): لیست جملات فارسی
    
    Returns:
        numpy.ndarray: ماتریس شباهت (n x n)
    """
    # اگر کمتر از 2 جمله داریم، نمی‌توانیم شباهت محاسبه کنیم
    if len(sentences) < 2:
        return np.zeros((len(sentences), len(sentences)))
    
    # تبدیل جملات به بردارهای TF-IDF
    # TfidfVectorizer جملات را به بردارهای عددی تبدیل می‌کند
    # که اهمیت هر کلمه در جمله را نشان می‌دهد
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # محاسبه شباهت کسینوسی بین تمام جفت جملات
        # خروجی یک ماتریس n x n است که similarity_matrix[i][j]
        # نشان‌دهنده شباهت بین جمله i و جمله j است
        similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        return similarity_matrix
    
    except Exception as e:
        print(f"خطا در محاسبه ماتریس شباهت: {e}")
        return np.zeros((len(sentences), len(sentences)))


def build_similarity_graph(similarity_matrix, threshold=0.1):
    """
    ساخت گراف شباهت از ماتریس شباهت
    
    Args:
        similarity_matrix (numpy.ndarray): ماتریس شباهت جملات
        threshold (float): حداقل شباهت برای ایجاد یال (پیش‌فرض: 0.1)
    
    Returns:
        networkx.Graph: گراف شباهت جملات
    """
    # ساخت یک گراف خالی
    graph = nx.Graph()
    
    # تعداد جملات
    num_sentences = similarity_matrix.shape[0]
    
    # اضافه کردن نودها (هر جمله یک نود است)
    for i in range(num_sentences):
        graph.add_node(i)
    
    # اضافه کردن یال‌ها (ارتباط بین جملات)
    # اگر شباهت دو جمله بیشتر از threshold باشد، یک یال ایجاد می‌کنیم
    for i in range(num_sentences):
        for j in range(i + 1, num_sentences):
            similarity = similarity_matrix[i][j]
            
            # فقط یال‌هایی با وزن بالاتر از threshold اضافه می‌شوند
            if similarity > threshold:
                graph.add_edge(i, j, weight=similarity)
    
    return graph


def textrank_summarize(text, summary_ratio=0.3, num_sentences=None):
    """
    خلاصه‌سازی استخراجی متن با استفاده از الگوریتم TextRank
    
    Args:
        text (str): متن فارسی ورودی
        summary_ratio (float): نسبت خلاصه به متن اصلی (پیش‌فرض: 0.3 یعنی 30%)
        num_sentences (int): تعداد دقیق جملات خلاصه (اگر مشخص شود، summary_ratio نادیده گرفته می‌شود)
    
    Returns:
        dict: شامل خلاصه، جملات اصلی، و اطلاعات اضافی
    """
    # مرحله 1: نرمال‌سازی متن
    normalized_text = normalize_text(text)
    
    # مرحله 2: تقسیم به جملات
    sentences = sentence_tokenize_persian(normalized_text)
    
    # بررسی حداقل تعداد جملات
    if len(sentences) < 2:
        return {
            "summary": normalized_text,
            "sentences": sentences,
            "num_original_sentences": len(sentences),
            "num_summary_sentences": len(sentences),
            "error": "متن باید حداقل 2 جمله داشته باشد"
        }
    
    # مرحله 3: محاسبه ماتریس شباهت
    similarity_matrix = calculate_similarity_matrix(sentences)
    
    # مرحله 4: ساخت گراف
    graph = build_similarity_graph(similarity_matrix)
    
    # مرحله 5: اجرای الگوریتم PageRank
    # PageRank به هر نود (جمله) یک امتیاز می‌دهد که نشان‌دهنده اهمیت آن است
    try:
        scores = nx.pagerank(graph, weight='weight')
    except:
        # اگر گراف خالی بود یا مشکلی پیش آمد، امتیاز یکسان به همه جملات بده
        scores = {i: 1.0 / len(sentences) for i in range(len(sentences))}
    
    # مرحله 6: رتبه‌بندی جملات بر اساس امتیاز
    # جملات را بر اساس امتیاز PageRank مرتب می‌کنیم
    ranked_sentences = sorted(
        ((scores[i], i, sentence) for i, sentence in enumerate(sentences)),
        key=lambda x: x[0],
        reverse=True
    )
    
    # مرحله 7: انتخاب تعداد جملات خلاصه
    if num_sentences is not None:
        # اگر تعداد دقیق مشخص شده، از آن استفاده کن
        n = min(num_sentences, len(sentences))
    else:
        # در غیر این صورت از نسبت استفاده کن
        n = max(1, int(len(sentences) * summary_ratio))
    
    # مرحله 8: انتخاب n جمله برتر
    selected_sentences = ranked_sentences[:n]
    
    # مرحله 9: مرتب‌سازی جملات بر اساس ترتیب ظهور در متن اصلی
    # این کار باعث می‌شود خلاصه طبیعی‌تر و روان‌تر باشد
    selected_sentences = sorted(selected_sentences, key=lambda x: x[1])
    
    # مرحله 10: ساخت خلاصه نهایی
    summary = ' '.join([sentence for _, _, sentence in selected_sentences])
    
    # بازگشت نتایج
    return {
        "summary": summary,
        "original_text": text,
        "sentences": sentences,
        "num_original_sentences": len(sentences),
        "num_summary_sentences": n,
        "summary_ratio": n / len(sentences),
        "selected_indices": [idx for _, idx, _ in selected_sentences],
        "scores": {i: scores.get(i, 0) for i in range(len(sentences))}
    }


def summarize_from_file(file_path, summary_ratio=0.3):
    """
    خلاصه‌سازی متن از روی فایل
    
    Args:
        file_path (str): مسیر فایل متنی
        summary_ratio (float): نسبت خلاصه
    
    Returns:
        dict: نتیجه خلاصه‌سازی
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return textrank_summarize(text, summary_ratio=summary_ratio)
    
    except FileNotFoundError:
        return {"error": f"فایل {file_path} یافت نشد"}
    except Exception as e:
        return {"error": f"خطا در خواندن فایل: {e}"}


# تست سریع
if __name__ == "__main__":
    # متن نمونه
    sample_text = """
    هوش مصنوعی یکی از مهم‌ترین فناوری‌های قرن بیست‌ویکم است. 
    این فناوری توانسته است در حوزه‌های مختلفی مانند پزشکی، صنعت و آموزش تحول ایجاد کند.
    گوگل اخیراً مدل زبانی جدید خود را معرفی کرد که قابلیت پردازش همزمان متن، تصویر و صدا را دارد.
    در ایران نیز استارتاپ‌های مختلفی در حوزه پردازش زبان طبیعی فارسی فعالیت می‌کنند.
    کارشناسان معتقدند که هوش مصنوعی تا سال ۲۰۳۰ بیش از ۱۵ درصد از تولید ناخالص داخلی جهان را تحت تأثیر قرار خواهد داد.
    با این حال، نگرانی‌هایی درباره اخلاق و امنیت داده‌ها در استفاده از این فناوری‌ها وجود دارد.
    """
    
    print("=" * 80)
    print("تست خلاصه‌سازی TextRank")
    print("=" * 80)
    
    result = textrank_summarize(sample_text, summary_ratio=0.3)
    
    print(f"\n📄 متن اصلی:")
    print(result['original_text'].strip())
    
    print(f"\n📊 آمار:")
    print(f"  • تعداد جملات اصلی: {result['num_original_sentences']}")
    print(f"  • تعداد جملات خلاصه: {result['num_summary_sentences']}")
    print(f"  • نسبت خلاصه: {result['summary_ratio']:.1%}")
    
    print(f"\n✨ خلاصه:")
    print(result['summary'])
    
    print(f"\n🎯 امتیاز جملات:")
    for i, score in result['scores'].items():
        print(f"  جمله {i+1}: {score:.4f}")
