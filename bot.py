import os
import json
import random
import logging
from threading import Thread, Lock
from flask import Flask, request, jsonify
import telebot
from telebot import types

# Cấu hình logging để giám sát hệ thống chuyên nghiệp
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
file_lock = Lock()  # Khóa luồng bảo vệ dữ liệu an toàn tuyệt đối

# ================= CORE DATA MANAGEMENT =================
def init_db():
    """Khởi tạo cơ sở dữ liệu nếu chưa tồn tại"""
    if not os.path.exists(DATA_FILE):
        initial_data = {"users": {}, "accounts": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        logging.info("Khởi tạo file dữ liệu shop_data.json thành công.")

def read_db() -> dict:
    """Đọc dữ liệu từ file JSON an toàn với Lock"""
    with file_lock:
        try:
            if not os.path.exists(DATA_FILE):
                return {"users": {}, "accounts": []}
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("users", {})
                data.setdefault("accounts", [])
                return data
        except Exception as e:
            logging.error(f"Lỗi đọc file DB: {e}")
            return {"users": {}, "accounts": []}

def write_db(data: dict) -> bool:
    """Ghi dữ liệu vào file JSON an toàn với Lock"""
    with file_lock:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logging.error(f"Lỗi ghi file DB: {e}")
            return False

def sync_user_data(data: dict, user_id: str) -> dict:
    """Đồng bộ và ép kiểu dữ liệu người dùng (Admin có số dư khởi tạo = 0)"""
    user_id = str(user_id)
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "balance": 0,
            "total_nap": 0,
            "total_tieu": 0,
            "don_mua": 0
        }
    else:
        # Ép kiểu int an toàn để triệt tiêu lỗi không trừ tiền
        data["users"][user_id]["balance"] = int(data["users"][user_id].get("balance", 0))
        data["users"][user_id]["total_nap"] = int(data["users"][user_id].get("total_nap", 0))
        data["users"][user_id]["total_tieu"] = int(data["users"][user_id].get("total_tieu", 0))
        data["users"][user_id]["don_mua"] = int(data["users"][user_id].get("don_mua", 0))
    return data

