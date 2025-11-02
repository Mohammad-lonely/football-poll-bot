import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# دیکشنری برای ذخیره اطلاعات شرکت‌کنندگان
# ساختار: {chat_id: {day: {user_id: {'name': str, 'count': int}}}}
participants = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام خوش‌آمدگویی"""
    await update.message.reply_text(
        "سلام! 👋\n\n"
        "⚽️ **بات نظرسنجی فوتبال**\n\n"
        "برای شروع، یکی از دستورات زیر را انتخاب کنید:\n\n"
        "🟡 /thursday - نظرسنجی پنج‌شنبه\n"
        "🟢 /friday - نظرسنجی جمعه",
        parse_mode='Markdown'
    )

async def start_poll(update: Update, context: ContextTypes.DEFAULT_TYPE, day_name: str, day_emoji: str):
    """شروع نظرسنجی برای روز مشخص"""
    chat_id = update.message.chat_id
    
    # اگر این روز برای این چت در دیکشنری نیست، اضافه کن
    if chat_id not in participants:
        participants[chat_id] = {}
    if day_name not in participants[chat_id]:
        participants[chat_id][day_name] = {}
    
    await show_main_poll(update.message, chat_id, day_name, day_emoji)

async def thursday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نظرسنجی پنج‌شنبه"""
    await start_poll(update, context, "پنج‌شنبه", "🟡")

