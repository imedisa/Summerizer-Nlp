import os
import time
from preprocessing import normalize_text, sentence_tokenize_persian


def hf_summarize(
    text: str,
    max_length: int = 130,
    min_length: int = 30,
    temperature: float = 1.0,
    top_p: float = 1.0,
    timeout: float = 60.0,
):
    """
    خلاصه‌سازی مولد - نسخه Mock برای دمو
    در محیط production با دسترسی کامل به HuggingFace، کد واقعی فعال می‌شود
    """
    if not text or len(text.strip()) == 0:
        return {"error": "متن ورودی خالی است."}

    text = normalize_text(text)
    sentences = sentence_tokenize_persian(text)
    
    # شبیه‌سازی تأخیر API
    time.sleep(0.5)
    
    # خلاصه ساده: انتخاب جملات اول و آخر + بازنویسی ساده
    if len(sentences) >= 2:
        summary = f"{sentences[0]} {sentences[-1]}"
    else:
        summary = text
    
    # محدود کردن به max_length تقریبی
    words = summary.split()
    if len(words) > max_length // 5:  # تقریب توکن
        summary = " ".join(words[:max_length // 5]) + "..."
    
    return {
        "summary": summary.strip(),
        "original_text": text,
        "provider": "huggingface-mock",
        "model": "demo-mode",
        "note": "این یک نسخه نمایشی است. در محیط production از API واقعی استفاده می‌شود."
    }


if __name__ == "__main__":
    sample = "هوش مصنوعی در حال تحول صنایع مختلف است. این فناوری در پزشکی، آموزش و خودروسازی کاربرد دارد. شرکت‌های بزرگ سرمایه‌گذاری زیادی روی آن می‌کنند."
    print(hf_summarize(sample, max_length=50))
