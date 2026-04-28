import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.schemas.message import PredictResponse, ChatHistoryResponse
from backend.services.inference import inference_service
from backend.services.database import DatabaseService
from backend.routers.auth import get_current_user

logger = logging.getLogger("LandmarkAPI.Chat")
router = APIRouter(prefix="/chat", tags=["Chat & Prediction"])

@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    """Nhận diện địa điểm từ ảnh và lưu lịch sử"""
    # Kiểm tra phần mở rộng file
    allowed_extensions = {'.jpg', '.jpeg', '.png'}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file extension. Allowed: {allowed_extensions}")

    try:
        content = await file.read()
        
        # Gọi mô hình
        result = inference_service.predict(content)
        
        # Nếu dự đoán thành công, lưu vào DB
        if result["success"]:
            DatabaseService.save_chat_history(
                user_id=user_id,
                file_name=file.filename,
                location_name=result["location_name"],
                inliers=result["inliers"],
                processing_time=result["processing_time"]
            )
            
        return result
        
    except Exception as e:
        logger.error(f"Error in predict endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(user_id: str = Depends(get_current_user)):
    """Lấy lịch sử tra cứu của user"""
    history = DatabaseService.get_chat_history(user_id)
    return {
        "total": len(history),
        "history": history
    }