async def friday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نظرسنجی جمعه"""
    await start_poll(update, context, "جمعه", "🟢")

async def show_main_poll(message, chat_id, day_name, day_emoji):
    """نمایش نظرسنجی اصلی"""
    # محاسبه تعداد کل
    total_people = sum(data['count'] for data in participants.get(chat_id, {}).get(day_name, {}).values())
    total_participants = len(participants.get(chat_id, {}).get(day_name, {}))
    
    keyboard = [
        [InlineKeyboardButton("✅ شرکت می‌کنم", callback_data=f"participate_{day_name}")],
        [InlineKeyboardButton("📊 مشاهده لیست", callback_data=f"show_status_{day_name}")],
        [InlineKeyboardButton("🗑 ریست نظرسنجی", callback_data=f"reset_poll_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"⚽️ **نظرسنجی فوتبال - {day_emoji} {day_name}**\n\n"
        "برای ثبت‌نام روی دکمه زیر کلیک کنید:\n\n"
        f"👥 تعداد کل: {total_people} نفر\n"
        f"👤 تعداد شرکت‌کنندگان: {total_participants} نفر"
    )
    
    await message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def participate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ثبت‌نام کاربر و انتخاب تعداد افراد"""
    query = update.callback_query
    await query.answer()
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("participate_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    # اگر گروه در دیکشنری نیست، اضافه کن
    if chat_id not in participants:
        participants[chat_id] = {}
    if day_name not in participants[chat_id]:
        participants[chat_id][day_name] = {}
    
    # اگر کاربر قبلاً ثبت‌نام نکرده، با 1 نفر شروع کن
    if user_id not in participants[chat_id][day_name]:
        participants[chat_id][day_name][user_id] = {'name': user_name, 'count': 1}
    
    current_count = participants[chat_id][day_name][user_id]['count']
    
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"decrease_{day_name}"),
            InlineKeyboardButton(f"👥 {current_count} نفر", callback_data="show_count"),
            InlineKeyboardButton("➕", callback_data=f"increase_{day_name}")
        ],
        [InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{day_name}")],
        [InlineKeyboardButton("❌ انصراف و حذف", callback_data=f"cancel_participation_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"سلام {user_name}! 👋\n\n"
             f"**{day_emoji} {day_name}**\n\n"
             f"تعداد افرادی که می‌آورید را انتخاب کنید:\n"
             f"(خودتان + همراهان)\n\n"
             f"تعداد فعلی: **{current_count} نفر**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def increase_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """افزایش تعداد افراد"""
    query = update.callback_query
    await query.answer()
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("increase_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if chat_id in participants and day_name in participants[chat_id] and user_id in participants[chat_id][day_name]:
        participants[chat_id][day_name][user_id]['count'] += 1
        current_count = participants[chat_id][day_name][user_id]['count']
        
        keyboard = [
            [
                InlineKeyboardButton("➖", callback_data=f"decrease_{day_name}"),
                InlineKeyboardButton(f"👥 {current_count} نفر", callback_data="show_count"),
                InlineKeyboardButton("➕", callback_data=f"increase_{day_name}")
            ],
            [InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{day_name}")],
            [InlineKeyboardButton("❌ انصراف و حذف", callback_data=f"cancel_participation_{day_name}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"سلام {user_name}! 👋\n\n"
                 f"**{day_emoji} {day_name}**\n\n"
                 f"تعداد افرادی که می‌آورید را انتخاب کنید:\n"
                 f"(خودتان + همراهان)\n\n"
                 f"تعداد فعلی: **{current_count} نفر**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def decrease_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کاهش تعداد افراد"""
    query = update.callback_query
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("decrease_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    if chat_id in participants and day_name in participants[chat_id] and user_id in participants[chat_id][day_name]:
        if participants[chat_id][day_name][user_id]['count'] > 1:
            participants[chat_id][day_name][user_id]['count'] -= 1
            await query.answer()
        else:
            await query.answer("حداقل 1 نفر باید باشد!", show_alert=True)
            return
        
        current_count = participants[chat_id][day_name][user_id]['count']
        
        keyboard = [
            [
                InlineKeyboardButton("➖", callback_data=f"decrease_{day_name}"),
                InlineKeyboardButton(f"👥 {current_count} نفر", callback_data="show_count"),
                InlineKeyboardButton("➕", callback_data=f"increase_{day_name}")
            ],
            [InlineKeyboardButton("✅ تایید", callback_data=f"confirm_{day_name}")],
            [InlineKeyboardButton("❌ انصراف و حذف", callback_data=f"cancel_participation_{day_name}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"سلام {user_name}! 👋\n\n"
                 f"**{day_emoji} {day_name}**\n\n"
                 f"تعداد افرادی که می‌آورید را انتخاب کنید:\n"
                 f"(خودتان + همراهان)\n\n"
                 f"تعداد فعلی: **{current_count} نفر**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def confirm_participation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید نهایی شرکت"""
    query = update.callback_query
    await query.answer("ثبت شد! ✅")
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("confirm_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    
    # محاسبه تعداد کل
    total_people = sum(data['count'] for data in participants.get(chat_id, {}).get(day_name, {}).values())
    total_participants = len(participants.get(chat_id, {}).get(day_name, {}))
    
    keyboard = [
        [InlineKeyboardButton("✅ شرکت می‌کنم", callback_data=f"participate_{day_name}")],
        [InlineKeyboardButton("📊 مشاهده لیست", callback_data=f"show_status_{day_name}")],
        [InlineKeyboardButton("🗑 ریست نظرسنجی", callback_data=f"reset_poll_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"⚽️ **نظرسنجی فوتبال - {day_emoji} {day_name}**\n\n"
        "برای ثبت‌نام روی دکمه زیر کلیک کنید:\n\n"
        f"👥 تعداد کل: {total_people} نفر\n"
        f"👤 تعداد شرکت‌کنندگان: {total_participants} نفر"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def cancel_participation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف شرکت کاربر"""
    query = update.callback_query
    await query.answer("حذف شد! ❌")
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("cancel_participation_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    
    if chat_id in participants and day_name in participants[chat_id] and user_id in participants[chat_id][day_name]:
        del participants[chat_id][day_name][user_id]
    
    # محاسبه تعداد کل
    total_people = sum(data['count'] for data in participants.get(chat_id, {}).get(day_name, {}).values())
    total_participants = len(participants.get(chat_id, {}).get(day_name, {}))
    
    keyboard = [
        [InlineKeyboardButton("✅ شرکت می‌کنم", callback_data=f"participate_{day_name}")],
        [InlineKeyboardButton("📊 مشاهده لیست", callback_data=f"show_status_{day_name}")],
        [InlineKeyboardButton("🗑 ریست نظرسنجی", callback_data=f"reset_poll_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"⚽️ **نظرسنجی فوتبال - {day_emoji} {day_name}**\n\n"
        "برای ثبت‌نام روی دکمه زیر کلیک کنید:\n\n"
        f"👥 تعداد کل: {total_people} نفر\n"
        f"👤 تعداد شرکت‌کنندگان: {total_participants} نفر"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کامل شرکت‌کنندگان"""
    query = update.callback_query
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("show_status_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    
    if chat_id not in participants or day_name not in participants[chat_id] or not participants[chat_id][day_name]:
        await query.answer("هنوز کسی ثبت‌نام نکرده!", show_alert=True)
        return
    
    await query.answer()
    
    # ساخت لیست شرکت‌کنندگان
    status_text = f"📊 **لیست شرکت‌کنندگان - {day_emoji} {day_name}:**\n\n"
    total_people = 0
    
    for i, (user_id, data) in enumerate(participants[chat_id][day_name].items(), 1):
        status_text += f"{i}. {data['name']}: {data['count']} نفر\n"
        total_people += data['count']
    
    status_text += f"\n👥 **جمع کل: {total_people} نفر**\n"
    status_text += f"👤 **تعداد شرکت‌کنندگان: {len(participants[chat_id][day_name])} نفر**"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_to_poll_{day_name}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=status_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def back_to_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به صفحه اصلی نظرسنجی"""
    query = update.callback_query
    await query.answer()
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("back_to_poll_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    
    # محاسبه تعداد کل
    total_people = sum(data['count'] for data in participants.get(chat_id, {}).get(day_name, {}).values())
    total_participants = len(participants.get(chat_id, {}).get(day_name, {}))
    
    keyboard = [
        [InlineKeyboardButton("✅ شرکت می‌کنم", callback_data=f"participate_{day_name}")],
        [InlineKeyboardButton("📊 مشاهده لیست", callback_data=f"show_status_{day_name}")],
        [InlineKeyboardButton("🗑 ریست نظرسنجی", callback_data=f"reset_poll_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"⚽️ **نظرسنجی فوتبال - {day_emoji} {day_name}**\n\n"
        "برای ثبت‌نام روی دکمه زیر کلیک کنید:\n\n"
        f"👥 تعداد کل: {total_people} نفر\n"
        f"👤 تعداد شرکت‌کنندگان: {total_participants} نفر"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def reset_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ریست کردن نظرسنجی برای هفته جدید"""
    query = update.callback_query
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("reset_poll_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    
    # بررسی اینکه آیا کاربر ادمین گروه است یا خیر
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        is_admin = chat_member.status in ['creator', 'administrator']
    except:
        is_admin = False
    
    if not is_admin:
        await query.answer("⚠️ فقط ادمین‌ها می‌توانند نظرسنجی را ریست کنند!", show_alert=True)
        return
    
    # نمایش تایید
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، ریست کن", callback_data=f"confirm_reset_{day_name}"),
            InlineKeyboardButton("❌ انصراف", callback_data=f"cancel_reset_{day_name}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.answer()
    await query.edit_message_text(
        text=f"⚠️ **هشدار!**\n\n"
             f"آیا مطمئن هستید که می‌خواهید نظرسنجی **{day_emoji} {day_name}** را ریست کنید؟\n\n"
             f"❗️ تمام اطلاعات ثبت‌نام شده حذف خواهد شد!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید نهایی ریست"""
    query = update.callback_query
    await query.answer("نظرسنجی ریست شد! ✅")
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("confirm_reset_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    
    # ریست کردن داده‌ها
    if chat_id in participants and day_name in participants[chat_id]:
        participants[chat_id][day_name] = {}
    
    keyboard = [
        [InlineKeyboardButton("✅ شرکت می‌کنم", callback_data=f"participate_{day_name}")],
        [InlineKeyboardButton("📊 مشاهده لیست", callback_data=f"show_status_{day_name}")],
        [InlineKeyboardButton("🗑 ریست نظرسنجی", callback_data=f"reset_poll_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"⚽️ **نظرسنجی فوتبال - {day_emoji} {day_name}**\n\n"
        "برای ثبت‌نام روی دکمه زیر کلیک کنید:\n\n"
        "👥 تعداد کل: 0 نفر\n"
        "👤 تعداد شرکت‌کنندگان: 0 نفر"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def cancel_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """انصراف از ریست"""
    query = update.callback_query
    await query.answer("انصراف داده شد")
    
    # استخراج نام روز از callback_data
    day_name = query.data.replace("cancel_reset_", "")
    day_emoji = "🟡" if day_name == "پنج‌شنبه" else "🟢"
    
    chat_id = query.message.chat_id
    
    # محاسبه تعداد کل
    total_people = sum(data['count'] for data in participants.get(chat_id, {}).get(day_name, {}).values())
    total_participants = len(participants.get(chat_id, {}).get(day_name, {}))
    
    keyboard = [
        [InlineKeyboardButton("✅ شرکت می‌کنم", callback_data=f"participate_{day_name}")],
        [InlineKeyboardButton("📊 مشاهده لیست", callback_data=f"show_status_{day_name}")],
        [InlineKeyboardButton("🗑 ریست نظرسنجی", callback_data=f"reset_poll_{day_name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        f"⚽️ **نظرسنجی فوتبال - {day_emoji} {day_name}**\n\n"
        "برای ثبت‌نام روی دکمه زیر کلیک کنید:\n\n"
        f"👥 تعداد کل: {total_people} نفر\n"
        f"👤 تعداد شرکت‌کنندگان: {total_participants} نفر"
    )
    
    await query.edit_message_text(
        text=message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک‌های دکمه"""
    query = update.callback_query
    
    if query.data.startswith("participate_"):
        await participate(update, context)
    elif query.data.startswith("increase_"):
        await increase_count(update, context)
    elif query.data.startswith("decrease_"):
        await decrease_count(update, context)
    elif query.data.startswith("confirm_"):
        await confirm_participation(update, context)
    elif query.data.startswith("cancel_participation_"):
        await cancel_participation(update, context)
    elif query.data.startswith("show_status_"):
        await show_status(update, context)
    elif query.data.startswith("back_to_poll_"):
        await back_to_poll(update, context)
    elif query.data.startswith("reset_poll_"):
        await reset_poll(update, context)
    elif query.data.startswith("confirm_reset_"):
        await confirm_reset(update, context)
    elif query.data.startswith("cancel_reset_"):
        await cancel_reset(update, context)
    elif query.data == "show_count":
        await query.answer()

def main():
    """راه‌اندازی بات"""
    # توکن بات خود را اینجا قرار دهید
    TOKEN = "YOUR_BOT_TOKEN"
    
    # ساخت Application
    application = Application.builder().token(TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("thursday", thursday))
    application.add_handler(CommandHandler("friday", friday))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # شروع بات
    print("بات شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
