import os
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# ── لایه‌های داخلی ---------------------------------------------------------
from config          import listings_collection, vector_store
from search_service  import SearchService
from search_semantic import SemanticSearch
from agent_manager   import run_agent_with_filters

# ─────────────────── مقداردهی اپلیکیشن ────────────────────────────────────
app = FastAPI(title="AMLAK Chat API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# سرو کردن فایل‌های static
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse("static/index.html")

# ── سرویس‌های دیتابیس و وکتور ───────────────────────────────────────────
semantic_layer = SemanticSearch(vector_store)
search_service = SearchService(listings_collection, vector_store, semantic_layer)

# ── مدل‌های ورودی/خروجی ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    prompt:       Optional[str] = Field(None, description="متن پرسش آزاد یا سوال follow-up")
    neighborhood: Optional[str] = Field(None, description="فیلتر محله")
    max_price:    Optional[float] = Field(None, description="سقف قیمت")
    min_sqft:     Optional[float] = Field(None, description="حداقل مساحت")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="پاسخ مدل بر اساس دیتابیس و سوالات شما")

class SearchRequest(BaseModel):
    neighborhood: Optional[str] = None
    max_price:    Optional[float] = None
    min_sqft:     Optional[float] = None

# ── اندپوینت‌های API ─────────────────────────────────────────────────────
@app.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="گفتگو با هوش‌مصنوعی (RAG با دیتابیس و Follow-up)"
)
async def chat_endpoint(req: ChatRequest):
    try:
        # 1) جستجوی ساختاری با فیلترها
        props = search_service.structured_search(
            neighborhood=req.neighborhood,
            max_price=req.max_price,
            min_sqft=req.min_sqft,
            limit=10
        )
        # 2) ساخت خلاصه نتایج
        if props:
            summary_lines = []
            for p in props:
                addr = p.get('address', 'Unknown address')
                neigh = p.get('neighborhood', 'Unknown')
                price = p.get('sale_price', 0)
                sqft = p.get('gross_square_feet', 0)
                summary_lines.append(
                    f"{addr} in {neigh} for ${price} ({sqft} sqft)"
                )
            summary_text = "\n".join(summary_lines)
        else:
            summary_text = "هیچ ملکی مطابق فیلترها یافت نشد."

        # 3) اگر فقط فیلتر و بدون prompt باشند
        if not req.prompt:
            return ChatResponse(reply=summary_text)

        # 4) ترکیب فیلترها و سوال کاربر
        combined_text = (
            "املاک زیر با فیلترهای شما یافت شد:\n"
            f"{summary_text}\n\n"
            "سوال شما: " + req.prompt
        )

        # 5) فراخوانی Agent با متن ترکیبی و فیلترها
        result = await run_agent_with_filters(
            neighborhood=req.neighborhood,
            max_price=req.max_price,
            min_sqft=req.min_sqft,
            text=combined_text,
        )
        # تبدیل خروجی به رشته
        if isinstance(result, dict):
            answer_text = result.get('output') or result.get('reply') or str(result)
        else:
            answer_text = str(result)

        return ChatResponse(reply=answer_text)

    except Exception:
        raise HTTPException(status_code=500, detail="خطا در پردازش درخواست چت")

@app.post(
    "/api/search",
    response_model=List[Dict],
    summary="جستجوی ساختاری مستقیم در MongoDB"
)
async def search_endpoint(req: SearchRequest):
    try:
        return search_service.structured_search(
            neighborhood=req.neighborhood,
            max_price=req.max_price,
            min_sqft=req.min_sqft
        )
    except Exception:
        raise HTTPException(status_code=500, detail="خطا در جستجوی املاک")

@app.get("/health", summary="Health-check")
async def health():
    return {"status": "ok"}





# # main.py
# import os
# from typing import Optional, List

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from pydantic import BaseModel

# # لایه‌های داخلی
# from config import listings_collection, vector_store
# from search_service import SearchService
# from search_semantic import SemanticSearch
# from agent_manager import run_agent_with_filters

# # ---------- مقداردهی اصلی اپ ----------
# app = FastAPI(title="AMLAK Chat API", version="0.1.0")

# # پوشه static (برای index.html ساده)
# os.makedirs("static", exist_ok=True)

# # لایه معنایی و سرویس جست‌وجو
# semantic_layer = SemanticSearch(vector_store)
# search_service = SearchService(listings_collection, vector_store, semantic_layer)

# # CORS برای فرانت
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ---------- مدل‌های ورودی/خروجی ----------
# class ChatRequest(BaseModel):
#     prompt: Optional[str] = None
#     neighborhood: Optional[str] = None
#     max_price: Optional[float] = None
#     min_sqft: Optional[float] = None

# class ChatResponse(BaseModel):
#     reply: str

# class SearchRequest(BaseModel):
#     neighborhood: Optional[str] = None
#     max_price: Optional[float] = None
#     min_sqft: Optional[float] = None

