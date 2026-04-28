import os
import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
import h5py
import logging
from tqdm import tqdm
from pathlib import Path
import sys
import time
import cv2
import faiss

# Cấu hình logging chi tiết cho VPS
logger = logging.getLogger("LandmarkRecognizer")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

# Thiết lập đường dẫn thư mục cho sys.path TRƯỚC KHI gọi thư viện từ folder khác
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.feature_extractor import extract_features
from utils.download_model import download_model
from utils.feature_extractor import extract_features_batch
from utils.feature_extractor import append_features_batch
from utils.file_utils import scan_image_folder
from utils.matcher import match_local_ransac


# Đường dẫn đã được sửa trỏ thẳng ra ngoài thư mục weights chính xác của Project
weights_dir = os.path.join(parent_dir, "weights")
model_file = 'dinov2_vits14_reg.pth'
db_files = ['global_features.npy', 'image_paths.npy', 'labels.npy', 'local_features.h5']

class LandmarkRecognizer:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transform = T.Compose([
            T.Resize((336, 336)),
            T.ToTensor(),
            T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ])
    
    def load_model(self, weights_dir=weights_dir):
        logger.info("="*50)
        logger.info("Đang khởi tạo mạng thuật toán dinov2_vits14_reg từ PyTorch Hub ...")
        logger.info("="*50)
        # PyTorch Hub sẽ tự động tải trọng số DINO từ facebookresearch (nếu chưa có)
        self.model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vits14_reg')
        self.model.eval()
        self.model.to(self.device)
        logger.info("Khởi tạo model dinov2_vits14_reg thành công! Device: %s", self.device)
        
    def load_database(self, db_dir=weights_dir):
        os.makedirs(db_dir, exist_ok=True)
        for f in db_files:
            logger.info("Kiểm tra/Tải file CSDL: %s (db_dir=%s)", f, db_dir)
            file_path = os.path.join(db_dir, f)
            if not os.path.exists(file_path):
                logger.info("File %s chưa tồn tại. Bắt đầu tải từ HuggingFace...", f)
                download_model(file_name=f, local_dir=db_dir)
                if os.path.exists(file_path):
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    logger.info("Tải file %s thành công! (%.2f MB)", f, file_size_mb)
                else:
                    logger.error("Không thể tải Database online '%s' từ HuggingFace. Kiểm tra kết nối mạng.", f)
            else:
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                logger.info("File %s đã tồn tại. (%.2f MB)", f, file_size_mb)
                
        global_features_path = os.path.join(db_dir, 'global_features.npy')
        labels_path = os.path.join(db_dir, 'labels.npy')
        image_paths_path = os.path.join(db_dir, 'image_paths.npy')
        self.h5_path = os.path.join(db_dir, 'local_features.h5')
        
        if not os.path.exists(global_features_path):
            logger.warning("CSDL tại %s chưa đủ file. Bỏ qua khởi tạo FAISS.", db_dir)
            return
            
        logger.info("Đang khởi tạo dữ liệu FAISS và load Metadata lên RAM...")
        labels_fixed_path = os.path.join(db_dir, 'labels_fixed.npy')
        self.labels = np.load(labels_fixed_path if os.path.exists(labels_fixed_path) else labels_path, allow_pickle=True)
        self.image_paths = np.load(image_paths_path, allow_pickle=True)
        global_features = np.load(global_features_path)
        logger.info("Đã load: %d vectors, %d labels, %d image_paths", len(global_features), len(self.labels), len(self.image_paths))
        
        norms = np.linalg.norm(global_features, axis=1, keepdims=True)
        self.db_globals = global_features / (norms + 1e-8)
        
        cpu_index = faiss.IndexFlatIP(384)
        try:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            logger.info("FAISS đang chạy trên GPU.")
        except Exception as e:
            self.index = cpu_index
            logger.warning("FAISS GPU không khả dụng, fallback sang CPU. Lý do: %s", str(e))
            
        self.index.add(self.db_globals)
        logger.info("FAISS Index đã sẵn sàng. Tổng số vectors: %d", self.index.ntotal)
    
    def train(self, dataset_dir="dataset", db_dir="weights"):
        dataset_path = Path(dataset_dir)
        logger.info("Bắt đầu training. Device: %s | Dataset: %s | DB: %s", self.device, dataset_dir, db_dir)
        if not dataset_path.exists():
            logger.error("Thư mục dataset '%s' không tồn tại! Hủy training.", dataset_dir)
            return
            
        image_paths, labels = scan_image_folder(dataset_dir)
        total_images = len(image_paths)
        unique_labels = len(set(labels))
        logger.info("Quét xong: %d ảnh thuộc %d địa điểm.", total_images, unique_labels)
        os.makedirs(db_dir, exist_ok=True)
        global_features_path = os.path.join(db_dir, 'global_features.npy')
        labels_path = os.path.join(db_dir, 'labels.npy')
        image_paths_path = os.path.join(db_dir, 'image_paths.npy')
        local_features_path = os.path.join(db_dir, 'local_features.h5')
    
        global_feats_list = []
        extract_features_batch(image_paths, labels, self.model, self.transform, self.device, global_features_path, labels_path, image_paths_path, local_features_path)
        logger.info("Training hoàn tất. Output files:")
        logger.info("  Global Features: %s", global_features_path)
        logger.info("  Metadata (Labels & Paths): %s", labels_path)
        logger.info("  Local Features (HDF5): %s", local_features_path)

    def retrain(self, new_dataset_dir, db_dir=weights_dir):
        logger.info("Bắt đầu retrain. New dataset: %s | DB: %s", new_dataset_dir, db_dir)
        global_features_path = os.path.join(db_dir, 'global_features.npy')
        labels_path = os.path.join(db_dir, 'labels.npy')
        image_paths_path = os.path.join(db_dir, 'image_paths.npy')
        local_features_path = os.path.join(db_dir, 'local_features.h5')
        
        required_paths = [global_features_path, labels_path, image_paths_path, local_features_path]
        missing = [p for p in required_paths if not os.path.exists(p)]
        if missing:
            logger.error("CSDL tại %s thiếu file: %s. Vui lòng chạy train() trước.", db_dir, missing)
            return
            
        logger.info("Đang tải dữ liệu hiện tại từ %s ...", db_dir)
        old_global_feats = np.load(global_features_path)
        old_labels = np.load(labels_path, allow_pickle=True).tolist()
        old_image_paths = np.load(image_paths_path, allow_pickle=True).tolist()
        logger.info("Dữ liệu cũ: %d vectors, %d labels.", len(old_global_feats), len(old_labels))
        
        # Quét thư mục lấy file mới
        dataset_path = Path(new_dataset_dir)
        logger.info("Bắt đầu quét thư mục mới: %s", dataset_path)
        
        if not dataset_path.exists():
            logger.error("Thư mục '%s' không tồn tại! Hủy retrain.", new_dataset_dir)
            return
            
        new_image_paths, new_labels = scan_image_folder(new_dataset_dir, exclude_paths=old_image_paths)
                            
        total_images = len(new_image_paths)
        if total_images == 0:
            logger.warning("Không có ảnh mới nào được tìm thấy hoặc tất cả đều đã có trong database.")
            return
            
        logger.info("Tìm thấy %d ảnh mới thuộc %d địa điểm.", total_images, len(set(new_labels)))
        logger.info("Bắt đầu trích xuất đặc trưng cho dữ liệu mới...")
        
        append_features_batch(
            new_image_paths=new_image_paths, 
            new_labels=new_labels, 
            old_global_feats=old_global_feats, 
            old_labels=old_labels, 
            old_image_paths=old_image_paths,
            model=self.model, 
            transform=self.transform, 
            device=self.device, 
            global_features_path=global_features_path, 
            labels_path=labels_path, 
            image_paths_path=image_paths_path, 
            local_features_path=local_features_path
        )
        logger.info("Retrain hoàn tất.")

    def predict(self, query_img_path):
        from utils.matcher import match_local_ransac
        
        if not hasattr(self, 'index'):
            logger.error("FAISS Index chưa được nạp. Gọi load_database() trước khi predict().")
            return None, 0
            
        start_time = time.time()
        logger.info("Nhận truy vấn mới: %s", query_img_path)
        
        query_global, query_local = extract_features(query_img_path, self.model, self.transform, self.device)
        query_global = query_global / (np.linalg.norm(query_global) + 1e-8)
        
        D, I = self.index.search(query_global.reshape(1, -1), k=10)
        top10_idx = I[0]
        
        best_inliers = -1
        best_idx = -1
        
        logger.info("Bắt đầu ghép cặp RANSAC cho top-10 candidates...")
        with h5py.File(self.h5_path, 'r') as h5f:
            for i, cand_id in enumerate(top10_idx):
                try: 
                    cand_local = h5f[f'idx_{cand_id}'][()].astype(np.float32)
                except KeyError:
                    logger.debug("Bỏ qua candidate idx_%d: không tìm thấy trong HDF5.", cand_id)
                    continue
                    
                inliers, mutual_dots = match_local_ransac(query_local, cand_local)
                logger.debug("[Top %2d] ID: %5d | Inliers: %3d/%3d | Cosine: %.4f | Label: %s",
                             i+1, cand_id, inliers, mutual_dots, D[0][i], self.labels[cand_id])
                
                if inliers > best_inliers:
                    best_inliers = inliers
                    best_idx = cand_id
        
        elapsed = time.time() - start_time
        logger.info("RANSAC hoàn tất. Thời gian xử lý: %.2fs | Best inliers: %d", elapsed, best_inliers)
        
        THRESHOLD = 15  
        if best_inliers < THRESHOLD:
            logger.warning("Tỷ lệ khớp chưa đạt chuẩn (inliers=%d < threshold=%d). Query: %s",
                           best_inliers, THRESHOLD, query_img_path)
            return None, best_inliers

        final_label = self.labels[best_idx]
        final_match_img = self.image_paths[best_idx]
        logger.info("KẾT QUẢ: [%s] | Inliers: %d | Match: %s | Thời gian: %.2fs",
                    final_label, best_inliers, final_match_img, elapsed)
        return final_match_img, best_inliers, time.time() - start_time
