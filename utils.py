import streamlit as st
import base64

def load_css(file_name):
    """Inject custom CSS to override Streamlit defaults and apply Next.js styles."""
    # أضفنا encoding="utf-8" هنا لحل المشكلة
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def apply_global_styles():
    load_css("styles/main.css")
    # Hide Streamlit header and footer
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

def image_to_base64(img_path):
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()