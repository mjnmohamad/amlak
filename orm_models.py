


# # ─── orm_models.py ───────────────────────────────────────────────────────────
# from sqlalchemy import (
#     Column, Integer, String, Float, Text, Date, MetaData
# )
# from sqlalchemy.orm import declarative_base
# from config import engine  # استفاده از همان Engine پروژه

# Base     = declarative_base()
# metadata = MetaData()

# class Listing(Base):
#     __tablename__ = "listings"  # چون rename کردی

#     id                      = Column(Integer, primary_key=True)
#     borough                = Column(Integer)
#     neighborhood           = Column(String(100))
#     building_class_category = Column(String(100))
#     tax_class_present      = Column(String(10))
#     block                  = Column(Integer)
#     lot                    = Column(Integer)
#     easement               = Column(String(10))
#     building_class_present = Column(String(10))
#     address                = Column(String(200))
#     apartment_number       = Column(String(50))
#     zip_code               = Column(String(10))
#     residential_units      = Column(Integer)
#     commercial_units       = Column(Integer)
#     total_units            = Column(Integer)
#     land_square_feet       = Column(Integer)
#     gross_square_feet      = Column(Integer)
#     year_built             = Column(Integer)
#     tax_class_sale         = Column(String(10))
#     building_class_sale    = Column(String(10))
#     sale_price             = Column(Float)
#     sale_date              = Column(String(20))  # یا Date اگر فرمت اصلاح شده

#     def __repr__(self):
#         return f"<Listing(id={self.id}, address='{self.address}', sale_price={self.sale_price})>"





# # ─── orm_models.py ───────────────────────────────────────────────────────────
# from sqlalchemy import (
#     Column, Integer, String, Float, Text, MetaData
# )
# from sqlalchemy.orm     import declarative_base
# from config             import engine   # ← همان Engine واحد

# Base      = declarative_base()
# metadata  = MetaData()

# class Listing(Base):
#     __tablename__ = "listings"

#     id          = Column(Integer, primary_key=True, index=True)
#     title       = Column(String(255),  index=True)
#     city        = Column(String(100),  index=True)
#     zone        = Column(String(100),  nullable=True, index=True)
#     price       = Column(Float,        nullable=True, index=True)
#     price_per_m = Column(Float,        nullable=True)
#     area        = Column(Float,        nullable=True, index=True)
#     rooms       = Column(Integer,      nullable=True)
#     floor       = Column(Integer,      nullable=True)
#     amenities   = Column(Text,         nullable=True)
#     description = Column(Text,         nullable=False)
#     images_url  = Column(Text,         nullable=True)
#     metadata_extra = Column(Text,      nullable=True)  # ستون JSON آزاد

#     def __repr__(self):
#         return f"<Listing(id={self.id}, title='{self.title}', city='{self.city}')>"

# # اگر فقط در محیط dev قصد ساخت جدول دارید، این خط را نگه‌دارید
# # (در production بهتر است Alembic استفاده شود)
# if __name__ == "__main__":
#     Base.metadata.create_all(bind=engine)



# # فایل: orm_models.py

# import os
# from sqlalchemy import create_engine, Column, Integer, String, Float, Text, MetaData
# from sqlalchemy.orm import sessionmaker, declarative_base
# from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL environment variable not set")

# Base = declarative_base()
# metadata = MetaData()

# class Listing(Base): # [cite: 56]
#     __tablename__ = "listings" # [cite: 7, 36, 56] نام جدول آگهی‌ها

#     id = Column(Integer, primary_key=True, index=True) # [cite: 7, 36, 56]
#     title = Column(String(255), index=True) # [cite: 7]
#     city = Column(String(100), index=True) # [cite: 7, 36, 56]
#     zone = Column(String(100), nullable=True, index=True) # [cite: 7] محله
#     price = Column(Float, nullable=True, index=True) # [cite: 7, 36, 56]
#     price_per_m = Column(Float, nullable=True) # [cite: 7] قیمت هر متر
#     area = Column(Float, nullable=True, index=True) # [cite: 7, 36, 56] متراژ
#     rooms = Column(Integer, nullable=True) # [cite: 7, 36, 56] تعداد اتاق
#     floor = Column(Integer, nullable=True) # [cite: 7] طبقه
#     amenities = Column(Text, nullable=True) # [cite: 7] امکانات
#     description = Column(Text, nullable=False) # [cite: 7, 36, 56]
#     images_url = Column(Text, nullable=True) # [cite: 56] (می‌تواند لیستی از URLها به صورت JSON باشد)
#     metadata_extra = Column(Text, nullable=True) # [cite: 36] (برای ذخیره اطلاعات اضافی به صورت JSON، تغییر نام از metadata)

#     def __repr__(self):
#         return f"<Listing(id={self.id}, title='{self.title}', city='{self.city}')>"

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# def get_db_session():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# برای ایجاد جدول در دیتابیس (یکبار در ابتدای پروژه اجرا شود اگر جدول وجود ندارد)
# if __name__ == "__main__":
#     Base.metadata.create_all(bind=engine)
#     print("Tables created (if they didn't exist).")
