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

# Kiểm tra và khởi tạo cơ sở dữ liệu file shop_data.json
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
            data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "accounts" not in data: data["accounts"] = []
            return data
    except:
        return {"users": {}, "accounts": []}

def ghi_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# HÀM FIX LỖI SỐ DƯ ALL: Đồng bộ và sửa lỗi hiển thị tiền cho toàn bộ hệ thống
def kiem_tra_va_dong_bo_user(data, u_id):
    u_id = str(u_id)
    if u_id not in data["users"] or not isinstance(data["users"][u_id], dict):
        if u_id == str(ADMIN_ID):
            # Khởi tạo mặc định cho Admin tối thượng
            data["users"][u_id] = {"balance": 999999999, "total_nap": 999999999, "total_tieu": 0, "don_mua": 0}
        else:
            # Khởi tạo mặc định cho Khách hàng thông thường
            data["users"][u_id] = {"balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0}
    else:
        # THUẬT TOÁN TỰ ĐỘNG CẬP NHẬT SỐ DƯ THẬT CHO ADMIN TỪ BẢN CŨ SANG BẢN MỚI
        if u_id == str(ADMIN_ID) and data["users"][u_id].get("balance", 0) < 500000000:
            old_tieu = data["users"][u_id].get("total_tieu", 0)
            old_balance = data["users"][u_id].get("balance", 0) # Lấy số tiền admin đã tự cộng tay trước đó
            # Thiết lập lại số dư gốc chuẩn xác
            data["users"][u_id]["balance"] = 999999999 - old_tieu + old_balance
            data["users"][u_id]["total_nap"] = 999999999 + data["users"][u_id].get("total_nap", 0)
    return data

# ================= MENU BÀN PHÍM CHÍNH (REPLY KEYBOARD) =================
def tao_ban_phim_chinh():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ Mua Key/Acc"),
        types.KeyboardButton("💳 Nạp Tiền Shop"),
        types.KeyboardButton("👤 Tài Khoản Của Tôi"),
        types.KeyboardButton("🛠️ Admin Panel")
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
            chuoi_sau_nap = noi_dung.replace("NAP", "").strip()
            khach_id = chuoi_sau_nap[:-6] # Cắt bỏ 6 ký tự mã bill cuối cùng
            
            if khach_id.isdigit():
                data = doc_data()
                khach_id = str(khach_id)
                data = kiem_tra_va_dong_bo_user(data, khach_id)
                
                # Cập nhật ví tiền thật thông qua cổng Bank tự động
                data["users"][khach_id]["balance"] += so_tien
                data["users"][khach_id]["total_nap"] += so_tien
                ghi_data(data)
                
                try:
                    bot.send_message(khach_id, f"🎉 *HỆ THỐNG CỘNG TIỀN THÀNH CÔNG!*\n Tài khoản của bạn đã được cộng tự động *+{so_tien:,} VNĐ* qua Ngân hàng.", parse_mode="Markdown")
                except:
                    pass
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
            bot.reply_to(message, "❌ Sai định dạng! Phải dùng dấu gạch đứng `|`.\nVí dụ: `50000 | Nick Free Fire VIP | TK: abc | MK: 123`")
            return

        chuoi = message.text.split("|")
        gia = int(chuoi[0].strip())
        ten_sp = chuoi[1].strip()
        thong_tin = "|".join(chuoi[2:]).strip()
        
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
        bot.reply_to(message, f"✅ Đã thêm thành công vào kho *{ten_sp}* (Mã tài khoản #{new_id})\n💰 Giá: {gia:,} VNĐ", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ Lỗi định dạng! Vui lòng nhập đúng mẫu: `Giá | Tên kho sản phẩm | Thông tin nick`")

# Hàm xử lý Admin cộng tiền thủ công kèm Ghi chú
def xu_ly_admin_plus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        if "|" not in message.text:
            bot.reply_to(message, "❌ Sai định dạng! Vui lòng nhập đúng mẫu:\n`ID Khách | Số tiền | Ghi chú`\n\nVí dụ: `6074595642 | 100000 | Event tang qua`")
            return
            
        parts = message.text.split("|")
        khach_id = parts[0].strip()
        so_tien = int(parts[1].strip())
        ghi_chu = parts[2].strip() if len(parts) > 2 else "Được Admin cộng tay thủ công"
        
        if so_tien <= 0:
            bot.reply_to(message, "❌ Số tiền cộng phải lớn hơn 0!")
            return
            
        data = doc_data()
        khach_id = str(khach_id)
        data = kiem_tra_va_dong_bo_user(data, khach_id)
            
        data["users"][khach_id]["balance"] += so_tien
        data["users"][khach_id]["total_nap"] += so_tien
        ghi_data(data)
        
        bot.reply_to(message, f"✅ Đã cộng thành công *+{so_tien:,}đ* cho khách hàng ID `{khach_id}`.\n📝 Ghi chú: {ghi_chu}")
        try:
            bot.send_message(khach_id, f"🎉 *THÔNG BÁO BIẾN ĐỘNG SỐ DƯ!*\n Tài khoản của bạn đã được hệ thống cộng *+{so_tien:,} VNĐ* từ Admin.\n📝 *Nội dung:* {ghi_chu}", parse_mode="Markdown")
        except:
            pass
    except Exception as e:
        bot.reply_to(message, "❌ Đã xảy ra lỗi! Vui lòng kiểm tra lại ID khách hoặc định dạng nhập vào.")

# Hàm xử lý Admin trừ tiền thủ công kèm Ghi chú
def xu_ly_admin_minus_money(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        if "|" not in message.text:
            bot.reply_to(message, "❌ Sai định dạng! Vui lòng nhập đúng mẫu:\n`ID Khách | Số tiền | Ghi chú`\n\nVí dụ: `6074595642 | 50000 | Phat vi pham`")
            return
            
        parts = message.text.split("|")
        khach_id = parts[0].strip()
        so_tien = int(parts[1].strip())
        ghi_chu = parts[2].strip() if len(parts) > 2 else "Bị Admin trừ tiền thủ công"
        
        if so_tien <= 0:
            bot.reply_to(message, "❌ Số tiền trừ phải lớn hơn 0!")
            return
            
        data = doc_data()
        khach_id = str(khach_id)
        if khach_id not in data["users"]:
            bot.reply_to(message, "❌ Không tìm thấy thông tin khách hàng này trên hệ thống!")
            return
            
        data["users"][khach_id]["balance"] -= so_tien
        if data["users"][khach_id]["balance"] < 0:
            data["users"][khach_id]["balance"] = 0
            
        ghi_data(data)
        
        bot.reply_to(message, f"✅ Đã trừ thành công *-{so_tien:,}đ* của khách hàng ID `{khach_id}`.\n📝 Ghi chú: {ghi_chu}")
        try:
            bot.send_message(khach_id, f"💸 *THÔNG BÁO BIẾN ĐỘNG SỐ DƯ!*\n Tài khoản của bạn đã bị trừ *-{so_tien:,} VNĐ* theo lệnh điều chỉnh từ Admin.\n📝 *Nội dung:* {ghi_chu}", parse_mode="Markdown")
        except:
            pass
    except Exception as e:
        bot.reply_to(message, "❌ Đã xảy ra lỗi! Vui lòng kiểm tra kỹ lại dữ liệu.")

# Hàm xử lý gửi thông báo toàn Shop
def xu_ly_admin_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    noi_dung = message.text.strip()
    if not noi_dung:
        bot.reply_to(message, "❌ Nội dung thông báo không được bỏ trống!")
        return
        
    data = doc_data()
    danh_sach_user = data.get("users", {})
    
    status_msg = bot.reply_to(message, f"⏳ Đang tiến hành gửi thông báo tới toàn bộ {len(danh_sach_user)} thành viên...")
    thanh_cong = 0
    that_bai = 0
    
    for u_id in danh_sach_user:
        try:
            bot.send_message(u_id, f"📢 *THÔNG BÁO TỪ BAN QUẢN TRỊ SHOP*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n{noi_dung}\n\n━━━━━━━━━━━━━━━━━━━━━━━", parse_mode="Markdown")
            thanh_cong += 1
        except:
            that_bai += 1
            
    bot.edit_message_text(f"✅ *GỬI THÔNG BÁO HOÀN TẤT!*\n🚀 Gửi thành công: {thanh_cong}\n❌ Thất bại (Chặn Bot): {that_bai}", message.chat.id, status_msg.message_id, parse_mode="Markdown")

# ================= LỆNH KHỞI ĐỘNG /START =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    u_id = str(message.from_user.id)
    data = doc_data()
    data = kiem_tra_va_dong_bo_user(data, u_id)
    ghi_data(data)
        
    if message.from_user.username:
        ten_khach = f"@{message.from_user.username}"
    else:
        ten_khach = message.from_user.first_name if message.from_user.first_name else "Thành Viên"
    
    van_ban = (
        f"👑 *HỆ THỐNG SHOP KDANGX VIP* 👑\n"
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
    data = kiem_tra_va_dong_bo_user(data, u_id)
    ghi_data(data)
        
    user_info = data["users"][u_id]
    is_admin = (message.from_user.id == ADMIN_ID)
    
    if message.from_user.username:
        ten_khach_hang = f"@{message.from_user.username}"
    else:
        ten_khach_hang = message.from_user.first_name if message.from_user.first_name else "Thành Viên"

    if message.text == "👤 Tài Khoản Của Tôi" or message.text == "👤 Tài Khoản":
        # FIX LỖI SỐ DƯ ALL: Cả Admin và khách đều lấy số dư thực tế trong file lưu trữ
        so_du_hien_thi = f"{user_info.get('balance', 0):,}"
        hang_hien_thi = "ADMIN TỐI THƯỢNG" if is_admin else "USER"

        van_ban = (
            f"👤 *TÀI KHOẢN CỦA BẠN*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 *ID:* `{u_id}`\n"
            f"👤 *Tên:* {ten_khach_hang}\n"
            f"⭐ *Hạng:* {hang_hien_thi}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Số dư:* {so_du_hien_thi}đ\n"
            f"💸 *Đã tiêu:* {user_info.get('total_tieu', 0):,}đ\n"
            f"💳 *Tổng nạp:* {user_info.get('total_nap', 0):,}đ\n"
            f"🛒 *Đơn mua:* {user_info.get('don_mua', 0)}\n\n"
            f"🆘 *Hỗ trợ:* @kdangx"
        )
        bot.send_message(message.chat.id, van_ban, parse_mode="Markdown")

    elif message.text == "💳 Nạp Tiền Shop" or message.text == "💳 Nạp Tiền":
        msg = bot.send_message(message.chat.id, "💰 *Hãy nhập số tiền bạn muốn nạp.*\nVí dụ: `20000`, `50000`, `100000`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, xu_ly_nhap_tien_nap)

    elif message.text == "🛍️ Mua Key/Acc":
        markup = types.InlineKeyboardMarkup(row_width=1)
        kho_hang = {}
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                ten = acc["name"]
                kho_hang[ten] = kho_hang.get(ten, 0) + 1
        
        if kho_hang:
            for ten_kho, so_luong in kho_hang.items():
                markup.add(types.InlineKeyboardButton(f"📁 {ten_kho} • [Số lượng: {so_luong}]", callback_data=f"open_kho_{ten_kho}"))
                
            van_ban_kho = (
                f"🛍️ *DANH MỤC KHO HÀNG SHOP KDANGX*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✨ Vui lòng chọn loại sản phẩm bạn muốn mua bên dưới:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.send_message(message.chat.id, van_ban_kho, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Hiện tại kho hàng đã hết sạch sản phẩm!*")

    elif message.text == "🛠️ Admin Panel":
        if not is_admin: return
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ THÊM ACC", callback_data="admin_add_acc"),
            types.InlineKeyboardButton("➖ XOÁ ACC", callback_data="admin_del_acc"),
            types.InlineKeyboardButton("💵 CỘNG TIỀN KHÁCH", callback_data="admin_plus_money"),
            types.InlineKeyboardButton("💸 TRỪ TIỀN KHÁCH", callback_data="admin_minus_money")
        )
        # Hàng nút riêng cho tính năng Thông báo toàn hệ thống shop lớn
        markup.add(types.InlineKeyboardButton("📢 THÔNG BÁO TOÀN SHOP", callback_data="admin_broadcast"))
        bot.send_message(message.chat.id, "🛠 *BẢNG ĐIỀU KHIỂN ADMIN QUẢN LÝ SHOP TỐI THƯỢNG*", reply_markup=markup, parse_mode="Markdown")

def xu_ly_nhap_tien_nap(message):
    if message.text in ["🛍️ Mua Key/Acc", "💳 Nạp Tiền Shop", "👤 Tài Khoản Của Tôi", "🛠️ Admin Panel"]:
        xu_ly_giao_dien(message)
        return
        
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
    is_admin = (call.from_user.id == ADMIN_ID)

    if call.data.startswith("open_kho_"):
        ten_kho = call.data.replace("open_kho_", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_acc = False
        for acc in data["accounts"]:
            if acc["name"] == ten_kho and acc["status"] == "ConHang":
                co_acc = True
                markup.add(types.InlineKeyboardButton(f"🎟️ Mã sản phẩm #{acc['id']} — Giá: {acc['price']:,}đ", callback_data=f"view_sp_{acc['id']}"))
                
        markup.add(types.InlineKeyboardButton("⬅️ Quay lại danh mục chính", callback_data="back_to_list"))
        if co_acc:
            bot.edit_message_text(f"📦 *DANH SÁCH SẢN PHẨM TRONG KHO:* `{ten_kho}`\n━━━━━━━━━━━━━━━━━━━━━━━\n👉 Chọn một mã sản phẩm cụ thể để tiến hành xem thông tin và mua:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Kho hàng này vừa hết sạch sản phẩm!", show_alert=True)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("view_sp_"):
        acc_id = int(call.data.split("_")[2])
        target_acc = next((acc for acc in data["accounts"] if acc["id"] == acc_id), None)
        
        if target_acc:
            van_ban_ct = (
                f"📦 *CHI TIẾT SẢN PHẨM*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 *Mã Số:* #{target_acc['id']}\n"
                f"🏷️ *Loại kho:* {target_acc['name']}\n"
                f"⭐ *Hạng giá:* USER\n"
                f"💰 *Giá bán:* {target_acc['price']:,}đ\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ Bấm nút mua bên dưới, hệ thống trừ tiền và trả tài khoản mật khẩu ngay lập tức."
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
        kho_hang = {}
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                ten = acc["name"]
                kho_hang[ten] = kho_hang.get(ten, 0) + 1
        if kho_hang:
            for ten_kho, so_luong in kho_hang.items():
                markup.add(types.InlineKeyboardButton(f"📁 {ten_kho} • [Số lượng: {so_luong}]", callback_data=f"open_kho_{ten_kho}"))
            van_ban_kho = (
                f"🛍️ *DANH MỤC KHO HÀNG SHOP KDANGX*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"✨ Vui lòng chọn loại sản phẩm bạn muốn mua bên dưới:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━"
            )
            bot.edit_message_text(van_ban_kho, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    elif call.data.startswith("confirm_buy_"):
        acc_id = int(call.data.split("_")[2])
        target_acc = next((acc for acc in data["accounts"] if acc["id"] == acc_id and acc["status"] == "ConHang"), None)
        
        if not target_acc:
            bot.answer_callback_query(call.id, "❌ Sản phẩm này đã bị người khác mua mất!", show_alert=True)
            return

        data = kiem_tra_va_dong_bo_user(data, u_id)
        user_info = data["users"][u_id]
        vi_tien_hien_tai = user_info.get("balance", 0)
        
        if vi_tien_hien_tai < target_acc["price"]:
            bot.answer_callback_query(call.id, "❌ Số dư của bạn không đủ! Vui lòng nạp thêm tiền.", show_alert=True)
        else:
            # Cơ chế trừ tiền chuẩn áp dụng đồng loạt (Fix lỗi số dư all)
            data["users"][u_id]["balance"] -= target_acc["price"]
            data["users"][u_id]["total_tieu"] += target_acc["price"]
            data["users"][u_id]["don_mua"] += 1
            
            target_acc["status"] = "DaBan"
            ghi_data(data)
            
            van_ban_tc = (
                f"🎉 *XÁC NHẬN MUA THÀNH CÔNG*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📦 *Loại kho:* {target_acc['name']}\n"
                f"🆔 *Mã Số:* #{target_acc['id']}\n"
                f"💰 *Chi phí trừ:* -{target_acc['price']:,} VNĐ\n\n"
                f"🔑 *THÔNG TIN TÀI KHOẢN ĐĂNG NHẬP:*\n"
                f"`{target_acc['info']}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Lưu ý:* Vui lòng bảo mật thông tin đơn hàng tránh tranh chấp."
            )
            bot.edit_message_text(van_ban_tc, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            bot.answer_callback_query(call.id, "✅ Giao dịch thành công!")

    # --- ĐIỀU HƯỚNG SỰ KIỆN QUẢN TRỊ ADMIN ---
    elif call.data == "admin_add_acc":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📝 Nhập theo mẫu:\n`Giá | Tên kho hàng trùng nhau | Thông tin nick`\n\nVí dụ: `25000 | ACC FF CỰC NGON | TK: dangvip1 | MK: 12345`")
        bot.register_next_step_handler(msg, xử_lý_thêm_acc)
        bot.answer_callback_query(call.id)

    elif call.data == "admin_del_acc":
        if not is_admin: return
        markup = types.InlineKeyboardMarkup(row_width=1)
        co_acc = False
        for acc in data["accounts"]:
            if acc["status"] == "ConHang":
                co_acc = True
                markup.add(types.InlineKeyboardButton(f"❌ Xoá #{acc['id']} - [{acc['name']}]", callback_data=f"adm_delete_{acc['id']}"))
        if co_acc:
            bot.send_message(call.message.chat.id, "🛠 Chọn sản phẩm muốn xoá hẳn khỏi cơ sở dữ liệu:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "📭 Kho hàng trống.")
        bot.answer_callback_query(call.id)

    elif call.data.startswith("adm_delete_"):
        if not is_admin: return
        acc_id = int(call.data.split("_")[2])
        data["accounts"] = [a for a in data["accounts"] if a["id"] != acc_id]
        ghi_data(data)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, f"🗑 Đã xóa hoàn toàn sản phẩm mã #{acc_id}.")
        bot.answer_callback_query(call.id)

    elif call.data == "admin_plus_money":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "💵 *CỘNG TIỀN CHO KHÁCH HÀNG*\nNhập đúng định dạng kèm ghi chú:\n`ID Khách | Số tiền cộng | Ghi chú lý do`\n\nVí dụ: `6074595642 | 100000 | Hoàn tiền lỗi key`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, xu_ly_admin_plus_money)
        bot.answer_callback_query(call.id)

    elif call.data == "admin_minus_money":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "💸 *TRỪ TIỀN CỦA KHÁCH HÀNG*\nNhập đúng định dạng kèm ghi chú:\n`ID Khách | Số tiền trừ | Ghi chú lý do`\n\nVí dụ: `6074595642 | 50000 | Phạt vi phạm quy định`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, xu_ly_admin_minus_money)
        bot.answer_callback_query(call.id)

    elif call.data == "admin_broadcast":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📢 *GỬI THÔNG BÁO TOÀN HỆ THỐNG*\nNhập nội dung thông báo muốn phát sóng đến toàn bộ thành viên của Shop:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, xu_ly_admin_broadcast)
        bot.answer_callback_query(call.id)

def run_api():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    try: bot.remove_webhook()
    except: pass
    t = Thread(target=run_api)
    t.start()
    bot.infinity_polling(skip_pending=True)
