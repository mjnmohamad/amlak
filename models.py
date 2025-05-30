

# models.py


# -*- coding: utf-8 -*-
import os
import httpx
import logging
import asyncio

# تنظیم لاگر
logger = logging.getLogger(__name__)

# تنها مدل فعال: gpt-4o
MODELS = {
    "gpt-4o": "openai/gpt-4o-2024-11-20"
}

# مابقی دیکشنری‌های مدل فعلا خالی نگه داشته شده‌اند
MODELS_FREE = {}
MODELS_THINKING = {}
MODELS_IMAGE_ANALYZE = {}

class Model:
    def __init__(self, model_type='gpt-4o'):
        self.model_type = model_type
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        self.api_base = 'https://openrouter.ai/api/v1'
        logger.info(f"Model initialized with type: {self.model_type}")

    async def generate_response(self, prompt, image_url=None, conversation_history=None):
        return await self._generate_openrouter_response(prompt, image_url, conversation_history)

    async def _generate_openrouter_response(self, prompt, image_url=None, conversation_history=None, retries=3, backoff_in_seconds=2):
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': self._get_model_name()
            }

            messages = []

            if conversation_history:
                messages.extend(conversation_history)

            if self.model_type in MODELS_IMAGE_ANALYZE and image_url:
                user_message_content = [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url', 'image_url': {'url': image_url}}
                ]
                logger.info("Preparing messages with image_url for gpt-4o.")
            else:
                user_message_content = prompt
                logger.info("Preparing messages without image.")

            messages.append({
                'role': 'user',
                'content': user_message_content
            })

            data['messages'] = messages

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.api_base}/chat/completions',
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                response_json = response.json()

                if 'choices' in response_json and response_json['choices']:
                    logger.info("Response received from OpenRouter API.")
                    return response_json['choices'][0]['message']['content'].strip()
                else:
                    logger.error(f"Unexpected response format: {response_json}")
                    return "An unexpected error occurred while processing the response."

        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            if http_err.response.status_code == 422:
                return "An unexpected error occurred while processing the response."
            elif http_err.response.status_code == 429:
                if retries > 0:
                    logger.warning(f"Rate limited. Retrying after {backoff_in_seconds} seconds...")
                    await asyncio.sleep(backoff_in_seconds)
                    return await self._generate_openrouter_response(prompt, image_url, conversation_history, retries - 1, backoff_in_seconds * 2)
                else:
                    return "You have reached the rate limit. Please try again later."
            else:
                return "An error occurred while contacting the language model service."
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return "An unexpected error occurred."

    def _get_model_name(self):
        if self.model_type in MODELS:
            logger.info(f"Model name resolved: {MODELS[self.model_type]}")
            return MODELS[self.model_type]
        else:
            logger.error("Unsupported model type.")
            raise ValueError("Unsupported model type.")


   
