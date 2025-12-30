from preprocessing import normalize_text, sentence_tokenize_persian, word_tokenize_persian


# متن‌های نمونه فارسی برای تست
test_texts = [
    """
    هوش مصنوعی یکی از مهم‌ترین فناوری‌های قرن بیست‌ویکم است. این فناوری توانسته است در حوزه‌های مختلفی مانند پزشکی، صنعت و آموزش تحول ایجاد کند.
    """,
    
    """
    ايران كشوري با تاريخ كهن و تمدني غني است . مردم اين سرزمين هميشه در برابر ظلم ايستاده‌اند .
    """,
    
    """
    خلاصه‌سازی متن فرآیند کاهش حجم یک متن با حفظ اطلاعات مهم آن است. دو روش اصلی برای خلاصه‌سازی وجود دارد: استخراجی و مولد.
    """,
    
    """
    پردازش زبان طبیعی (NLP) شاخه‌ای از هوش مصنوعی است که به کامپیوتر کمک می‌کند زبان انسانی را درک کند.
    """,
    
    """
    دانشگاه تهران  ،  بزرگترین دانشگاه ایران   است   . این دانشگاه در سال ۱۳۱۳ تأسیس شد!!!
    """,
    
    """
    یادگیری ماشین زیرمجموعه‌ای از هوش مصنوعی است. الگوریتم‌های یادگیری ماشین می‌توانند از داده‌ها یاد بگیرند و پیش‌بینی انجام دهند.
    """
]


def test_normalize():
    """تست تابع نرمال‌سازی"""
    print("=" * 80)
    print("تست نرمال‌سازی متن")
    print("=" * 80)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- متن {i} ---")
        print(f"اصلی: {text.strip()}")
        normalized = normalize_text(text)
        print(f"نرمال: {normalized}")
        print(f"طول اصلی: {len(text)} | طول نرمال: {len(normalized)}")


def test_sentence_tokenize():
    """تست تابع جداسازی جمله"""
    print("\n" + "=" * 80)
    print("تست جداسازی جملات")
    print("=" * 80)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- متن {i} ---")
        sentences = sentence_tokenize_persian(text)
        print(f"تعداد جملات: {len(sentences)}")
        for j, sent in enumerate(sentences, 1):
            print(f"  جمله {j}: {sent}")


def test_word_tokenize():
    """تست تابع جداسازی کلمات"""
    print("\n" + "=" * 80)
    print("تست جداسازی کلمات")
    print("=" * 80)
    
    # فقط یک متن رو تست می‌کنیم (خروجی زیاد میشه)
    sample = test_texts[0]
    print(f"متن نمونه: {sample.strip()}")
    words = word_tokenize_persian(sample)
    print(f"\nتعداد کلمات: {len(words)}")
    print(f"کلمات: {words}")


def test_all():
    """اجرای همه تست‌ها"""
    test_normalize()
    test_sentence_tokenize()
    test_word_tokenize()
    
    print("\n" + "=" * 80)
    print("✅ تست‌ها با موفقیت اجرا شدند!")
    print("=" * 80)


if __name__ == "__main__":
    test_all()
