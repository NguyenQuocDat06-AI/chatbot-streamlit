import torch
from PIL import Image
import numpy as np
import h5py
from tqdm import tqdm

def extract_features(image_path, model, transform, device):
    """
    Trích xuất đặc trưng (global và local) từ một hình ảnh bằng mô hình.
    """
    img = Image.open(image_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        ret = model.forward_features(img_tensor)
        cls_token = ret['x_norm_clstoken'].cpu().numpy()[0]
        patch_tokens = ret['x_norm_patchtokens'].cpu().numpy()[0].astype(np.float16)
    return cls_token, patch_tokens

def extract_features_batch(image_paths, labels, model, transform, device, global_features_path, labels_path, image_paths_path, local_features_path):
    global_feats_list = []
    
    with h5py.File(local_features_path, 'w') as h5f:
        for i, img_path in enumerate(tqdm(image_paths, desc="Features Extraction")):
            try:
                cls_token, patch_tokens = extract_features(img_path, model, transform, device)
                global_feats_list.append(cls_token)
                h5f.create_dataset(f'idx_{i}', data=patch_tokens, compression="gzip", compression_opts=4)
            except Exception as e:
                print(f"\n  Lỗi: Không thể xử lý ảnh {img_path}: {e}")
                global_feats_list.append(np.zeros(384, dtype=np.float32))
                h5f.create_dataset(f'idx_{i}', data=np.zeros((1, 384), dtype=np.float16), compression="gzip", compression_opts=4)

    print("Đang lưu ...")
    np.save(global_features_path, np.array(global_feats_list, dtype=np.float32))
    np.save(labels_path, np.array(labels, dtype=object))
    np.save(image_paths_path, np.array(image_paths, dtype=object))
    print("Đã lưu thành công!")


def append_features_batch(new_image_paths, new_labels, old_global_feats, old_labels, old_image_paths, 
                          model, transform, device, global_features_path, labels_path, image_paths_path, local_features_path):
    current_idx = len(old_image_paths)
    new_global_feats_list = []
    
    with h5py.File(local_features_path, 'a') as h5f:
        for i, img_path in enumerate(tqdm(new_image_paths, desc="Features Update")):
            try:
                cls_token, patch_tokens = extract_features(img_path, model, transform, device)
                new_global_feats_list.append(cls_token)
                h5f.create_dataset(f'idx_{current_idx + i}', data=patch_tokens, compression="gzip", compression_opts=4)
            except Exception as e:
                print(f"\n  Lỗi: Không thể xử lý ảnh {img_path}: {e}")
                new_global_feats_list.append(np.zeros(384, dtype=np.float32))
                h5f.create_dataset(f'idx_{current_idx + i}', data=np.zeros((1, 384), dtype=np.float16), compression="gzip", compression_opts=4)

    updated_global_feats = np.vstack((old_global_feats, np.array(new_global_feats_list, dtype=np.float32)))
    updated_labels = old_labels + new_labels
    updated_image_paths = old_image_paths + new_image_paths
    
    print("Đang lưu bản cập nhật ...")
    np.save(global_features_path, updated_global_feats)
    np.save(labels_path, np.array(updated_labels, dtype=object))
    np.save(image_paths_path, np.array(updated_image_paths, dtype=object))
    print(f"\n✅ Hoàn tất cập nhật! Tổng số ảnh hiện hành: {len(updated_image_paths)}")