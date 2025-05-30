# ingest.py
import os, logging, tiktoken
from dotenv import load_dotenv
from pymongo import MongoClient
from pinecone import Pinecone, ServerlessSpec
from embedding_config import (
    get_embedding, num_tokens_from_string,
    EMBEDDING_CTX_LENGTH, EMBEDDING_ENCODING
)

load_dotenv()

MONGODB_URI   = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "manhatan")

PINECONE_API_KEY   = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── MongoDB ────────────────────────────────────────────
mongo = MongoClient(MONGODB_URI)
col   = mongo[MONGO_DB_NAME]["listings"]

# ── Pinecone ───────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

def ingest_data():
    if PINECONE_INDEX_NAME not in pc.list_indexes().names:
        logger.info("Creating Pinecone index …")
        pc.create_index(
            name      = PINECONE_INDEX_NAME,
            dimension = 1536,
            metric    = "cosine",
            spec      = ServerlessSpec(cloud="aws", region="us-east-1")
        )
    index = pc.Index(PINECONE_INDEX_NAME)

    listings = list(col.find({}))
    logger.info(f"Fetched {len(listings)} docs from MongoDB")

    batch, B = [], 100
    for doc in listings:
        desc = (doc.get("description") or "").replace("\n", " ")
        if not desc:
            logger.warning(f"Skip {doc.get('_id')} (no description)")
            continue

        # برش متن در صورت طولانی بودن
        tok = num_tokens_from_string(desc, EMBEDDING_ENCODING)
        if tok > EMBEDDING_CTX_LENGTH:
            enc  = tiktoken.get_encoding(EMBEDDING_ENCODING)
            desc = enc.decode(enc.encode(desc)[:EMBEDDING_CTX_LENGTH - 1])

        try:
            vec = get_embedding(desc)
        except Exception as e:
            logger.error(f"Embedding failed for {doc.get('_id')}: {e}")
            continue

        meta = {
            "id":        str(doc.get("_id") or doc.get("id")),
            "text":      desc,
            "neighborhood": doc.get("neighborhood", ""),
            "borough":      doc.get("borough", ""),
            "address":      doc.get("address", ""),
            "sale_price":   float(doc.get("sale_price") or 0),
            "gross_square_feet": float(doc.get("gross_square_feet") or 0),
            "year_built":  doc.get("year_built"),
            "original_description_snippet": desc[:200] + "…"
        }
        meta = {k: v for k, v in meta.items() if v not in ("", None)}

        batch.append({"id": meta["id"], "values": vec, "metadata": meta})

        if len(batch) >= B:
            index.upsert(vectors=batch)
            logger.info(f"Upserted {len(batch)} vectors")
            batch = []

    if batch:
        index.upsert(vectors=batch)
        logger.info(f"Upserted remaining {len(batch)} vectors")

    logger.info("✅ Ingestion finished.")

if __name__ == "__main__":
    ingest_data()







# import os
# import logging
# from dotenv import load_dotenv
# from sqlalchemy.orm import Session
# from pinecone import Pinecone, ServerlessSpec, PodSpec

# import tiktoken

# from orm_models import Listing, SessionLocal
# from embedding_config import get_embedding, num_tokens_from_string, EMBEDDING_CTX_LENGTH, EMBEDDING_ENCODING

# load_dotenv()

# # تنظیم لاگر
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # تنظیمات Pinecone
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
# PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME]):
#     raise ValueError("Pinecone API key, environment, or index name not set in .env file.")

# pc = Pinecone(api_key=PINECONE_API_KEY)

# def ingest_data():
#     db: Session = SessionLocal()
    
#     logger.info(f"Connecting to Pinecone index: {PINECONE_INDEX_NAME} in environment: {PINECONE_ENVIRONMENT}")

#     # بررسی وجود ایندکس و ایجاد آن در صورت نیاز
#     if PINECONE_INDEX_NAME not in pc.list_indexes().names:
#         logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' not found. Creating new index...")
#         try:
#             pc.create_index(
#                 name=PINECONE_INDEX_NAME,
#                 dimension=1536,  # ابعاد امبدینگ مدل text-embedding-ada-002
#                 metric='cosine', # [cite: 37] معیار فاصله، cosine برای تشابه معنایی مناسب است
#                 spec=ServerlessSpec( # یا PodSpec بسته به نوع اکانت Pinecone
#                     cloud='aws', # یا 'gcp', 'azure'
#                     region='us-east-1' # یا منطقه مناسب شما
#                 )
#                 # برای PodSpec:
#                 # spec=PodSpec(environment=PINECONE_ENVIRONMENT)
#             )
#             logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' created successfully.")
#         except Exception as e:
#             logger.error(f"Failed to create Pinecone index: {e}")
#             raise
#     else:
#         logger.info(f"Pinecone index '{PINECONE_INDEX_NAME}' already exists.")
    
