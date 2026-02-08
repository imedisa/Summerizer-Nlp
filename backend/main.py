import logging
import os
import time
from threading import Lock
from uuid import uuid4

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    _env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(_env_path)

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any, Callable
from preprocessing import sentence_tokenize
from extractive import textrank_summarize
from abstractive import summarize_long_text
from evaluation import evaluate_dataset

logger = logging.getLogger("summarizer.api")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

EVAL_JOB_TTL_SEC = int(os.getenv("EVAL_JOB_TTL_SEC", "3600"))
_EVAL_JOBS: Dict[str, Dict[str, Any]] = {}
_EVAL_JOBS_LOCK = Lock()


def _get_allowed_origins() -> List[str]:
    raw = os.getenv("ALLOW_ORIGINS", "*")
    if raw.strip() == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI(
    title="Persian Text Summarization API",
    description="API برای خلاصه‌سازی متون فارسی",
    version=os.getenv("API_VERSION", "1.1.0"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True if os.getenv("ALLOW_CREDENTIALS", "1") == "1" else False,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled server error")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "خطای داخلی سرور",
                "request_id": request_id,
            },
        )
    process_time = time.time() - start_time
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    return response


class SummarizeRequest(BaseModel):
    text: str = Field(..., description="متن ورودی")
    method: Literal["extractive", "abstractive", "hybrid"] = Field(
        "extractive",
        description="نوع خلاصه‌سازی: extractive یا abstractive",
    )
    length: int = Field(30, description="درصد طول خلاصه (1-100)", ge=1, le=100)
    extractive_length: Optional[int] = Field(
        None, description="درصد طول خلاصه در مرحله extractive (1-100)", ge=1, le=100
    )
    abstractive_length: Optional[int] = Field(
        None, description="درصد طول خلاصه در مرحله abstractive (1-100)", ge=1, le=100
    )
    abstractive_num_beams: int = Field(
        2,
        description="تعداد پرتوها (Beam) برای خلاصه‌سازی مولد",
        ge=1,
        le=8,
    )
    abstractive_length_penalty: float = Field(
        1.0,
        description="جریمه طول برای خلاصه‌سازی مولد",
        ge=0.2,
        le=2.0,
    )
    abstractive_repetition_penalty: float = Field(
        1.1,
        description="جریمه تکرار برای خلاصه‌سازی مولد",
        ge=1.0,
        le=2.0,
    )
    abstractive_no_repeat_ngram_size: int = Field(
        3,
        description="اندازه n-gram بدون تکرار برای خلاصه‌سازی مولد",
        ge=0,
        le=6,
    )


class SummarizeResponse(BaseModel):
    ok: bool = True
    summary: str
    method: str
    original_length_chars: int
    original_length_sentences: Optional[int] = None
    summary_length_chars: int
    summary_length_sentences: Optional[int] = None
    processing_time_sec: float
    request_id: str
    extra: dict = None


class EvaluateRequest(BaseModel):
    method: Literal["extractive", "abstractive", "hybrid"] = Field(
        "extractive",
        description="نوع خلاصه‌سازی برای تست",
    )
    length: int = Field(30, description="درصد طول خلاصه (1-100)", ge=1, le=100)
    extractive_length: Optional[int] = Field(
        None, description="درصد طول خلاصه در مرحله extractive (1-100)", ge=1, le=100
    )
    abstractive_length: Optional[int] = Field(
        None, description="درصد طول خلاصه در مرحله abstractive (1-100)", ge=1, le=100
    )
    abstractive_num_beams: int = Field(
        2,
        description="تعداد پرتوها (Beam) برای خلاصه‌سازی مولد",
        ge=1,
        le=8,
    )
    abstractive_length_penalty: float = Field(
        1.0,
        description="جریمه طول برای خلاصه‌سازی مولد",
        ge=0.2,
        le=2.0,
    )
    abstractive_repetition_penalty: float = Field(
        1.1,
        description="جریمه تکرار برای خلاصه‌سازی مولد",
        ge=1.0,
        le=2.0,
    )
    abstractive_no_repeat_ngram_size: int = Field(
        3,
        description="اندازه n-gram بدون تکرار برای خلاصه‌سازی مولد",
        ge=0,
        le=6,
    )
    max_samples: int = Field(30, description="حداکثر تعداد نمونه برای ارزیابی", ge=1, le=1000)
    start_index: int = Field(0, description="شروع از ردیف مشخص", ge=0)
    shuffle: bool = Field(False, description="shuffle ردیف‌ها قبل از ارزیابی")
    seed: int = Field(42, description="seed برای shuffle")


