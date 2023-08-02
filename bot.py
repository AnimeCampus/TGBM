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

# Character classes
classes = ['warrior', 'mage', 'archer']

# List of locations and their possible encounters
locations = {
    'forest': ['goblin', 'wolf', 'orc'],
    'cave': ['bat', 'spider', 'troll'],
    'mountain': ['griffin', 'yeti', 'dragon']
}

# Shop database
shop_db = {
    'sword': {'name': 'Sword', 'type': 'weapon', 'damage': 20, 'price': 50},
    'armor': {'name': 'Armor', 'type': 'armor', 'defense': 15, 'price': 40},
    'ring': {'name': 'Ring', 'type': 'accessory', 'bonus': 'hp', 'price': 30},
    # Add more items and their data here
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
    args = message.text.split()[1:]

    if len(args) != 1 or args[0].lower() not in locations:
        client.send_message(chat_id=user_id, text='Invalid command. Use /go [forest/cave/mountain] to explore.')
        return

    location = args[0].lower()

    player = player_collection.find_one({'_id': user_id})

    # Implement logic to handle exploration and encounters with monsters here.
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
                if player['exp'] >= 100 + player['level'] * 30:
                    player['level'] += 1
                    player['exp'] = 0
                    player['max_hp'] += 20
                    player['hp'] = player['max_hp']
                    client.send_message(chat_id=user_id, text=f"Congratulations! You leveled up to level {player['level']}!")
            else:
                # Reduce player HP based on monster attack
                player['hp'] -= monster_attack
                if player['hp'] <= 0:
                    player['hp'] = player['max_hp']
                    client.send_message(chat_id=user_id, text="You were defeated in battle, but you have been revived with full HP.")

            player_collection.update_one({'_id': user_id}, {'$set': {'hp': player['hp']}})

# Command: /flee
@app.on_message(filters.command('flee') & filters.private)
def flee_from_battle(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    if 'current_monster' not in player:
        client.send_message(chat_id=user_id, text="There's no monster to flee from. Use /go [location] to explore first.")
    else:
        player_collection.update_one({'_id': user_id}, {'$unset': {'current_monster': '', 'current_monster_hp': ''}})
        client.send_message(chat_id=user_id, text="You fled from the battle. Use /go [location] to explore more.")

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
    args = message.text.split()

    if len(args) < 2:
        client.send_message(chat_id=user_id, text='Invalid command. Use /equip [item] to equip an item.')
        return

    item = args[1].lower()
    player = player_collection.find_one({'_id': user_id})

    if item not in player['inventory']:
        client.send_message(chat_id=user_id, text=f"{item} is not in your inventory.")
    else:
        item_data = get_item_data(item)

        if not item_data:
            client.send_message(chat_id=user_id, text="Invalid item.")
            return

        allowed_equipment = get_allowed_equipment_for_class(player['class'])
        if item_data['type'] not in allowed_equipment:
            client.send_message(chat_id=user_id, text=f"You cannot equip {item_data['name']} as a {player['class']}.")
            return

        equipped_item = player['equipment'].get(item_data['type'])
        if equipped_item:
            player['inventory'].append(equipped_item)
            client.send_message(chat_id=user_id, text=f"{equipped_item} unequipped.")

        player['equipment'][item_data['type']] = item
        player['inventory'].remove(item)

        player_collection.update_one({'_id': user_id}, {'$set': {'inventory': player['inventory'], 'equipment': player['equipment']}})
        client.send_message(chat_id=user_id, text=f"{item_data['name']} equipped.")

# Command: /stats
@app.on_message(filters.command('stats') & filters.private)
def show_stats(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    stats_text = f"Player: {player['name']}\nClass: {player['class'].capitalize()}\nLevel: {player['level']}\nXP: {player['exp']}\nHP: {player['hp']}/{player['max_hp']}"
    client.send_message(chat_id=user_id, text=stats_text)

# Command: /heal
@app.on_message(filters.command('heal') & filters.private)
def heal_player(client: Client, message: Message):
    user_id = message.from_user.id
    player = player_collection.find_one({'_id': user_id})

    heal_amount = random.randint(10, 20)
    player['hp'] = min(player['hp'] + heal_amount, player['max_hp'])
    player_collection.update_one({'_id': user_id}, {'$set': {'hp': player['hp']}})

    client.send_message(chat_id=user_id, text=f"You have been healed for {heal_amount} HP. Current HP: {player['hp']}/{player['max_hp']}")

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
    /quests - View available quests.
    /inventory - View your inventory.
    /equip [item] - Equip an item.
    /stats - Show player stats.
    /heal - Heal yourself.
    /help - Show this help message.
    """
    client.send_message(chat_id=user_id, text=help_text)

# Function: Get item data
def get_item_data(item):
    # Implement logic to fetch the item's data from the MongoDB based on its name
    item_data = item_collection.find_one({'name': item})
    return item_data

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

# Command: /buy [item]
@app.on_message(filters.command('buy') & filters.private)
def buy_item(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        client.send_message(chat_id=user_id, text='Invalid command. Use /buy [item] to buy an item.')
        return

    item = args[1].lower()

    if item not in shop_db:
        client.send_message(chat_id=user_id, text=f"{item} is not available in the shop.")
        return

    player = player_collection.find_one({'_id': user_id})
    player_gold = player.get('gold', 500)
    item_data = shop_db[item]

    if player_gold < item_data['price']:
        client.send_message(chat_id=user_id, text="You don't have enough gold to buy this item.")
        return

    player_gold -= item_data['price']
    player['gold'] = player_gold

    # Add the item to the player's inventory
    player['inventory'].append(item)
    player_collection.update_one({'_id': user_id}, {'$set': {'inventory': player['inventory'], 'gold': player_gold}})

    client.send_message(chat_id=user_id, text=f"You bought {item_data['name']} for {item_data['price']} gold. You now have {player_gold} gold.")


print("started") 

# Run the bot
app.run()
