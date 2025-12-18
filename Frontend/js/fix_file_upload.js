// Quick fix script - paste this into browser console after uploading an image

// Override the attachFile function
async function attachFile() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '*/*';

    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        addMessage('user', `📎 Uploading: ${file.name} (${(file.size / 1024).toFixed(2)} KB)`);
        const typingId = addTypingIndicator();

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('question', 'Describe this image in detail');
            formData.append('auto_analyze', 'true');

            const response = await fetch(`${API_URL}/files/upload`, {
                method: 'POST',
                headers: { 'X-API-Key': API_KEY },
                body: formData
            });

            const data = await response.json();
            removeTypingIndicator(typingId);

            if (data.success) {
                const fileInfo = data.file;
                const analysis = data.analysis;

                let message = `✅ **File Uploaded Successfully**\n\n`;
                message += `📄 **Filename:** ${fileInfo.filename}\n`;
                message += `📊 **Type:** ${fileInfo.type}\n`;
                message += `💾 **Size:** ${fileInfo.size_mb} MB\n\n`;

                if (fileInfo.type === 'image' && analysis && analysis.success) {
                    message += `🤖 **AI Vision Analysis:**\n\n`;

                    if (analysis.caption) {
                        message += `**Caption:** ${analysis.caption}\n\n`;
                    }

                    if (analysis.ocr_text && analysis.ocr_text.trim()) {
                        message += `📝 **Text in Image:**\n${analysis.ocr_text.substring(0, 200)}${analysis.ocr_text.length > 200 ? '...' : ''}\n\n`;
                    }

                    if (analysis.answer) {
                        message += `💬 **AI Analysis:**\n${analysis.answer}\n\n`;
                    }

                    if (analysis.metadata) {
                        message += `⚙️ **Processing:** ${analysis.metadata.model}, ${analysis.metadata.processing_time_ms}ms\n`;
                    }
                } else if (fileInfo.type === 'image') {
                    message += `📸 **Image uploaded**\n`;
                }

                addMessage('assistant', message);

                if (fileInfo.type === 'image') {
                    const imageUrl = `http://localhost:5000/data/Uploads/${fileInfo.filename}`;
                    addImageMessage('assistant', imageUrl);
                }
            } else {
                addMessage('assistant', `❌ Upload failed: ${data.error}`);
            }
        } catch (error) {
            removeTypingIndicator(typingId);
            addMessage('assistant', `❌ Error uploading file: ${error.message}`);
        }
    };

    input.click();
}

console.log('✅ VQA-enabled attachFile() function loaded! Try uploading an image now.');
