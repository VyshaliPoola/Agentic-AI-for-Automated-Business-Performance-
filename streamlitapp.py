import streamlit as st
from io import BytesIO
from typing import Tuple, Optional

# PDF + DOCX
from PyPDF2 import PdfReader
import docx


# ---------- Helper functions ----------
def count_words(text: str) -> int:
    # Splitting on whitespace is a reasonable "word" definition for most cases
    return len(text.split())


def count_lines(text: str) -> int:
    # Count visible lines from extracted text
    # If text is empty, return 0
    if not text.strip():
        return 0
    return len(text.splitlines())


def extract_txt(file_bytes: bytes) -> Tuple[str, int]:
    text = file_bytes.decode("utf-8", errors="ignore")
    pages = 1  # TXT doesn't have true "pages"
    return text, pages


def extract_pdf(file_bytes: bytes) -> Tuple[str, int]:
    reader = PdfReader(BytesIO(file_bytes))
    pages = len(reader.pages)
    all_text = []
    for p in reader.pages:
        all_text.append(p.extract_text() or "")
    return "\n".join(all_text), pages


def extract_docx(file_bytes: bytes) -> Tuple[str, int]:
    # Note: DOCX doesn't store an easy, reliable "page count" without rendering.
    # We'll estimate pages using a common heuristic (e.g., ~300 words per page).
    d = docx.Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in d.paragraphs if p.text]
    text = "\n".join(paragraphs)

    words = count_words(text)
    est_pages = max(1, round(words / 300)) if words > 0 else 1
    return text, est_pages


def extract_text_and_pages(file_name: str, file_bytes: bytes) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    lower = file_name.lower()

    try:
        if lower.endswith(".txt"):
            text, pages = extract_txt(file_bytes)
            return text, pages, None
        elif lower.endswith(".pdf"):
            text, pages = extract_pdf(file_bytes)
            return text, pages, None
        elif lower.endswith(".docx"):
            text, pages = extract_docx(file_bytes)
            return text, pages, "DOCX page count is estimated (DOCX pages depend on font/margins/rendering)."
        else:
            return None, None, "Unsupported file type. Please upload .txt, .pdf, or .docx."
    except Exception as e:
        return None, None, f"Could not read this file. Error: {e}"


# ---------- Streamlit page config ----------
st.set_page_config(
    page_title="File Stats Analyzer",
    page_icon="📄",
    layout="wide"
)

# ---------- Simple styling ----------
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
      .title { font-size: 2.0rem; font-weight: 750; margin-bottom: 0.25rem; }
      .subtitle { color: #666; margin-top: 0rem; margin-bottom: 1.25rem; }
      .hint { font-size: 0.92rem; color: #666; }
      .card {
        padding: 1rem 1.2rem;
        border-radius: 14px;
        border: 1px solid rgba(0,0,0,0.08);
        background: rgba(255,255,255,0.65);
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Header ----------
st.markdown('<div class="title">📄 File Stats Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Upload a file to instantly see words, lines, and pages.</div>', unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader("Choose a file", type=["txt", "pdf", "docx"])
    st.caption("Supported: .txt, .pdf, .docx")

    show_preview = st.checkbox("Show extracted text preview", value=True)
    st.divider()
    st.markdown("**Notes**")
    st.markdown(
        "- PDF pages are accurate.\n"
        "- TXT pages are set to 1.\n"
        "- DOCX pages are estimated (rendering-dependent)."
    )

# ---------- Main content ----------
if not uploaded:
    st.info("👈 Upload a file from the sidebar to begin.")
    st.stop()

file_bytes = uploaded.getvalue()
text, pages, warning = extract_text_and_pages(uploaded.name, file_bytes)

if warning and text is None:
    st.error(warning)
    st.stop()

if warning:
    st.warning(warning)

words = count_words(text or "")
lines = count_lines(text or "")

# Metrics row
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric("Words", f"{words:,}")
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric("Lines", f"{lines:,}")
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.metric("Pages", f"{pages:,}")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")  # spacer

# Preview + download report
left, right = st.columns([1.2, 1])

with left:
    st.subheader("File details")
    st.write(f"**File name:** {uploaded.name}")
    st.write(f"**File size:** {len(file_bytes)/1024:.1f} KB")

    report_text = (
        f"File Stats Report\n"
        f"-----------------\n"
        f"File: {uploaded.name}\n"
        f"Words: {words}\n"
        f"Lines: {lines}\n"
        f"Pages: {pages}\n"
    )
    st.download_button(
        "⬇️ Download report (TXT)",
        data=report_text.encode("utf-8"),
        file_name="file_stats_report.txt",
        mime="text/plain"
    )

with right:
    st.subheader("Preview")
    if show_preview:
        preview = (text or "").strip()
        if not preview:
            st.caption("No extractable text found.")
        else:
            # Keep preview readable: show first ~2500 chars
            st.text_area("Extracted text (preview)", preview[:2500], height=280)
    else:
        st.caption("Preview is off (toggle it on from the sidebar).")
