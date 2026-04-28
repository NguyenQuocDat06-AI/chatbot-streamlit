import os
import toml
import firebase_admin
from firebase_admin import credentials, firestore
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger("LandmarkAPI.Config")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
secrets_path = os.path.join(project_dir, 'secrets.toml')

config = {}
if os.path.exists(secrets_path):
    config = toml.load(secrets_path)
else:
    logger.warning(f"Không tìm thấy file {secrets_path}")

def init_firebase():
    """Khởi tạo Firebase Admin SDK"""
    if not firebase_admin._apps:
        try:
            admin_config = config.get("firebase_admin", {}).copy()
            if admin_config:
                # Xử lý newline trong private_key
                if 'private_key' in admin_config and '\\n' in admin_config['private_key']:
                    admin_config['private_key'] = admin_config['private_key'].replace('\\n', '\n')
                
                cred = credentials.Certificate(admin_config)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized successfully.")
            else:
                logger.error("Missing [firebase_admin] section in secrets.toml")
        except Exception as e:
            logger.error(f"Error initializing Firebase Admin: {e}")

# Khởi tạo db instance
db = None
try:
    init_firebase()
    if firebase_admin._apps:
        db = firestore.client()
except Exception as e:
    logger.error(f"Error initializing Firestore: {e}")

# Các biến config khác
FIREBASE_WEB_API_KEY = config.get("firebase_client", {}).get("apiKey", "")
