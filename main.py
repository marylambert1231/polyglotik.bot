
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext, CallbackQueryHandler
import os
import asyncio

'''                                       НАЧАЛО КОДА                                        '''

# Инициализация базы данных
def init_db(user_id):
    db_name = 'polyglotik.db'  # Имя базы данных с уникальным ID пользователя
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Создание таблиц для пользователей, групп, слов и настроек
    c.execute('''CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER UNIQUE, 
        username TEXT
        )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS Groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )''')

    # Создание таблицы Words
    c.execute('''CREATE TABLE IF NOT EXISTS Words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER,
        foreign_word TEXT,
        russian_word TEXT,
        user_id INTEGER,
        FOREIGN KEY(group_id) REFERENCES Groups(id),
        FOREIGN KEY(user_id) REFERENCES Users(user_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_id INTEGER, 
        language TEXT, 
        FOREIGN KEY(user_id) REFERENCES Users(user_id))''')

    conn.commit()
    conn.close()


def get_user_db(user_id):
    db_name = 'polyglotik.db'
    return sqlite3.connect(db_name)

# Команда /start для запуска бота
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id  # Получаем уникальный ID пользователя
    username = update.message.from_user.first_name  # Получаем имя пользователя

    init_db(user_id)

    # Добавляем пользователя в базу данных, если его еще нет
    conn = get_user_db(user_id)  # Передаем user_id в get_user_db
    c = conn.cursor()
    c.execute("SELECT id FROM Users WHERE user_id = ?", (user_id,))
    user = c.fetchone()

    if not user:
        # Если пользователя нет в базе, добавляем его
        c.execute("INSERT INTO Users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()

    conn.close()

    # Приветствие пользователя
    keyboard = [
        [KeyboardButton("Добавить слова➕"), KeyboardButton("Поиграем🧩"), KeyboardButton("Список слов📋")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Привет, {username}! Добро пожаловать в Полиглотик 📚 Чем займемся?", reply_markup=reply_markup)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка сообщений от Telegram через вебхук"""
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, application.bot)
    application.update_queue.put(update)
    return 'ok', 200

# Команда для возврата В меню✨
async def menu(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("Добавить слова➕"), KeyboardButton("Поиграем🧩"), KeyboardButton("Список слов📋")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Вы вернулись в меню✨ Чем займемся??", reply_markup=reply_markup)

async def return_to_menu(update: Update, context: CallbackContext):
    """Функция для возврата в главное меню."""
    await menu(update, context)  # Отправляем пользователя в главное меню
    return ConversationHandler.END  # Завершаем текущую операцию

'''                                       ДОБАВИТЬ СЛОВА                                        '''


ADD_WORDS_GROUP = range(1)

# Этап добавления слов (выбор группы)
async def add_words_group(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    conn = sqlite3.connect('polyglotik.db')
    c = conn.cursor()

    # Извлекаем названия групп пользователя
    c.execute('SELECT name FROM Groups WHERE user_id = ?', (user_id,))
    groups = c.fetchall()
    conn.close()

    if groups:
        # Если группы есть, показываем их в виде кнопок
        keyboard = [[KeyboardButton(group[0])] for group in groups]
        # Кнопка для возврата В меню✨
        keyboard.append([KeyboardButton("В меню✨")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "Чтобы добавить слово, *выберите группу* или *напишите название новой* с клавиатуры:",
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
    else:
        # Если групп нет, просим ввести название новой группы
        keyboard = [[KeyboardButton("В меню✨")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Не смог найти *группы* 🥺 Пожалуйста, введите *название новой группы* с клавиатуры:",
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )

    return 1  # Переход к следующему этапу

# Этап добавления слова на иностранном языке
async def add_words_foreign(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Используем новую функцию для возврата В меню✨

    # Сохраняем выбранную группу
    context.user_data['group'] = update.message.text

    # Скрываем кнопки с группами и отображаем только кнопку Меню
    keyboard = [[KeyboardButton("В меню✨")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Введите слово на *иностранном<* языке:", parse_mode="MarkdownV2", reply_markup=reply_markup)
    return 2  # Переход к следующему этапу


# Этап добавления перевода на русский
async def add_words_russian(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Используем новую функцию для возврата В меню✨

    context.user_data['foreign_word'] = update.message.text  # Сохраняем слово на иностранном
    await update.message.reply_text("Введите *перевод на русском*:", parse_mode="MarkdownV2")
    return 3


# Сохранение слова в базу данных
async def save_word(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Используем новую функцию для возврата В меню✨

    russian_word = update.message.text
    group = context.user_data['group']
    foreign_word = context.user_data['foreign_word']
    user_id = update.message.from_user.id

    conn = sqlite3.connect('polyglotik.db')
    c = conn.cursor()

    # Если группа новая, создаем её
    c.execute("SELECT id FROM Groups WHERE name = ? AND user_id = ?", (group, user_id))
    group_id = c.fetchone()

    if not group_id:
        # Если группа новая, создаём её
        c.execute("INSERT INTO Groups (name, user_id) VALUES (?, ?)", (group, user_id))
        group_id = c.lastrowid
    else:
        group_id = group_id[0]

    # Добавляем слово в базу
    c.execute(
        "INSERT INTO Words (group_id, foreign_word, russian_word) VALUES (?, ?, ?)",
        (group_id, foreign_word, russian_word)
    )
    
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Слово '{foreign_word}' успешно добавлено в группу '{group}' 🎉")

    # Переход к первому этапу добавления нового слова
    await add_words_group(update, context)
    return 1


'''                                       Список  СЛОВ И ГРУПП                                        '''


# Команда для списка слов
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
import sqlite3

DELETE_ACTION, DELETE_WORD_OR_GROUP, DELETE_WORD, DELETE_GROUP = range(4, 8)

# Этап для вывода списка слов
async def list_words(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'
    
    
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
            SELECT g.name, w.foreign_word, w.russian_word
            FROM Groups g
            LEFT JOIN Words w ON g.id = w.group_id
            WHERE g.user_id = ?
        """, (user_id,))
    words = c.fetchall()
    conn.close()

    # Проверка на кнопку "В меню✨"
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Используем новую функцию для возврата В меню✨

    # Если есть слова в базе
    if words:
        grouped_words = {}

        # Группируем слова по группе
        for group, foreign_word, russian_word in words:
            if group not in grouped_words:
                grouped_words[group] = []
            if foreign_word is not None and russian_word is not None:
                grouped_words[group].append(f"{foreign_word} - {russian_word}")

        # Формируем сообщение
        message = "Список слов📋 :\n\n"
        for group, word_list in grouped_words.items():
            message += f"ГРУППА  {group}\n"
            if word_list:
                for word in word_list:
                    message += f"                  {word}\n"
            else:
                message += "                  (Тут пусто)\n"
            message += "\n"  # Добавляем новую строку после каждой группы, чтобы они не сливались
        await update.message.reply_text(message)
    
        

        # Скрываем все кнопки, кроме "В меню✨" и добавляем кнопку для удаления
        keyboard = [
            [KeyboardButton("Удалить слово или группу")],
            [KeyboardButton("В меню✨")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Хотите скорректировать список?", reply_markup=reply_markup)

        return DELETE_ACTION  # Переход к следующему этапу

    # Если нет слов в базе, предлагаем Добавить слова➕ слово
    keyboard = [
        [KeyboardButton("Добавить слово➕")],
        [KeyboardButton("В меню✨")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
    "Не нашел слов в Вашей базе 🥺 Хотите добавить слова?",
    reply_markup=reply_markup
)

# Устанавливаем обработчик для кнопки "Добавить слова➕ слово"
    return ADD_WORDS_GROUP

"---------------------"
async def delete_word_or_group(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Используем новую функцию для возврата В меню✨
    if update.message.text == "Удалить слово или группу":
        # Отображаем кнопки для выбора действия
        keyboard = [
            [KeyboardButton("Удалить слово")],
            [KeyboardButton("Удалить группу")],
            [KeyboardButton("В меню✨")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Что хотите удалить?:", reply_markup=reply_markup)
        return DELETE_WORD_OR_GROUP  # Переход к следующему этапу


"""------------------------"""
async def delete_word(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'
    
    
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT g.name, w.id, w.foreign_word, w.russian_word
        FROM Words w
        JOIN Groups g ON w.group_id = g.id
        WHERE g.user_id = ?
    """, (user_id,))
    words = c.fetchall()
    conn.close()

    if words:
        # Группируем слова по группе
        grouped_words = {}
        for group, word_id, foreign_word, russian_word in words:
            if group not in grouped_words:
                grouped_words[group] = []
            grouped_words[group].append((word_id, foreign_word, russian_word))

        # Формируем сообщение с группированными словами
        message = "Какое слово нужно удалить? Введите номер слова с клавиатуры:\n \n"
        idx = 1
        context.user_data['delete_words'] = []  # Список слов📋 для сохранения id слов
        for group, word_list in grouped_words.items():
            message += f"ГРУППА  {group}\n"
            for word_id, foreign_word, russian_word in word_list:
                message += f"                  {idx}. {foreign_word} - {russian_word}\n"
                context.user_data['delete_words'].append(word_id)  # Сохраняем id слов в порядке отображения
                idx += 1
                                                

        # Кнопка для возврата В меню✨
        keyboard = [[KeyboardButton("В меню✨")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        # Отправляем сообщение с кнопкой "В меню✨"
        await update.message.reply_text(message, reply_markup=reply_markup)
        return DELETE_WORD
    else:
        # Если нет слов для удаления
        await update.message.reply_text("Не нашел слов для удаления 🥺", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def confirm_delete_word(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'

    try:
        selected_idx = int(update.message.text) - 1  # Преобразуем ввод пользователя в индекс
        if selected_idx < 0 or selected_idx >= len(context.user_data['delete_words']):
            raise IndexError

        word_id = context.user_data['delete_words'][selected_idx]

        # Удаляем слово из базы данных
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("DELETE FROM Words WHERE id = ?", (word_id,))
        conn.commit()
        conn.close()

        # Отправляем сообщение о том, что слово удалено
        await update.message.reply_text("Слово успешно удалено 🎉")

        # После удаления снова загружаем Список слов📋 слов
        return await list_words(update, context)  # Перезапускаем отображение списка слов

    except (ValueError, IndexError):
        await update.message.reply_text("Такого номера нет в списке 🥺 Пожалуйста, выберите существующий номер слова.")
        return DELETE_WORD

"""------------------------------"""
async def delete_group(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'
    
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)
    
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute(f'SELECT id, name FROM Groups WHERE user_id = ?', (user_id,))  # Получаем id и название групп
    groups = c.fetchall()
    conn.close()

    if groups:
        # Создание кнопок с названиями групп
        keyboard = [[KeyboardButton(group_name)] for _, group_name in groups]
        keyboard.append([KeyboardButton("В меню✨")])  # Кнопка для возврата В меню✨

        # Отправляем сообщение с кнопками
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Какую группу нужно удалить?", reply_markup=reply_markup)

        # Сохраняем Список слов📋 групп в context для последующего использования
        context.user_data['delete_groups'] = {group_name: group_id for group_id, group_name in groups}
        return DELETE_GROUP
    else:
        await update.message.reply_text("Не нашел групп для удаления 🥺")
        return ConversationHandler.END

async def confirm_delete_group(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'

    selected_group = update.message.text  # Получаем название группы из текста сообщения

    if selected_group == "В меню✨":
        await menu(update, context)  # Возврат в главное меню
        return ConversationHandler.END

    group_map = context.user_data.get('delete_groups', {})
    group_id = group_map.get(selected_group)

    if not group_id:
        await update.message.reply_text("Выберите группу из предложенного списка.")
        return DELETE_GROUP

    # Удаление группы и её слов из базы данных
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("DELETE FROM Words WHERE group_id = ?", (group_id,))
    c.execute("DELETE FROM Groups WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()

    # Подтверждающее сообщение
    await update.message.reply_text(f"Группа '{selected_group}' и все её слова успешно удалены.")

    return await list_words(update, context)
  
'''-----------------'''


# Отмена и выход В меню✨
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Действие отменено.")
    return await return_to_menu(update, context)

# Команда для удаления всех групп
async def delete_all(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'
    
    
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Удаляем Учить все слова
    c.execute("DELETE FROM Words")
    
    # Удаляем все группы
    c.execute("DELETE FROM Groups")
    conn.commit()
    conn.close()

    await update.message.reply_text("Все группы и их слова были успешно удалены!")


from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
import random
'''--------------------'''

'''                                       Поиграем🧩 СЛОВА                                        '''

# Новые стадии для игры
import random

GAME_START, GAME_QUESTION, GAME_CHECK_ANSWER, GAME_END = range(1, 5)

# Этап выбора группы или всех слов
async def play(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'
    
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
   
    keyboard = [
        [KeyboardButton("Учить все слова"), KeyboardButton("Учить слова по группам")],
        [KeyboardButton("В меню✨")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать в игру 🧩 \nЗдесь можно тренировать знание всех слов или слов из определенной группы. \nОтветь правильно за 3 попытки или проиграешь 😈",
        reply_markup=reply_markup
    )
    return GAME_START

# Этап выбора группы
async def select_group_or_all(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    db_name = 'polyglotik.db'

    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Используем новую функцию для возврата В меню✨

    if update.message.text == "Учить слова по группам":
        # Получаем Список слов📋 групп
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("SELECT name FROM Groups WHERE user_id = ?", (user_id,))
        groups = c.fetchall()
        conn.close()

        

        if groups:
            keyboard = [[KeyboardButton(group[0])] for group in groups]
            keyboard.append([KeyboardButton("В меню✨")])  # Кнопка для возврата В меню✨
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "Какую группу выбрать для игры?",
                reply_markup=reply_markup
            )
            return GAME_START
        else:
            await update.message.reply_text("Я не нашел у Вас групп 🥺 Вы можете добавить их через меню")
            return ConversationHandler.END

    elif update.message.text == "Учить все слова":
        # Получаем Учить все слова для игры
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("""
            SELECT foreign_word, russian_word 
            FROM Words 
            JOIN Groups ON Words.group_id = Groups.id 
            WHERE Groups.user_id = ?
        """, (user_id,))
        words = c.fetchall()
        conn.close()

        # Запускаем игру с этими словами
        if words:
            random.shuffle(words)  # Перемешиваем список слов
            context.user_data['game_words'] = words
            context.user_data['used_words'] = set()  # Слово, которое уже было задано
            context.user_data['current_word_index'] = 0
            context.user_data['used_questions'] = set()  # Для отслеживания пар слово-перевод
            await ask_question(update, context)
            return GAME_QUESTION
        else:
            await update.message.reply_text("Я не нашел слов для игры 🥺 Вы можете добавить их через меню")
            return ConversationHandler.END

    # Если выбрана группа
    else:
        group_name = update.message.text
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        c.execute("""
            SELECT foreign_word, russian_word 
            FROM Words 
            JOIN Groups ON Words.group_id = Groups.id 
            WHERE Groups.name = ? AND Groups.user_id = ?
        """, (group_name, user_id))
        words = c.fetchall()
        conn.close()

        if words:
            random.shuffle(words)  # Перемешиваем список слов
            context.user_data['game_words'] = words
            context.user_data['used_words'] = set()  # Слово, которое уже было задано
            context.user_data['current_word_index'] = 0
            context.user_data['used_questions'] = set()  # Для отслеживания пар слово-перевод
            await ask_question(update, context)
            return GAME_QUESTION
        else:
            await update.message.reply_text(f"Я не нашел слов в группе '{group_name}' 🥺")
            # Повторный вызов select_group_or_all после сообщения
            keyboard = [
                [KeyboardButton("Учить все слова"), KeyboardButton("Учить слова по группам")],
                [KeyboardButton("В меню✨")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "Какую группу выбрать для игры?",
                reply_markup=reply_markup
            )
            return GAME_START

# Этап игры (задается вопрос)
async def ask_question(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)  # Возврат в меню

    # Инициализируем переменные
    words = context.user_data.get('game_words', [])
    question_queue = context.user_data.get('question_queue', [])
    
    # Если очередь вопросов пуста, создаем ее
    if not question_queue:
        # Создаем вопросы с учетом направления
        for word_pair in words:
            question_queue.append((word_pair[0], word_pair[1], "foreign_to_russian"))  # С иностранного на русский
            question_queue.append((word_pair[1], word_pair[0], "russian_to_foreign"))  # С русского на иностранный
        random.shuffle(question_queue)  # Перемешиваем вопросы

    # Если все вопросы заданы, завершаем игру
    if not question_queue:
        
        await update.message.reply_text("Упс. Кажется, слова закончились. Поздравляю! 🎉")
        sticker = "CAACAgIAAxkBAAELQFBncC1h6OjAnenr-yZj1HqW0RHxmAACVioAAoFtsEnew0qW1q4NCTYE"
        await update.message.reply_sticker(sticker)
        return GAME_END

    # Извлекаем текущий вопрос из очереди
    question, correct_answer, question_type = question_queue.pop(0)
    context.user_data['question_queue'] = question_queue  # Сохраняем обновленную очередь
    context.user_data['correct_answer'] = correct_answer  # Сохраняем правильный ответ

    # Отправляем вопрос пользователю
    if question_type == "foreign_to_russian":
        await update.message.reply_text(f"Как перевести слово - {question} ?")
    else:
        await update.message.reply_text(f"Как перевести слово - {question} ?")

    # Кнопка для возврата в меню
    keyboard = [[KeyboardButton("В меню✨")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Введите Ваш ответ с клавиатуры", reply_markup=reply_markup)

    return GAME_CHECK_ANSWER


# Этап проверки ответа
async def check_answer(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await return_to_menu(update, context)

    correct_answer = context.user_data['correct_answer']
    user_answer = update.message.text.strip().lower()

    if 'incorrect_attempts' not in context.user_data:
        context.user_data['incorrect_attempts'] = 0

    if user_answer == correct_answer.lower():
        context.user_data['incorrect_attempts'] = 0
        await update.message.reply_text("Правильно✅")

        # Проверяем, какие вопросы были заданы, чтобы избежать повторов
        if len(context.user_data['question_queue']) == 0:
            await update.message.reply_text("Упс. Кажется, слова закончились.\n         Поздравляю! 🎉")
            sticker = "CAACAgIAAxkBAAELQFBncC1h6OjAnenr-yZj1HqW0RHxmAACVioAAoFtsEnew0qW1q4NCTYE"  # Пример стикера
            await update.message.reply_sticker(sticker)
            return await play(update, context)
        # Переходим к следующему вопросу
        return await ask_question(update, context)
    else:
        context.user_data['incorrect_attempts'] += 1
        remaining_attempts = 3 - context.user_data['incorrect_attempts']

        if context.user_data['incorrect_attempts'] >= 3:
            await update.message.reply_text(f"Неправильно ❌ Попытки закончились. Правильный ответ - {correct_answer}. ")
            return await game_end(update, context)
        else:
            await update.message.reply_text(f"Неправильно ❌ Попробуйте снова.\nОсталось попыток: {remaining_attempts}")
            return GAME_CHECK_ANSWER



    # Переход к следующему слову
    return await ask_question(update, context)

# Завершение игры
async def game_end(update: Update, context: CallbackContext):
    if update.message.text == "В меню✨":
        return await play(update, context)  # Используем новую функцию для возврата В меню✨

    # Отправляем стикер (замените ссылку на стикер на вашу)
    sticker = "CAACAgIAAxkBAAELQExncCyUMaxoz_1Tc6yhwaijmY_7xgACgSwAArMIIEvBatc5UbVj1DYE"  # Пример стикера
    await update.message.reply_sticker(sticker)

    # Завершаем игру и возвращаемся В меню✨
    return await play(update, context)


"""------------------------------------------------"""

import os
from telegram.ext import CallbackQueryHandler
# Основной код для бота
def main():
    
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден. Проверьте переменные окружения!")
    
    application = Application.builder().token(token).build()

    play_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Поиграем🧩$'), play)],
        states={
            GAME_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_group_or_all)],
            GAME_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
            GAME_CHECK_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
            GAME_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_end)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(play_conversation)
    
    
    # Команда /start
    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("delete_all", delete_all))

    # Создание конверсации для добавления слов
    add_word_conversation = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex('^Добавить слово➕$'), add_words_group),  # Для кнопки "Добавить слова➕ слово"
        MessageHandler(filters.Regex('^Добавить слова➕$'), add_words_group),  # Для основного меню
    ],
    states={
        1: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_words_foreign)],
        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_words_russian)],
        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_word)],
    },
    fallbacks=[MessageHandler(filters.Regex('^В меню✨$'), return_to_menu)],
)


    application.add_handler(add_word_conversation)

    # Обработка команды списка слов
    
    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Список слов📋$'), list_words)],
        states={
            DELETE_ACTION: [MessageHandler(filters.TEXT, delete_word_or_group)],
            DELETE_WORD_OR_GROUP: [
               MessageHandler(filters.Regex('^Удалить слово$'), delete_word),
               MessageHandler(filters.Regex('^Удалить группу$'), delete_group),
            ],
            DELETE_WORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_word)],
            DELETE_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_group)],
            ADD_WORDS_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_words_group)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )  
    application.add_handler(conversation_handler)
    
    application.add_handler(CallbackQueryHandler(confirm_delete_group))


    # Обработка команды меню
    application.add_handler(MessageHandler(filters.Regex('^В меню✨$'), menu))  # Обработчик кнопки меню

    application.run_polling()
      
if __name__ == '__main__':
    main()
