"""
AI Job Interviewer - Practice Interviews & Get Scored
======================================================
Realistic job interview practice with feedback and scoring.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIJobInterviewer:
    """
    Conduct realistic job interviews for any role.
    Ask questions, evaluate answers, provide feedback.
    """
    
    def __init__(self):
        self._llm = None
        self.sessions = {}  # Active interview sessions
        self.user_history = {}  # Performance history per user
        self.industry_templates = self._load_industry_templates()
        logger.info("[INTERVIEW] AI Job Interviewer initialized with templates")
    
    @property
    def llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            try:
                from Backend.LLM import ChatCompletion
                self._llm = ChatCompletion
            except Exception as e:
                logger.error(f"[INTERVIEW] LLM load failed: {e}")
        return self._llm
    
    def start_interview(self, job_role: str, company: str = "a top tech company",
                       experience_level: str = "mid", difficulty: str = "medium",
                       industry: str = None, user_id: str = "default") -> Dict[str, Any]:
        """
        Start a new interview session.
        
        Args:
            job_role: The job you're interviewing for
            company: Company name (for context)
            experience_level: junior/mid/senior
            difficulty: easy/medium/hard/expert
            industry: Optional industry template (tech/finance/healthcare/etc.)
            user_id: Session identifier
            
        Returns:
            Session info and first question
        """
        if not self.llm:
            return {"status": "error", "message": "LLM not available"}
        
        logger.info(f"[INTERVIEW] Starting interview for {job_role} at {company}")
        
        # Load template if industry specified
        template_questions = []
        if industry and industry in self.industry_templates:
            template_questions = self.industry_templates[industry].get("questions", [])
            logger.info(f"[INTERVIEW] Loaded {industry} template")
        
        # Generate interview questions for this role
        questions = template_questions if template_questions else self._generate_questions(job_role, experience_level, difficulty)
        
        # Create session
        session = {
            "job_role": job_role,
            "company": company,
            "experience_level": experience_level,
            "difficulty": difficulty,
            "industry": industry,
            "questions": questions,
            "current_question": 0,
            "answers": [],
            "scores": [],
            "hints_used": 0,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        self.sessions[user_id] = session
        
        # Get first question
        first_question = questions[0] if questions else "Tell me about yourself."
        
        return {
            "status": "success",
            "message": f"🎯 Interview started for {job_role} at {company}",
            "total_questions": len(questions),
            "current_question": 1,
            "question": first_question,
            "tip": "Answer as if you're in a real interview. Be specific and give examples!"
        }
    
    def _generate_questions(self, job_role: str, level: str, difficulty: str = "medium") -> List[str]:
        """Generate interview questions for the role."""
        
        difficulty_context = {
            "easy": "straightforward, common",
            "medium": "moderately challenging",
            "hard": "challenging, in-depth",
            "expert": "extremely difficult, expert-level"
        }.get(difficulty, "moderately challenging")
        
        prompt = f"""Generate 5 {difficulty_context} interview questions for a {level}-level {job_role} position.
Mix of:
- 1 behavioral question (tell me about a time...)
- 2 technical/skill questions specific to {job_role}
- 1 situational question (what would you do if...)
- 1 motivation question (why this role/company)

