import sys
import os
import glob
import traceback

# Importing from the 'src' directory after modularization
from src.ai_brain import AIBrain
from src.vision_engine import VisionEngine
from src.audio_listener import AudioListener
from src.speech_engine import SpeechEngine
from src.code_injector import CodeInjector

def main() -> None:
    """
    Main entry point for the AMD Hackathon AI Assistant.
    Orchestrates the asynchronous flow between Voice (STT), Vision, 
    LLM Reasoning (AI Brain), and Code Injection modules.
    """
    print("[System] Initializing AMD AI Assistant components...")
    
    # WORKSPACE CLEANUP: Clear residual audio files to keep the project clean
    print("[System] Executing workspace cleanup...")
    for file in glob.glob("temp_audio_*.mp3"): 
        try:
            os.remove(file)
        except OSError:
            pass

    try:
        # CORE INITIALIZATION: Utilizing Qwen-VL via Fireworks API for multimodal reasoning
        brain = AIBrain(model_id="accounts/fireworks/models/qwen3-vl-30b-a3b-instruct")
        vision = VisionEngine(memory_limit=3)
        listener = AudioListener()
        speaker = SpeechEngine()
        
        # BRIDGE PATTERN: Link listener to speaker for immediate playback interruption
        listener.speaker_ref = speaker
        
        injector = CodeInjector()
        
        # SENSORY ACTIVATION: Start background observation and listening threads
        vision.start_observation()
        listener.start_listening()
        
        print("[System] All systems online. Awaiting commands.")
        speaker.speak("Systems online. Ready to code.")

        # MAIN EVENT LOOP
        while True:
            # 1. VOICE PERCEPTION: Blocking call for command transcription
            user_command = listener.get_next_command()
            if not user_command:
                continue
            
            # NOISE & INTERRUPTION FILTER: Ignore short fragments or stop commands
            command_lower = user_command.lower().strip()
            stop_keywords = ['para', 'chega', 'stop', 'enough', 'quiet', 'cancel']
            
            if any(k in command_lower for k in stop_keywords) or len(command_lower.split()) <= 2:
                print(f"[System] Command filtered (Interruption/Noise): '{user_command}'")
                continue
            
            print(f"\n[User Request] {user_command}")

            # 2. VISUAL CONTEXT: Capture the current IDE/Workspace state
            visual_context = vision.get_visual_context()

            # 3. REASONING: Process multimodal inputs through the AI Brain
            ai_response = brain.process_instruction(user_command, visual_context)
            print(f"\n[AI Response]\n{ai_response}\n")

            # 4. ACTION EXECUTION & INTELLIGENT FEEDBACK: 
            # Execute injection and capture status for voice-guided error handling
            action_status = injector.execute_action(ai_response)
            
            if action_status == "FILE_NOT_FOUND":
                # VOICE FALLBACK: If the recursive search fails, the AI asks for clarification via voice
                speaker.speak("I couldn't find that file in your workspace. Could you tell me which folder it is in?")
            else:
                # NATURAL FEEDBACK: Regular conversational response from the AI
                speaker.speak(ai_response)

    except KeyboardInterrupt:
        print("\n[System] Shutdown signal received. Terminating processes...")
    except Exception as e:
        print(f"\n[System] CRITICAL ERROR DETECTED: {e}")
        traceback.print_exc() 
    finally:
        # DESTRUCTOR SEQUENCE: Release hardware resources and terminate threads
        if 'vision' in locals():
            vision.stop_observation()
        if 'listener' in locals():
            listener.stop_listening()
        if 'speaker' in locals():
            speaker.shutdown()
        print("[System] Shutdown complete.")

if __name__ == "__main__":
    main()