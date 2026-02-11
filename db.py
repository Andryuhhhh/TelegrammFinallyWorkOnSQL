from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Words

def seed_words():
    session = SessionLocal()

    if session.query(Words).count() > 0:
        session.close()
        return  # чтобы не дублировать

    words = [
        ("Peace", "Мир"),
        ("Car", "Машина"),
        ("House", "Дом"),
        ("Water", "Вода"),
        ("Sun", "Солнце"),
        ("Book", "Книга"),
        ("Dog", "Собака"),
        ("Love", "Любовь"),
        ("Food", "Еда"),
        ("Friend", "Друг"),
    ]

    for en, ru in words:
        session.add(Words(target=en, translate=ru))

    session.commit()
    session.close()



engine = create_engine("sqlite:///words.db")
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
seed_words()