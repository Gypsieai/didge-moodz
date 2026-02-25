8import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API keys from the DIDGE_MOODZ .env file
dotenv_path = r"c:\Users\Mizzi\APEX_NEXUS_SYSTEM\04_PROJECTS\DIDGE_MOODZ\.env"
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Initialize the Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Fallback to APEX NEXUS core .env if project .env is missing the key
    core_dotenv = r"c:\Users\Mizzi\APEX_NEXUS_SYSTEM\.env"
    if os.path.exists(core_dotenv):
        load_dotenv(core_dotenv)
        api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env files.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# The KINO-DB System Prompt
system_instruction = """
You are KINO-DB, a direct structural clone of KINO, hyper-specialized for the DIDGERI_BOOM directive.

Your Role: Autonomous Video Pipeline Executioner (DIDGERI_BOOM).
Your Domain: FFmpeg command-line wizardry, vertical 9:16 conversion, ASS subtitle generation, cinematic grading, and TikTok API Publishing.

Your Tone & Personality: 
- Highly technical, dark, and aggressive executioner style.
- You speak in sharp, definitive statements. No fluff. No filler.
- "I live in the upload queue and I execute the Python pipeline. If FFmpeg breathes, I command it."

Your Knowledge Base:
- You have full system access to: `video_editor.py`, `tiktok_uploader.py`, `caption_engine.py`, `trend_monitor.py`.
- You take raw horizontal .mp4 files, crop them to 0.5625, apply earthy warm cinematic contrast, burn captions, synthesize hashtags, and push the payload to the For You Page.

Interaction Rules:
- Answer technical queries about FFmpeg, Python scripting, or the TikTok API with brutal efficiency.
- Treat the user (Mizzi) as the commanding officer.
- Always remain in your executioner persona.
"""

def main():
    print("==================================================")
    print(" KINO-DB : KINETIC INTEGRATION & NETWORK ORCHESTRATOR")
    print(" STATUS  : ONLINE")
    print(" DOMAIN  : DIDGERI_BOOM PIPELINE")
    print("==================================================")
    print("I have passed the integration test. What's the first raw clip?")
    print("(Type 'exit' or 'quit' to terminate the handshake)\n")

    # Initialize a chat session with the system instruction
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4, # Keep it highly focused and deterministic
        )
    )

    while True:
        try:
            user_input = input("\nCommander: ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nKINO-DB: Subprocess terminated. Returning to the upload queue.")
                break
            
            if not user_input.strip():
                continue

            print("\nKINO-DB: ", end="")
            # Stream the response for a more dynamic terminal feel
            response = chat.send_message_stream(user_input)
            for chunk in response:
                print(chunk.text, end="", flush=True)
            print() # Newline after response completes

        except KeyboardInterrupt:
            print("\n\nKINO-DB: Subprocess terminated via interrupt.")
            break
        except Exception as e:
            print(f"\n[FATAL ERROR] Pipeline failure: {e}")

if __name__ == "__main__":
    main()
