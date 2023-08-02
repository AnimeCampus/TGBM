from pyrogram import Client, filters
from pyrogram.types import Message
import random
import requests



API_ID = 19099900
API_HASH = '2b445de78e5baf012a0793e60bd4fbf5'
BOT_TOKEN = '6206599982:AAFhXRwC0SnPCBK4WDwzdz7TbTsM2hccgZc'

app = Client("ninja_quiz_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store user scores (You can replace this with a database)
user_scores = {}

def get_user_score(user_id):
    return user_scores.get(user_id, 0)

def increase_user_score(user_id):
    user_scores[user_id] = get_user_score(user_id) + 1

def fetch_questions(category_id, difficulty):
    url = f"https://opentdb.com/api.php?amount=5&category={category_id}&difficulty={difficulty}&type=multiple"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["results"]
    return []

def format_question(question_data):
    question = question_data["question"]
    correct_answer = question_data["correct_answer"]
    incorrect_answers = question_data["incorrect_answers"]
    options = incorrect_answers + [correct_answer]
    random.shuffle(options)
    return {
        "question": question,
        "options": options,
        "correct_answer": options.index(correct_answer)
    }

def get_random_question(category_id, difficulty):
    questions = fetch_questions(category_id, difficulty)
    if questions:
        return format_question(random.choice(questions))
    return None

category_id = None
difficulty = None

@app.on_message(filters.command("start"))
def start(_, message: Message):
    # Code to handle the start command
    user_id = message.from_user.id
    user_scores[user_id] = 0
    message.reply_text("Welcome to the Ninja Quiz Bot! Use /help to see available categories and start the quiz.")

@app.on_message(filters.command("help"))
def help_command(_, message: Message):
    # Code to handle the help command
    categories = get_category_list()
    categories_text = "\n".join([f"{category['id']}. {category['name']}" for category in categories])
    help_text = f"""
    Available Commands:
    /start - Start the game
    /help - Show available commands and categories
    /quiz <category_id> <difficulty> - Start a quiz (e.g., /quiz 31 medium)
    
    Available Categories:
    {categories_text}
    """
    message.reply_text(help_text)

@app.on_message(filters.command("quiz"))
def quiz(_, message: Message):
    # Code to handle the quiz command and ask a random question
    global category_id, difficulty  # Declare them as global

    user_id = message.from_user.id
    user_score = get_user_score(user_id)
    message.reply_text(f"Your current score: {user_score}")

    try:
        category_id = int(message.command[1])
        difficulty = message.command[2].lower()

        if difficulty not in ["easy", "medium", "hard"]:
            raise ValueError

        question = get_random_question(category_id, difficulty)
        if question:
            question_text = question["question"]
            options = question["options"]

            # Format the question with options as a string
            options_text = "\n".join([f"{index + 1}. {option}" for index, option in enumerate(options)])

            message.reply_text(f"{question_text}\n\n{options_text}\n\nAnswer using /answer <option_number>.")
        else:
            message.reply_text("Failed to fetch a question from the API. Try again later.")
    except (IndexError, ValueError):
        message.reply_text("Invalid command format. Use /quiz <category_id> <difficulty> (e.g., /quiz 31 medium).")

@app.on_message(filters.command("answer"))
def answer(_, message: Message):
    # Code to handle the answer command and check if the answer is correct
    user_id = message.from_user.id
    global category_id, difficulty  # Declare them as global

    try:
        selected_option = int(message.command[1]) - 1
        question = get_random_question(category_id, difficulty)
        correct_answer = question["correct_answer"]

        if selected_option == correct_answer:
            increase_user_score(user_id)
            message.reply_text("Correct answer! Well done!")
        else:
            message.reply_text("Oops, that's not the correct answer. Try again!")
    except (IndexError, ValueError):
        message.reply_text("Invalid command format. Use /answer <option_number>.")

if __name__ == "__main__":
    app.run()
