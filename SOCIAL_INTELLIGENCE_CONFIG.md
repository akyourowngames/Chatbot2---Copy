# Social Intelligence Configuration Guide

Add these environment variables to your `.env` file to configure the social intelligence system:

```env
# ==================== SOCIAL INTELLIGENCE SETTINGS ====================
# Enable/disable social intelligence processing (default: true)
SOCIAL_INTELLIGENCE_ENABLED=true

# Which model to use for social intelligence (default: gemini-1.5-flash)
# Options: gemini-1.5-flash (recommended), gemini-1.5-pro
SOCIAL_INTELLIGENCE_MODEL=gemini-1.5-flash

# Enable detailed logging for debugging (default: false)
SOCIAL_INTELLIGENCE_DEBUG=false
```

## What These Do:

- **SOCIAL_INTELLIGENCE_ENABLED**: Turn the social intelligence system on/off globally
- **SOCIAL_INTELLIGENCE_MODEL**: Choose which Gemini model to use (flash is faster and cheaper)
- **SOCIAL_INTELLIGENCE_DEBUG**: Enable verbose logging to see context analysis and transformations

## Performance Notes:

- Social intelligence adds ~200-500ms per response (one extra Gemini API call)
- Uses Gemini Flash by default for speed and cost efficiency
- Automatically skips processing for simple queries to save API calls
- Can be disabled per-call with `apply_social_intelligence=False`

## Example Usage in Code:

```python
from Backend.LLM import ChatCompletion

# With social intelligence (default)
response = ChatCompletion(messages, user_id="user123")

# Without social intelligence (for system messages, etc.)
response = ChatCompletion(messages, user_id="user123", apply_social_intelligence=False)
```
