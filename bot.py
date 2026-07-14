import os
import json
import random
import logging
import re
from threading import Thread, Lock
from flask import Flask, request, jsonify
import telebot
from telebot import types

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

# ================= CORE DATA MANAGEMENT (FIXED RACE CONDITION) =================
def init_db():
    if not os.path.exists(DATA_FILE):
        initial_data = {"users": {}, "accounts": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)

def clean_money_value(val) -> int:
    if val is None: return 0
    if isinstance(val, (int, float)): return int(val)
    try:
        cleaned = re.sub(r'[^\d]', '', str(val))
        return int(cleaned) if cleaned else 0
    except Exception: return 0

# Hàm chỉ đọc (Không lock, lock sẽ bọc ở vòng ngoài)
def get_db_raw() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "accounts": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("users", {})
            data.setdefault("accounts", [])
            return data
    except Exception:
        return {"users": {}, "accounts": []}

# Hàm chỉ ghi (Không lock, lock sẽ bọc ở vòng ngoài)
def save_db_raw(data: dict) -> bool:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def sync_user_data(data: dict, user_id: str) -> dict:
    user_id = str(user_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "balance": 0, "total_nap": 0, "total_tieu": 0, "don_mua": 0
        }
    else:
        data["users"][user_id]["balance"] = clean_money_value(data["users"][user_id].get("balance", 0))
        data["users"][user_id]["total_nap"] = clean_money_value(data["users"][user_id].get("total_nap", 0))
        data["users"][user_id]["total_tieu"] = clean_money_value(data["users"][user_id].get("total_tieu", 0))
        data["users"][user_id]["don_mua"] = int(data["users"][user_id].get("don_mua", 0))
    return data

# ================= KEYBOARD UI BUILDERS =================
def build_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 Mua Sản Phẩm"),
        types.KeyboardButton("💳 Nạp Số Dư")
    )
    markup.add(
        types.KeyboardButton("👤 Hồ Sơ Cá Nhân"),
        types.KeyboardButton("☎️ Hỗ Trợ/Liên Hệ")
    )
    return markup

# ================= WEBHOOK AUTOMATION (ABBANK) =================
@app.route('/', methods=['GET'])
def index():
    return "VIP Shop Bot Gateway is running smoothly!", 200

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
                        with file_lock: # BẢO VỆ DỮ LIỆU CHẶT CHẼ
                            db = get_db_raw()
                            db = sync_user_data(db, client_id)
                            db["users"][client_id]["balance"] += amount
                            db["users"][client_id]["total_nap"] += amount
                            success = save_db_raw(db)
                            
                        if success:
                            # Báo khách hàng
                            try:
                                receipt = (
                                    f"✅ *NẠP TIỀN THÀNH CÔNG*\n"
                                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"Tài khoản của bạn vừa được cộng: *+{amount:,} VNĐ*\n"
                                    f"Cảm ơn bạn đã sử dụng dịch vụ!"
                                )
                                bot.send_message(client_id, receipt, parse_mode="Markdown")
                            except Exception: pass
                                
                            # Báo Admin
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
            
        bot.reply_to(message, f"✅ *THÊM KHO THÀNH CÔNG*\n📦 {name} | Mã: #{next_id} | 💰 {price:,}đ", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "❌ Sai định dạng! Hãy gửi: `Giá | Tên Gói | Tài khoản | Mật khẩu`", parse_mode="Markdown")

