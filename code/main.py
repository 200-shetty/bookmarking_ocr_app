import streamlit as st
import pytesseract
import sys


from upload_handler import handle_upload_and_ocr
from bookmark_handler import handle_smart_bookmarking
from extraction_handler import handle_download
from side_bar import render_sidebar
from helper import initialize_session_state

from helper import initialize_session_state


try:
    if sys.platform.startswith('linux'):
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    elif sys.platform.startswith('darwin'):
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    else:
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except:
    pass

st.set_page_config(
    page_title="OCR & Bookmarking Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main { padding-top: 1rem; }
    
    .step-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .page-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        transition: all 0.2s ease;
    }
    
    .page-card:hover {
        transform: translateX(3px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    
    .nav-button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    
    .summary-chip {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.85rem;
        font-weight: 500;
        color: #334155;
        border: 1px solid #e2e8f0;
    }
    
    .custom-bookmark-input {
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)




def main():
    initialize_session_state()
    st.title("⚡ OCR & Bookmarking Studio")
    tab1, tab2, tab3 = st.tabs(["📤 Upload & OCR", "🔖 Smart Bookmarking", "📥 Download"])
    with tab1:
        handle_upload_and_ocr()
    with tab2:
        handle_smart_bookmarking()
    with tab3:
        handle_download()


if __name__ == "__main__":
    render_sidebar()
    main()

