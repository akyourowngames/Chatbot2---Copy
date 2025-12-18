import re

# Read the file
with open('chat.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the problematic section
old_pattern = r"let message = `✅ \*\*File Uploaded & Analyzed\*\*\\n\\n`;\s+message \+= `📄 \*\*Filename:\*\* \$\{analysis\.filename\}\\n`;\s+message \+= `📊 \*\*Type:\*\* \$\{analysis\.file_type\}\\n`;\s+message \+= `💾 \*\*Size:\*\* \$\{analysis\.size_mb\} MB\\n\\n`;"

new_code = """let message = `✅ **File Uploaded Successfully**\\\\n\\\\n`;
                        message += `📄 **Filename:** ${fileInfo.filename}\\\\n`;
                        message += `📊 **Type:** ${fileInfo.type}\\\\n`;
                        message += `💾 **Size:** ${fileInfo.size_mb} MB\\\\n\\\\n`;"""

content = re.sub(old_pattern, new_code, content)

# Replace the image analysis section
old_image_check = r"if \(analysis\.type === 'image'\) \{"
new_image_check = "if (fileInfo.type === 'image' && analysis && analysis.success) {"
content = content.replace(old_image_check, new_image_check, 1)

# Replace AI description with VQA fields
old_ai_desc = r"// Show AI description FIRST and prominently\s+if \(analysis\.ai_description\) \{\s+message \+= `🤖 \*\*AI Description:\*\*\\n\$\{analysis\.ai_description\}\\n\\n`;\s+\}\s+// Then show technical details\s+message \+= `📸 \*\*Technical Details:\*\*\\n`;\s+message \+= `- Dimensions: \$\{analysis\.width\}x\$\{analysis\.height\} pixels\\n`;\s+message \+= `- Format: \$\{analysis\.format\}\\n`;\s+message \+= `- Megapixels: \$\{analysis\.megapixels\} MP\\n`;"

new_vqa_code = """message += `🤖 **AI Vision Analysis:**\\\\n\\\\n`;
                            if (analysis.caption) {
                                message += `**Caption:** ${analysis.caption}\\\\n\\\\n`;
                            }
                            if (analysis.ocr_text && analysis.ocr_text.trim()) {
                                message += `📝 **Text in Image:**\\\\n${analysis.ocr_text.substring(0, 200)}${analysis.ocr_text.length > 200 ? '...' : ''}\\\\n\\\\n`;
                            }
                            if (analysis.answer) {
                                message += `💬 **AI Analysis:**\\\\n${analysis.answer}\\\\n\\\\n`;
                            }
                            if (analysis.metadata) {
                                message += `⚙️ **Processing:** ${analysis.metadata.model}, ${analysis.metadata.processing_time_ms}ms\\\\n`;
                            }"""

content = re.sub(old_ai_desc, new_vqa_code, content, flags=re.DOTALL)

# Remove the code/text/pdf analysis sections and replace with simple else
old_other_types = r"\} else if \(analysis\.type === 'code'\) \{.*?\} else if \(analysis\.type === 'pdf'\) \{.*?\}"
new_else = """} else if (fileInfo.type === 'image') {
                            message += `📸 **Image uploaded**\\\\n`;
                        }"""

content = re.sub(old_other_types, new_else, content, flags=re.DOTALL)

# Fix the image display section
old_image_display = r"if \(analysis\.type === 'image'\) \{\s+addImageMessage\('assistant', `http://localhost:5000\$\{analysis\.filepath\.replace\(/\\\\\\\\/g, '/'\)\.split\('Data'\)\[1\] \? '/data' \+ analysis\.filepath\.replace\(/\\\\\\\\/g, '/'\)\.split\('Data'\)\[1\] : analysis\.filepath\}`\);\s+\}"

new_image_display = """if (fileInfo.type === 'image') {
                            const imageUrl = `http://localhost:5000/data/Uploads/${fileInfo.filename}`;
                            addImageMessage('assistant', imageUrl);
                        }"""

content = re.sub(old_image_display, new_image_display, content)

# Write back
with open('chat.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ chat.html updated successfully!")
