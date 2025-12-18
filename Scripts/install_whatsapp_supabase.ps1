# WhatsApp + Supabase Installation Script
# =========================================
# Run this to install all required dependencies

Write-Host "Installing WhatsApp Automation + Supabase Dependencies..." -ForegroundColor Cyan

# Install Python packages
pip install supabase
pip install pywhatkit
pip install pyautogui
pip install pillow
pip install python-dotenv

Write-Host "`n✅ All dependencies installed!" -ForegroundColor Green

# Create .env file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "`nCreating .env file..." -ForegroundColor Yellow
    @"
SUPABASE_URL=https://skbfmcwrshxnmaxfqyaw.supabase.co
SUPABASE_KEY=sb_secret_kT3r_lTsBYBLwpv313A0qQ_przZ-Q8v
GROQ_API_KEY=your_groq_key_here
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ .env file created!" -ForegroundColor Green
} else {
    Write-Host "`n.env file already exists" -ForegroundColor Yellow
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://supabase.com and log in"
Write-Host "2. Open your project: skbfmcwrshxnmaxfqyaw"
Write-Host "3. Go to SQL Editor"
Write-Host "4. Run the schema from implementation_plan.md"
Write-Host "5. Log into WhatsApp Web manually (required for automation)"
Write-Host "6. Restart api_server.py"

Write-Host "`n🚀 Ready to use WhatsApp automation!" -ForegroundColor Green
