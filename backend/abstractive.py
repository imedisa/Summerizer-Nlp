import os
from typing import List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from preprocessing import normalize_text_language, sentence_tokenize, word_tokenize

_MODEL = None
_TOKENIZER = None
_MODEL_NAME = None


def _get_device():
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _safe_model_max_length(tokenizer):
    max_len = getattr(tokenizer, "model_max_length", 512)
    if max_len is None or max_len > 4096:
        return 1024
    return max_len


def _resolve_model_path(model_name: str) -> str:
    if os.path.isdir(model_name):
        return model_name

    local_root = os.getenv("HF_MODEL_DIR")
    if local_root:
        if os.path.isdir(local_root):
            direct = os.path.join(local_root, model_name)
            if os.path.isdir(direct):
                return direct
            if "/" in model_name:
                short_name = os.path.basename(model_name)
                short_path = os.path.join(local_root, short_name)
                if os.path.isdir(short_path):
                    return short_path

        candidate = os.path.join(local_root, model_name)
        if os.path.isdir(candidate):
            return candidate

    local_default = os.path.join(os.path.dirname(__file__), "hf-models", model_name)
    if os.path.isdir(local_default):
        return local_default

    if "/" in model_name:
        short_name = os.path.basename(model_name)
        local_short = os.path.join(os.path.dirname(__file__), "hf-models", short_name)
        if os.path.isdir(local_short):
            return local_short

    return model_name


def _load_model(model_name: str | None = None):
    global _MODEL, _TOKENIZER, _MODEL_NAME

    model_name = model_name or os.getenv(
        "ABSTRACTIVE_MODEL", "nafisehNik/mt5-persian-summary"
    )

    device = _get_device()
    dtype = torch.float16 if device == "cuda" else torch.float32
    resolved_model = _resolve_model_path(model_name)
    using_local_path = os.path.isdir(resolved_model)
    local_only = os.getenv("HF_LOCAL_ONLY", "0") == "1" or using_local_path

    if local_only and not using_local_path:
        raise FileNotFoundError(
            "Local model not found. Place it under backend/hf-models/"
            " and set ABSTRACTIVE_MODEL to the folder name, or set HF_MODEL_DIR"
            " to the model folder."
        )

    if _MODEL is not None and _TOKENIZER is not None and _MODEL_NAME == resolved_model:
        return _MODEL, _TOKENIZER, _MODEL_NAME

    tokenizer = AutoTokenizer.from_pretrained(
        resolved_model, local_files_only=local_only
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(
        resolved_model, torch_dtype=dtype, local_files_only=local_only
    )

    model.to(device)
    model.eval()

    _MODEL = model
    _TOKENIZER = tokenizer
    _MODEL_NAME = resolved_model

    return _MODEL, _TOKENIZER, _MODEL_NAME


def _summarize_one(
    model,
    tokenizer,
    text,
    num_beams=2,
    max_input_length=1024,
    max_new_tokens=120,
    min_new_tokens=40,
    length_penalty=1.0,
    repetition_penalty=1.1,
    no_repeat_ngram_size=3,
    prefix="summarize: ",
):
    prompt = (prefix + text.strip()) if prefix else text.strip()

    enc = tokenizer(
        prompt, truncation=True, max_length=max_input_length, return_tensors="pt"
    ).to(_get_device())

    with torch.no_grad():
        out_ids = model.generate(
            **enc,
            num_beams=num_beams,
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            length_penalty=length_penalty,
            repetition_penalty=repetition_penalty,
            no_repeat_ngram_size=no_repeat_ngram_size,
            early_stopping=True,
            use_cache=True,
        )

    return tokenizer.decode(out_ids[0], skip_special_tokens=True).strip()


def chunk_text_by_tokens(
    tokenizer, text, chunk_size=850, overlap=120, prefix_tokens=10
):
    ids = tokenizer.encode(text, add_special_tokens=False)

    effective_chunk = max(50, chunk_size - prefix_tokens)

    step = max(1, effective_chunk - overlap)
    chunks = []
    for start in range(0, len(ids), step):
        end = min(len(ids), start + effective_chunk)
        chunk_ids = ids[start:end]
        chunk_text = tokenizer.decode(
            chunk_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
        ).strip()
        if chunk_text:
            chunks.append(chunk_text)
        if end >= len(ids):
            break
    return chunks


def summarize_long_text(
    text,
    chunk_size=850,
    overlap=120,
    chunk_num_beams=2,
    chunk_max_new_tokens=120,
    chunk_min_new_tokens=40,
    final_num_beams=2,
    final_max_new_tokens=120,
    final_min_new_tokens=40,
    length_penalty=1.0,
    repetition_penalty=1.1,
    no_repeat_ngram_size=3,
    max_input_length=1024,
    prefix="summarize: ",
    length_ratio=None,
):
    global _MODEL, _TOKENIZER
    if _MODEL is None or _TOKENIZER is None:
        _load_model()
    prefix_tok = (
        len(_TOKENIZER.encode(prefix, add_special_tokens=False)) if prefix else 0
    )

    chunks = chunk_text_by_tokens(
        _TOKENIZER,
        text,
        chunk_size=chunk_size,
        overlap=overlap,
        prefix_tokens=prefix_tok,
    )

    if length_ratio:
        total_tokens = len(_TOKENIZER.encode(text, add_special_tokens=False))
        target_total = int(total_tokens * length_ratio)
        target_total = max(40, min(600, target_total))
        chunk_count = max(1, len(chunks))
        chunk_target = max(20, int(target_total / chunk_count))
        chunk_max_new_tokens = max(30, min(240, chunk_target))
        chunk_min_new_tokens = max(10, min(chunk_max_new_tokens, int(chunk_max_new_tokens * 0.6)))
        final_max_new_tokens = max(50, min(600, target_total))
        final_min_new_tokens = max(20, min(final_max_new_tokens, int(final_max_new_tokens * 0.6)))

    chunk_summaries = []
    for i, ch in enumerate(chunks, 1):
        s = _summarize_one(
            _MODEL,
            _TOKENIZER,
            ch,
            num_beams=chunk_num_beams,
            max_input_length=max_input_length,
            max_new_tokens=chunk_max_new_tokens,
            min_new_tokens=chunk_min_new_tokens,
            length_penalty=length_penalty,
            repetition_penalty=repetition_penalty,
            no_repeat_ngram_size=no_repeat_ngram_size,
            prefix=prefix,
        )
        chunk_summaries.append(s)

    merged = "\n".join(f"- {s}" for s in chunk_summaries if s)

    final = _summarize_one(
        _MODEL,
        _TOKENIZER,
        merged,
        num_beams=final_num_beams,
        max_input_length=max_input_length,
        max_new_tokens=final_max_new_tokens,
        min_new_tokens=final_min_new_tokens,
        length_penalty=length_penalty,
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=no_repeat_ngram_size,
        prefix=prefix,
    )

    return final, chunk_summaries, merged
