from hazm import Normalizer, sent_tokenize, word_tokenize
import re

def normalize_text(text):
    """
    نرمال‌سازی متن فارسی
    
    Args:
        text (str): متن ورودی
    
    Returns:
        str: متن نرمال‌شده
    """
    normalizer = Normalizer()
    text = normalizer.normalize(text)
    
    # حذف کاراکترهای اضافی
    text = text.replace("‌", " ")  # نیم‌فاصله به فاصله
    text = text.replace("\u200c", " ")
    text = text.replace("\xa0", " ")
    
    # حذف علائم اضافی
    text = re.sub(r'[،؛:!؟\-]+', ' ', text)
    
    # حذف فاصله‌های اضافی
    text = re.sub(r'\s+', ' ', text)
    
    text = text.strip()
    return text

def sentence_tokenize_persian(text):
    """
    جمله‌بندی متن فارسی
    
    Args:
        text (str): متن ورودی
    
    Returns:
        list: لیست جملات
    """
    text = normalize_text(text)
    sentences = sent_tokenize(text)
    return sentences

def word_tokenize_persian(text):
    """
    واژه‌بندی متن فارسی
    
    Args:
        text (str): متن ورودی
    
    Returns:
        list: لیست کلمات
    """
    text = normalize_text(text)
    words = word_tokenize(text)
    return words

if __name__ == "__main__":
    # تست
    sample = "این یک متن نمونه است. برای تست کد!"
    print("اصلی:", sample)
    print("نرمال:", normalize_text(sample))
    print("جملات:", sentence_tokenize_persian(sample))
    print("کلمات:", word_tokenize_persian(sample))
