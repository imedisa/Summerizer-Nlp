import os
import time
from preprocessing import normalize_text, sentence_tokenize_persian, word_tokenize_persian

# Mock version - بدون نیاز به HuggingFace API
def hf_summarize(
    text: str,
    max_length: int = 130,
    min_length: int = 30,
    temperature: float = 1.0,
    top_p: float = 1.0,
    timeout: float = 60.0
):
    """
    Mock summarizer - برای تست بدون API
    در production می‌تونید HuggingFace API رو فعال کنید
    """
    if not text or len(text.strip()) == 0:
        return {"error": "متن خالی است"}
    
    # نرمال‌سازی متن
    text = normalize_text(text)
    sentences = sentence_tokenize_persian(text)
    
    if len(sentences) == 0:
        return {"error": "متن قابل پردازش نیست"}
    
    # انتخاب جملات کلیدی (اول، وسط، آخر)
    selected = [sentences[0]]
    
    if len(sentences) >= 3:
        mid = len(sentences) // 2
        selected.append(sentences[mid])
    
    if len(sentences) >= 2:
        selected.append(sentences[-1])
    
    summary = " ".join(selected)
    
    # محدود کردن طول بر اساس max_length
    words = word_tokenize_persian(summary)
    if len(words) > max_length:
        summary = " ".join(words[:max_length]) + "..."
    
    return {
        "summary": summary,
        "originaltext": text,
        "provider": "mock",
        "model": "simple-abstractive"
    }


# نسخه واقعی HuggingFace (اختیاری - فعلاً کامنت)
"""
import requests

HFAPI_URL = "https://router.huggingface.co/hf-inference/models/nafisehNik/mt5-persian-summary"

def get_headers():
    token = os.getenv("HFTOKEN")
    if not token:
        raise ValueError("HFTOKEN تنظیم نشده است")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def hf_summarize_real(
    text: str,
    max_length: int = 130,
    min_length: int = 30,
    temperature: float = 1.0,
    top_p: float = 1.0,
    timeout: float = 60.0
):
    if not text or len(text.strip()) == 0:
        return {"error": "متن خالی است"}
    
    text = normalize_text(text)
    
    payload = {
        "inputs": text,
        "parameters": {
            "max_length": max_length,
            "min_length": min_length,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": False
        }
    }
    
    try:
        headers = get_headers()
        response = requests.post(
            HFAPI_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 503:
            return {"error": "مدل در حال بارگذاری است. لطفاً 20 ثانیه صبر کنید"}
        
        if response.status_code != 200:
            return {
                "error": f"خطای HuggingFace: {response.status_code}",
                "details": response.text[:500]
            }
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            generated = data[0].get("summary_text", "")
        elif isinstance(data, dict):
            generated = data.get("summary_text", "")
        else:
            return {"error": "پاسخ نامعتبر از API", "raw": str(data)[:200]}
        
        if not generated:
            return {"error": "خلاصه تولید نشد", "raw": str(data)[:200]}
        
        return {
            "summary": generated.strip(),
            "originaltext": text,
            "provider": "huggingface",
            "model": "mt5-persian"
        }
        
    except requests.exceptions.Timeout:
        return {"error": "timeout در ارتباط با HuggingFace"}
    except requests.exceptions.ConnectionError:
        return {"error": "خطای اتصال به HuggingFace"}
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception as e:
        return {"error": f"خطای ناشناخته: {e}"}
"""

if __name__ == "__main__":
    # تست
    sample = "هوش مصنوعی یکی از مهم‌ترین فناوری‌های قرن بیست و یکم است. این فناوری در حال تغییر دنیا است. کاربردهای آن بسیار گسترده است."
    result = hf_summarize(sample, max_length=60, min_length=20)
    print(result)
