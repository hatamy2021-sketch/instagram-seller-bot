#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اسکریپت تنظیم پایگاه داده برای ربات تلگرام
"""

import mysql.connector
from mysql.connector import Error
import sys

def create_database():
    """ایجاد پایگاه داده"""
    
    # اتصال به سرور MySQL بدون پایگاه داده مشخص
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        
        cursor = connection.cursor()
        
        # ایجاد پایگاه داده
        cursor.execute('CREATE DATABASE IF NOT EXISTS instagram_seller_bot')
        print('✅ پایگاه داده ایجاد شد')
        
        # انتخاب پایگاه داده
        cursor.execute('USE instagram_seller_bot')
        
        # ایجاد جداول
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        cursor.execute('''
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
        
        connection.commit()
        print('✅ جداول ایجاد شدند')
        
        cursor.close()
        connection.close()
        
        print('\n✅ تنظیم پایگاه داده به موفقیت انجام شد!')
        print('\n📝 نکات مهم:')
        print('1. فایل .env را تنظیم کنید')
        print('2. توکن ربات را در .env وارد کنید')
        print('3. شناسه ادمین را در .env وارد کنید')
        print('4. دستور "python bot.py" را اجرا کنید')
        
    except Error as e:
        print(f'❌ خطا: {e}')
        sys.exit(1)

if __name__ == '__main__':
    create_database()
