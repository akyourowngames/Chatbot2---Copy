# ==================== BROWSER AUTOMATION ENDPOINTS ====================

@app.route('/api/v1/automation/analyze-page', methods=['POST', 'OPTIONS'])
def automation_analyze_page():
    """Analyze a webpage's content and structure"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.json
        url = data.get('url')
        title = data.get('title')
        forms = data.get('forms', [])
        text = data.get('text', '')
        
        # Use Gemini to analyze the page
        from Backend.LLM import ChatCompletion
        
        prompt = f"""Analyze this webpage and provide insights:

URL: {url}
Title: {title}
Number of forms: {len(forms)}
Text preview: {text[:1000]}

Provide a concise analysis including:
1. Page purpose/type
2. Key actions a user can take
3. Any forms or interactions available
4. Suggestions for automation
"""
        
        analysis = ChatCompletion(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            text_only=True
        )
        
        response = jsonify({
            "success": True,
            "analysis": analysis,
            "forms_detected": len(forms),
            "url": url
        })
        return _corsify_actual_response(response)
        
    except Exception as e:
        print(f"[AUTOMATION] Analyze error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({"error": str(e)})
        return _corsify_actual_response(response), 500


@app.route('/api/v1/automation/fill-form-smart', methods=['POST', 'OPTIONS'])
def automation_fill_form():
    """Intelligently fill a form using user data and AI"""
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        data = request.json
        url = data.get('url')
        forms = data.get('forms', [])
        
        if not forms or len(forms) == 0:
            response = jsonify({"error": "No forms detected"})
            return _corsify_actual_response(response), 400
        
        # Get first form (or specified form index)
        form = forms[0]
        fields = form.get('fields', [])
        
        # TODO: Get user profile data from Firebase
        # For now, use sample data
        user_data = {
            "firstName": "John",
            "lastName": "Doe",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "address": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102",
            "country": "USA"
        }
        
        # Use Gemini to map fields intelligently
        from Backend.LLM import ChatCompletion
        
        fields_desc = "\n".join([
            f"- {f['name']} ({f['type']}): {f.get('label', 'No label')}"
            for f in fields
        ])
        
        prompt = f"""Map user data to form fields intelligently.

Form fields:
{fields_desc}

User data:
{json.dumps(user_data, indent=2)}

Return ONLY a JSON object mapping field names/selectors to values:
{{
  "input[name='firstName']": "John",
  "input[name='email']": "john.doe@example.com"
}}

Use CSS selectors like: input[name='X'], #id, .class
"""
        
        mapping_text = ChatCompletion(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            text_only=True
        )
        
        # Parse JSON from response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in mapping_text:
                mapping_text = mapping_text.split("```json")[1].split("```")[0]
            elif "```" in mapping_text:
                mapping_text = mapping_text.split("```")[1].split("```")[0]
            
            mappings = json.loads(mapping_text.strip())
        except json.JSONDecodeError:
            # Fallback: simple mapping
            mappings = {}
            for field in fields:
                field_name = field['name']
                field_type = field['type']
                
                # Simple heuristic matching
                if 'email' in field_name.lower():
                    mappings[f"input[name='{field_name}']"] = user_data.get('email')
                elif 'first' in field_name.lower() and 'name' in field_name.lower():
                    mappings[f"input[name='{field_name}']"] = user_data.get('firstName')
                elif 'last' in field_name.lower() and 'name' in field_name.lower():
                    mappings[f"input[name='{field_name}']"] = user_data.get('lastName')
                elif 'name' in field_name.lower():
                    mappings[f"input[name='{field_name}']"] = user_data.get('name')
                elif 'phone' in field_name.lower():
                    mappings[f"input[name='{field_name}']"] = user_data.get('phone')
        
        response = jsonify({
            "success": True,
            "mappings": mappings,
            "fields_filled": len(mappings)
        })
        return _corsify_actual_response(response)
        
    except Exception as e:
        print(f"[AUTOMATION] Fill form error: {e}")
        import traceback
        traceback.print_exc()
        response = jsonify({"error": str(e)})
        return _corsify_actual_response(response), 500

# ==================== END OF AUTOMATION ENDPOINTS ====================
