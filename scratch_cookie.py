import streamlit as st
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()
st.write("Cookies:", cookie_manager.get_all())
