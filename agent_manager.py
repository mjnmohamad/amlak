

from __future__ import annotations
import json
import asyncio
from typing import Optional, Any

from config import Session, vector_store
from search_service import SearchService
from search_semantic import SemanticSearch
from models import Model, MODELS

from langchain.llms.base import LLM
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

# ───────────────── ۱) سرویس‌های جست‌وجو ─────────────────────────────────────
semantic_layer = SemanticSearch(vector_store)
search_service = SearchService(Session, vector_store, semantic_layer)

# ───────────────── ۲) رَپِر LLM برای LangChain ──────────────────────────────
class OpenRouterLangChain(LLM):
    model_name: str = MODELS

    @property
    def _llm_type(self) -> str:
        return "openrouter"

    def _call(self, prompt: str, stop: Optional[list[str]] = None, **kwargs: Any) -> str:
        """
        متد _call باید **kwargs رو هم بپذیرد تا ارور functions مربوط به agent حل شود.
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                Model(model_type=self.model_name).generate_response(prompt)
            )
        finally:
            loop.close()

llm = OpenRouterLangChain()

# ───────────────── ۳) ابزارها ───────────────────────────────────────────────
structured_tool = Tool(
    name="structured_search",
    func=search_service.structured_search,
    description="Structured SQL search with filters: neighborhood, max_price, min_sqft",
)

semantic_tool = Tool(
    name="semantic_search",
    func=search_service.semantic_search,
    description="Semantic similarity search over listing descriptions",
)

# ───────────────── ۴) Agent ────────────────────────────────────────────────
agent = initialize_agent(
    tools=[structured_tool, semantic_tool],
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=False,
)

# ───────────────── ۵) توابع کمکی ────────────────────────────────────────────
def run_agent(prompt: str) -> str:
    # به جای run از invoke استفاده می‌کنیم (بدون deprecated warning)
    return agent.invoke(prompt)

def run_agent_with_filters(
    neighborhood: str | None = None,
    max_price:    float | None = None,
    min_sqft:     float | None = None,
    text:         str | None = None,
) -> str:
    payload = {
        "neighborhood": neighborhood,
        "max_price":    max_price,
        "min_sqft":     min_sqft,
    }
    prompt = text or json.dumps(payload, ensure_ascii=False)
    return agent.invoke(prompt)







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
