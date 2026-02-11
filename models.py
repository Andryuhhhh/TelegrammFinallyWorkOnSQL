from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(60), nullable=False)

    words = relationship("UserWords", back_populates="user")


class Words(Base):
    __tablename__ = "words"

    word_id = Column(Integer, primary_key=True)
    target = Column(String(60), nullable=False)
    translate = Column(String(60), nullable=False)

    users = relationship("UserWords", back_populates="word")


class UserWords(Base):
    __tablename__ = "user_words"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    word_id = Column(Integer, ForeignKey("words.word_id"), primary_key=True)
    is_learned = Column(Boolean, nullable=False, default=False)

    user = relationship("Users", back_populates="words")
    word = relationship("Words", back_populates="users")
