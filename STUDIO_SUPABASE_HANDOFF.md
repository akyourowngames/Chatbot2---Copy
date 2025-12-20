# Studio Team Handoff: Supabase Persistence Integration

## Overview
We have integrated Supabase Storage for all file operations (Generations, Uploads, Captures).
All files generated or uploaded are now:
1.  Saved locally (for development/analysis cache).
2.  **Uploaded to Supabase Storage** (Bucket: `kai-files`) in production or if `USE_SUPABASE_STORAGE=true`.
3.  Returned with a `url` field in the API response.

## Frontend Requirements

### 1. File Uploads (Vision & Generic)
When uploading files, check the `success` field (boolean) and use `file.url` for display/links.

**Endpoint:** `POST /api/v1/files/upload`
**Form Data:** 
- `file`: The file object.
- `auto_analyze`: "true" (for images to get analysis) or "false".

**Response (JSON):**
```json
{
  "success": true, 
  "file": {
    "filename": "20241220_110316_doc.txt",
    "filepath": "C:\\...\\Data\\Uploads\\20241220_110316_doc.txt",
    "url": "https://skbfmcwrshxnmaxfqyaw.supabase.co/storage/v1/object/public/kai-files/uploads/20241220_110316_doc.txt",
    "type": "document",
    "size_mb": 0.01
  },
  "analysis": { ... } // If auto_analyze=true and image
}
```

### 2. Document Generation (PDF/PPTX)
**Endpoint:** `POST /api/v1/documents/pdf` or `/api/v1/documents/powerpoint`

**Response (JSON):**
```json
{
  "status": "success",
  "message": "Created successfully",
  "filepath": "...",
  "url": "https://.../kai-files/documents/MyDoc.pdf"
}
```

### 3. Website Capture
**Response (JSON):**
```json
{
  "status": "success",
  "pdf": "https://.../kai-files/captures/website.pdf",
  "screenshot": "https://.../kai-files/captures/website.jpg"
}
```

### 4. Implementation in `chat.html`
- **File Uploads:** Updated `uploadToSupabase` to parse `file.url` and create Markdown links: `[Filename](URL)`.
- **Image Analysis:** Updated `uploadAndAnalyzeImage` to use `/api/v1/files/upload` with `auto_analyze=true`.
- **PDF Previews:** Already handles `url` field.
- **Persistence:** Chat history saves the `url` in the message content, so links remain valid across sessions/devices.

## Environment Variables
Ensure `.env` has:
```
USE_SUPABASE_STORAGE=true
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_BUCKET=kai-files
```
