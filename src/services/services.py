from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.openai_api_key
) 

async def generate(prompt: str):
    response = await client.chat.completions.create(
        model=settings.model_name,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content
