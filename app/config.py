import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # loads from .env file

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)
