import datetime
from datetime import timezone
import fitz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext import filters
import google.generativeai as genai  # Gemini API import
import os
from pymongo import MongoClient
from PIL import Image

# MongoDB configuration
client = MongoClient("Mongodb_connection")  # Replace with your MongoDB connection string
db = client['telegram_bot']
users_collection = db['users']

# Bot token
BOT_TOKEN = ""  # Replace with your Telegram bot token

# GenAI API configuration
genai.configure(api_key="Your_api_key")  # Replace with your Gemini API Key
model = genai.GenerativeModel("gemini-1.5-flash")  # Use appropriate Gemini model

# Start command: Registers user and requests phone number
async def start(update: Update, context: CallbackContext):
    """Handles user registration on the first interaction."""
    user = update.effective_user
    chat_id = user.id
    username = user.username
    first_name = user.first_name

    # Check if user already exists in MongoDB
    existing_user = users_collection.find_one({"chat_id": chat_id})
    if not existing_user:
        # Save user to MongoDB
        users_collection.insert_one({
            "chat_id": chat_id,
            "username": username,
            "first_name": first_name,
            "registered_at": datetime.datetime.now(timezone.utc)
        })
        # Request phone number
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("Share Contact", request_contact=True)]], one_time_keyboard=True
        )
        await update.message.reply_text("Welcome! Please share your phone number:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Welcome back! You're already registered.")

# Save user phone number after contact sharing
async def save_contact(update: Update, context: CallbackContext):
    """Saves the user's phone number."""
    contact = update.message.contact
    chat_id = update.effective_chat.id
    phone_number = contact.phone_number

    # Update phone number in MongoDB
    users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": phone_number}})
    
    # Send confirmation message without triggering any AI processing
    await update.message.reply_text("Thank you! Your phone number has been saved.")

# Chat command: Respond to user queries using Gemini AI
async def chat(update: Update, context: CallbackContext):
    """Handles user queries and responds using GenAI."""
    user_input = update.message.text
    chat_id = update.effective_chat.id

    # Use GenAI to generate a response
    try:
        response = model.generate_content(user_input)
        if response and hasattr(response, "text"):
            bot_response = response.text
        else:
            bot_response = "Sorry, I couldn't process your request. Please try again later."
    except Exception as e:
        bot_response = "Sorry, I couldn't process your request. Please try again later."

    # Save chat history to MongoDB
    chat_entry = {
        "user_input": user_input,
        "bot_response": bot_response,
        "timestamp": datetime.datetime.now(timezone.utc)
    }
    users_collection.update_one({"chat_id": chat_id}, {"$push": {"chat_history": chat_entry}})

    # Respond to the user
    await update.message.reply_text(bot_response)

# Handle file uploads and analyze them (photo or document)

async def handle_file(update: Update, context: CallbackContext):
    """Handles file uploads and analyzes them using Gemini AI."""
    chat_id = update.effective_chat.id
    message = update.message

    # Check if the message contains a document or a photo
    if message.document:
        file = await message.document.get_file()
        file_name = f"./downloads/{message.document.file_name}"
        file_type = "document"
    elif message.photo:
        file = await message.photo[-1].get_file()
        file_name = f"./downloads/{file.file_unique_id}.jpg"
        file_type = "photo"
    else:
        await update.message.reply_text("Unsupported file type. Please send an image or PDF.")
        return

    # Ensure the downloads directory exists
    os.makedirs("./downloads", exist_ok=True)

    # Download the file
    await file.download_to_drive(file_name)

    # Analyze the file
    analysis_result = "Analysis failed. Please try again."
    
    try:
        if file_type == "photo":
            # Convert image bytes to PIL Image
            with Image.open(file_name) as img:
                response = model.generate_content(["Describe this image in detail.", img])
            analysis_result = response.text if response.text else "No description available."
        
        elif file_name.endswith(".pdf"):
            # Extract text from PDF
            with fitz.open(file_name) as pdf:
                text = "\n".join([page.get_text() for page in pdf])

            # Send extracted text to Gemini for analysis
            response = model.generate_content(f"Summarize this document:\n{text[:2000]}")  # Limit to 2000 chars
            analysis_result = response.text if response.text else "No summary available."

    except Exception as e:
        analysis_result = f"Error analyzing file: {str(e)}"

    # Split long messages for Telegram (limit: 4096 chars)
    max_length = 4000
    if len(analysis_result) > max_length:
        for i in range(0, len(analysis_result), max_length):
            await update.message.reply_text(analysis_result[i:i+max_length])
    else:
        await update.message.reply_text(f"File analyzed: {analysis_result}")

# Web search using Gemini AI
async def web_search(update: Update, context: CallbackContext):
    """Handles /websearch command using Gemini AI."""
    chat_id = update.effective_chat.id

    # Extract query from user command
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search term. Example: /websearch artificial intelligence")
        return

    try:
        # Use Gemini to generate a summary of the search results
        response = model.generate_content(
            f"Summarize the top results for the search query: {query}"
        )

        # Check if we got a valid response
        if response and hasattr(response, "text"):
            bot_response = response.text
        else:
            bot_response = "Sorry, I couldn't process your request. Please try again later."

        # Send the summarized response to the user
        await update.message.reply_text(f"🔎 **Search Summary for:** {query}\n\n{bot_response}")

    except Exception as e:
        print(f"Error during search: {str(e)}")
        await update.message.reply_text(f"Error during search: {str(e)}. Please try again.")

# Main entry point for the bot
def main():
    """Main entry point for the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("websearch", web_search))  # Adding the /websearch handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.add_handler(MessageHandler(filters.CONTACT, save_contact))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
