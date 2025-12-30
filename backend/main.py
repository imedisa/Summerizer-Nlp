from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time
from preprocessing import normalize_text, sentence_tokenize_persian
from extractive import textrank_summarize
from abstractive import hf_summarize

app = FastAPI(
    title="Persian Text Summarization API",
    description="API برای خلاصه‌سازی متون فارسی",
    version="1.0.0"
)

# CORS - برای اتصال React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در production فقط دامنه خودتون رو اجازه بدید
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class SummarizeRequest(BaseModel):
    text: str = Field(..., description="متن ورودی فارسی")
    method: str = Field("extractive", description="نوع خلاصه‌سازی: extractive یا abstractive")
    length: int = Field(30, description="درصد طول خلاصه (1-100)", ge=1, le=100)

class SummarizeResponse(BaseModel):
    summary: str
    method: str
    original_length_chars: int
    original_length_sentences: int = None
    summary_length_chars: int
    summary_length_sentences: int = None
    processing_time_sec: float
    extra: dict = None

@app.get("/")
def root():
    """صفحه اصلی API"""
    return {
        "message": "Persian Summarization API is running.",
        "endpoints": {
            "docs": "/docs",
            "summarize": "/api/summarize"
        }
    }

@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest):
    """
    Endpoint اصلی برای خلاصه‌سازی
    """
    start_time = time.time()
    
    # بررسی متن ورودی
    text = request.text or ""
    text = text.strip()
    
    if not text:
        return {
            "summary": "",
            "method": request.method,
            "original_length_chars": 0,
            "original_length_sentences": 0,
            "summary_length_chars": 0,
            "summary_length_sentences": 0,
            "processing_time_sec": 0,
            "extra": {"error": "متن خالی است"}
        }
    
    method = request.method.lower()
    
    # خلاصه‌سازی استخراجی (TextRank)
    if method == "extractive":
        ratio = max(0.05, min(0.9, request.length / 100))
        result = textrank_summarize(text, summary_ratio=ratio)
        
        summary_text = result["summary"]
        num_orig = result["num_original_sentences"]
        num_sum = result["num_summary_sentences"]
        extra = {
            "summary_ratio": result["summary_ratio"],
            "selected_indices": result["selected_indices"],
            "scores": result.get("scores", {}),
            "provider": "local",
            "model": "TextRank"
        }
    
    # خلاصه‌سازی مولد (HuggingFace)
    elif method == "abstractive":
        gen = hf_summarize(text, max_length=request.length)
        
        if "error" in gen:
            summary_text = gen.get("error", "خطا در تولید خلاصه")
            num_orig = None
            num_sum = None
            extra = {"provider": "response", "model": gen.get("model", "unknown")}
        else:
            summary_text = gen["summary"]
            num_orig = len(sentence_tokenize_persian(normalize_text(text)))
            num_sum = len(sentence_tokenize_persian(normalize_text(summary_text)))
            extra = {"provider": gen["provider"], "model": gen["model"]}
    
    else:
        raise ValueError("method باید extractive یا abstractive باشد")
    
    end_time = time.time()
    
    return SummarizeResponse(
        summary=summary_text,
        method=method,
        original_length_chars=len(text),
        original_length_sentences=num_orig,
        summary_length_chars=len(summary_text),
        summary_length_sentences=num_sum,
        processing_time_sec=round(end_time - start_time, 3),
        extra=extra
    )

# برای اجرا:
# uvicorn main:app --reload
