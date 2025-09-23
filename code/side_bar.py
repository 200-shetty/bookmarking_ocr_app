import streamlit as st
from helper import calculate_cascading_assignments, cleanup_temp_files



def render_sidebar():
    with st.sidebar:
        st.markdown("### Progress")
        
        if hasattr(st.session_state, 'total_pages'):
            # Progress overview
            manual_assignments = len(st.session_state.page_assignments)
            total = st.session_state.total_pages
            
            if manual_assignments > 0:
                all_assignments = calculate_cascading_assignments(st.session_state.page_assignments, total)
                covered_pages = len(all_assignments)
                progress = covered_pages / total
                
                st.metric("Coverage", f"{covered_pages}/{total}", f"{manual_assignments} anchors")
                st.progress(progress)
            else:
                st.metric("Coverage", "0/0", "No assignments")
        
        st.divider()
        
        if st.button("🔄 Start Over", type="secondary", use_container_width=True):
            # Clean up temp files
            cleanup_temp_files()
            
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Quick batch navigation (only show if we're on the bookmarking functionality)
        if hasattr(st.session_state, 'total_pages') and st.session_state.total_pages:
            total_batches = (st.session_state.total_pages + 5) // 6
            if total_batches > 1:
                st.markdown("### Quick Navigation")
                batch_num = st.selectbox(
                    "Jump to Batch",
                    range(total_batches),
                    index=st.session_state.current_batch,
                    format_func=lambda x: f"Batch {x+1}"
                )
                if batch_num != st.session_state.current_batch:
                    st.session_state.current_batch = batch_num
                    st.rerun()