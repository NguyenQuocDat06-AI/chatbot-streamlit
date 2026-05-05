import logging
import base64
import io
from datetime import datetime
from PIL import Image
from google.cloud.firestore_v1.base_query import FieldFilter
from backend.core.config import db

logger = logging.getLogger("LandmarkAPI.Database")


class DatabaseService:

    @staticmethod
    def compress_image_to_base64(image_bytes: bytes, max_size: int = 800, quality: int = 70) -> str:
        """Resize và nén ảnh, trả về base64 string."""
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((max_size, max_size))
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    # ═══════════════════════════════════════════════════════════════════════
    #  Conversation CRUD
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_conversation(user_id: str, title: str = "Cuộc trò chuyện mới") -> dict | None:
        if db is None:
            return None
        try:
            doc_ref = db.collection("conversations").document()
            data = {
                "user_id": user_id,
                "title": title,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            doc_ref.set(data)
            return {"id": doc_ref.id, "title": title}
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None

    @staticmethod
    def list_conversations(user_id: str, limit: int = 50) -> list:
        if db is None:
            return []
        try:
            docs = db.collection("conversations") \
                .where(filter=FieldFilter("user_id", "==", user_id)) \
                .stream()
            conversations = []
            for doc in docs:
                data = doc.to_dict()
                conversations.append({
                    "id": doc.id,
                    "title": data.get("title", ""),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                })
            conversations.sort(key=lambda x: x.get("updated_at", datetime.min), reverse=True)
            return conversations[:limit]
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return []

    @staticmethod
    def get_conversation_messages(user_id: str, conv_id: str) -> dict | None:
        if db is None:
            return None
        try:
            conv_ref = db.collection("conversations").document(conv_id)
            conv_doc = conv_ref.get()
            if not conv_doc.exists:
                return None
            conv_data = conv_doc.to_dict()
            if conv_data.get("user_id") != user_id:
                return None

            msgs_stream = conv_ref.collection("messages").stream()
            messages = []
            for msg in msgs_stream:
                d = msg.to_dict()
                messages.append({
                    "id": msg.id,
                    "role": d.get("role", ""),
                    "content_type": d.get("content_type", "text"),
                    "content": d.get("content", ""),
                    "timestamp": d.get("timestamp")
                })
            messages.sort(key=lambda x: x.get("timestamp", datetime.min))
            return {"id": conv_id, "title": conv_data.get("title", ""), "messages": messages}
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None

    @staticmethod
    def add_message(conv_id: str, role: str, content_type: str, content: str) -> str | None:
        if db is None:
            return None
        try:
            conv_ref = db.collection("conversations").document(conv_id)
            msg_ref = conv_ref.collection("messages").document()
            msg_ref.set({
                "role": role,
                "content_type": content_type,
                "content": content,
                "timestamp": datetime.utcnow()
            })
            conv_ref.update({"updated_at": datetime.utcnow()})
            return msg_ref.id
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return None

    @staticmethod
    def update_conversation_title(conv_id: str, title: str):
        if db is None:
            return
        try:
            db.collection("conversations").document(conv_id).update({"title": title})
        except Exception as e:
            logger.error(f"Error updating title: {e}")

    @staticmethod
    def delete_conversation(user_id: str, conv_id: str) -> bool:
        if db is None:
            return False
        try:
            conv_ref = db.collection("conversations").document(conv_id)
            conv_doc = conv_ref.get()
            if not conv_doc.exists or conv_doc.to_dict().get("user_id") != user_id:
                return False
            for msg in conv_ref.collection("messages").stream():
                msg.reference.delete()
            conv_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
