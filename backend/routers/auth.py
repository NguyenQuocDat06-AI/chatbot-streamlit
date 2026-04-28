import logging
import requests
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse
from firebase_admin import auth as firebase_admin_auth
from typing import Optional
from backend.core.config import config

logger = logging.getLogger("LandmarkAPI.Auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Dependency: Validate Firebase ID token từ request header. Trả về user_id"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
        
    token = authorization.split("Bearer ")[1]
    
    try:
        decoded_token = firebase_admin_auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    """Trả về thông tin user (test endpoint)"""
    try:
        user = firebase_admin_auth.get_user(user_id)
        return {
            "uid": user.uid,
            "email": user.email,
            "email_verified": user.email_verified
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")


# --- Google Login Oauth2 Endpoints ---
google_config = config.get("google-login", {})
GOOGLE_CLIENT_ID = google_config.get("google_client_id")
GOOGLE_CLIENT_SECRET = google_config.get("google_client_secret")
GOOGLE_REDIRECT_URI = google_config.get("google_redirect_uri")
FRONTEND_URL = google_config.get("frontend_url", "http://localhost:8501")
FIREBASE_API_KEY = google_config.get("firebase_web_api_key")

@router.get("/google/start")
def google_start():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google client id not configured")
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile"
    )
    return RedirectResponse(url=auth_url)

@router.get("/google/callback")
def google_callback(code: str):
    # 1. Exchange code for Google token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI
    }
    
    token_res = requests.post(token_url, data=data)
    token_data = token_res.json()
    
    if "id_token" not in token_data:
        logger.error(f"Google Token error: {token_data}")
        raise HTTPException(status_code=400, detail="Google authentication failed")
        
    google_id_token = token_data["id_token"]
    
    # 2. Login to Firebase using Google ID Token via Identity Toolkit REST API
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    firebase_data = {
        "postBody": f"id_token={google_id_token}&providerId=google.com",
        "requestUri": FRONTEND_URL,
        "returnIdpCredential": True,
        "returnSecureToken": True
    }
    
    firebase_res = requests.post(firebase_url, json=firebase_data)
    firebase_data_res = firebase_res.json()
    
    if "idToken" not in firebase_data_res:
        logger.error(f"Firebase Identity error: {firebase_data_res}")
        raise HTTPException(status_code=400, detail="Firebase authentication failed")
        
    firebase_id_token = firebase_data_res["idToken"]
    firebase_email = firebase_data_res.get("email", "")
    
    # Redirect back to frontend with tokens
    redirect_url = f"{FRONTEND_URL}/?idToken={firebase_id_token}&email={firebase_email}"
    return RedirectResponse(url=redirect_url)
