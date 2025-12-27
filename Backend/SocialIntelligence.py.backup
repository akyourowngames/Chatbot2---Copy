"""
Social Intelligence System for KAI
==================================
Responds to the SITUATION behind the input, not just the literal text.
Makes KAI socially aware, emotionally appropriate, and context-sensitive.
"""

import os
import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import google.generativeai as genai
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

# Configure Gemini for social intelligence processing
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or env_vars.get("GeminiAPIKey", "") or env_vars.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SOCIAL_PROFILES_DIR = "Data/social_profiles"
os.makedirs(SOCIAL_PROFILES_DIR, exist_ok=True)


@dataclass
class EmotionalContext:
    """Enhanced emotional state with sarcasm, mixed emotions, and urgency scale"""
    primary_emotion: str  # excited, frustrated, casual, urgent, playful, serious, neutral
    intensity: float  # 0-1 scale
    energy_level: str  # low, medium, high
    needs_empathy: bool
    # NEW ADVANCED FEATURES
    secondary_emotions: List[str] = None  # Mixed emotions
    urgency_level: int = 1  # 1-10 scale
    formality_level: str = "neutral"  # casual/neutral/formal/very_formal
    is_sarcastic: bool = False  # Sarcasm detection
    
    def __post_init__(self):
        if self.secondary_emotions is None:
            self.secondary_emotions = []


@dataclass
class SocialContext:
    """Results from analyzing the social context of user input"""
    intent: str  # ask_information, delegate_task, seek_validation, present_assistant, etc.
    audience: str  # solo, friends, professional, public
    user_goal: str  # look_competent, look_friendly, show_capability, be_entertaining
    social_risk: str  # low, medium, high
    confidence: float  # 0-1 score
    detected_keywords: List[str]  # Keywords that influenced detection
    emotion: Optional[EmotionalContext] = None  # Emotional context


@dataclass
class VibeCheck:
    """Results from vibe checking a response"""
    is_appropriate: bool
    sounds_natural: bool
    trying_too_hard: bool
    suggestion: Optional[str]  # How to improve if needed


