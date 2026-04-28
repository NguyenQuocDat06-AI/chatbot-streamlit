```text
chatbot-streamlit/
├── .gitignore                 # Dùng để loại bỏ các file cache, file tạm, secrets, token, private key
├── README.md                  # Chứa hướng dẫn cài đặt environment, cách chạy frontend/backend và link video demo
├── requirements.txt           # Liệt kê các thư viện Python cần thiết (FastAPI, Streamlit, PyTorch, v.v.)
├── frontend/                  # Thư mục dùng để hiển thị giao diện và gửi request
│   ├── app.py                 # File chính chạy giao diện Streamlit, hiển thị đăng nhập và tính năng gửi ảnh
│   ├── firebase_auth.py       # Xử lý giao diện và logic đăng nhập, đăng xuất bằng Firebase Authentication
│   └── components/            # (Tùy chọn) Chứa các module giao diện nhỏ gọn, hiển thị kết quả
└── backend/                   # Thư mục dùng để xử lý logic, xác thực và thao tác với database
    ├── main.py                # File khởi tạo app FastAPI, chứa các endpoint cơ bản như GET / và GET /health
    ├── routers/               # Chứa các file phân chia endpoint
    │   ├── auth.py            # Chứa endpoint xác thực phù hợp
    │   └── chat.py            # Chứa endpoint cho feature chính (POST /chat) và endpoint đọc dữ liệu (GET /messages)
    ├── schemas/               # Định nghĩa các model dữ liệu vào/ra (Pydantic models)
    │   └── message.py         # Định dạng dữ liệu trả về cho frontend và cấu trúc lưu vào database
    ├── services/              # Nơi chứa các hàm xử lý logic nghiệp vụ tách biệt khỏi router
    │   ├── database.py        # Thao tác với database để lưu dữ liệu và đọc lại dữ liệu đã lưu
    │   └── inference.py       # Nơi gọi model để trích xuất tên địa điểm từ ảnh
    └── core/                  # Nơi lưu cấu hình Firebase Admin SDK
        └── config.py
```