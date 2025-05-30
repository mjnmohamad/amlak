


# ─── search_semantic.py ───────────────────────────────────────────────────────
from langchain.vectorstores import Pinecone as PineconeStore

class SemanticSearch:
    """
    پرس‌وجوی معنایی روی Pinecone  (Vector-DB).
    متادیتاهایی که در ingest.py ذخیره می‌کنیم باید دقیقاً همین کلیدها را داشته باشد.
    """
    def __init__(self, vector_store: PineconeStore):
        self.vs = vector_store

    # --------------------------------------------------------------------- #
    def search(self,
               query: str,
               k: int = 5,
               filter_dict: dict | None = None) -> list[dict]:
        """
        filter_dict می‌تواند هرکدام از فیلدهای متادیتا مثل
        {'borough': 1, 'sale_price': {'$lte': 1_000_000}}
        باشد (سینتکس Pinecone).
        """
        docs = self.vs.similarity_search(query=query,
                                         k=k,
                                         filter=filter_dict or {})
        results: list[dict] = []
        for d in docs:
            meta = d.metadata or {}
            results.append({
                "id":            meta.get("id"),
                "borough":       meta.get("borough"),
                "neighborhood":  meta.get("neighborhood"),
                "address":       meta.get("address"),
                "sale_price":    meta.get("sale_price"),
                "gross_sqft":    meta.get("gross_square_feet"),
                "year_built":    meta.get("year_built"),
                "snippet": (
                    (d.page_content or "")[:200] + "…"
                    if d.page_content else meta.get("snippet", "")
                ),
            })
        return results




# # ─── search_semantic.py ───────────────────────────────────────────────────────
# from langchain.vectorstores import Pinecone as PineconeStore

# class SemanticSearch:
#     """
#     لایهٔ بازیابی معنایی روی Vector DB.
#     اگر هنگام ساخت vector_store  توابع embedding داده شده باشد،
#     similarity_search خودش embedding پرسش را انجام می‌دهد.
#     """
#     def __init__(self, vector_store: PineconeStore):
#         self.vs = vector_store

#     # -------------------------------------------------------------------------
#     def search(self, query: str, k: int = 5, filter_dict: dict | None = None):
#         docs = self.vs.similarity_search(query=query, k=k, filter=filter_dict or {})
#         out  = []
#         for d in docs:
#             meta = d.metadata or {}
#             out.append({
#                 "id":    meta.get("id", "N/A"),
#                 "title": meta.get("title", "N/A"),
#                 "city":  meta.get("city",  "N/A"),
#                 "price": meta.get("price"),
#                 "area":  meta.get("area"),
#                 "rooms": meta.get("rooms"),
#                 "description_snippet": (
#                     d.page_content[:200] + "…" if d.page_content else
#                     meta.get("original_description_snippet", "")
#                 )
#             })
#         return out



