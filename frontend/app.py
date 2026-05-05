import streamlit as st
import os
import requests
import time

# ─── Cấu hình chung ────────────────────────────────────────────────────────
st.set_page_config(page_title="Landmark Detector", page_icon="🗺️", layout="wide")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

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
    if "messages" in st.session_state:
        del st.session_state.messages
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
                        res = requests.post(
                            f"{BACKEND_URL}/auth/login",
                            json={"email": login_email, "password": login_password}
                        )
                        
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.idToken = data["idToken"]
                            st.session_state.user_email = data["email"]
                            st.success("Đăng nhập thành công!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            error_detail = res.json().get("detail", "Đăng nhập thất bại")
                            st.error(f"Lỗi đăng nhập: {error_detail}")
                except requests.exceptions.ConnectionError:
                    st.error("Không thể kết nối đến Backend Server.")
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
                        # Gọi backend API thay vì gọi Firebase trực tiếp
                        res = requests.post(
                            f"{BACKEND_URL}/auth/register",
                            json={"email": reg_email, "password": reg_password}
                        )
                        
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.idToken = data["idToken"]
                            st.session_state.user_email = data["email"]
                            st.success("Đăng ký thành công!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            error_detail = res.json().get("detail", "Đăng ký thất bại")
                            st.error(f"Lỗi đăng ký: {error_detail}")
                except requests.exceptions.ConnectionError:
                    st.error("Không thể kết nối đến Backend Server.")
                except Exception as e:
                    st.error(f"Lỗi đăng ký: {e}")

# ─── Giao diện Chính (Sau khi đăng nhập) ────────────────────────────────────
else:
    # ─── Sidebar: Lịch sử & Đăng xuất ────────────────────────────────────────
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_email}**")
        st.button("🚪 Đăng xuất", on_click=logout, use_container_width=True)
        st.markdown("---")
        
        st.subheader("🕒 Lịch sử tra cứu")
        if st.button("🔄 Làm mới", use_container_width=True):
            pass
            
        try:
            headers = {"Authorization": f"Bearer {st.session_state.idToken}"}
            res = requests.get(f"{BACKEND_URL}/chat/history", headers=headers)
            
            if res.status_code == 200:
                history_data = res.json().get("history", [])
                if not history_data:
                    st.info("Chưa có lịch sử.")
                else:
                    for idx, item in enumerate(history_data):
                        with st.expander(f"📍 {item.get('location_name')} ({item.get('timestamp')[:10]})"):
                            st.write(f"**File:** {item.get('file_name')}")
                            st.write(f"**Inliers:** {item.get('inliers')}")
                            st.write(f"**Tốc độ:** {item.get('processing_time')}s")
            else:
                st.error("Không thể tải lịch sử.")
        except requests.exceptions.ConnectionError:
            st.error("Backend offline.")

    # ─── Main Area: Chat Interface ───────────────────────────────────────────
    st.title("🗺️ AI Landmark Detector")
    
    # Khởi tạo tin nhắn chào mừng nếu chưa có
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "type": "text", "content": "Xin chào! Hãy tải lên một bức ảnh địa danh tại Việt Nam, tôi sẽ giúp bạn nhận diện nó."}]
        
    # Cấu hình key cho uploader để reset sau khi upload
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = str(time.time())

    # Hiển thị lịch sử chat trong phiên hiện tại
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("type") == "image":
                st.image(msg["content"], width=300)
            else:
                st.markdown(msg["content"])
                
    # Vùng Upload ảnh ở cuối đoạn chat
    st.markdown("---")
    uploaded_file = st.file_uploader("📎 Tải lên ảnh địa điểm (JPG, PNG)", type=['jpg', 'jpeg', 'png'], key=st.session_state.uploader_key)
    
    if uploaded_file is not None:
        image_bytes = uploaded_file.getvalue()
        
        # 1. Hiển thị ảnh của người dùng trong chat
        st.session_state.messages.append({"role": "user", "type": "image", "content": image_bytes})
        
        with st.chat_message("user"):
            st.image(image_bytes, width=300)
            
        # 2. AI xử lý và trả lời — gọi backend API
        with st.chat_message("assistant"):
            with st.spinner("AI đang phân tích ảnh..."):
                try:
                    files = {"file": (uploaded_file.name, image_bytes, uploaded_file.type)}
                    headers = {"Authorization": f"Bearer {st.session_state.idToken}"}
                    
                    response = requests.post(f"{BACKEND_URL}/chat/predict", files=files, headers=headers)
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get("success"):
                            reply_text = f"📍 Đây có vẻ là **{res_data.get('location_name')}**.\n\n*(Độ tin cậy/Inliers: {res_data.get('inliers')} | Thời gian: {res_data.get('processing_time')}s)*"
                        else:
                            reply_text = "⚠️ Xin lỗi, tôi không thể nhận diện được địa điểm trong ảnh này."
                    else:
                        reply_text = f"❌ Lỗi từ server: {response.text}"
                except requests.exceptions.ConnectionError:
                    reply_text = "❌ Không thể kết nối đến Backend Server (localhost:8000)."
                except Exception as e:
                    reply_text = f"❌ Lỗi không xác định: {e}"
                
                st.markdown(reply_text)
                
                # Lưu câu trả lời của AI vào session
                st.session_state.messages.append({"role": "assistant", "type": "text", "content": reply_text})
                
        # 3. Thay đổi key để reset vùng upload và rerun để vẽ lại UI
        st.session_state.uploader_key = str(time.time())
        st.rerun()
