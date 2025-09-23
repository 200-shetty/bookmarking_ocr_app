import streamlit as st 
import fitz
import tempfile
import pytesseract
from PIL import Image
import io
import base64
import os

def safe_pdf_open(pdf_bytes):
    """Uploader support helper function to safely open PDF from bytes"""
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
        

def create_ocr_pdf(original_pdf):
    """Uploader support helper function to create OCR PDF"""
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
                
                # Try to perform OCR if Tesseract is available
                try:
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
                except Exception as e:
                    # If OCR fails, continue without OCR text
                    pass
                
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
        
    except Exception as e:
        st.error(f"PDF processing error: {str(e)}")
        return None
    

def get_page_image_base64(page, size_factor=1.5):
    """Helper for bookmark_handler to get base64 image of a PDF page for preview"""
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
    """Helper for bookmark_handler to create HTML for zoomable page preview"""
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

def calculate_cascading_assignments(page_assignments, total_pages):
    """Helper for bookmark_handler to calculate page assignments with cascading logic"""
    cascaded_assignments = {}
    
    if not page_assignments:
        return {}
    
    # Sort assignment points by page number
    assignment_points = sorted(page_assignments.items())
    
    # Add default starting point if first assignment isn't page 1
    if assignment_points[0][0] > 1:
        assignment_points.insert(0, (1, {"type": "Index", "number": "", "custom_name": ""}))
    
    # Apply cascading logic
    for i, (page_num, assignment) in enumerate(assignment_points):
        # Determine end page for this assignment
        end_page = assignment_points[i + 1][0] - 1 if i < len(assignment_points) - 1 else total_pages
        
        # Apply assignment to all pages in range
        for page in range(page_num, end_page + 1):
            cascaded_assignments[page] = assignment.copy()
    
    return cascaded_assignments


def create_bookmarks_from_assignments(pdf_doc, page_assignments, total_pages):
    """Helper for extractionCreate PDF bookmarks from page assignments"""
    try:
        all_assignments = calculate_cascading_assignments(page_assignments, total_pages)
        
        if not all_assignments:
            return pdf_doc
        
        # Group pages by category
        categories = {}
        for page_num, assignment in all_assignments.items():
            # Use custom name if provided, otherwise generate from type and number
            if assignment.get("custom_name"):
                category = assignment["custom_name"]
            elif assignment["type"] == "Annexures" and assignment["number"]:
                category = f"Annexure A{assignment['number']}"
            else:
                category = assignment["type"]
            
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
    

def initialize_session_state():
    """Helper for sidebar to initialize session state variables"""
    if 'page_assignments' not in st.session_state:
        st.session_state.page_assignments = {}
    
    if 'current_batch' not in st.session_state:
        st.session_state.current_batch = 0

def cleanup_temp_files():
    """Helper for sidebar to clean up temporary files"""
    if hasattr(st.session_state, 'temp_path') and st.session_state.temp_path:
        try:
            if os.path.exists(st.session_state.temp_path):
                os.unlink(st.session_state.temp_path)
        except Exception:
            pass
