from hazm import Normalizer, sent_tokenize, word_tokenize
import re


def normalize_text(text):
    """
    نرمال‌سازی متن فارسی
    
    Args:
        text (str): متن ورودی فارسی
    
    Returns:
        str: متن نرمال‌شده
    """
    # استفاده از Normalizer کتابخانه hazm
    normalizer = Normalizer()
    text = normalizer.normalize(text)
    
    # تبدیل حروف عربی به فارسی
    text = text.replace('ي', 'ی')
    text = text.replace('ك', 'ک')
    text = text.replace('ۀ', 'ه')
    
    # حذف کاراکترهای غیرضروری (اعداد انگلیسی به فارسی تبدیل نمیشه، فقط نگه میداریم)
    # حذف کاراکترهای خاص غیرضروری
    text = re.sub(r'[^\w\s\.\,\:\;\!\?\؛\،\٪\-]', '', text)
    
    # حذف فاصله‌های اضافی
    text = re.sub(r'\s+', ' ', text)
    
    # حذف فاصله‌های ابتدا و انتهای متن
    text = text.strip()
    
    return text


def sentence_tokenize_persian(text):
    """
    تقسیم متن فارسی به جملات
    
    Args:
        text (str): متن فارسی
    
    Returns:
        list: لیست جملات
    """
    # ابتدا متن رو نرمال کن
    text = normalize_text(text)
    
    # استفاده از sent_tokenize کتابخانه hazm
    sentences = sent_tokenize(text)
    
    return sentences


def word_tokenize_persian(text):
    """
    تقسیم متن فارسی به کلمات
    
    Args:
        text (str): متن فارسی
    
    Returns:
        list: لیست کلمات
    """
    # ابتدا متن رو نرمال کن
    text = normalize_text(text)
    
    # استفاده از word_tokenize کتابخانه hazm
    words = word_tokenize(text)
    
    return words


# تست سریع (اختیاری)
if __name__ == "__main__":
    sample = "این یک متن نمونه است. برای تست کردن توابع!"
    print("متن اصلی:", sample)
    print("نرمال‌شده:", normalize_text(sample))
    print("جملات:", sentence_tokenize_persian(sample))
    print("کلمات:", word_tokenize_persian(sample))
