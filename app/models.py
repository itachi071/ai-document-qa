from sqlalchemy import Column, Integer, String
from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    description = Column(String)

    author = Column(String, nullable=False)

    filename = Column(String)