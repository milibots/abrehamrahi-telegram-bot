# abrehamrahi Bot

A Telegram bot for uploading files to abrehamrahi storage with advanced file management features.

## Features

- 📤 **Auto File Upload**: Send any file to automatically upload
- 📊 **Live Progress**: Real-time upload progress with speed and ETA
- 🔗 **Public Links**: Generate public download links
- 📂 **File Management**: View, list, and delete files
- 👤 **User Profile**: Check storage account information
- 🗑️ **Secure Deletion**: Complete file removal from server
- ⚡ **High Performance**: Multi-part uploads with retry mechanism

## Setup

### 1. Install Dependencies


pip install -r requirements.txt
2. Configuration
The bot will automatically create a .env file on first run with:

env
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_TOKEN=your_bot_token
REFRESH_TOKEN=your_abrehamrahi_refresh_token
3. Get Credentials
Telegram API Credentials
API_ID & API_HASH: Get from https://my.telegram.org

Go to "API Development Tools"

Create a new application

Copy API_ID and API_HASH

Bot Token
Bot Token: Create a bot with @BotFather on Telegram

Start chat with @BotFather

Use /newbot command

Follow instructions to create your bot

Copy the bot token

Refresh Token
Refresh Token: Get from https://abrehamrahi.ir

Login to your account at https://abrehamrahi.ir

Open Developer Tools (F12 or Right-click → Inspect)

Go to "Network" tab

Refresh the page or navigate through the site

Look for API requests in the Network tab

Find requests to endpoints like /api/v2/profile/auth/token-refresh/

Check the request headers or payload for the refresh token

Copy the refresh token value

Alternative Method for Refresh Token:
Login to https://abrehamrahi.ir

Open Browser Console (F12)

Go to Application/Storage tab

Look for Local Storage or Session Storage

Search for "refresh" or "token" keys

Copy the refresh token value

4. Run the Bot
bash
python main.py
Usage
Commands
/start - Main menu with options

/list - View uploaded files

/delete <file_id> - Delete specific file

/profile - User account information

/help - Usage guide

File Upload
Simply send any file (document, video, audio) to the bot and it will automatically upload to your storage.

File Management
Use the inline buttons to:

View all uploaded files

Delete files with confirmation

Generate public download links

Monitor upload progress

Features Details
Multi-part Upload
Automatic chunking for large files

Parallel upload with progress tracking

Retry mechanism for failed chunks

Token Management
Automatic token refresh

Secure token storage

Session persistence

User Interface
Interactive buttons

Progress indicators

Error handling

Security
Tokens stored locally in encrypted format

Automatic session management

Secure file deletion

No data persistence on bot server

Troubleshooting
