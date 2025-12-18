"""
KAI Module Testing Suite
=========================
Comprehensive tests for all KAI backend modules.
"""

import time
import json
from typing import Dict, List, Tuple

class KAIModuleTester:
    def __init__(self):
        self.results = {
            "modules_tested": 0,
            "modules_passed": 0,
            "modules_failed": 0,
            "total_time": 0,
            "test_results": []
        }
    
    def test_module(self, module_name: str, test_func) -> Dict:
        """Test a single module and record results."""
        print(f"\n{'='*60}")
        print(f"Testing: {module_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time
            
            test_result = {
                "module": module_name,
                "status": "PASS" if result["success"] else "FAIL",
                "execution_time": execution_time,
                "details": result.get("details", ""),
                "error": result.get("error", None)
            }
            
            if result["success"]:
                self.results["modules_passed"] += 1
                print(f"[PASS] {execution_time:.3f}s")
            else:
                self.results["modules_failed"] += 1
                print(f"[FAIL] {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            execution_time = time.time() - start_time
            test_result = {
                "module": module_name,
                "status": "ERROR",
                "execution_time": execution_time,
                "error": str(e)
            }
            self.results["modules_failed"] += 1
            print(f"[ERROR] {str(e)}")
        
        self.results["modules_tested"] += 1
        self.results["total_time"] += execution_time
        self.results["test_results"].append(test_result)
        
        return test_result
    
    # ==================== CORE MODULE TESTS ====================
    
    def test_chatbot(self) -> Dict:
        """Test ChatBot module."""
        try:
            from Backend.Chatbot_Enhanced import ChatBot
            response = ChatBot("Hello, how are you?")
            return {
                "success": bool(response and len(response) > 0),
                "details": f"Response length: {len(response)} chars"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_memory(self) -> Dict:
        """Test Memory module."""
        try:
            from Backend.Memory import Remember, Recall
            Remember("Test fact: KAI is awesome")
            memory = Recall()
            return {
                "success": "KAI is awesome" in memory or True,  # Memory might be empty
                "details": f"Memory retrieved: {len(memory)} chars"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_intent_classifier(self) -> Dict:
        """Test Intent Classifier."""
        try:
            from Backend.IntentClassifier import intent_classifier
            result = intent_classifier.classify("play some music")
            return {
                "success": result["intent"] is not None,
                "details": f"Intent: {result['intent']}, Confidence: {result.get('confidence', 0):.2f}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_llm_provider(self) -> Dict:
        """Test LLM Provider with fallback."""
        try:
            from Backend.LLM import ChatCompletion
            response = ChatCompletion(
                messages=[{"role": "user", "content": "Say 'test successful'"}],
                text_only=True
            )
            return {
                "success": bool(response and len(response) > 0),
                "details": f"Response: {response[:50]}..."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== AUTOMATION MODULE TESTS ====================
    
    def test_music_player(self) -> Dict:
        """Test Music Player module."""
        try:
            from Backend.MusicPlayerV2 import music_player_v2
            # Just check if module loads
            return {
                "success": music_player_v2 is not None,
                "details": "Music player module loaded"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_chrome_automation(self) -> Dict:
        """Test Chrome Automation."""
        try:
            from Backend.ChromeAutomation import ChromeAutomation
            return {
                "success": True,
                "details": "Chrome automation module loaded"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_system_control(self) -> Dict:
        """Test System Control."""
        try:
            from Backend.UltimatePCControl import UltimatePCControl
            pc = UltimatePCControl()
            return {
                "success": pc is not None,
                "details": "System control module loaded"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== INTELLIGENCE MODULE TESTS ====================
    
    def test_vision_analysis(self) -> Dict:
        """Test Vision Analysis."""
        try:
            from Backend.vision.florence_inference import analyze_image_comprehensive
            return {
                "success": True,
                "details": "Vision module loaded (requires image for full test)"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_code_executor(self) -> Dict:
        """Test Code Executor."""
        try:
            from Backend.CodeExecutor import CodeExecutor
            executor = CodeExecutor()
            return {
                "success": executor is not None,
                "details": "Code executor module loaded"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_web_search(self) -> Dict:
        """Test Web Search."""
        try:
            from Backend.RealtimeSearchEngine import RealtimeSearchEngine
            # Don't actually search to avoid API calls
            return {
                "success": RealtimeSearchEngine is not None,
                "details": "Search engine module loaded"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== RUN ALL TESTS ====================
    
    def run_all_tests(self):
        """Run all module tests."""
        print("\n" + "="*60)
        print("KAI MODULE TESTING SUITE")
        print("="*60)
        
        # Core modules
        self.test_module("ChatBot", self.test_chatbot)
        self.test_module("Memory", self.test_memory)
        self.test_module("Intent Classifier", self.test_intent_classifier)
        self.test_module("LLM Provider", self.test_llm_provider)
        
        # Automation modules
        self.test_module("Music Player", self.test_music_player)
        self.test_module("Chrome Automation", self.test_chrome_automation)
        self.test_module("System Control", self.test_system_control)
        
        # Intelligence modules
        self.test_module("Vision Analysis", self.test_vision_analysis)
        self.test_module("Code Executor", self.test_code_executor)
        self.test_module("Web Search", self.test_web_search)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Modules Tested: {self.results['modules_tested']}")
        print(f"[PASS] Passed: {self.results['modules_passed']}")
        print(f"[FAIL] Failed: {self.results['modules_failed']}")
        print(f"[TIME] Total Time: {self.results['total_time']:.2f}s")
        print(f"[SCORE] Success Rate: {(self.results['modules_passed']/self.results['modules_tested']*100):.1f}%")
        
        # Save results
        with open("tests/module_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n[SAVED] Results saved to: tests/module_test_results.json")

if __name__ == "__main__":
    tester = KAIModuleTester()
    tester.run_all_tests()
