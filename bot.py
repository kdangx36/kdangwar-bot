import telebot
from telebot import types
import json
import os
from flask import Flask, request, jsonify
from threading import Thread

# 1. THÔNG TIN CỦA BẠN ĐÃ ĐƯỢC THAY ĐỔI CHUẨN XÁC
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642

# Cấu hình ví ZaloPay chính chủ của bạn để tạo mã QR tự động
MA_NGAN_HANG = "ZALOPAY"      # Hệ thống VietQR hỗ trợ quét thẳng vào ví ZaloPay
SO_TAI_KHOAN = "0325683433"  # Số điện thoại ZaloPay của bạn
TEN_CHU_TK = "NGUYEN KHOA DANG" # Tên chủ ví viết hoa không dấu

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DATA_FILE = "shop_data.json"

# Kiểm tra và khởi tạo dữ liệu kho acc/số dư
if not os.path.exists(DATA_FILE):
    initial_data = {
        "users": {},
        "accounts": [
            {"id": 1, "price": 20000, "info": "TK: dangnguyen123 | MK: dang123456", "status": "ConHang"},
            {"id": 2, "price": 50000, "info": "TK: top1ff@gmail.com | MK: freefire2026", "status": "ConHang"}
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

# BÀN PHÍM MENU CHUYÊN NGHIỆP DƯỚI THANH TIN NHẮN (UI như các shop lớn)
def tao_ban_phim_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_buy = types.KeyboardButton("🛒 Mua Acc Free Fire")
    btn_nap = types.KeyboardButton("💳 Nạp Tiền")
    btn_user = types.KeyboardButton("👤 Tài Khoản")
    markup.add(btn_buy, btn_nap, btn_user)
    return markup

# ================= CỔNG WEBHOOK API NHẬN TIỀN TỰ ĐỘNG =================
@app.route('/', methods=['GET'])
def home():
    return "Server Bot ZaloPay đang chạy ngon lành!", 200

@app.route('/webhook/zalopay', methods=['POST'])
def zalopay_webhook():
    try:
        req_data = request.get_json()
        noi_dung = req_data.get("description", "").upper() 
        so_tien = int(req_data.get("amount", 0))
        
        if "NAP" in noi_dung and so_tien > 0:
            parts = noi_dung.split()
            khach_id = None
            for p in parts:
                if p.isdigit() and len(p) >= 8:
                    khach_id = p
                    break
            
            if khach_id:
                data = doc_data()
                if khach_id in data["users"]:
                    data["users"][khach_id] += so_tien
                else:
                    data["users"][khach_id] = so_tien
                ghi_data(data)
                
                bot.send_message(khach_id, f"🎉 Tài khoản của bạn đã được cộng tự động *+{so_tien:,} VNĐ* thành công!", parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"💰 Khách ID `{khach_id}` vừa nạp thành công *{so_tien:,}đ* vào hệ thống.", parse_mode="Markdown")
                return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Lỗi API Server:", str(e))
    return jsonify({"status": "error"}), 400
# ====================================================================

# LỆNH /START
@bot.message_handler(commands=['start'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
        
    van_ban = (
        f"🔥 *WELCOME TO KHANH SHOP FREE FIRE* 🔥\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"Xin chào *{message.from_user.first_name}*!\n"
        f"Hệ thống phân phối Acc tự động nâng cấp giao diện VIP.\n"
        f"Vui lòng sử dụng các nút bấm dưới thanh tin nhắn để chọn chức năng 👇"
    )
    bot.send_message(message.chat.id, van_ban, reply_markup=tao_ban_phim_chinh(), parse_mode="Markdown")

# XỬ LÝ CLICK NÚT BẤM DƯỚI THANH TIN NHẮN
@bot.message_handler(func=lambda message: True)
def xu_ly_giao_dien(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
    so_du = data["users"][u_id]

    # GIAO DIỆN TÀI KHOẢN
    if message.text == "👤 Tài Khoản":
        van_ban = (
            f"👤 *THÔNG TIN TÀI KHOẢN NGƯỜI DÙNG*\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"▶️ Khách hàng: *{message.from_user.first_name}*\n"
            f"🆔 ID cá nhân: `{u_id}`\n"
            f"💰 Số dư shop: *{so_du:,} VNĐ*\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
        )
        bot.send_message(message.chat.id, van_ban, parse_mode="Markdown")

    # GIAO DIỆN NẠP TIỀN + TỰ ĐỘNG IN ẢNH MÃ QR CỦA BẠN
    elif message.text == "💳 Nạp Tiền":
        noi_dung_ck = f"NAP{u_id}"
        
        # CÔNG THỨC GEN QR: Sử dụng API VietQR để tự tạo mã QR ví ZaloPay kèm nội dung chuyển khoản tự động
        link_qr = f"https://api.vietqr.io/image/970439-{SO_TAI_KHOAN}-compact2.jpg?accountName={TEN_CHU_TK}&addInfo={noi_dung_ck}"
        
        van_ban_nap = (
            f"💳 *THÔNG TIN NẠP TIỀN TỰ ĐỘNG* 💳\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"🏦 Hình thức nạp: *Ví điện tử ZALOPAY*\n"
            f"💳 Số tài khoản/SĐT: `{SO_TAI_KHOAN}`\n"
            f"👤 Chủ tài khoản: *{TEN_CHU_TK}*\n"
            f"📝 Nội dung bắt buộc: `{noi_dung_ck}`\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"⚠️ *MẸO NẠP NHANH:* Bạn chỉ cần **lưu ảnh QR phía trên** về điện thoại, sau đó mở ứng dụng Quét mã của ZaloPay hoặc Ngân hàng lên quét là xong, hệ thống tự động điền đúng tên và nội dung, chờ 30 giây là có tiền!"
        )
        bot.send_photo(message.chat.id, photo=link_qr, caption=van_ban_nap, parse_mode="Markdown")

    # GIAO DIỆN MUA ACC
    elif message.text == "🛒 Mua Acc Free Fire":
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_hang = True
                markup.add(types.InlineKeyboardButton(f"🎟 ACC #{acc['id']} — Giá: {acc['price']:,}đ", callback_data=f"buy_{acc['id']}"))
        
        van_ban_kho = "🛒 *DANH SÁCH ACC FREE FIRE ĐANG CÓ TRONG KHO:*" if co_hang else "❌ Hiện tại kho hàng đã hết sạch sản phẩm!"
        bot.send_message(message.chat.id, van_ban_kho, reply_markup=markup, parse_mode="Markdown")

# XỬ LÝ TRỪ TIỀN KHI MUA ACC
@bot.callback_query_handler(func=lambda call: True)
def callback_mua_acc(call):
    u_id = str(call.from_user.id)
    data = doc_data()
    so_du = data["users"].get(u_id, 0)

    if call.data.startswith("buy_"):
        acc_id = int(call.data.split("_")[1])
        target_acc = None
        for acc in data["accounts"]:
            if acc["id"] == acc_id and acc["status"] == "ConHang":
                target_acc = acc
                break
        if not target_acc:
            bot.answer_callback_query(call.id, "❌ Acc này vừa mới có người mua mất rồi!")
            return
        if so_du < target_acc["price"]:
            bot.answer_callback_query(call.id, f"❌ Số dư không đủ! Vui lòng chọn 'Nạp Tiền' dưới bàn phím.", show_alert=True)
        else:
            data["users"][u_id] -= target_acc["price"]
            target_acc["status"] = "DaBan"
            ghi_data(data)
            
            bot.send_message(
                call.message.chat.id,
                f"🎉 *MUA ACC THÀNH CÔNG!*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎟 Mã sản phẩm: `# {target_acc['id']}`\n💰 Chi phí: -{target_acc['price']:,}đ\n🔑 *THÔNG TIN ĐĂNG NHẬP:*\n`{target_acc['info']}`\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "✅ Mua tài khoản thành công!")

def run_api():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    t = Thread(target=run_api)
    t.start()
    bot.infinity_polling()
  
