from app.backend.config import Base
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Users(Base):
    reg_date = Column(DateTime(timezone=True), server_default=func.now())
    tg_id = Column(BigInteger, unique=True)
    username = Column(String, unique=True)
    language = Column(String, default="en")
    balance = Column(Float, default=0)
    is_admin = Column(Boolean, default=False)
    source = Column(String, default=None)
    active = Column(Boolean, default=True)
    block_bot = Column(Boolean, default=False)
    hashed_password = Column(String)
    orders = relationship("Orders", backref="orders", lazy=True)
    payments = relationship("Payment", backref="payments", lazy=True)
    promos = relationship("UsersPromo", backref="user_promos", lazy=True)


class Payment(Base):
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tg_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"))
    amount = Column(Float, default=0)
    uuid = Column(String)
    confirmed = Column(Boolean, default=False)


class Orders(Base):
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tg_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"))
    quantity = Column(Integer, default=0)
    model = Column(String, ForeignKey("catalog.model", ondelete="CASCADE"))
    cc = Column(Integer, default=0)
    horsepower = Column(Integer, default=0)
    age = Column(String, default=None)
    purchase = Column(Float, default=0)
    is_paid = Column(Boolean, default=False)
    order_archive = Column(String, default=None)


class Manufacturer(Base):
    name = Column(String, unique=True)
    country = Column(String, default=None)
    models = relationship(
        "Catalog", back_populates="manufacturer_obj", lazy=True
    )


class Catalog(Base):
    manufacturer = Column(
        String, ForeignKey("manufacturer.name", ondelete="CASCADE")
    )
    type = Column(String, default=None)
    model = Column(String, unique=True)
    quantity = Column(Integer, default=0)
    sort_type = Column(String, default=None)
    items = relationship("Items", backref="items", lazy=True)
    type_orders = relationship("Orders", backref="type_orders", lazy=True)
    manufacturer_obj = relationship("Manufacturer", back_populates="models")


class Items(Base):
    model = Column(String, ForeignKey("catalog.model"))
    cc = Column(Integer, default=0)
    horsepower = Column(Integer, default=0)
    age = Column(String, default=None)
    price = Column(Float, default=0)
    row = Column(String, unique=True)


class Promo(Base):
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_promo = Column(Boolean, default=True)
    file = Column(String, default=None)
    downloads = Column(Integer, default=0)
    users = relationship("UsersPromo", backref="promo_users", lazy=True)


class UsersPromo(Base):
    __table_args__ = (UniqueConstraint("tg_id", "promo_id"),)
    tg_id = Column(
        "tg_id",
        BigInteger,
        ForeignKey("users.tg_id", ondelete="CASCADE"),
        nullable=False,
    )
    promo_id = Column(
        "promo_id",
        Integer,
        ForeignKey("promo.id", ondelete="CASCADE"),
        nullable=False,
    )
