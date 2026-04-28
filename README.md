chatbot-streamlit/
├── .gitignore                 # Dùng để loại bỏ các file cache, file tạm, secrets, token, private key [cite: 110, 124, 125, 126]
├── README.md                  # Chứa hướng dẫn cài đặt environment, cách chạy frontend/backend và link video demo [cite: 43, 116, 119, 120, 121, 122, 123]
├── requirements.txt           # Liệt kê các thư viện Python cần thiết (FastAPI, Streamlit, PyTorch, v.v.) [cite: 44, 109, 118]
├── frontend/                  # Thư mục dùng để hiển thị giao diện và gửi request [cite: 33, 41, 117]
│   ├── app.py                 # File chính chạy giao diện Streamlit, hiển thị đăng nhập và tính năng gửi ảnh [cite: 96, 98]
│   ├── firebase_auth.py       # Xử lý giao diện và logic đăng nhập, đăng xuất bằng Firebase Authentication [cite: 53, 55, 56]
│   └── components/            # (Tùy chọn) Chứa các module giao diện nhỏ gọn, hiển thị kết quả [cite: 99]
└── backend/                   # Thư mục dùng để xử lý logic, xác thực và thao tác với database [cite: 34, 42, 117]
    ├── main.py                # File khởi tạo app FastAPI, chứa các endpoint cơ bản như GET / và GET /health [cite: 85, 86, 87]
    ├── routers/               # Chứa các file phân chia endpoint [cite: 108]
    │   ├── auth.py            # Chứa endpoint xác thực phù hợp (ví dụ: /auth/login, /auth/me) [cite: 91]
    │   └── chat.py            # Chứa endpoint cho feature chính (ví dụ: POST /chat để nhận ảnh) và endpoint đọc dữ liệu (ví dụ: GET /messages) [cite: 92, 93]
    ├── schemas/               # Định nghĩa các model dữ liệu vào/ra (Pydantic models) [cite: 108]
    │   └── message.py         # Định dạng dữ liệu trả về cho frontend và cấu trúc lưu vào database
    ├── services/              # Nơi chứa các hàm xử lý logic nghiệp vụ tách biệt khỏi router [cite: 108]
    │   ├── database.py        # Thao tác với database để lưu dữ liệu và đọc lại dữ liệu đã lưu [cite: 75, 77, 78]
    │   └── inference.py       # Nơi gọi model hoặc dịch vụ xử lý nội dung để trích xuất tên địa điểm từ ảnh [cite: 71]
    └── core/                  # (Tùy chọn) Nơi lưu cấu hình Firebase Admin SDK và thiết lập hệ thống
        └── config.py