def process_admin_deposit(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split("|")
        target_id = str(parts[0].strip())
        amount = clean_money_value(parts[1].strip())
        
        if amount <= 0: raise ValueError
            
        with file_lock:
            db = get_db_raw()
            db = sync_user_data(db, target_id)
            db["users"][target_id]["balance"] += amount
            db["users"][target_id]["total_nap"] += amount
            save_db_raw(db)
        
        bot.reply_to(message, f"✅ Đã nạp tay *+{amount:,}đ* cho ID `{target_id}`", parse_mode="Markdown")
        try:
            bot.send_message(target_id, f"🎁 *QUÀ TẶNG TỪ ADMIN*\nTài khoản của bạn vừa nhận được *+{amount:,} VNĐ*", parse_mode="Markdown")
        except: pass
    except Exception:
        bot.reply_to(message, "❌ Mẫu chuẩn: `ID Khách | Số tiền`", parse_mode="Markdown")

# ================= TELEGRAM HANDLERS =================
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    if message.chat.type != 'private':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Truy cập cửa hàng", url=f"t.me/{bot.get_me().username}?start=shop"))
        bot.reply_to(message, "❌ Vui lòng nhắn tin riêng cho bot để mua hàng an toàn!", reply_markup=markup)
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
        f"Hệ thống phân phối Tài khoản / Key tự động 24/7.\n"
        f"Uy Tín - Nhanh Chóng - Bảo Mật.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *Lựa chọn tính năng ở Menu bên dưới:*"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=build_main_keyboard(), parse_mode="Markdown")
    
