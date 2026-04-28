import streamlit as st
import toml
import os
import requests
import time
from firebase_auth import FirebaseAuth
from PIL import Image

# ─── Cấu hình chung ────────────────────────────────────────────────────────
st.set_page_config(page_title="Landmark Detector", page_icon="🗺️", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, '..'))
secrets_path = os.path.join(project_dir, 'secrets.toml')

# Load API keys
try:
    config = toml.load(secrets_path)
    API_KEY = config.get("firebase_client", {}).get("apiKey", "")
    BACKEND_URL = "http://localhost:8000"
except Exception as e:
    st.error(f"Lỗi đọc file secrets.toml: {e}")
    st.stop()

auth = FirebaseAuth(API_KEY)

# ─── Xử lý Token từ Google Login (Query Params) ─────────────────────────────
if "idToken" in st.query_params:
    st.session_state.idToken = st.query_params["idToken"]
    st.session_state.user_email = st.query_params.get("email", "Google User")
    st.query_params.clear()
    st.rerun()

# ─── Khởi tạo Session State ─────────────────────────────────────────────────
if "idToken" not in st.session_state:
    st.session_state.idToken = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def logout():
    st.session_state.idToken = None
    st.session_state.user_email = None
    st.rerun()

# ─── Giao diện Đăng nhập / Đăng ký ───────────────────────────────────────────
if not st.session_state.idToken:
    st.title("Chào mừng đến với Landmark Detector AI")
    st.write("Vui lòng đăng nhập để sử dụng hệ thống nhận dạng địa điểm.")
    
    tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
    
    with tab1:
        st.subheader("Đăng nhập tài khoản")
        
        # Nút Đăng nhập bằng Google
        st.markdown(
            f'''
            <a href="{BACKEND_URL}/auth/google/start" target="_self">
                <div style="background-color: white; color: #444; border: 1px solid #ddd; border-radius: 4px; padding: 10px 15px; text-align: center; font-weight: 500; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 15px;">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="18" height="18"/>
                    Đăng nhập bằng Google
                </div>
            </a>
            <div style="text-align: center; margin-bottom: 15px; color: #666; font-size: 14px;">HOẶC ĐĂNG NHẬP BẰNG EMAIL</div>
            ''',
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Mật khẩu", type="password", key="login_pass")
            submit_login = st.form_submit_button("Đăng nhập")
            
            if submit_login:
                try:
                    with st.spinner("Đang đăng nhập..."):
                        user = auth.sign_in_with_email_and_password(login_email, login_password)
                        st.session_state.idToken = user['idToken']
                        st.session_state.user_email = user['email']
                    st.success("Đăng nhập thành công!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi đăng nhập: {e}")
                    
    with tab2:
        st.subheader("Đăng ký tài khoản mới")
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Mật khẩu (ít nhất 6 ký tự)", type="password", key="reg_pass")
            submit_reg = st.form_submit_button("Đăng ký")
            
            if submit_reg:
                try:
                    with st.spinner("Đang đăng ký..."):
                        user = auth.create_user_with_email_and_password(reg_email, reg_password)
                        st.session_state.idToken = user['idToken']
                        st.session_state.user_email = user['email']
                    st.success("Đăng ký thành công!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi đăng ký: {e}")

# ─── Giao diện Chính (Sau khi đăng nhập) ────────────────────────────────────
else:
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("🗺️ AI Landmark Detector")
    with col2:
        st.write(f"Xin chào, **{st.session_state.user_email}**")
        st.button("Đăng xuất", on_click=logout)
        
    st.markdown("---")
    
    # ─── Chia 2 cột: Tính năng & Lịch sử ─────────────────────────────────────
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("Nhận dạng địa điểm")
        uploaded_file = st.file_uploader("Upload ảnh địa điểm (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh đã tải lên", use_container_width=True)
            
            if st.button("🔍 Phân tích ảnh", type="primary"):
                with st.spinner("AI đang phân tích..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        headers = {"Authorization": f"Bearer {st.session_state.idToken}"}
                        
                        response = requests.post(f"{BACKEND_URL}/chat/predict", files=files, headers=headers)
                        
                        if response.status_code == 200:
                            res_data = response.json()
                            if res_data.get("success"):
                                st.success(f"Dự đoán thành công trong {res_data.get('processing_time')}s")
                                st.markdown(f"### 📍 Địa điểm: **{res_data.get('location_name')}**")
                                st.info(f"Label ID: {res_data.get('label')} | Inliers: {res_data.get('inliers')}")
                            else:
                                st.warning("Không thể nhận diện được địa điểm trong ảnh này.")
                        else:
                            st.error(f"Lỗi từ server: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Không thể kết nối đến Backend Server (localhost:8000). Vui lòng kiểm tra server.")
                    except Exception as e:
                        st.error(f"Lỗi không xác định: {e}")
                        
    with right_col:
        st.subheader("🕒 Lịch sử tra cứu")
        if st.button("Làm mới lịch sử", use_container_width=True):
            pass # Nút này tự trigger rerun component này
            
        try:
            headers = {"Authorization": f"Bearer {st.session_state.idToken}"}
            res = requests.get(f"{BACKEND_URL}/chat/history", headers=headers)
            
            if res.status_code == 200:
                history_data = res.json().get("history", [])
                if not history_data:
                    st.info("Chưa có lịch sử tra cứu nào.")
                else:
                    for idx, item in enumerate(history_data):
                        with st.expander(f"{item.get('location_name')} - {item.get('file_name')} ({item.get('timestamp')[:10]})"):
                            st.write(f"**Thời gian:** {item.get('timestamp')}")
                            st.write(f"**Inliers:** {item.get('inliers')}")
                            st.write(f"**Tốc độ xử lý:** {item.get('processing_time')}s")
            else:
                st.error("Không thể tải lịch sử từ server.")
        except requests.exceptions.ConnectionError:
            st.error("Backend offline.")
