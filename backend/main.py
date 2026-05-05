import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.inference import inference_service
from backend.routers import auth, chat

logger = logging.getLogger("LandmarkAPI.Main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo model và database khi server start."""
    logger.info("=" * 60)
    logger.info("  KHỞI TẠO LANDMARK RECOGNIZER API")
    logger.info("=" * 60)
    
    # Init inference model
    inference_service.initialize()
    
    logger.info("=" * 60)
    logger.info("  SERVER SẴN SÀNG!")
    logger.info("=" * 60)
    
    yield
    
    logger.info("Server đang tắt...")

app = FastAPI(
    title="Landmark Recognizer API",
    description="API nhận dạng địa điểm Việt Nam, có tích hợp Firebase Auth và Firestore",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/", tags=["General"])
async def root():
    return {
        "service": "Landmark Recognizer API",
        "version": "2.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["General"])
async def health_check():
    """Kiểm tra trạng thái hệ thống: model, FAISS index, database."""
    recognizer = inference_service.recognizer
    
    faiss_ready = recognizer is not None and hasattr(recognizer, 'index')
    total_vectors = recognizer.index.ntotal if faiss_ready else 0
    total_labels = len(recognizer.labels) if (recognizer and hasattr(recognizer, 'labels')) else 0
    device = str(recognizer.device) if recognizer else "N/A"
    
    status = "healthy" if faiss_ready else "degraded"
    
    return {
        "status": status,
        "device": device,
        "faiss_ready": faiss_ready,
        "total_vectors": total_vectors,
        "total_labels": total_labels
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
