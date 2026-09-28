import asyncio
import os
import sys

# Set env vars to simulate the app running
from dotenv import load_dotenv
load_dotenv('.env')

from app.services.llm_service import OpenAIProvider
from app.schemas.chat import ChatMessage

async def main():
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    print(f"Testing model: {model}")
    
    try:
        provider = OpenAIProvider(api_key=api_key, model=model)
        answer = await provider.generate(
            user_message="Hello",
            context_block="Test context",
            history=[]
        )
        print("SUCCESS!")
        print(answer)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
