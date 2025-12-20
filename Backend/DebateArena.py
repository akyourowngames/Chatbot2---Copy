"""
AI Debate Arena - Watch Two AIs Argue Any Topic
=================================================
Spawn two AI agents that debate opposite sides of any topic.
Learn both perspectives, get a final verdict.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIDebateArena:
    """
    Create debates between two AI agents on any topic.
    Each agent argues for their assigned side.
    """
    
    def __init__(self):
        self._llm = None
        logger.info("[DEBATE] AI Debate Arena initialized")
    
    @property
    def llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from Backend.LLM import ChatCompletion
                self._llm = ChatCompletion
            except Exception as e:
                logger.error(f"[DEBATE] LLM load failed: {e}")
        return self._llm
    
    def start_debate(self, topic: str, rounds: int = 3) -> Dict[str, Any]:
        """
        Start a debate on any topic.
        
        Args:
            topic: The debate topic (e.g., "Is AI good for humanity?")
            rounds: Number of debate rounds (default 3)
            
        Returns:
            Complete debate transcript with verdict
        """
        if not self.llm:
            return {"status": "error", "message": "LLM not available"}
        
        logger.info(f"[DEBATE] Starting: {topic}")
        
        # Determine the two sides
        sides = self._analyze_topic(topic)
        pro_side = sides.get("pro", "In favor")
        con_side = sides.get("con", "Against")
        
        debate_log = []
        pro_arguments = []
        con_arguments = []
        
        # Opening statements
        print(f"\n🎭 DEBATE ARENA: {topic}\n")
        print(f"🔵 PRO: {pro_side}")
        print(f"🔴 CON: {con_side}\n")
        
        # Run debate rounds
        for round_num in range(1, rounds + 1):
            print(f"--- ROUND {round_num} ---\n")
            
            # PRO argument
            pro_context = "\n".join(con_arguments[-2:]) if con_arguments else ""
            pro_arg = self._generate_argument(
                topic, pro_side, "PRO", round_num, pro_context, pro_arguments
            )
            pro_arguments.append(pro_arg)
            debate_log.append({
                "round": round_num,
                "side": "PRO",
                "position": pro_side,
                "argument": pro_arg
            })
            print(f"🔵 PRO: {pro_arg}\n")
            
            # CON argument (responding to PRO)
            con_arg = self._generate_argument(
                topic, con_side, "CON", round_num, pro_arg, con_arguments
            )
            con_arguments.append(con_arg)
            debate_log.append({
                "round": round_num,
                "side": "CON",
                "position": con_side,
                "argument": con_arg
            })
            print(f"🔴 CON: {con_arg}\n")
        
        # Final verdict
        verdict = self._generate_verdict(topic, pro_side, con_side, debate_log)
        
        return {
            "status": "success",
            "topic": topic,
            "pro_position": pro_side,
            "con_position": con_side,
            "rounds": rounds,
            "debate_log": debate_log,
            "verdict": verdict,
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_topic(self, topic: str) -> Dict[str, str]:
        """Determine the two sides of a debate topic."""
        prompt = f"""Analyze this debate topic and identify the two opposing sides.

TOPIC: {topic}

Reply in this exact format:
PRO: [position that supports/agrees]
CON: [position that opposes/disagrees]

Keep each position to 5-10 words."""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            inject_memory=False
        )
        
        lines = response.strip().split('\n')
        pro = "In favor of the topic"
        con = "Against the topic"
        
        for line in lines:
            if line.upper().startswith("PRO:"):
                pro = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("CON:"):
                con = line.split(":", 1)[-1].strip()
        
        return {"pro": pro, "con": con}
    
    def _generate_argument(self, topic: str, position: str, side: str, 
                          round_num: int, opponent_arg: str, 
                          previous_args: List[str]) -> str:
        """Generate a debate argument."""
        
        prev_context = ""
        if previous_args:
            prev_context = f"\nYour previous arguments: {'; '.join(previous_args[-2:])}"
        
        opponent_context = ""
        if opponent_arg:
            opponent_context = f"\nOpponent's last argument: {opponent_arg}\nCounter their points while making your case."
        
        prompt = f"""You are a {side} debater arguing: {position}

TOPIC: {topic}
ROUND: {round_num}/3
{prev_context}
{opponent_context}

Rules:
1. Make ONE strong argument (2-3 sentences)
2. Use facts, logic, or emotional appeal
3. Be persuasive but respectful
4. Don't repeat previous arguments

Your {side} argument:"""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            inject_memory=False
        )
        
        return response.strip()
    
    def _generate_verdict(self, topic: str, pro_side: str, con_side: str,
                         debate_log: List[Dict]) -> Dict[str, Any]:
        """Generate a final verdict analyzing both sides."""
        
        # Compile debate summary
        debate_summary = ""
        for entry in debate_log:
            debate_summary += f"\n{entry['side']}: {entry['argument']}"
        
        prompt = f"""You are a neutral judge analyzing this debate.

TOPIC: {topic}
PRO POSITION: {pro_side}
CON POSITION: {con_side}

DEBATE TRANSCRIPT:
{debate_summary}

Provide your verdict:
1. WINNER: Which side argued more effectively? (PRO or CON or DRAW)
2. PRO STRENGTHS: Best arguments from the PRO side
3. CON STRENGTHS: Best arguments from the CON side
4. WEAKNESSES: Where each side could improve
5. FINAL THOUGHTS: What viewers should take away from this debate

Be fair and objective."""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            inject_memory=False
        )
        
        # Determine winner
        response_upper = response.upper()
        if "WINNER: PRO" in response_upper or "PRO WINS" in response_upper:
            winner = "PRO"
        elif "WINNER: CON" in response_upper or "CON WINS" in response_upper:
            winner = "CON"
        else:
            winner = "DRAW"
        
        return {
            "winner": winner,
            "analysis": response.strip()
        }
    
    def quick_debate(self, topic: str) -> str:
        """Get a quick 1-round debate summary."""
        result = self.start_debate(topic, rounds=1)
        
        if result.get("status") != "success":
            return f"Debate failed: {result.get('message')}"
        
        output = f"""🎭 DEBATE: {topic}

🔵 PRO ({result['pro_position']}):
{result['debate_log'][0]['argument']}

🔴 CON ({result['con_position']}):
{result['debate_log'][1]['argument']}

🏆 VERDICT: {result['verdict']['winner']}
{result['verdict']['analysis'][:500]}..."""
        
        return output


# Global instance
debate_arena = AIDebateArena()


# Convenience function
def debate(topic: str, rounds: int = 3) -> Dict[str, Any]:
    """Start a debate on any topic."""
    return debate_arena.start_debate(topic, rounds)


if __name__ == "__main__":
    # Test
    result = debate_arena.quick_debate("Should social media be banned for kids under 16?")
    print(result)