# ================= KEYBOARD UI BUILDERS =================
def build_main_keyboard():
    """Tạo bàn phím tương tác chính"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ Mua Key/Acc"),
        types.KeyboardButton("💳 Nạp Tiền Shop"),
        types.KeyboardButton("👤 Tài Khoản Của Tôi"),
        types.KeyboardButton("🛠️ Admin Panel")
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
        amount = int(req_data.get("amount", 0))
        
        if "NAP" in description and amount > 0:
            raw_content = description.replace("NAP", "").strip()
            client_id = raw_content[:-6]  # Loại bỏ mã bill ngẫu nhiên
            
            if client_id.isdigit():
                client_id = str(client_id)
                db = read_db()
                db = sync_user_data(db, client_id)
                
                # Cập nhật số dư
                db["users"][client_id]["balance"] += amount
                db["users"][client_id]["total_nap"] += amount
                
                if write_db(db):
                    logging.info(f"Nạp tiền tự động thành công cho Client ID: {client_id} (+{amount:,}đ)")
                    try:
                        bot.send_message(
                            client_id, 
                            f"🎉 *HỆ THỐNG CỘNG TIỀN THÀNH CÔNG!*\n━━━━━━━━━━━━━━━━━━━━━━━\n💰 Tài khoản của bạn đã được cộng tự động *+{amount:,} VNĐ* qua cổng ABBank VIP.", 
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logging.warning(f"Không thể gửi thông báo tới khách {client_id}: {e}")
                        
                    try:
                        bot.send_message(
                            ADMIN_ID, 
                            f"💰 *THÔNG BÁO BIẾN ĐỘNG QUỸ SHOP*\n━━━━━━━━━━━━━━━━━━━━━━━\n👤 Khách hàng ID `{client_id}` vừa nạp thành công *{amount:,}đ* qua hệ thống Gateway.", 
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logging.warning(f"Không thể gửi thông báo tới Admin: {e}")
                        
                    return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Lỗi hệ thống Webhook API: {e}")
    return jsonify({"status": "error"}), 400

# ================= ADMIN ACTIONS =================
def process_admin_add_product(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        if "|" not in message.text:
            bot.reply_to(message, "❌ *Sai định dạng cấu trúc!* Vui lòng nhập theo mẫu:\n`Giá | Tên kho sản phẩm | Tài khoản | Mật khẩu`", parse_mode="Markdown")
            return
            
        parts = message.text.split("|")
        price = int(parts[0].strip())
        name = parts[1].strip()
        info = "|".join(parts[2:]).strip()
        
        db = read_db()
        existing_ids = [acc["id"] for acc in db["accounts"]]
        next_id = max(existing_ids) + 1 if existing_ids else 1
        
        db["accounts"].append({
            "id": next_id,
            "name": name,
            "price": price,
            "info": info,
            "status": "ConHang"
        })
        write_db(db)
        bot.reply_to(message, f"✅ *THÊM SẢN PHẨM THÀNH CÔNG!*\n━━━━━━━━━━━━━━━━━━━━━━━\n📦 **Loại kho:** {name}\n🆔 **Mã số:** #{next_id}\n💰 **Định giá:** {price:,} VNĐ", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ *Thao tác thất bại!* Kiểm tra định dạng số tiền. Chi tiết: {e}", parse_mode="Markdown")

def process_admin_deposit(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split("|")
        target_id = str(parts[0].strip())
        amount = int(parts[1].strip())
        reason = parts[2].strip() if len(parts) > 2 else "Được bổ sung số dư bởi Ban quản trị"
        
        if amount <= 0:
            bot.reply_to(message, "❌ Số tiền cộng hợp lệ phải lớn hơn 0.")
            return
            
        db = read_db()
        db = sync_user_data(db, target_id)
        
        db["users"][target_id]["balance"] += amount
        db["users"][target_id]["total_nap"] += amount
        write_db(db)
        
        bot.reply_to(message, f"✅ Đã điều chỉnh cộng *+{amount:,}đ* cho tài khoản ID `{target_id}`.", parse_mode="Markdown")
        try:
            bot.send_message(
                target_id, 
                f"🎉 *BIẾN ĐỘNG SỐ DƯ TÀI KHOẢN!*\n━━━━━━━━━━━━━━━━━━━━━━━\n💰 Ví của bạn được Admin cộng thêm *+{amount:,} VNĐ*.\n📝 **Lý do:** {reason}", 
                parse_mode="Markdown"
            )
        except: pass
    except Exception:
        bot.reply_to(message, "❌ Lỗi thực thi! Sai định dạng đầu vào. Mẫu: `ID | Số tiền | Ghi chú`")

def process_admin_withdraw(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split("|")
        target_id = str(parts[0].strip())
        amount = int(parts[1].strip())
        reason = parts[2].strip() if len(parts) > 2 else "Bị khấu trừ tài khoản bởi Admin"
        
        if amount <= 0:
            bot.reply_to(message, "❌ Số tiền khấu trừ hợp lệ phải lớn hơn 0.")
            return
            
        db = read_db()
        if target_id not in db["users"]:
            bot.reply_to(message, "❌ Thất bại! Khách hàng này chưa từng đăng ký trên hệ thống.")
            return
            
        db["users"][target_id]["balance"] -= amount
        if db["users"][target_id]["balance"] < 0:
            db["users"][target_id]["balance"] = 0
            
        write_db(db)
        bot.reply_to(message, f"✅ Đã khấu trừ thành công *-{amount:,}đ* của tài khoản ID `{target_id}`.", parse_mode="Markdown")
        try:
            bot.send_message(
                target_id, 
                f"💸 *BIẾN ĐỘNG SỐ DƯ TÀI KHOẢN!*\n━━━━━━━━━━━━━━━━━━━━━━━\n⚠️ Ví của bạn đã bị khấu trừ *-{amount:,} VNĐ* theo lệnh Admin.\n📝 **Lý do:** {reason}", 
                parse_mode="Markdown"
            )
        except: pass
    except Exception:
        bot.reply_to(message, "❌ Lỗi thực thi! Sai định dạng đầu vào. Mẫu: `ID | Số tiền | Ghi chú`")

def process_admin_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    content = message.text.strip()
    if not content:
        bot.reply_to(message, "❌ Nội dung phát sóng không được để trống.")
        return
        
    db = read_db()
    user_list = db.get("users", {})
    
    progress_msg = bot.reply_to(message, f"⏳ Hệ thống đang gửi thông báo tới {len(user_list)} người dùng...")
    success, fail = 0, 0
    
    for uid in user_list:
        try:
            bot.send_message(
                uid, 
                f"📢 *THÔNG BÁO TOÀN HỆ THỐNG*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n{content}\n\n━━━━━━━━━━━━━━━━━━━━━━━", 
                parse_mode="Markdown"
            )
            success += 1
        except:
            fail += 1
            
    bot.edit_message_text(
        f"✅ *KẾT QUẢ PHÁT THÔNG BÁO:*\n🚀 Thành công: {success}\n❌ Thất bại (Chặn bot): {fail}", 
        message.chat.id, 
        progress_msg.message_id, 
        parse_mode="Markdown"
    )

# ================= TELEGRAM HANDLERS =================
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    uid = str(message.from_user.id)
    db = read_db()
    db = sync_user_data(db, uid)
    write_db(db)
    
    username = f"@{message.from_user.username}" if message.from_user.username else (message.from_user.first_name or "Thành viên")
    welcome_text = (
        f"👑 *HỆ THỐNG SHOP KDANGX VIP* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Xin chào *{username}*!\n"
        f"🔥 Nơi giao dịch và phân phối Acc/Key Free Fire hoàn toàn tự động, uy tín 24/7.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 Vui lòng sử dụng các phím điều hướng bên dưới:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=build_main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: True)
def handle_text_interface(message):
    uid = str(message.from_user.id)
    db = read_db()
    db = sync_user_data(db, uid)
    write_db(db)
    
    user_info = db["users"][uid]
    is_admin = (message.from_user.id == ADMIN_ID)
    username = f"@{message.from_user.username}" if message.from_user.username else (message.from_user.first_name or "Thành viên")

    if message.text in ["👤 Tài Khoản Của Tôi", "👤 Tài Khoản"]:
        role = "ADMIN TỐI THƯỢNG" if is_admin else "USER"
        profile_text = (
            f"👤 *THÔNG TIN TÀI KHOẢN NGƯỜI DÙNG*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 **ID Tài khoản:** `{uid}`\n"
            f"👤 **Tên hiển thị:** {username}\n"
            f"⭐ **Hạng cấp tài khoản:** {role}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Số dư ví hiện tại:** {user_info['balance']:,}đ\n"
            f"💸 **Tổng chi tiêu:** {user_info['total_tieu']:,}đ\n"
            f"💳 **Tổng tiền đã nạp:** {user_info['total_nap']:,}đ\n"
            f"🛒 **Đơn hàng đã mua:** {user_info['don_mua']}\n\n"
            f"🆘 **Liên hệ hỗ trợ:** @kdangx"
        )
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

    elif message.text in ["💳 Nạp Tiền Shop", "💳 Nạp Tiền"]:
        msg = bot.send_message(message.chat.id, "💳 *CỔNG NẠP TIỀN TỰ ĐỘNG VNPAY/VIETQR*\nVui lòng nhập số tiền bạn muốn nạp vào shop (Ví dụ: `50000`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_deposit_input)

    elif message.text == "🛍️ Mua Key/Acc":
        markup = types.InlineKeyboardMarkup(row_width=1)
        stock_summary = {}
        for acc in db["accounts"]:
            if acc["status"] == "ConHang":
                stock_summary[acc["name"]] = stock_summary.get(acc["name"], 0) + 1
                
        if stock_summary:
            for category, count in stock_summary.items():
                markup.add(types.InlineKeyboardButton(f"📁 {category} • [Số lượng: {count}]", callback_data=f"open_cat_{category}"))
            bot.send_message(message.chat.id, "🛍️ *DANH MỤC SẢN PHẨM ĐANG SẴN HÀNG*\nVui lòng chọn loại sản phẩm bạn cần:", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ *Hiện tại kho hàng của hệ thống đang tạm hết sản phẩm!* Vui lòng quay lại sau.")

    elif message.text == "🛠️ Admin Panel":
        # Chặn khách hàng bấm trực tiếp vào Admin Panel từ bàn phím Reply
        if not is_admin:
            bot.reply_to(message, "❌ *Quyền truy cập bị từ chối!*\nKhu vực chỉ dành riêng cho Admin tối thượng của Shop.", parse_mode="Markdown")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ THÊM ACC", callback_data="adm_add"),
            types.InlineKeyboardButton("➖ XOÁ ACC", callback_data="adm_del"),
            types.InlineKeyboardButton("💵 CỘNG TIỀN KHÁCH", callback_data="adm_plus"),
            types.InlineKeyboardButton("💸 TRỪ TIỀN KHÁCH", callback_data="adm_minus")
        )
        markup.add(types.InlineKeyboardButton("📊 DANH SÁCH KHÁCH HÀNG (CHECK ALL)", callback_data="adm_checkall"))
        markup.add(types.InlineKeyboardButton("📢 PHÁT THÔNG BÁO SHOP", callback_data="adm_bc"))
        bot.send_message(message.chat.id, "🛠️ *BẢNG ĐIỀU KHIỂN HỆ THỐNG QUẢN TRỊ*", reply_markup=markup, parse_mode="Markdown")

def process_deposit_input(message):
    if message.text in ["🛍️ Mua Key/Acc", "💳 Nạp Tiền Shop", "👤 Tài Khoản Của Tôi", "🛠️ Admin Panel"]:
        handle_text_interface(message)
        return
    try:
        amount = int(message.text.strip())
        if amount < 1000:
            bot.reply_to(message, "❌ Số tiền nạp tối thiểu được cấu hình là 1.000 VNĐ.")
            return
            
        uid = str(message.from_user.id)
        rand_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        invoice_info = f"NAP{uid}{rand_code}"
        
        qr_url = f"https://api.vietqr.io/image/{MA_NGAN_HANG}-{SO_TAI_KHOAN}-print.jpg?accountName={TEN_CHU_TK}&amount={amount}&addInfo={invoice_info}"
        
        caption = (
            f"🏦 *THÔNG TIN GIAO DỊCH CHUYỂN KHOẢN*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏛️ **Ngân hàng:** ABBank (Ngân Hàng An Bình)\n"
            f"💳 **Số tài khoản:** `{SO_TAI_KHOAN}`\n"
            f"👤 **Chủ tài khoản:** {TEN_CHU_TK}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Số tiền cần chuyển:** {amount:,}đ\n"
            f"📝 **Nội dung chuyển tiền:** `{invoice_info}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ **Lưu ý quan trọng:** Quét QR hoặc nhập chuẩn xác 100% nội dung để hệ thống Auto nạp tiền sau 1-2 phút."
        )
        bot.send_photo(message.chat.id, photo=qr_url, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "❌ Đầu vào không hợp lệ. Vui lòng điền số nguyên đại diện cho mệnh giá.")

# ================= CALLBACK INTERACTION RESPONSES =================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid_click = str(call.from_user.id)
    db = read_db()
    is_admin = (call.from_user.id == ADMIN_ID)

    if call.data.startswith("open_cat_"):
        cat_name = call.data.replace("open_cat_", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_items = False
        
        for acc in db["accounts"]:
            if acc["name"] == cat_name and acc["status"] == "ConHang":
                has_items = True
                markup.add(types.InlineKeyboardButton(f"🎟️ Mã SP #{acc['id']} — Giá: {acc['price']:,}đ", callback_data=f"target_sp_{acc['id']}"))
                
        markup.add(types.InlineKeyboardButton("⬅️ Quay lại danh mục chính", callback_data="nav_home"))
        if has_items:
            bot.edit_message_text(f"📦 *KHO SẢN PHẨM ĐANG CHỨA:* `{cat_name}`\n━━━━━━━━━━━━━━━━━━━━━━━\nVui lòng lựa chọn một mã số sản phẩm để xem chi tiết cấu trúc tài khoản:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Rất tiếc, phân mục này vừa bị mua sạch hàng!", show_alert=True)

    elif call.data.startswith("target_sp_"):
        acc_id = int(call.data.split("_")[2])
        product = next((acc for acc in db["accounts"] if acc["id"] == acc_id), None)
        
        if product:
            detail_text = (
                f"📦 *THÔNG TIN SẢN PHẨM CHI TIẾT*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 **Mã Số:** #{product['id']}\n"
                f"🏷️ **Loại hàng:** {product['name']}\n"
                f"💰 **Đơn giá thanh toán:** {product['price']:,}đ\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚡ Nhấp nút mua phía dưới, tài khoản sẽ được bóc tách hiển thị ngay lập tức."
            )
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton(f"💳 Tiến Hành Mua Ngay", callback_data=f"commit_checkout_{product['id']}"),
                types.InlineKeyboardButton("⬅️ Quay lại", callback_data="nav_home")
            )
            bot.edit_message_text(detail_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "nav_home":
        markup = types.InlineKeyboardMarkup(row_width=1)
        stock_summary = {}
        for acc in db["accounts"]:
            if acc["status"] == "ConHang": stock_summary[acc["name"]] = stock_summary.get(acc["name"], 0) + 1
            
        if stock_summary:
            for cat, cnt in stock_summary.items():
                markup.add(types.InlineKeyboardButton(f"📁 {cat} • [Số lượng: {cnt}]", callback_data=f"open_cat_{cat}"))
            bot.edit_message_text("🛍️ *DANH MỤC SẢN PHẨM ĐANG SẴN HÀNG*\nVui lòng chọn loại sản phẩm bạn cần:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ *Hiện tại kho hàng của hệ thống đang tạm hết sản phẩm!*", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data.startswith("commit_checkout_"):
        acc_id = int(call.data.split("_")[2])
        
        # Đọc dữ liệu mới nhất ngay tại thời điểm thanh toán để chống lỗi trùng lặp dữ liệu
        db = read_db()
        product = next((acc for acc in db["accounts"] if acc["id"] == acc_id and acc["status"] == "ConHang"), None)
        
        if not product:
            bot.answer_callback_query(call.id, "❌ Tài khoản này đã được giao dịch thành công bởi một người dùng khác!", show_alert=True)
            return

        db = sync_user_data(db, uid_click)
        wallet_balance = int(db["users"][uid_click]["balance"])
        product_price = int(product["price"])
        
        if wallet_balance < product_price:
            bot.answer_callback_query(call.id, "❌ Tài khoản của bạn không đủ điều kiện thanh toán! Vui lòng nạp thêm tiền.", show_alert=True)
        else:
            # THỰC THI PHÉP TRỪ TIỀN VÀ TRỪ TRỰC TIẾP TRÊN FILE CỨNG
            db["users"][uid_click]["balance"] = wallet_balance - product_price
            db["users"][uid_click]["total_tieu"] += product_price
            db["users"][uid_click]["don_mua"] += 1
            product["status"] = "DaBan"
            
            if write_db(db):
                success_text = (
                    f"🎉 *XÁC NHẬN GIAO DỊCH THÀNH CÔNG*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 **Loại sản phẩm:** {product['name']}\n"
                    f"🆔 **Mã Số:** #{product['id']}\n"
                    f"💸 **Hệ thống khấu trừ:** -{product_price:,} VNĐ\n\n"
                    f"🔑 **THÔNG TIN DỮ LIỆU SẢN PHẨM:**\n"
                    f"`{product['info']}`\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ **Khuyến cáo:** Vui lòng đổi mật khẩu ngay lập tức để bảo mật tài sản."
                )
                bot.edit_message_text(success_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
                bot.answer_callback_query(call.id, "✅ Giao dịch hoàn tất!")
            else:
                bot.answer_callback_query(call.id, "❌ Lỗi hệ thống dữ liệu trục trặc, vui lòng thử lại.", show_alert=True)

    # --- ADMIN INLINE ROUTER ---
    elif call.data == "adm_add":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📝 Gửi thông tin nhập kho theo định dạng chuẩn:\n`Giá | Tên kho hàng | Thông tin tài khoản`")
        bot.register_next_step_handler(msg, process_admin_add_product)
        
    elif call.data == "adm_del":
        if not is_admin: return
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_item = False
        for acc in db["accounts"]:
            if acc["status"] == "ConHang":
                has_item = True
                markup.add(types.InlineKeyboardButton(f"❌ Xóa vĩnh viễn #{acc['id']} - [{acc['name']}]", callback_data=f"kill_sp_{acc['id']}"))
        if has_item:
            bot.send_message(call.message.chat.id, "🛠 Chọn mã sản phẩm cần thanh trừng khỏi Database:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "📭 Hiện không có tài khoản sẵn có để xóa.")
            
    elif call.data.startswith("kill_sp_"):
        if not is_admin: return
        target_id = int(call.data.split("_")[2])
        db["accounts"] = [a for a in db["accounts"] if a["id"] != target_id]
        write_db(db)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, f"🗑 Đã loại bỏ hoàn toàn mã sản phẩm #{target_id} khỏi hệ thống.")
        
    elif call.data == "adm_plus":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "💵 Cấu trúc cộng số dư khách hàng:\n`ID Khách | Số tiền cộng | Ghi chú lý do`")
        bot.register_next_step_handler(msg, process_admin_deposit)
        
    elif call.data == "adm_minus":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "💸 Cấu trúc khấu trừ số dư khách hàng:\n`ID Khách | Số tiền trừ | Ghi chú lý do`")
        bot.register_next_step_handler(msg, process_admin_withdraw)
        
    elif call.data == "adm_checkall":
        if not is_admin: return
        users_list = db.get("users", {})
        report_text = "📊 *BẢNG THỐNG KÊ TOÀN BỘ KHÁCH HÀNG SHOP*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        index_num = 1
        for u_id, info in users_list.items():
            if u_id == str(ADMIN_ID): continue
            report_text += f"{index_num}. ID: `{u_id}` ➜ *{info.get('balance', 0):,}đ* (Tổng nạp: {info.get('total_nap', 0):,}đ)\n"
            index_num += 1
        if index_num == 1:
            report_text += "Hệ thống hiện tại chưa ghi nhận dữ liệu người dùng."
        bot.send_message(call.message.chat.id, report_text, parse_mode="Markdown")
        
    elif call.data == "adm_bc":
        if not is_admin: return
        msg = bot.send_message(call.message.chat.id, "📢 Nhập nội dung văn bản muốn phát sóng diện rộng tới toàn thành viên:")
        bot.register_next_step_handler(msg, process_admin_broadcast)
        
    bot.answer_callback_query(call.id)

def run_web_gateway():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    init_db()
    try: bot.remove_webhook()
    except: pass
    
    # Khởi động Web Gateway trên tiến trình chạy ngầm độc lập
    gateway_thread = Thread(target=run_web_gateway)
    gateway_thread.daemon = True
    gateway_thread.start()
    
    logging.info("Bot Telegram đã bắt đầu Polling an toàn...")
    bot.infinity_polling(skip_pending=True)
