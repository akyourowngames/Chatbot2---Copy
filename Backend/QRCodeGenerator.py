"""
QR Code Generator
=================
Generate QR codes for URLs, text, and more
"""

import os
from typing import Dict, Any

class QRCodeGenerator:
    def __init__(self):
        self.qr_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "QR_Codes")
        os.makedirs(self.qr_dir, exist_ok=True)
        
        # Check if qrcode library is available
        self.qrcode_available = False
        try:
            import qrcode
            self.qrcode_available = True
            print("[OK] QR Code Generator initialized")
        except ImportError:
            print("[WARN] qrcode library not available. Install with: pip install qrcode[pil]")
    
    def generate(self, data: str, filename: str = None, size: int = 512) -> Dict[str, Any]:
        """Generate QR code"""
        if not self.qrcode_available:
            return {
                "status": "error",
                "error": "QR code library not installed. Run: pip install qrcode[pil]"
            }
        
        try:
            import qrcode
            from datetime import datetime
            
            # Generate filename if not provided
            if not filename:
                safe_data = "".join(c if c.isalnum() else "_" for c in data[:30])
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"qr_{safe_data}_{timestamp}.png"
            
            # Ensure .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            filepath = os.path.join(self.qr_dir, filename)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize if needed
            if size != 512:
                img = img.resize((size, size))
            
            # Save
            img.save(filepath)
            
            return {
                "status": "success",
                "message": f"✅ QR Code generated!",
                "filepath": filepath,
                "filename": filename,
                "data": data,
                "size": f"{size}x{size}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "data": data
            }
    
    def generate_url(self, url: str, filename: str = None) -> Dict[str, Any]:
        """Generate QR code for URL"""
        return self.generate(url, filename)
    
    def generate_text(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Generate QR code for text"""
        return self.generate(text, filename)
    
    def generate_wifi(self, ssid: str, password: str, security: str = "WPA") -> Dict[str, Any]:
        """Generate QR code for WiFi credentials"""
        wifi_string = f"WIFI:T:{security};S:{ssid};P:{password};;"
        filename = f"wifi_{ssid}.png"
        return self.generate(wifi_string, filename)
    
    def generate_contact(self, name: str, phone: str = "", email: str = "") -> Dict[str, Any]:
        """Generate QR code for contact (vCard)"""
        vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\n"
        if phone:
            vcard += f"TEL:{phone}\n"
        if email:
            vcard += f"EMAIL:{email}\n"
        vcard += "END:VCARD"
        
        filename = f"contact_{name.replace(' ', '_')}.png"
        return self.generate(vcard, filename)

# Global instance
qr_generator = QRCodeGenerator()

if __name__ == "__main__":
    print("QR Code Generator initialized!")
    print(f"QR directory: {qr_generator.qr_dir}")
    print(f"QRCode available: {qr_generator.qrcode_available}")
