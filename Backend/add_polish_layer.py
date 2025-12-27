#!/usr/bin/env python
"""Add the Polish layer - final refinement pass for ultra-natural responses"""

import re

# Read the file
with open("Backend/SocialIntelligence.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add the polish_response method before process_response
polish_method = '''
    def polish_response(self, response: str, context: SocialContext) -> str:
        """
        FINAL POLISH LAYER - Ultra-strict naturalness and flow optimization.
        Removes remaining corporate speak, unnecessary words, improves flow.
        """
        # Ultra-short prompt for FAST polishing
        polish_prompt = f"""You are a naturalness polish filter. Make this response sound MORE natural and conversational.

RESPONSE TO POLISH:
{response}

CONTEXT: {context.audience}, {context.emotion.primary_emotion if context.emotion else 'neutral'}

RULES:
1. Remove unnecessary filler words (totally, definitely, absolutely, actually)
2. Replace ANY remaining corporate speak with casual equivalents
3. Shorten if too wordy - get to the point faster
4. Ensure conversational flow
5. Keep it punchy and engaging

Return ONLY the polished response. No explanations."""

        try:
            from Backend.LLM import ChatCompletion
            
            polish_messages = [
                {"role": "system", "content": "You are a response polisher. Follow instructions precisely."},
                {"role": "user", "content": polish_prompt}
            ]
            
            polished = ChatCompletion(
                messages=polish_messages,
                text_only=True,
                model="llama-3.3-70b-versatile",
                user_id="polisher",
                inject_memory=False,
                apply_social_intelligence=False  # Don't recurse!
            )
            
            polished = polished.strip()
            
            if self.debug:
                print(f"[Polisher] Before: {response[:80]}...")
                print(f"[Polisher] After: {polished[:80]}...")
            
            return polished
            
        except Exception as e:
            print(f"[Polisher] Failed: {e}")
            return response  # Fallback to unpolished
'''

# Find where to insert (before process_response method)
insert_marker = "    def process_response(self, user_input: str, llm_response: str"
insert_pos = content.find(insert_marker)

if insert_pos != -1:
    # Insert the polish method
    content_new = content[:insert_pos] + polish_method + "\n" + content[insert_pos:]
    
    # Now update process_response to use the polisher
    # Find the line where it returns the adapted response
    # Look for: return adapted_response (should be near the end of process_response)
    
    # Pattern: adapt_persona call followed by return
    old_flow = "adapted_response = self.adapt_persona(llm_response, context, user_id)"
    new_flow = """adapted_response = self.adapt_persona(llm_response, context, user_id)
            
            # 🔥 POLISH LAYER - Final ultra-refinement (NEW!)
            if self.enabled:
                adapted_response = self.polish_response(adapted_response, context)"""
    
    content_new = content_new.replace(old_flow, new_flow, 1)
    
    # Write back
    with open("Backend/SocialIntelligence.py", "w", encoding="utf-8") as f:
        f.write(content_new)
    
    print("✓ Added Polish Layer - responses will be ultra-natural now!")
    print("✓ Flow: Raw → Social Intelligence → Polish → Return")
else:
    print("✗ Could not find insertion point")
