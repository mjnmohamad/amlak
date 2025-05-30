
from typing import Optional, List, Dict
from pymongo.collection import Collection

class StructuredSearch:
    """
    جستجوی ساختاری روی MongoDB با پشتیبانی از فیلترهای عددی ذخیره شده به صورت رشته‌ای
    پارامترها (همگی اختیاری):
      • neighborhood / city  : رشتهٔ جستجو (regex, case-insensitive)
      • max_price            : سقف قیمت (قاعدتاً فیلد SALE PRICE به‌صورت رشته با جداکننده هزار)
      • min_sqft / min_area  : حداقل مساحت (فیلد GROSS SQUARE FEET به‌صورت رشته با جداکننده هزار)
      • limit                : حداکثر تعداد نتایج
    خروجی:
      • id, borough, neighborhood, address,
        sale_price (int), gross_square_feet (int), year_built
    """
    def __init__(self, collection: Collection):
        self.col = collection

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        # حذف جداکننده‌های هزار و تبدیل به عدد
        try:
            return int(value.replace(",", ""))
        except Exception:
            return None

    def search(
        self,
        neighborhood: Optional[str] = None,
        city:         Optional[str] = None,
        max_price:    Optional[float] = None,
        min_sqft:     Optional[float] = None,
        min_area:     Optional[float] = None,
        limit:        int            = 20,
    ) -> List[Dict]:
        # کوئری Mongo فقط بر اساس regex محله/شهر
        query: Dict = {}
        text = neighborhood or city
        if text:
            query["NEIGHBORHOOD"] = {"$regex": text, "$options": "i"}

        cursor = self.col.find(query)

        results: List[Dict] = []
        target_size = min_sqft if min_sqft is not None else min_area

        for doc in cursor:
            # تبدیل رشته‌های عددی به int
            sale_raw = doc.get("SALE PRICE")
            sqft_raw = doc.get("GROSS SQUARE FEET")
            sale_val = self._parse_int(sale_raw)
            sqft_val = self._parse_int(sqft_raw)

            # اعمال فیلتر عددی
            if max_price is not None and (sale_val is None or sale_val > max_price):
                continue
            if target_size is not None and (sqft_val is None or sqft_val < target_size):
                continue

            # افزودن به نتایج
            results.append({
                "id":                 str(doc.get("_id")),
                "borough":            doc.get("BOROUGH"),
                "neighborhood":       doc.get("NEIGHBORHOOD"),
                "address":            doc.get("ADDRESS"),
                "sale_price":         sale_val,
                "gross_square_feet":  sqft_val,
                "year_built":         doc.get("YEAR BUILT"),
            })

            if len(results) >= limit:
                break

        # مرتب‌سازی بر اساس قیمت
        results.sort(key=lambda x: (x.get("sale_price") or 0))
        return results



# from typing import Optional, List, Dict
# from pymongo.collection import Collection

# class StructuredSearch:
#     """
#     جست‌وجوی ساختاری روی MongoDB.
#     پارامترها (همگی اختیاری):
#       • neighborhood / city  : رشتهٔ جست‌وجو (regex, case-insensitive)
#       • max_price            : سقف قیمت (SALE PRICE)
#       • min_sqft / min_area  : حداقل مساحت (GROSS SQUARE FEET)
#       • limit                : حداکثر تعداد نتایج
#     فیلدهای مسترجع در خروجی:
#       • id, borough, neighborhood, address,
#         sale_price, gross_square_feet, year_built
#     """
#     def __init__(self, collection: Collection):
#         self.col = collection

#     def search(
#         self,
#         neighborhood: Optional[str] = None,
#         city:         Optional[str] = None,
#         max_price:    Optional[float] = None,
#         min_sqft:     Optional[float] = None,
#         min_area:     Optional[float] = None,
#         limit:        int            = 20,
#     ) -> List[Dict]:
#         # ساخت کوئری
#         query: Dict = {}

#         # نام محله یا شهر (case-insensitive regex)
#         text = neighborhood or city
#         if text:
#             query["NEIGHBORHOOD"] = {"$regex": text, "$options": "i"}

#         # فیلتر سقف قیمت
#         if max_price is not None:
#             query["SALE PRICE"] = {"$lte": max_price}

#         # فیلتر حداقل مساحت
#         size = min_sqft if min_sqft is not None else min_area
#         if size is not None:
#             query["GROSS SQUARE FEET"] = {"$gte": size}

#         # اجرای کوئری و مرتب‌سازی بر اساس قیمت صعودی
#         cursor = (
#             self.col
#                 .find(query)
#                 .sort([("SALE PRICE", 1)])
#                 .limit(limit)
#         )

#         # نگاشت اسناد به دیکشنری خروجی
#         results: List[Dict] = []
#         for doc in cursor:
#             results.append({
#                 "id":                 str(doc.get("_id")),
#                 "borough":            doc.get("BOROUGH"),
#                 "neighborhood":       doc.get("NEIGHBORHOOD"),
#                 "address":            doc.get("ADDRESS"),
#                 "sale_price":         doc.get("SALE PRICE"),
#                 "gross_square_feet":  doc.get("GROSS SQUARE FEET"),
#                 "year_built":         doc.get("YEAR BUILT"),
#             })

#         return results




# # search_structured.py
# from typing import Optional, List, Dict
# from pymongo.collection import Collection

# class StructuredSearch:
#     """
#     جست‌وجوی ساختاری روی MongoDB.
#     پارامترها (همگی اختیاری):
#       • neighborhood / city  : رشتهٔ جست‌وجو (regex, case-insensitive)
#       • max_price            : سقف قیمت
#       • min_sqft / min_area  : حداقل متراژ
#     """
#     def __init__(self, collection: Collection):
#         self.col = collection

#     # ----------------------------------------------------
#     def search(
#         self,
#         neighborhood: Optional[str] = None,
#         city:         Optional[str] = None,
#         max_price:    Optional[float] = None,
#         min_sqft:     Optional[float] = None,
#         min_area:     Optional[float] = None,
#         limit: int = 20,
#     ) -> List[Dict]:
#         query = {}

#         if neighborhood or city:
#             qtext            = neighborhood or city
#             query["neighborhood"] = {"$regex": qtext, "$options": "i"}

#         if max_price is not None:
#             query["sale_price"] = {"$lte": max_price}

#         min_size = min_sqft if min_sqft is not None else min_area
#         if min_size is not None:
#             query["gross_square_feet"] = {"$gte": min_size}

#         cursor = self.col.find(query).sort("sale_price", 1).limit(limit)

#         return [
#             {
#                 "id":                 str(d.get("_id") or d.get("id")),
#                 "borough":            d.get("borough"),
#                 "neighborhood":       d.get("neighborhood"),
#                 "address":            d.get("address"),
#                 "sale_price":         d.get("sale_price"),
#                 "gross_square_feet":  d.get("gross_square_feet"),
#                 "year_built":         d.get("year_built"),
#             }
#             for d in cursor
#         ]





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
