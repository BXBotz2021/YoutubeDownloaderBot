import os
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import yt_dlp
from urllib.parse import urlparse
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot credentials - Replace with your actual credentials
API_ID = "7813390"  # Get from https://my.telegram.org
API_HASH = "1faadd9cc60374bca1e88c2f44e3ee2f"  # Get from https://my.telegram.org
BOT_TOKEN = "7594234544:AAEqQ2R5HsDsLVEABcNBPDDjJqDyZPRYods"  # Get from @BotFather

class YouTubeDownloader:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def is_valid_youtube_url(self, url):
        """Check if the URL is a valid YouTube URL"""
        parsed = urlparse(url)
        return parsed.netloc in ['www.youtube.com', 'youtube.com', 'youtu.be', 'm.youtube.com']
    
    async def get_video_info(self, url):
        """Get video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'formats': info.get('formats', []),
                    'filesize': info.get('filesize', 0) or info.get('filesize_approx', 0)
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    async def download_video(self, url, quality='best', format_type='mp4', progress_callback=None):
        """Download video with specified quality and format"""
        try:
            output_path = os.path.join(self.temp_dir, '%(title)s.%(ext)s')
            
            # Progress hook for download progress
            def progress_hook(d):
                if progress_callback and d['status'] == 'downloading':
                    try:
                        percent = d.get('_percent_str', '0%').strip()
                        speed = d.get('_speed_str', 'N/A')
                        asyncio.create_task(progress_callback(percent, speed))
                    except:
                        pass
            
            if quality == 'audio':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_path,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                    'progress_hooks': [progress_hook],
                }
            else:
                if quality == 'low':
                    format_selector = 'worst[height<=480]/worst'
                elif quality == 'medium':
                    format_selector = 'best[height<=720]/best'
                elif quality == 'high':
                    format_selector = 'best[height<=1080]/best'
                else:  # ultra quality
                    format_selector = 'best'
                
                ydl_opts = {
                    'format': format_selector,
                    'outtmpl': output_path,
                    'quiet': True,
                    'progress_hooks': [progress_hook],
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.get_event_loop().run_in_executor(
                    None, ydl.download, [url]
                )
            
            # Find the downloaded file
            for file in os.listdir(self.temp_dir):
                if file.endswith(('.mp4', '.webm', '.mkv', '.mp3', '.m4a')):
                    return os.path.join(self.temp_dir, file)
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")

# Global downloader instance
downloader = YouTubeDownloader()

# Initialize Pyrogram client
app = Client(
    "youtube_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    welcome_message = """
🎥 **YouTube Video Downloader Bot (No Size Limit!)**

Welcome! I can download YouTube videos of ANY size using MTProto.

**Features:**
✅ No file size limits (up to 2GB)
✅ High-speed downloads using MTProto
✅ Multiple quality options
✅ Audio extraction
✅ Download progress tracking

**How to use:**
1. Send me a YouTube video URL
2. Choose your preferred quality
3. I'll download and send the video

**Commands:**
/start - Show this message
/help - Detailed help information

**Quality Options:**
• Ultra (Best available)
• High (1080p)
• Medium (720p) 
• Low (480p)
• Audio Only (MP3)

Just send me a YouTube link to get started! 🚀
    """
    
    await message.reply_text(welcome_message, parse_mode="markdown")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    help_text = """
🔧 **Detailed Help - YouTube Downloader Bot**

**MTProto Advantages:**
• Download files up to 2GB (vs 50MB limit with Bot API)
• Faster upload/download speeds
• Better reliability for large files
• Resume capability for interrupted transfers

**Supported URLs:**
• youtube.com/watch?v=...
• youtu.be/...
• m.youtube.com/...
• youtube.com/playlist?list=... (first video)

**Quality Guide:**
• **Ultra** - Highest available quality (4K/8K if available)
• **High** - 1080p Full HD
• **Medium** - 720p HD (good balance)
• **Low** - 480p (smaller files, mobile-friendly)
• **Audio** - MP3 format, 192kbps

**File Size Examples:**
• 10-minute 1080p video: ~100-200MB
• 1-hour 1080p video: ~500MB-1GB  
• 4K videos can be 1-2GB+

**Tips:**
• Longer videos will take more time to download
• Choose lower quality for faster downloads
• The bot shows download progress
• Please respect copyright and YouTube ToS

**Technical Details:**
This bot uses MTProto library (Pyrogram) instead of Bot API, which removes Telegram's file size restrictions for bots.
    """
    
    await message.reply_text(help_text, parse_mode="markdown")

@app.on_message(filters.text & filters.regex(r'(youtube\.com|youtu\.be)'))
async def handle_youtube_url(client: Client, message: Message):
    """Handle YouTube URL messages"""
    url = message.text.strip()
    
    if not downloader.is_valid_youtube_url(url):
        await message.reply_text(
            "❌ Please send a valid YouTube URL.\n\n"
            "Examples:\n"
            "• https://youtube.com/watch?v=...\n"
            "• https://youtu.be/...\n"
            "• https://m.youtube.com/watch?v=..."
        )
        return
    
    # Send processing message
    status_msg = await message.reply_text("🔍 Analyzing video... Please wait.")
    
    # Get video info
    video_info = await downloader.get_video_info(url)
    
    if not video_info:
        await status_msg.edit_text("❌ Could not retrieve video information. Please check the URL and try again.")
        return
    
    # Format duration
    duration = video_info['duration']
    if duration:
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours > 0:
            duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{minutes}:{seconds:02d}"
    else:
        duration_str = "Unknown"
    
    # Format view count
    views = video_info['view_count']
    views_str = f"{views:,}" if views else "Unknown"
    
    # Estimate file sizes
    filesize = video_info['filesize']
    size_info = f"\n**Est. Size:** {filesize / (1024*1024):.1f}MB" if filesize else ""
    
    # Create info message
    info_text = f"""
📹 **Video Information**

**Title:** {video_info['title'][:60]}{'...' if len(video_info['title']) > 60 else ''}
**Channel:** {video_info['uploader']}
**Duration:** {duration_str}
**Views:** {views_str}{size_info}

