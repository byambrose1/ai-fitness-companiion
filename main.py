import openai
import os

# Get API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")