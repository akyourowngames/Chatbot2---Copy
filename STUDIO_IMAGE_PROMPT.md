
    # Prompt for Studio Team: Supabase Image Integration

    ## Context
    We have updated the backend to upload generated images directly to our Supabase Storage bucket (`kai-files`). 
    Previously, images were stored locally in `/data/Images/` and served via static file serving.
    Now, the API returns a full HTTPS URL pointing to Supabase Cloud Storage (e.g., `https://<YOUR_PROJECT>.supabase.co/storage/v1/object/public/kai-files/generated/my_image.png`).

    ## Objective
    Update the frontend (`chat.html` and related JS) to correctly handle and display these cloud URLs for generated images.

    ## Instructions for Studio Team/AI

    1.  **Locate Image Rendering Logic:**
        Find the code responsible for displaying generated images. This is likely in `chat.html` (specifically functions like `addImageMessage`, `addMessage`, or where valid responses from `/api/v1/image/generate` are handled).

    2.  **Update Logic to Handle Full URLs:**
        The backend now returns a list of URLs in the `images` field of the JSON response.
        *   **Old Behavior:** Paths were like `/data/Images/filename.png` or `C:\...\filename.png`.
        *   **New Behavior:** Paths are `https://...` (Cloud) OR `/data/Images/...` (Local fallback).
        
        Update the `src` attribute logic often found in your image card builder:
        ```javascript
        // BEFORE (Example)
        // const fullUrl = imageUrl.startsWith('http') ? imageUrl : `${BASE_URL}${imageUrl}`;
        
        // AFTER (Requirement)
        // Ensure you trust the full string if it starts with "http".
        // Only prepend BASE_URL if it does NOT start with "http" AND is a relative path.
        const fullUrl = imageUrl.startsWith('http') ? imageUrl : `${API_URL}${imageUrl}`;
        ```

    3.  **Check `addImageMessage` Function:**
        Ensure the `addImageMessage(role, imageUrl)` function directly accepts these new strings without trying to re-format them incorrectly. 
        
        *Code Snippet Reference (chat.html):*
        ```javascript
        function addImageMessage(role, imageUrl) {
            // ...
            // Ensure this works:
            const isCloud = imageUrl.startsWith('http');
            const displayUrl = isCloud ? imageUrl : `/data/Images/${imageUrl.split('/').pop()}`; // Fallback logic
            // ...
        }
        ```

    4.  **Verify Lightbox Implementation:**
        Ensure the "Lightbox" (click-to-expand) feature works with cross-origin (CORS) Supabase URLs. The `kai-files` bucket is public, so standard `<img>` tags will work fine.

    5.  **Persistence Check:**
        Verify that when the chat history is reloaded from `localStorage` (or Firebase), the `content` field containing these long Supabase URLs is preserved and rendered correctly.

    ## API Response Example
    **Endpoint:** `POST /api/v1/image/generate`
    **Response:**
    ```json
    {
    "status": "success",
    "images": [
        "https://skbfmcwrshxnmaxfqyaw.supabase.co/storage/v1/object/public/kai-files/generated/Cyberpunk_City_20251220_113500_1.png"
    ]
    }
    ```

    ## Note on Folder Structure
    Images are automatically organized into the `generated/` folder within the `kai-files` bucket. You do not need to manually construct this path; simply use the URL provided by the API.
