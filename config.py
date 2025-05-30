


import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Pinecone SDK v5+
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# ── ENV ───────────────────────────────────────────────────────────────────────
DATABASE_URL         = os.getenv("DATABASE_URL")
OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY     = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME", "listings-index")

if not (DATABASE_URL and OPENAI_API_KEY and PINECONE_API_KEY):
    raise RuntimeError("Missing one of DATABASE_URL, OPENAI_API_KEY or PINECONE_API_KEY")

# ── SQLAlchemy ────────────────────────────────────────────────────────────────
engine  = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# ── Pinecone Client ───────────────────────────────────────────────────────────
pc = Pinecone(
    api_key=PINECONE_API_KEY,
    environment=PINECONE_ENVIRONMENT,
)

# اگر ایندکس وجود نداشت، ایجادش کن
existing = [info["name"] for info in pc.list_indexes()]
if PINECONE_INDEX_NAME not in existing:
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=1536,         # یا هر بعد embedding که استفاده می‌کنی
        metric="cosine",        # یا "euclidean"
        spec=ServerlessSpec(    # یا هر Spec دیگری
            cloud="aws",
            region="us-east-1",
        )
    )
    # صبر کن تا ایندکس آماده بشه
    while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
        time.sleep(1)

# هندل ایندکس
index = pc.Index(PINECONE_INDEX_NAME)

# ── Embeddings & VectorStore ─────────────────────────────────────────────────
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

vector_store = PineconeVectorStore(
    index=index,
    embedding=embeddings,
    text_key="text",     # همون کلید متادیتا
    # namespace="default"  # اگر لازم داری
)









# # ─── config.py ───────────────────────────────────────────────────────────────
# import os
# from dotenv import load_dotenv
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# import pinecone
# from langchain.embeddings           import OpenAIEmbeddings
# from langchain_community.vectorstores import (
#     Pinecone as PineconeVectorStore   # نسخهٔ جدید ماژول
# )

# # ── env ---------------------------------------------------------------------
# load_dotenv()

# OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# PINECONE_ENV     = os.getenv("PINECONE_ENVIRONMENT")
# INDEX_NAME       = os.getenv("PINECONE_INDEX_NAME") or "listings-index"
# DATABASE_URL     = os.getenv("DATABASE_URL")         # مثل:  mysql+pymysql://user:pass@host/db
# MODEL_TYPE       = os.getenv("MODEL_TYPE", "gpt-4o")

# # ── SQLAlchemy --------------------------------------------------------------
# if not DATABASE_URL:
#     raise RuntimeError("DATABASE_URL not set in environment!")

# engine   = create_engine(DATABASE_URL, pool_pre_ping=True)
# Session  = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# def get_db():
#     """Dependency برای FastAPI—هر درخواست یک Session مستقل."""
#     db = Session()
#     try:
#         yield db
#     finally:
#         db.close()

# # ── Pinecone & Vector-Store -------------------------------------------------
# pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
# index = pinecone.Index(INDEX_NAME)

# embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# # این شیء در همهٔ سرویس‌ها share می‌شود
# vector_store = PineconeVectorStore.from_existing_index(
#     index_name = INDEX_NAME,
#     embedding  = embeddings,
#     text_key   = "text"        # کلید متنی که در ingest.py ذخیره کردیم
# )

