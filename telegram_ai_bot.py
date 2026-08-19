  """
Simple AI Telegram support bot — FREE version, using Google's Gemini API.

How it works (in plain terms):
1. Telegram sends us a message when a customer writes to the bot.
2. We forward that message to Gemini, along with a "business briefing"
   (BUSINESS_INFO below) so it answers with real facts about the business.
3. We send Gemini's answer back to the customer on Telegram.

Before running:
- Set two environment variables (never write secrets directly in code):
    TELEGRAM_TOKEN   -> the token BotFather gave you
    GEMINI_API_KEY   -> your free key from aistudio.google.com/app/apikey
- Install requirements:  pip install -r requirements.txt
"""

import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from google import genai
from google.genai import types

# ---------- 1. Load secrets from the environment (not hardcoded) ----------
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

# ---------- 2. Set up basic logging so you can see what's happening ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- 3. Set up the Gemini client ----------
gemini = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.6-flash"  # current fast model, covered by the free tier

# ---------- 4. YOUR BUSINESS BRIEFING — edit this section for your business ----------
BUSINESS_INFO = """
You are the AI support and sales assistant for Hateta Tech Solutions, based in Ethiopia.
Contact: +251 960957751 | hatetatech@gmail.com | Telegram: @HatetaTech

SERVICES (only mention prices/timelines below — never invent others):
- Business websites: starting from 15,000 ETB, typical turnaround 3–7 days
- AI chatbots: starting from 10,000 ETB, typical turnaround 1–2 weeks
- AI automation / custom AI tools: no fixed price or timeline — depends on
  requirements, always recommend a free consultation for these

RULES:
- "Starting from" = not guaranteed final price. Never invent discounts,
  exact quotes, features, timelines, payment details, or company history
  beyond what's stated here.
- Payment: bank transfer, 25% down payment after agreement. Don't share
  account details — say the team will provide them.
- If you don't know something, say so honestly and offer a team follow-up.
  Never guess, never pretend to be human — you're an AI assistant.

CONSULTATION / LEAD CAPTURE:
Offer a free consultation when the customer wants to proceed, asks to talk
to a human, needs custom pricing, or has a question you can't answer.
Collect only what's missing: business name, Telegram username, business
type, desired service, budget. Don't re-ask for info already given.

STYLE:
Friendly, professional, concise — short Telegram-style messages, not
essays. Minimal emojis. Don't repeatedly push for a consultation.
Reply in whichever language the customer is using — English or Amharic.
"""

# ---------- 5. The core logic: message in -> Gemini -> message out ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Message from {chat_id}: {user_message}")

    try:
        response = gemini.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=BUSINESS_INFO,
                max_output_tokens=500,
                # "low" = answer faster, less internal reasoning. Good fit for
                # straightforward support questions. Raise to "medium" only if
                # you notice answers getting noticeably shallow.
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        reply_text = response.text
    except Exception as e:
        # Logged in full so you can see the REAL cause in your Railway logs
        # (rate limit, timeout, etc) — the customer only ever sees the friendly line.
        logger.error(f"Gemini API error: {type(e).__name__}: {e}")
        reply_text = "Sorry, I'm having trouble right now — please try again shortly."

    await update.message.reply_text(reply_text)


# ---------- 5b. What happens when someone taps Telegram's "Start" button ----------
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm the support assistant for Habesha Tech Solutions. "
        "Ask me anything about our services, pricing, or how to get started."
    )


# ---------- 6. Start the bot ----------
def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot is starting... press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
