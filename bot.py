import telebot, json, os, random, re, threading
from telebot import types
from flask import Flask, request, jsonify

# ================= CẤU HÌNH =================
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642
MA_NGAN_HANG = "970425"
SO_TAI_KHOAN = "0325683433"
TEN_CHU_TK = "NGUYEN KHOA DANG"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "shop_data.json"

# ================= KHỞI TẠO DỮ LIỆU =================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "accounts": [], "last_id": 0}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= MENU =================
def get_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Mua Acc", "💳 Nạp Tiền", "👤 Cá Nhân")
    if int(user_id) == ADMIN_ID:
        markup.add("🛠 Admin Panel")
    return markup

# ================= XỬ LÝ NHẮN TIN =================
@bot.message_handler(commands=['start'])
def start(m):
    welcome = (f"👑 *SHOP KDANGX - NGON BỔ RẺ*\n"
               f"💎 Uy tín - Tự động - Bảo mật 24/7\n\n"
               f"👇 Chọn tính năng bên dưới để bắt đầu:")
    bot.send_message(m.chat.id, welcome, reply_markup=get_main_menu(m.from_user.id), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛒 Mua Acc")
def buy_menu(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎟️ Clone Lv5", callback_data="list_Lv5"),
               types.InlineKeyboardButton("💎 Clone KC", callback_data="list_KC"))
    bot.send_message(m.chat.id, "📦 *Chọn loại tài khoản:*", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 Nạp Tiền")
def nap_tien(m):
    markup = types.InlineKeyboardMarkup()
    for v in [10000, 20000, 50000, 100000]:
        markup.add(types.InlineKeyboardButton(f"{v:,} VNĐ", callback_data=f"nap_{v}"))
    bot.send_message(m.chat.id, "💳 *Chọn mệnh giá cần nạp:*", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 Cá Nhân")
def profile(m):
    data = load_data()
    sodu = data["users"].get(str(m.from_user.id), 0)
    bot.send_message(m.chat.id, f"👤 *THÔNG TIN TÀI KHOẢN*\n🆔 ID: `{m.from_user.id}`\n💰 Số dư: *{sodu:,} VNĐ*", parse_mode="Markdown")

# ================= ADMIN PANEL =================
@bot.message_handler(func=lambda m: m.text == "🛠 Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_p(m):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Thêm Acc", callback_data="adm_add"),
               types.InlineKeyboardButton("➖ Xoá Acc", callback_data="adm_del"))
    bot.send_message(m.chat.id, "🛠 *ADMIN DASHBOARD*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_"))
def admin_action(c):
    if c.data == "adm_add":
        msg = bot.send_message(c.message.chat.id, "Nhập: `Loại|Giá|Info`\n(Ví dụ: `Lv5|20000|dang123@g.com|pass`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, lambda m: [
            data := load_data(),
            data["last_id"] := data["last_id"] + 1,
            data["accounts"].append({"id": data["last_id"], "cat": m.text.split("|")[0], "price": int(m.text.split("|")[1]), "info": m.text.split("|")[2], "status": "ConHang"}),
            save_data(data),
            bot.reply_to(m, "✅ Đã thêm!")
        ])
    elif c.data == "adm_del":
        data = load_data()
        markup = types.InlineKeyboardMarkup()
        for a in data["accounts"]:
            if a["status"] == "ConHang":
                markup.add(types.InlineKeyboardButton(f"Xoá #{a['id']} ({a['cat']})", callback_data=f"del_{a['id']}"))
        bot.send_message(c.message.chat.id, "Chọn Acc cần xoá:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del_"))
def admin_del_proc(c):
    data = load_data()
    data["accounts"] = [a for a in data["accounts"] if a["id"] != int(c.data.split("_")[1])]
    save_data(data)
    bot.answer_callback_query(c.id, "Đã xoá!")

# ================= CALLBACK & WEBHOOK =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("list_"))
def list_acc(c):
    cat = c.data.split("_")[1]
    data = load_data()
    markup = types.InlineKeyboardMarkup()
    found = False
    for a in data["accounts"]:
        if a["cat"] == cat and a["status"] == "ConHang":
            markup.add(types.InlineKeyboardButton(f"🎟️ Acc #{a['id']} — {a['price']:,}đ", callback_data=f"buy_{a['id']}"))
            found = True
    if found: bot.send_message(c.message.chat.id, f"📦 *Danh sách {cat}:*", reply_markup=markup, parse_mode="Markdown")
    else: bot.answer_callback_query(c.id, "❌ Hết hàng!")

@bot.callback_query_handler(func=lambda c: c.data.startswith("nap_"))
def nap_qr(c):
    val = c.data.split("_")[1]
    noi_dung = f"NAP{c.from_user.id}"
    url = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.png?accountName={TEN_CHU_TK}&amount={val}&addInfo={noi_dung}"
    bot.send_photo(c.message.chat.id, url, caption=f"📝 *Nội dung CK:* `{noi_dung}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_proc(c):
    id_acc = int(c.data.split("_")[1])
    data = load_data()
    u_id = str(c.from_user.id)
    acc = next((a for a in data["accounts"] if a["id"] == id_acc), None)
    
    if acc and acc["status"] == "ConHang":
        if data["users"].get(u_id, 0) >= acc["price"]:
            data["users"][u_id] -= acc["price"]
            acc["status"] = "DaBan"
            save_data(data)
            bot.send_message(c.message.chat.id, f"✅ *Giao dịch thành công!*\n🎟️ Acc: `{acc['info']}`", parse_mode="Markdown")
        else: bot.answer_callback_query(c.id, "❌ Không đủ tiền!")
    else: bot.answer_callback_query(c.id, "❌ Acc đã bán!")

@app.route('/webhook/abbank', methods=['POST'])
def abbank_webhook():
    try:
        req = request.get_json()
        desc = str(req.get("description") or req.get("content") or "").upper()
        amt = int(req.get("amount") or 0)
        match = re.search(r'NAP(\d+)', desc)
        if match and amt > 0:
            uid = match.group(1)
            data = load_data()
            data["users"][uid] = data["users"].get(uid, 0) + amt
            save_data(data)
            try: bot.send_message(int(uid), f"💰 *Cộng {amt:,}đ thành công!*")
            except: pass
            return jsonify({"status": "success"}), 200
    except: pass
    return "OK", 200

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000)).start()
    bot.infinity_polling()
