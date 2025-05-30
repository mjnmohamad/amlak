# search_structured.py
from typing import Optional, List, Dict
from pymongo.collection import Collection

class StructuredSearch:
    """
    جست‌وجوی ساختاری روی MongoDB.
    پارامترها (همگی اختیاری):
      • neighborhood / city  : رشتهٔ جست‌وجو (regex, case-insensitive)
      • max_price            : سقف قیمت
      • min_sqft / min_area  : حداقل متراژ
    """
    def __init__(self, collection: Collection):
        self.col = collection

    # ----------------------------------------------------
    def search(
        self,
        neighborhood: Optional[str] = None,
        city:         Optional[str] = None,
        max_price:    Optional[float] = None,
        min_sqft:     Optional[float] = None,
        min_area:     Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict]:
        query = {}

        if neighborhood or city:
            qtext            = neighborhood or city
            query["neighborhood"] = {"$regex": qtext, "$options": "i"}

        if max_price is not None:
            query["sale_price"] = {"$lte": max_price}

        min_size = min_sqft if min_sqft is not None else min_area
        if min_size is not None:
            query["gross_square_feet"] = {"$gte": min_size}

        cursor = self.col.find(query).sort("sale_price", 1).limit(limit)

        return [
            {
                "id":                 str(d.get("_id") or d.get("id")),
                "borough":            d.get("borough"),
                "neighborhood":       d.get("neighborhood"),
                "address":            d.get("address"),
                "sale_price":         d.get("sale_price"),
                "gross_square_feet":  d.get("gross_square_feet"),
                "year_built":         d.get("year_built"),
            }
            for d in cursor
        ]





# # فایل: search_structured.py
# # from sqlalchemy.orm import sessionmaker # دیگر لازم نیست، Session از config_manager می‌آید
# from orm_models import Listing # اصلاح import

# class StructuredSearch:
#     def __init__(self, SessionLocal_sql): # SessionLocal از config_manager
#         self.SessionLocal_sql = SessionLocal_sql

#     def search(self, city: str, max_price: float | None, min_area: float | None, limit: int = 20):
#         session = self.SessionLocal_sql()
#         try:
#             q = session.query(Listing)
#             if city: # اطمینان از اینکه city خالی نیست
#                  q = q.filter(Listing.city.ilike(f"%{city}%"))
#             if max_price is not None:
#                 q = q.filter(Listing.price <= max_price)
#             if min_area is not None:
#                 q = q.filter(Listing.area >= min_area)
#             results = q.limit(limit).all()
#             # تبدیل نتایج به دیکشنری برای سازگاری بهتر با لایه‌های بعدی
#             return [
#                 {
#                     "id": str(r.id),
#                     "title": r.title,
#                     "city": r.city,
#                     "price": r.price,
#                     "area": r.area,
#                     "rooms": r.rooms,
#                     "description_snippet": (r.description[:150] + "...") if r.description else ""
#                 } for r in results
#             ]
#         finally:
#             session.close()


# from sqlalchemy.orm import sessionmaker
# from orm_models import Listing

# class StructuredSearch:
#     def __init__(self, Session):
#         self.Session = Session

#     def search(self, city: str, max_price: float|None, min_area: float|None):
#         session = self.Session()
#         q = session.query(Listing).filter(Listing.city.ilike(f"%{city}%"))
#         if max_price is not None:
#             q = q.filter(Listing.price <= max_price)
#         if min_area is not None:
#             q = q.filter(Listing.area >= min_area)
#         results = q.limit(20).all()
#         return [r.__dict__ for r in results]
