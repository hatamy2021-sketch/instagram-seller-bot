#!/bin/bash
# اسکریپت نصب ربات روی cPanel

echo "📦 شروع نصب ربات تلگرام..."

# نصب بسته‌ها
echo "📥 نصب بسته‌های مورد نیاز..."
pip install -r requirements.txt

echo "✅ بسته‌ها نصب شدند"

# ایجاد پایگاه داده
echo "🗄️  ایجاد پایگاه داده..."
python setup.py

echo "✅ نصب کامل شد!"
echo ""
echo "📝 نکات بعدی:"
echo "1. فایل .env را تنظیم کنید"
echo "2. ADMIN_ID خود را در .env وارد کنید"
echo "3. دستور زیر را اجرا کنید:"
echo "   nohup python bot.py > bot.log 2>&1 &"
