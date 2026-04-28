"""
FastAPI Landmark Recognizer API
Chạy: uvicorn api.api:app --host 0.0.0.0 --port 8000
"""
import os
import sys
import csv
import time
import io
import logging
import shutil
import tempfile
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# ─── Thiết lập đường dẫn ──────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
models_dir = os.path.join(parent_dir, 'models')
weights_dir = os.path.join(parent_dir, 'weights')

if models_dir not in sys.path:
    sys.path.insert(0, models_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# ─── Cấu hình logging ────────────────────────────────────────────────────────
logger = logging.getLogger("LandmarkAPI")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ─── Load bảng tra cứu tên địa điểm từ hash_locations.csv ────────────────────
hash_locations_path = os.path.join(parent_dir, 'hash_locations.csv')
location_lookup = {}

def load_location_lookup():
    """Load bảng ánh xạ id -> location_name từ hash_locations.csv"""
    global location_lookup
    if os.path.exists(hash_locations_path):
        with open(hash_locations_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                location_lookup[str(row['id']).strip()] = row['location_name'].strip()
        logger.info("Đã load %d địa điểm từ hash_locations.csv", len(location_lookup))
    else:
        logger.warning("Không tìm thấy hash_locations.csv tại %s", hash_locations_path)

# ─── Biến global cho recognizer ───────────────────────────────────────────────
recognizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Khởi tạo model và database khi server start, giải phóng khi shutdown."""
    global recognizer
    
    logger.info("=" * 60)
    logger.info("  KHỞI TẠO LANDMARK RECOGNIZER API")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Load bảng tra cứu
    load_location_lookup()
    
    # Khởi tạo recognizer
    from landmark_recognizer import LandmarkRecognizer
    recognizer = LandmarkRecognizer()
    logger.info("Device: %s", recognizer.device)
    
    # Load model DINOv2
    recognizer.load_model(weights_dir=weights_dir)
    
    # Load database FAISS
    recognizer.load_database(db_dir=weights_dir)
    
    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("  SERVER SẴN SÀNG! Tổng thời gian khởi tạo: %.2fs", elapsed)
    logger.info("=" * 60)
    
    yield  # Server đang chạy
    
    # Shutdown
    logger.info("Server đang tắt...")
    recognizer = None

# ─── Khởi tạo FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(
    title="Landmark Recognizer API",
    description="API nhận dạng địa điểm Việt Nam sử dụng DINOv2 + FAISS + RANSAC",
    version="1.0.0",
    lifespan=lifespan
)

# CORS cho phép truy cập từ mọi nguồn (phù hợp cho VPS public)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (Ảnh lưu thẳng vào RAM, không dùng thư mục tạm nữa)


# ─── Pydantic models ─────────────────────────────────────────────────────────
class PredictResponse(BaseModel):
    success: bool
    label: Optional[str] = None
    location_name: Optional[str] = None
    inliers: int
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    device: str
    faiss_ready: bool
    total_vectors: int
    total_labels: int


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/", tags=["General"])
async def root():
    """Trang chủ API"""
    return {
        "service": "Landmark Recognizer API",
        "version": "1.0.0",
        "endpoints": {
            "POST /predict": "Nhận dạng địa điểm từ ảnh upload",
            "GET /health": "Kiểm tra trạng thái hệ thống",
            "GET /labels": "Danh sách các địa điểm trong database",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Kiểm tra trạng thái hệ thống"""
    if recognizer is None:
        raise HTTPException(status_code=503, detail="Hệ thống chưa sẵn sàng.")
    
    faiss_ready = hasattr(recognizer, 'index')
    return HealthResponse(
        status="healthy",
        device=str(recognizer.device),
        faiss_ready=faiss_ready,
        total_vectors=recognizer.index.ntotal if faiss_ready else 0,
        total_labels=len(set(recognizer.labels)) if hasattr(recognizer, 'labels') else 0,
    )


@app.get("/labels", tags=["Database"])
async def get_labels():
    """Lấy danh sách các địa điểm trong database"""
    if recognizer is None or not hasattr(recognizer, 'labels'):
        raise HTTPException(status_code=503, detail="Database chưa được load.")
    
    unique_labels = sorted(set(recognizer.labels.tolist()))
    result = []
    for label_id in unique_labels:
        entry = {"id": label_id}
        location_name = location_lookup.get(str(label_id))
        if location_name:
            entry["name"] = location_name
        result.append(entry)
    
    return {
        "total": len(result),
        "labels": result
    }


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
async def predict(file: UploadFile = File(...)):
    """
    Nhận dạng địa điểm từ ảnh upload.
    
    - **file**: File ảnh (JPG, JPEG, PNG)
    - Trả về: Tên địa điểm, độ tin cậy (inliers), thời gian xử lý
    """
    if recognizer is None:
        raise HTTPException(status_code=503, detail="Hệ thống chưa sẵn sàng.")
    
    if not hasattr(recognizer, 'index'):
        raise HTTPException(status_code=503, detail="FAISS Index chưa được khởi tạo.")
    
    # Kiểm tra định dạng file
    allowed_extensions = {'.jpg', '.jpeg', '.png'}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng file không hợp lệ: '{file_ext}'. Chấp nhận: {allowed_extensions}"
        )
    
    try:
        content = await file.read()
        file_size_kb = len(content) / 1024
        logger.info("Nhận ảnh upload: %s (%.1f KB)", file.filename, file_size_kb)
        
        # Load trực tiếp lên RAM
        image_stream = io.BytesIO(content)
        
        # Predict từ RAM
        result = recognizer.predict(image_stream)
        
        if result[0] is None:
            return PredictResponse(
                success=False,
                label=None,
                location_name=None,
                inliers=result[1],
                processing_time=0,
            )
        
        matched_img, inliers, elapsed = result
        label = str(recognizer.labels[recognizer.image_paths.tolist().index(matched_img)] 
                     if matched_img in recognizer.image_paths else "unknown")
        
        # Tra cứu tên địa điểm từ hash_locations.csv
        location_name = location_lookup.get(label, None)
        
        logger.info("Predict thành công: label=%s, name=%s, inliers=%d, time=%.2fs",
                     label, location_name, inliers, elapsed)
        
        return PredictResponse(
            success=True,
            label=label,
            location_name=location_name,
            inliers=inliers,
            processing_time=round(elapsed, 3),
        )
        
    except Exception as e:
        logger.error("Lỗi khi predict: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý ảnh: {str(e)}")


# ─── Chạy trực tiếp ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )
