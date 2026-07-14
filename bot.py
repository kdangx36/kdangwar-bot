import os
import json
import random
import logging
import re
from threading import Thread, Lock
from flask import Flask, request, jsonify
import telebot
from telebot import types

# Tối ưu Logging chuyên nghiệp
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# ================= CONFIG THÔNG TIN CHÍNH CHỦ =================
TOKEN = "8320265018:AAHPpy71v6eplijZjfWzLkvG0xql_WVeBRg"
ADMIN_ID = 6074595642

MA_NGAN_HANG = "970425"        
SO_TAI_KHOAN = "0325683433"    
TEN_CHU_TK = "NGUYEN KHOA DANG" 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DATA_FILE = "shop_data.json"
file_lock = Lock()

# ================= CORE DATA MANAGEMENT =================
def init_db():
    if not os.path.exists(DATA_FILE):
        # Bổ sung dict settings để lưu trạng thái Admin
        initial_data = {"users": {}, "accounts": [], "settings": {"admin_status": "🟢 Online 24/7"}}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)

def clean_money_value(val) -> int:
    if val is None: return 0
    if isinstance(val, (int, float)): return int(val)
    try:
        cleaned = re.sub(r'[^\d]', '', str(val))
        return int(cleaned) if cleaned else 0
    except Exception: return 0

def get_db_raw() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "accounts": [], "settings": {"admin_status": "🟢 Online 24/7"}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("users", {})
            data.setdefault("accounts", [])
            data.setdefault("settings", {"admin_status": "🟢 Online 24/7"}) # Khởi tạo nếu thiếu
            return data
    except Exception:
        return {"users": {}, "accounts": [], "settings": {"admin_status": "🟢 Online 24/7"}}

def save_db_raw(data: dict) -> bool:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logging.error(f"Lỗi lưu DB: {e}")
        return False

def sync_user_data(data: dict, user_id: str) -> dict:
    user_id = str(user_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0
        }
    else:
        # Auto-clean data tránh bug type
        for key in ["balance", "total_nap", "total_tieu"]:
            data["users"][user_id][key] = clean_money_value(data["users"][user_id].get(key, 0))
        data["users"][user_id]["don_mua"] = int(data["users"][user_id].get("don_mua", 0))
    return data

# ================= KEYBOARD UI BUILDERS =================
def build_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Cửa Hàng"),
        types.KeyboardButton("💳 Nạp Số Dư")
    )
    markup.add(
        types.KeyboardButton("👤 Hồ Sơ Cá Nhân"),
        types.KeyboardButton("☎️ Liên Hệ Hỗ Trợ")
    )
    return markup

# ================= WEBHOOK AUTOMATION (ABBANK) =================
@app.route('/', methods=['GET'])
def index():
    return "KDANGX VIP Shop Gateway - 🟢 Online", 200

@app.route('/webhook/abbank', methods=['POST'])
def abbank_callback():
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"status": "invalid_payload"}), 400
            
        description = req_data.get("description", "").upper() 
        amount = clean_money_value(req_data.get("amount", 0))
        
        if amount > 0:
            match = re.search(r"NAP(\d+)", description)
            if match:
                full_code = match.group(1) 
                if len(full_code) > 6:
                    client_id = str(full_code[:-6])
                    
                    if client_id.isdigit():
                        with file_lock: 
                            db = get_db_raw()
                            db = sync_user_data(db, client_id)
                            db["users"][client_id]["balance"] += amount
                            db["users"][client_id]["total_nap"] += amount
                            success = save_db_raw(db)
                            
                        if success:
                            try:
                                receipt = (
                                    f"✅ *NẠP TIỀN THÀNH CÔNG*\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"Tài khoản của bạn vừa được cộng: *+{amount:,} VNĐ*\n"
                                    f"Chúc bạn mua sắm vui vẻ tại hệ thống! ❤️"
                                )
                                bot.send_message(client_id, receipt, parse_mode="Markdown")
                            except Exception: pass
                                
                            try:
                                admin_notif = (
                                    f"💰 *KẾ TOÁN: CÓ BIẾN ĐỘNG QUỸ*\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"👤 ID Khách: `{client_id}`\n"
                                    f"💵 Số tiền nạp: *+{amount:,}đ*\n"
                                    f"🌐 Cổng: Gateway ABBank Tự Động"
                                )
                                bot.send_message(ADMIN_ID, admin_notif, parse_mode="Markdown")
                            except Exception: pass
                                
                            return jsonify({"status": "success"}), 200
    except Exception as e: 
        logging.error(f"Webhook Error: {e}")
    return jsonify({"status": "error"}), 400

# ================= ADMIN ACTIONS =================
def process_admin_add_product(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split("|")
        if len(parts) < 3: raise ValueError("Thiếu dữ liệu")
            
        price = clean_money_value(parts[0].strip())
        name = parts[1].strip()
        info = "|".join(parts[2:]).strip()
        
        with file_lock:
            db = get_db_raw()
            existing_ids = [acc["id"] for acc in db["accounts"]]
            next_id = max(existing_ids) + 1 if existing_ids else 1
            
            db["accounts"].append({
                "id": next_id, "name": name, "price": price, "info": info, "status": "ConHang"
            })
            save_db_raw(db)
            
        bot.reply_to(message, f"✅ *THÊM KHO THÀNH CÔNG*\n📦 SP: `{name}` | Mã: `#{next_id}` | 💰 Giá: `{price:,}đ`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ Sai định dạng! Hãy gửi chính xác theo mẫu:\n`Giá | Tên Gói | Tài khoản | Mật khẩu`\n\n*(Ví dụ: `50000 | Netflix 1 Tháng | user@gmail.com | pass123`)*", parse_mode="Markdown")

def process_admin_deposit(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split("|")
        target_id = str(parts[0].strip())
        amount = clean_money_value(parts[1].strip())
        
        if amount <= 0: raise ValueError("Số tiền phải lớn hơn 0")
            
        with file_lock:
            db = get_db_raw()
            db = sync_user_data(db, target_id)
            db["users"][target_id]["balance"] += amount
            db["users"][target_id]["total_nap"] += amount
            save_db_raw(db)
        
        bot.reply_to(message, f"✅ Đã CỘNG tay *+{amount:,}đ* cho ID `{target_id}`", parse_mode="Markdown")
        try:
            bot.send_message(target_id, f"🎁 *QUÀ TẶNG TỪ ADMIN*\nTài khoản của bạn vừa nhận được *+{amount:,} VNĐ*", parse_mode="Markdown")
        except: pass
    except Exception:
        bot.reply_to(message, "❌ Mẫu chuẩn: `ID Khách | Số tiền`\n*(Ví dụ: `123456789 | 50000`)*", parse_mode="Markdown")

def process_admin_deduct(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split("|")
        target_id = str(parts[0].strip())
        amount = clean_money_value(parts[1].strip())
        
        if amount <= 0: raise ValueError("Số tiền phải lớn hơn 0")
            
        with file_lock:
            db = get_db_raw()
            db = sync_user_data(db, target_id)
            # Trừ tiền, nếu số dư < 0 thì đưa về 0 cho an toàn
            db["users"][target_id]["balance"] -= amount
            if db["users"][target_id]["balance"] < 0:
                db["users"][target_id]["balance"] = 0
            save_db_raw(db)
        
        bot.reply_to(message, f"✅ Đã TRỪ tay *-{amount:,}đ* của ID `{target_id}`", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ Mẫu chuẩn: `ID Khách | Số tiền`\n*(Ví dụ: `123456789 | 50000`)*", parse_mode="Markdown")

def process_admin_status(message):
    if message.from_user.id != ADMIN_ID: return
    new_status = message.text.strip()
    with file_lock:
        db = get_db_raw()
        db["settings"]["admin_status"] = new_status
        save_db_raw(db)
    bot.reply_to(message, f"✅ Đã cập nhật trạng thái Admin thành:\n*{new_status}*", parse_mode="Markdown")

def process_admin_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text_to_send = message.text
    bot.reply_to(message, "⏳ Đang tiến hành gửi thông báo đến toàn bộ hệ thống...")
    
    with file_lock:
        db = get_db_raw()
        users = list(db["users"].keys())
        
    success_count = 0
    for u_id in users:
        # Bỏ qua không gửi cho chính Admin
        if str(u_id) == str(ADMIN_ID): 
            continue
        try:
            bot.send_message(u_id, f"📢 *THÔNG BÁO TỪ HỆ THỐNG*\n━━━━━━━━━━━━━━━━━━━━━━━\n{text_to_send}", parse_mode="Markdown")
            success_count += 1
        except Exception:
            pass # Bỏ qua nếu user chặn bot
            
    bot.send_message(message.chat.id, f"✅ *Hoàn tất quá trình gửi thông báo!*\nĐã gửi thành công: {success_count} người dùng.", parse_mode="Markdown")

# ================= TELEGRAM HANDLERS =================
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    if message.chat.type != 'private':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Mở Cửa Hàng Riêng", url=f"t.me/{bot.get_me().username}?start=shop"))
        bot.reply_to(message, "❌ Vui lòng nhắn tin riêng (Inbox) cho bot để đảm bảo bảo mật tài khoản!", reply_markup=markup)
        return

    uid = str(message.from_user.id)
    with file_lock:
        db = get_db_raw()
        db = sync_user_data(db, uid)
        save_db_raw(db)
    
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    welcome_text = (
        f"🌟 *CHÀO MỪNG ĐẾN VỚI KDANGX STORE* 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Xin chào, *{username}*!\n"
        f"Hệ thống phân phối Tài khoản / Key Tự động cao cấp.\n"
        f"⚡️ Uy Tín - ⚡️ Nhanh Chóng - ⚡️ Bảo Mật.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Vui lòng thao tác tại Menu bên dưới:*"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=build_main_keyboard(), parse_mode="Markdown")
    
@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ THÊM SP", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ XOÁ SP", callback_data="adm_del")
    )
    markup.add(
        types.InlineKeyboardButton("💵 CỘNG TIỀN", callback_data="adm_plus"),
        types.InlineKeyboardButton("📉 TRỪ TIỀN", callback_data="adm_minus")
    )
    markup.add(
        types.InlineKeyboardButton("🔄 ĐỔI TRẠNG THÁI", callback_data="adm_status"),
        types.InlineKeyboardButton("📢 THÔNG BÁO TẤT CẢ", callback_data="adm_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton("📊 CHECK USER", callback_data="adm_checkall"),
        types.InlineKeyboardButton("📝 HƯỚNG DẪN", callback_data="adm_help")
    )
    bot.reply_to(message, "⚙️ *TRUNG TÂM QUẢN TRỊ ADMIN (V2.1)*\n━━━━━━━━━━━━━━━━━━━━━━━\nChọn chức năng bên dưới:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_text_interface(message):
    if message.chat.type != 'private': return

    uid = str(message.from_user.id)
    with file_lock:
        db = get_db_raw()
        db = sync_user_data(db, uid)
        save_db_raw(db)
    
    user_info = db["users"][uid]

    if message.text in ["👤 Hồ Sơ Cá Nhân"]:
        current_bal = user_info['balance']
        profile_text = (
            f"👤 *HỒ SƠ KHÁCH HÀNG*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 ID của bạn: `{uid}` *(Chạm để copy)*\n"
            f"💳 Số dư khả dụng: *{current_bal:,} VNĐ*\n\n"
            f"🛒 Tổng đơn đã mua: {user_info['don_mua']} đơn\n"
            f"💵 Tổng tiền đã nạp: {user_info['total_nap']:,} VNĐ\n"
            f"🔥 Tổng tiền đã tiêu: {user_info['total_tieu']:,} VNĐ\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

    elif message.text in ["☎️ Liên Hệ Hỗ Trợ"]:
        with file_lock:
            db_data = get_db_raw()
            status_text = db_data["settings"]["admin_status"]
            
        support_text = (
            f"👨‍💻 *THÔNG TIN LIÊN HỆ ADMIN*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 Chủ Shop: [@kdangx](https://t.me/kdangx)\n"
            f"🌐 Trạng thái Admin: *{status_text}*\n\n"
            f"📝 *Lưu ý:*\n"
            f"- Mọi giao dịch nạp tiền & xuất hàng đều tự động 100%.\n"
            f"- Nếu gặp lỗi đơn hàng, vui lòng copy mã ID của bạn (`{uid}`) và gửi cho Admin để được hỗ trợ nhanh nhất!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(message.chat.id, support_text, parse_mode="Markdown", disable_web_page_preview=True)

    elif message.text in ["💳 Nạp Số Dư"]:
        msg = bot.send_message(message.chat.id, "💳 *HỆ THỐNG NẠP TIỀN TỰ ĐỘNG*\n━━━━━━━━━━━━━━━━━━━━━━━\n✍️ Vui lòng nhập số tiền bạn muốn nạp bằng số.\n\n*(Ví dụ muốn nạp 50 cành thì nhập: `{}`)*".format("50000"), parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_deposit_input)

    elif message.text in ["🛒 Cửa Hàng"]:
        markup = types.InlineKeyboardMarkup(row_width=1)
        stock_summary = {}
        for acc in db["accounts"]:
            if acc["status"] == "ConHang":
                stock_summary[acc["name"]] = stock_summary.get(acc["name"], 0) + 1
                
        if stock_summary:
            for cat, cnt in stock_summary.items():
                markup.add(types.InlineKeyboardButton(f"📁 {cat} (Còn: {cnt} SP)", callback_data=f"open_cat_{cat}"))
            bot.send_message(message.chat.id, "🛍️ *TRUNG TÂM MUA SẮM*\n━━━━━━━━━━━━━━━━━━━━━━━\nDanh mục sản phẩm hiện đang có sẵn:", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Rất tiếc! Hiện tại tất cả sản phẩm đều đã cháy hàng, vui lòng quay lại sau!*", parse_mode="Markdown")

def process_deposit_input(message):
    try:
        amount = clean_money_value(message.text.strip())
        if amount < 10000:
            bot.reply_to(message, "❌ Số tiền nạp tối thiểu là `10,000 VNĐ`. Vui lòng thử lại.", parse_mode="Markdown")
            return
            
        uid = str(message.from_user.id)
        rand_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        invoice_info = f"NAP{uid}{rand_code}"
        qr_url = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.jpg?accountName={TEN_CHU_TK}&amount={amount}&addInfo={invoice_info}"
        
        caption = (
            f"🏦 *HÓA ĐƠN NẠP TIỀN (Quét QR hoặc Chuyển Tay)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏦 Ngân hàng: *ABBank*\n"
            f"💳 Số tài khoản: `{SO_TAI_KHOAN}` *(Chạm để copy)*\n"
            f"👤 Chủ tài khoản: *{TEN_CHU_TK}*\n"
            f"💵 Số tiền cần chuyển: `{amount}` *(Chạm để copy)*\n"
            f"📝 Nội dung CK: `{invoice_info}` *(Bắt buộc copy)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ *Hệ thống tự động duyệt quỹ trong 10-30 giây.*"
        )
        bot.send_photo(message.chat.id, photo=qr_url, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ Lỗi: Vui lòng chỉ nhập số (Ví dụ: `50000`).", parse_mode="Markdown")

# ================= CALLBACK INTERACTION RESPONSES =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.message.chat.type != 'private':
        bot.answer_callback_query(call.id, "❌ Hãy chat riêng với bot để thao tác!", show_alert=True)
        return

    uid_click = str(call.from_user.id)
    is_admin = (call.from_user.id == ADMIN_ID)

    if call.data.startswith("open_cat_"):
        cat_name = call.data.replace("open_cat_", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_items = False
        
        with file_lock: db = get_db_raw()
        for acc in db["accounts"]:
            if acc["name"] == cat_name and acc["status"] == "ConHang":
                has_items = True
                price_val = clean_money_value(acc['price'])
                markup.add(types.InlineKeyboardButton(f"🎟️ Mã SP #{acc['id']} — Giá: {price_val:,}đ", callback_data=f"target_sp_{acc['id']}"))
                
        markup.add(types.InlineKeyboardButton("🔙 Quay Lại Danh Mục", callback_data="nav_home"))
        if has_items:
            bot.edit_message_text(f"📦 *DANH SÁCH: {cat_name}*\n━━━━━━━━━━━━━━━━━━━━━━━\nBấm chọn vào mã SP để xem chi tiết:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Chậm chân rồi, sản phẩm này vừa bị người khác mua mất!", show_alert=True)
            handle_callbacks(types.CallbackQuery(call.id, call.from_user, call.data, call.chat_instance, call.message, "nav_home"))

    elif call.data.startswith("target_sp_"):
        acc_id = int(call.data.split("_")[2])
        with file_lock: db = get_db_raw()
        product = next((acc for acc in db["accounts"] if acc["id"] == acc_id), None)
        
        if product:
            price_val = clean_money_value(product['price'])
            detail_text = (
                f"🔎 *CHI TIẾT ĐƠN HÀNG (#{product['id']})*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 Sản phẩm: *{product['name']}*\n"
                f"💰 Giá bán: *{price_val:,} VNĐ*\n"
                f"⚡️ Trạng thái: *Sẵn sàng giao (Auto)*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Lưu ý:* Vui lòng kiểm tra lại số dư trước khi ấn Mua."
            )
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(f"💳 XÁC NHẬN MUA NGAY (-{price_val:,}đ)", callback_data=f"commit_checkout_{product['id']}"),
                types.InlineKeyboardButton("🔙 Quay Lại", callback_data=f"open_cat_{product['name']}")
            )
            bot.edit_message_text(detail_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "nav_home":
        markup = types.InlineKeyboardMarkup(row_width=1)
        stock_summary = {}
        with file_lock: db = get_db_raw()
        for acc in db["accounts"]:
            if acc["status"] == "ConHang": stock_summary[acc["name"]] = stock_summary.get(acc["name"], 0) + 1
            
        if stock_summary:
            for cat, cnt in stock_summary.items():
                markup.add(types.InlineKeyboardButton(f"📁 {cat} (Còn: {cnt} SP)", callback_data=f"open_cat_{cat}"))
            bot.edit_message_text("🛍️ *TRUNG TÂM MUA SẮM*\n━━━━━━━━━━━━━━━━━━━━━━━\nDanh mục sản phẩm hiện đang có sẵn:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ *Kho hàng hiện đang trống!*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data.startswith("commit_checkout_"):
        acc_id = int(call.data.split("_")[2])
        success = False
        product_info = None
        
        with file_lock:
            db = get_db_raw()
            db = sync_user_data(db, uid_click)
            product = next((acc for acc in db["accounts"] if acc["id"] == acc_id and acc["status"] == "ConHang"), None)
            
            if not product:
                bot.answer_callback_query(call.id, "❌ Sản phẩm đã bị người khác mua hoặc không tồn tại!", show_alert=True)
                return

            wallet_balance = db["users"][uid_click]["balance"]
            product_price = clean_money_value(product["price"])
            
            if wallet_balance < product_price:
                bot.answer_callback_query(call.id, f"❌ Thiếu lúa! Số dư của bạn hiện tại là: {wallet_balance:,}đ.", show_alert=True)
                return
                
            # Thanh toán
            db["users"][uid_click]["balance"] -= product_price
            db["users"][uid_click]["total_tieu"] += product_price
            db["users"][uid_click]["don_mua"] += 1
            product["status"] = "DaBan"
            
            if save_db_raw(db):
                success = True
                product_info = product

        if success:
            success_text = (
                f"🎉 *MUA HÀNG THÀNH CÔNG*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 Sản phẩm: *{product_info['name']}* (Mã: `#{product_info['id']}`)\n"
                f"💸 Đã thanh toán: *-{product_price:,} VNĐ*\n\n"
                f"🔐 *THÔNG TIN TÀI KHOẢN (Chạm để copy):*\n"
                f"```text\n{product_info['info']}\n```\n\n"
                f"⚠️ *Lưu ý:* Vui lòng đổi mật khẩu ngay lập tức sau khi đăng nhập thành công!\n"
                f"❤️ *Cảm ơn bạn đã tin tưởng và ủng hộ KDANGX STORE!*"
            )
            bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            # --- THÔNG BÁO CHO ADMIN KHI CÓ ĐƠN HÀNG MỚI ---
            try:
                admin_msg = (
                    f"🛒 *TING TING! CÓ ĐƠN HÀNG MỚI!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 Khách hàng ID: `{uid_click}`\n"
                    f"📦 Sản phẩm: {product_info['name']} (`#{product_info['id']}`)\n"
                    f"💵 Doanh thu: *+{product_price:,} VNĐ*\n"
                    f"✅ Đã giao hàng tự động."
                )
                bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
            except Exception: pass
            
        else:
            bot.answer_callback_query(call.id, "❌ Lỗi hệ thống: Không thể xử lý giao dịch lúc này.", show_alert=True)

    # --- ADMIN INLINE ROUTER ---
    elif call.data == "adm_add":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📝 Vui lòng gửi thông tin SP theo định dạng:\n`Giá | Tên | Tài khoản | Mật khẩu`\n\n*(Ví dụ: `50000 | Netflix | admin | 123`)*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_add_product)
        
    elif call.data == "adm_del":
        if not is_admin: return
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_item = False
        with file_lock: db = get_db_raw()
        for acc in db["accounts"]:
            if acc["status"] == "ConHang":
                has_item = True
                markup.add(types.InlineKeyboardButton(f"❌ Xóa #{acc['id']} - {acc['name']}", callback_data=f"kill_sp_{acc['id']}"))
        if has_item:
            bot.send_message(call.message.chat.id, "🛠 *Chọn sản phẩm muốn XOÁ khỏi kho:*", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "📭 Kho hiện tại không có hàng để xoá.")
            
    elif call.data.startswith("kill_sp_"):
        if not is_admin: return
        target_id = int(call.data.split("_")[2])
        with file_lock:
            db = get_db_raw()
            db["accounts"] = [a for a in db["accounts"] if a["id"] != target_id]
            save_db_raw(db)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, f"🗑 Đã xoá vĩnh viễn sản phẩm mã `#{target_id}`.", parse_mode="Markdown")
        
    elif call.data == "adm_plus":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "💵 *CỘNG TIỀN*\nVui lòng gửi theo cú pháp:\n`ID Khách | Số tiền`\n*(Ví dụ: `1234567 | 50000`)*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_deposit)
        
    elif call.data == "adm_minus":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📉 *TRỪ TIỀN*\nVui lòng gửi theo cú pháp:\n`ID Khách | Số tiền`\n*(Ví dụ: `1234567 | 50000`)*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_deduct)

    elif call.data == "adm_status":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "🔄 *CẬP NHẬT TRẠNG THÁI ADMIN*\nVui lòng nhập trạng thái mới (VD: `🔴 Offline` hoặc `🟢 Online`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_status)

    elif call.data == "adm_broadcast":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📢 *THÔNG BÁO TOÀN SHOP*\nVui lòng nhập nội dung muốn gửi đến tất cả người dùng:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_admin_broadcast)

    elif call.data == "adm_checkall":
        if not is_admin: return
        with file_lock: db = get_db_raw()
        users_list = db.get("users", {})
        report_text = "📊 *THỐNG KÊ KHÁCH HÀNG*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        index_num = 1
        for u_id, info in users_list.items():
            if u_id == str(ADMIN_ID): continue
            bal = info.get('balance', 0)
            t_nap = info.get('total_nap', 0)
            report_text += f"{index_num}. ID: `{u_id}` | Dư: {bal:,}đ | Nạp: {t_nap:,}đ\n"
            index_num += 1
        if index_num == 1:
            report_text += "Chưa có khách hàng nào!"
        bot.send_message(call.message.chat.id, report_text, parse_mode="Markdown")

    elif call.data == "adm_help":
        if not is_admin: return
        help_text = (
            "📝 *HƯỚNG DẪN DÀNH CHO ADMIN*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "**1. THÊM SP:** Chọn nút thêm và gõ theo cấu trúc:\n`Giá | Tên SP | Thông tin SP`\n"
            "*(Bạn có thể gõ bao nhiêu dấu `|` ở phần thông tin cũng được, bot tự hiểu)*\n\n"
            "**2. CỘNG/TRỪ TIỀN:** Gõ ID khách và số tiền cách nhau bởi dấu `|`.\nVí dụ: `123456789 | 50000`\n\n"
            "**3. ĐỔI TRẠNG THÁI:** Tuỳ chỉnh chữ hiển thị tại mục Liên Hệ Hỗ Trợ.\n\n"
            "**4. QUẢN LÝ:** Mọi dữ liệu an toàn trong file `shop_data.json`."
        )
        bot.send_message(call.message.chat.id, help_text, parse_mode="Markdown")
        
    try: bot.answer_callback_query(call.id)
    except: pass

def run_web_gateway():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    init_db()
    try: bot.remove_webhook()
    except: pass
    
    gateway_thread = Thread(target=run_web_gateway)
    gateway_thread.daemon = True
    gateway_thread.start()
    
    bot.infinity_polling(skip_pending=True)
