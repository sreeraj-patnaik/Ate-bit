import os


def extract_text_from_image(image_file):
    try:
        from PIL import Image
        import pytesseract
        from pytesseract import TesseractNotFoundError
    except Exception:
        return "", "OCR dependencies are missing. Install Pillow and pytesseract."

    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        image_file.seek(0)
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return cleaned, None
    except TesseractNotFoundError:
        return "", "Tesseract OCR engine is not installed. Install Tesseract and set TESSERACT_CMD if needed."
    except Exception as exc:
        return "", f"OCR failed: {exc}"
