from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.voice_service import VoiceService
import os
import uuid

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribes an uploaded audio file using Whisper."""
    # Save the file temporarily
    file_bytes = await file.read()
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
    
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
        
    try:
        text = VoiceService.transcribe_audio(temp_path)
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    if not text:
        raise HTTPException(status_code=400, detail="Could not transcribe the audio.")
        
    return {"text": text}


class TTSRequest(BaseModel):
    text: str

@router.post("/speak")
async def text_to_speech(request: TTSRequest):
    """Synthesizes text into speech and returns an audio file."""
    output_path = f"/tmp/{uuid.uuid4()}_output.wav"
    
    path = VoiceService.synthesize_speech(request.text, output_path)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=500, detail="Failed to synthesize speech.")
        
    return FileResponse(path, media_type="audio/wav", filename="speech.wav")
