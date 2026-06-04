import telebot
from telebot import types
import random
import string
from config import BOT_TOKEN, ADMIN_ID, SERVICES, VERIFICATION_LEVELS
from database import Database
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()

# تنظیمات کاربران (موقت)
user_states = {}
user_data = {}

# کدهای تایید
verification_codes = {}

def generate_verification_code():
    """تولید کد تایید 6 رقمی"""
    return ''.join(random.choices(string.digits, k=6))

def get_main_keyboard():
    """صفحه کلید اصلی"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('🛍️ خرید خدمات'),
        types.KeyboardButton('💰 موجودی'),
        types.KeyboardButton('📋 سفارش‌های من'),
        types.KeyboardButton('⚙️ تنظیمات'),
        types.KeyboardButton('💬 پشتیبانی'),
        types.KeyboardButton('ℹ️ درباره')
    )
    return markup

def get_services_keyboard():
    """صفحه کلید خدمات"""
    markup = types.InlineKeyboardMarkup()
    for service_key, service_info in SERVICES.items():
        callback_data = f'service_{service_key}'
        markup.add(types.InlineKeyboardButton(service_info['name'], callback_data=callback_data))
    markup.add(types.InlineKeyboardButton('⬅️ بازگشت', callback_data='back_to_menu'))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    """شروع ربات"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # بررسی کاربر موجود
    user = db.get_user(user_id)
    if not user:
        db.insert_user(user_id, username)
        bot.send_message(
            user_id,
            f'سلام {username}! 👋\n\nبه ربات فروش خدمات اینستاگرام خوش آمدید.\n\nابتدا باید احراز هویت کنید.',
            reply_markup=get_main_keyboard()
        )
        user_states[user_id] = 'awaiting_phone'
        send_verification_request(user_id)
    else:
        bot.send_message(
            user_id,
            f'خوش آمدید {username}! 🎉\n\nچه می‌تونم برای شما انجام بدم؟',
            reply_markup=get_main_keyboard()
        )

