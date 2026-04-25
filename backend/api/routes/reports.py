import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from storage import supabase_client
from api.middleware.auth import get_tenant_id

router = APIRouter(prefix="/api", tags=["reports"])

LIB_DIR = Path(__file__).parent.parent.parent / "lib"


async def _render_pdf(spec: dict, filename: str) -> Response:
    with tempfile.TemporaryDirectory() as tmp:
        spec_path = os.path.join(tmp, "spec.json")
        out_path = os.path.join(tmp, "report.pdf")

        with open(spec_path, "w", encoding="utf-8") as f:
            json.dump(spec, f)

        # asyncio.create_subprocess_exec requires ProactorEventLoop on Windows,
        # but we use SelectorEventLoop (required by psycopg3). Use run_in_executor
        # with blocking subprocess.run() instead.
        def _run():
            return subprocess.run(
                ["python", str(LIB_DIR / "generate_report.py"),
                 "--spec", spec_path, "--output", out_path],
                capture_output=True, text=True,
            )

        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(loop.run_in_executor(None, _run), timeout=120)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="PDF generation timed out")

        if result.returncode != 0 or not os.path.exists(out_path):
            raise HTTPException(
                status_code=500,
                detail=f"PDF generation failed: {result.stderr[:500]}",
            )

        pdf_bytes = open(out_path, "rb").read()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/pdf")
async def generate_pdf_from_report(
    report: dict,
    tenant_id: str = Depends(get_tenant_id),
):
    from services.pdf_builder import build_pdf_spec
    spec = build_pdf_spec(report)
    report_id = report.get("report_id", "report")
    return await _render_pdf(spec, f"pbm-report-{report_id}.pdf")


@router.get("/reports/{report_id}")
async def get_report(report_id: str, tenant_id: str = Depends(get_tenant_id)):
    data = await supabase_client.get_report(report_id, tenant_id)
    if not data:
        raise HTTPException(status_code=404, detail="Report not found")
    return data