Return ONLY the questions, numbered 1-5, one per line."""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            inject_memory=False
        )
        
        # Parse questions
        questions = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering
                q = line.lstrip("0123456789.-) ").strip()
                if q:
                    questions.append(q)
        
        # Fallback questions if parsing failed
        if len(questions) < 3:
            questions = [
                "Tell me about yourself and your experience.",
                f"What skills make you a good fit for {job_role}?",
                "Tell me about a challenging project you worked on.",
                "Where do you see yourself in 5 years?",
                "Why are you interested in this role?"
            ]
        
        return questions[:5]
    
    def answer_question(self, answer: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Submit an answer and get feedback.
        
        Args:
            answer: User's answer to the current question
            user_id: Session identifier
            
        Returns:
            Feedback and next question (or final results)
        """
        if user_id not in self.sessions:
            return {"status": "error", "message": "No active interview. Start one first!"}
        
        session = self.sessions[user_id]
        
        if session["status"] != "in_progress":
            return {"status": "error", "message": "Interview already completed."}
        
        current_q = session["current_question"]
        question = session["questions"][current_q]
        
        # Evaluate the answer
        evaluation = self._evaluate_answer(question, answer, session["job_role"])
        
        # Store answer and score
        session["answers"].append({
            "question": question,
            "answer": answer,
            "score": evaluation["score"],
            "feedback": evaluation["feedback"]
        })
        session["scores"].append(evaluation["score"])
        
        # Move to next question
        session["current_question"] += 1
        
        # Check if interview is complete
        if session["current_question"] >= len(session["questions"]):
            session["status"] = "completed"
            return self._generate_final_report(user_id)
        
        # Return feedback and next question
        next_question = session["questions"][session["current_question"]]
        
        return {
            "status": "success",
            "question_number": current_q + 1,
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "improvement": evaluation["improvement"],
            "next_question": {
                "number": session["current_question"] + 1,
                "total": len(session["questions"]),
                "question": next_question
            }
        }
    
    def _evaluate_answer(self, question: str, answer: str, job_role: str) -> Dict[str, Any]:
        """Evaluate an interview answer."""
        prompt = f"""You are an expert interviewer evaluating a candidate for {job_role}.

QUESTION: {question}

CANDIDATE'S ANSWER:
{answer}

Evaluate this answer:
1. SCORE: Give a score 1-10 (10 = excellent)
2. FEEDBACK: What was good about this answer? (1-2 sentences)
3. IMPROVEMENT: How could they improve? (1-2 sentences)

Format your response exactly like this:
SCORE: [number]
FEEDBACK: [text]
IMPROVEMENT: [text]"""

        response = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            inject_memory=False
        )
        
        # Parse response
        score = 5
        feedback = "Good attempt."
        improvement = "Try to be more specific."
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if line.upper().startswith("SCORE:"):
                try:
                    score_text = line.split(":", 1)[-1].strip()
                    score = int(''.join(filter(str.isdigit, score_text[:3])))
                    score = max(1, min(10, score))
                except:
                    score = 5
            elif line.upper().startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("IMPROVEMENT:"):
                improvement = line.split(":", 1)[-1].strip()
        
        return {
            "score": score,
            "feedback": feedback,
            "improvement": improvement
        }
    
    def _generate_final_report(self, user_id: str) -> Dict[str, Any]:
        """Generate final interview report."""
        session = self.sessions[user_id]
        
        avg_score = sum(session["scores"]) / len(session["scores"])
        
        # Determine verdict
        if avg_score >= 8:
            verdict = "🎉 EXCELLENT! You would likely get the job!"
            grade = "A"
        elif avg_score >= 6:
            verdict = "👍 GOOD! You're a strong candidate."
            grade = "B"
        elif avg_score >= 4:
            verdict = "📝 FAIR. Some areas need improvement."
            grade = "C"
        else:
            verdict = "📚 NEEDS WORK. Practice more before the real interview."
            grade = "D"
        
        # Generate detailed report
        report_prompt = f"""Generate a brief interview performance summary.

Job Role: {session['job_role']}
Average Score: {avg_score:.1f}/10
Grade: {grade}

Questions and Scores:
{chr(10).join(f"Q{i+1}: {a['score']}/10" for i, a in enumerate(session['answers']))}

Write 3-4 sentences summarizing their performance, strengths, and areas to improve."""

        summary = self.llm(
            messages=[{"role": "user", "content": report_prompt}],
            model="llama-3.1-8b-instant",
            inject_memory=False
        )
        
        return {
            "status": "completed",
            "message": "🎯 Interview Complete!",
            "job_role": session["job_role"],
            "company": session["company"],
            "total_questions": len(session["questions"]),
            "average_score": round(avg_score, 1),
            "grade": grade,
            "verdict": verdict,
            "summary": summary.strip(),
            "detailed_results": session["answers"],
            "tips": self._get_tips(avg_score, session["job_role"])
        }
    
    def _get_tips(self, score: float, role: str) -> List[str]:
        """Get personalized tips based on performance."""
        tips = []
        
        if score < 5:
            tips.extend([
                "Practice the STAR method for behavioral questions",
                "Research common questions for your role",
                "Prepare specific examples from past experience"
            ])
        elif score < 7:
            tips.extend([
                "Add more specific metrics and results to your answers",
                "Practice explaining technical concepts simply",
                "Prepare questions to ask the interviewer"
            ])
        else:
            tips.extend([
                "Great job! Keep practicing to stay sharp",
                "Consider mock interviews with harder questions",
                "Work on salary negotiation skills"
            ])
        
        return tips
    
    def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current interview session."""
        return self.sessions.get(user_id)
    
    def quick_question(self, job_role: str) -> Dict[str, Any]:
        """Get a quick random interview question for practice."""
        questions = self._generate_questions(job_role, "mid")
        question = random.choice(questions)
        
        return {
            "status": "success",
            "job_role": job_role,
            "question": question,
            "tip": "Practice answering out loud for best results!"
        }
    
    def _load_industry_templates(self) -> Dict[str, Dict]:
        """Load industry-specific question templates."""
        return {
            "tech": {
                "name": "Technology",
                "questions": [
                    "Describe your experience with agile development methodologies.",
                    "How do you approach debugging a complex system?",
                    "Tell me about a time you optimized system performance.",
                    "How do you stay updated with new technologies?",
                    "Explain a situation where you had to make a trade-off between code quality and delivery speed."
                ]
            },
            "finance": {
                "name": "Finance",
                "questions": [
                    "How do you assess financial risk in investment decisions?",
                    "Describe your experience with financial modeling.",
                    "How would you explain a complex financial concept to a non-finance stakeholder?",
                    "Tell me about a time you identified a critical error in financial data.",
                    "How do you prioritize competing deadlines during quarter-end close?"
                ]
            },
            "healthcare": {
                "name": "Healthcare",
                "questions": [
                    "How do you handle patient confidentiality in your work?",
                    "Describe a difficult situation with a patient or family member.",
                    "How do you stay current with medical best practices?",
                    "Tell me about a time you had to make a critical decision under pressure.",
                    "How do you approach interdisciplinary collaboration?"
                ]
            },
            "marketing": {
                "name": "Marketing",
                "questions": [
                    "How do you measure the success of a marketing campaign?",
                    "Describe your approach to understanding target audiences.",
                    "Tell me about a campaign that didn't perform well and what you learned.",
                    "How do you balance creativity with data-driven decision making?",
                    "What's your experience with digital marketing tools and platforms?"
                ]
            }
        }
    
    def load_custom_questions(self, questions: List[str], user_id: str = "default"):
        """Load custom questions for current session."""
        if user_id in self.sessions:
            self.sessions[user_id]["questions"] = questions
            self.sessions[user_id]["current_question"] = 0
            logger.info(f"[INTERVIEW] Loaded {len(questions)} custom questions")
    
    def get_hint(self, user_id: str = "default") -> Dict[str, Any]:
        """Provide a hint for the current question."""
        if user_id not in self.sessions:
            return {"status": "error", "message": "No active interview"}
        
        session = self.sessions[user_id]
        current_q = session["current_question"]
        question = session["questions"][current_q]
        
        if not self.llm:
            return {"status": "error", "message": "LLM not available"}
        
        prompt = f"""Provide a helpful hint for answering this interview question.
