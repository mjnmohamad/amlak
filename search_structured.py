


# ─── search_structured.py ────────────────────────────────────────────────────
from sqlalchemy.orm import Session
from orm_models import Listing


class StructuredSearch:
    """
    فیلتر ساختاری روی جدول listings.
    پارامترها:
      • neighborhood : نام محله (عبارت جزئی یا کامل، case-insensitive)
      • max_price    : سقف قیمت فروش (دلار)
      • min_sqft     : حداقل متراژ ناخالص (gross_square_feet)
    """
    def __init__(self, SessionLocal):
        self.SessionLocal = SessionLocal

    # --------------------------------------------------------------------- #
    def search(
        self,
        neighborhood: str | None = None,
        max_price: float | None = None,
        min_sqft: float | None = None,
        limit: int = 20,
    ) -> list[dict]:
        session: Session = self.SessionLocal()
        try:
            q = session.query(Listing)

            if neighborhood:
                q = q.filter(Listing.neighborhood.ilike(f"%{neighborhood}%"))

            if max_price is not None:
                q = q.filter(Listing.sale_price <= max_price)

            if min_sqft is not None:
                q = q.filter(Listing.gross_square_feet >= min_sqft)

            rows = q.order_by(Listing.sale_price.asc()).limit(limit).all()

            return [
                {
                    "id":                r.id,
                    "borough":           r.borough,
                    "neighborhood":      r.neighborhood,
                    "address":           r.address,
                    "sale_price":        r.sale_price,
                    "gross_square_feet": r.gross_square_feet,
                    "year_built":        r.year_built,
                }
                for r in rows
            ]
        finally:
            session.close()




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