def send_verification_request(user_id):
    """ارسال درخواست تایید"""
    code = generate_verification_code()
    verification_codes[user_id] = code
    
    bot.send_message(
        user_id,
        f'🔐 **کد تایید شماره تلگرام شما:**\n\n`{code}`\n\nلطفاً این کد را برای من ارسال کنید:',
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_phone')
def verify_phone(message):
    """تایید شماره تلگرام"""
    user_id = message.from_user.id
    code = message.text.strip()
    
    if code == verification_codes.get(user_id):
        db.update_user_verification(user_id, 1)
        user_states[user_id] = 'awaiting_card'
        bot.send_message(
            user_id,
            '✅ شماره تلگرام شما تایید شد!\n\n🔐 حالا لطفاً **شماره کارت** خود را برای دریافت پول ارسال کنید:'
        )
    else:
        bot.send_message(user_id, '❌ کد اشتباه است. دوباره تلاش کنید:')

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_card')
def verify_card(message):
    """تایید شماره کارت"""
    user_id = message.from_user.id
    card_number = message.text.strip()
    
    if len(card_number) == 16 and card_number.isdigit():
        # ذخیره شماره کارت
        db.execute_query(
            'UPDATE users SET card_number = %s, verification_level = 2 WHERE user_id = %s',
            (card_number, user_id)
        )
        del user_states[user_id]
        
        bot.send_message(
            user_id,
            '✅ شماره کارت شما تایید شد!\n\n🎉 اکنون می‌تونید خدمات را خریداری کنید.',
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(user_id, '❌ شماره کارت باید 16 رقم باشد. دوباره تلاش کنید:')

@bot.message_handler(func=lambda message: message.text == '🛍️ خرید خدمات')
def show_services(message):
    """نمایش خدمات"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    
    if user['verification_level'] < 2:
        bot.send_message(user_id, '❌ ابتدا باید احراز هویت کنید!')
        return
    
    bot.send_message(
        user_id,
        '📱 **لطفاً یک خدمت را انتخاب کنید:**',
        reply_markup=get_services_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def select_service(call):
    """انتخاب خدمت"""
    user_id = call.from_user.id
    service_key = call.data.replace('service_', '')
    
    if service_key not in SERVICES:
        bot.answer_callback_query(call.id, '❌ خدمت نامعتبر')
        return
    
    service = SERVICES[service_key]
    user_data[user_id] = {'service_key': service_key, 'service': service}
    
    # نمایش قیمت‌ها
    message_text = f"💰 **{service['name']}**\n\nلطفاً مقدار را انتخاب کنید:\n\n"
    
    markup = types.InlineKeyboardMarkup()
    for quantity, price in service['prices'].items():
        text = f"{quantity} عدد - {price:,} تومان"
        callback_data = f"quantity_{service_key}_{quantity}"
        markup.add(types.InlineKeyboardButton(text, callback_data=callback_data))
    
    markup.add(types.InlineKeyboardButton('⬅️ بازگشت', callback_data='back_to_services'))
    
    bot.edit_message_text(
        message_text,
        call.from_user.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('quantity_'))
def select_quantity(call):
    """انتخاب مقدار"""
    user_id = call.from_user.id
    parts = call.data.split('_')
    service_key = parts[1]
    quantity = parts[2]
    
    user_data[user_id]['quantity'] = quantity
    
    bot.send_message(
        user_id,
        '📝 لطفاً **نام کاربری یا لینک اینستاگرام** خود را ارسال کنید:'
    )
    user_states[user_id] = 'awaiting_instagram_account'

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_instagram_account')
def get_instagram_account(message):
    """دریافت نام کاربری اینستاگرام"""
    user_id = message.from_user.id
    account = message.text.strip()
    
    if not account or len(account) < 3:
        bot.send_message(user_id, '❌ نام کاربری نامعتبر است. دوباره تلاش کنید:')
        return
    
    user_data[user_id]['account'] = account
    
    # محاسبه قیمت
    service_key = user_data[user_id]['service_key']
    quantity = user_data[user_id]['quantity']
    service = SERVICES[service_key]
    price = service['prices'][quantity]
    
    user = db.get_user(user_id)
    balance = user['balance']
    
    message_text = f"""
☑️ **خلاصه سفارش:**

📱 خدمت: {service['name']}
📊 مقدار: {quantity} عدد
💰 قیمت: {price:,} تومان
👤 حساب: {account}

💳 موجودی شما: {balance:,} تومان
    """
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('✅ تایید', callback_data='confirm_order'),
        types.InlineKeyboardButton('❌ لغو', callback_data='cancel_order')
    )
    
    if balance < price:
        message_text += f"\n\n⚠️ **موجودی کافی نیست!**\nشما باید {price - balance:,} تومان بیشتر واریز کنید."
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('💸 واریز پول', callback_data='deposit_money'),
            types.InlineKeyboardButton('❌ لغو', callback_data='cancel_order')
        )
    
    user_data[user_id]['price'] = price
    
    del user_states[user_id]
    bot.send_message(user_id, message_text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_order')
def confirm_order(call):
    """تایید سفارش"""
    user_id = call.from_user.id
    service_key = user_data[user_id]['service_key']
    quantity = user_data[user_id]['quantity']
    price = user_data[user_id]['price']
    account = user_data[user_id]['account']
    
    # کسر موجودی
    result = db.deduct_balance(user_id, price)
    
    if result is not None:
        # ایجاد سفارش
        order_id = db.create_order(user_id, service_key, quantity, price, account)
        
        bot.send_message(
            user_id,
            f"""✅ **سفارش شما ثبت شد!**

📋 شماره سفارش: {order_id}
🔄 وضعیت: در انتظار تکمیل

پس از تکمیل سفارش شما را مطلع می‌کنم.
            """,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
        # اطلاع به ادمین
        admin_message = f"""
📢 **سفارش جدید!**

👤 کاربر: {call.from_user.first_name}
🆔 شناسه: {user_id}
📋 شماره سفارش: {order_id}
📱 خدمت: {SERVICES[service_key]['name']}
📊 مقدار: {quantity}
💰 قیمت: {price:,} تومان
👤 حساب: {account}
        """
        bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
        
        del user_data[user_id]
    else:
        bot.send_message(user_id, '❌ موجودی کافی نیست!')

@bot.callback_query_handler(func=lambda call: call.data == 'deposit_money')
def deposit_money(call):
    """واریز پول"""
    user_id = call.from_user.id
    price = user_data[user_id]['price']
    user = db.get_user(user_id)
    needed = price - user['balance']
    
    bot.send_message(
        user_id,
        f"""💳 **واریز پول**

🏦 شماره کارت برای واریز: **6104337598756434**
پلتفرم: بانک ملی

💰 مبلغ مورد نیاز: {needed:,} تومان

پس از واریز، **شماره پیگیری** را برای من ارسال کنید:
        """,
        parse_mode='Markdown'
    )
    user_states[user_id] = 'awaiting_tracking_number'

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_tracking_number')
def get_tracking_number(message):
    """دریافت شماره پیگیری"""
    user_id = message.from_user.id
    tracking_number = message.text.strip()
    
    # ایجاد درخواست پرداخت
    price = user_data[user_id]['price']
    user = db.get_user(user_id)
    needed = price - user['balance']
    
    db.execute_query(
        'INSERT INTO payments (user_id, amount, card_number, status) VALUES (%s, %s, %s, "pending")',
        (user_id, needed, tracking_number)
    )
    
    bot.send_message(
        user_id,
        f"""✅ **درخواست پرداخت ثبت شد!**

📋 شماره پیگیری: {tracking_number}
💰 مبلغ: {needed:,} تومان
⏳ وضعیت: در انتظار تایید ادمین

بعد از تایید ادمین، موجودی شما اضافه می‌شود.
        """,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    
    # اطلاع به ادمین
    admin_message = f"""
💳 **درخواست پرداخت جدید!**

👤 کاربر: {message.from_user.first_name}
🆔 شناسه: {user_id}
💰 مبلغ: {needed:,} تومان
📋 شماره پیگیری: {tracking_number}

لطفاً درخواست را تایید یا رد کنید.
    """
    bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
    
    del user_states[user_id]

@bot.message_handler(func=lambda message: message.text == '💰 موجودی')
def show_balance(message):
    """نمایش موجودی"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0
    
    bot.send_message(
        user_id,
        f"""💰 **موجودی شما**

💳 موجودی فعلی: {balance:,} تومان
        """,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == '📋 سفارش‌های من')
def show_orders(message):
    """نمایش سفارش‌های کاربر"""
    user_id = message.from_user.id
    orders = db.get_user_orders(user_id)
    
    if not orders:
        bot.send_message(user_id, '❌ شما هنوز سفارشی نداشته‌اید.', reply_markup=get_main_keyboard())
        return
    
    message_text = '📋 **سفارش‌های شما:**\n\n'
    for order in orders:
        status_emoji = '⏳' if order['status'] == 'pending' else '✅'
        message_text += f"""{status_emoji} سفارش #{order['order_id']}
    خدمت: {SERVICES[order['service_type']]['name']}
    مقدار: {order['quantity']}
    وضعیت: {order['status']}
    تاریخ: {order['created_at']}

"""
    
    bot.send_message(user_id, message_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '⚙️ تنظیمات')
def settings(message):
    """تنظیمات"""
    user_id = message.from_user.id
    user = db.get_user(user_id)
    verification_level = VERIFICATION_LEVELS[str(user['verification_level'])]
    
    message_text = f"""
⚙️ **تنظیمات**

👤 نام کاربری: {user['username']}
🔐 سطح احراز هویت: {verification_level}
🆔 شناسه: {user_id}
    """
    
    bot.send_message(user_id, message_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == '💬 پشتیبانی')
def support(message):
    """پشتیبانی"""
    user_id = message.from_user.id
    bot.send_message(
        user_id,
        '💬 **پشتیبانی**\n\nلطفاً پیام خود را ارسال کنید:',
        parse_mode='Markdown'
    )
    user_states[user_id] = 'awaiting_support_message'

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'awaiting_support_message')
def receive_support_message(message):
    """دریافت پیام پشتیبانی"""
    user_id = message.from_user.id
    support_message = message.text
    
    db.execute_query(
        'INSERT INTO admin_messages (user_id, message) VALUES (%s, %s)',
        (user_id, support_message)
    )
    
    bot.send_message(
        user_id,
        '✅ پیام شما با موفقیت ارسال شد. پشتیبان زودتر پاسخ می‌دهد.',
        reply_markup=get_main_keyboard()
    )
    
    # اطلاع به ادمین
    bot.send_message(
        ADMIN_ID,
        f"""💬 **پیام پشتیبانی جدید!**

👤 کاربر: {message.from_user.first_name}
🆔 شناسه: {user_id}
📝 پیام: {support_message}
        """,
        parse_mode='Markdown'
    )
    
    del user_states[user_id]

@bot.message_handler(func=lambda message: message.text == 'ℹ️ درباره')
def about(message):
    """درباره"""
    bot.send_message(
        message.from_user.id,
        """ℹ️ **درباره ربات**

🤖 ربات فروش خدمات اینستاگرام
📱 فالو، لایک، بازدید و بیشتر

✨ ویژگی‌ها:
• احراز هویت کاربر
• پرداخت امن
• پشتیبانی 24/7
• سفارش‌های آنی

📞 تماس: @YourSupportBot
        """,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu(call):
    """بازگشت به منو اصلی"""
    bot.edit_message_text(
        '🏠 **منوی اصلی**',
        call.from_user.id,
        call.message.message_id,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_services')
def back_to_services(call):
    """بازگشت به خدمات"""
    bot.edit_message_text(
        '📱 **لطفاً یک خدمت را انتخاب کنید:**',
        call.from_user.id,
        call.message.message_id,
        reply_markup=get_services_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_order')
def cancel_order(call):
    """لغو سفارش"""
    user_id = call.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    bot.send_message(user_id, '❌ سفارش لغو شد.', reply_markup=get_main_keyboard())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """پنل ادمین"""
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.from_user.id, '❌ شما دسترسی ندارید!')
        return
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('📊 آمار'),
        types.KeyboardButton('📦 سفارش‌های در انتظار'),
        types.KeyboardButton('💳 درخواست‌های پرداخت'),
        types.KeyboardButton('💬 پیام‌های پشتیبانی'),
        types.KeyboardButton('👥 مدیریت کاربران')
    )
    
    bot.send_message(message.from_user.id, '🛡️ **پنل ادمین**', reply_markup=markup, parse_mode='Markdown')

if __name__ == '__main__':
    logger.info('ربات شروع شد...')
    db.create_tables()
    bot.infinity_polling()
