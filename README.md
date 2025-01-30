# Telegram Bot with Gemini AI and MongoDB

## Overview
This is a Telegram bot that integrates with Google Gemini AI to provide intelligent responses, perform web searches, and analyze uploaded files (PDFs and images). It also stores user data and chat history in MongoDB.

## Features
- **User Registration**: Stores user details and phone numbers in MongoDB.
- **Chat Handling**: Processes user queries using Gemini AI.
- **File Handling**: Analyzes PDF and image files using AI.
- **Web Search**: Fetches summarized web search results using Gemini AI.
- **MongoDB Storage**: Saves chat history and user information.

## Prerequisites
Ensure you have the following:
- Python 3.8+
- Telegram Bot API token
- Google Gemini AI API key
- MongoDB database
- Required dependencies installed

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/telegram-gemini-bot.git
   cd telegram-gemini-bot
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Replace `BOT_TOKEN` with your Telegram bot token.
   - Replace `Your_api_key` with your Gemini AI API key.
   - Replace `Mongodb_connection` with your MongoDB connection string.

## Usage
Run the bot using:
```sh
python bot.py
```

## Commands
- `/start` - Registers the user and requests contact info.
- `/websearch <query>` - Searches the web and provides a summary.
- `Text Messages` - Generates AI-powered responses.
- `Upload Files (PDF/Image)` - Analyzes and summarizes content.

## File Handling
- **PDFs**: Extracts and summarizes text content.
- **Images**: Provides AI-generated descriptions.

## Deployment
You can deploy this bot using a cloud server or a service like Heroku.

## License
This project is licensed under the MIT License.

