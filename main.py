import streamlit as st
import fitz 
import pytesseract
from PIL import Image
import io
import tempfile
import os
import base64



# Configure page
st.set_page_config(
    page_title="OCR & Bookmarking Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Minimal, effective CSS
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
</style>
""", unsafe_allow_html=True)

def safe_pdf_open(pdf_bytes):
    """Safely open PDF with fallback to temporary file"""
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        return pdf_doc, None
    except Exception as e:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                tmp_file.flush()
                pdf_doc = fitz.open(tmp_file.name)
                return pdf_doc, tmp_file.name
        except Exception as e2:
            st.error(f"Failed to open PDF: {str(e2)}")
            return None, None

def convert_page_to_ocr(page):
    """Convert a PDF page to OCR text"""
    try:
        # Create pixmap with higher resolution for better OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # OCR with specific configuration
        ocr_text = pytesseract.image_to_string(
            image, 
            lang='eng',
            config='--psm 1 --oem 3'
        )
        
        rect = page.rect
        
        # Clean up resources
        image.close()
        pix = None
        
        return ocr_text.strip(), rect
        
    except Exception as e:
        st.warning(f"OCR failed for page: {str(e)}")
        return "", getattr(page, 'rect', fitz.Rect(0, 0, 595, 842))

def get_page_image_base64(page, size_factor=1.5):
    """Convert page to base64 image with higher resolution for better readability"""
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(size_factor, size_factor))
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode()
        pix = None
        return img_base64
    except Exception as e:
        st.warning(f"Failed to create page image: {str(e)}")
        return None

def create_readable_zoom_preview(img_base64, page_num):
    """Create a simplified zoomable preview without extra buttons"""
    if not img_base64:
        return f'<div style="width: 100px; height: 120px; background: #f1f5f9; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 10px;">No preview</div>'
    
    unique_id = f"zoom_{page_num}_{abs(hash(img_base64[:100])) % 10000}"
    
    return f"""
    <div style="position: relative; display: inline-block;">
        <!-- Thumbnail -->
        <img src="data:image/png;base64,{img_base64}" 
             style="width: 100px; height: 120px; object-fit: cover; border-radius: 8px; box-shadow: 0 3px 12px rgba(0,0,0,0.15); cursor: pointer; border: 2px solid #e2e8f0; transition: all 0.3s ease;"
             onmouseover="this.style.transform='scale(1.05)'; this.style.borderColor='#667eea'"
             onmouseout="this.style.transform='scale(1)'; this.style.borderColor='#e2e8f0'"
             onclick="openReader_{unique_id}()"
        />
        <div style="position: absolute; bottom: 4px; right: 6px; background: rgba(0,0,0,0.8); color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 600;">{page_num}</div>
        <div style="position: absolute; top: 4px; right: 4px; background: #667eea; color: white; padding: 2px 4px; border-radius: 3px; font-size: 8px; font-weight: 500;">🔍</div>
    </div>
    
    <!-- Full-Screen Reader -->
    <div id="reader_{unique_id}" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.95); z-index: 99999; overflow: hidden;">
        
        <!-- Simple Close Button -->
        <div style="position: absolute; top: 20px; right: 20px; z-index: 100001;">
            <button onclick="closeReader_{unique_id}()" style="background: #ef4444; border: none; color: white; border-radius: 8px; padding: 8px 15px; cursor: pointer; font-size: 12px; font-weight: bold;">Close</button>
        </div>
        
        <!-- Image Container -->
        <div id="imageContainer_{unique_id}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; overflow: hidden; cursor: grab;">
            <img id="zoomImg_{unique_id}" 
                 src="data:image/png;base64,{img_base64}" 
                 style="transition: transform 0.2s ease-out; user-select: none;"
                 draggable="false"
            />
        </div>
    </div>
    
    <script>
    (function() {{
        let scale_{unique_id} = 0.2; // Start at 20% zoom
        let panX_{unique_id} = 0;
        let panY_{unique_id} = 0;
        let isDragging_{unique_id} = false;
        let lastMouseX_{unique_id} = 0;
        let lastMouseY_{unique_id} = 0;
        
        const img_{unique_id} = document.getElementById('zoomImg_{unique_id}');
        const container_{unique_id} = document.getElementById('imageContainer_{unique_id}');
        
        function updateDisplay_{unique_id}() {{
            if (img_{unique_id}) {{
                img_{unique_id}.style.transform = `translate(${{panX_{unique_id}}}px, ${{panY_{unique_id}}}px) scale(${{scale_{unique_id}}})`;
            }}
            if (container_{unique_id}) {{
                container_{unique_id}.style.cursor = isDragging_{unique_id} ? 'grabbing' : (scale_{unique_id} > 0.2 ? 'grab' : 'default');
            }}
        }}
        
        function openReader_{unique_id}() {{
            const reader = document.getElementById('reader_{unique_id}');
            reader.style.display = 'block';
            document.body.style.overflow = 'hidden';
            
            // Initialize with 20% zoom
            setTimeout(() => {{
                scale_{unique_id} = 0.2;
                
                // Center the image
                panX_{unique_id} = 0;
                panY_{unique_id} = 0;
                
                updateDisplay_{unique_id}();
            }}, 100);
        }}
        
        function closeReader_{unique_id}() {{
            document.getElementById('reader_{unique_id}').style.display = 'none';
            document.body.style.overflow = 'auto';
            // Reset zoom and pan
            scale_{unique_id} = 0.2;
            panX_{unique_id} = 0;
            panY_{unique_id} = 0;
        }}
        
        // Mouse controls
        if (container_{unique_id}) {{
            container_{unique_id}.addEventListener('mousedown', function(e) {{
                // Always allow dragging regardless of zoom level
                isDragging_{unique_id} = true;
                lastMouseX_{unique_id} = e.clientX;
                lastMouseY_{unique_id} = e.clientY;
                container_{unique_id}.style.cursor = 'grabbing';
                e.preventDefault();
            }});
            
            container_{unique_id}.addEventListener('mousemove', function(e) {{
                if (isDragging_{unique_id}) {{
                    const deltaX = e.clientX - lastMouseX_{unique_id};
                    const deltaY = e.clientY - lastMouseY_{unique_id};
                    
                    panX_{unique_id} += deltaX;
                    panY_{unique_id} += deltaY;
                    
                    lastMouseX_{unique_id} = e.clientX;
                    lastMouseY_{unique_id} = e.clientY;
                    
                    updateDisplay_{unique_id}();
                    e.preventDefault();
                }}
            }});
            
            container_{unique_id}.addEventListener('mouseup', function() {{
                isDragging_{unique_id} = false;
                container_{unique_id}.style.cursor = scale_{unique_id} > 0.2 ? 'grab' : 'default';
            }});
            
            container_{unique_id}.addEventListener('mouseleave', function() {{
                isDragging_{unique_id} = false;
                container_{unique_id}.style.cursor = scale_{unique_id} > 0.2 ? 'grab' : 'default';
            }});
            
            // Mouse wheel zoom
            container_{unique_id}.addEventListener('wheel', function(e) {{
                e.preventDefault();
                
                const zoomFactor = e.deltaY > 0 ? 0.85 : 1.18;
                const oldScale = scale_{unique_id};
                scale_{unique_id} = Math.max(0.2, Math.min(10, scale_{unique_id} * zoomFactor));
                
                // Zoom towards mouse position
                const rect = container_{unique_id}.getBoundingClientRect();
                const mouseX = e.clientX - rect.left - rect.width / 2;
                const mouseY = e.clientY - rect.top - rect.height / 2;
                
                const scaleDiff = scale_{unique_id} / oldScale;
                panX_{unique_id} = mouseX - (mouseX - panX_{unique_id}) * scaleDiff;
                panY_{unique_id} = mouseY - (mouseY - panY_{unique_id}) * scaleDiff;
                
                updateDisplay_{unique_id}();
            }}, {{ passive: false }});
        }}
        
        // Keyboard shortcuts
        function handleKeyDown_{unique_id}(e) {{
            const reader = document.getElementById('reader_{unique_id}');
            if (reader && reader.style.display === 'block') {{
                if (e.key === 'Escape') {{
                    closeReader_{unique_id}();
                }}
            }}
        }}
        
        document.addEventListener('keydown', handleKeyDown_{unique_id});
        
        // Close on background click
        const reader_{unique_id} = document.getElementById('reader_{unique_id}');
        if (reader_{unique_id}) {{
            reader_{unique_id}.addEventListener('click', function(e) {{
                if (e.target === this) {{
                    closeReader_{unique_id}();
                }}
            }});
        }}
        
        // Make functions globally available
        window.openReader_{unique_id} = openReader_{unique_id};
        window.closeReader_{unique_id} = closeReader_{unique_id};
    }})();
    </script>
    """

def create_ocr_pdf(original_pdf):
    """Create OCR version of PDF"""
   try:
        if not original_pdf or original_pdf.is_closed:
            raise Exception("Invalid PDF document")
        
        new_doc = fitz.open()
        total_pages = len(original_pdf)
        
        if total_pages == 0:
            raise Exception("PDF has no pages")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for page_num in range(total_pages):
            status_text.text(f"Converting page {page_num + 1} of {total_pages}...")
            progress_bar.progress((page_num + 1) / total_pages)
            
            try:
                original_page = original_pdf[page_num]
                new_page = new_doc.new_page(
                    width=original_page.rect.width, 
                    height=original_page.rect.height
                )
                
                # Insert original page as image
                pix = original_page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                new_page.insert_image(new_page.rect, stream=img_data)
                
                # Perform OCR and add invisible text layer
                image = Image.open(io.BytesIO(img_data))
                ocr_text = pytesseract.image_to_string(
                    image, 
                    lang='eng',
                    config='--psm 1 --oem 3'
                )
                
                # Add invisible OCR text layer
                if ocr_text.strip():
                    new_page.insert_text(
                        (10, 30),
                        ocr_text,
                        fontsize=1,
                        color=(1, 1, 1)  # White text (invisible)
                    )
                
                # Clean up resources
                image.close()
                pix = None
                
            except Exception as e:
                st.warning(f"Failed to process page {page_num + 1}: {str(e)}")
                # Create blank page as fallback
                new_doc.new_page()
                continue
        
        # Clean up UI elements
        status_text.empty()
        progress_bar.empty()
        return new_doc
       
        new_doc = fitz.open()
        new_doc.insert_pdf(original_pdf)
        return new_doc
        
    except Exception as e:
        st.error(f"OCR conversion error: {str(e)}")
        return None

def calculate_cascading_assignments(page_assignments, total_pages):
    """Calculate page assignments with cascading logic"""
    cascaded_assignments = {}
    
    if not page_assignments:
        return {}
    
    # Sort assignment points by page number
    assignment_points = sorted(page_assignments.items())
    
    # Add default starting point if first assignment isn't page 1
    if assignment_points[0][0] > 1:
        assignment_points.insert(0, (1, {"type": "Index", "number": ""}))
    
    # Apply cascading logic
    for i, (page_num, assignment) in enumerate(assignment_points):
        # Determine end page for this assignment
        end_page = assignment_points[i + 1][0] - 1 if i < len(assignment_points) - 1 else total_pages
        
        # Apply assignment to all pages in range
        for page in range(page_num, end_page + 1):
            cascaded_assignments[page] = assignment.copy()
    
    return cascaded_assignments

def create_bookmarks_from_assignments(pdf_doc, page_assignments, total_pages):
    """Create PDF bookmarks from page assignments"""
    try:
        all_assignments = calculate_cascading_assignments(page_assignments, total_pages)
        
        if not all_assignments:
            return pdf_doc
        
        # Group pages by category
        categories = {}
        for page_num, assignment in all_assignments.items():
            category = assignment["type"]
            if assignment["type"] == "Annexures" and assignment["number"]:
                category = f"Annexure A{assignment['number']}"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(page_num)
        
        # Create table of contents
        toc = []
        
        # Define category order
        category_order = ["Index", "Original Application (OA)"]
        
        # Sort annexure categories
        annexure_categories = [cat for cat in categories.keys() if cat.startswith("Annexure A")]
        annexure_categories.sort(key=lambda x: (
            0, int(x.replace("Annexure A", ""))
        ) if x.replace("Annexure A", "").isdigit() else (1, x))
        category_order.extend(annexure_categories)
        
        # Add any remaining categories
        for cat in categories.keys():
            if cat not in category_order:
                category_order.append(cat)
        
        # Create bookmarks
        for category in category_order:
            if category in categories:
                pages = sorted(categories[category])
                if pages:
                    # Add bookmark pointing to first page of this category
                    toc.append([1, category, pages[0]])
        
        # Set table of contents
        if toc:
            pdf_doc.set_toc(toc)
        
        return pdf_doc
        
    except Exception as e:
        st.error(f"Error creating bookmarks: {str(e)}")
        return pdf_doc

def get_current_step():
    """Determine current step based on session state"""
    if hasattr(st.session_state, 'ocr_pdf_doc') and st.session_state.ocr_pdf_doc is not None:
        if hasattr(st.session_state, 'ready_for_download') and st.session_state.ready_for_download:
            return 3
        return 2
    return 1

def render_step_badges():
    """Simple step indicator using Streamlit columns"""
    current_step = get_current_step()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if current_step >= 1:
            st.success("✓ Upload & OCR")
        else:
            st.info("1. Upload & OCR")
    
    with col2:
        if current_step >= 2:
            if current_step > 2:
                st.success("✓ Smart Bookmarking")
            else:
                st.warning("→ Smart Bookmarking")
        else:
            st.info("2. Smart Bookmarking")
    
    with col3:
        if current_step >= 3:
            st.warning("→ Download")
        else:
            st.info("3. Download")

def initialize_session_state():
    """Initialize session state variables"""
    if 'page_assignments' not in st.session_state:
        st.session_state.page_assignments = {}
    
    if 'current_batch' not in st.session_state:
        st.session_state.current_batch = 0

def cleanup_temp_files():
    """Clean up temporary files"""
    if hasattr(st.session_state, 'temp_path') and st.session_state.temp_path:
        try:
            if os.path.exists(st.session_state.temp_path):
                os.unlink(st.session_state.temp_path)
        except Exception:
            pass

def main():
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("⚡ OCR & Bookmarking Studio")
    
    # Step indicator
    render_step_badges()
    st.divider()
    
    # Determine current step
    current_step = get_current_step()
    
    # Step 1: Upload & OCR
    if current_step == 1:
        st.markdown('<div class="step-container">', unsafe_allow_html=True)
        st.subheader("Step 1: Upload PDF")
        
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
                                st.rerun()
                            else:
                                st.error("OCR conversion failed")
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Step 2: Smart Bookmarking
    elif current_step == 2:
        st.subheader("Step 2: Smart Bookmarking")
        
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
                default_assignment = {"type": "Index", "number": ""}
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
                category_options = ["Index", "Original Application (OA)", "Annexures", "Vakalath"]
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
                else:
                    annexure_number = ""
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
                current_assignment.get("number", "") != annexure_number):
                st.session_state.page_assignments[page_num] = {
                    "type": category,
                    "number": annexure_number
                }
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Assignment Summary
        if st.session_state.page_assignments:
            all_assignments = calculate_cascading_assignments(st.session_state.page_assignments, total_pages)
            
            st.divider()
            st.subheader("Assignment Overview")
            
            assignment_summary = {}
            for page_num, assignment in all_assignments.items():
                category = assignment["type"]
                if assignment["type"] == "Annexures" and assignment["number"]:
                    category = f"Annexure A{assignment['number']}"
                
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
            
            # Progress to step 3
            manual_count = len(st.session_state.page_assignments)
            progress_pct = (len(all_assignments) / total_pages) * 100
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"{manual_count} anchor points → {len(all_assignments)} pages covered ({progress_pct:.0f}%)")
            
            with col2:
                if st.button("Create PDF", type="primary"):
                    st.session_state.ready_for_download = True
                    st.rerun()
    
    # Step 3: Download
    elif current_step >= 3:
        st.subheader("Step 3: Download")
        
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
                    category = assignment["type"]
                    if assignment["type"] == "Annexures" and assignment["number"]:
                        category = f"Annexure A{assignment['number']}"
                    
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
        
        # Back button
        if st.button("← Back to Edit Bookmarks", type="secondary"):
            if 'ready_for_download' in st.session_state:
                del st.session_state.ready_for_download
            if 'final_pdf_bytes' in st.session_state:
                del st.session_state.final_pdf_bytes
            st.rerun()

# Sidebar
def render_sidebar():
    with st.sidebar:
        current_step = get_current_step()
        
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
        
        # Quick batch navigation for step 2
        if current_step == 2 and hasattr(st.session_state, 'total_pages'):
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

# Run app
if __name__ == "__main__":
    render_sidebar()
    main()
    
    # Cleanup on exit (register cleanup function)
    import atexit
    atexit.register(cleanup_temp_files)