# # ---------- اندپوینت‌ها ----------
# @app.post("/api/chat", response_model=ChatResponse)
# async def chat_endpoint(body: ChatRequest):
#     raw = await run_agent_with_filters(
#         neighborhood=body.neighborhood,
#         max_price=body.max_price,
#         min_sqft=body.min_sqft,
#         text=body.prompt,
#     )
#     reply_text = raw["output"] if isinstance(raw, dict) else raw
#     return {"reply": reply_text}

# @app.post("/api/search", summary="جست‌وجوی ساختاری آگهی‌ها")
# async def search_endpoint(body: SearchRequest) -> List[dict]:
#     listings = search_service.structured_search(
#         neighborhood=body.neighborhood,
#         max_price=body.max_price,
#         min_sqft=body.min_sqft,
#     )
#     return listings


# @app.get("/api/debug", include_in_schema=False, summary="Debug MongoDB")
# async def debug_mongo():
#     total = listings_collection.count_documents({})
#     sample = listings_collection.find_one()
#     # فقط کلیدها را به عنوان لیست برمی‌گردانیم
#     keys = list(sample.keys()) if sample else []
#     return {"total_docs": total, "sample_keys": keys}
    
# @app.get("/health", summary="Health-check")
# async def health():
#     return {"status": "ok"}

# # ---------- سرو فایل‌های استاتیک ----------
# app.mount(
#     "/",  # http://<host>/
#     StaticFiles(directory="static", html=True),
#     name="static",
# )







# اجرا:  uvicorn main:app --reload --port 8000





# # ─── main.py ────────────────────────────────────────────────────────────────
# from fastapi import FastAPI
# from pydantic import BaseModel
# from typing import Optional

# from agent_manager import run_agent_with_filters   # توابع آماده

# app = FastAPI(
#     title="ShishDong Real-Estate Chat API",
#     version="0.1.0",
# )

# # ──────────────────── مدل ورودی ─────────────────────────────────────────────
# class Query(BaseModel):
#     city: str
#     max_price: Optional[float] = None
#     min_area: Optional[float] = None
#     text:     Optional[str]   = None

# # ──────────────────── مسیردهی ───────────────────────────────────────────────
# @app.post("/chat/", summary="گفت‌وگو با چت‌بات املاک")
# async def chat(q: Query):
#     """
#     نقطهٔ ورودی اصلی برای کلاینت وب.
#     - در صورت وجود `text` از آن به عنوان پرسش کاربر استفاده می‌شود.
#     - در غیر این صورت فیلترها (city, max_price, min_area) به‌شکل JSON
#       به Agent پاس داده می‌شود تا خودش بهترین جواب را برگرداند.
#     """
#     response = run_agent_with_filters(
#         city       = q.city,
#         max_price  = q.max_price,
#         min_area   = q.min_area,
#         text       = q.text
#     )
#     return {"response": response}

# # اندپوینت سلامت ساده
# @app.get("/", summary="سلامت سرویس")
# async def root():
#     return {"status": "ok"}

# # برای اجرای محلی:
# # uvicorn main:app --reload --host 0.0.0.0 --port 8000




# # ✅ main.py - نسخه بازنویسی شده برای استفاده از config.py

# from fastapi import FastAPI
# from pydantic import BaseModel
# import json

# from config import Session, vector_store, OPENAI_API_KEY
# from search_service import SearchService
# from langchain.chat_models import ChatOpenAI
# from langchain.agents import initialize_agent, AgentType
# from langchain.tools import Tool

# # ───── راه‌اندازی سرویس جست‌وجو ─────
# search_service = SearchService(Session, vector_store)

# # ───── راه‌اندازی مدل چت ─────
# llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)

# # ───── تعریف ابزارها برای Agent ─────
# search_tool = Tool(
#     name='search_listings',
#     func=search_service.structured_search,
#     description='جست‌وجوی آگهی‌ها با فیلتر city, max_price, min_area'
# )

# embed_tool = Tool(
#     name='semantic_search',
#     func=search_service.semantic_search,
#     description='بازیابی متن توضیحات مرتبط از Vector DB'
# )

# # ───── تعریف Agent با قابلیت Function Calling ─────
# agent = initialize_agent(
#     tools=[search_tool, embed_tool],
#     llm=llm,
#     agent=AgentType.OPENAI_FUNCTIONS,
#     verbose=False
# )

# # ───── تعریف API ─────
# app = FastAPI()

# class Query(BaseModel):
#     city: str
#     max_price: float | None = None
#     min_area: float | None = None
#     text: str | None = None

# @app.post('/chat/')
# def chat(q: Query):
#     payload = {'city': q.city, 'max_price': q.max_price, 'min_area': q.min_area}
#     prompt = q.text or json.dumps(payload, ensure_ascii=False)
#     response = agent.run(prompt)
#     return {'response': response}

# # برای اجرای سرور:
# # uvicorn main:app --reload --host 0.0.0.0 --port 8000
