import telebot
from telebot import types
import json
import os

# 1. CẤU HÌNH TOKEN BOT VÀ ID ADMIN CỦA BẠN
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642

bot = telebot.TeleBot(TOKEN)

# File lưu trữ dữ liệu shop
DATA_FILE = "shop_data.json"

# Khởi tạo dữ liệu mẫu nếu chưa có file
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

# HÀM TẠO GIAO DIỆN MENU CHÍNH
def tao_menu_chinh(message, u_id, so_du):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_buy = types.InlineKeyboardButton("🛒 MUA ACC FREE FIRE", callback_data="list_acc")
    btn_nap = types.InlineKeyboardButton("💳 NẠP TIỀN ZALOPAY", callback_data="nap_tien")
    markup.add(btn_buy, btn_nap)
    
    van_ban = (
        f"🔥 *WELCOME TO KHANH SHOP FREE FIRE* 🔥\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 Tài khoản: *{message.from_user.first_name}*\n"
        f"🆔 ID cá nhân: `{u_id}`\n"
        f"💰 Số dư: *{so_du:,} VNĐ*\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"📌 Vui lòng chọn tính năng bên dưới:"
    )
    return van_ban, markup

# LỆNH /START HOẶC /SHOP_MENU
@bot.message_handler(commands=['start', 'shop_menu'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
        
    so_du = data["users"][u_id]
    van_ban, markup = tao_menu_chinh(message, u_id, so_du)
    
    bot.send_message(message.chat.id, van_ban, reply_markup=markup, parse_mode="Markdown")

# XỬ LÝ SỰ KIỆN NÚT BẤM CALLBACK
@bot.callback_query_handler(func=lambda call: True)
def callback_xu_ly(call):
    u_id = str(call.from_user.id)
    data = doc_data()
    
    if u_id not in data["users"]:
        data["users"][u_id] = 0
        ghi_data(data)
        
    so_du = data["users"][u_id]

    # NÚT QUAY LẠI MENU CHÍNH
    if call.data == "shop_menu":
        van_ban, markup = tao_menu_chinh(call, u_id, so_du)
        try:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=van_ban, reply_markup=markup, parse_mode="Markdown")
        except:
            pass
            
    # GIAO DIỆN NẠP TIỀN
    elif call.data == "nap_tien":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 QUAY LẠI MENU", callback_data="shop_menu"))
        
        van_ban_nap = (
            f"💳 *HƯỚNG DẪN NẠP TIỀN TỰ ĐỘNG*\n\n"
            f"▶ Ví ZaloPay: *0325683433*\n"
            f"▶ Chủ TK: *NGUYEN KHOA DANG*\n"
            f"📝 Nội dung CK bắt buộc: `NAP {u_id}`\n\n"
            f"⚠️ *Lưu ý:* Hệ thống auto check sau 30 giây. Bạn nhớ ghi đúng nội dung để được tự động cộng tiền nhé!"
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=van_ban_nap, reply_markup=markup, parse_mode="Markdown")
        
    # DANH SÁCH ACC
    elif call.data == "list_acc":
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_hang = True
                gia_acc = acc['price']
                markup.add(types.InlineKeyboardButton(f"🎟 ACC #{acc['id']} - Giá: {gia_acc:,}đ", callback_data=f"buy_{acc['id']}"))
                
        markup.add(types.InlineKeyboardButton("🔙 QUAY LẠI MENU", callback_data="shop_menu"))
        
        van_ban_kho = "🛒 *DANH SÁCH ACC FREE FIRE TRONG KHO*\n\nChọn mã sản phẩm bạn muốn mua tự động:" if co_hang else "❌ Hiện tại kho hàng đã hết sạch acc!"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=van_ban_kho, reply_markup=markup, parse_mode="Markdown")
        
    # MUA ACC TỰ ĐỘNG
    elif call.data.startswith("buy_"):
        acc_id = int(call.data.split("_")[1])
        
        target_acc = None
        for acc in data["accounts"]:
            if acc["id"] == acc_id and acc["status"] == "ConHang":
                target_acc = acc
                break
                
        if not target_acc:
            bot.answer_callback_query(call.id, "❌ Acc này vừa mới có người mua hoặc không tồn tại!")
            return
            
        if so_du < target_acc["price"]:
            bot.answer_callback_query(call.id, f"❌ Bạn không đủ tiền! Cần nạp thêm tiền vào ví.", show_alert=True)
        else:
            # Trừ tiền và đổi trạng thái
            data["users"][u_id] -= target_acc["price"]
            target_acc["status"] = "DaBan"
            ghi_data(data)
            
            # Nhả tài khoản mật khẩu thẳng ra màn hình chat công khai cho khách mua
            info_acc = target_acc["info"]
            id_mua = target_acc["id"]
            gia_mua = target_acc["price"]
            
            bot.send_message(
                call.message.chat.id,
                f"🎉 *MUA ACC THÀNH CÔNG!*\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"🎟 Mã sản phẩm: `# {id_mua}`\n"
                f"💰 Giá tiền: -{gia_mua:,}đ\n"
                f"🔑 *THÔNG TIN TÀI KHOẢN:*\n"
                f"`{info_acc}`\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"📌 *Vui lòng copy thông tin và đổi mật khẩu ngay nhé!*",
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, "✅ Đã mua thành công!")

# LỆNH ADMIN ĐỂ CỘNG TIỀN TỰ ĐỘNG
@bot.message_handler(commands=['cong_tien'])
def cong_tien_admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        khach_id = parts[1]
        money = int(parts[2])
        
        data = doc_data()
        if khach_id in data["users"]:
            data["users"][khach_id] += money
            ghi_data(data)
            bot.send_message(message.chat.id, f"✅ Đã cộng {money:,}đ cho ID {khach_id}")
            bot.send_message(khach_id, f"🎉 Tài khoản của bạn đã được cộng *{money:,} VNĐ* từ hệ thống!", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ Không tìm thấy người dùng này.")
    except:
        bot.send_message(message.chat.id, "⚠️ Cú pháp sai. Vui lòng gõ: `/cong_tien ID SO_TIEN`", parse_mode="Markdown")

bot.infinity_polling()