class EvaluateResponse(BaseModel):
    rouge1_f1: float
    rouge2_f1: float
    rougeL_f1: float
    avg_gen_len: float
    avg_ref_len: float
    compression_ratio: float


class EvaluateAsyncResponse(BaseModel):
    ok: bool = True
    job_id: str
    status: Literal["queued", "running"]


class EvaluateProgress(BaseModel):
    processed: int
    total: Optional[int] = None
    samples: int
    skipped: int
    percent: Optional[float] = None


class EvaluateStatusResponse(BaseModel):
    ok: bool = True
    status: Literal["queued", "running", "completed", "failed"]
    result: Optional[EvaluateResponse] = None
    error: Optional[str] = None
    progress: Optional[EvaluateProgress] = None


def _resolve_dataset_path() -> str:
    default_dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "dataset", "test.csv")
    )
    return os.getenv("TEST_DATASET_PATH", default_dataset_path)


def _build_eval_result(metrics: Dict[str, float], length_metrics: Dict[str, float]) -> Dict[str, float]:
    return {
        "rouge1_f1": metrics["rouge1_f1"],
        "rouge2_f1": metrics["rouge2_f1"],
        "rougeL_f1": metrics["rougeL_f1"],
        "avg_gen_len": length_metrics["avg_gen_len"],
        "avg_ref_len": length_metrics["avg_ref_len"],
        "compression_ratio": length_metrics["compression_ratio"],
    }


def _cleanup_eval_jobs() -> None:
    if EVAL_JOB_TTL_SEC <= 0:
        return
    cutoff = time.time() - EVAL_JOB_TTL_SEC
    with _EVAL_JOBS_LOCK:
        for job_id, job in list(_EVAL_JOBS.items()):
            if job.get("updated_at", 0) < cutoff:
                del _EVAL_JOBS[job_id]


def _set_eval_job(job_id: str, **updates: Any) -> None:
    with _EVAL_JOBS_LOCK:
        current = _EVAL_JOBS.get(job_id, {})
        current.update(updates)
        current["updated_at"] = time.time()
        _EVAL_JOBS[job_id] = current


def _run_evaluation(
    request: EvaluateRequest,
    dataset_path: str,
    progress_cb: Optional[Callable[[int, int, int, int], None]] = None,
) -> Dict[str, float]:
    extractive_length = request.extractive_length or request.length
    abstractive_length = request.abstractive_length or request.length
    metrics, length_metrics, _counts = evaluate_dataset(
        dataset_path=dataset_path,
        method=request.method.lower(),
        length=request.length,
        extractive_length=extractive_length,
        abstractive_length=abstractive_length,
        abstractive_num_beams=request.abstractive_num_beams,
        abstractive_length_penalty=request.abstractive_length_penalty,
        abstractive_repetition_penalty=request.abstractive_repetition_penalty,
        abstractive_no_repeat_ngram_size=request.abstractive_no_repeat_ngram_size,
        max_samples=request.max_samples,
        start_index=request.start_index,
        shuffle=request.shuffle,
        seed=request.seed,
        progress_cb=progress_cb,
    )
    return _build_eval_result(metrics, length_metrics)

@app.get("/")
def root():
    return {
        "message": "Persian Summarization API is running.",
        "endpoints": {
            "docs": "/docs",
            "summarize": "/api/summarize"
        }
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.post("/api/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest, http_request: Request):
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", str(uuid4()))

    dataset_path = _resolve_dataset_path()

    try:
        result = _run_evaluation(request, dataset_path)
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "فایل دیتاست پیدا نشد"},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"error": str(exc)},
        )

    return EvaluateResponse(**result)


