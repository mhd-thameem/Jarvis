import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from faster_whisper import WhisperModel

# Ensure import matches your capitalized folder
from Core.brain import consult_jarvis

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

if not BOT_TOKEN or not ALLOWED_USER_ID:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_ALLOWED_USER_ID in .env")

ALLOWED_USER_ID = int(ALLOWED_USER_ID)

# Lightweight Whisper model for transcribing mobile voice notes
print("Loading Whisper STT engine...")
stt_model = WhisperModel("base.en", device="cpu", compute_type="int8")

def is_authorized(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == ALLOWED_USER_ID

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text("Jarvis online. Send text or a voice note anytime.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    user_query = update.message.text
    # Show typing indicator
    await update.message.chat.send_action("typing")

    reply = consult_jarvis(user_query, category="telegram_text")
    await update.message.reply_text(reply)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    await update.message.chat.send_action("record_voice")

    # Download voice note file
    voice_file = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    await voice_file.download_to_drive(tmp_path)

    # Transcribe locally on CPU
    segments, _ = stt_model.transcribe(tmp_path, beam_size=1)
    transcript = " ".join([segment.text for segment in segments]).strip()

    # Clean up temp file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    if not transcript:
        await update.message.reply_text("Could not clearly decode audio.")
        return

    # Process with Jarvis brain
    reply = consult_jarvis(transcript, category="telegram_voice")
    await update.message.reply_text(f"🎤 *You said:* {transcript}\n\n🤖 *Jarvis:* {reply}", parse_mode="Markdown")

def main():
    print("Starting Jarvis Telegram Daemon...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_polling()

if __name__ == "__main__":
    main()