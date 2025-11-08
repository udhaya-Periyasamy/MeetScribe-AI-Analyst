# check_models.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your .env file to get the API key
load_dotenv()

try:
    api_key = os.environ["GEMINI_API_KEY"]
    if not api_key:
        raise KeyError
    genai.configure(api_key=api_key)
    print("API key loaded. Fetching available models...")
except KeyError:
    print("FATAL: GEMINI_API_KEY not found in .env file.")
    print("Please make sure your .env file is in the same folder and has your key.")
    exit()

print("\n--- ✅ Models available to your API key ---")
print("We are looking for a model that supports 'generateContent' and video.\n")

found_video_model = False

# Loop and print all models
for m in genai.list_models():
    # We only care about models that can be used for 'generateContent'
    if 'generateContent' in m.supported_generation_methods:
        print(f"Model name: {m.name}")
        # This is the check for video.
        if m.name.startswith('models/gemini-1.5-flash'):
            found_video_model = True

print("-------------------------------------------\n")

if found_video_model:
    print("SUCCESS: Your key has access to 'gemini-1.5-flash'.")
    print("The error might be an outdated library.")
else:
    print("PROBLEM: Your key does not have access to 'gemini-1.5-flash'.")
    print("It might have a different name, like 'gemini-2.0-flash' or 'gemini-2.5-flash'.")

print("\nPlease copy this entire output and paste it back to me.")