# Landmark Detector API & Streamlit UI (Lab 2)

## Thông tin sinh viên
- **MSSV**: 24120282
- **Họ tên**: Nguyễn Quốc Đạt
- **Lớp**: 24CTT3

Dự án này là một ứng dụng Web phân tách rõ ràng Frontend và Backend, sử dụng mô hình học sâu (DINOv2) kết hợp FAISS để nhận diện địa danh tại Việt Nam. Nó tích hợp Firebase Authentication và Firestore để quản lý người dùng và lưu trữ lịch sử nhận diện.

## Liên kết quan trọng (Links)

### Video Demo
[![Video Demo](https://img.youtube.com/vi/19D8S_z8868/maxresdefault.jpg)](https://youtu.be/19D8S_z8868)

- **YouTube**: [https://youtu.be/19D8S_z8868](https://youtu.be/19D8S_z8868)
- **Google Drive**: [https://drive.google.com/file/d/15e1xHXoHSlgfyzIN0tkjPr6R3lYFcKfQ/view?usp=sharing](https://drive.google.com/file/d/15e1xHXoHSlgfyzIN0tkjPr6R3lYFcKfQ/view?usp=sharing)

### Trọng số mô hình đã train
- **Hugging Face**: [https://huggingface.co/datasets/nquocdat06/landmark-features](https://huggingface.co/datasets/nquocdat06/landmark-features)

## Kiến trúc Hệ Thống
- **Frontend:** Streamlit (UI/UX, Login, Upload Ảnh, Hiển thị Kết quả)
- **Backend:** FastAPI (REST API, logic xử lý)
- **AI Model:** PyTorch (DINOv2), FAISS, RANSAC
- **Database/Auth:** Firebase (Authentication qua REST API cho Frontend & Admin SDK cho Backend; Firestore để lưu lịch sử).

## Cấu trúc Thư Mục
```text
chatbot-streamlit/
├── .gitignore                 (Dùng để loại bỏ các file cache, file tạm, secrets, token, private key)
├── README.md                  (Chứa hướng dẫn cài đặt environment, cách chạy frontend/backend và link video demo)
├── requirements.txt           (Liệt kê các thư viện Python cần thiết (FastAPI, Streamlit, PyTorch, v.v.))
├── secrets.toml.example       (File cấu hình mẫu, cần đổi tên thành secrets.toml và điền các key của bạn)
├── frontend/                  (Thư mục dùng để hiển thị giao diện và gửi request)
│   ├── app.py                 (File chính chạy giao diện Streamlit, hiển thị đăng nhập và tính năng gửi ảnh)
│   ├── firebase_auth.py       (Xử lý giao diện và logic đăng nhập, đăng xuất bằng Firebase Authentication)
│   └── components/            (Tùy chọn) Chứa các module giao diện nhỏ gọn, hiển thị kết quả
└── backend/                   (Thư mục dùng để xử lý logic, xác thực và thao tác với database)
    ├── main.py                (File khởi tạo app FastAPI, chứa các endpoint cơ bản như GET / và GET /health)
    ├── core/                  (Load config từ secrets.toml và setup Firebase Admin)
    ├── routers/               (Endpoints cho /auth và /chat)
    ├── schemas/               (Pydantic models)
    ├── services/              (Thao tác Database Firestore, Model Inference)
    └── landmark_recognizer/   (Model weights, FAISS database, script AI)
```

## Hướng dẫn cài đặt

1. **Cài đặt môi trường Python (Khuyến nghị dùng virtual environment):**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Cấu hình biến môi trường (`secrets.toml`):**
Dự án có cung cấp sẵn file mẫu `secrets.toml.example`. Bạn cần copy hoặc đổi tên file này thành `secrets.toml` tại thư mục gốc của project, sau đó điền đầy đủ các thông tin:
- `[firebase_client]`: API keys và config cho Firebase Client (dùng cho Streamlit Frontend).
- `[firebase_admin]`: Thông tin từ Service Account JSON để Backend khởi tạo Firebase Admin SDK.
- `[google-login]`: Thông tin Client ID, Secret, Redirect URI phục vụ tính năng đăng nhập Google OAuth2.

3. **Chạy Backend (FastAPI):**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation có thể xem tại: `http://localhost:8000/docs`

4. **Chạy Frontend (Streamlit):**
Mở một terminal mới (nhớ active venv) và chạy:
```bash
streamlit run frontend/app.py
```
Ứng dụng sẽ mở tại: `http://localhost:8501`
