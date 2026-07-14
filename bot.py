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

# Cấu hình chuẩn định danh Napas của ví ZaloPay NGUYEN KHOA DANG
MA_NGAN_HANG = "970439"        
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

# MENU CHUYÊN NGHIỆP DƯỚI THANH TIN NHẮN
def tao_ban_phim_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_buy = types.KeyboardButton("🛒 Mua Acc Free Fire")
    btn_nap = types.KeyboardButton("💳 Nạp Tiền")
    btn_user = types.KeyboardButton("👤 Tài Khoản")
    markup.add(btn_buy, btn_nap, btn_user)
    return markup

# ================= CỔNG WEBHOOK AUTO CHECK TIỀN CỦA SHOP LỚN =================
@app.route('/', methods=['GET'])
def home():
    return "Server Bot ZaloPay VIP đang chạy cực mượt!", 200

@app.route('/webhook/zalopay', methods=['POST'])
def zalopay_webhook():
    try:
        req_data = request.get_json()
        noi_dung = req_data.get("description", "").upper() 
        so_tien = int(req_data.get("amount", 0))
        
        if "NAP" in noi_dung and so_tien > 0:
            # Tách chuỗi lấy ID khách (cắt chuỗi 10 số sau chữ NAP)
            khach_id = noi_dung.replace("NAP", "")[:10]
            
            if khach_id.isdigit():
                data = doc_data()
                if khach_id in data["users"]:
                    data["users"][khach_id] += so_tien
                else:
                    data["users"][khach_id] = so_tien
                ghi_data(data)
                
                bot.send_message(khach_id, f"🎉 *HỆ THỐNG CỘNG TIỀN THÀNH CÔNG!*\n Tài khoản của bạn đã được cộng tự động *+{so_tien:,} VNĐ*.", parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"💰 Admin ơi! Khách ID `{khach_id}` vừa nạp thành công *{so_tien:,}đ* qua ZaloPay.", parse_mode="Markdown")
                return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Lỗi API Webhook:", str(e))
    return jsonify({"status": "error"}), 400
# ====================================================================

# LỆNH /START KHỞI ĐỘNG BOT
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

# XỬ LÝ SỰ KIỆN NÚT BẤM DƯỚI THANH TIN NHẮN
@bot.message_handler(func=lambda message: True)
def xu_ly_giao_dien(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
    so_du = data["users"][u_id]

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

    # KHI KHÁCH BẤM NẠP TIỀN -> SHOW MENU CHỌN MỆNH GIÁ NHƯ SHOP LỚN
    elif message.text == "💳 Nạp Tiền":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("💵 10.000đ", callback_data="amount_10000")
        btn2 = types.InlineKeyboardButton("💵 20.000đ", callback_data="amount_20000")
        btn3 = types.InlineKeyboardButton("💵 50.000đ", callback_data="amount_50000")
        btn4 = types.InlineKeyboardButton("💵 100.000đ", callback_data="amount_100000")
        btn5 = types.InlineKeyboardButton("💵 200.000đ", callback_data="amount_200000")
        btn6 = types.InlineKeyboardButton("💵 500.000đ", callback_data="amount_500000")
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        
        bot.send_message(
            message.chat.id, 
            "💳 *VUI LÒNG CHỌN SỐ TIỀN BẠN MUỐN NẠP:*", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )

    elif message.text == "🛒 Mua Acc Free Fire":
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_hang = True
                markup.add(types.InlineKeyboardButton(f"🎟 ACC #{acc['id']} — Giá: {acc['price']:,}đ", callback_data=f"buy_{acc['id']}"))
        
        van_ban_kho = "🛒 *DANH SÁCH ACC FREE FIRE ĐANG CÓ TRONG KHO:*" if co_hang else "❌ Hiện tại kho hàng đã hết sạch sản phẩm!"
        bot.send_message(message.chat.id, van_ban_kho, reply_markup=markup, parse_mode="Markdown")

# XỬ LÝ SỰ KIỆN CHỌN SỐ TIỀN NẠP VÀ MUA ACC (CALLBACK DATA)
@bot.callback_query_handler(func=lambda call: True)
def callback_xu_ly(call):
    u_id = str(call.from_user.id)
    data = doc_data()

    # NẾU KHÁCH CHỌN MỆNH GIÁ NẠP TIỀN
    if call.data.startswith("amount_"):
        so_tien_nap = int(call.data.split("_")[1])
        
        # Tạo chuỗi hóa đơn ngẫu nhiên dài 10 ký tự số phía sau ID
        ma_hoa_don_ngau_nhien = "".join([str(random.randint(0, 9)) for _ in range(10)])
        noi_dung_ck = f"NAP{u_id}{ma_hoa_don_ngau_nhien}"
        
        # Link sinh mã VietQR chuẩn hình ảnh ZaloPay, tự động điền sẵn Số tiền + Nội dung dài
        link_qr = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-qr_only.jpg?accountName={TEN_CHU_TK}&amount={so_tien_nap}&addInfo={noi_dung_ck}"
        
        van_ban_nap = (
            f"📥 *THÔNG TIN KHỞI TẠO LỆNH NẠP TIỀN* 📥\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"🏦 Kênh nhận: *Ví Điện Tử ZALOPAY*\n"
            f"💳 Số tài khoản/SĐT: `{SO_TAI_KHOAN}`\n"
            f"👤 Chủ tài khoản: *{TEN_CHU_TK}*\n"
            f"💰 Số tiền nạp: *{so_tien_nap:,} VNĐ*\n"
            f"📝 Nội dung bắt buộc: `{noi_dung_ck}`\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"⚠️ *QUAN TRỌNG:* Bạn chỉ cần lưu mã QR ở trên về máy, mở ứng dụng ZaloPay lên quét là hệ thống tự điền Số tiền & Nội dung hóa đơn. Tiền vào tài khoản sau 30 giây!"
        )
        
        # Xóa tin nhắn chọn mệnh giá cũ đi cho sạch giao diện shop lớn
        bot.delete_message(call.message.chat.id, call.message.message_id)
        # Bắn ảnh QR xịn kèm text thông tin hóa đơn dài
        bot.send_photo(call.message.chat.id, photo=link_qr, caption=van_ban_nap, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "✅ Đã tạo hóa đơn nạp tiền!")

    # NẾU KHÁCH BẤM MUA ACC
    elif call.data.startswith("buy_"):
        so_du = data["users"].get(u_id, 0)
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
          
