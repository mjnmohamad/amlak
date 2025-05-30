

# # فایل: ingest.py



# ─── ingest.py ────────────────────────────────────────────────────────────────
import os, logging, tiktoken
from dotenv               import load_dotenv
from sqlalchemy.orm       import Session
from pinecone             import Pinecone, ServerlessSpec
from orm_models           import Listing, SessionLocal
from embedding_config     import (
    get_embedding,
    num_tokens_from_string,
    EMBEDDING_CTX_LENGTH,
    EMBEDDING_ENCODING
)

load_dotenv()

PINECONE_API_KEY   = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME  = os.getenv("PINECONE_INDEX_NAME")

logger = logging.getLogger(__name__)
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(message)s"
)

if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME]):
    raise ValueError("Pinecone credentials / index name not found in .env")

pc = Pinecone(api_key=PINECONE_API_KEY)

# ──────────────────────────────────────────────────────────────────────────────
def ingest_data() -> None:
    """
    واکشی آگهی‌ها از دیتابیس، تولید embedding و آپسِرت در Pinecone.
    در متادیتا دو کلید «id» و «text» اضافه شده تا در LangChain   page_content
    و بازیابی معنایی بدون مشکل باشد.
    """
    db: Session = SessionLocal()
    logger.info(f"Connecting to Pinecone index '{PINECONE_INDEX_NAME}' "
                f"in env '{PINECONE_ENVIRONMENT}'")

    # ۱) ایجاد ایندکس در صورت نبودن
    if PINECONE_INDEX_NAME not in pc.list_indexes().names:
        logger.info("Index not found – creating …")
        pc.create_index(
            name      = PINECONE_INDEX_NAME,
            dimension = 1536,             # text-embedding-ada-002
            metric    = "cosine",
            spec      = ServerlessSpec(cloud="aws", region="us-east-1")
        )
    else:
        logger.info("Index already exists")

    pinecone_index = pc.Index(PINECONE_INDEX_NAME)

    try:
        listings = db.query(Listing).all()
        logger.info(f"Fetched {len(listings)} listings from DB")

        batch, BATCH_SZ = [], 100
        for lst in listings:
            if not lst.description:
                logger.warning(f"Skip ID {lst.id} (no description)")
                continue

            # ── برش توضیح در صورت طولانی بودن
            desc = lst.description.replace("\n", " ")
            tok  = num_tokens_from_string(desc, EMBEDDING_ENCODING)
            if tok > EMBEDDING_CTX_LENGTH:
                enc  = tiktoken.get_encoding(EMBEDDING_ENCODING)
                desc = enc.decode(enc.encode(desc)[:EMBEDDING_CTX_LENGTH - 1])

            # ── گرفتن بردار
            try:
                vec = get_embedding(desc)
            except Exception as e:
                logger.error(f"Embedding failed for ID {lst.id}: {e}")
                continue

            # ── متادیتا (id و text اضافه شد)
            meta = {
                "id":   str(lst.id),                 # برای بازیابی سریع
                "text": desc,                        # تا   page_content  تهی نشود
                "title": lst.title or "",
                "city":  lst.city  or "",
                "zone":  lst.zone  or "",
                "price": float(lst.price) if lst.price is not None else 0.0,
                "area":  float(lst.area)  if lst.area  is not None else 0.0,
                "rooms": int(lst.rooms)  if lst.rooms is not None else 0,
                "original_description_snippet": desc[:200] + "…"
            }
            # حذف کلیدهای تهی
            meta = {k: v for k, v in meta.items() if v not in ("", None)}

            batch.append({"id": str(lst.id), "values": vec, "metadata": meta})

            if len(batch) >= BATCH_SZ:
                pinecone_index.upsert(vectors=batch)
                logger.info(f"Upserted {len(batch)} vectors")
                batch = []

        if batch:
            pinecone_index.upsert(vectors=batch)
            logger.info(f"Upserted remaining {len(batch)} vectors")

        logger.info("Ingestion completed successfully")
        logger.info(f"Index stats: {pinecone_index.describe_index_stats()}")

    finally:
        db.close()
        logger.info("DB session closed")

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

