"""
AI Assistant Test Pipeline - Load and Use Trained Model
=======================================================

This script loads your fine-tuned DistilGPT2 model and creates a text generation pipeline
for your AI assistant.

USAGE:
1. Make sure you have trained your model using train_assistant.py
2. Run this script to test your trained assistant
3. The model should be in ./distilgpt2_assistant/

REQUIREMENTS:
- transformers
- torch
- Your trained model in ./distilgpt2_assistant/
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssistantInference:
    """
    AI Assistant Inference Pipeline
    Loads trained model and generates responses
    """
    
    def __init__(self, model_path: str = "./gpt2_assistant"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.generator = None
        
        logger.info(f"Initialized AssistantInference with model path: {model_path}")
    
    def load_trained_model(self):
        """
        Load the fine-tuned model and tokenizer
        """
        logger.info("Loading trained model and tokenizer...")
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Load model
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            
            # Set model to evaluation mode
            self.model.eval()
            
            logger.info("✅ Trained model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading trained model: {e}")
            raise
    
    def create_generation_pipeline(self):
        """
        Create a text generation pipeline
        """
        logger.info("Creating text generation pipeline...")
        
        try:
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,  # CPU only
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info("✅ Text generation pipeline created")
            
        except Exception as e:
            logger.error(f"❌ Error creating pipeline: {e}")
            raise
    
    def generate_response(self, user_prompt: str) -> str:
        """
        Generate assistant response to user prompt
        """
        try:
            # Format the prompt
            formatted_prompt = f"Human: {user_prompt}\nAssistant:"
            
            # Generate response
            generated = self.generator(
                formatted_prompt,
                max_length=len(formatted_prompt.split()) + 50,  # Add some length
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the response
            full_text = generated[0]['generated_text']
            response = full_text.split("Assistant:")[-1].strip()
            
            # Clean up the response
            response = response.replace("Human:", "").strip()
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return "I'm sorry, I couldn't generate a response right now."
    
    def chat_with_assistant(self):
        """
        Interactive chat with the assistant
        """
        logger.info("🤖 Starting interactive chat with your trained assistant!")
        logger.info("Type 'quit' to exit")
        logger.info("=" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    logger.info("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Generate response
                logger.info("🤔 Thinking...")
                response = self.generate_response(user_input)
                
                # Display response
                print(f"Assistant: {response}")
                
            except KeyboardInterrupt:
                logger.info("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error in chat: {e}")
                print("I'm sorry, something went wrong. Please try again.")

def test_assistant():
    """
    Test the trained assistant with sample prompts
    """
    logger.info("🧪 Testing trained assistant...")
    
    try:
        # Initialize assistant
        assistant = AssistantInference()
        
        # Load model
        assistant.load_trained_model()
        
        # Create pipeline
        assistant.create_generation_pipeline()
        
        # Test prompts
        test_prompts = [
            "Hello, how are you?",
            "What's the weather like today?",
            "Tell me a joke",
            "What's your favorite color?",
            "How can I help you today?"
        ]
        
        logger.info("📝 Running test prompts...")
        print("\n" + "=" * 50)
        print("TESTING YOUR TRAINED ASSISTANT")
        print("=" * 50)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\nTest {i}:")
            print(f"Human: {prompt}")
            
            response = assistant.generate_response(prompt)
            print(f"Assistant: {response}")
        
        print("\n" + "=" * 50)
        print("✅ Testing completed!")
        
        # Ask if user wants to chat
        while True:
            choice = input("\nWould you like to chat with your assistant? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                assistant.chat_with_assistant()
                break
            elif choice in ['n', 'no']:
                logger.info("👋 Goodbye!")
                break
            else:
                print("Please enter 'y' or 'n'")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

def main():
    """
    Main function to run the assistant test
    """
    logger.info("🤖 AI Assistant Test Pipeline")
    logger.info("=" * 50)
    
    try:
        test_assistant()
        
    except Exception as e:
        logger.error(f"❌ Assistant test failed: {e}")
        raise

if __name__ == "__main__":
    main()
