import telebot
from telebot import types
import json
import os
import random
from flask import Flask, request, jsonify
from threading import Thread

# ================= CONFIG THÔNG TIN CHÍNH CHỦ CỦA BẠN =================
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642

# Cấu hình chuẩn định danh VietQR của ngân hàng ABBank NGUYEN KHOA DANG
MA_NGAN_HANG = "970425"        
SO_TAI_KHOAN = "0325683433"    
TEN_CHU_TK = "NGUYEN KHOA DANG" 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "shop_data.json"

# Kiểm tra dữ liệu bộ nhớ shop
if not os.path.exists(DATA_FILE):
    initial_data = {
        "users": {},
        "accounts": [
            # 5 Acc Clone thường
            {"id": 1, "type": "Clone Lv5", "price": 2999, "info": "TK: clone1@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 2, "type": "Clone Lv5", "price": 2999, "info": "TK: clone2@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 3, "type": "Clone Lv5", "price": 2999, "info": "TK: clone3@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 4, "type": "Clone Lv5", "price": 2999, "info": "TK: clone4@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 5, "type": "Clone Lv5", "price": 2999, "info": "TK: clone5@gmail.com | MK: 123456", "status": "ConHang"},
            # 5 Acc Clone KC
            {"id": 6, "type": "CloneKC", "price": 29999, "info": "TK: kcvip1@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 7, "type": "CloneKC", "price": 29999, "info": "TK: kcvip2@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 8, "type": "CloneKC", "price": 29999, "info": "TK: kcvip3@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 9, "type": "CloneKC", "price": 29999, "info": "TK: kcvip4@gmail.com | MK: 123456", "status": "ConHang"},
            {"id": 10, "type": "CloneKC", "price": 29999, "info": "TK: kcvip5@gmail.com | MK: 123456", "status": "ConHang"}
        ]
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=4)

def doc_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def ghi_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# MENU CHÍNH CẬP NHẬT MỚI
def tao_ban_phim_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_buy = types.KeyboardButton("🛒 MUA ACC CLONE")
    btn_buy_kc = types.KeyboardButton("💎 MUA ACC CLONE KC")
    btn_nap = types.KeyboardButton("💳 NẠP TIỀN SHOP")
    btn_user = types.KeyboardButton("👤 TÀI KHOẢN CỦA TÔI")
    markup.add(btn_buy, btn_buy_kc, btn_nap, btn_user)
    return markup

# ================= CỔNG WEBHOOK =================
@app.route('/', methods=['GET'])
def home():
    return "Server Bot ABBank VIP đang chạy!", 200

@app.route('/webhook/abbank', methods=['POST'])
def abbank_webhook():
    try:
        req_data = request.get_json()
        noi_dung = req_data.get("description", "").upper() 
        so_tien = int(req_data.get("amount", 0))
        if "NAP" in noi_dung and so_tien > 0:
            khach_id = noi_dung.replace("NAP", "")[:10]
            if khach_id.isdigit():
                data = doc_data()
                if khach_id in data["users"]: data["users"][khach_id] += so_tien
                else: data["users"][khach_id] = so_tien
                ghi_data(data)
                bot.send_message(khach_id, f"🎉 *CỘNG TIỀN THÀNH CÔNG!*\n Tài khoản của bạn: *+{so_tien:,} VNĐ*.", parse_mode="Markdown")
                return jsonify({"status": "success"}), 200
    except: pass
    return jsonify({"status": "error"}), 400

# ================= CÁC LỆNH BOT =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
    ten_khach = message.from_user.first_name if message.from_user.first_name else "Thành Viên VIP"
    van_ban = (f"👑 *SHOP ACC KDANGX VIP* 👑\n━━━━━━━━━━━━━━━━━━━━━━\n👋 Chào {ten_khach}, chọn dịch vụ bên dưới:" )
    bot.send_message(message.chat.id, van_ban, reply_markup=tao_ban_phim_chinh(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def xu_ly_giao_dien(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"]: data["users"][u_id] = 0; ghi_data(data)
    so_du = data["users"][u_id]

    if message.text == "👤 TÀI KHOẢN CỦA TÔI":
        bot.send_message(message.chat.id, f"👤 *THÔNG TIN*\n💰 Số dư: *{so_du:,} VNĐ*", parse_mode="Markdown")
        
    elif message.text == "💳 NẠP TIỀN SHOP":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for val in [10000, 20000, 50000, 100000]:
            markup.add(types.InlineKeyboardButton(f"{val:,}đ", callback_data=f"amount_{val}"))
        bot.send_message(message.chat.id, "💳 Chọn mệnh giá:", reply_markup=markup)

    elif message.text in ["🛒 MUA ACC CLONE", "💎 MUA ACC CLONE KC"]:
        acc_type = "Clone" if message.text == "🛒 MUA ACC CLONE" else "CloneKC"
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang" and acc["type"] == acc_type:
                co_hang = True
                label = f"🎟️ ACC #{acc['id']} — {acc['price']:,}đ"
                markup.add(types.InlineKeyboardButton(label, callback_data=f"buy_{acc['id']}"))
        
        text = f"🛒 *DANH SÁCH {acc_type} TRONG KHO:*" if co_hang else "❌ Hết hàng!"
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_xu_ly(call):
    u_id = str(call.from_user.id)
    data = doc_data()

    if call.data.startswith("amount_"):
        so_tien = int(call.data.split("_")[1])
        noi_dung = f"NAP{u_id}{random.randint(10000,99999)}"
        link_qr = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.png?accountName={TEN_CHU_TK}&amount={so_tien}&addInfo={noi_dung}"
        bot.send_photo(call.message.chat.id, photo=link_qr, caption=f"💰 Nội dung CK: `{noi_dung}`", parse_mode="Markdown")

    elif call.data.startswith("buy_"):
        acc_id = int(call.data.split("_")[1])
        acc = next((a for a in data["accounts"] if a["id"] == acc_id), None)
        if acc and acc["status"] == "ConHang":
            if data["users"].get(u_id, 0) >= acc["price"]:
                data["users"][u_id] -= acc["price"]
                acc["status"] = "DaBan"
                ghi_data(data)
                bot.send_message(call.message.chat.id, f"✅ Mua thành công!\n🔑 Info: `{acc['info']}`", parse_mode="Markdown")
            else:
                bot.answer_callback_query(call.id, "❌ Không đủ tiền!")
        else:
            bot.answer_callback_query(call.id, "❌ Hết hàng!")

def run_api(): app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    t = Thread(target=run_api)
    t.start()
    bot.infinity_polling()
