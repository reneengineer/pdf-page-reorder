#!/usr/bin/env python3
"""
PDF Page Reorder Tool
Streamlit app for reordering PDF pages - specifically for moving Unit Summary to front
"""

import streamlit as st
import fitz  # PyMuPDF
import io
from datetime import datetime
from PIL import Image

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_summary_page(pdf_bytes):
    """Find the page containing 'Unit Summary' or 'Summary'"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().lower()

        # Check for summary indicators
        if "unit summary" in text or "summary" in text.lower():
            doc.close()
            return page_num

    doc.close()
    return None

def get_page_thumbnail(pdf_bytes, page_num, width=200):
    """Generate thumbnail image of a PDF page"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]

    # Calculate zoom to get desired width
    zoom = width / page.rect.width
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")

    doc.close()
    return img_bytes

def reorder_pdf(pdf_bytes, new_order):
    """Reorder PDF pages according to new_order list"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Create a new PDF with pages in new order
    new_doc = fitz.open()

    for page_num in new_order:
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    # Save to bytes
    output_bytes = new_doc.tobytes()

    doc.close()
    new_doc.close()

    return output_bytes

def move_page_to_front(pdf_bytes, page_num):
    """Move a specific page to the front of the PDF"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)

    # Create new order: [page_num] + [all other pages]
    new_order = [page_num] + [i for i in range(total_pages) if i != page_num]

    doc.close()

    return reorder_pdf(pdf_bytes, new_order)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

# Page configuration
st.set_page_config(
    page_title="PDF Page Reorder",
    page_icon="📄",
    layout="wide"
)

# Title
st.markdown("# 📄 PDF Page Reorder Tool")
st.markdown("### Reorder pages in billing reports - Move Unit Summary to front")

# Main content
uploaded_file = st.file_uploader(
    "📤 Upload PDF",
    type=['pdf'],
    help="Upload your billing report PDF"
)

if uploaded_file:
    st.success(f"✓ Uploaded: {uploaded_file.name}")

    # Read PDF
    uploaded_file.seek(0)
    pdf_bytes = uploaded_file.read()

    # Open PDF to get page count
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    doc.close()

    st.info(f"📊 Total pages: {total_pages}")

    # Auto-detect Summary page
    summary_page = find_summary_page(pdf_bytes)

    if summary_page is not None:
        st.success(f"✓ Found summary on page {summary_page + 1}")

        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("🚀 Move Summary to Front", type="primary", use_container_width=True):
                with st.spinner("Reordering pages..."):
                    reordered_pdf = move_page_to_front(pdf_bytes, summary_page)

                    st.session_state['reordered_pdf'] = reordered_pdf
                    st.session_state['filename'] = uploaded_file.name

                    st.success("✅ Summary moved to page 1!")
    else:
        st.warning("⚠️ No 'Unit Summary' page found - use manual reorder below")

    # Manual reorder section
    st.markdown("---")
    st.subheader("🔧 Manual Page Reorder")

    # Show page thumbnails
    st.markdown("**Current page order:**")

    cols = st.columns(min(5, total_pages))
    for i in range(total_pages):
        with cols[i % 5]:
            thumbnail = get_page_thumbnail(pdf_bytes, i, width=150)
            st.image(thumbnail, caption=f"Page {i + 1}", use_container_width=True)

    # Manual reorder input
    st.markdown("**Specify new page order:**")
    st.caption("Enter page numbers separated by commas (e.g., 3,1,2,4 to move page 3 to front)")

    default_order = ",".join(str(i+1) for i in range(total_pages))
    new_order_input = st.text_input(
        "New page order",
        value=default_order,
        help="Enter page numbers in desired order, separated by commas"
    )

    if st.button("🔄 Apply Custom Order", use_container_width=True):
        try:
            # Parse input
            new_order = [int(x.strip()) - 1 for x in new_order_input.split(",")]

            # Validate
            if len(new_order) != total_pages:
                st.error(f"Error: Must specify exactly {total_pages} page numbers")
            elif set(new_order) != set(range(total_pages)):
                st.error("Error: Invalid page numbers or duplicates")
            else:
                with st.spinner("Reordering pages..."):
                    reordered_pdf = reorder_pdf(pdf_bytes, new_order)

                    st.session_state['reordered_pdf'] = reordered_pdf
                    st.session_state['filename'] = uploaded_file.name

                    st.success(f"✅ Pages reordered: {new_order_input}")
        except ValueError:
            st.error("Error: Invalid input. Use comma-separated numbers (e.g., 3,1,2,4)")

    # Download section
    if 'reordered_pdf' in st.session_state:
        st.markdown("---")
        st.subheader("📥 Download Reordered PDF")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = st.session_state['filename'].replace('.pdf', '')

        st.download_button(
            label="📄 Download Reordered PDF",
            data=st.session_state['reordered_pdf'],
            file_name=f"{base_name}_reordered_{timestamp}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        # Show preview of reordered PDF
        st.markdown("**Preview (first 3 pages):**")
        cols = st.columns(3)
        for i in range(min(3, total_pages)):
            with cols[i]:
                thumbnail = get_page_thumbnail(st.session_state['reordered_pdf'], i, width=200)
                st.image(thumbnail, caption=f"New Page {i + 1}", use_container_width=True)
else:
    st.info("👆 Upload a PDF to get started")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
    <p>PDF Page Reorder Tool | Built with Streamlit + PyMuPDF</p>
    <p style='font-size: 0.8em;'>Perfect for billing reports with unit summaries</p>
    </div>
""", unsafe_allow_html=True)
