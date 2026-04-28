import requests
import json

class FirebaseAuth:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def sign_in_with_email_and_password(self, email: str, password: str):
        request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        
        response = requests.post(request_url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json().get('error', {}).get('message', 'Login failed'))
            
    def create_user_with_email_and_password(self, email: str, password: str):
        request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
        
        response = requests.post(request_url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json().get('error', {}).get('message', 'Registration failed'))
