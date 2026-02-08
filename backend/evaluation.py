import csv
import os
import random
import re
import time
from typing import Dict, List, Tuple, Optional, Callable

from rouge_score import rouge_scorer

from abstractive import summarize_long_text
from extractive import textrank_summarize
from preprocessing import sentence_tokenize


def _clean_dataset_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.replace("[n]", " ")
    cleaned = cleaned.replace("\u200c", " ")
    cleaned = cleaned.replace("\xa0", " ")
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def _read_test_rows(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


class _UnicodeWordTokenizer:
    def tokenize(self, text: str) -> List[str]:
        # Match unicode word characters so Persian tokens are preserved.
        return re.findall(r"\w+", text, flags=re.UNICODE)


def _generate_summary(
    text: str,
    method: str,
    length: int,
    extractive_length: int,
    abstractive_length: int,
    abstractive_num_beams: int = 2,
    abstractive_length_penalty: float = 1.0,
    abstractive_repetition_penalty: float = 1.1,
    abstractive_no_repeat_ngram_size: int = 3,
) -> str:
    if method == "extractive":
        ratio = max(0.05, min(0.9, extractive_length / 100))
        result = textrank_summarize(text, summary_ratio=ratio)
        return result["summary"]

    if method == "hybrid":
        extractive_ratio = max(0.05, min(0.9, extractive_length / 100))
        abstractive_ratio = max(0.1, min(0.9, abstractive_length / 100))
        extractive_result = textrank_summarize(text, summary_ratio=extractive_ratio)
        extractive_summary = extractive_result["summary"]
        final_summary, _, _ = summarize_long_text(
            extractive_summary,
            length_ratio=abstractive_ratio,
            chunk_num_beams=abstractive_num_beams,
            final_num_beams=abstractive_num_beams,
            length_penalty=abstractive_length_penalty,
            repetition_penalty=abstractive_repetition_penalty,
            no_repeat_ngram_size=abstractive_no_repeat_ngram_size,
        )
        return final_summary

    ratio = max(0.1, min(0.9, length / 100))
    final_summary, _, _ = summarize_long_text(
        text,
        length_ratio=ratio,
        chunk_num_beams=abstractive_num_beams,
        final_num_beams=abstractive_num_beams,
        length_penalty=abstractive_length_penalty,
        repetition_penalty=abstractive_repetition_penalty,
        no_repeat_ngram_size=abstractive_no_repeat_ngram_size,
    )
    return final_summary


def evaluate_dataset(
    dataset_path: str,
    method: str,
    length: int,
    extractive_length: int,
    abstractive_length: int,
    max_samples: int,
    start_index: int,
    shuffle: bool,
    seed: int,
    abstractive_num_beams: int = 2,
    abstractive_length_penalty: float = 1.0,
    abstractive_repetition_penalty: float = 1.1,
    abstractive_no_repeat_ngram_size: int = 3,
    progress_cb: Optional[Callable[[int, int, int, int], None]] = None,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float], Dict[str, int]]:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    rows = _read_test_rows(dataset_path)
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(rows)

    if start_index < 0:
        start_index = 0

    if max_samples is None or max_samples <= 0:
        selected = rows[start_index:]
    else:
        selected = rows[start_index : start_index + max_samples]

    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=False,
        tokenizer=_UnicodeWordTokenizer(),
    )

    totals = {
        "rouge1_f1": 0.0,
        "rouge2_f1": 0.0,
        "rougeL_f1": 0.0,
    }

    length_totals = {
        "original_chars": 0,
        "reference_chars": 0,
        "generated_chars": 0,
        "original_sentences": 0,
        "generated_sentences": 0,
    }

    counts = {"samples": 0, "skipped": 0}

    total_selected = len(selected)

    for idx, row in enumerate(selected, start=1):
        article = _clean_dataset_text(row.get("article", ""))
        reference = _clean_dataset_text(row.get("summary", ""))

        if not article or not reference:
            counts["skipped"] += 1
            if progress_cb:
                progress_cb(idx, total_selected, counts["samples"], counts["skipped"])
            continue

        generated = _generate_summary(
            article,
            method=method,
            length=length,
            extractive_length=extractive_length,
            abstractive_length=abstractive_length,
            abstractive_num_beams=abstractive_num_beams,
            abstractive_length_penalty=abstractive_length_penalty,
            abstractive_repetition_penalty=abstractive_repetition_penalty,
            abstractive_no_repeat_ngram_size=abstractive_no_repeat_ngram_size,
        )
        generated = _clean_dataset_text(generated)

        if not generated:
            counts["skipped"] += 1
            if progress_cb:
                progress_cb(idx, total_selected, counts["samples"], counts["skipped"])
            continue

        scores = scorer.score(reference, generated)
        totals["rouge1_f1"] += scores["rouge1"].fmeasure
        totals["rouge2_f1"] += scores["rouge2"].fmeasure
        totals["rougeL_f1"] += scores["rougeL"].fmeasure

        length_totals["original_chars"] += len(article)
        length_totals["reference_chars"] += len(reference)
        length_totals["generated_chars"] += len(generated)
        length_totals["original_sentences"] += len(sentence_tokenize(article))
        length_totals["generated_sentences"] += len(sentence_tokenize(generated))

        counts["samples"] += 1

        if progress_cb:
            progress_cb(idx, total_selected, counts["samples"], counts["skipped"])

    if counts["samples"] == 0:
        raise ValueError("No valid samples found for evaluation")

    averaged = {
        "rouge1_f1": round(totals["rouge1_f1"] / counts["samples"], 6),
        "rouge2_f1": round(totals["rouge2_f1"] / counts["samples"], 6),
        "rougeL_f1": round(totals["rougeL_f1"] / counts["samples"], 6),
    }

    avg_original_chars = round(length_totals["original_chars"] / counts["samples"], 2)
    avg_reference_chars = round(length_totals["reference_chars"] / counts["samples"], 2)
    avg_generated_chars = round(length_totals["generated_chars"] / counts["samples"], 2)

    if avg_original_chars > 0:
        compression_ratio = round(avg_generated_chars / avg_original_chars, 4)
    else:
        compression_ratio = 0.0

    length_metrics = {
        "avg_gen_len": avg_generated_chars,
        "avg_ref_len": avg_reference_chars,
        "compression_ratio": compression_ratio,
    }

    return averaged, length_metrics, counts
