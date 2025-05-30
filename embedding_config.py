

# فایل: embedding_config.py

import os
from dotenv import load_dotenv
from openai import OpenAI as OpenAIClient # تغییر نام برای جلوگیری از تداخل با Langchain OpenAI
import tiktoken

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002") # [cite: 37]

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set for embeddings.")

# کلاینت OpenAI برای embeddings
openai_client_for_embeddings = OpenAIClient(api_key=OPENAI_API_KEY)

# اطلاعات مدل embedding
EMBEDDING_CTX_LENGTH = 8191 # حداکثر توکن برای text-embedding-ada-002
EMBEDDING_ENCODING = 'cl100k_base' # انکودینگ برای text-embedding-ada-002

def get_embedding(text: str, model: str = EMBEDDING_MODEL_NAME) -> list[float]:
    """
    تولید embedding برای متن داده شده با استفاده از مدل مشخص شده OpenAI.
    """
    text = text.replace("\n", " ")
    try:
        response = openai_client_for_embeddings.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding for text: '{text[:100]}...'. Error: {e}")
        raise

def num_tokens_from_string(string: str, encoding_name: str = EMBEDDING_ENCODING) -> int:
    """
    محاسبه تعداد توکن‌ها در یک رشته بر اساس انکودینگ مشخص.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens