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
MA_NGAN_HANG = "970425"        # Mã BIN chuẩn của ABBank (Ngân hàng An Bình)
SO_TAI_KHOAN = "0325683433"    # Số tài khoản ABBank của bạn
TEN_CHU_TK = "NGUYEN KHOA DANG" 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "shop_data.json"

# Kiểm tra dữ liệu bộ nhớ shop
if not os.path.exists(DATA_FILE):
    initial_data = {
        "users": {},
        "accounts": [
            {"id": 1, "price": 0, "info": "TK: dangnguyen123 | MK: dang123456", "status": "ConHang"},
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

# MENU CHÍNH DƯỚI THANH TIN NHẮN
def tao_ban_phim_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_buy = types.KeyboardButton("🛒 MUA ACC CLONE")
    btn_nap = types.KeyboardButton("💳 NẠP TIỀN SHOP")
    btn_user = types.KeyboardButton("👤 TÀI KHOẢN CỦA TÔI")
    markup.add(btn_buy, btn_nap, btn_user)
    return markup

# ================= CỔNG WEBHOOK AUTO CHECK TIỀN CỦA ABBANK =================
@app.route('/', methods=['GET'])
def home():
    return "Server Bot ABBank VIP đang chạy cực mượt!", 200

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
                if khach_id in data["users"]:
                    data["users"][khach_id] += so_tien
                else:
                    data["users"][khach_id] = so_tien
                ghi_data(data)
                
                bot.send_message(khach_id, f"🎉 *HỆ THỐNG CỘNG TIỀN THÀNH CÔNG!*\n Tài khoản của bạn đã được cộng tự động *+{so_tien:,} VNĐ*.", parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"💰 Admin ơi! Khách ID `{khach_id}` vừa nạp thành công *{so_tien:,}đ* qua ABBank.", parse_mode="Markdown")
                return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Lỗi API Webhook:", str(e))
    return jsonify({"status": "error"}), 400
# ====================================================================

# LỆNH /START KHỞI ĐỘNG BOT VỚI GIAO DIỆN VIP
@bot.message_handler(commands=['start'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
        
    # FIX LỖI TÊN KHÁCH HÀNG: Lấy trực tiếp từ hệ thống tin nhắn
    ten_khach = message.from_user.first_name if message.from_user.first_name else (f"@{message.from_user.username}" if message.from_user.username else "Thành Viên VIP")
    
    van_ban = (
        f"👑 *HỆ THỐNG SHOP ACC KDANGX VIP* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Chào mừng *{ten_khach}* đã đến với cửa hàng!\n"
        f"🔥 Nơi phân phối và giao dịch Nick Free Fire tự động, uy tín, bảo mật tuyệt đối 24/7.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 Vui lòng chọn các tính năng ở thanh menu bên dưới để bắt đầu giao dịch:"
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
    
    # FIX LỖI TÊN KHÁCH HÀNG: Đảm bảo luôn luôn hiện tên chuẩn
    ten_khach = message.from_user.first_name if message.from_user.first_name else (f"@{message.from_user.username}" if message.from_user.username else "Thành Viên VIP")

    if message.text == "👤 TÀI KHOẢN CỦA TÔI":
        van_ban = (
            f"👤 *THÔNG TIN TÀI KHOẢN KHÁCH HÀNG*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 Tên khách hàng: *{ten_khach}*\n"
            f"🆔 ID cá nhân: `{u_id}`\n"
            f"💰 Số dư khả dụng: *{so_du:,} VNĐ*\n"
            f"✨ Cấp bậc: *Thành Viên Đồng*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(message.chat.id, van_ban, parse_mode="Markdown")

    elif message.text == "💳 NẠP TIỀN SHOP":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("💵 10.000 VNĐ", callback_data="amount_10000")
        btn2 = types.InlineKeyboardButton("💵 20.000 VNĐ", callback_data="amount_20000")
        btn3 = types.InlineKeyboardButton("💵 50.000 VNĐ", callback_data="amount_50000")
        btn4 = types.InlineKeyboardButton("💵 100.000 VNĐ", callback_data="amount_100000")
        btn5 = types.InlineKeyboardButton("💵 200.000 VNĐ", callback_data="amount_200000")
        btn6 = types.InlineKeyboardButton("💵 500.000 VNĐ", callback_data="amount_500000")
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        
        bot.send_message(
            message.chat.id, 
            "💳 *VUI LÒNG CHỌN HẠN MỨC SỐ TIỀN MUỐN NẠP VÀO SHOP:*", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )

    elif message.text == "🛒 MUA ACC CLONE":
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_hang = True
                markup.add(types.InlineKeyboardButton(f"🎟️ ACC FREEFIRE #{acc['id']} — 💰 Giá: {acc['price']:,}đ", callback_data=f"buy_{acc['id']}"))
        
        if co_hang:
            van_ban_kho = "🛒 *DANH SÁCH SẢN PHẨM ACC ĐANG SẴN CÓ TRONG KHO:* \n\n" \
                          "👉 Hãy chọn tài khoản bạn ưng ý ở menu danh sách bên dưới:"
        else:
            van_ban_kho = "❌ *Hiện tại kho hàng đã hết sạch sản phẩm, vui lòng quay lại sau!*"
            
        bot.send_message(message.chat.id, van_ban_kho, reply_markup=markup, parse_mode="Markdown")

# XỬ LÝ SỰ KIỆN CALLBACK DATA
@bot.callback_query_handler(func=lambda call: True)
def callback_xu_ly(call):
    u_id = str(call.from_user.id)
    data = doc_data()

    if call.data.startswith("amount_"):
        so_tien_nap = int(call.data.split("_")[1])
        ma_hoa_don_ngau_nhien = "".join([str(random.randint(0, 9)) for _ in range(10)])
        noi_dung_ck = f"NAP{u_id}{ma_hoa_don_ngau_nhien}"
        
        # FIX MÃ QR: Đổi template sang "print" để xóa sạch logo lỏ ở giữa, chỉ giữ lại mã QR ABBank nguyên bản quét siêu mượt
        link_qr = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.jpg?accountName={TEN_CHU_TK}&amount={so_tien_nap}&addInfo={noi_dung_ck}"
        
        van_ban_nap = (
            f"📥 *THÔNG TIN HÓA ĐƠN NẠP TIỀN TỰ ĐỘNG* 📥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Ngân hàng đối tác: *ABBank (Ngân Hàng An Bình)*\n"
            f"💳 Số tài khoản nhận: `{SO_TAI_KHOAN}`\n"
            f"👤 Chủ tài khoản: *{TEN_CHU_TK}*\n"
            f"💰 Số tiền cần chuyển: *{so_tien_nap:,} VNĐ*\n"
            f"📝 Nội dung chuyển khoản: `{noi_dung_ck}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ *HƯỚNG DẪN QUÉT QR NHANH CHÓNG:*\n"
            f"1️⃣ Tải ảnh QR code hệ thống vừa gửi ở trên về điện thoại.\n"
            f"2️⃣ Mở ứng dụng Ngân hàng (hoặc Ví điện tử) của bạn chọn tính năng Quét QR.\n"
            f"3️⃣ Hệ thống tự nhận diện ABBank, điền sẵn Số tiền và Nội dung hóa đơn dài xịn!"
        )
        
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
            
        bot.send_photo(call.message.chat.id, photo=link_qr, caption=van_ban_nap, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "✅ Đã tạo hóa đơn chuyển khoản VIP thành công!")

    elif call.data.startswith("buy_"):
        so_du = data["users"].get(u_id, 0)
        acc_id = int(call.data.split("_")[1])
        target_acc = None
        for acc in data["accounts"]:
            if acc["id"] == acc_id and acc["status"] == "ConHang":
                target_acc = acc
                break
        if not target_acc:
            bot.answer_callback_query(call.id, "❌ Acc này vừa mới có khách hàng khác mua mất rồi!")
            return
        if so_du < target_acc["price"]:
            bot.answer_callback_query(call.id, f"❌ Số dư của bạn không đủ! Hãy nhấn 'NẠP TIỀN SHOP' để bổ sung.", show_alert=True)
        else:
            data["users"][u_id] -= target_acc["price"]
            target_acc["status"] = "DaBan"
            ghi_data(data)
            
            bot.send_message(
                call.message.chat.id,
                f"🎉 *GIAO DỊCH THÀNH CÔNG — CẢM ƠN BẠN ĐÃ ỦNG HỘ!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎟️ Mã sản phẩm: `# {target_acc['id']}`\n"
                f"💰 Chi phí trừ: -{target_acc['price']:,} VNĐ\n"
                f"🔑 *THÔNG TIN TÀI KHOẢN ĐĂNG NHẬP:*\n"
                f"`{target_acc['info']}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ Lưu ý: Bạn nên đăng nhập ngay và tiến hành thay đổi mật khẩu thông tin bảo mật để tránh tranh chấp.",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "✅ Chúc mừng bạn đã mua tài khoản thành công!")

def run_api():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    t = Thread(target=run_api)
    t.start()
    bot.infinity_polling()
