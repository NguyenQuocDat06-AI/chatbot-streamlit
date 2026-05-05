import streamlit as st
import streamlit.components.v1 as components
import os
import requests
import time
import base64
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Landmark Detector", page_icon="🗺️", layout="wide", initial_sidebar_state="expanded")

# ─── CSS: ChatGPT-like Theme ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    /* Base Typography & Hidden Streamlit Elements */
    div[class*="st-"], h1, h2, h3, h4, p, span, label, input, button {
        font-family: 'Outfit', sans-serif !important;
    }
    .material-symbols-rounded, [data-testid="stIconMaterial"], .stIcon, i, span[class*="material"] {
        font-family: 'Material Symbols Rounded' !important;
    }
    /* Footer */
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Main Background - Modern Dark with subtle gradient */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e2e8f0;
    }
    .main .block-container { max-width: 900px; padding-top: 1rem; padding-bottom: 3rem; }

    /* Sidebar - Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #cbd5e1 !important; }

    /* Chat Messages (Glass Cards) */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
    }
    [data-testid="stChatMessage"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
        background: rgba(255, 255, 255, 0.05);
    }

    /* Primary Button (New Chat) */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        border: none;
        border-radius: 12px;
        color: white !important;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 0.6rem 1rem;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.39);
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        filter: brightness(1.1);
    }

    /* Normal Buttons (History, Delete, Logout) */
    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background: rgba(255, 255, 255, 0.02) !important;
        transition: all 0.2s ease !important;
        color: #e2e8f0 !important;
    }
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-1px);
    }

    /* Form Inputs */
    .stTextInput input {
        background: rgba(0, 0, 0, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: white !important;
        transition: all 0.3s ease;
    }
    .stTextInput input:focus {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.25) !important;
    }

    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: rgba(0, 0, 0, 0.15);
        border: 1px dashed rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #a855f7;
        background: rgba(168, 85, 247, 0.05);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 500; }
    .stTabs [aria-selected="true"] { color: #a855f7 !important; border-bottom-color: #a855f7 !important; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }

    /* Text Colors overrides */
    h1, h2, h3, h4, label, .stMarkdown, .stAlert p { color: #f8fafc !important; }
    
    /* Divider */
    hr { border-color: rgba(255,255,255,0.08) !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


# ─── Helper: localStorage ───────────────────────────────────────────────────
def save_to_local_storage(token: str, email: str):
    components.html(
        f"<script>localStorage.setItem('idToken',`{token}`);localStorage.setItem('user_email',`{email}`);</script>",
        height=0
    )

def clear_local_storage():
    components.html(
        "<script>localStorage.removeItem('idToken');localStorage.removeItem('user_email');</script>",
        height=0
    )


# ─── Auth: Query Params (Google Login) ───────────────────────────────────────
if "idToken" in st.query_params:
    st.session_state.idToken = st.query_params["idToken"]
    st.session_state.user_email = st.query_params.get("email", "Google User")
    st.session_state._pending_save = True
    st.query_params.clear()
    st.rerun()

if "idToken" not in st.session_state:
    st.session_state.idToken = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if st.session_state.get("_pending_save") and st.session_state.idToken:
    save_to_local_storage(st.session_state.idToken, st.session_state.user_email)
    st.session_state._pending_save = False

# ─── Auth: Restore from localStorage ────────────────────────────────────────
if st.session_state.idToken is None:
    restored = streamlit_js_eval(
        js_expressions="({t: localStorage.getItem('idToken'), e: localStorage.getItem('user_email')})",
        key="restore_session"
    )
    if restored and restored != 0 and isinstance(restored, dict) and restored.get("t"):
        st.session_state.idToken = restored["t"]
        st.session_state.user_email = restored.get("e", "")
        st.rerun()


def logout():
    st.session_state.idToken = None
    st.session_state.user_email = None
    for key in ["messages", "current_conv_id", "uploader_key"]:
        st.session_state.pop(key, None)
    clear_local_storage()
    time.sleep(0.5)
    st.rerun()


# ─── Giao diện Đăng nhập ─────────────────────────────────────────────────────
if not st.session_state.idToken:
    st.markdown("<h1 style='text-align:center;background:-webkit-linear-gradient(135deg,#a855f7 0%,#6366f1 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:3rem;margin-bottom:0;'>🗺️ Landmark Detector</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#94a3b8;'>Đăng nhập để sử dụng hệ thống nhận dạng địa điểm AI</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])

        with tab1:
            st.markdown(
                f'''<a href="{BACKEND_URL}/auth/google/start" target="_self">
                <div style="background:rgba(255,255,255,0.05);color:#f8fafc;border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:12px;text-align:center;font-weight:500;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:10px;margin-bottom:15px;transition:all 0.2s ease;">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="20"/>
                Đăng nhập bằng Google</div></a>
                <div style="text-align:center;margin-bottom:15px;color:#64748b;font-size:13px;font-weight:600;letter-spacing:1px;">HOẶC</div>''',
                unsafe_allow_html=True
            )
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Mật khẩu", type="password", key="login_pass")
                if st.form_submit_button("Đăng nhập", use_container_width=True):
                    try:
                        res = requests.post(f"{BACKEND_URL}/auth/login", json={"email": email, "password": password})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.idToken = data["idToken"]
                            st.session_state.user_email = data["email"]
                            save_to_local_storage(data["idToken"], data["email"])
                            st.success("Đăng nhập thành công!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Đăng nhập thất bại"))
                    except requests.exceptions.ConnectionError:
                        st.error("Không thể kết nối đến Backend.")

        with tab2:
            with st.form("register_form"):
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Mật khẩu (≥6 ký tự)", type="password", key="reg_pass")
                if st.form_submit_button("Đăng ký", use_container_width=True):
                    try:
                        res = requests.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.idToken = data["idToken"]
                            st.session_state.user_email = data["email"]
                            save_to_local_storage(data["idToken"], data["email"])
                            st.success("Đăng ký thành công!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Đăng ký thất bại"))
                    except requests.exceptions.ConnectionError:
                        st.error("Không thể kết nối đến Backend.")


# ─── Giao diện chính (sau đăng nhập) ─────────────────────────────────────────
else:
    headers = {"Authorization": f"Bearer {st.session_state.idToken}"}

    # Init session keys
    if "current_conv_id" not in st.session_state:
        st.session_state.current_conv_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = str(time.time())

    # ─── Sidebar ─────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"<p style='font-size:13px;color:#8E8EA0!important;margin-bottom:4px;'>👤 {st.session_state.user_email}</p>", unsafe_allow_html=True)

        # New chat button
        if st.button("➕  Trò chuyện mới", use_container_width=True, type="primary"):
            try:
                res = requests.post(f"{BACKEND_URL}/chat/conversations", headers=headers)
                if res.status_code == 200:
                    st.session_state.current_conv_id = res.json()["id"]
                    st.session_state.messages = []
                    st.rerun()
            except Exception:
                st.error("Lỗi tạo cuộc trò chuyện.")

        st.markdown("---")

        # Load conversation list
        try:
            res = requests.get(f"{BACKEND_URL}/chat/conversations", headers=headers)
            if res.status_code == 200:
                convs = res.json().get("conversations", [])
                if not convs:
                    st.markdown("<p style='color:#8E8EA0!important;font-size:13px;'>Chưa có cuộc trò chuyện nào.</p>", unsafe_allow_html=True)
                for conv in convs:
                    is_active = conv["id"] == st.session_state.current_conv_id
                    col_name, col_del = st.columns([5, 1])
                    with col_name:
                        label = f"{'🟢' if is_active else '💬'}  {conv['title']}"
                        if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                            st.session_state.current_conv_id = conv["id"]
                            try:
                                msg_res = requests.get(f"{BACKEND_URL}/chat/conversations/{conv['id']}", headers=headers)
                                if msg_res.status_code == 200:
                                    st.session_state.messages = msg_res.json().get("messages", [])
                                else:
                                    st.session_state.messages = []
                            except Exception:
                                st.session_state.messages = []
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_{conv['id']}"):
                            try:
                                requests.delete(f"{BACKEND_URL}/chat/conversations/{conv['id']}", headers=headers)
                                if st.session_state.current_conv_id == conv["id"]:
                                    st.session_state.current_conv_id = None
                                    st.session_state.messages = []
                            except Exception:
                                pass
                            st.rerun()
        except requests.exceptions.ConnectionError:
            st.error("Backend offline.")

        st.markdown("---")
        st.button("🚪  Đăng xuất", on_click=logout, use_container_width=True)

    # ─── Main Chat Area ──────────────────────────────────────────────────
    if not st.session_state.current_conv_id:
        # Welcome screen
        st.markdown("""
        <div style="text-align:center;padding-top:100px;">
            <h1 style="background:-webkit-linear-gradient(135deg,#a855f7 0%,#6366f1 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:3.5rem;margin-bottom:0.5rem;">🗺️ Landmark Detector</h1>
            <p style="color:#cbd5e1!important;font-size:1.2rem;margin-top:8px;">
                Tải lên một bức ảnh địa danh Việt Nam,<br/>AI sẽ giúp bạn nhận diện nó.
            </p>
            <p style="color:#64748b!important;font-size:0.95rem;margin-top:24px;font-weight:500;">
                Bấm <b style="color:#a855f7;">➕ Trò chuyện mới</b> ở sidebar để bắt đầu.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display messages
        for msg in st.session_state.messages:
            role = msg.get("role", "user") if isinstance(msg, dict) else "user"
            content_type = msg.get("content_type", "text") if isinstance(msg, dict) else "text"
            content = msg.get("content", "") if isinstance(msg, dict) else str(msg)

            with st.chat_message(role):
                if content_type == "image":
                    try:
                        img_bytes = base64.b64decode(content)
                        st.image(img_bytes, width=350)
                    except Exception:
                        st.write("(Không thể hiển thị ảnh)")
                else:
                    st.markdown(content)

        # File uploader
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "📎 Tải lên ảnh địa điểm (JPG, PNG)",
            type=['jpg', 'jpeg', 'png'],
            key=st.session_state.uploader_key
        )

        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()

            # Show user image immediately
            with st.chat_message("user"):
                st.image(image_bytes, width=350)

            # AI prediction
            with st.chat_message("assistant"):
                with st.spinner("AI đang phân tích ảnh..."):
                    try:
                        files = {"file": (uploaded_file.name, image_bytes, uploaded_file.type)}
                        response = requests.post(
                            f"{BACKEND_URL}/chat/conversations/{st.session_state.current_conv_id}/predict",
                            files=files, headers=headers
                        )

                        if response.status_code == 200:
                            res_data = response.json()
                            if res_data.get("success"):
                                reply = (
                                    f"📍 Đây có vẻ là **{res_data.get('location_name')}**.\n\n"
                                    f"*(Inliers: {res_data.get('inliers')} | "
                                    f"Thời gian: {res_data.get('processing_time')}s)*"
                                )
                            else:
                                reply = "⚠️ Xin lỗi, tôi không thể nhận diện được địa điểm trong ảnh này."
                        else:
                            reply = f"❌ Lỗi từ server: {response.text}"
                    except requests.exceptions.ConnectionError:
                        reply = "❌ Không thể kết nối đến Backend."
                    except Exception as e:
                        reply = f"❌ Lỗi: {e}"

                    st.markdown(reply)

            # Reload messages from backend to stay in sync
            try:
                msg_res = requests.get(
                    f"{BACKEND_URL}/chat/conversations/{st.session_state.current_conv_id}",
                    headers=headers
                )
                if msg_res.status_code == 200:
                    st.session_state.messages = msg_res.json().get("messages", [])
            except Exception:
                pass

            st.session_state.uploader_key = str(time.time())
            st.rerun()
