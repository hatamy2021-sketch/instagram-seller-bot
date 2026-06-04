import telebot
from telebot import types
from config import ADMIN_ID, SERVICES
from database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()

class AdminPanel:
    def __init__(self, bot):
        self.bot = bot
        self.admin_states = {}
    
    def check_admin(self, user_id):
        """بررسی ادمین"""
        return user_id == ADMIN_ID
    
    def get_statistics(self):
        """دریافت آمار"""
        # تعداد کاربران
        self.bot.execute_query('SELECT COUNT(*) as count FROM users')
        users_count = self.bot.cursor.fetchone()['count']
        
        # تعداد سفارش‌ها
        self.bot.execute_query('SELECT COUNT(*) as count FROM orders')
        orders_count = self.bot.cursor.fetchone()['count']
        
        # کل درآمد
        self.bot.execute_query('SELECT SUM(price) as total FROM orders WHERE status="completed"')
        result = self.bot.cursor.fetchone()
        total_revenue = result['total'] if result['total'] else 0
        
        return {
            'users_count': users_count,
            'orders_count': orders_count,
            'total_revenue': total_revenue
        }
    
    def send_statistics(self, user_id):
        """ارسال آمار"""
        stats = self.get_statistics()
        
        message = f"""
📊 **آمار سیستم**

👥 تعداد کاربران: {stats['users_count']}
📦 تعداد سفارش‌ها: {stats['orders_count']}
💰 کل درآمد: {stats['total_revenue']:,} تومان
        """
        
        self.bot.send_message(user_id, message, parse_mode='Markdown')
    
    def send_pending_orders(self, user_id):
        """ارسال سفارش‌های در انتظار"""
        orders = db.get_pending_orders()
        
        if not orders:
            self.bot.send_message(user_id, '❌ سفارش در انتظار وجود ندارد.')
            return
        
        for order in orders:
            message = f"""
📦 **سفارش #{order['order_id']}**

👤 کاربر: {order['user_id']}
📱 خدمت: {SERVICES[order['service_type']]['name']}
📊 مقدار: {order['quantity']}
💰 قیمت: {order['price']:,} تومان
👤 حساب: {order['target_account']}
⏰ تاریخ: {order['created_at']}
            """
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton('✅ تکمیل', callback_data=f'complete_order_{order["order_id"]}'),
                types.InlineKeyboardButton('❌ لغو', callback_data=f'reject_order_{order["order_id"]}')
            )
            
            self.bot.send_message(user_id, message, reply_markup=markup, parse_mode='Markdown')
    
    def complete_order(self, order_id):
        """تکمیل سفارش"""
        db.update_order_status(order_id, 'completed')
    
    def reject_order(self, order_id):
        """رد سفارش و بازگرداندن موجودی"""
        order = db.execute_query('SELECT * FROM orders WHERE order_id = %s', (order_id,))
        if order:
            user_id = order[0]['user_id']
            price = order[0]['price']
            db.add_balance(user_id, price)
            db.update_order_status(order_id, 'rejected')

# توابع ادمین برای bot.py
def setup_admin_handlers(bot):
    """تنظیم handlers ادمین"""
    admin_panel = AdminPanel(bot)
    
    @bot.message_handler(commands=['admin'])
    def admin_command(message):
        if not admin_panel.check_admin(message.from_user.id):
            bot.send_message(message.from_user.id, '❌ شما دسترسی ندارید!')
            return
        
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(
            types.KeyboardButton('📊 آمار'),
            types.KeyboardButton('📦 سفارش‌های در انتظار'),
            types.KeyboardButton('💳 درخواست‌های پرداخت'),
            types.KeyboardButton('💬 پیام‌های پشتیبانی'),
            types.KeyboardButton('👥 مدیریت کاربران'),
            types.KeyboardButton('🚪 خروج')
        )
        
        bot.send_message(message.from_user.id, '🛡️ **پنل ادمین**', reply_markup=markup, parse_mode='Markdown')
    
    @bot.message_handler(func=lambda message: message.text == '📊 آمار')
    def show_stats(message):
        if not admin_panel.check_admin(message.from_user.id):
            return
        admin_panel.send_statistics(message.from_user.id)
    
    @bot.message_handler(func=lambda message: message.text == '📦 سفارش‌های در انتظار')
    def show_pending(message):
        if not admin_panel.check_admin(message.from_user.id):
            return
        admin_panel.send_pending_orders(message.from_user.id)
    
    return admin_panel
