# agent_manager.py
# ────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import json, asyncio
from typing import Optional, Any

from config          import listings_collection, vector_store
from search_service  import SearchService
from search_semantic import SemanticSearch
from models          import Model, MODELS

from langchain.llms.base import LLM
from langchain.agents    import initialize_agent, AgentType
from langchain.tools     import Tool

# ───────────────── ۱) لایهٔ جست‌وجو ─────────────────────────────────────────
semantic_layer  = SemanticSearch(vector_store)
search_service  = SearchService(listings_collection, vector_store, semantic_layer)

# ───────────────── ۲) رَپِر LLM برای LangChain ─────────────────────────────
class OpenRouterLangChain(LLM):
    """
    لایهٔ نازک روی کلاس Model تا با LangChain سازگار شود.
    - اگر فراخوان همگام باشد (مثلاً در CLI)، متد _call اجرا می‌شود.
    - اگر فراخوان ناهمگام باشد (در FastAPI یا هر رویداد‌محور دیگر)، LangChain
      به‌طور خودکار _acall را صدا می‌زند.
    """
    model_name: str = "gpt-4o"

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    # — مسیر «همگام» (Sync) —-------------------------------------------------
    def _call(self, prompt: str, stop: Optional[list[str]] = None, **kw: Any) -> str:
        """
        فقط زمانی فراخوانی می‌شود که داخل event-loop نباشیم؛ در غیر این صورت
        باید از نسخهٔ async استفاده شود (agent.ainvoke).
        """
        try:
            asyncio.get_running_loop()
            raise RuntimeError(
                "OpenRouterLangChain._call در حالی صدا زده شد که یک event-loop در حال اجرا است. "
                "لطفاً از agent.ainvoke یا متدهای async استفاده کنید."
            )
        except RuntimeError:  # یعنی هیچ loop فعالی وجود ندارد → مشکلی نیست
            return asyncio.run(
                Model(model_type=self.model_name).generate_response(prompt)
            )

    # — مسیر «ناهمگام» (Async) —---------------------------------------------
    async def _acall(self, prompt: str, stop: Optional[list[str]] = None, **kw: Any) -> str:
        return await Model(model_type=self.model_name).generate_response(prompt)

# نمونهٔ LLM
llm = OpenRouterLangChain()

# ───────────────── ۳) تعریف ابزارها ─────────────────────────────────────────
structured_tool = Tool(
    name        = "structured_search",
    func        = search_service.structured_search,
    description = "Structured Mongo search (neighborhood, max_price, min_sqft)",
)

semantic_tool = Tool(
    name        = "semantic_search",
    func        = search_service.semantic_search,
    description = "Semantic similarity search over listing descriptions",
)

# ───────────────── ۴) ساخت Agent ────────────────────────────────────────────
agent = initialize_agent(
    tools  = [structured_tool, semantic_tool],
    llm    = llm,
    agent  = AgentType.OPENAI_FUNCTIONS,
    verbose=False,
)

# ───────────────── ۵) توابع کمکی برای فراخوان Agent ────────────────────────
async def run_agent(prompt: str) -> str:
    """فراخوان آزاد Agent به‌صورت ناهمگام"""
    return await agent.ainvoke(prompt)

async def run_agent_with_filters(
    neighborhood: str  | None = None,
    max_price:    float | None = None,
    min_sqft:     float | None = None,
    text:         str   | None = None,
) -> str:
    """فراخوان Agent همراه با فیلترهای ساختاری"""
    payload = {
        "neighborhood": neighborhood,
        "max_price":    max_price,
        "min_sqft":     min_sqft,
    }
    prompt = text or json.dumps(payload, ensure_ascii=False)
    return await agent.ainvoke(prompt)









# # ─── agent_manager.py ────────────────────────────────────────────────────────
# """
# اینجا همهٔ وابستگی‌ها (SearchService، ابزارها، LLM و Agent) یک‌بار مقداردهی
# می‌شوند تا در طول عمر برنامه مجدداً ساخته نشوند.
# """

# from __future__ import annotations
# import json
# import os
# from typing import Optional

# # ─── لایه‌های داخلی پروژه ───────────────────────────────────────────────────
# from config             import Session, OPENAI_API_KEY
# from search_service     import SearchService
# from search_semantic    import SemanticSearch

# # ─── Pinecone و LangChain برای بازیابی معنایی ─────────────────────────────
# from langchain.vectorstores           import Pinecone as PineconeStore
# from langchain.embeddings.openai     import OpenAIEmbeddings
# import pinecone

# # ─── LLM و Agent ────────────────────────────────────────────────────────────
# from langchain.chat_models            import ChatOpenAI
# from langchain.agents                 import initialize_agent, AgentType
# from langchain.tools                  import Tool

# # ──────────────────── ۱) مقداردهی Pinecone ──────────────────────────────────
# pinecone.init(
#     api_key      = os.getenv("PINECONE_API_KEY"),
#     environment  = os.getenv("PINECONE_ENVIRONMENT")
# )

