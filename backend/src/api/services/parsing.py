import fitz  # PyMuPDF
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_bytes: bytes) -> List[Dict[str, str | int]]:
    """
    Extracts text from a PDF byte array.
    Returns a list of dictionaries, one for each page:
    [
        {"page_number": 1, "text_content": "Text from page 1..."},
        {"page_number": 2, "text_content": "Text from page 2..."},
        ...
    ]
    """
    pages_data = []
    
    try:
        # Open the PDF directly from memory
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            
            # Clean up the text slightly (optional, depending on requirements)
            text = text.strip() if text else ""
            
            pages_data.append({
                "page_number": page_num + 1,  # 1-indexed page numbers
                "text_content": text
            })
            
        doc.close()
    except Exception as e:
        logger.error(f"Failed to parse PDF: {str(e)}")
        raise ValueError("Invalid or corrupted PDF file.") from e

    return pages_data
