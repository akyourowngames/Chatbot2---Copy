#!/usr/bin/env python
"""Quick script to patch the detect_emotion method"""

import re

# Read the file
with open("Backend/SocialIntelligence.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find and replace the detect_emotion method (lines 102-178)
old_method_pattern = r'(    def detect_emotion\(self, user_input: str\) -> EmotionalContext:.*?        \))\r?\n'

new_method = '''    def detect_emotion(self, user_input: str) -> EmotionalContext:
        """ADVANCED emotion detection: sarcasm, mixed emotions, urgency scale, formality."""
        user_lower = user_input.lower()
        
        emotion_scores = {"excited": 0, "frustrated": 0, "urgent": 0, "playful": 0, "serious": 0, "casual": 0}
        
        # 🔥 SARCASM
        is_sarcastic = False
        for phrase, neg_words in [("oh great", ["problem", "error", "broke"]), ("just perfect", ["issue", "wrong"])]:
            if phrase in user_lower and any(w in user_lower for w in neg_words):
                is_sarcastic = True
                emotion_scores["frustrated"] += 4
                break
        
        # 🎯 INTRO FIX - THE BUG!
        is_intro = any(p in user_lower for p in ["intro", "introduce", "greet", "meet", "say hi", "my brother", "my friend"])
        if is_intro:
            emotion_scores["playful"] += 4
            emotion_scores["excited"] += 3
            emotion_scores["urgent"] = 0
        
        # Excited
        if ("!!!" in user_input or user_input.count("!") >= 2) and not is_intro:
            emotion_scores["excited"] += 3
        if any(w in user_lower for w in ["omg", "wow", "amazing", "awesome", "great", "sick"]):
            emotion_scores["excited"] += 2
        if user_input.isupper() and len(user_input) > 10:
            emotion_scores["excited"] += 3
        
        # Frustrated
        if any(w in user_lower for w in ["ugh", "annoyed", "frustrated", "broken", "fix", "damn"]):
            emotion_scores["frustrated"] += 3
        if any(w in user_lower for w in ["help!", "stuck", "can't"]):
            emotion_scores["frustrated"] += 2
        
        # 🚨 URGENCY 1-10
        urgency_level = 1
        urgency_map = {10: ["emergency"], 9: ["asap", "urgent"], 8: ["quickly", "hurry"], 7: ["soon"], 6: ["need this"]}
        if not is_intro:
            for level, kws in sorted(urgency_map.items(), reverse=True):
                if any(kw in user_lower for kw in kws):
                    urgency_level=level
                    emotion_scores["urgent"] += level // 2
                    break
        
        # Playful
        if any(w in user_lower for w in ["lol", "haha", "yo", "sup", "bro"]):
            emotion_scores["playful"] += 3
        
        # Serious
        if any(w in user_lower for w in ["important", "critical", "must"]):
            emotion_scores["serious"] += 2
        
        # Casual
        if max(emotion_scores.values()) == 0:
            emotion_scores["casual"] = 1
        
        # 🎭 FORMALITY
        formality_level = "neutral"
        if any(w in user_lower for w in ["i would appreciate", "if you could"]):
            formality_level = "very_formal"
        elif any(w in user_lower for w in ["please", "kindly"]):
            formality_level = "formal"
        elif any(w in user_lower for w in ["yo", "sup", "bro", "lol", "ur"]):
            formality_level = "casual"
        
        # PRIMARY + SECONDARY
        sorted_emo = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        primary_emotion = sorted_emo[0][0]
        secondary_emotions = [e[0] for e in sorted_emo[1:3] if e[1] >= 2]
        
        # Metrics
        max_score = emotion_scores[primary_emotion]
        intensity = min(max_score / 6.0, 1.0)
        energy_level = "high" if primary_emotion in ["excited", "urgent"] else "medium" if primary_emotion in ["frustrated", "playful"] else "low"
        needs_empathy = (primary_emotion in ["frustrated", "urgent"] and intensity > 0.5) or urgency_level >= 7
        
        return EmotionalContext(primary_emotion=primary_emotion, secondary_emotions=secondary_emotions,
                                intensity=intensity, energy_level=energy_level, needs_empathy=needs_empathy,
                                urgency_level=urgency_level, formality_level=formality_level, is_sarcastic=is_sarcastic)
'''

# Replace using regex
content_new = re.sub(old_method_pattern, new_method + "\r\n", content, count=1, flags=re.DOTALL)

# Write back
with open("Backend/SocialIntelligence.py", "w", encoding="utf-8") as f:
    f.write(content_new)

print("✓ Fixed detect_emotion method - intro requests no longer misclassified as urgent!")
