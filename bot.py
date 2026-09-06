import requests
import random
import os
import sys
import time

# ── تنظیمات ────────────────────────────────────────────────
BOT_TOKEN   = os.environ.get('BOT_TOKEN')
GROUP1_ID   = os.environ.get('GROUP1_ID')
GROUP2_ID   = os.environ.get('GROUP2_ID')

target_group = sys.argv[1] if len(sys.argv) > 1 else "group1"

# چک اولیه متغیرهای ضروری
if not BOT_TOKEN:
    print("❌ BOT_TOKEN در محیط تعریف نشده است (GitHub Secrets)")
    sys.exit(1)

# دیکشنری گروه‌ها → خواناتر و گسترش‌پذیرتر
GROUPS = {
    "group1": {
        "chat_id": GROUP1_ID,
        "module_name": "messages_group1",
        "label": "Group 1"
    },
    "group2": {
        "chat_id": GROUP2_ID,
        "module_name": "messages_group2",
        "label": "Group 2"
    }
}

if target_group not in GROUPS:
    print(f"❌ گروه نامعتبر: {target_group} (فقط group1 یا group2 مجاز است)")
    sys.exit(1)

group = GROUPS[target_group]
chat_id = group["chat_id"]

if not chat_id:
    print(f"❌ {group['label']}_ID در محیط تعریف نشده است")
    sys.exit(1)

# ایمپورت دینامیک پیام‌ها
try:
    messages_mod = __import__(group["module_name"])
    MESSAGES = messages_mod.MESSAGES
except ImportError as e:
    print(f"❌ خطا در ایمپورت فایل پیام‌ها: {e}")
    print(f"   مطمئن شوید فایل {group['module_name']}.py وجود دارد")
    sys.exit(1)
except AttributeError:
    print(f"❌ فایل {group['module_name']}.py متغیر MESSAGES ندارد")
    sys.exit(1)

# ── توابع ──────────────────────────────────────────────────
def send_message(chat_id: str, text: str, retries: int = 3) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,   # اختیاری – جلوگیری از پیش‌نمایش لینک
    }

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                print(f"✅ پیام ارسال شد به {group['label']} | وضعیت: 200")
                return True

            print(f"  تلاش {attempt} ناموفق – کد {resp.status_code}")
            print(f"  پاسخ: {resp.text[:180]}")

            if resp.status_code == 429:  # rate limit
                time.sleep(12)
            elif attempt < retries:
                time.sleep(3 + attempt * 2)  # backoff ساده: 5s → 7s → 9s

        except requests.RequestException as e:
            print(f"  خطای شبکه/درخواست تلاش {attempt}: {e}")
            if attempt < retries:
                time.sleep(4 + attempt * 3)

    print(f"⛔️ ارسال پیام به {group['label']} پس از {retries} تلاش ناموفق ماند")
    return False


def main():
    print(f"▶ شروع ارسال به {group['label']} (target: {target_group})")
    print(f"زمان اجرا: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")

    message_type = "lucy_hot"

    try:
        messages_list = MESSAGES[message_type]
    except KeyError:
        print(f"❌ دسته پیام '{message_type}' در MESSAGES وجود ندارد")
        sys.exit(1)

    if not messages_list:
        print("❌ لیست پیام‌ها خالی است")
        sys.exit(1)

    message = random.choice(messages_list)

    # چک طول پیام (تلگرام محدودیت دارد)
    if len(message) > 4090:
        message = message[:4080] + " ... (کوتاه شده)"
        print("⚠️ پیام خیلی بلند بود → کوتاه شد")

    print(f"پیام انتخابی: {message[:60]}{'...' if len(message)>60 else ''}")

    success = send_message(chat_id, message)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ خطای غیرمنتظره در اجرای اصلی: {type(e).__name__}: {e}")
        sys.exit(1)