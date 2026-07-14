import telebot
from telebot import types
import json, os, random
from flask import Flask, request, jsonify
from threading import Thread

# ================= CONFIG =================
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642  # ĐIỀN ID CỦA BẠN VÀO ĐÂY
MA_NGAN_HANG = "970425"
SO_TAI_KHOAN = "0325683433"
TEN_CHU_TK = "NGUYEN KHOA DANG"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "shop_data.json"

# ================= DATA MANAGER =================
def init_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": {}, "accounts": [], "last_id": 0}, f, ensure_ascii=False, indent=4)

def doc_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)

def ghi_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

init_data()

# ================= UI HELPERS =================
def menu_chinh(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Mua Acc", "💳 Nạp Tiền", "👤 Cá Nhân")
    if int(user_id) == ADMIN_ID:
        markup.add("🛠 Admin Panel")
    return markup

# ================= BOT COMMANDS & LOGIC =================
@bot.message_handler(commands=['start'])
def start(m):
    welcome_text = (
        f"👑 *Chào mừng đến với SHOP KDANGX*\n"
        f"💎 _Ngon - Bổ - Rẻ - Tự động 24/7_\n\n"
        f"Chọn tính năng bên dưới để bắt đầu giao dịch."
    )
    bot.send_message(m.chat.id, welcome_text, reply_markup=menu_chinh(m.from_user.id), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛒 Mua Acc")
def chon_loai(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Lv5 (Clone)", callback_data="show_Lv5"))
    markup.add(types.InlineKeyboardButton("KC (Clone)", callback_data="show_KC"))
    bot.send_message(m.chat.id, "📦 *Vui lòng chọn loại Acc bạn cần:*", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛠 Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_panel(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Thêm Acc", callback_data="admin_add"),
               types.InlineKeyboardButton("➖ Xoá Acc", callback_data="admin_del"))
    bot.send_message(m.chat.id, "🛠 *BẢNG ĐIỀU KHIỂN ADMIN*", reply_markup=markup, parse_mode="Markdown")

# Xử lý thêm/xoá acc (Dùng ForceReply để nhập liệu nhanh)
@bot.callback_query_handler(func=lambda c: c.data.startswith("admin_"))
def admin_actions(c):
    if c.data == "admin_add":
        msg = bot.send_message(c.message.chat.id, "Nhập theo định dạng:\n`Loại|Giá|Info`\nVí dụ: `Lv5|10000|abc@gmail.com|123`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add)
    elif c.data == "admin_del":
        data = doc_data()
        markup = types.InlineKeyboardMarkup()
        for acc in data["accounts"]:
            markup.add(types.InlineKeyboardButton(f"ID {acc['id']} | {acc['cat']} | {acc['price']}đ", callback_data=f"del_{acc['id']}"))
        bot.send_message(c.message.chat.id, "Chọn acc cần xoá:", reply_markup=markup)

def process_add(m):
    try:
        cat, price, info = m.text.split("|")
        data = doc_data()
        data["last_id"] += 1
        data["accounts"].append({"id": data["last_id"], "cat": cat, "price": int(price), "info": info, "status": "ConHang"})
        ghi_data(data)
        bot.reply_to(m, "✅ Thêm thành công!")
    except: bot.reply_to(m, "❌ Lỗi định dạng!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def process_del(c):
    acc_id = int(c.data.split("_")[1])
    data = doc_data()
    data["accounts"] = [a for a in data["accounts"] if a["id"] != acc_id]
    ghi_data(data)
    bot.answer_callback_query(c.id, "Đã xoá!")
    bot.delete_message(c.message.chat.id, c.message.message_id)

# ================= API WEBHOOK =================
@app.route('/webhook/abbank', methods=['POST'])
def abbank_webhook():
    req = request.get_json()
    noi_dung = req.get("description", "").upper()
    tien = int(req.get("amount", 0))
    # Giả định nội dung CK là "NAP [ID]"
    khach_id = noi_dung.replace("NAP", "").strip()
    if khach_id.isdigit():
        data = doc_data()
        data["users"][khach_id] = data["users"].get(khach_id, 0) + tien
        ghi_data(data)
        bot.send_message(int(khach_id), f"💰 *Cộng {tien:,}đ thành công!*", parse_mode="Markdown")
    return "OK", 200

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    bot.infinity_polling()
