import random
import pymongo
from pyrogram import Client, filters
from pyrogram.types import Message

# Initialize Pyrogram
api_id = 19099900
api_hash = '2b445de78e5baf012a0793e60bd4fbf5'
bot_token = '6206599982:AAFhXRwC0SnPCBK4WDwzdz7TbTsM2hccgZc'

app = Client('adventure_bot', api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Initialize MongoDB connection
mongo_url = 'mongodb+srv://sonu55:sonu55@cluster0.vqztrvk.mongodb.net/?retryWrites=true&w=majority'
mongo_client = pymongo.MongoClient(mongo_url)
db = mongo_client['adventure_db']

# Collection names
player_collection = db['players']
monster_collection = db['monsters']
quest_collection = db['quests']
item_collection = db['items']  

# Character classes
classes = ['warrior', 'mage', 'archer']

# List of locations and their possible encounters
locations = {
    'forest': ['goblin', 'wolf', 'orc'],
    'cave': ['bat', 'spider', 'troll'],
    'mountain': ['griffin', 'yeti', 'dragon']
}

# Command: /start
@app.on_message(filters.command('start'))
def start_game(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    if not player:
        # If the player is not found, it means they haven't created their character yet.
        client.send_message(chat_id=user_id, text='Welcome to Adventure Quest!\nPlease create your character using /create [name] [class]')
    else:
        client.send_message(chat_id=user_id, text='Welcome back to Adventure Quest!\nUse /help to see available commands.')

# Command: /create [name] [class]
@app.on_message(filters.command('create') & filters.private)
def create_character(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()[1:]

    if len(args) != 2 or args[1].lower() not in classes:
        client.send_message(chat_id=user_id, text='Invalid command. Use /create [name] [class] to create your character.')
        return

    name, char_class = args
    player_data = {
        '_id': user_id,
        'name': name,
        'class': char_class.lower(),
        'level': 1,
        'exp': 0,
        'hp': 100,
        'max_hp': 100,
        'inventory': [],
        'equipment': {}
    }

    player_collection.insert_one(player_data)
    client.send_message(chat_id=user_id, text=f'Congratulations, {name}! You are now a {char_class}.\nUse /go [location] to start your adventure.')

# Command: /go [location]
@app.on_message(filters.command('go') & filters.private)
def explore_location(client: Client, message: Message):
    user_id = message.from_user.id
    location = message.text.split()[1].lower()

    player = player_collection.find_one({'_id': user_id})

    # Check if the location is valid
    if location not in locations:
        client.send_message(chat_id=user_id, text='Invalid location. Use /go [forest/cave/mountain] to explore.')
    else:
        monster_pool = locations[location]
        monster = random.choice(monster_pool)
        monster_hp = random.randint(50 + player['level'] * 10, 100 + player['level'] * 20)

        # Save the current monster encounter in the player's data
        player_collection.update_one({'_id': user_id}, {'$set': {'current_monster': monster, 'current_monster_hp': monster_hp}})

        client.send_message(chat_id=user_id, text=f"You have encountered a {monster} in the {location.capitalize()}!")
        client.send_message(chat_id=user_id, text="What will you do?\n/attack - Attack the monster\n/flee - Flee from the battle")

# Command: /attack [monster]
@app.on_message(filters.command('attack') & filters.private)
def attack_monster(client: Client, message: Message):
    user_id = message.from_user.id

    player = player_collection.find_one({'_id': user_id})
    monster = player.get('current_monster')
    monster_hp = player.get('current_monster_hp')

    if not monster:
        client.send_message(chat_id=user_id, text="There's no monster to attack. Use /go [location] to explore first.")
    else:
        player_attack = random.randint(10 + player['level'] * 2, 20 + player['level'] * 5)
        monster_attack = random.randint(5 + player['level'] * 2, 15 + player['level'] * 3)

        if monster_hp <= 0:
            client.send_message(chat_id=user_id, text=f"You have already defeated the {monster}. Use /go [location] to explore more.")
        elif player['hp'] <= 0:
            client.send_message(chat_id=user_id, text="You are too weak to fight. Use /go [location] to heal.")
        else:
            # Reduce monster HP and player HP based on attacks
            monster_hp -= player_attack
            player_collection.update_one({'_id': user_id}, {'$set': {'current_monster_hp': monster_hp}})
            player['hp'] -= monster_attack

            if monster_hp <= 0:
                client.send_message(chat_id=user_id, text=f"You have defeated the {monster}!")
                exp_gained = random.randint(50 + player['level'] * 20, 100 + player['level'] * 30)
                player['exp'] += exp_gained
                handle_level_up(user_id)  # Check and handle level up
                player_collection.update_one({'_id': user_id}, {'$set': {'exp': player['exp']}})
                check_and_complete_quest(user_id, monster)  # Check and complete quests
            else:
                client.send_message(chat_id=user_id, text=f"The {monster} attacked you back for {monster_attack} damage.")
                check_for_player_death(user_id)  # Check if player died

            player_collection.update_one({'_id': user_id}, {'$set': {'hp': player['hp']}})

# Command: /flee
@app.on_message(filters.command('flee') & filters.private)
def flee_from_battle(client: Client, message: Message):
    user_id = message.from_user.id
    player_collection.update_one({'_id': user_id}, {'$unset': {'current_monster': '', 'current_monster_hp': ''}})
    client.send_message(chat_id=user_id, text="You fled from the battle. Use /go [location] to explore more.")

# Command: /heal
@app.on_message(filters.command('heal') & filters.private)
def heal_player(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    if player['hp'] == player['max_hp']:
        client.send_message(chat_id=user_id, text="Your HP is already at maximum.")
    else:
        # Implement logic to consume a healing item or deduct gold for healing
        # For simplicity, let's assume we have a healing item called 'potion' that restores 30 HP
        if 'potion' in player['inventory']:
            player['hp'] = min(player['hp'] + 30, player['max_hp'])
            player['inventory'].remove('potion')
            client.send_message(chat_id=user_id, text="You used a potion to heal 30 HP.")
        else:
            client.send_message(chat_id=user_id, text="You don't have any healing items.")

        player_collection.update_one({'_id': user_id}, {'$set': {'hp': player['hp'], 'inventory': player['inventory']}})

# Command: /quests
@app.on_message(filters.command('quests') & filters.private)
def show_quests(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    # Fetch available quests based on player's level
    available_quests = []
    for quest in quest_collection.find({'min_level': {'$lte': player['level']}}):
        available_quests.append(f"{quest['name']} (Min. Level: {quest['min_level']})")

    if not available_quests:
        client.send_message(chat_id=user_id, text="There are no quests available for your level.")
    else:
        quest_list = "\n".join(available_quests)
        client.send_message(chat_id=user_id, text=f"Available quests:\n{quest_list}")

# Command: /inventory
@app.on_message(filters.command('inventory') & filters.private)
def show_inventory(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    if not player['inventory']:
        client.send_message(chat_id=user_id, text="Your inventory is empty.")
    else:
        inventory_list = "\n".join(player['inventory'])
        client.send_message(chat_id=user_id, text=f"Your inventory:\n{inventory_list}")

# Command: /equip [item]
@app.on_message(filters.command('equip') & filters.private)
def equip_item(client: Client, message: Message):
    user_id = message.from_user.id
    item = message.text.split()[1].lower()
    player = player_collection.find_one({'_id': user_id})

    if item not in player['inventory']:
        client.send_message(chat_id=user_id, text=f"{item} is not in your inventory.")
    else:
        # Check if the item can be equipped based on its type and player's class
        item_data = get_item_data(item)
        if not item_data:
            client.send_message(chat_id=user_id, text="Invalid item.")
            return

        if item_data['type'] not in get_allowed_equipment_for_class(player['class']):
            client.send_message(chat_id=user_id, text=f"You cannot equip {item_data['name']} as a {player['class']}.")
            return

        # Unequip the currently equipped item of the same type, if any
        equipped_item = player['equipment'].get(item_data['type'])
        if equipped_item:
            # Move the currently equipped item back to the inventory
            player['inventory'].append(equipped_item)
            client.send_message(chat_id=user_id, text=f"{equipped_item} unequipped.")

        # Equip the new item
        player['equipment'][item_data['type']] = item
        player['inventory'].remove(item)

        # Update the player's data in the database
        player_collection.update_one({'_id': user_id}, {'$set': {'inventory': player['inventory'], 'equipment': player['equipment']}})
        client.send_message(chat_id=user_id, text=f"{item_data['name']} equipped.")

# Function: Get item data
def get_item_data(item):
    # Implement logic to fetch the item's data from the database based on its name
    # For this example, I'll use a simple dictionary as an item database
    items_db = {
        'sword': {'name': 'Sword', 'type': 'weapon', 'damage': 20},
        'armor': {'name': 'Armor', 'type': 'armor', 'defense': 15},
        'ring': {'name': 'Ring', 'type': 'accessory', 'bonus': 'hp'}
        # Add more items and their data here
    }
    
    return items_db.get(item)

# Function: Get allowed equipment for class
def get_allowed_equipment_for_class(char_class):
    # Implement logic to determine the allowed equipment types for a given character class
    allowed_equipment = {
        'warrior': ['weapon', 'armor'],
        'mage': ['weapon', 'accessory'],
        'archer': ['weapon', 'armor', 'accessory']
        # Add more character classes and their allowed equipment types here
    }
    
    return allowed_equipment.get(char_class, [])

# Function: Check and handle level up
def handle_level_up(user_id):
    player = player_collection.find_one({'_id': user_id})
    while player['exp'] >= 100 + player['level'] * 30:
        player['level'] += 1
        player['exp'] -= (100 + (player['level'] - 1) * 30)
        player['max_hp'] += 20
        player['hp'] = player['max_hp']
        player_collection.update_one({'_id': user_id}, {'$set': {'level': player['level'], 'exp': player['exp'], 'max_hp': player['max_hp'], 'hp': player['hp']}})
        client.send_message(chat_id=user_id, text=f"Congratulations! You leveled up to level {player['level']}!")

# Function: Check and complete quests
def check_and_complete_quest(user_id, monster):
    player = player_collection.find_one({'_id': user_id})
    for quest in quest_collection.find({'name': monster}):
        if player['level'] >= quest['min_level']:
            # Implement logic to complete the quest and reward the player
            # For simplicity, let's just increase player's gold by quest reward amount
            player['gold'] += quest['reward']
            player_collection.update_one({'_id': user_id}, {'$set': {'gold': player['gold']}})
            client.send_message(chat_id=user_id, text=f"Quest '{quest['name']}' completed! You earned {quest['reward']} gold.")

# Function: Check if player died and revive
def check_for_player_death(user_id):
    player = player_collection.find_one({'_id': user_id})
    if player['hp'] <= 0:
        player['hp'] = player['max_hp']
        player_collection.update_one({'_id': user_id}, {'$set': {'hp': player['hp']}})
        client.send_message(chat_id=user_id, text="You were defeated in battle, but you have been revived with full HP.")

# Command: /help
@app.on_message(filters.command('help'))
def show_help(client: Client, message: Message):
    user_id = message.from_user.id
    help_text = """
    Welcome to Adventure Quest!
    Available commands:
    /start - Start or resume your adventure.
    /create [name] [class] - Create your character.
    /go [location] - Explore new locations.
    /attack [monster] - Attack a monster.
    /flee - Flee from the battle.
    /heal - Use a healing item to restore HP.
    /quests - View available quests.
    /inventory - View your inventory.
    /equip [item] - Equip an item.
    /help - Show this help message.
    """
    client.send_message(chat_id=user_id, text=help_text)


# Run the bot
app.run()
