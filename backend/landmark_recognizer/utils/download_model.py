from huggingface_hub import hf_hub_download
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


def download_model(file_name = None, local_dir = None):
    print("="*50)
    print(f"Đang gọi HuggingFace để tải {file_name} ....")
    print("="*50)
    try:
        hf_hub_download(
            repo_id="nquocdat06/landmark-features",
            repo_type="dataset", 
            filename=file_name,
            local_dir=local_dir
        )
        print("Tải model thành công!")
    except Exception as e:
        print(f"Lỗi khi tải model: {e}")