#     pinecone_index = pc.Index(PINECONE_INDEX_NAME)

#     try:
#         # واکشی کلیه آگهی‌ها از DB [cite: 37]
#         listings_from_db = db.query(Listing).all() # [cite: 59]
#         logger.info(f"Fetched {len(listings_from_db)} listings from the database.")

#         vectors_to_upsert = []
#         batch_size = 100  # برای ارسال دسته‌ای به Pinecone جهت بهینگی

#         for listing in listings_from_db:
#             if not listing.description:
#                 logger.warning(f"Skipping listing ID {listing.id} (title: {listing.title}) due to missing description.")
#                 continue

#             description_to_embed = listing.description
#             token_count = num_tokens_from_string(description_to_embed, EMBEDDING_ENCODING)

#             if token_count > EMBEDDING_CTX_LENGTH:
#                 logger.warning(f"Description for listing ID {listing.id} (title: {listing.title}) exceeds token limit "
#                                f"({token_count} > {EMBEDDING_CTX_LENGTH}). It will be truncated.")
#                 # ساده‌ترین روش: بریدن متن (می‌توانید از روش‌های پیچیده‌تر خلاصه‌سازی استفاده کنید)
#                 encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)
#                 tokens = encoding.encode(description_to_embed)
#                 truncated_tokens = tokens[:EMBEDDING_CTX_LENGTH - 1] # -1 برای اطمینان
#                 description_to_embed = encoding.decode(truncated_tokens)
            
#             try:
#                 embedding = get_embedding(description_to_embed) # [cite: 37]
#             except Exception as e:
#                 logger.error(f"Could not get embedding for listing ID {listing.id} (title: {listing.title}). Error: {e}")
#                 continue

#             # آماده‌سازی متادیتا برای ذخیره در Pinecone [cite: 38]
#             metadata = {
#                 "title": str(listing.title) if listing.title else "",
#                 "city": str(listing.city) if listing.city else "",
#                 "zone": str(listing.zone) if listing.zone else "",
#                 "price": float(listing.price) if listing.price is not None else 0.0,
#                 "area": float(listing.area) if listing.area is not None else 0.0,
#                 "rooms": int(listing.rooms) if listing.rooms is not None else 0,
#                 # برای جستجوی بهتر، می‌توانید متن اصلی (یا خلاصه‌ای از آن) را هم در متادیتا ذخیره کنید
#                 "original_description_snippet": listing.description[:200] + "...", # فقط برای نمایش سریع
#                 "text": description_to_embed 
#             }
#             # حذف کلیدهایی که مقدار None دارند از متادیتا (Pinecone با مقادیر null مشکل دارد)
#             # Pinecone مقادیر null را به خوبی مدیریت نمی‌کند، بهتر است مقادیر پیش‌فرض معقول بگذارید یا کلا حذف کنید
#             metadata_cleaned = {k: v for k, v in metadata.items() if v is not None and v != ""}


#             vectors_to_upsert.append({
#                 "id": str(listing.id),  # ID باید رشته باشد
#                 "values": embedding,
#                 "metadata": metadata_cleaned
#             })

#             if len(vectors_to_upsert) >= batch_size:
#                 logger.info(f"Upserting batch of {len(vectors_to_upsert)} vectors to Pinecone...")
#                 pinecone_index.upsert(vectors=vectors_to_upsert)
#                 vectors_to_upsert = []
        
#         if vectors_to_upsert:  # آپلود باقیمانده بردارها
#             logger.info(f"Upserting remaining {len(vectors_to_upsert)} vectors to Pinecone...")
#             pinecone_index.upsert(vectors=vectors_to_upsert)

#         logger.info("Data ingestion and indexing complete.")
#         logger.info(f"Pinecone index stats: {pinecone_index.describe_index_stats()}")

#     except Exception as e:
#         logger.error(f"An error occurred during ingestion: {e}", exc_info=True)
#     finally:
#         db.close()
#         logger.info("Database session closed.")

# if __name__ == "__main__":
#     logger.info("Starting data ingestion process...")
#     ingest_data() # [cite: 59]
#     logger.info("Ingestion process finished.")

