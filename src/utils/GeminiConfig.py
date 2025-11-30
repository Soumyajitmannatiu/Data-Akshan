import os
import dotenv
from google import genai
dotenv.load_dotenv()

try:
    gemini_api_key=os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("Check API key")
    os.environ=gemini_api_key
    print("Gemini Configured")
except Exception as e:
    print("Error",e)