@app.post("/api/evaluate/async", response_model=EvaluateAsyncResponse)
def evaluate_async(
    request: EvaluateRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
):
    request_id = getattr(http_request.state, "request_id", str(uuid4()))
    job_id = str(uuid4())
    payload = request.model_dump()

    _cleanup_eval_jobs()
    _set_eval_job(
        job_id,
        status="queued",
        request_id=request_id,
        payload=payload,
        progress={"processed": 0, "total": None, "samples": 0, "skipped": 0, "percent": 0.0},
        created_at=time.time(),
    )

    def _runner(job_id: str, request: EvaluateRequest) -> None:
        _set_eval_job(job_id, status="running", started_at=time.time())
        dataset_path = _resolve_dataset_path()

        def _progress_cb(processed: int, total: int, samples: int, skipped: int) -> None:
            percent = round((processed / total) * 100, 2) if total else None
            _set_eval_job(
                job_id,
                progress={
                    "processed": processed,
                    "total": total,
                    "samples": samples,
                    "skipped": skipped,
                    "percent": percent,
                },
            )

        try:
            result = _run_evaluation(request, dataset_path, progress_cb=_progress_cb)
        except FileNotFoundError:
            _set_eval_job(job_id, status="failed", error="فایل دیتاست پیدا نشد", finished_at=time.time())
            return
        except ValueError as exc:
            _set_eval_job(job_id, status="failed", error=str(exc), finished_at=time.time())
            return
        except Exception:
            logger.exception("Evaluation job failed")
            _set_eval_job(job_id, status="failed", error="خطای داخلی سرور", finished_at=time.time())
            return

        _set_eval_job(job_id, status="completed", result=result, finished_at=time.time())

    background_tasks.add_task(_runner, job_id, request)

    return EvaluateAsyncResponse(job_id=job_id, status="queued")


@app.get("/api/evaluate/status/{job_id}", response_model=EvaluateStatusResponse)
def evaluate_status(job_id: str):
    _cleanup_eval_jobs()
    with _EVAL_JOBS_LOCK:
        job = _EVAL_JOBS.get(job_id)

    if not job:
        return JSONResponse(
            status_code=404,
            content={"error": "شناسه ارزیابی پیدا نشد"},
        )

    status = job.get("status", "queued")
    if status == "completed":
        result = job.get("result") or {}
        progress = job.get("progress")
        return EvaluateStatusResponse(
            status="completed",
            result=EvaluateResponse(**result),
            progress=EvaluateProgress(**progress) if progress else None,
        )

    if status == "failed":
        progress = job.get("progress")
        return EvaluateStatusResponse(
            status="failed",
            error=job.get("error") or "خطای داخلی سرور",
            progress=EvaluateProgress(**progress) if progress else None,
        )

    progress = job.get("progress")
    return EvaluateStatusResponse(
        status=status,
        progress=EvaluateProgress(**progress) if progress else None,
    )


