import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.schemas.message import (
    PredictResponse, ConversationListResponse,
    ConversationDetailResponse, CreateConversationResponse
)
from backend.services.inference import inference_service
from backend.services.database import DatabaseService
from backend.routers.auth import get_current_user

logger = logging.getLogger("LandmarkAPI.Chat")
router = APIRouter(prefix="/chat", tags=["Chat & Prediction"])


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(user_id: str = Depends(get_current_user)):
    """Tạo cuộc trò chuyện mới."""
    result = DatabaseService.create_conversation(user_id)
    if not result:
        raise HTTPException(status_code=500, detail="Could not create conversation")
    return result


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(user_id: str = Depends(get_current_user)):
    """Liệt kê tất cả cuộc trò chuyện của user."""
    convs = DatabaseService.list_conversations(user_id)
    return {"total": len(convs), "conversations": convs}


@router.get("/conversations/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(conv_id: str, user_id: str = Depends(get_current_user)):
    """Lấy chi tiết cuộc trò chuyện với tất cả tin nhắn."""
    result = DatabaseService.get_conversation_messages(user_id, conv_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user_id: str = Depends(get_current_user)):
    """Xoá cuộc trò chuyện."""
    success = DatabaseService.delete_conversation(user_id, conv_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@router.post("/conversations/{conv_id}/predict", response_model=PredictResponse)
async def predict_in_conversation(
    conv_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    """Nhận diện địa điểm và lưu tin nhắn vào cuộc trò chuyện."""
    allowed = {'.jpg', '.jpeg', '.png'}
    ext = Path(file.filename).suffix.lower() if file.filename else ''
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid file. Allowed: {allowed}")

    try:
        content = await file.read()

        # Lưu ảnh user (nén base64)
        img_b64 = DatabaseService.compress_image_to_base64(content)
        DatabaseService.add_message(conv_id, "user", "image", img_b64)

        # Chạy inference
        result = inference_service.predict(content)

        # Tạo reply text
        if result["success"]:
            reply = (
                f"📍 Đây có vẻ là **{result['location_name']}**.\n\n"
                f"*(Inliers: {result['inliers']} | Thời gian: {result['processing_time']}s)*"
            )
            DatabaseService.update_conversation_title(conv_id, result["location_name"])
        else:
            reply = "⚠️ Xin lỗi, tôi không thể nhận diện được địa điểm trong ảnh này."

        # Lưu reply
        DatabaseService.add_message(conv_id, "assistant", "text", reply)
        return result

    except Exception as e:
        logger.error(f"Error in predict: {e}")
        raise HTTPException(status_code=500, detail=str(e))
