# تنظیمات ربات تلگرام
import os
from dotenv import load_dotenv

load_dotenv()

# توکن ربات تلگرام
BOT_TOKEN = '8851801825:AAH-w21pkd7GO3pFMNQMQ2pVJ5zq8wc_Jas'

# تنظیمات پایگاه داده
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'instagram_seller_bot'

# تنظیمات ادمین
ADMIN_ID = 123456789  # شناسه تلگرام ادمین (بعدا تغییر دهید)

# تنظیمات خدمات
SERVICES = {
    'instagram_followers': {
        'name': 'دنبال کننده اینستاگرام',
        'prices': {
            '100': 50000,      # 100 followers = 50,000 تومان
            '500': 200000,     # 500 followers = 200,000 تومان
            '1000': 350000,    # 1000 followers = 350,000 تومان
            '5000': 1500000,   # 5000 followers = 1,500,000 تومان
        }
    },
    'instagram_likes': {
        'name': 'لایک اینستاگرام',
        'prices': {
            '100': 40000,
            '500': 180000,
            '1000': 300000,
            '5000': 1200000,
        }
    },
    'instagram_views': {
        'name': 'بازدید اینستاگرام',
        'prices': {
            '500': 30000,
            '1000': 50000,
            '5000': 200000,
            '10000': 350000,
        }
    },
    'instagram_comments': {
        'name': 'کامنت اینستاگرام',
        'prices': {
            '10': 50000,
            '50': 200000,
            '100': 350000,
        }
    },
    'instagram_stories_views': {
        'name': 'بازدید استوری',
        'prices': {
            '500': 40000,
            '1000': 70000,
            '5000': 300000,
        }
    },
    'instagram_saves': {
        'name': 'ذخیره اینستاگرام',
        'prices': {
            '100': 60000,
            '500': 250000,
            '1000': 450000,
        }
    },
    'instagram_shares': {
        'name': 'اشتراک‌گذاری اینستاگرام',
        'prices': {
            '50': 80000,
            '100': 150000,
            '500': 600000,
        }
    },
}

# تنظیمات سطح احراز هویت
VERIFICATION_LEVELS = {
    '0': 'تایید نشده',
    '1': 'تایید شماره تلگرام',
    '2': 'تایید شماره کارت',
}

# مدت زمان انقضای کد تایید (به ثانیه)
VERIFICATION_CODE_EXPIRY = 600  # 10 دقیقه

# حداقل موجودی برای سفارش
MIN_BALANCE_FOR_ORDER = 10000  # 10,000 تومان