🎬 **Choose download quality:**
*(No size limits with MTProto!)*
    """
    
    # Create quality selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("🌟 Ultra Quality", callback_data=f"dl_ultra_{message.id}"),
            InlineKeyboardButton("🎬 High (1080p)", callback_data=f"dl_high_{message.id}")
        ],
        [
            InlineKeyboardButton("📺 Medium (720p)", callback_data=f"dl_medium_{message.id}"),
            InlineKeyboardButton("📱 Low (480p)", callback_data=f"dl_low_{message.id}")
        ],
        [
            InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data=f"dl_audio_{message.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Store URL for callback
    app.user_data = getattr(app, 'user_data', {})
    app.user_data[f"url_{message.id}"] = url
    
    await status_msg.edit_text(info_text, reply_markup=reply_markup, parse_mode="markdown")

@app.on_callback_query(filters.regex(r"^dl_"))
async def download_callback(client: Client, callback_query: CallbackQuery):
    """Handle download callback queries"""
    await callback_query.answer()
    
    # Parse callback data
    data_parts = callback_query.data.split('_')
    if len(data_parts) != 3:
        await callback_query.edit_message_text("❌ Invalid download request.")
        return
    
    action, quality, msg_id = data_parts
    
    # Get stored URL
    app.user_data = getattr(app, 'user_data', {})
    url = app.user_data.get(f"url_{msg_id}")
    
    if not url:
        await callback_query.edit_message_text("❌ URL not found. Please send the YouTube link again.")
        return
    
    # Quality names
    quality_names = {
        'ultra': '🌟 Ultra Quality',
        'high': '🎬 High Quality (1080p)',
        'medium': '📺 Medium Quality (720p)', 
        'low': '📱 Low Quality (480p)',
        'audio': '🎵 Audio Only (MP3)'
    }
    
    selected_quality = quality_names.get(quality, quality)
    
    # Progress tracking
    current_progress = {"percent": "0%", "speed": "N/A", "last_update": 0}
    
    async def update_progress(percent, speed):
        import time
        current_time = time.time()
        current_progress["percent"] = percent
        current_progress["speed"] = speed
        
        # Update every 3 seconds to avoid rate limits
        if current_time - current_progress["last_update"] > 3:
            try:
                await callback_query.edit_message_text(
                    f"⬇️ **Downloading {selected_quality}**\n\n"
                    f"📊 Progress: {percent}\n"
                    f"🚀 Speed: {speed}\n"
                    f"⏳ Please wait..."
                )
                current_progress["last_update"] = current_time
            except:
                pass  # Ignore rate limit errors
    
    # Start download
    await callback_query.edit_message_text(
        f"⬇️ **Starting download...**\n\n"
        f"Quality: {selected_quality}\n"
        f"🔄 Initializing download..."
    )
    
    file_path = await downloader.download_video(url, quality, progress_callback=update_progress)
    
    if not file_path or not os.path.exists(file_path):
        await callback_query.edit_message_text("❌ Download failed. Please try again later.")
        return
    
    # Get file info
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    filename = os.path.basename(file_path)
    
    # Update status for upload
    await callback_query.edit_message_text(
        f"📤 **Uploading file...**\n\n"
        f"📁 **File:** {filename[:50]}{'...' if len(filename) > 50 else ''}\n"
        f"📊 **Size:** {file_size_mb:.1f}MB\n"
        f"🚀 **Using MTProto** (No size limits!)\n\n"
        f"⏳ Upload in progress..."
    )
    
    # Upload progress callback
    async def upload_progress(current, total):
        percent = (current / total) * 100
        try:
            await callback_query.edit_message_text(
                f"📤 **Uploading file...**\n\n"
                f"📁 **File:** {filename[:50]}{'...' if len(filename) > 50 else ''}\n"
                f"📊 **Size:** {file_size_mb:.1f}MB\n"
                f"📈 **Upload Progress:** {percent:.1f}%\n"
                f"🚀 **Using MTProto** (No size limits!)"
            )
        except:
            pass
    
    # Send the file
    try:
        caption = (
            f"✅ **Download Completed!**\n\n"
            f"🎬 **Quality:** {selected_quality}\n"
            f"📊 **Size:** {file_size_mb:.1f}MB\n"
            f"🚀 **Downloaded via MTProto**\n\n"
            f"🤖 @YourBotUsername"
        )
        
        if quality == 'audio':
            await client.send_audio(
                chat_id=callback_query.message.chat.id,
                audio=file_path,
                caption=caption,
                progress=upload_progress
            )
        else:
            await client.send_video(
                chat_id=callback_query.message.chat.id,
                video=file_path,
                caption=caption,
                progress=upload_progress
            )
        
        await callback_query.edit_message_text(
            f"✅ **Success!**\n\n"
            f"File uploaded successfully!\n"
            f"Size: {file_size_mb:.1f}MB\n\n"
            f"Send me another YouTube link to download more videos! 🎥",
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        await callback_query.edit_message_text(
            f"❌ **Upload Error**\n\n"
            f"Failed to upload the file.\n"
            f"File size: {file_size_mb:.1f}MB\n\n"
            f"This might be due to:\n"
            f"• Network issues\n"
            f"• Temporary server problems\n"
            f"• File corruption\n\n"
            f"Please try again."
        )
    
    finally:
        # Clean up the file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        
        # Clean up stored URL
        app.user_data.pop(f"url_{msg_id}", None)

@app.on_message(filters.text & ~filters.regex(r'(youtube\.com|youtu\.be)') & ~filters.command(['start', 'help']))
async def handle_other_messages(client: Client, message: Message):
    """Handle non-YouTube URL messages"""
    await message.reply_text(
        "Please send me a YouTube video URL to download.\n\n"
        "Use /help for more information about supported formats and features.\n\n"
        "🚀 **This bot supports files up to 2GB using MTProto!**"
    )

if __name__ == "__main__":
    print("🚀 Starting YouTube Downloader Bot with MTProto...")
    print("📁 No file size limits (up to 2GB)!")
    print("⚡ High-speed downloads and uploads")
    
    # Run the bot
    app.run()
