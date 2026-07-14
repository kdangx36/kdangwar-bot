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
        "accounts": []
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=4)

def doc_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "accounts": []}

def ghi_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= MENU BÀN PHÍM CHÍNH (REPLY KEYBOARD) =================
def tao_ban_phim_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ Mua Key/Acc"),
        types.KeyboardButton("💳 Nạp Tiền"),
        types.KeyboardButton("👤 Tài Khoản"),
        types.KeyboardButton("🛠️ Admin Panel")  # Nút này chỉ Admin bấm mới có tác dụng
    )
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
                if khach_id not in data["users"]:
                    data["users"][khach_id] = {"balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0}
                
                # Cập nhật số dư và tổng nạp
                data["users"][khach_id]["balance"] += so_tien
                data["users"][khach_id]["total_nap"] += so_tien
                ghi_data(data)
                
                bot.send_message(khach_id, f"🎉 *HỆ THỐNG CỘNG TIỀN THÀNH CÔNG!*\n Tài khoản của bạn đã được cộng tự động *+{so_tien:,} VNĐ*.", parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"💰 Admin ơi! Khách ID `{khach_id}` vừa nạp thành công *{so_tien:,}đ* qua ABBank.", parse_mode="Markdown")
                return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Lỗi API Webhook:", str(e))
    return jsonify({"status": "error"}), 400

# ================= LOGIC QUẢN LÝ CỦA ADMIN =================
def xử_lý_thêm_acc(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        if "|" not in message.text:
            bot.reply_to(message, "❌ Sai định dạng! Phải dùng dấu gạch đứng `|`.\nVí dụ: `50000 | Tên Sản Phẩm VIP | TK: abc | MK: 123`")
            return

        chuoi = message.text.split("|")
        gia = int(chuoi[0].strip())
        ten_sp = chuoi[1].strip()
        thong_tin = chuoi[2].strip()
        
        data = doc_data()
        cac_id_hien_tai = [acc["id"] for acc in data["accounts"]]
        new_id = max(cac_id_hien_tai) + 1 if cac_id_hien_tai else 1
        
        data["accounts"].append({
            "id": new_id,
            "name": ten_sp,
            "price": gia,
            "info": thong_tin,
            "status": "ConHang"
        })
        ghi_data(data)
        bot.reply_to(message, f"✅ Đã thêm thành công: *{ten_sp}* (Mã #{new_id})\n💰 Giá: {gia:,} VNĐ", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ Lỗi định dạng! Vui lòng nhập đúng mẫu: `Giá | Tên sản phẩm | Thông tin nick`")

# ================= LỆNH KHỞI ĐỘNG /START =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    if u_id not in data["users"] or isinstance(data["users"][u_id], int):
        data["users"][u_id] = {"balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0}
        ghi_data(data)
        
    ten_khach = message.from_user.first_name if message.from_user.first_name else "Thành Viên VIP"
    
    van_ban = (
        f"👑 *HỆ THỐNG SHOP ACC KDANGX VIP* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Chào mừng *{ten_khach}* đã đến với cửa hàng!\n"
        f"🔥 Nơi phân phối và giao dịch Nick Free Fire tự động, uy tín, bảo mật tuyệt đối 24/7.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 Vui lòng sử dụng các phím chức năng bên dưới:"
    )
    bot.send_message(message.chat.id, van_ban, reply_markup=tao_ban_phim_chinh(), parse_mode="Markdown")

# ================= XỬ LÝ SỰ KIỆN NÚT BẤM TEXT CHÍNH =================
@bot.message_handler(func=lambda message: True)
def xu_ly_giao_dien(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    
    if u_id not in data["users"] or isinstance(data["users"][u_id], int):
        data["users"][u_id] = {"balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0}
        ghi_data(data)
        
    user_info = data["users"][u_id]
    username = f"@{message.from_user.username}" if message.from_user.username else "Chưa thiết lập"

    if message.text == "👤 Tài Khoản":
        van_ban = (
            f"👤 *TÀI KHOẢN CỦA BẠN*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 *ID:* `{u_id}`\n"
            f"👥 *Tên:* {username}\n"
            f"⭐ *Hạng:* USER\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Số dư:* {user_info.get('balance', 0):,}đ\n"
            f"💸 *Đã tiêu:* {user_info.get('total_tieu', 0):,}đ\n"
            f"💳 *Tổng nạp:* {user_info.get('total_nap', 0):,}đ\n"
            f"🛒 *Đơn mua:* {user_info.get('don_mua', 0)}\n\n"
            f"🆘 *Hỗ trợ:* @kdangx"
        )
        bot.send_message(message.chat.id, van_ban, parse_mode="Markdown")

    elif message.text == "💳 Nạp Tiền":
        msg = bot.send_message(message.chat.id, "💰 *Hãy nhập số tiền bạn muốn nạp.*\nVí dụ: `20000`, `50000`, `100000`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, xu_ly_nhap_tien_nap)

    elif message.text == "🛍️ Mua Key/Acc":
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_hang = True
                markup.add(types.InlineKeyboardButton(f"📦 {acc['id']}. {acc['name']} • Kho còn 1", callback_data=f"view_sp_{acc['id']}"))
        
        if co_hang:
            van_ban_kho = (
                f"🛍️ *SHOP KEY/ACC AUTO*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✨ Chọn sản phẩm bên dưới để xem gói.\n"
                f"⚡ Mua xong bot trả tài khoản tự động.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(message.chat.id, van_ban_kho, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Hiện tại kho hàng đã hết sạch sản phẩm!*")

    elif message.text == "🛠️ Admin Panel":
        if message.from_user.id != ADMIN_ID: return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ THÊM ACC", callback_data="admin_add_acc"),
            types.InlineKeyboardButton("➖ XOÁ ACC", callback_data="admin_del_acc")
        )
        bot.send_message(message.chat.id, "🛠 *BẢNG ĐIỀU KHIỂN ADMIN QUẢN LÝ SHOP*", reply_markup=markup, parse_mode="Markdown")

# Xử lý bước nhập số tiền chuyển khoản
def xu_ly_nhap_tien_nap(message):
    try:
        so_tien_nap = int(message.text.strip())
        if so_tien_nap < 1000:
            bot.reply_to(message, "❌ Số tiền nạp tối thiểu là 1.000 VNĐ!")
            return
        
        u_id = str(message.from_user.id)
        ma_hoa_don_ngau_nhien = "".join([str(random.randint(0, 9)) for _ in range(6)])
        noi_dung_ck = f"NAP{u_id}{ma_hoa_don_ngau_nhien}"
        
        link_qr = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.jpg?accountName={TEN_CHU_TK}&amount={so_tien_nap}&addInfo={noi_dung_ck}"
        
        van_ban_nap = (
            f"⚡ *THÔNG TIN NẠP TIỀN*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏦 *Ngân hàng:* ABBank\n"
            f"💳 *STK:* `{SO_TAI_KHOAN}`\n"
            f"👤 *Chủ TK:* {TEN_CHU_TK}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Số tiền:* {so_tien_nap:,}đ\n"
            f"📝 *Nội dung:* `{noi_dung_ck}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Chuyển đúng số tiền + đúng nội dung.*\n"
            f"⏳ Hệ thống duyệt tự động sau 1-3 phút."
        )
        bot.send_photo(message.chat.id, photo=link_qr, caption=van_ban_nap, parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Vui lòng chỉ nhập ký tự số nguyên!")

# ================= XỬ LÝ CÁC CALLBACK SỰ KIỆN NÚT BẤM INLINE =================
@bot.callback_query_handler(func=lambda call: True)
def callback_xu_ly(call):
    u_id = str(call.from_user.id)
    data = doc_data()

    if call.data.startswith("view_sp_"):
        acc_id = int(call.data.split("_")[2])
        target_acc = next((acc for acc in data["accounts"] if acc["id"] == acc_id), None)
        
        if target_acc:
            van_ban_ct = (
                f"📦 *CHI TIẾT SẢN PHẨM*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 *STT:* {target_acc['id']}\n"
                f"🏷️ *Tên:* {target_acc['name']}\n"
                f"👤 *Hạng giá:* USER\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👇 *Chọn gói muốn mua:*\n\n"
                f"⏱️ *Gói Gốc*\n"
                f"💰 *Giá:* {target_acc['price']:,}đ\n"
                f"🔑 *Kho:* ✅ Còn 1"
            )
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(f"🛒 Mua Ngay • {target_acc['price']:,}đ", callback_data=f"confirm_buy_{target_acc['id']}"),
                types.InlineKeyboardButton("⬅️ Quay lại danh mục", callback_data="back_to_list")
            )
            bot.edit_message_text(van_ban_ct, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data == "back_to_list":
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_hang = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_hang = True
                markup.add(types.InlineKeyboardButton(f"📦 {acc['id']}. {acc['name']} • Kho còn 1", callback_data=f"view_sp_{acc['id']}"))
        if co_hang:
            van_ban_kho = (
                f"🛍️ *SHOP KEY/ACC AUTO*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✨ Chọn sản phẩm bên dưới để xem gói.\n"
                f"⚡ Mua xong bot trả tài khoản tự động.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.edit_message_text(van_ban_kho, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data.startswith("confirm_buy_"):
        acc_id = int(call.data.split("_")[2])
        target_acc = next((acc for acc in data["accounts"] if acc["id"] == acc_id and acc["status"] == "ConHang"), None)
        user_info = data["users"].get(u_id, {"balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0})
        
        if not target_acc:
            bot.answer_callback_query(call.id, "❌ Sản phẩm này đã bị người khác mua mất!", show_alert=True)
            return
            
        if user_info["balance"] < target_acc["price"]:
            bot.answer_callback_query(call.id, "❌ Số dư của bạn không đủ! Vui lòng nạp tiền.", show_alert=True)
        else:
            # Khấu trừ tài khoản thương mại
            data["users"][u_id]["balance"] -= target_acc["price"]
            data["users"][u_id]["total_tieu"] += target_acc["price"]
            data["users"][u_id]["don_mua"] += 1
            
            target_acc["status"] = "DaBan"
            ghi_data(data)
            
            van_ban_tc = (
                f"🎉 *XÁC NHẬN MUA THÀNH CÔNG*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 *Sản phẩm:* {target_acc['name']}\n"
                f"💰 *Chi phí trừ:* -{target_acc['price']:,} VNĐ\n"
                f"🔑 *THÔNG TIN TÀI KHOẢN ĐĂNG NHẬP:*\n\n"
                f"`{target_acc['info']}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Lưu ý:* Vui lòng bảo mật thông tin đơn hàng tránh tranh chấp."
            )
            bot.edit_message_text(van_ban_tc, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "✅ Giao dịch thành công!")

    # --- ĐIỀU HƯỚNG SỰ KIỆN QUẢN TRỊ ADMIN ---
    elif call.data == "admin_add_acc":
        if call.from_user.id != ADMIN_ID: return
        msg = bot.send_message(call.message.chat.id, "📝 Nhập theo mẫu:\n`Giá | Tên sản phẩm hiển thị | Thông tin đăng nhập`\n\nVí dụ: `30000 | ACC FF GIÁ RẺ #1 | TK: dang1 | MK: 123`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, xử_lý_thêm_acc)
        bot.answer_callback_query(call.id)

    elif call.data == "admin_del_acc":
        if call.from_user.id != ADMIN_ID: return
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_acc = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_acc = True
                markup.add(types.InlineKeyboardButton(f"❌ Xoá mã #{acc['id']} - {acc['name']}", callback_data=f"adm_delete_{acc['id']}"))
        if co_acc:
            bot.send_message(call.message.chat.id, "🛠 Chọn sản phẩm muốn xoá:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "📭 Kho hàng trống.")
        bot.answer_callback_query(call.id)

    elif call.data.startswith("adm_delete_"):
        if call.from_user.id != ADMIN_ID: return
        acc_id = int(call.data.split("_")[2])
        data["accounts"] = [a for a in data["accounts"] if a["id"] != acc_id]
        ghi_data(data)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, f"🗑 Đã xóa hoàn toàn sản phẩm mã #{acc_id}.")
        bot.answer_callback_query(call.id)

def run_api():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    try: bot.remove_webhook()
    except: pass
    t = Thread(target=run_api)
    t.start()
    bot.infinity_polling(skip_pending=True)
