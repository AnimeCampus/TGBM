import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# Replace these with your actual credentials
api_id = 19099900
api_hash = '2b445de78e5baf012a0793e60bd4fbf5'
api_key = 'tbWHBFNxFtKoZ3kaYbFaxuJG'
bot_token = '6206599982:AAFhXRwC0SnPCBK4WDwzdz7TbTsM2hccgZc'

app = Client("remove_bg_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def remove_background_from_image(file_path, output_filename):
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        headers={'X-Api-Key': api_key},
        files={'image_file': open(file_path, 'rb')},
    )

    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False

@app.on_message(filters.command("start"))
def start_command(client: Client, message: Message):
    message.reply_text("Hello! I am a bot that can remove the background from images. Just reply to an image with /rmbg <output_filename> to remove its background.")

@app.on_message(filters.command("help"))
def help_command(client: Client, message: Message):
    message.reply_text("Just reply to an image with /rmbg <output_filename> to remove its background. The output filename should have a valid extension like .png, .jpg, etc.")

@app.on_message(filters.command("rmbg"))
def remove_bg_command(client: Client, message: Message):
    if len(message.command) != 2:
        message.reply_text("Usage: /rmbg <output_filename>")
        return

    replied_message = message.reply_to_message
    if not replied_message or not replied_message.document:
        message.reply_text("Reply to an image with /rmbg <output_filename> to remove its background.")
        return

    output_filename = message.command[1]
    if not output_filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        message.reply_text("Invalid output filename extension. Please use .png or .jpg.")
        return

    image = replied_message.document
    image_path = client.download_media(image)
    
    if remove_background_from_image(image_path, output_filename):
        message.reply_document("Here is the background removed image:", document=output_filename)
        os.remove(output_filename)
    else:
        message.reply_text("Failed to remove the background. Please try again later.")


app.run()