# index_name       = os.getenv("PINECONE_INDEX_NAME")
# embedding_model  = OpenAIEmbeddings()
# vector_store     = PineconeStore.from_existing_index(index_name, embedding_model)

# # ──────────────────── ۲) ساخت شی SemanticSearch ─────────────────────────────
# semantic_search = SemanticSearch(vector_store)

# # ──────────────────── ۳) ساخت SearchService با همه وابستگی‌ها ───────────────
# search_service = SearchService(Session, vector_store, semantic_search)

# # ──────────────────── ۴) مدل زبانی (LLM) ─────────────────────────────────────
# llm = ChatOpenAI(
#     temperature   = 0,
#     openai_api_key = OPENAI_API_KEY
# )

# # ──────────────────── ۵) تعریف Tools برای Agent ─────────────────────────────
# search_tool = Tool(
#     name        = "search_listings",
#     func        = search_service.structured_search,
#     description = "جست‌وجوی ساختاری آگهی‌های املاک با فیلترهای city, max_price, min_area"
# )

# embed_tool = Tool(
#     name        = "semantic_search",
#     func        = search_service.semantic_search,
#     description = "بازیابی معنایی توضیحات آگهی‌ها از Vector DB (کلمات مرتبط)"
# )

# # ──────────────────── ۶) مقداردهی Agent ─────────────────────────────────────
# agent = initialize_agent(
#     tools   = [search_tool, embed_tool],
#     llm     = llm,
#     agent   = AgentType.OPENAI_FUNCTIONS,
#     verbose = False
# )

# # ──────────────────── ۷) توابع کمکی برای استفاده در بیرون ──────────────────
# def run_agent(prompt: str) -> str:
#     """اجرای مستقیم Agent با یک پرامپت خام."""
#     return agent.run(prompt)

# def run_agent_with_filters(
#     city: str,
#     max_price: Optional[float] = None,
#     min_area: Optional[float] = None,
#     text: Optional[str] = None
# ) -> str:
#     """
#     اگر متن پرسش (text) داده شود همان استفاده می‌شود؛
#     در غیر این صورت فیلترها به‌صورت JSON در پرامپت قرار می‌گیرند.
#     """
#     payload = {"city": city, "max_price": max_price, "min_area": min_area}
#     prompt  = text or json.dumps(payload, ensure_ascii=False)
#     return agent.run(prompt)





# # ─── agent_manager.py ────────────────────────────────────────────────────────
# """
# اینجا همهٔ وابستگی‌ها (SearchService، ابزارها، LLM و Agent) یک‌بار مقداردهی
# می‌شوند تا در طول عمر برنامه مجدداً ساخته نشوند.
# """

# from __future__ import annotations
# import json
# from typing import Optional

# from config             import Session, vector_store, OPENAI_API_KEY
# from search_service import SearchService
# from langchain.chat_models import ChatOpenAI
# from langchain.agents      import initialize_agent, AgentType
# from langchain.tools       import Tool

# # ──────────────────── ۱) سرویس‌های پایه ─────────────────────────────────────
# search_service = SearchService(Session, vector_store)

# llm = ChatOpenAI(
#     temperature   = 0,
#     openai_api_key = OPENAI_API_KEY          # کلید مستقیماً از config می‌آید
# )

# # ──────────────────── ۲) تعریف Tools برای Agent ─────────────────────────────
# search_tool = Tool(
#     name        = "search_listings",
#     func        = search_service.structured_search,
#     description = "جست‌وجوی ساختاری آگهی‌های املاک با فیلترهای city, max_price, min_area"
# )

# embed_tool = Tool(
#     name        = "semantic_search",
#     func        = search_service.semantic_search,
#     description = "بازیابی معنایی توضیحات آگهی‌ها از Vector DB (کلمات مرتبط)"
# )

# # ──────────────────── ۳) مقداردهی Agent ─────────────────────────────────────
# agent = initialize_agent(
#     tools   = [search_tool, embed_tool],
#     llm     = llm,
#     agent   = AgentType.OPENAI_FUNCTIONS,
#     verbose = False
# )

# # ──────────────────── ۴) توابع کمکی برای استفاده در بیرون ──────────────────
# def run_agent(prompt: str) -> str:
#     """اجرای مستقیم Agent با یک پرامپت خام."""
#     return agent.run(prompt)

# def run_agent_with_filters(
#     city: str,
#     max_price: Optional[float] = None,
#     min_area: Optional[float] = None,
#     text: Optional[str] = None
# ) -> str:
#     """
#     اگر متن پرسش (text) داده شود همان استفاده می‌شود؛
#     در غیر این صورت فیلترها به‌صورت JSON در پرامپت قرار می‌گیرند.
#     """
#     payload = {"city": city, "max_price": max_price, "min_area": min_area}
#     prompt  = text or json.dumps(payload, ensure_ascii=False)
#     return agent.run(prompt)