Don't give the full answer, just guide them in the right direction.

QUESTION: {question}

Hint (2-3 sentences):"""
        
        hint = self.llm(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            inject_memory=False
        )
        
        session["hints_used"] += 1
        
        return {
            "status": "success",
            "hint": hint.strip(),
            "hints_used_total": session["hints_used"]
        }
    
    def get_analytics(self, user_id: str = "default") -> Dict[str, Any]:
        """Get performance analytics for a user."""
        if user_id not in self.user_history:
            return {"status": "error", "message": "No interview history found"}
        
        history = self.user_history[user_id]
        
        scores = [s["average_score"] for s in history]
        avg_overall = sum(scores) / len(scores) if scores else 0
        
        return {
            "status": "success",
            "user_id": user_id,
            "total_interviews": len(history),
            "average_score": round(avg_overall, 1),
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0,
            "improvement_trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable",
            "recent_interviews": history[-3:]
        }
    
    def get_industry_templates(self) -> List[Dict[str, str]]:
        """Get list of available industry templates."""
        return [
            {"id": key, "name": val["name"], "question_count": len(val["questions"])}
            for key, val in self.industry_templates.items()
        ]


# Global instance
job_interviewer = AIJobInterviewer()


# Convenience functions
def start_interview(job_role: str, company: str = "a top company") -> Dict[str, Any]:
    """Start an interview session."""
    return job_interviewer.start_interview(job_role, company)


def answer(response: str, user_id: str = "default") -> Dict[str, Any]:
    """Answer the current question."""
    return job_interviewer.answer_question(response, user_id)


if __name__ == "__main__":
    # Test
    result = job_interviewer.start_interview("Software Engineer", "Google")
    print(result)
