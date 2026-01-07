"""
Quick script to add automation endpoints to api_server.py
Run this to integrate the bookmarklet system
"""

# Copy this code and paste it after line 700 in api_server.py (after auth endpoints)

AUTOMATION_ENDPOINTS = """
# ==================== BROWSER AUTOMATION ENDPOINTS ====================

@app.route('/api/v1/automation/analyze-page', methods=['POST', 'OPTIONS'])
def automation_analyze_page():
    '''Analyze a webpage content and structure'''
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        url = data.get('url')
        title = data.get('title')
        forms = data.get('forms', [])
        text = data.get('text', '')
        
        # Use LLM to analyze
        from Backend.LLM import ChatCompletion
        
        prompt = f'''Analyze this webpage:
URL: {url}
Title: {title}
Forms: {len(forms)}
Text: {text[:500]}

Brief analysis:'''
        
        analysis = ChatCompletion(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            text_only=True
        )
        
        response = jsonify({
            "success": True,
            "analysis": analysis,
            "forms_detected": len(forms)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"[AUTOMATION] Error: {e}")
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@app.route('/api/v1/automation/fill-form-smart', methods=['POST', 'OPTIONS'])
def automation_fill_form():
    '''Intelligently fill form using AI'''
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    try:
        data = request.json
        forms = data.get('forms', [])
        
        if not forms:
            response = jsonify({"error": "No forms detected"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Sample user data (TODO: Get from Firebase)
        user_data = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890"
        }
        
        # Simple field mapping
        form = forms[0]
        mappings = {}
        
        for field in form.get('fields', []):
            name = field.get('name', '').lower()
            if 'email' in name:
                mappings[f"input[name='{field['name']}']"] = user_data['email']
            elif 'first' in name and 'name' in name:
                mappings[f"input[name='{field['name']}']"] = user_data['firstName']
            elif 'last' in name and 'name' in name:
                mappings[f"input[name='{field['name']}']"] = user_data['lastName']
            elif 'phone' in name:
                mappings[f"input[name='{field['name']}']"] = user_data['phone']
        
        response = jsonify({
            "success": True,
            "mappings": mappings,
            "fields_filled": len(mappings)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"[AUTOMATION] Error: {e}")
        response = jsonify({"error": str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# ==================== END AUTOMATION ====================
"""

print("Copy the code above and paste into api_server.py around line 700")
print("Then restart the backend: python api_server.py")
