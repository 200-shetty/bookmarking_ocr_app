import streamlit as st
from helper import safe_pdf_open, create_ocr_pdf




def handle_upload_and_ocr():
    """Handle PDF upload and OCR conversion"""
    st.subheader("Upload PDF")
    
    uploaded_file = st.file_uploader("Drop your PDF here", type="pdf", label_visibility="collapsed")
    
    if uploaded_file:
        try:
            pdf_bytes = uploaded_file.getvalue()
            pdf_doc, temp_path = safe_pdf_open(pdf_bytes)
            
            if pdf_doc is None:
                st.error("Failed to open PDF file")
                return
            
            total_pages = len(pdf_doc)
            
            # Store in session state
            st.session_state.original_pdf_doc = pdf_doc
            st.session_state.temp_path = temp_path
            st.session_state.total_pages = total_pages
            st.session_state.uploaded_filename = uploaded_file.name
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{uploaded_file.name}**")
                st.caption(f"{total_pages} pages • {len(pdf_bytes)/1024/1024:.1f} MB")
            
            with col2:
                if st.button("Convert to OCR", type="primary"):
                    with st.spinner("Converting to OCR..."):
                        ocr_pdf = create_ocr_pdf(st.session_state.original_pdf_doc)
                        if ocr_pdf:
                            st.session_state.ocr_pdf_doc = ocr_pdf
                            st.balloons()
                            st.success("✅ OCR conversion complete! Switch to 'Smart Bookmarking' tab to continue.")
                        else:
                            st.error("PDF conversion failed")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")