import mysql.connector
from mysql.connector import Error
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """اتصال به پایگاه داده"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info('اتصال به پایگاه داده موفق')
        except Error as e:
            logger.error(f'خطا در اتصال به پایگاه داده: {e}')
            raise
    
    def create_tables(self):
        """ایجاد جداول پایگاه داده"""
        try:
            # جدول کاربران
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    phone_number VARCHAR(20),
                    card_number VARCHAR(20),
                    verification_level INT DEFAULT 0,
                    balance BIGINT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول کدهای تایید
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_codes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    code VARCHAR(6),
                    type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_used BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول سفارش‌ها
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    service_type VARCHAR(100),
                    quantity INT,
                    price BIGINT,
                    target_account VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول تاریخچه پرداخت‌ها
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    payment_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    amount BIGINT,
                    card_number VARCHAR(20),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # جدول پیام‌های ادمین
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_messages (
                    message_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    message TEXT,
                    status VARCHAR(50) DEFAULT 'unread',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    replied_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            self.connection.commit()
            logger.info('جداول پایگاه داده ایجاد شد')
        except Error as e:
            logger.error(f'خطا در ایجاد جداول: {e}')
            raise
    
    def execute_query(self, query, params=None):
        """اجرای درخواست SQL"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f'خطا در اجرای درخواست: {e}')
            self.connection.rollback()
            return None
    
    def insert_user(self, user_id, username):
        """افزودن کاربر جدید"""
        query = 'INSERT INTO users (user_id, username) VALUES (%s, %s)'
        return self.execute_query(query, (user_id, username))
    
    def get_user(self, user_id):
        """دریافت اطلاعات کاربر"""
        query = 'SELECT * FROM users WHERE user_id = %s'
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()
    
    def update_user_verification(self, user_id, level):
        """به‌روزرسانی سطح تایید کاربر"""
        query = 'UPDATE users SET verification_level = %s WHERE user_id = %s'
        return self.execute_query(query, (level, user_id))
    
    def add_balance(self, user_id, amount):
        """افزودن موجودی به حساب کاربر"""
        query = 'UPDATE users SET balance = balance + %s WHERE user_id = %s'
        return self.execute_query(query, (amount, user_id))
    
    def get_balance(self, user_id):
        """دریافت موجودی کاربر"""
        user = self.get_user(user_id)
        return user['balance'] if user else 0
    
    def create_order(self, user_id, service_type, quantity, price, target_account):
        """ایجاد سفارش جدید"""
        query = '''
            INSERT INTO orders (user_id, service_type, quantity, price, target_account)
            VALUES (%s, %s, %s, %s, %s)
        '''
        self.execute_query(query, (user_id, service_type, quantity, price, target_account))
        self.cursor.execute('SELECT LAST_INSERT_ID()')
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_user_orders(self, user_id):
        """دریافت سفارش‌های کاربر"""
        query = 'SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC'
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()
    
    def get_pending_orders(self):
        """دریافت سفارش‌های در انتظار"""
        query = 'SELECT * FROM orders WHERE status = "pending" ORDER BY created_at ASC'
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def update_order_status(self, order_id, status):
        """به‌روزرسانی وضعیت سفارش"""
        query = 'UPDATE orders SET status = %s, completed_at = NOW() WHERE order_id = %s'
        return self.execute_query(query, (status, order_id))
    
    def deduct_balance(self, user_id, amount):
        """کسر موجودی از حساب کاربر"""
        query = 'UPDATE users SET balance = balance - %s WHERE user_id = %s AND balance >= %s'
        return self.execute_query(query, (amount, user_id, amount))
    
    def close(self):
        """بستن اتصال"""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            logger.info('اتصال بسته شد')
