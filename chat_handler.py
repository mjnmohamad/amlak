


# ─── chat_handler.py ─────────────────────────────────────────────────────────
import os, asyncio
from typing       import List, Dict
from dotenv       import load_dotenv
from sqlalchemy   import create_engine
from sqlalchemy.orm import sessionmaker
from models          import Model
from search_service  import SearchService
from config          import vector_store

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
MODEL_TYPE   = os.getenv("MODEL_TYPE", "gpt-4o")

# ── Session واحد از همان Engine همه‌جا
engine   = create_engine(DATABASE_URL)
Session  = sessionmaker(bind=engine)

search_service = SearchService(Session, vector_store)
llm_model      = Model(model_type=MODEL_TYPE)

Message = Dict[str, str]

# ---------------------------------------------------------------------------
async def handle_user_message(
    user_message: str,
    filters: Dict[str, str],
    conversation_history: List[Message]
) -> str:
    """جست‌وجو، ساخت کانتکست، فراخوانی LLM و برگرداندن پاسخ متن"""
    # ۱) search
    structured = search_service.structured_search(
        city      = filters.get("city", ""),
        max_price = float(filters["max_price"]) if filters.get("max_price") else None,
        min_area  = float(filters["min_area"])  if filters.get("min_area")  else None
    )
    semantic   = search_service.semantic_search(user_message)

    # ۲) کانتکست → فقط رشته‌های کوتاه
    ctx_lines = [
        f"{it['id']}: {it['description_snippet']}" for it in structured[:5]
    ] + [
        f"{it['id']}: {it['description_snippet']}" for it in semantic
    ]

    prompt = (
        "You are a real-estate assistant.\n"
        "Relevant listings:\n" + "\n".join(ctx_lines) +
        f"\n\nUser question: {user_message}"
    )

    # ۳) تاریخچه + پیام فعلی
    messages = conversation_history.copy()
    messages.append({"role": "user", "content": prompt})

    reply = await llm_model.generate_response(
        prompt               = prompt,
        conversation_history = messages
    )
    return reply

# ─── اجرای نمونه ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    async def _demo():
        hist: List[Message] = []
        flt  = {"city": "تهران", "max_price": "10000000000", "min_area": "70"}
        ans  = await handle_user_message(
            "می‌خوام یه آپارتمان دوخوابه نزدیک مترو با نور عالی",
            flt, hist
        )
        print(ans)

    asyncio.run(_demo())



# import os
# import asyncio
# from typing import List, Dict
# from dotenv import load_dotenv
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from models import Model
# from search_service import SearchService
# from config import vector_store


# # بارگذاری متغیرهای محیطی
# load_dotenv()
# DATABASE_URL = os.getenv('DATABASE_URL')
# MODEL_TYPE = os.getenv('MODEL_TYPE', 'gpt-4o')

# # تنظیم دیتابیس و Session
# engine = create_engine(DATABASE_URL)
# Session = sessionmaker(bind=engine)

# # نمونه‌سازی SearchService با هر دو روش جست‌وجو
# search_service = SearchService(Session, vector_store)

# # نمونه‌سازی LLM از OpenRouter
# llm_model = Model(model_type=MODEL_TYPE)

# # نوع پیام‌ها
# Message = Dict[str, str]

# async def handle_user_message(
#     user_message: str,
#     filters: Dict[str, str],   # {'city':'تهران','max_price':'...','min_area':'...'}
#     conversation_history: List[Message]
# ) -> str:
#     """
#     1. جست‌وجو ساختاری و معنایی از طریق SearchService
#     2. ترکیب کانتکست
#     3. ارسال prompt به مدل و دریافت پاسخ
#     """
#     # ۱. Structured + Semantic
#     structured_results = search_service.structured_search(
#         filters.get('city', ''),
#         float(filters.get('max_price')) if filters.get('max_price') else None,
#         float(filters.get('min_area')) if filters.get('min_area') else None
#     )
#     semantic_results = search_service.semantic_search(user_message)

#     # ۲. آماده‌سازی کانتکست
#     context_snippets: List[str] = []
#     for item in structured_results[:5]:
#         context_snippets.append(f"{item['id']}: {item['description']}")
#     for snippet in semantic_results:
#         context_snippets.append(snippet)

#     prompt = f"""
# You are a real estate assistant. Here are some relevant listings:
# {chr(10).join(context_snippets)}

# User question: {user_message}
# """

#     # افزودن تاریخچه مکالمه
#     messages = conversation_history.copy()
#     messages.append({'role': 'user', 'content': prompt})

#     # ۳. فراخوانی مدل
#     response = await llm_model.generate_response(
#         prompt=prompt,
#         conversation_history=messages
#     )
#     return response

# # مثال اجرای مستقل
# if __name__ == '__main__':
#     async def demo():
#         history: List[Message] = []
#         filters = {'city': 'تهران', 'max_price': '10000000000', 'min_area': '70'}
#         answer = await handle_user_message(
#             "می‌خوام یه آپارتمان دوخوابه نزدیک مترو با نور عالی", filters, history
#         )
#         print(answer)
#     asyncio.run(demo())

