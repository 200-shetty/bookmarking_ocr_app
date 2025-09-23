import streamlit as st
import io
from helper import calculate_cascading_assignments, create_bookmarks_from_assignments

def handle_download():
    """Handle PDF download functionality"""
    if not hasattr(st.session_state, 'ocr_pdf_doc') or st.session_state.ocr_pdf_doc is None:
        st.warning("⚠️ Please upload and convert a PDF first in the 'Upload & OCR' tab.")
        return
    
    if not st.session_state.page_assignments:
        st.warning("⚠️ Please assign bookmarks in the 'Smart Bookmarking' tab first.")
        return
    
    st.subheader("Download")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Generate Final PDF**")
        
        # Show bookmark preview
        if st.session_state.page_assignments:
            all_assignments = calculate_cascading_assignments(
                st.session_state.page_assignments, 
                st.session_state.total_pages
            )
            assignment_summary = {}
            for page_num, assignment in all_assignments.items():
                # Use custom name if provided, otherwise generate from type and number
                if assignment.get("custom_name"):
                    category = assignment["custom_name"]
                elif assignment["type"] == "Annexures" and assignment["number"]:
                    category = f"Annexure A{assignment['number']}"
                else:
                    category = assignment["type"]
                
                if category not in assignment_summary:
                    assignment_summary[category] = []
                assignment_summary[category].append(page_num)
            
            st.info(f"Creating {len(assignment_summary)} bookmarks for {len(all_assignments)} pages")
        
        if st.button("Generate Bookmarked PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Creating bookmarks..."):
                    # Create copy for bookmarking
                    bookmarked_pdf = create_bookmarks_from_assignments(
                        st.session_state.ocr_pdf_doc, 
                        st.session_state.page_assignments, 
                        st.session_state.total_pages
                    )
                    
                    # Save to bytes
                    pdf_output = io.BytesIO()
                    bookmarked_pdf.save(pdf_output)
                    pdf_bytes = pdf_output.getvalue()
                    pdf_output.close()
                    
                    st.session_state.final_pdf_bytes = pdf_bytes
                    st.success("PDF ready for download!")
            
            except Exception as e:
                st.error(f"Error creating final PDF: {str(e)}")
    
    with col2:
        st.markdown("**Download Options**")
        
        # OCR-only download
        if st.button("Download OCR PDF Only", use_container_width=True):
            try:
                pdf_output = io.BytesIO()
                st.session_state.ocr_pdf_doc.save(pdf_output)
                pdf_bytes = pdf_output.getvalue()
                pdf_output.close()
                
                st.download_button(
                    "📄 Download OCR PDF",
                    data=pdf_bytes,
                    file_name=f"ocr_{st.session_state.uploaded_filename}",
                    mime="application/pdf",
                    key="dl_ocr",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error preparing OCR PDF: {str(e)}")
        
        # Final PDF download
        if hasattr(st.session_state, 'final_pdf_bytes'):
            st.download_button(
                "📑 Download Complete PDF",
                data=st.session_state.final_pdf_bytes,
                file_name=f"complete_{st.session_state.uploaded_filename}",
                mime="application/pdf",
                key="dl_final",
                type="primary",
                use_container_width=True
            )