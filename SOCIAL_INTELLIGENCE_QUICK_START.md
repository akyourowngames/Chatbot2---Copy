# KAI Social Intelligence - Quick Start Guide

## What Just Happened?

KAI now has **social intelligence** - it responds to the **situation behind your input**, not just the literal words. This makes KAI sound more human, contextually appropriate, and socially aware.

---

## Try It Out!

### Test 1: Casual Introduction
Open your KAI chat and type:
```
hey kai give your introduction to my friends
```

**What you'll notice:**
- Casual, cool tone (not robotic)
- Makes you look good (not showing off)
- Natural language

### Test 2: Professional Context
```
explain what you do for my portfolio in a professional way
```

**What you'll notice:**
- Formal, competent tone
- Professional language
- No casual slang

### Test 3: Simple Question
```
what is 2+2?
```

**What you'll notice:**
- Fast, direct answer
- No unnecessary social processing
- Efficient response

---

## How It Works

```
Your Input → KAI detects:
  - Who's listening (friends? boss? solo?)
  - What you want (look competent? get help?)
  - Social risk (how bad if this goes wrong?)
  
→ Transforms response to match context
→ Checks if it sounds natural
→ Learns your communication style
```

---

## Configuration (Optional)

Social intelligence is **enabled by default**. To customize:

### Disable Globally
Add to `.env`:
```env
SOCIAL_INTELLIGENCE_ENABLED=false
```

### Enable Debug Mode
See detailed context analysis:
```env
SOCIAL_INTELLIGENCE_DEBUG=true
```

### Disable Per-Call (In Code)
```python
from Backend.LLM import ChatCompletion

response = ChatCompletion(
    messages, 
    apply_social_intelligence=False  # Skip social processing
)
```

---

## What Changed?

### New Features ✨
- **Context Detection**: Knows if you're talking to friends, boss, or solo
- **Persona Adaptation**: Changes tone based on audience
- **Vibe Check**: Prevents robotic/cringe responses
- **Style Learning**: Remembers your communication preferences

### Files Added
- `Backend/SocialIntelligence.py` - The brain
- `Data/social_profiles/` - Your learned preferences
- `Backend/test_social_intelligence.py` - Tests
- `SOCIAL_INTELLIGENCE_CONFIG.md` - Detailed config guide

### Files Modified
- `Backend/LLM.py` - Added social intelligence hook

---

## Performance Impact

- **Latency**: +200-500ms per response (one extra Gemini call)
- **Cost**: Uses Gemini Flash (cheap and fast)
- **Smart Skipping**: Simple queries skip social processing automatically

---

## Examples

### Before Social Intelligence
**Input:** "introduce yourself to my friends"
**Response:** "I am KAI, an artificial intelligence assistant designed to help with various computational tasks..."

### After Social Intelligence
**Input:** "introduce yourself to my friends"
**Response:** "Hey! I'm KAI — basically his second brain when things get busy. I help with research, automation, and keeping everything organized."

---

## Need Help?

- **Full Documentation**: See `walkthrough.md` in artifacts
- **Configuration**: See `SOCIAL_INTELLIGENCE_CONFIG.md`
- **Tests**: Run `python Backend\test_social_intelligence.py`

---

## What's Next?

The social intelligence system will continue learning from your conversations:
- Tracks corrections
- Learns tone preferences
- Adapts to your style
- Improves over time

**Just use KAI normally - it will learn!** 🧠✨