@bot.message_handler(commands=['admin'])
def handle_admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ THÊM SP", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ XOÁ SP", callback_data="adm_del"),
        types.InlineKeyboardButton("💵 CỘNG TIỀN", callback_data="adm_plus"),
        types.InlineKeyboardButton("📊 CHECK USER", callback_data="adm_checkall")
    )
    bot.reply_to(message, "⚙️ *TRUNG TÂM QUẢN TRỊ ADMIN*", reply_markup=markup, parse_mode="Markdown")

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
            f"🆔 ID của bạn: `{uid}`\n"
            f"💳 Số dư khả dụng: *{current_bal:,} VNĐ*\n"
            f"🛒 Tổng đơn đã mua: {user_info['don_mua']}\n"
            f"💵 Tổng tiền đã nạp: {user_info['total_nap']:,} VNĐ\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

    elif message.text in ["☎️ Hỗ Trợ/Liên Hệ"]:
        bot.send_message(message.chat.id, "👨‍💻 *THÔNG TIN LIÊN HỆ*\n- Chủ Shop: @kdangx\n- Trạng thái: Online", parse_mode="Markdown")

    elif message.text in ["💳 Nạp Số Dư"]:
        msg = bot.send_message(message.chat.id, "💳 *HỆ THỐNG NẠP TIỀN*\nNhập số tiền bạn muốn nạp (Ví dụ: `50000`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_deposit_input)

    elif message.text in ["🛒 Mua Sản Phẩm"]:
        markup = types.InlineKeyboardMarkup(row_width=1)
        stock_summary = {}
        for acc in db["accounts"]:
            if acc["status"] == "ConHang":
                stock_summary[acc["name"]] = stock_summary.get(acc["name"], 0) + 1
                
        if stock_summary:
            for cat, cnt in stock_summary.items():
                markup.add(types.InlineKeyboardButton(f"📁 {cat} (Còn: {cnt})", callback_data=f"open_cat_{cat}"))
            bot.send_message(message.chat.id, "🛍️ *KHO SẢN PHẨM HIỆN CÓ*\nChọn danh mục bạn quan tâm:", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Xin lỗi, hiện tại tất cả sản phẩm đều cháy hàng!*")

def process_deposit_input(message):
    try:
        amount = clean_money_value(message.text.strip())
        if amount < 10000:
            bot.reply_to(message, "❌ Số tiền nạp tối thiểu là 10,000 VNĐ. Vui lòng thử lại.")
            return
            
        uid = str(message.from_user.id)
        rand_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        invoice_info = f"NAP{uid}{rand_code}"
        qr_url = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.jpg?accountName={TEN_CHU_TK}&amount={amount}&addInfo={invoice_info}"
        
        caption = (
            f"🏦 *HÓA ĐƠN NẠP TIỀN VIETQR*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Ngân hàng: ABBank\n"
            f"Số tài khoản: `{SO_TAI_KHOAN}`\n"
            f"Chủ thẻ: {TEN_CHU_TK}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Số tiền: *{amount:,} VNĐ*\n"
            f"Nội dung CK: `{invoice_info}` (Chạm để copy)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ *Hệ thống tự động cộng tiền trong 10-30 giây.*"
        )
        bot.send_photo(message.chat.id, photo=qr_url, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ Đầu vào không hợp lệ. Vui lòng nhập số (VD: 50000).")

# ================= CALLBACK INTERACTION RESPONSES =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.message.chat.type != 'private':
        bot.answer_callback_query(call.id, "❌ Chat riêng với bot để mua hàng nhé!", show_alert=True)
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
            bot.edit_message_text(f"📦 *DANH SÁCH: {cat_name}*\nBấm chọn để xem chi tiết:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Đã có người nhanh tay mua mất rồi!", show_alert=True)

    elif call.data.startswith("target_sp_"):
        acc_id = int(call.data.split("_")[2])
        with file_lock: db = get_db_raw()
        product = next((acc for acc in db["accounts"] if acc["id"] == acc_id), None)
        
        if product:
            price_val = clean_money_value(product['price'])
            detail_text = (
                f"🔎 *CHI TIẾT MÃ #{product['id']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Loại hàng: {product['name']}\n"
                f"Giá bán: *{price_val:,} VNĐ*\n"
                f"Trạng thái: Sẵn sàng giao\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(f"💳 XÁC NHẬN MUA NGAY", callback_data=f"commit_checkout_{product['id']}"),
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
                markup.add(types.InlineKeyboardButton(f"📁 {cat} (Còn: {cnt})", callback_data=f"open_cat_{cat}"))
            bot.edit_message_text("🛍️ *KHO SẢN PHẨM HIỆN CÓ*\nChọn danh mục bạn quan tâm:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
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
                bot.answer_callback_query(call.id, "❌ Sản phẩm đã được người khác mua!", show_alert=True)
                return

            wallet_balance = db["users"][uid_click]["balance"]
            product_price = clean_money_value(product["price"])
            
            if wallet_balance < product_price:
                bot.answer_callback_query(call.id, f"❌ Thiếu tiền! Số dư của bạn là: {wallet_balance:,}đ.", show_alert=True)
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
                f"Sản phẩm: {product_info['name']} (#{product_info['id']})\n"
                f"Đã thanh toán: -{product_price:,} VNĐ\n\n"
                f"🔑 *THÔNG TIN SẢN PHẨM:*\n"
                f"`{product_info['info']}`\n\n"
                f"⚠️ Lưu ý: Đổi pass ngay lập tức!"
            )
            bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            
            # --- THÔNG BÁO CHO ADMIN KHI CÓ ĐƠN HÀNG MỚI ---
            try:
                admin_msg = (
                    f"🛒 *CÓ ĐƠN HÀNG MỚI BÁN RA!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 Khách hàng ID: `{uid_click}`\n"
                    f"📦 Sản phẩm: {product_info['name']} (#{product_info['id']})\n"
                    f"💵 Doanh thu: *+{product_price:,} VNĐ*\n"
                    f"✅ Đã giao hàng tự động."
                )
                bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
            except Exception: pass
            
        else:
            bot.answer_callback_query(call.id, "❌ Lỗi hệ thống ghi dữ liệu trục trặc.", show_alert=True)

    # --- ADMIN INLINE ROUTER ---
    elif call.data == "adm_add":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📝 Định dạng: `Giá | Tên | Tài khoản | Mật khẩu`")
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
            bot.send_message(call.message.chat.id, "🛠 Chọn sản phẩm xoá:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "📭 Kho trống.")
            
    elif call.data.startswith("kill_sp_"):
        if not is_admin: return
        target_id = int(call.data.split("_")[2])
        with file_lock:
            db = get_db_raw()
            db["accounts"] = [a for a in db["accounts"] if a["id"] != target_id]
            save_db_raw(db)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, f"🗑 Đã loại bỏ mã #{target_id}.")
        
    elif call.data == "adm_plus":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "💵 Gửi: `ID Khách | Số tiền`")
        bot.register_next_step_handler(msg, process_admin_deposit)
        
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
        bot.send_message(call.message.chat.id, report_text, parse_mode="Markdown")
        
    bot.answer_callback_query(call.id)

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
