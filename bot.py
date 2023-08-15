import random
from io import BytesIO
from PIL import Image, ImageDraw

from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto

app = Client("snake_ladder_bot", api_id=19099900, api_hash="2b445de78e5baf012a0793e60bd4fbf5", bot_token="6206599982:AAGELlIUapiHd88l5z4YuVwXp1h3tHMfotY)

players = []
current_player_index = 0
board_size = 10
board = [0] * (board_size * board_size)
colors = ["red", "green", "blue", "yellow"]

snakes = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100}
win_position = 100

def create_board_image():
    # ... same as before ...

def position_to_coordinates(position):
    # ... same as before ...

@app.on_message(filters.command("start", prefixes="/"))
def start_command(_, message):
    app.send_message(message.chat.id, "Welcome to Snake and Ladder Game Bot!\nUse /gstart to start a new game.")

@app.on_message(filters.command("gstart", prefixes="/"))
def start_game(_, message):
    global players
    players = []
    current_player_index = 0

    app.send_message(message.chat.id, "Starting a new game!\nHow many players want to play (1-4)?")
    app.register_next_step_handler_by_chat_id(message.chat.id, get_num_players)

def get_num_players(_, message):
    num_players = int(message.text)
    app.send_message(message.chat.id, f"Great! Please send the names of {num_players} players, one by one.")

    app.register_next_step_handler_by_chat_id(message.chat.id, lambda _, msg: store_player_name(msg, num_players))

def store_player_name(message, num_players):
    global players

    players.append(message.text)
    if len(players) < num_players:
        app.send_message(message.chat.id, f"Player {len(players) + 1} name:")
        app.register_next_step_handler_by_chat_id(message.chat.id, lambda _, msg: store_player_name(msg, num_players))
    else:
        app.send_message(message.chat.id, f"Players: {', '.join(players)}\nStarting the game!")

        send_player_names(message.chat.id, 0)
        update_board()

def send_player_names(chat_id, player_index):
    if player_index >= len(players):
        return

    app.send_message(chat_id, f"{players[player_index]}, it's your turn. Use /roll to roll the dice.")
    app.send_message(chat_id, f"{players[player_index]}, type /roll when you are ready!")

@app.on_message(filters.command("roll", prefixes="/"))
def roll_command(_, message):
    global current_player_index

    if players and current_player_index < len(players) and message.from_user.username == players[current_player_index]:
        dice_result = roll_dice()
        app.send_message(message.chat.id, f"{players[current_player_index]} rolled a {dice_result}!")

        update_player_position(current_player_index, dice_result)
        update_board()

        next_player()

def next_player():
    global current_player_index
    current_player_index = (current_player_index + 1) % len(players)
    send_player_names(message.chat.id, current_player_index)

def update_player_position(player_index, dice_result):
    global board

    if players[player_index]:
        position = board[player_index]
        new_position = position + dice_result

        if new_position in snakes:
            new_position = snakes[new_position]
        elif new_position in ladders:
            new_position = ladders[new_position]

        if new_position <= win_position:
            board[player_index] = new_position

def update_board():
    img = create_board_image()
    img_byte_array = BytesIO()
    img.save(img_byte_array, format="PNG")
    img_byte_array.seek(0)

    media = InputMediaPhoto(media=img_byte_array, caption="Current Game Board")
    app.send_photo(chat_id=YOUR_CHAT_ID, photo=img_byte_array, caption="Current Game Board")


print("Started") 
app.run()
idle() 
