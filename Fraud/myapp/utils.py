import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from io import BytesIO
import tempfile

# Set the path to the installed Tesseract OCR executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_files(files):
    """
    Extracts text from a list of uploaded files (PDFs or Images).
    """
    texts = []
    for f in files:
        name = f.name.lower()
        if name.endswith('.pdf'):
            texts.append(extract_text_from_pdf(f))
        elif name.endswith(('.jpg', '.jpeg', '.png')):
            texts.append(extract_text_from_image(f))
        else:
            print(f"Unsupported file format: {name}")
            continue
    return texts

def extract_text_from_pdf(file):
    """
    Extracts text from a PDF using PyMuPDF, with OCR fallback if needed.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    text = ''
    try:
        doc = fitz.open(tmp_path)
        for page in doc:
            page_text = page.get_text().strip()
            if not page_text:
                # OCR fallback if page is image-only
                pix = page.get_pixmap(dpi=300)
                img = Image.open(BytesIO(pix.tobytes('png')))
                page_text = pytesseract.image_to_string(img).strip()
            text += page_text + '\n'
        doc.close()
    finally:
        os.remove(tmp_path)

    return text.strip()

def extract_text_from_image(file):
    """
    Extracts text from an image file using pytesseract OCR.
    """
    img = Image.open(file)
    return pytesseract.image_to_string(img).strip()
