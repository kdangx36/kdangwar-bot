import telebot, json, os, re, threading
from telebot import types
from flask import Flask, request, jsonify

# ================= CẤU HÌNH THÔNG TIN =================
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642
STK = "0325683433"
CTK = "NGUYEN KHOA DANG"
BANK = "ABBank"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "shop_data.json"

# ================= QUẢN LÝ DỮ LIỆU =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "accounts": [], "last_id": 0}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "accounts": [], "last_id": 0}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= GIAO DIỆN MENU (UI/UX) =================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Mua Acc", "💳 Nạp Tiền", "👤 Cá Nhân", "🛠 Admin")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    welcome_msg = (
        f"👑 *KHANH SHOP FREE FIRE*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 Uy tín - Chất lượng - Tự động 24/7\n"
        f"👉 Chọn tính năng bên dưới để bắt đầu:"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_menu(), parse_mode="Markdown")

# ================= CÁC CHỨC NĂNG CHÍNH =================
@bot.message_handler(func=lambda m: m.text == "🛒 Mua Acc")
def buy_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎟️ Acc Clone (Lv5)", callback_data="list_Lv5"),
        types.InlineKeyboardButton("💎 Acc KC (VIP)", callback_data="list_KC")
    )
    bot.send_message(message.chat.id, "📦 *DANH SÁCH TÀI KHOẢN*", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def nap_tien(message):
    msg = (
        f"💳 *HƯỚNG DẪN NẠP TIỀN TỰ ĐỘNG*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏦 Ngân hàng: {BANK}\n"
        f"💳 Số TK: `{STK}`\n"
        f"👤 Chủ TK: {CTK}\n"
        f"📝 Nội dung CK: `NAP {message.from_user.id}`\n\n"
        f"⚠️ *LƯU Ý:* Ghi đúng nội dung để hệ thống cộng tiền trong 30 giây."
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 Cá Nhân")
def profile(message):
    data = load_data()
    uid = str(message.from_user.id)
    balance = data["users"].get(uid, 0)
    msg = (
        f"👤 *THÔNG TIN TÀI KHOẢN*\n"
        f"🆔 ID: `{uid}`\n"
        f"💰 Số dư: *{balance:,} VNĐ*"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

# ================= WEBHOOK (SERVER API) =================
@app.route('/webhook/abbank', methods=['POST'])
def abbank_webhook():
    try:
        req = request.get_json()
        print(f"Log Webhook: {req}") # In log để debug
        
        description = str(req.get("description") or req.get("content") or "").upper()
        amount = int(req.get("amount") or 0)
        
        # Regex tìm mã NAP + ID
        match = re.search(r'NAP\s*(\d+)', description)
        
        if match and amount > 0:
            uid = match.group(1)
            data = load_data()
            data["users"][uid] = data["users"].get(uid, 0) + amount
            save_data(data)
            
            try:
                bot.send_message(int(uid), f"✅ *Nạp tiền thành công!*\n💰 Cộng: *{amount:,} VNĐ*\n📊 Số dư mới cập nhật.")
            except:
                pass
            return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"status": "ignored"}), 200

# ================= CHẠY SERVER =================
if __name__ == "__main__":
    # Chạy Flask ở luồng riêng (Port 10000 là mặc định của Render)
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    bot.infinity_polling()
