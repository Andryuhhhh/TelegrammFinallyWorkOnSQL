import random
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Words


print("Start telegram bot...")

# ================== НАСТРОЙКИ ==================

TOKEN = "Тут нужно вставить свой токен из телеграмма"
state_storage = StateMemoryStorage()
bot = TeleBot(TOKEN, state_storage=state_storage)

engine = create_engine("sqlite:///words.db")
Session = sessionmaker(bind=engine)

# ================== СОСТОЯНИЯ ==================

class MyStates(StatesGroup):
    add_target = State()
    add_translate = State()
    delete_word = State()

# ================== КОМАНДЫ ==================

class Command:
    ADD_WORD = "Добавить слово ➕"
    DELETE_WORD = "Удалить слово 🗑"
    NEXT = "Дальше ⏭"

# ================== ЗАГРУЗКА СЛОВ ==================

def reload_words():
    global WORD_LIST
    session = Session()
    words = session.query(Words).all()
    session.close()
    WORD_LIST = [(w.word_id, w.target, w.translate) for w in words]

reload_words()

# ================== РАБОТА С БД ==================

def add_word_db(target_word, translate_word):
    session = Session()
    try:
        exists = session.query(Words).filter(Words.target == target_word).first()
        if exists:
            return False

        new_word = Words(target=target_word, translate=translate_word)
        session.add(new_word)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print("Ошибка при добавлении:", e)
        return False
    finally:
        session.close()


def delete_word_db(target_word):
    session = Session()
    try:
        word = session.query(Words).filter(Words.target == target_word).first()
        if word:
            session.delete(word)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print("Ошибка при удалении:", e)
        return False
    finally:
        session.close()

# ================== СОЗДАНИЕ КАРТОЧЕК ==================

@bot.message_handler(commands=["start", "cards"])
def create_cards(message):
    if not WORD_LIST:
        bot.send_message(message.chat.id, "⚠️ В базе нет слов.")
        return

    word_id, target_word, translate_word = random.choice(WORD_LIST)

    other_words = [w[1] for w in WORD_LIST if w[0] != word_id]
    others_count = min(3, len(other_words))
    others = random.sample(other_words, others_count)

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    buttons = [types.KeyboardButton(target_word)]
    buttons += [types.KeyboardButton(word) for word in others]

    random.shuffle(buttons)

    buttons.append(types.KeyboardButton(Command.NEXT))
    buttons.append(types.KeyboardButton(Command.ADD_WORD))
    buttons.append(types.KeyboardButton(Command.DELETE_WORD))

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        f"Выбери перевод слова:\n🇷🇺 {translate_word}",
        reply_markup=markup
    )

    bot.set_state(message.from_user.id, None, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["correct"] = target_word
        data["translate"] = translate_word


# ================== ДАЛЬШЕ ==================

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_card(message):
    create_cards(message)


# ================== ДОБАВЛЕНИЕ СЛОВ ==================

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word_start(message):
    bot.send_message(message.chat.id, "Введите английское слово:")
    bot.set_state(message.from_user.id, MyStates.add_target, message.chat.id)


@bot.message_handler(state=MyStates.add_target)
def get_target_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["new_target"] = message.text.lower()

    bot.send_message(message.chat.id, "Введите перевод:")
    bot.set_state(message.from_user.id, MyStates.add_translate, message.chat.id)


@bot.message_handler(state=MyStates.add_translate)
def get_translate_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target = data["new_target"]
        translate = message.text.lower()

    if add_word_db(target, translate):
        reload_words()
        bot.send_message(message.chat.id, f"✅ Слово '{target}' добавлено!")
    else:
        bot.send_message(message.chat.id, "⚠️ Такое слово уже существует!")

    bot.delete_state(message.from_user.id, message.chat.id)


# ================== УДАЛЕНИЕ СЛОВ ==================

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word_start(message):
    bot.send_message(message.chat.id, "Введите английское слово для удаления:")
    bot.set_state(message.from_user.id, MyStates.delete_word, message.chat.id)


@bot.message_handler(state=MyStates.delete_word)
def confirm_delete(message):
    target = message.text.lower()

    if delete_word_db(target):
        reload_words()
        bot.send_message(message.chat.id, f"🗑 Слово '{target}' удалено.")
    else:
        bot.send_message(message.chat.id, f"🚫 Слово '{target}' не найдено.")

    bot.delete_state(message.from_user.id, message.chat.id)


# ================== ПРОВЕРКА ОТВЕТА ==================

@bot.message_handler(func=lambda message: True, content_types=["text"])
def check_answer(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        correct = data.get("correct")
        translate = data.get("translate")

    if not correct:
        return

    if message.text == correct:
        bot.send_message(
            message.chat.id,
            f"✅ Верно!\n{correct} -> {translate}"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Неверно.\nПравильный ответ: {correct}"
        )


# ================== ЗАПУСК ==================

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)
