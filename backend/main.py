from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import time

from preprocessing import normalize_text
from extractive import textrank_summarize
from abstractive import hf_summarize


app = FastAPI(
    title="Persian Text Summarization API",
    description="سامانه خلاصه‌سازی متن فارسی با روش‌های استخراجی و مولد",
    version="1.0.0",
)


# تنظیم CORS برای اینکه بعدا React بتواند متصل شود[web:62][web:59]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در نسخه نهایی می‌توانی محدود کنی
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeRequest(BaseModel):
    text: str = Field(..., description="متن فارسی برای خلاصه‌سازی")
    method: str = Field("extractive", description='"extractive" یا "abstractive"')
    length: int = Field(
        30,
        description="برای استخراجی: درصد جملات (مثلاً 30). برای مولد: حداکثر طول خلاصه تقریبی.",
        ge=1,
        le=1000,
    )


class SummarizeResponse(BaseModel):
    summary: str
    method: str
    original_length_chars: int
    original_length_sentences: int | None = None
    summary_length_chars: int
    summary_length_sentences: int | None = None
    processing_time_sec: float
    extra: dict | None = None


@app.get("/")
def root():
    return {"message": "Persian Summarization API is running."}


@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest):
    """
    Endpoint اصلی خلاصه‌سازی.
    """
    start_time = time.time()

    text = request.text or ""
    text = text.strip()
    if not text:
        # FastAPI خودش هم خطای ولیدیشن می‌دهد، ولی اینجا هم چک می‌کنیم[web:62]
        raise ValueError("متن ورودی خالی است.")

    method = request.method.lower()

    # استخراجی
    if method == "extractive":
        # length را به درصد جملات تبدیل می‌کنیم، مثلاً 30 یعنی 30٪
        ratio = max(0.05, min(0.9, request.length / 100))
        result = textrank_summarize(text, summary_ratio=ratio)
        summary_text = result["summary"]
        num_orig = result["num_original_sentences"]
        num_sum = result["num_summary_sentences"]
        extra = {
            "summary_ratio": result["summary_ratio"],
            "selected_indices": result["selected_indices"],
            "scores": result["scores"],
        }

    # مولد
    elif method == "abstractive":
        # length را مستقیم به max_length پاس می‌دهیم
        gen = hf_summarize(text, max_length=request.length)
        if "error" in gen:
            # خطای API HuggingFace را در extra برمی‌گردانیم
            summary_text = gen.get("error")
            num_orig = None
            num_sum = None
            extra = {"provider_response": gen}
        else:
            summary_text = gen["summary"]
            # می‌توانیم تعداد جملات را با پیش‌پردازش حساب کنیم
            from preprocessing import sentence_tokenize_persian

            num_orig = len(sentence_tokenize_persian(normalize_text(text)))
            num_sum = len(sentence_tokenize_persian(normalize_text(summary_text)))
            extra = {
                "provider": gen["provider"],
                "model": gen["model"],
            }

    else:
        raise ValueError('method باید یکی از "extractive" یا "abstractive" باشد.')

    end_time = time.time()

    return SummarizeResponse(
        summary=summary_text,
        method=method,
        original_length_chars=len(text),
        original_length_sentences=num_orig,
        summary_length_chars=len(summary_text),
        summary_length_sentences=num_sum,
        processing_time_sec=round(end_time - start_time, 3),
        extra=extra,
    )
