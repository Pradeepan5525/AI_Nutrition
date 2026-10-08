"""Report generation router compiling downloadable clinical nutrition PDF reports."""

from __future__ import annotations

import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import ReportRequest
from nutri.reports.pdf import generate_nutrition_pdf

router = APIRouter(prefix="/report", tags=["Reports"])


@router.post("", response_class=StreamingResponse)
def generate_pdf_report(payload: ReportRequest) -> StreamingResponse:
    """Generate and stream a publication-grade 2-page clinical nutrition PDF report."""
    try:
        report_data = payload.model_dump()
        pdf_bytes = generate_nutrition_pdf(report_data)

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=clinical_nutrition_report.pdf",
                "Content-Length": str(len(pdf_bytes)),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF report generation error: {str(e)}") from e
