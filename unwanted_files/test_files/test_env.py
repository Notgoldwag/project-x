from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("GPT-5 Mini Configuration Test")
print("=" * 60)
print(f"GPT5_MINI_ENDPOINT: {os.getenv('GPT5_MINI_ENDPOINT')}")
print(f"GPT5_MINI_DEPLOYMENT: {os.getenv('GPT5_MINI_DEPLOYMENT')}")
print(f"GPT5_MINI_API_VERSION: {os.getenv('GPT5_MINI_API_VERSION')}")
print(f"GPT5_MINI_API_KEY: {os.getenv('GPT5_MINI_API_KEY')[:20]}..." if os.getenv('GPT5_MINI_API_KEY') else "Not set")
print("=" * 60)

endpoint = os.getenv('GPT5_MINI_ENDPOINT')
deployment = os.getenv('GPT5_MINI_DEPLOYMENT')
version = os.getenv('GPT5_MINI_API_VERSION', '2024-02-15-preview')

url = f"{endpoint}openai/deployments/{deployment}/chat/completions?api-version={version}"
print(f"Full URL: {url}")
print("=" * 60)
