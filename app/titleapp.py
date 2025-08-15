import streamlit as st
import requests

# FastAPI endpoints
SIGNON_URL = "http://127.0.0.1:8001/user-signon"
LOGIN_URL = "http://127.0.0.1:8001/user-login"

st.set_page_config(page_title="User Authentication", page_icon="🔐")

st.title("🔐 User Authentication Portal")

tab1, tab2 = st.tabs(["🆕 Sign On", "🔓 Login"])

# ----------- SIGN ON TAB -----------
with tab1:
    st.subheader("Create a New Account")
    username = st.text_input("User Name", placeholder="Enter your username", key="signon_username")
    email = st.text_input("Email", placeholder="Enter your email address", key="signon_email")
    password = st.text_input("Password", placeholder="Enter a password", type="password", key="signon_password")
    
    if st.button("Sign On", key="signon_button"):
        if username and email and password:
            payload = {
                "username": username,
                "email": email,
                "password": password
            }
            try:
                response = requests.post(SIGNON_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"✅ {response.json().get('result', [['Success']])[0][0]}")
                else:
                    st.error(f"❌ Failed: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"⚠️ API connection error: {e}")
        else:
            st.warning("⚠️ Please fill in all fields.")

# ----------- LOGIN TAB -----------
with tab2:
    st.subheader("Login to Your Account")
    login_username = st.text_input("User Name", placeholder="Enter your username", key="login_username")
    login_password = st.text_input("Password", placeholder="Enter your password", type="password", key="login_password")
    
    if st.button("Login", key="login_button"):
        if login_username and login_password:
            payload = {
                "username": login_username,
                "password": login_password
            }
            try:
                response = requests.post(LOGIN_URL, json=payload)
                if response.status_code == 200:
                    st.success(f"✅ {response.json().get('result', [['Login Success']])[0][0]}")
                else:
                    st.error(f"❌ Failed: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"⚠️ API connection error: {e}")
        else:
            st.warning("⚠️ Please fill in all fields.")
