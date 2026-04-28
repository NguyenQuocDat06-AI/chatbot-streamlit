import os
import sys
import csv
import logging
import io
import time

logger = logging.getLogger("LandmarkAPI.Inference")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
models_dir = os.path.join(project_dir, 'backend', 'landmark_recognizer', 'models')
weights_dir = os.path.join(project_dir, 'backend', 'landmark_recognizer', 'weights')

if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

hash_locations_path = os.path.join(project_dir, 'backend', 'landmark_recognizer', 'hash_locations.csv')

class InferenceService:
    def __init__(self):
        self.recognizer = None
        self.location_lookup = {}
        
    def load_location_lookup(self):
        """Load bảng ánh xạ id -> location_name từ hash_locations.csv"""
        if os.path.exists(hash_locations_path):
            with open(hash_locations_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.location_lookup[str(row['id']).strip()] = row['location_name'].strip()
            logger.info("Đã load %d địa điểm từ hash_locations.csv", len(self.location_lookup))
        else:
            logger.warning("Không tìm thấy hash_locations.csv tại %s", hash_locations_path)

    def initialize(self):
        """Khởi tạo mô hình DINOv2 và FAISS Index."""
        logger.info("Khởi tạo InferenceService...")
        start_time = time.time()
        
        self.load_location_lookup()
        
        try:
            from landmark_recognizer import LandmarkRecognizer
            self.recognizer = LandmarkRecognizer()
            logger.info(f"Device: {self.recognizer.device}")
            
            # Load model DINOv2
            self.recognizer.load_model(weights_dir=weights_dir)
            
            # Load database FAISS
            self.recognizer.load_database(db_dir=weights_dir)
            
            elapsed = time.time() - start_time
            logger.info(f"InferenceService sẵn sàng sau {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo InferenceService: {e}")
            raise e

    def predict(self, file_content: bytes):
        """Thực hiện dự đoán từ bytes file ảnh."""
        if not self.recognizer or not hasattr(self.recognizer, 'index'):
            raise RuntimeError("Model or Database not initialized.")
            
        image_stream = io.BytesIO(file_content)
        result = self.recognizer.predict(image_stream)
        
        if result[0] is None:
            return {
                "success": False,
                "label": None,
                "location_name": None,
                "inliers": result[1],
                "processing_time": 0.0,
            }
            
        matched_img, inliers, elapsed = result
        label = str(self.recognizer.labels[self.recognizer.image_paths.tolist().index(matched_img)] 
                     if matched_img in self.recognizer.image_paths else "unknown")
        
        location_name = self.location_lookup.get(label, "Không xác định")
        
        return {
            "success": True,
            "label": label,
            "location_name": location_name,
            "inliers": inliers,
            "processing_time": round(elapsed, 3),
        }

# Global instance
inference_service = InferenceService()
