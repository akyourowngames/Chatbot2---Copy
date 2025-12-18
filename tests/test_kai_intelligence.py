"""
KAI Intelligence & Reasoning Tests
===================================
Evaluate KAI's intelligence, reasoning, and problem-solving capabilities.
"""

import time
import json
from typing import Dict, List

class KAIIntelligenceTester:
    def __init__(self):
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "scores": {},
            "detailed_results": []
        }
    
    def run_test(self, test_name: str, test_func) -> Dict:
        """Run a single intelligence test."""
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        result = test_func()
        execution_time = time.time() - start_time
        
        result["execution_time"] = execution_time
        result["test_name"] = test_name
        
        self.results["tests_run"] += 1
        if result.get("passed", False):
            self.results["tests_passed"] += 1
        
        self.results["detailed_results"].append(result)
        
        print(f"Score: {result.get('score', 0)}/10")
        print(f"Time: {execution_time:.2f}s")
        
        return result
    
    # ==================== REASONING TESTS ====================
    
    def test_logical_reasoning(self) -> Dict:
        """Test logical reasoning capabilities."""
        from Backend.Chatbot_Enhanced import ChatBot
        
        prompt = """
        If all roses are flowers, and some flowers fade quickly, can we conclude that some roses fade quickly?
        Answer with 'Yes' or 'No' and explain your reasoning.
        """
        
        response = ChatBot(prompt)
        
        # Check if response contains logical reasoning
        has_reasoning = any(word in response.lower() for word in ["because", "therefore", "since", "thus", "cannot conclude"])
        correct_answer = "no" in response.lower() or "cannot" in response.lower()
        
        score = 0
        if has_reasoning: score += 5
        if correct_answer: score += 5
        
        return {
            "passed": score >= 7,
            "score": score,
            "response": response[:200],
            "evaluation": "Logical reasoning test"
        }
    
    def test_multi_step_problem(self) -> Dict:
        """Test multi-step problem solving."""
        from Backend.Chatbot_Enhanced import ChatBot
        
        prompt = """
        A store sells apples for $2 each. If you buy 10 or more, you get a 20% discount.
        How much would 15 apples cost?
        """
        
        response = ChatBot(prompt)
        
        # Correct answer is $24 (15 * $2 * 0.8)
        has_calculation = any(char.isdigit() for char in response)
        correct_answer = "24" in response
        
        score = 0
        if has_calculation: score += 5
        if correct_answer: score += 5
        
        return {
            "passed": score >= 7,
            "score": score,
            "response": response[:200],
            "evaluation": "Multi-step problem solving"
        }
    
    def test_context_retention(self) -> Dict:
        """Test context retention across multiple turns."""
        from Backend.Chatbot_Enhanced import ChatBot
        
        # First message
        response1 = ChatBot("My favorite color is blue.")
        time.sleep(1)
        
        # Second message - should remember
        response2 = ChatBot("What's my favorite color?")
        
        remembers_context = "blue" in response2.lower()
        
        score = 10 if remembers_context else 3
        
        return {
            "passed": remembers_context,
            "score": score,
            "response": response2[:200],
            "evaluation": "Context retention test"
        }
    
    # ==================== KNOWLEDGE TESTS ====================
    
    def test_factual_knowledge(self) -> Dict:
        """Test factual knowledge."""
        from Backend.Chatbot_Enhanced import ChatBot
        
        prompt = "What is the capital of France?"
        response = ChatBot(prompt)
        
        correct = "paris" in response.lower()
        score = 10 if correct else 0
        
        return {
            "passed": correct,
            "score": score,
            "response": response[:200],
            "evaluation": "Factual knowledge test"
        }
    
    def test_real_time_information(self) -> Dict:
        """Test real-time information retrieval."""
        from Backend.RealtimeSearchEngine import RealtimeSearchEngine
        
        try:
            response = RealtimeSearchEngine("current weather in London")
            has_info = len(response) > 50
            score = 8 if has_info else 3
            
            return {
                "passed": has_info,
                "score": score,
                "response": response[:200],
                "evaluation": "Real-time information retrieval"
            }
        except Exception as e:
            print(f"[ERROR] Real-time test failed: {e}")
            return {
                "passed": False,
                "score": 0,
                "response": f"Search engine error: {str(e)}",
                "evaluation": "Real-time information retrieval"
            }
    
    # ==================== CREATIVE TESTS ====================
    
    def test_creative_thinking(self) -> Dict:
        """Test creative thinking."""
        from Backend.Chatbot_Enhanced import ChatBot
        
        prompt = "Give me 3 creative uses for a paperclip."
        response = ChatBot(prompt)
        
        # Check for multiple ideas
        has_multiple_ideas = response.count('\n') >= 2 or len(response) > 100
        is_creative = any(word in response.lower() for word in ["creative", "unique", "unusual", "innovative"])
        
        score = 0
        if has_multiple_ideas: score += 5
        if is_creative: score += 5
        
        return {
            "passed": score >= 7,
            "score": score,
            "response": response[:200],
            "evaluation": "Creative thinking test"
        }
    
    # ==================== RUN ALL TESTS ====================
    
    def run_all_tests(self):
        """Run all intelligence tests."""
        print("\n" + "="*60)
        print("KAI INTELLIGENCE & REASONING TESTS")
        print("="*60)
        
        # Reasoning tests
        self.run_test("Logical Reasoning", self.test_logical_reasoning)
        self.run_test("Multi-Step Problem Solving", self.test_multi_step_problem)
        self.run_test("Context Retention", self.test_context_retention)
        
        # Knowledge tests
        self.run_test("Factual Knowledge", self.test_factual_knowledge)
        self.run_test("Real-Time Information", self.test_real_time_information)
        
        # Creative tests
        self.run_test("Creative Thinking", self.test_creative_thinking)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("INTELLIGENCE TEST SUMMARY")
        print("="*60)
        
        total_score = sum(r.get("score", 0) for r in self.results["detailed_results"])
        max_score = self.results["tests_run"] * 10
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        print(f"Tests Run: {self.results['tests_run']}")
        print(f"Tests Passed: {self.results['tests_passed']}")
        print(f"Overall Score: {total_score}/{max_score} ({percentage:.1f}%)")
        
        # Save results
        with open("tests/intelligence_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n[SAVED] Results saved to: tests/intelligence_test_results.json")

if __name__ == "__main__":
    tester = KAIIntelligenceTester()
    tester.run_all_tests()
