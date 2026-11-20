from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Instantiates client using GEMINI_API_KEY from environment
client = genai.Client()

# Initialize chat with an active supported model string
chat = client.chats.create(model="gemini-3.6-flash")

response = chat.send_message("Explain how to create a route in FastAPI")

print(response.text)