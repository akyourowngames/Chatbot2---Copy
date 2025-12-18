# Tesseract OCR Installation Guide

## What is Tesseract?

Tesseract is an open-source OCR (Optical Character Recognition) engine that extracts text from images. The VQA system uses it to read text from uploaded images.

## Installation Instructions

### Windows

1. **Download Tesseract Installer**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest installer (e.g., `tesseract-ocr-w64-setup-5.3.3.exe`)

2. **Run the Installer**
   - Double-click the downloaded `.exe` file
   - Follow the installation wizard
   - **IMPORTANT**: Note the installation path (default: `C:\Program Files\Tesseract-OCR`)

3. **Add to System PATH**
   - Open System Properties → Advanced → Environment Variables
   - Under "System variables", find and edit "Path"
   - Add new entry: `C:\Program Files\Tesseract-OCR`
   - Click OK to save

4. **Verify Installation**
   ```powershell
   tesseract --version
   ```
   You should see version information if installed correctly.

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

### macOS

```bash
brew install tesseract
```

## Python Package Installation

After installing Tesseract binary, install the Python wrapper:

```bash
pip install pytesseract
```

## Configuration (Optional)

If Tesseract is not in your PATH, you can specify the path in your code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Testing

Test Tesseract with a simple Python script:

```python
from PIL import Image
import pytesseract

# Test with an image
image = Image.open('test_image.png')
text = pytesseract.image_to_string(image)
print(text)
```

## Troubleshooting

### "TesseractNotFoundError"
- Tesseract binary is not installed or not in PATH
- Solution: Follow installation steps above and ensure PATH is set correctly

### "Permission Denied"
- Tesseract doesn't have permission to access temp files
- Solution: Run as administrator or check file permissions

### Poor OCR Accuracy
- Image quality is too low
- Solution: Use higher resolution images with clear text

## Additional Languages

Tesseract supports 100+ languages. To install additional language packs:

**Windows**: Select languages during installation

**Linux**:
```bash
sudo apt-get install tesseract-ocr-[lang]
# Example for Spanish:
sudo apt-get install tesseract-ocr-spa
```

**macOS**:
```bash
brew install tesseract-lang
```

## Resources

- Official Documentation: https://github.com/tesseract-ocr/tesseract
- Language Data: https://github.com/tesseract-ocr/tessdata
- Python Wrapper Docs: https://pypi.org/project/pytesseract/