@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest, http_request: Request):
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", str(uuid4()))
    
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
            "request_id": request_id,
            "error": "متن خالی است",
            "extra": {"error": "متن خالی است"}
        }
    
    method = request.method.lower()
    extractive_length = request.extractive_length or request.length
    abstractive_length = request.abstractive_length or request.length
    
    orig_sentences = sentence_tokenize(text)
    num_orig = len(orig_sentences)

    if method == "extractive":
        ratio = max(0.05, min(0.9, extractive_length / 100))
        result = textrank_summarize(text, summary_ratio=ratio)
        
        summary_text = result["summary"]
        num_sum = result["num_summary_sentences"]
        extra = {
            "metrics": {
                "requested_length_ratio": ratio,
                "extractive_ratio": result["summary_ratio"],
                "extractive_sentences": num_sum,
            },
            "summary_ratio": result["summary_ratio"],
            "selected_indices": result["selected_indices"],
            "scores": result.get("scores", {}),
            "provider": "local",
            "model": "TextRank",
        }

        end_time = time.time()

        return SummarizeResponse(
            ok=True,
            summary=summary_text,
            method=method,
            original_length_chars=len(text),
            original_length_sentences=num_orig,
            summary_length_chars=len(summary_text),
            summary_length_sentences=num_sum,
            processing_time_sec=round(end_time - start_time, 3),
            request_id=request_id,
            extra=extra,
        )
    
    elif method == "abstractive":
        ratio = max(0.1, min(0.9, abstractive_length / 100))
        gen_settings = {
            "num_beams": request.abstractive_num_beams,
            "length_penalty": request.abstractive_length_penalty,
            "repetition_penalty": request.abstractive_repetition_penalty,
            "no_repeat_ngram_size": request.abstractive_no_repeat_ngram_size,
        }
        final_summary, per_chunk, merged_text = summarize_long_text(
            text,
            length_ratio=ratio,
            chunk_num_beams=gen_settings["num_beams"],
            final_num_beams=gen_settings["num_beams"],
            length_penalty=gen_settings["length_penalty"],
            repetition_penalty=gen_settings["repetition_penalty"],
            no_repeat_ngram_size=gen_settings["no_repeat_ngram_size"],
        )
        summary_sentences = sentence_tokenize(final_summary)
        num_sum = len(summary_sentences)
        summary_text = final_summary
        extra = {
            "metrics": {
                "requested_length_ratio": ratio,
                "abstractive_input_chars": len(text),
                "abstractive_target_ratio": ratio,
            },
            "generation_settings": gen_settings,
            "chunks": per_chunk,
            "merged_text": merged_text,
            "provider": "local",
            "model": "Abstractive",
        }

        end_time = time.time()

        return SummarizeResponse(
            ok=True,
            summary=summary_text,
            method=method,
            original_length_chars=len(text),
            original_length_sentences=num_orig,
            summary_length_chars=len(summary_text),
            summary_length_sentences=num_sum,
            processing_time_sec=round(end_time - start_time, 3),
            request_id=request_id,
            extra=extra,
        )
    elif method == "hybrid":
        extractive_ratio = max(0.05, min(0.9, extractive_length / 100))
        abstractive_ratio = max(0.1, min(0.9, abstractive_length / 100))

        extractive_result = textrank_summarize(text, summary_ratio=extractive_ratio)
        extractive_summary = extractive_result["summary"]
        extractive_sentences = extractive_result["num_summary_sentences"]

        gen_settings = {
            "num_beams": request.abstractive_num_beams,
            "length_penalty": request.abstractive_length_penalty,
            "repetition_penalty": request.abstractive_repetition_penalty,
            "no_repeat_ngram_size": request.abstractive_no_repeat_ngram_size,
        }

        final_summary, per_chunk, merged_text = summarize_long_text(
            extractive_summary,
            length_ratio=abstractive_ratio,
            chunk_num_beams=gen_settings["num_beams"],
            final_num_beams=gen_settings["num_beams"],
            length_penalty=gen_settings["length_penalty"],
            repetition_penalty=gen_settings["repetition_penalty"],
            no_repeat_ngram_size=gen_settings["no_repeat_ngram_size"],
        )

        summary_sentences = sentence_tokenize(final_summary)
        num_sum = len(summary_sentences)
        summary_text = final_summary

        extra = {
            "metrics": {
                "requested_extractive_ratio": extractive_ratio,
                "requested_abstractive_ratio": abstractive_ratio,
                "extractive_sentences": extractive_sentences,
                "abstractive_input_chars": len(extractive_summary),
            },
            "generation_settings": gen_settings,
            "extractive_summary": extractive_summary,
            "chunks": per_chunk,
            "merged_text": merged_text,
            "provider": "local",
            "model": "Hybrid",
        }

        end_time = time.time()

        return SummarizeResponse(
            ok=True,
            summary=summary_text,
            method=method,
            original_length_chars=len(text),
            original_length_sentences=num_orig,
            summary_length_chars=len(summary_text),
            summary_length_sentences=num_sum,
            processing_time_sec=round(end_time - start_time, 3),
            request_id=request_id,
            extra=extra,
        )
    
    
    else:
        raise ValueError("method باید extractive یا abstractive یا hybrid باشد")
