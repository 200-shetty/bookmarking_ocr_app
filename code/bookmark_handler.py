
import streamlit as st
from helper import get_page_image_base64, create_readable_zoom_preview, calculate_cascading_assignments

def handle_smart_bookmarking():
    """Handle smart bookmarking interface"""
    if not hasattr(st.session_state, 'ocr_pdf_doc') or st.session_state.ocr_pdf_doc is None:
        st.warning("⚠️ Please upload and convert a PDF first in the 'Upload & OCR' tab.")
        return
    
    st.subheader("Smart Bookmarking")
    
    total_pages = st.session_state.total_pages
    pages_per_batch = 6
    total_batches = (total_pages + pages_per_batch - 1) // pages_per_batch
    current_batch = st.session_state.current_batch
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Previous", disabled=(current_batch == 0)):
            st.session_state.current_batch = max(0, current_batch - 1)
            st.rerun()
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #f8fafc, #f1f5f9); border-radius: 10px;">
            <div style="font-size: 1.3rem; font-weight: bold; color: #1e293b;">Batch {current_batch + 1} of {total_batches}</div>
            <div style="color: #64748b; font-size: 0.9rem;">Pages {current_batch * pages_per_batch + 1}-{min((current_batch + 1) * pages_per_batch, total_pages)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("Next →", disabled=(current_batch >= total_batches - 1)):
            st.session_state.current_batch = min(total_batches - 1, current_batch + 1)
            st.rerun()
    
    st.divider()
    
    # Page assignment interface
    start_page = current_batch * pages_per_batch + 1
    end_page = min(start_page + pages_per_batch - 1, total_pages)
    
    for page_num in range(start_page, end_page + 1):
        # Get current assignment or inherit from previous
        if page_num not in st.session_state.page_assignments:
            default_assignment = {"type": "Index", "number": "", "custom_name": ""}
            if page_num > 1:
                # Look for previous assignment to inherit
                for prev_page in range(page_num - 1, 0, -1):
                    if prev_page in st.session_state.page_assignments:
                        default_assignment = st.session_state.page_assignments[prev_page].copy()
                        break
            current_assignment = default_assignment
        else:
            current_assignment = st.session_state.page_assignments[page_num]
        
        # Page row
        st.markdown('<div class="page-card">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([0.5, 2, 2, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem;">
                {page_num}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            category_options = ["Index", "Original Application (OA)", "Annexures", "Vakalath", "Custom"]
            try:
                current_index = category_options.index(current_assignment["type"])
            except ValueError:
                current_index = 0
            
            category = st.selectbox(
                "Category",
                category_options,
                index=current_index,
                key=f"cat_{page_num}",
                label_visibility="collapsed"
            )
        
        with col3:
            if category == "Annexures":
                annexure_number = st.text_input(
                    "A-Number",
                    value=current_assignment.get("number", ""),
                    placeholder="1, 2, 10(1), A, etc.",
                    key=f"ann_{page_num}",
                    label_visibility="collapsed"
                )
                display_text = f"Annexure A{annexure_number}" if annexure_number else "Annexures"
                custom_name = ""
            elif category == "Custom":
                custom_name = st.text_input(
                    "Custom Name",
                    value=current_assignment.get("custom_name", ""),
                    placeholder="Enter custom bookmark name",
                    key=f"custom_{page_num}",
                    label_visibility="collapsed"
                )
                display_text = custom_name if custom_name else "Custom"
                annexure_number = ""
            else:
                annexure_number = ""
                custom_name = ""
                display_text = category
            
            # Show assignment result
            is_anchor = page_num in st.session_state.page_assignments
            st.caption(f"{'📌 Anchor:' if is_anchor else '📋 Inherited:'} {display_text}")
        
        with col4:
            # Enhanced preview with working zoom  
            try:
                if hasattr(st.session_state, 'original_pdf_doc') and st.session_state.original_pdf_doc:
                    page = st.session_state.original_pdf_doc[page_num - 1]
                    img_base64 = get_page_image_base64(page, size_factor=1.5)  # Higher resolution
                    if img_base64:
                        preview_html = create_readable_zoom_preview(img_base64, page_num)
                        st.components.v1.html(preview_html, height=130)
                    else:
                        st.markdown('<div style="width: 100px; height: 120px; background: #f1f5f9; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 10px;">No preview</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown('<div style="width: 100px; height: 120px; background: #f1f5f9; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 10px;">Error</div>', unsafe_allow_html=True)
        
        # Save assignment if changed
        if (current_assignment.get("type", "") != category or 
            current_assignment.get("number", "") != annexure_number or
            current_assignment.get("custom_name", "") != custom_name):
            st.session_state.page_assignments[page_num] = {
                "type": category,
                "number": annexure_number,
                "custom_name": custom_name
            }
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Assignment Summary
    if st.session_state.page_assignments:
        all_assignments = calculate_cascading_assignments(st.session_state.page_assignments, total_pages)
        
        st.divider()
        st.subheader("Assignment Overview")
        
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
        
        # Summary as chips
        summary_html = ""
        for category, pages in assignment_summary.items():
            page_count = len(pages)
            first_page = min(pages)
            last_page = max(pages)
            range_text = f"{first_page}" if first_page == last_page else f"{first_page}-{last_page}"
            
            summary_html += f'<span class="summary-chip">{category} • {page_count}p • {range_text}</span>'
        
        st.markdown(summary_html, unsafe_allow_html=True)
        
        # Progress info
        manual_count = len(st.session_state.page_assignments)
        progress_pct = (len(all_assignments) / total_pages) * 100
        
        st.info(f"{manual_count} anchor points → {len(all_assignments)} pages covered ({progress_pct:.0f}%)")
        st.success("✅ Bookmarks ready! Switch to 'Download' tab to generate your PDF.")