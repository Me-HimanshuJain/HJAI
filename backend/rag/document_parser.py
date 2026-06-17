import fitz  # PyMuPDF
from docx import Document

class DocumentParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes) -> str:
        """Extracts text from a PDF file."""
        text = ""
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return ""

    @staticmethod
    def parse_docx(file_bytes: bytes) -> str:
        """Extracts text from a DOCX file."""
        text = ""
        try:
            import io
            doc = Document(io.BytesIO(file_bytes))
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            return ""

    @staticmethod
    def parse_txt(file_bytes: bytes) -> str:
        """Extracts text from a TXT file."""
        try:
            return file_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error parsing TXT: {e}")
            return ""
