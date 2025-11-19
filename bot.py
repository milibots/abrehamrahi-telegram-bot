import os
import json
import asyncio
import requests
import time
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

class abrehamrahiStorage:
    def __init__(self, access_token=None, refresh_token=None, token_file="tokens.json"):
        self.base_url = "https://abrehamrahi.ir"
        self.token_file = token_file
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._load_tokens()
        self._update_session_headers()

    def _load_tokens(self):
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
        except Exception:
            pass

    def _save_tokens(self):
        try:
            tokens = {
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f, indent=2)
        except Exception:
            pass

    def _update_session_headers(self):
        self.headers = {
            'authorization': f'Bearer {self.access_token}' if self.access_token else '',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
            'origin': self.base_url,
            'referer': f'{self.base_url}/drive/files',
            'content-type': 'application/json',
        }
        
        if not hasattr(self, 'session'):
            self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_access_token_from_refresh(self, refresh_token):
        url = f"{self.base_url}/api/v2/profile/auth/token-refresh/"
        data = {"refresh": refresh_token}
        
        try:
            temp_session = requests.Session()
            temp_headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'content-type': 'application/json',
            }
            temp_session.headers.update(temp_headers)
            
            response = temp_session.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                new_access_token = result.get('access')
                if new_access_token:
                    self.access_token = new_access_token
                    self.refresh_token = refresh_token
                    self._update_session_headers()
                    self._save_tokens()
                    return True
            return False
        except Exception:
            return False

    def refresh_access_token(self):
        if not self.refresh_token:
            return False
        
        url = f"{self.base_url}/api/v2/profile/auth/token-refresh/"
        data = {"refresh": self.refresh_token}
        
        try:
            temp_session = requests.Session()
            temp_headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'content-type': 'application/json',
            }
            temp_session.headers.update(temp_headers)
            
            response = temp_session.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                new_access_token = result.get('access')
                if new_access_token:
                    self.access_token = new_access_token
                    self._update_session_headers()
                    self._save_tokens()
                    return True
            return False
        except Exception:
            return False

    def start_upload(self, file_size, file_name):
        url = f"{self.base_url}/api/v2/flat/start-upload/"
        data = {"obj_size": file_size, "name": file_name}
        
        response = self.session.post(url, json=data)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.post(url, json=data)
        
        response.raise_for_status()
        return response.json()

    def upload_file_part(self, signed_url, chunk_data, part_number):
        headers = {'content-type': 'application/octet-stream'}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chunk_session = requests.Session()
                response = chunk_session.put(signed_url, data=chunk_data, headers=headers, timeout=30)
                response.raise_for_status()
                etag = response.headers.get('ETag', '').strip('"')
                if not etag:
                    etag = f"part-{part_number}"
                return etag
            except requests.exceptions.RequestException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)

    def complete_upload(self, upload_id, key, parts, file_name, force_overwrite=False):
        url = f"{self.base_url}/api/v2/flat/complete-upload/"
        
        data = {
            "upload_id": upload_id,
            "key": key,
            "name": file_name,
            "force_overwrite": force_overwrite,
            "parts": [
                {
                    "ETag": part['etag'],
                    "PartNumber": part['part_number'],
                    "size": part['size']
                }
                for part in parts
            ]
        }
        
        response = self.session.post(url, json=data)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.post(url, json=data)
        
        response.raise_for_status()
        return response.json()

    def create_public_link(self, obj_id):
        url = f"{self.base_url}/api/v2/sharing/public-link/create/"
        data = {
            "obj_id": obj_id,
            "duration": None,
            "expiration_count": None
        }
        
        response = self.session.post(url, json=data)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.post(url, json=data)
        
        response.raise_for_status()
        return response.json()

    def list_objects(self, is_trash=False, limit=1000):
        url = f"{self.base_url}/api/v2/flat/list-objects/"
        params = {"is_trash": str(is_trash).lower(), "limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_profile(self):
        url = f"{self.base_url}/api/v6/profile/auth/get-profile/"
        response = self.session.get(url)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.get(url)
        
        response.raise_for_status()
        return response.json()

    def delete_objects(self, obj_ids):
        url = f"{self.base_url}/api/v2/rgw/trash-objects/"
        data = {"obj_ids": obj_ids}
        
        response = self.session.delete(url, json=data)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.delete(url, json=data)
        
        response.raise_for_status()
        return response.json()

    def delete_version_groups(self, version_groups):
        url = f"{self.base_url}/api/v3/rgw/delete-version-groups/"
        data = {"version_groups": version_groups}
        
        response = self.session.delete(url, json=data)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.delete(url, json=data)
        
        response.raise_for_status()
        return response.status_code == 200

    def get_file_details(self, obj_id):
        url = f"{self.base_url}/api/v2/flat/list-objects/"
        params = {"limit": 1000}
        response = self.session.get(url, params=params)
        
        if response.status_code == 401:
            if self.refresh_access_token():
                response = self.session.get(url, params=params)
        
        response.raise_for_status()
        files_data = response.json()
        
        for file_obj in files_data.get('results', []):
            if file_obj.get('id') == obj_id:
                return file_obj
        return None

    def _format_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"

class abrehamrahiBot:
    def __init__(self):
        self.setup_environment()
        
        self.uploader = abrehamrahiStorage(refresh_token=self.refresh_token)
        
        if not self.uploader.get_access_token_from_refresh(self.refresh_token):
            print("Failed to get access token")
            exit(1)
        
        self.app = Client(
            "abrehamrahi_bot",
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=self.bot_token,
            in_memory=True,
            workers=20,
        )
        
        self.setup_handlers()

    def setup_environment(self):
        env_file = ".env"
        
        if not os.path.exists(env_file):
            print("Creating .env file...")
            self.create_env_file(env_file)
        
        load_dotenv(env_file)
        
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.bot_token = os.getenv('BOT_TOKEN')
        self.refresh_token = os.getenv('REFRESH_TOKEN')
        
        if not all([self.api_id, self.api_hash, self.bot_token, self.refresh_token]):
            print("Missing required environment variables")
            exit(1)
        
        try:
            self.api_id = int(self.api_id)
        except ValueError:
            print("API_ID must be a number")
            exit(1)

    def create_env_file(self, env_file):
        print("\n" + "="*50)
        print("Telegram Bot Configuration")
        print("="*50)
        
        api_id = input("Enter API_ID: ").strip()
        api_hash = input("Enter API_HASH: ").strip()
        bot_token = input("Enter Bot Token: ").strip()
        refresh_token = input("Enter Refresh Token: ").strip()
        
        env_content = f"""API_ID={api_id}
API_HASH={api_hash}
BOT_TOKEN={bot_token}
REFRESH_TOKEN={refresh_token}
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(".env file created!")

    def setup_handlers(self):
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Upload File", callback_data="upload_help")],
                [InlineKeyboardButton("My Files", callback_data="list_files")],
                [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
                [InlineKeyboardButton("My Profile", callback_data="my_profile")],
                [InlineKeyboardButton("Help", callback_data="help")]
            ])
            
            await message.reply_text(
                "Welcome to abrehamrahi Bot!\n\nSend any file to upload or use buttons below:",
                reply_markup=keyboard
            )

        @self.app.on_message(filters.command("profile"))
        async def profile_command(client, message: Message):
            try:
                profile = await asyncio.to_thread(self.uploader.get_profile)
                
                profile_text = f"""
User Profile

Name: {profile.get('name', 'N/A')}
Phone: {profile.get('phone', 'N/A')}
ID: `{profile.get('id', 'N/A')}`
Country: {profile.get('country', 'N/A')}
Language: {profile.get('language', 'N/A')}
Balance: {profile.get('withdrawable_balance', 0)}

Last Updated: {datetime.fromtimestamp(profile.get('object_last_modified', 0)).strftime('%Y-%m-%d %H:%M')}
                """
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back to Main", callback_data="main_menu")]
                ])
                
                await message.reply_text(profile_text, reply_markup=keyboard)
                
            except Exception as e:
                await message.reply_text(f"Error getting profile: {str(e)}")

        @self.app.on_message(filters.command("list"))
        async def list_command(client, message: Message):
            await self.show_file_list(message)

        @self.app.on_message(filters.command("delete"))
        async def delete_command(client, message: Message):
            try:
                args = message.text.split()
                if len(args) < 2:
                    await message.reply_text("Please provide file ID:\n`/delete <file_id>`")
                    return
                
                file_id = args[1]
                await self.delete_file(message, file_id)
                
            except Exception as e:
                await message.reply_text(f"Error deleting file: {str(e)}")

        @self.app.on_message(filters.command("help"))
        async def help_command(client, message: Message):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Upload Guide", callback_data="upload_help")],
                [InlineKeyboardButton("View Files", callback_data="list_files")],
                [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
                [InlineKeyboardButton("My Profile", callback_data="my_profile")],
                [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
            ])
            
            help_text = """
abrehamrahi Bot Help

Main Commands:
• Send file → Auto upload
• /start → Main menu
• /list → View files
• /delete <file_id> → Delete file
• /profile → User profile
• /help → This help

Features:
✅ Live upload progress
✅ All file formats
✅ File management
✅ Secure
            """
            
            await message.reply_text(help_text, reply_markup=keyboard)

        @self.app.on_callback_query()
        async def handle_callbacks(client, callback_query):
            data = callback_query.data
            
            if data == "main_menu":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Upload File", callback_data="upload_help")],
                    [InlineKeyboardButton("My Files", callback_data="list_files")],
                    [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
                    [InlineKeyboardButton("My Profile", callback_data="my_profile")],
                    [InlineKeyboardButton("Help", callback_data="help")]
                ])
                await callback_query.message.edit_text(
                    "Main Menu\n\nPlease select an option:",
                    reply_markup=keyboard
                )
            
            elif data == "upload_help":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="main_menu")]
                ])
                await callback_query.message.edit_text(
                    "Upload Guide\n\nTo upload file:\n1. Select your file\n2. Send it here\n3. Wait for upload\n4. Get download link",
                    reply_markup=keyboard
                )
            
            elif data == "list_files" or data == "refresh_list":
                await self.show_file_list(callback_query.message, callback_query)
            
            elif data == "manage_files":
                await self.show_management_options(callback_query.message, callback_query)
            
            elif data.startswith("delete_"):
                file_id = data.replace("delete_", "")
                await self.delete_file(callback_query.message, file_id, callback_query)
            
            elif data.startswith("confirm_delete_"):
                file_id = data.replace("confirm_delete_", "")
                await self.confirm_delete_file(callback_query.message, file_id, callback_query)
            
            elif data.startswith("cancel_delete_"):
                file_id = data.replace("cancel_delete_", "")
                await self.cancel_delete_file(callback_query.message, file_id, callback_query)
            
            elif data == "my_profile":
                try:
                    profile = await asyncio.to_thread(self.uploader.get_profile)
                    
                    profile_text = f"""
User Profile

Name: {profile.get('name', 'N/A')}
Phone: {profile.get('phone', 'N/A')}
ID: `{profile.get('id', 'N/A')}`
Country: {profile.get('country', 'N/A')}
Language: {profile.get('language', 'N/A')}
Balance: {profile.get('withdrawable_balance', 0)}

Last Updated: {datetime.fromtimestamp(profile.get('object_last_modified', 0)).strftime('%Y-%m-%d %H:%M')}
                    """
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("Back to Main", callback_data="main_menu")]
                    ])
                    
                    await callback_query.message.edit_text(profile_text, reply_markup=keyboard)
                    
                except Exception as e:
                    await callback_query.message.edit_text(f"Error getting profile: {str(e)}")
            
            elif data == "help":
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Upload Guide", callback_data="upload_help")],
                    [InlineKeyboardButton("View Files", callback_data="list_files")],
                    [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
                    [InlineKeyboardButton("My Profile", callback_data="my_profile")],
                    [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
                ])
                await callback_query.message.edit_text(
                    "Help Menu\nUse buttons below for guidance",
                    reply_markup=keyboard)
            
            await callback_query.answer()

        @self.app.on_message(filters.document | filters.video | filters.audio)
        async def handle_file_upload(client, message: Message):
            progress_msg = await message.reply_text("Preparing upload...")
            file_path = None
            last_update_time = time.time()
            
            try:
                if message.document:
                    file = message.document
                    file_name = file.file_name
                elif message.video:
                    file = message.video
                    file_name = f"video_{file.file_id}.mp4"
                elif message.audio:
                    file = message.audio
                    file_name = f"audio_{file.file_id}.mp3" if not file.file_name else file.file_name
                else:
                    await progress_msg.edit_text("Unsupported file format!")
                    return

                file_size = file.file_size

                await progress_msg.edit_text(
                    f"Preparing Upload\n\nFile: `{file_name}`\nSize: {self.uploader._format_size(file_size)}\nPlease wait..."
                )

                download_start = time.time()
                download_path = await message.download(in_memory=False)
                file_path = Path(download_path)
                download_time = time.time() - download_start

                await progress_msg.edit_text(
                    f"Download Complete\n\nFile: `{file_name}`\nSize: {self.uploader._format_size(file_size)}\nDownload time: {download_time:.1f}s\nStarting upload..."
                )

                upload_data = await asyncio.to_thread(self.uploader.start_upload, file_size, file_name)
                
                upload_id = upload_data.get('upload_id')
                key = upload_data.get('key')
                signed_urls = upload_data.get('signed_urls', [])
                actual_chunk_size = upload_data.get('chunk_size', 5242880)

                if not upload_id or not key:
                    raise Exception("Server error")

                parts = []
                total_parts = (file_size + actual_chunk_size - 1) // actual_chunk_size

                upload_start_time = time.time()
                with open(file_path, 'rb') as f:
                    for part_number in range(1, total_parts + 1):
                        start_pos = (part_number - 1) * actual_chunk_size
                        end_pos = min(part_number * actual_chunk_size, file_size)
                        chunk_size_actual = end_pos - start_pos

                        f.seek(start_pos)
                        chunk = f.read(chunk_size_actual)

                        if part_number - 1 < len(signed_urls):
                            signed_url = signed_urls[part_number - 1]
                        else:
                            raise Exception("Upload URL error")

                        etag = await asyncio.to_thread(self.uploader.upload_file_part, signed_url, chunk, part_number)

                        parts.append({
                            "part_number": part_number,
                            "size": len(chunk),
                            "etag": etag
                        })

                        current_time = time.time()
                        if current_time - last_update_time >= 3 or part_number == total_parts:
                            elapsed_time = current_time - upload_start_time
                            progress_percent = (part_number / total_parts) * 100
                            progress_bar = "🟩" * int(progress_percent / 10) + "⬜" * (10 - int(progress_percent / 10))
                            
                            uploaded_bytes = part_number * actual_chunk_size
                            if uploaded_bytes > file_size:
                                uploaded_bytes = file_size
                            
                            if elapsed_time > 0:
                                speed = uploaded_bytes / elapsed_time
                                remaining_bytes = file_size - uploaded_bytes
                                eta = remaining_bytes / speed if speed > 0 else 0
                            else:
                                speed = 0
                                eta = 0

                            try:
                                await progress_msg.edit_text(
                                    f"Uploading...\n\nFile: `{file_name}`\nProgress: {progress_percent:.1f}%\n{progress_bar}\nPart: {part_number}/{total_parts}\nUploaded: {self.uploader._format_size(uploaded_bytes)} / {self.uploader._format_size(file_size)}\nSpeed: {self.uploader._format_size(speed)}/s\nETA: {eta:.0f}s"
                                )
                                last_update_time = current_time
                            except Exception:
                                pass

                await progress_msg.edit_text("Upload complete! Creating download link...")
                result = await asyncio.to_thread(self.uploader.complete_upload, upload_id, key, parts, file_name, False)
                
                file_id = result.get('id')
                if not file_id:
                    raise Exception("File ID error")

                public_link_data = await asyncio.to_thread(self.uploader.create_public_link, file_id)
                download_url = public_link_data.get('link', 'N/A')
                
                total_time = time.time() - download_start
                
                success_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Open Link", url=download_url)],
                    [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
                    [InlineKeyboardButton("View Files", callback_data="list_files")],
                    [InlineKeyboardButton("Upload New File", callback_data="upload_help")]
                ])
                
                await progress_msg.edit_text(
                    f"Upload Successful!\n\nFile: `{file_name}`\nSize: {self.uploader._format_size(file_size)}\nDownload URL: `{download_url}`\nFile ID: `{file_id}`\nTotal Time: {total_time:.1f}s",
                    reply_markup=success_keyboard,
                    disable_web_page_preview=True
                )

            except Exception as e:
                error_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Try Again", callback_data="upload_help")],
                    [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
                ])
                
                await progress_msg.edit_text(
                    f"Upload Error\n\nError: {str(e)}\nPlease try again!",
                    reply_markup=error_keyboard
                )
            
            finally:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass

        self.handle_file_upload = handle_file_upload

    async def show_file_list(self, message, callback_query=None):
        try:
            files = await asyncio.to_thread(self.uploader.list_objects)
            
            if files['count'] == 0:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Upload File", callback_data="upload_help")],
                    [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
                ])
                text = "Your drive is empty\nNo files to display."
                
                if callback_query:
                    await callback_query.message.edit_text(text, reply_markup=keyboard)
                else:
                    await message.reply_text(text, reply_markup=keyboard)
                return
            
            file_list = f"Your Files\n\nTotal Files: **{files['count']}**\n\n"
            
            for i, file_obj in enumerate(files['results'][:10], 1):
                size = self.uploader._format_size(file_obj['size'])
                file_id = file_obj['id']
                file_list += f"{i}. **{file_obj['name']}**\n"
                file_list += f"   {size} | ID `{file_id}`\n\n"
            
            if files['count'] > 10:
                file_list += f"and **{files['count'] - 10}** more files..."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
                [InlineKeyboardButton("Refresh List", callback_data="refresh_list")],
                [InlineKeyboardButton("Upload New File", callback_data="upload_help")],
                [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
            ])
            
            if callback_query:
                await callback_query.message.edit_text(file_list, reply_markup=keyboard)
            else:
                await message.reply_text(file_list, reply_markup=keyboard)
                
        except Exception as e:
            error_text = f"Error getting file list: {str(e)}"
            if callback_query:
                await callback_query.message.edit_text(error_text)
            else:
                await message.reply_text(error_text)

    async def show_management_options(self, message, callback_query=None):
        try:
            files = await asyncio.to_thread(self.uploader.list_objects)
            
            if files['count'] == 0:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Upload File", callback_data="upload_help")],
                    [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
                ])
                text = "Your drive is empty\nNo files to manage."
                
                if callback_query:
                    await callback_query.message.edit_text(text, reply_markup=keyboard)
                else:
                    await message.reply_text(text, reply_markup=keyboard)
                return
            
            management_text = f"File Management\n\nTotal Files: **{files['count']}**\n\nClick ❌ to delete files:\n\n"
            
            keyboard_buttons = []
            for i, file_obj in enumerate(files['results'][:10], 1):
                size = self.uploader._format_size(file_obj['size'])
                file_id = file_obj['id']
                file_name = file_obj['name']
                
                if len(file_name) > 30:
                    display_name = file_name[:27] + "..."
                else:
                    display_name = file_name
                
                management_text += f"{i}. **{display_name}**\n"
                management_text += f"   {size} | ID `{file_id}`\n\n"
                
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        f"❌ Delete {i} - {display_name}", 
                        callback_data=f"delete_{file_id}"
                    )
                ])
            
            keyboard_buttons.extend([
                [InlineKeyboardButton("View Files", callback_data="list_files")],
                [InlineKeyboardButton("Refresh List", callback_data="manage_files")],
                [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
            ])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            if callback_query:
                await callback_query.message.edit_text(management_text, reply_markup=keyboard)
            else:
                await message.reply_text(management_text, reply_markup=keyboard)
                
        except Exception as e:
            error_text = f"Error managing files: {str(e)}"
            if callback_query:
                await callback_query.message.edit_text(error_text)
            else:
                await message.reply_text(error_text)

    async def delete_file(self, message, file_id, callback_query=None):
        try:
            file_details = await asyncio.to_thread(self.uploader.get_file_details, int(file_id))
            
            if not file_details:
                error_text = f"File with ID `{file_id}` not found."
                if callback_query:
                    await callback_query.message.edit_text(error_text)
                else:
                    await message.reply_text(error_text)
                return
            
            file_name = file_details.get('name', 'Unknown')
            file_size = self.uploader._format_size(file_details.get('size', 0))
            
            confirmation_text = f"""
Confirm Deletion

File: **{file_name}**
Size: **{file_size}**
File ID: `{file_id}`

⚠️ **Warning:** This action cannot be undone!
Are you sure you want to delete this file?
            """
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{file_id}"),
                    InlineKeyboardButton("❌ No, Cancel", callback_data=f"cancel_delete_{file_id}")
                ],
                [InlineKeyboardButton("Back to Management", callback_data="manage_files")]
            ])
            
            if callback_query:
                await callback_query.message.edit_text(confirmation_text, reply_markup=keyboard)
            else:
                await message.reply_text(confirmation_text, reply_markup=keyboard)
                
        except Exception as e:
            error_text = f"Error getting file info: {str(e)}"
            if callback_query:
                await callback_query.message.edit_text(error_text)
            else:
                await message.reply_text(error_text)

    async def confirm_delete_file(self, message, file_id, callback_query=None):
        try:
            progress_text = "Deleting file..."
            if callback_query:
                await callback_query.message.edit_text(progress_text)
            else:
                progress_msg = await message.reply_text(progress_text)
            
            delete_result = await asyncio.to_thread(self.uploader.delete_objects, [int(file_id)])
            
            file_details = await asyncio.to_thread(self.uploader.get_file_details, int(file_id))
            version_group = file_details.get('version_group', '') if file_details else ''
            
            if version_group:
                permanent_delete = await asyncio.to_thread(
                    self.uploader.delete_version_groups, [version_group]
                )
            
            success_text = f"""
File Deleted Successfully

File ID: `{file_id}`
Status: Completely removed from server

File has been permanently deleted.
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("View Files", callback_data="list_files")],
                [InlineKeyboardButton("Manage Other Files", callback_data="manage_files")],
                [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
            ])
            
            if callback_query:
                await callback_query.message.edit_text(success_text, reply_markup=keyboard)
            else:
                await progress_msg.edit_text(success_text, reply_markup=keyboard)
                
        except Exception as e:
            error_text = f"Error deleting file: {str(e)}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Back to Management", callback_data="manage_files")]
            ])
            
            if callback_query:
                await callback_query.message.edit_text(error_text, reply_markup=keyboard)
            else:
                await progress_msg.edit_text(error_text, reply_markup=keyboard)

    async def cancel_delete_file(self, message, file_id, callback_query=None):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Manage Files", callback_data="manage_files")],
            [InlineKeyboardButton("Main Menu", callback_data="main_menu")]
        ])
        
        text = "File deletion cancelled\n\nFile was not deleted."
        
        if callback_query:
            await callback_query.message.edit_text(text, reply_markup=keyboard)
        else:
            await message.reply_text(text, reply_markup=keyboard)

    async def run(self):
        try:
            print("Connecting to Telegram...")
            await self.app.start()
            
            me = await self.app.get_me()
            print("abrehamrahi Bot started successfully!")
            print(f"Bot: @{me.username}")
            print(f"Bot ID: {me.id}")
            print("Waiting for messages...")
            
            await idle()
            
        except Exception as e:
            print(f"Bot error: {e}")
        finally:
            try:
                if self.app.is_connected:
                    await self.app.stop()
            except:
                pass

async def main():
    bot = abrehamrahiBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user!")
    except Exception as e:
        print(f"System error: {e}")
