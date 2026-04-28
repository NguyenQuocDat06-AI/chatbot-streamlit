import logging
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter, BaseCompositeFilter
from backend.core.config import db
from backend.schemas.message import ChatHistoryItem

logger = logging.getLogger("LandmarkAPI.Database")

class DatabaseService:
    @staticmethod
    def save_chat_history(user_id: str, file_name: str, location_name: str, inliers: int, processing_time: float) -> str:
        """Lưu lịch sử dự đoán vào Firestore"""
        if db is None:
            logger.warning("Firestore is not initialized. Skip saving.")
            return None
            
        try:
            doc_ref = db.collection("chat_history").document()
            data = {
                "user_id": user_id,
                "file_name": file_name,
                "location_name": location_name,
                "inliers": inliers,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow()
            }
            doc_ref.set(data)
            logger.info(f"Saved chat history for user {user_id}: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
            return None

    @staticmethod
    def get_chat_history(user_id: str, limit: int = 50) -> list[ChatHistoryItem]:
        """Lấy danh sách lịch sử dự đoán của một user"""
        if db is None:
            logger.warning("Firestore is not initialized.")
            return []
            
        try:
            # Sắp xếp theo thời gian mới nhất (cần tạo composite index trên Firestore nếu query cả bằng user_id và orderBy)
            # Tạm thời query theo user_id, sau đó sort ở code backend để tránh lỗi require index của Firestore.
            docs = db.collection("chat_history")\
                .where(filter=FieldFilter("user_id", "==", user_id))\
                .stream()
                
            history = []
            for doc in docs:
                data = doc.to_dict()
                item = ChatHistoryItem(
                    id=doc.id,
                    user_id=data.get("user_id", ""),
                    file_name=data.get("file_name", ""),
                    location_name=data.get("location_name", ""),
                    inliers=data.get("inliers", 0),
                    processing_time=data.get("processing_time", 0.0),
                    timestamp=data.get("timestamp")
                )
                history.append(item)
            
            # Sort descending by timestamp
            history.sort(key=lambda x: x.timestamp, reverse=True)
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []
