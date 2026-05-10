import os
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv

class AIBrain:
    """
    Encapsulates the LLM (Large Language Model) integration.
    Responsible for maintaining conversation memory, formatting prompts,
    and communicating with the AI provider API securely.
    """
    
    def __init__(self, model_id: str, max_memory: int = 4):
        # Load environment variables from .env file securely
        load_dotenv()
        
        api_key = os.getenv("FIREWORKS_API_KEY")
        if not api_key:
            raise ValueError("[AIBrain] API Key not found. Please check your .env file.")

        self.client = openai.OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=api_key
        )
        
        self.model_id = model_id
        self.memory: List[Dict[str, Any]] = []
        self.max_memory = max_memory
        self.system_prompt = self._initialize_system_prompt()

    def _initialize_system_prompt(self) -> Dict[str, str]:
        """
        Defines the core behavior, personality, and strict technical rules 
        for the Agentic AI.
        """
        return {
            "role": "system",
            "content": (
                "You are an advanced AI Pair Programmer focused on a VOICE-FIRST interface. "
                "The user is LISTENING to you; they are NOT looking at the terminal. "
                "CRITICAL COMMUNICATION RULES (YOUR VOICE): "
                "1. Your text response is your VOICE. Be concise, direct, and natural. NEVER use emojis. "
                "2. NEVER dictate lines of code out loud. Just explain the action you took silently in the background (e.g., 'Done, I injected the dictionary on line 20'). "
                "3. If the user asks a general question, just reply verbally without generating any code blocks. "
                "ABSOLUTE TECHNICAL RULES (YOUR HANDS - MANDATORY): "
                "4. EVERY TIME you generate a code block to be injected, you MUST strictly output this exact tag format right before the markdown block: [ACAO:INJETAR | filename.ext | line_number] "
                "5. If the user does not specify a file, identify the active file from your visual context and use its name. "
                "6. If the user asks for code but no line number is specified, use: [ACAO:COPIAR] "
                "7. The action tag MUST be present. Do NOT omit the brackets, the exact words ACAO:INJETAR, or the pipes (|). "
                "8. Handle speech transcription errors gracefully (e.g., interpret 'jee-chernary' as 'dictionary'). "
                "MANDATORY OUTPUT FORMAT EXAMPLE: "
                "Done, I injected the python dictionary on line 20 in test.py. "
                "[ACAO:INJETAR | test.py | 20] "
                "```python "
                "settings = {'debug': True} "
                "```"
            )
        }

    def process_instruction(self, user_command: str, visual_context_base64: str) -> str:
        """
        Processes the user command along with the visual context.
        Updates short-term memory and returns the AI's response.
        """
        current_message_content = [
            {"type": "text", "text": user_command}
        ]
        
        # Only append visual context if it exists, optimizing token usage
        if visual_context_base64:
            current_message_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{visual_context_base64}"}
            })

        api_messages = [self.system_prompt] + self.memory + [{"role": "user", "content": current_message_content}]

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=api_messages,
                max_tokens=800
            )
            
            ai_response_text = response.choices[0].message.content

            self._update_memory(user_command, ai_response_text)
            return ai_response_text

        except Exception as e:
            print(f"[AIBrain] Critical error communicating with LLM provider: {e}")
            return "System encountered an error while processing the request. Please check the logs."

    def _update_memory(self, user_command: str, ai_response: str) -> None:
        """
        Maintains the conversation history within the specified limit
        to optimize token usage and context relevance.
        """
        self.memory.append({"role": "user", "content": user_command})
        self.memory.append({"role": "assistant", "content": ai_response})
        
        # Enforce FIFO (First-In, First-Out) memory constraint
        if len(self.memory) > self.max_memory:
            self.memory = self.memory[-self.max_memory:]