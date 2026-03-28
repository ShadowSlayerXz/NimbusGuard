"""Financial document analysis — PDF upload + Gemini AI.

Accepts a PDF (annual report, cloud invoice, financial statement),
extracts text, and asks Gemini to produce a structured cost analysis
with predictions and optimization recommendations.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader

from backend.api import err, ok

router = APIRouter(prefix="/api/analyze", tags=["analyze"])

_MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


# ── PDF text extraction ───────────────────────────────────────────────────────

def _sync_extract_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {i + 1}]\n{text}")
    return "\n\n".join(pages)


async def _extract_pdf_text(file_bytes: bytes) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_extract_text, file_bytes)


# ── Gemini analysis ───────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an expert cloud infrastructure financial analyst for NimbusGuard,
a multi-cloud cost optimization platform. You analyse financial documents (annual reports,
cloud invoices, IT budgets, financial statements) to surface cloud spend patterns,
inefficiencies, and actionable optimisation opportunities.

Your analysis must be returned as a single valid JSON object — no markdown fences,
no commentary outside the JSON. Use exactly this schema:

{
  "executive_summary": "2-3 sentence high-level finding",
  "financial_health": "GOOD" | "FAIR" | "POOR",
  "cloud_spend_identified": {
    "total_monthly_usd": number | null,
    "annual_usd": number | null,
    "by_provider": {"aws": number | null, "azure": number | null, "gcp": number | null}
  },
  "key_findings": [
    {"title": "string", "detail": "string", "impact": "HIGH" | "MEDIUM" | "LOW"}
  ],
  "risk_factors": [
    {"risk": "string", "severity": "HIGH" | "MEDIUM" | "LOW"}
  ],
  "cost_projections": {
    "current_monthly_usd": number | null,
    "6_month_if_unchanged_usd": number | null,
    "12_month_if_unchanged_usd": number | null,
    "12_month_if_optimized_usd": number | null,
    "total_savings_opportunity_usd": number | null
  },
  "optimization_recommendations": [
    {
      "title": "string",
      "category": "idle_instances" | "right_sizing" | "region_arbitrage" | "provider_consolidation" | "reserved_instances" | "other",
      "priority": "HIGH" | "MEDIUM" | "LOW",
      "estimated_monthly_saving_usd": number | null,
      "saving_pct": number | null,
      "action": "specific action to take",
      "payback_period": "e.g. Immediate, 1-3 months, 6-12 months"
    }
  ],
  "total_monthly_recoverable_usd": number | null,
  "total_annual_recoverable_usd": number | null,
  "confidence_level": "HIGH" | "MEDIUM" | "LOW",
  "data_quality_note": "note about what financial data was found or what was missing"
}

Rules:
- If cloud spend figures are not explicitly stated, estimate from context clues and set confidence_level to LOW or MEDIUM.
- Always provide at least 3 key_findings and 3 optimization_recommendations even if some are general best-practices.
- Monetary values should be in USD. Convert other currencies using approximate rates.
- Be specific and actionable — vague advice is not useful."""


async def _call_gemini(extracted_text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured. Add it to your .env file.",
        )

    try:
        import google.generativeai as genai
    except ImportError:
        raise HTTPException(status_code=503, detail="google-generativeai package not installed")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=_SYSTEM_PROMPT,
    )

    truncated = extracted_text[:8000]  # free tier: ~1M tokens/day but 32k tokens/min limit
    prompt = (
        "Analyse the following financial document and return your findings "
        "as JSON exactly matching the schema in your instructions.\n\n"
        f"DOCUMENT TEXT:\n{truncated}"
    )

    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
    except Exception as exc:
        err_str = str(exc)
        if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit reached. Wait a minute and try again.",
            )
        raise HTTPException(status_code=502, detail=f"Gemini API error: {err_str[:200]}")

    raw = response.text.strip()

    # Strip accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini returned invalid JSON: {exc}. Raw: {raw[:300]}",
        )


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    """Upload a financial PDF and receive AI-powered cloud cost analysis."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return err("Only PDF files are accepted.")

    file_bytes = await file.read()
    if len(file_bytes) > _MAX_PDF_BYTES:
        return err(f"PDF exceeds maximum size of {_MAX_PDF_BYTES // 1024 // 1024} MB.")

    extracted = await _extract_pdf_text(file_bytes)
    if len(extracted.strip()) < 100:
        return err(
            "Could not extract readable text from this PDF. "
            "Scanned/image-only PDFs are not supported — please use a text-based PDF."
        )

    analysis = await _call_gemini(extracted)
    return ok({"filename": file.filename, "pages_extracted": extracted.count("[Page "), "analysis": analysis})
