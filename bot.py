import telebot
from telebot import types
import json
import os

# 1. CẤU HÌNH TOKEN BOT VÀ ID ADMIN CỦA BẠN
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642

bot = telebot.TeleBot(TOKEN)

# File lưu trữ dữ liệu shop (Số dư khách hàng và Kho Acc)
DATA_FILE = "shop_data.json"

# Khởi tạo dữ liệu nếu file chưa tồn tại
if not os.path.exists(DATA_FILE):
    initial_data = {
        "users": {}, # Lưu số dư: {"user_id": số_tiền}
        "accounts": [
            {"id": 1, "gane": "Free Fire", "price": 20000, "info": "TK: dangnguyen123 | MK: dang123456", "status": "ConHang"},
            {"id": 2, "gane": "Free Fire", "price": 50000, "info": "TK: top1ff@gmail.com | MK: freefire2026", "status": "ConHang"}
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

# MÀN HÌNH CHÍNH /START
@bot.message_handler(commands=['start', 'shop_menu'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    
    # Nếu khách mới, tạo số dư = 0đ
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
        
    so_du = data["users"][u_id]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_buy = types.InlineKeyboardButton("🛒 MUA ACC FREE FIRE", callback_data="list_acc")
    btn_nap = types.InlineKeyboardButton("💳 NẠP TIỀN ZALOPAY", callback_data="nap_tien")
    markup.add(btn_buy, btn_nap)
    
    bot.send_message(
        message.chat.id,
        f"🔥 **WELCOME TO KHANH SHOP FREE FIRE** 🔥\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 Tên tài khoản: **{message.from_user.first_name}**\n"
        f"🆔 ID cá nhân: `{u_id}`\n"
        f"💰 Số dư hiện tại: **{so_du:,} VNĐ**\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📌 Vui lòng chọn tính năng bên dưới:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# SỰ KIỆN NÚT BẤM
@bot.callback_query_handler(func=lambda call: True)
def callback_xu_ly(call):
    u_id = str(call.from_user.id)
    data = doc_data()
    
    # 1. TRANG NẠP TIỀN
    if call.data == "nap_tien":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 QUAY LẠI MENU", callback_data="shop_menu"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"💳 **HƯỚNG DẪN NẠP TIỀN TỰ ĐỘNG**\n\n"
                 f"▶ Ví ZaloPay: **0325683433**\n"
                 f"▶ Chủ TK: **NGUYEN KHOA DANG**\n"
                 f"📝 Nội dung chuyển khoản bắt buộc: `NAP {u_id}`\n\n"
                 f"⚠️ *Lưu ý:* Hệ thống auto check sau 30 giây. Bạn nhớ ghi đúng nội dung `NAP {u_id}` để được tự động cộng tiền nhé!",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    # 2. DANH SÁCH ACC TRONG KHO
    elif call.data == "list_acc":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                markup.add(types.InlineKeyboardButton(f"🎟 ACC #{acc['id']} - Giá: {acc['price']:,}đ", callback_data=f"buy_{acc['id']}"))
        markup.add(types.InlineKeyboardButton("🔙 QUAY LẠI MENU", callback_data="shop_menu"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🛒 **DANH SÁCH ACC FREE FIRE ĐANG CÓ TRONG KHO**\n\nChọn mã acc bạn muốn mua tự động:",
            reply_markup=markup
        )
        
    # 3. XỬ LÝ MUA ACC TỰ ĐỘNG
    elif call.data.startswith("buy_"):
        acc_id = int(call.data.split("_")[1])
        so_du_hien_tai = data["users"][u_id]
        
        # Tìm acc trong json
        target_acc = None
        for acc in data["accounts"]:
            if acc["id"] == acc_id and acc["status"] == "ConHang":
                target_acc = acc
                break
                
        if not target_acc:
            bot.answer_callback_query(call.id, "❌ Acc này vừa mới có người mua mất rồi hoặc không tồn tại!")
            return
            
        if so_du_hien_tai < target_acc["price"]:
            bot.answer_callback_query(call.id, f"❌ Bạn không đủ tiền! Cần thêm {target_acc['price'] - so_du_hien_tai:,}đ nữa.", show_alert=True)
        else:
            # TIẾN HÀNH TRỪ TIỀN VÀ GIAO ACC TỰ ĐỘNG
            data["users"][u_id] -= target_acc["price"]
            target_acc["status"] = "DaBan"
            ghi_data(data)
            
            # Gửi thông tin nick cho khách mua
            bot.send_message(
                call.message.chat.id,
                f"🎉 **MUA ACC THÀNH CÔNG!**\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"🎟 Mã sản phẩm: `# {target_acc['id']}`\n"
                f"💰 Giá tiền: -{target_acc['price']:,}đ\n"
                f"🔑 **THÔNG TIN TÀI KHOẢN:**\n"
                f"`{target_acc['info']}`\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"📌 *Vui lòng copy thông tin và đổi mật khẩu ngay nhé!*",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "✅ Mua acc thành công!")

# LỆNH CỦA ADMIN ĐỂ CỘNG TIỀN TỰ ĐỘNG QUA CHỮ HOẶC KHI API CALL VỀ
@bot.message_handler(commands=['cong_tien'])
def cong_tien_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        # Cú pháp lệnh admin gõ: /cong_tien ID TIEN (Ví dụ: /cong_tien 6074595642 50000)
        parts = message.text.split()
        khach_id = parts[1]
        money = int(parts[2])
        
        data = doc_data()
        if khach_id in data["users"]:
            data["users"][khach_id] += money
            ghi_data(data)
            bot.send_message(message.chat.id, f"✅ Đã cộng {money:,}đ cho ID {khach_id}")
            # Nhắn tin báo cho khách biết luôn
            bot.send_message(khach_id, f"🎉 Tài khoản của bạn đã được cộng **{money:,} VNĐ** từ hệ thống nạp tự động!", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Không tìm thấy người dùng này trong dữ liệu.")
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Cú pháp sai. Vui lòng gõ: /cong_tien [ID] [SO_TIEN]")

bot.infinity_polling()
