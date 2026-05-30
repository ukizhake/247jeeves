"""Import routes (broker CSV uploads)."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.schemas import FidelityImportResponse
from engine.import_.fidelity import parse_fidelity_csv

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/fidelity", response_model=FidelityImportResponse)
async def import_fidelity_csv(file: UploadFile = File(...)) -> FidelityImportResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a Fidelity Portfolio Positions .csv file")
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "CSV must be UTF-8 text") from exc
    result = parse_fidelity_csv(text)
    if result.position_count == 0:
        raise HTTPException(400, "No positions found — is this a Fidelity Portfolio Positions export?")
    return FidelityImportResponse(result=result)
