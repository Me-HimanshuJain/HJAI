from fastapi import APIRouter, UploadFile, File, HTTPException
from services.vision_service import VisionService

router = APIRouter()

@router.post("/ocr")
async def extract_text(file: UploadFile = File(...)):
    """Extracts text from an uploaded image using OCR."""
    file_bytes = await file.read()
    
    text = VisionService.extract_text_from_image(file_bytes)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from the image.")
        
    return {"extracted_text": text}
