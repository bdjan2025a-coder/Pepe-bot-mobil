# --- বিভাগ ১: প্রয়োজনীয় লাইব্রেরি ইম্পোর্ট ---
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from supabase import create_client, Client

# লগিং সেটআপ করা হচ্ছে, যাতে সার্ভারে কোনো সমস্যা হলে তা সহজেই বোঝা যায়
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- বিভাগ ২: আপনার দেওয়া তথ্য এবং ডেটাবেস সংযোগ ---
# Supabase সংযোগের তথ্য
SUPABASE_URL = "https://dzyyqvpzqspaarizvlly.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6eXlxdnB6cXNwYWFyaXp2bGx5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTY2OTM2MywiZXhwIjoyMDcxMjQ1MzYzfQ.7PInJsA5WFnV_Vu9VGCrF16dXS695gXat0L2W8fG51A"

# টেলিগ্রাম বট টোকেন
TELEGRAM_BOT_TOKEN = "8382556728:AAHtxUaLDcnGzPAdY2gUy2rwbgMvqJVh4nA"

# আপনার ব্লগার সাইটের URL
WEB_APP_URL = "https://pepe-coin.blogspot.com/"

# Supabase ক্লায়েন্ট তৈরি করা হচ্ছে
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    logger.info("Supabase ডেটাবেসের সাথে সফলভাবে সংযোগ স্থাপন হয়েছে।")
except Exception as e:
    logger.error(f"Supabase সংযোগ স্থাপনে মারাত্মক ত্রুটি: {e}")
    # সংযোগ স্থাপন না হলে বট চালু হবে না
    exit()


# --- বিভাগ ৩: '/start' কমান্ডের মূল ফাংশন ---
# যখন কোনো ব্যবহারকারী বটকে '/start' মেসেজ পাঠাবে, তখন এই ফাংশনটি কাজ করবে
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    new_user_id = user.id
    
    try:
        # ধাপ ক: ব্যবহারকারী ডেটাবেসে আগে থেকেই আছে কিনা তা চেক করা
        response = supabase.table('users').select('user_id').eq('user_id', new_user_id).execute()

        # ধাপ খ: যদি ব্যবহারকারী নতুন হয় (অর্থাৎ ডেটাবেসে তাকে খুঁজে পাওয়া না যায়)
        if not response.data:
            logger.info(f"নতুন ব্যবহারকারী সনাক্ত হয়েছে: ID={new_user_id}, Username=@{user.username}")
            
            # ধাপ গ: ব্যবহারকারী কি কারো রেফারেলে এসেছে তা চেক করা
            referrer_id = None
            if context.args and len(context.args) > 0:
                try:
                    # /start এর পরে থাকা আইডিটিকে সংখ্যায় পরিণত করার চেষ্টা
                    referrer_id = int(context.args[0])
                    logger.info(f"ব্যবহারকারী {new_user_id} রেফারার {referrer_id} এর মাধ্যমে এসেছেন।")
                except ValueError:
                    referrer_id = None
                    logger.warning(f"অবৈধ রেফারেল কোড পাওয়া গেছে: {context.args[0]}")

            # ধাপ ঘ: যদি একজন বৈধ রেফারার পাওয়া যায় এবং সে নিজে নিজেকে রেফার না করে
            if referrer_id and referrer_id != new_user_id:
                # রেফারারের তথ্য ডেটাবেস থেকে খুঁজে বের করা হচ্ছে
                referrer_response = supabase.table('users').select('points', 'referral_count').eq('user_id', referrer_id).execute()
                
                if referrer_response.data:
                    # রেফারারকে বোনাস দেওয়া হচ্ছে
                    current_points = referrer_response.data[0]['points']
                    current_referrals = referrer_response.data[0]['referral_count']
                    
                    new_points = current_points + 10  # রেফারেল বোনাস পয়েন্ট
                    new_referral_count = current_referrals + 1
                    
                    # ডেটাবেসে রেফারারের নতুন তথ্য আপডেট করা হচ্ছে
                    supabase.table('users').update({
                        'points': new_points,
                        'referral_count': new_referral_count
                    }).eq('user_id', referrer_id).execute()
                    logger.info(f"রেফারার {referrer_id} কে সফলভাবে বোনাস দেওয়া হয়েছে। নতুন পয়েন্ট: {new_points}, নতুন রেফারেল সংখ্যা: {new_referral_count}")

            # ধাপ ঙ: নতুন ব্যবহারকারীকে ডেটাবেসে যোগ করা
            supabase.table('users').insert({
                'user_id': new_user_id,
                'username': user.username,
                'points': 0,
                'referral_count': 0
            }).execute()
            logger.info(f"নতুন ব্যবহারকারী {new_user_id} কে সফলভাবে ডেটাবেসে যোগ করা হয়েছে।")

    except Exception as e:
        logger.error(f"/start কমান্ড হ্যান্ডেল করার সময় একটি সমস্যা হয়েছে: {e}")

    # সব ব্যবহারকারীকেই (নতুন বা পুরাতন) ওয়েব অ্যাপ খোলার বাটনসহ মেসেজ পাঠানো হবে
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Open App & Start Collecting", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    
    await update.message.reply_text(
        "Welcome to Pepe Coin! 🐸\n\nClick the button below to open the app and start collecting points!",
        reply_markup=keyboard
    )


# --- বিভাগ ৪: বট চালু করার মূল অংশ ---
def main() -> None:
    """বটটি শুরু এবং চালু রাখার জন্য মূল ফাংশন।"""
    
    # ApplicationBuilder ব্যবহার করে বট তৈরি করা হচ্ছে
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # বটকে বলা হচ্ছে যে /start কমান্ড পেলে উপরের 'start' ফাংশনটি চালাতে হবে
    application.add_handler(CommandHandler("start", start))

    logger.info("বট চালু হচ্ছে...")
    
    # বটটি মেসেজের জন্য অপেক্ষা করা শুরু করবে
    application.run_polling()

if __name__ == '__main__':
    main()
