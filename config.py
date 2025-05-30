

# ─── config.py ───────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pinecone import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore

# ── env -------------------------------------------------------------------- #
load_dotenv()

DATABASE_URL          = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")          # فقط برای Embedding
PINECONE_API_KEY      = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT  = os.getenv("PINECONE_ENVIRONMENT")    # دیگر استفاده نمی‌شود
PINECONE_INDEX_NAME   = os.getenv("PINECONE_INDEX_NAME") or "listings-index"
MODEL_TYPE            = os.getenv("MODEL_TYPE", "gpt-4o")    # برای models.Model

# ── SQLAlchemy ------------------------------------------------------------- #
engine   = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
Session  = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()

# ── Pinecone & LangChain Vector-Store ------------------------------------- #
pc = Pinecone(api_key=PINECONE_API_KEY)   # اتصال جدید طبق نسخه جدید Pinecone

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

vector_store = PineconeVectorStore.from_existing_index(
    index_name=PINECONE_INDEX_NAME,
    embedding=embeddings,
    text_key="text"  # همان کلیدی که در ingest.py ذخیره می‌کنیم
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