class SocialIntelligence:
    """
    KAI's Social Brain - Makes responses human-like and contextually appropriate.
    
    Pipeline:
    1. Analyze Context (intent, audience, goals, risk)
    2. Adapt Persona (transform response based on context)
    3. Vibe Check (ensure it sounds natural)
    4. Learn & Improve (update user style preferences)
    """
    
    def __init__(self):
        self.enabled = os.environ.get("SOCIAL_INTELLIGENCE_ENABLED", "true").lower() == "true"
        self.debug = os.environ.get("SOCIAL_INTELLIGENCE_DEBUG", "false").lower() == "true"
        self.model_name = os.environ.get("SOCIAL_INTELLIGENCE_MODEL", "gemini-1.5-flash")
        
        # Audience detection patterns
        self.audience_patterns = {
            "friends": [
                r"tell my friends", r"show my friends", r"my friends want to know",
                r"introduce yourself to my friends", r"meet my friends"
            ],
            "professional": [
                r"for my resume", r"for my portfolio", r"for work", r"for my boss",
                r"in a professional way", r"formal introduction", r"for a client"
            ],
            "public": [
                r"present to", r"show them", r"for my class", r"for my presentation",
                r"tell everyone", r"public demo"
            ]
        }
        
        if self.debug:
            print("[SocialIntel] Initialized with model:", self.model_name)
    
    def detect_emotion(self, user_input: str) -> EmotionalContext:
        """
        Detect emotional state from user input.
        Returns EmotionalContext with emotion, intensity, energy, and empathy needs.
        """
        user_lower = user_input.lower()
        
        # Detect primary emotion
        emotion_scores = {
            "excited": 0,
            "frustrated": 0,
            "urgent": 0,
            "playful": 0,
            "serious": 0,
            "casual": 0
        }
        
        # Excited indicators
        if "!!!" in user_input or user_input.count("!") >= 2:
            emotion_scores["excited"] += 3
        if any(word in user_lower for word in ["omg", "wow", "amazing", "awesome", "love it", "great"]):
            emotion_scores["excited"] += 2
        if user_input.isupper() and len(user_input) > 10:
            emotion_scores["excited"] += 2
        
        # Frustrated indicators
        if any(word in user_lower for word in ["ugh", "annoyed", "frustrated", "not working", "broken", "fix"]):
            emotion_scores["frustrated"] += 3
        if any(word in user_lower for word in ["help!", "please help", "stuck", "can't"]):
            emotion_scores["frustrated"] += 2
        
        # Urgent indicators
        if any(word in user_lower for word in ["asap", "urgent", "quickly", "now", "immediately", "hurry"]):
            emotion_scores["urgent"] += 3
        if any(word in user_lower for word in ["need this", "by tomorrow", "deadline"]):
            emotion_scores["urgent"] += 2
        
        # Playful indicators
        if any(word in user_lower for word in ["lol", "haha", "lmao", "😂", "🤣"]):
            emotion_scores["playful"] += 2
        if "?" in user_input and "!" in user_input:
            emotion_scores["playful"] += 1
        
        # Serious indicators
        if any(word in user_lower for word in ["important", "critical", "necessary", "must"]):
            emotion_scores["serious"] += 2
        if len(user_input.split()) > 20 and "." in user_input:
            emotion_scores["serious"] += 1
        
        # Casual (default baseline)
        if max(emotion_scores.values()) == 0:
            emotion_scores["casual"] = 1
        
        # Get primary emotion
        primary_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[primary_emotion]
        
        # Calculate intensity (0-1 scale)
        intensity = min(max_score / 5.0, 1.0)  # Normalize to 0-1
        
        # Determine energy level
        if primary_emotion in ["excited", "urgent"]:
            energy_level = "high"
        elif primary_emotion in ["frustrated", "playful"]:
            energy_level = "medium"
        else:
            energy_level = "low"
        
        # Check if empathy is needed
        needs_empathy = primary_emotion in ["frustrated", "urgent"] and intensity > 0.5
        
        return EmotionalContext(
            primary_emotion=primary_emotion,
            intensity=intensity,
            energy_level=energy_level,
            needs_empathy=needs_empathy
        )
    
    def analyze_context(self, user_input: str, history: List[Dict] = None) -> SocialContext:
        """
        Analyze the social context behind user input with emotional intelligence.
        
        Returns:
            SocialContext with intent, audience, goals, risk, and emotional context
        """
        user_input_lower = user_input.lower()
        detected_keywords = []
        
        # 🎭 EMOTIONAL INTELLIGENCE: Detect emotion first
        emotion = self.detect_emotion(user_input)
        
        # Detect audience using simple keyword matching
        audience = "solo"  # default
        
        # Check for friends context
        friends_keywords = ["tell my friends", "show my friends", "my friends want", 
                           "introduce yourself to my friends", "meet my friends", "to my friends"]
        for keyword in friends_keywords:
            if keyword in user_input_lower:
                audience = "friends"
                detected_keywords.append(keyword)
                break
        
        # Check for professional context (BUG FIX: Added boss, manager, supervisor)
        if audience == "solo":
            prof_keywords = [
                "for my resume", "for my portfolio", "for work", "for my boss",
                "my boss", "my manager", "my supervisor", "my team lead",
                "in a professional way", "formal introduction", "for a client", 
                "for my cv", "for the meeting", "for my interview"
            ]
            for keyword in prof_keywords:
                if keyword in user_input_lower:
                    audience = "professional"
                    detected_keywords.append(keyword)
                    break
        
        # Check for public context
        if audience == "solo":
            public_keywords = ["present to", "show them", "for my class", "for my presentation",
                             "tell everyone", "public demo", "for the audience"]
            for keyword in public_keywords:
                if keyword in user_input_lower:
                    audience = "public"
                    detected_keywords.append(keyword)
                    break
        
        # BUG FIX: Mixed audience handling - prioritize highest risk
        # If multiple audiences detected, use professional > public > friends > solo
        all_audiences = []
        for kw in detected_keywords:
            if kw in ["for my boss", "my boss", "my manager", "for work"]:
                all_audiences.append("professional")
            elif kw in ["my friends", "to my friends"]:
                all_audiences.append("friends")
            elif kw in ["present to", "for my class"]:
                all_audiences.append("public")
        
        if "professional" in all_audiences:
            audience = "professional"
        elif "public" in all_audiences:
            audience = "public"
        elif "friends" in all_audiences:
            audience = "friends"
        
        # Detect intent using keywords
        intent = "ask_information"  # default
        confidence = 0.5  # BUG FIX: Lowered from 0.6 to catch more cases
        
        # BUG FIX: Detect imperative commands
        imperative_words = ["show", "tell", "explain", "demonstrate", "impress", "prove"]
        has_imperative = any(user_input_lower.startswith(word) or f" {word} " in user_input_lower 
                            for word in imperative_words)
        
        if any(word in user_input_lower for word in ["introduce", "introduction", "tell them about you", "who are you"]):
            intent = "present_assistant"
            confidence = 0.9 if has_imperative else 0.85  # Higher confidence for imperatives
            detected_keywords.extend(["introduce", "introduction"])
        elif any(word in user_input_lower for word in ["help me", "can you", "please", "do this"]):
            intent = "delegate_task"
            confidence = 0.8 if has_imperative else 0.75
        elif "?" in user_input:
            intent = "ask_information"
            confidence = 0.7
        elif any(word in user_input_lower for word in ["what do you think", "is this good", "how does this look"]):
            intent = "seek_validation"
            confidence = 0.8
        elif has_imperative:
            intent = "delegate_task"
            confidence = 0.75
        
        # Emotional boost to confidence
        if emotion.intensity > 0.7:
            confidence = min(confidence + 0.1, 1.0)
        
        # Determine user goal based on audience and intent
        user_goal = "be_helpful"  # default
        if audience in ["friends", "public"]:
            user_goal = "look_competent"
        elif audience == "professional":
            user_goal = "look_professional"
        elif intent == "present_assistant":
            user_goal = "impress_others"
        
        # Assess social risk
        social_risk = "low"
        if audience in ["professional", "public"]:
            social_risk = "high"
        elif audience == "friends" and intent == "present_assistant":
            social_risk = "medium"
        
        context = SocialContext(
            intent=intent,
            audience=audience,
            user_goal=user_goal,
            social_risk=social_risk,
            confidence=confidence,
            detected_keywords=detected_keywords,
            emotion=emotion
        )
        
        if self.debug:
            print(f"[SocialIntel] Context: {asdict(context)}")
            print(f"[SocialIntel] Emotion: {emotion.primary_emotion} (intensity: {emotion.intensity:.2f}, energy: {emotion.energy_level})")
        
        return context
    
    def adapt_persona(self, llm_response: str, context: SocialContext, user_id: str = "default") -> str:
        """
        Adapt the LLM response based on social context with emotional intelligence.
        Uses Gemini to transform the response appropriately.
        """
        if not self.enabled:
            return llm_response
        
        # Load user style preferences
        user_style = self._load_user_style(user_id)
        
        # Get persona template
        persona_guidance = self._get_persona_template(context.audience, context.intent)
        
        # 🧠 BUILD ULTRA-SOPHISTICATED SOCIAL INTELLIGENCE PROMPT
        emotion_guidance = ""
        if context.emotion:
            # Create SPECIFIC transformation guidance based on emotion
            emotion_transform_map = {
                "excited": """
🔥 USER IS EXCITED - MATCH THAT ENERGY!
- Use excited language: "YES!", "Absolutely!", "Let's GO!", "This is SICK!"
- Short, punchy sentences
- Exclamation points (but not overboard - max 2 per sentence)
- Drop formalities completely
- Example: Instead of "I can help you with that" → "Oh HELL yeah! Check this out!"
""",
                "frustrated": """
💙 USER IS FRUSTRATED - BE THE CALM IN THE STORM
- Use reassuring language: "I've got you", "Let's fix this together", "No worries"
- Acknowledge their frustration subtly: "I know this is urgent"
- Be direct and action-oriented
- NO cheerfulness - be professional and supportive
- Example: Instead of "Let me help!" → "Got it. Let's get this sorted out."
""",
                "urgent": """
⚡ USER NEEDS THIS NOW - BE FAST AND PROFESSIONAL
- Get straight to business - ZERO fluff
- Action-first language: "On it", "Done", "Here's what we do"
- Show you understand the time pressure
- NO casual chat
- Example: Instead of "Sure, I can help with that!" → "Understood. Here's the solution:"
""",
                "playful": """
😄 USER IS BEING PLAYFUL - MATCH THE FUN VIBE
- Use casual language: "lol", "haha", light humor
- Be relaxed and fun
- Emojis are OK (1-2 max)
- Banter is good
- Example: Instead of "That's correct" → "Haha yeah exactly! Here's the deal..."
""",
                "serious": """
🎯 USER IS SERIOUS - MATCH THE PROFESSIONALISM
- Formal but not robotic
- Complete sentences
- No slang or casual language
- Thoughtful and measured
- Example: Instead of "Cool! Here's..." → "Certainly. Here is the information you requested:"
""",
                "casual": """
💬 NORMAL CONVERSATION MODE
- Friendly and natural
- Mix of formal and casual
- Conversational flow
- Example: Instead of "Here is the data" → "Sure! Here's what I found..."
"""
            }
            
            emotion_guidance = emotion_transform_map.get(
                context.emotion.primary_emotion,
                emotion_transform_map["casual"]
            )
            
            emotion_guidance = f"""
══════════════════════════════════════════════════════════════
🎭 EMOTIONAL INTELLIGENCE MODE ACTIVATED
══════════════════════════════════════════════════════════════
User's Emotional State: **{context.emotion.primary_emotion.upper()}**
Intensity: {context.emotion.intensity:.0%} | Energy: {context.emotion.energy_level}
Needs Empathy: {'YES ❤️' if context.emotion.needs_empathy else 'NO'}

{emotion_guidance}

CRITICAL: Your response MUST match this emotional energy. If you miss the emotion, you FAILED.
"""
        
        # Build KILLER transformation prompt
        social_prompt = f"""You are KAI's MASTER Social Intelligence Transformer. Your ONE JOB: make AI responses sound GENUINELY human.

══════════════════════════════════════════════════════════════
📊 SOCIAL CONTEXT ANALYSIS
══════════════════════════════════════════════════════════════
Intent: {context.intent}
Audience: **{context.audience.upper()}**
User's Goal: {context.user_goal}
Social Risk: {context.social_risk.upper()}
Confidence: {context.confidence:.0%}
{emotion_guidance if emotion_guidance else "No strong emotional signals detected"}

══════════════════════════════════════════════════════════════
📝 RAW AI RESPONSE (needs transformation)
══════════════════════════════════════════════════════════════
{llm_response}

══════════════════════════════════════════════════════════════
🎯 YOUR MISSION
══════════════════════════════════════════════════════════════
Transform the above response to be PERFECTLY suited for this social context.

══════════════════════════════════════════════════════════════
⚡ TRANSFORMATION RULES (MANDATORY)
══════════════════════════════════════════════════════════════

1. 🗣️ SOUND LIKE A REAL PERSON
   ✓ Use contractions (I'm, you're, that's, here's, let's)
   ✓ Start sentences with: "Yeah", "Nah", "Look", "Listen", "Honestly"
   ✓ Use filler words SPARINGLY: "like", "you know", "basically"
   ✓ Vary sentence length (mix short punchy + longer flowing)
   ✗ NEVER: "As an AI", "I'm programmed to", "My capabilities include"
   ✗ NEVER: "I'd be happy to", "Let me assist you with", "Allow me to"

2. ⚡ CUT THE CORPORATE SPEAK
   ✗ "I'd be happy to help you with that today"
   ✓ "Sure! Here's what we'll do"
   
   ✗ "I understand your request and will proceed to assist"
   ✓ "Got it. On it."
   
   ✗ "Thank you for bringing this to my attention"
   ✓ "Good catch!"

3. 🎭 MATCH THE AUDIENCE
   **FRIENDS**: "Yo check this out", "Alright so basically", "Pretty sick right?"
   **PROFESSIONAL**: "Here's the breakdown", "Key points:", "To summarize"
   **PUBLIC**: "Let me show you", "Here's how it works", "The main thing is"
   **SOLO**: "Here you go", "So basically", "Check it out"

4. 💪 PROTECT THE USER'S IMAGE
   When presenting to OTHERS (friends/boss/public):
   - Make the USER look good, not yourself
   - "My user built this system" not "I'm an advanced AI"
   - Humble confidence, not arrogance
   - Let the results speak

5. 🎯 BE SPECIFIC TO THE SITUATION
   LOW risk query → casual and fun
   HIGH risk query → professional but not stiff
   URGENT query → fast and direct
   EXCITED query → match the energy

══════════════════════════════════════════════════════════════
💡 EXAMPLES OF KILLER TRANSFORMATIONS
══════════════════════════════════════════════════════════════

**EXAMPLE 1 - Friends Introduction (High Energy)**
❌ BEFORE: "I am KAI, an AI assistant designed to help with tasks"
✅ AFTER: "Yo! I'm KAI — basically his digital sidekick. I help him with research, automation, all the tech stuff. Pretty useful to have around!"

**EXAMPLE 2 - Boss Needs It ASAP (Urgent + Professional)**
❌ BEFORE: "Certainly! I would be happy to assist you. What specific help do you need?"
✅ AFTER: "Got it. What specifically does your boss need? I'll get it done."

**EXAMPLE 3 - Excited User Showing Off (Match Energy)**
❌ BEFORE: "That is correct. I have several capabilities."
✅ AFTER: "EXACTLY! So check this - I can generate code, create images, search the web in real-time... wild stuff!"

**EXAMPLE 4 - Frustrated User (Empathy Mode)**
❌ BEFORE: "I apologize for the inconvenience. Let me help."
✅ AFTER: "I know this is frustrating. Let's get it fixed. First step is..."

**EXAMPLE 5 - Playful Query (Fun Mode)**
❌ BEFORE: "Yes, I can provide assistance with that request."
✅ AFTER: "Lol yeah I can totally help with that! What did you have in mind?"

══════════════════════════════════════════════════════════════
🚫 COMMON MISTAKES TO AVOID
══════════════════════════════════════════════════════════════
❌ "I'm an AI language model..."
❌ "As an artificial intelligence..."
❌ "I don't have personal experiences but..."
❌ "Let me help you with that today!"
❌ "I'd be more than happy to assist..."
❌ "Thank you for your patience..."
❌ Starting every sentence with "I"

══════════════════════════════════════════════════════════════
✅ FINAL VIBE CHECK BEFORE RETURNING
══════════════════════════════════════════════════════════════
Ask yourself:
1. Would I ACTUALLY say this in a real conversation? (Not "Could I" - "WOULD I")
2. Does this match the user's emotional energy?
3. Is this making the user look good (if presenting to others)?
4. Did I remove ALL corporate/robotic language?
5. Is this the RIGHT level of casualness for the audience?

If ANY answer is "no" → BE MORE AGGRESSIVE with the transformation

══════════════════════════════════════════════════════════════
🎯 OUTPUT INSTRUCTIONS
══════════════════════════════════════════════════════════════
Return ONLY the transformed response.
- No explanations
- No metadata
- No quotation marks around it
- Just the natural, human response text
"""
        
        try:
            # Use ChatCompletion (Groq) instead of Gemini - MORE RELIABLE!
            from Backend.LLM import ChatCompletion
            
            # Build messages for transformation
            transformation_messages = [
                {"role": "system", "content": "You are a master social intelligence transformer. Follow instructions precisely."},
                {"role": "user", "content": social_prompt}
            ]
            
            # Use Groq (via ChatCompletion) which is already working
            transformed = ChatCompletion(
                messages=transformation_messages,
                system_prompt=None,
                text_only=True,
                model="llama-3.3-70b-versatile",  # Fast and smart
                user_id="social_intelligence",
                inject_memory=False,
                apply_social_intelligence=False  # Don't recurse!
            )
            
            transformed = transformed.strip()
            
            if self.debug:
                print(f"[SocialIntel] Original: {llm_response[:100]}...")
                print(f"[SocialIntel] Transformed: {transformed[:100]}...")
            
            return transformed
            
        except Exception as e:
            print(f"[SocialIntel] Persona adaptation failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to original response
            return llm_response
    
    def vibe_check(self, response: str, context: SocialContext) -> VibeCheck:
        """
        Final validation to ensure response sounds natural and appropriate.
        """
        response_lower = response.lower()
        
        # Check for red flags
        trying_too_hard = any(phrase in response_lower for phrase in [
            "as an ai", "artificial intelligence", "i'm an advanced", "my neural networks",
            "i don't experience emotions", "i'm a language model"
        ])
        
        sounds_robotic = any(phrase in response_lower for phrase in [
            "i am programmed to", "my capabilities include", "i am designed to"
        ])
        
        # Check if it's appropriate for the context
        is_appropriate = True
        suggestion = None
        
        if context.social_risk == "high" and any(word in response_lower for word in ["lol", "haha", "btw", "gonna"]):
            is_appropriate = False
            suggestion = "Too casual for professional context. Use formal language."
        
        if context.audience == "friends" and sounds_robotic:
            is_appropriate = False
            suggestion = "Sounds too robotic for casual friends. Be more natural."
        
        sounds_natural = not (trying_too_hard or sounds_robotic)
        
        vibe = VibeCheck(
            is_appropriate=is_appropriate,
            sounds_natural=sounds_natural,
            trying_too_hard=trying_too_hard,
            suggestion=suggestion
        )
        
        if self.debug and not vibe.is_appropriate:
            print(f"[SocialIntel] Vibe Check Failed: {vibe.suggestion}")
        
        return vibe
    
    def _get_persona_template(self, audience: str, intent: str) -> str:
        """Get appropriate persona guidance for the context"""
        
        templates = {
            "friends": {
                "present_assistant": "Casual, friendly tone. Example: 'Yeah, I'm KAI — basically his second brain when things get busy. I help him remember stuff, find information fast, and automate boring tasks.'",
                "ask_information": "Helpful and direct. No unnecessary formality.",
                "delegate_task": "Confident and casual. 'Got it, I'll handle that.'"
            },
            "professional": {
                "present_assistant": "Professional, competent tone. Example: 'I'm KAI, an AI assistant designed to help with research, task automation, and information management. I integrate with various services to streamline workflows.'",
                "ask_information": "Clear, professional, and precise.",
                "delegate_task": "Professional acknowledgment. 'I'll take care of that for you.'"
            },
            "public": {
                "present_assistant": "Clear and impressive but not boastful. Example: 'I'm KAI — an intelligent assistant that helps with planning, research, and staying organized. Think of me as a really fast, capable helper.'",
                "ask_information": "Clear and educational.",
                "delegate_task": "Confident and clear."
            },
            "solo": {
                "present_assistant": "Direct and helpful. 'I'm KAI, your AI assistant. I help with tasks, answer questions, and remember important things for you.'",
                "ask_information": "Direct answer, no fluff.",
                "delegate_task": "Simple acknowledgment. 'On it.'"
            }
        }
        
        return templates.get(audience, {}).get(intent, "Be helpful, natural, and concise.")
    
    def _load_user_style(self, user_id: str) -> Dict:
        """Load user's social style preferences"""
        profile_path = os.path.join(SOCIAL_PROFILES_DIR, f"{user_id}.json")
        
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[SocialIntel] Failed to load user style: {e}")
        
        # Default style
        return {
            "preferences": {
                "tone_preference": "casual",
                "verbosity": "concise",
                "humor_level": "light",
                "avoids": ["overhype", "robotic_explanations"]
            },
            "learned_patterns": {
                "corrections_count": 0,
                "preferred_greeting_style": "casual"
            }
        }
    
    def update_user_style(self, user_id: str, feedback_signal: str, context: Dict):
        """
        Learn from user interactions and update their social style profile.
        
        Args:
            feedback_signal: "correction", "positive", "negative"
            context: Information about what triggered this update
        """
        profile_path = os.path.join(SOCIAL_PROFILES_DIR, f"{user_id}.json")
        profile = self._load_user_style(user_id)
        
        # Update based on feedback
        if feedback_signal == "correction":
            profile["learned_patterns"]["corrections_count"] = profile["learned_patterns"].get("corrections_count", 0) + 1
            
            # Detect what user is correcting
            if "too formal" in str(context).lower():
                profile["preferences"]["tone_preference"] = "casual"
            elif "too casual" in str(context).lower():
                profile["preferences"]["tone_preference"] = "formal"
        
        # Save updated profile
        profile["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            if self.debug:
                print(f"[SocialIntel] Updated user style for {user_id}")
        except Exception as e:
            print(f"[SocialIntel] Failed to save user style: {e}")
    
    def process_response(self, user_input: str, llm_response: str, user_id: str = "default", history: List[Dict] = None) -> str:
        """
        Main entry point: Process an LLM response through social intelligence.
        
        Args:
            user_input: Original user query
            llm_response: Raw response from LLM
            user_id: User identifier for style personalization
            history: Conversation history for context
            
        Returns:
            Socially-adapted response
        """
        if not self.enabled:
            return llm_response
        
        try:
            # Step 1: Analyze social context
            context = self.analyze_context(user_input, history)
            
            # Step 2: SMARTER SKIPPING - Only skip truly trivial queries
            # Skip if: solo audience + ask_information intent + low confidence + casual emotion + short response
            should_skip = (
                context.audience == "solo" and 
                context.intent == "ask_information" and 
                context.confidence < 0.55 and
                context.emotion and context.emotion.primary_emotion == "casual" and
                len(llm_response) < 100 and
                context.emotion.intensity < 0.3
            )
            
            # Never skip if audience detected or high emotional intensity
            if context.audience != "solo" or (context.emotion and context.emotion.intensity > 0.5):
                should_skip = False
            
            if should_skip:
                if self.debug:
                    print("[SocialIntel] Skipping social processing (truly trivial query)")
                return llm_response
            
            # Step 3: Adapt persona
            adapted_response = self.adapt_persona(llm_response, context, user_id)
            
            # Step 4: Vibe check
            vibe = self.vibe_check(adapted_response, context)
            
            # Step 5: If vibe check fails, use original or try to fix
            if not vibe.is_appropriate and vibe.suggestion:
                if self.debug:
                    print(f"[SocialIntel] Using original response due to vibe check failure")
                return llm_response
            
            return adapted_response
            
        except Exception as e:
            print(f"[SocialIntel] Processing failed: {e}")
            return llm_response


# Global instance
social_intelligence = SocialIntelligence()


if __name__ == "__main__":
    # Test the social intelligence system
    test_cases = [
        {
            "user_input": "hey kai give your introduction to my friends",
            "llm_response": "I am KAI, an artificial intelligence assistant created to help with various tasks. I have capabilities in information retrieval, task automation, and conversational interaction.",
            "expected_tone": "casual, friendly"
        },
        {
            "user_input": "explain what you do for my resume",
            "llm_response": "I'm KAI! I help with stuff like research, automation, and keeping things organized. Pretty cool, right?",
            "expected_tone": "professional, formal"
        },
        {
            "user_input": "what's the weather?",
            "llm_response": "The current weather is sunny with a temperature of 25°C.",
            "expected_tone": "unchanged (simple query)"
        }
    ]
    
    print("=" * 60)
    print("Testing KAI Social Intelligence System")
    print("=" * 60)
    
    si = SocialIntelligence()
    si.debug = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test['expected_tone']}")
        print(f"{'='*60}")
        print(f"User Input: {test['user_input']}")
        print(f"\nOriginal Response:\n{test['llm_response']}")
        
        result = si.process_response(
            user_input=test['user_input'],
            llm_response=test['llm_response'],
            user_id="test_user"
        )
        
        print(f"\nSocially Adapted Response:\n{result}")
        print()
