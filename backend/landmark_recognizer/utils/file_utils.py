import os
from pathlib import Path

def scan_image_folder(dataset_dir, exclude_paths=None):
    """
    Quét đệ quy thư mục dataset để lấy file ảnh (.jpg, .jpeg, .png).
    :param dataset_dir: Đường dẫn tới thư mục dataset.
    :param exclude_paths: List hoặc Set các đường dẫn file ảnh cần bỏ qua.
    :return: (image_paths, labels) tuple chứa list đường dẫn ảnh và list nhãn (tên thư mục con).
    """
    dataset_path = Path(dataset_dir)
    image_paths = []
    labels = []
    
    if not dataset_path.exists():
        return image_paths, labels

    exclude_set = set(exclude_paths) if exclude_paths is not None else set()
    
    for class_folder in dataset_path.iterdir():
        if class_folder.is_dir():
            class_id = class_folder.name
            for img_file in class_folder.glob('*.*'):
                if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    path_str = str(img_file)
                    if path_str not in exclude_set:
                        image_paths.append(path_str)
                        labels.append(class_id)
                        
    return image_paths, labels
