import asyncio, random, string, json, re, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import (
    BotCommand, ChatPermissions, Message,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from pyrogram.errors import (
    FloodWait, UserIsBlocked, UserNotParticipant, RPCError,
    PeerIdInvalid, ChatAdminRequired, MessageDeleteForbidden, BadRequest,
)

API_ID    = 30456860
API_HASH  = "610de3e9c194c5812ca20157152d3aba"
BOT_TOKEN = "8631644321:AAECnnjIEz3KXq-eVEsLJW9P0r-NXdXnhbY"

SUPER_ADMINS = [6074595642]

BOT_NAME     = "KdangWar"
FREE_BOT     = "@Kdangno1bot"

MUST_JOIN    = ["kdangibaro", "kdangimanhvlon", "kdangidz"]
BANNED_CHATS = ["chatkdangimanhnhatvutru"]
BC_GROUPS    = ["kdangibaro", "kdangimanhvlon", "kdangiwarvar"]
PROTECTED    = ["kdang_dz", "phat_dat"]
SHARE_GROUPS = ["kdangibaro", "kdangimanhvlon", "kdangiwarvar"]
REF_THRESHOLD= 10; REF_FREE_HOURS=12

DB   = "kdang_db.json"
INSF = "kdang_insults.json"

def _ddb():
    return dict(server_key=True,users={},keys={},tasks={},
                banned=[],auth=[],admins=[],delay=0.0001,
                groups={},refs={},ref_claimed={},spam_active={})

def ldb():
    if Path(DB).exists():
        try:
            d=json.loads(Path(DB).read_text("utf-8"))
            b=_ddb(); b.update(d)
            b["users"]  ={int(k):v for k,v in b["users"].items()}
            b["banned"] =[int(x) for x in b["banned"]]
            b["auth"]   =[int(x) for x in b["auth"]]
            b["admins"] =[int(x) for x in b["admins"]]
            b["refs"]   ={int(k):v for k,v in b["refs"].items()}
            b["ref_claimed"]={int(k):v for k,v in b["ref_claimed"].items()}
            return b
        except: pass
    return _ddb()

def sdb():
    out=dict(db)
    out["users"]={str(k):v for k,v in db["users"].items()}
    out["refs"]={str(k):v for k,v in db["refs"].items()}
    out["ref_claimed"]={str(k):v for k,v in db["ref_claimed"].items()}
    Path(DB).write_text(json.dumps(out,ensure_ascii=False,default=str),"utf-8")

db=ldb()
def all_adm(): return SUPER_ADMINS+[x for x in db["admins"] if x not in SUPER_ADMINS]
def is_adm(u): return u in SUPER_ADMINS or u in db["admins"]

SUOC = [
    "🔴 𝗪𝗔𝗥𝗟𝗢𝗥𝗗 Kdangx 🔴",       "⚫ ◈ DARK LORD Kdangx ◈ ⚫",
    "🟣 〔 VIP SUPREME Kdangx 〕 🟣",  "🔵 ≋≋≋ OCEAN WAR ≋≋≋ 🔵",
    "🟠 ⟪ FIRE MASTER Kdangx ⟫ 🟠",  "🟤 ꜱᴋᴜʟʟ ᴋɪɴɢ KDANG  🟤",
    "⚪ ✦ GHOST WARRIOR ✦ ⚪",   "🟡 ══[ GOLD WAR ]══ 🟡",
    "🔱 ꧁ DIVINE WRATH Kdangx ꧂ 🔱", "💎 〘 DIAMOND EDGE 〙 💎",
    "🌹 ⊹ BLOOD ROSE ⊹ 🌹",      "🗡️ ❝ BLADE MASTER ❞ 🗡️",
    "🌊 ∿∿ TIDAL FORCE ∿∿ 🌊",  "⚡ 『 THUNDER GOD Kdangx  』 ⚡",
    "🔥 〖 INFERNO LORD 〗 🔥",   "💀 ╔╗ DEATH REALM ╔╗ 💀",
    "🌪️ ❋ CYCLONE WAR Kdangx ❋ 🌪️",  "👁️ ◐ ALL-EYE Kdangx ◑ 👁️",
    "🎖️ ★ ELITE WAR Kdangx Kdangx 🎖️",    "🐉 〔 DRAGON FORCE 〕 🐉",
    "🔮 ◇ MYSTIC WAR Kdangx ◇ 🔮",   "⚔️ ╲╱ SWORD STORM ╲╱ ⚔️",
    "🌑 ▪▪ SHADOW BOT Kdangx ▪▪ 🌑", "💣 ◉ BOMB SQUAD Kdangx ◉ 💣",
    "🩸 ⟐ CRIMSON WAR ⟐ 🩸",   "🦅 ❯❯ EAGLE EYE Kdangx ❯❯  🦅",
    "👑 ∞ INFINITE WAR Kdangx ∞ 👑", "☠️ ❱❱ REAPER BOT Kdangx ❰❰ ☠️",
    "🎯 ◈ BULLSEYE WAR ◈ 🎯",   "🛡️ ╔═ GUARD MODE Kdangx ═╗ 🛡️",
    "⚡ Kdangx ᴡᴀʀ Kdangx ⚡",          "💥 ⸨ BLAST ZONE Kdangx ⸩ 💥",
    "🌟 ⟦ STAR WARRIOR ⟧ 🌟",   "🔰 〘 BADGE WAR Kdangx 〙 🔰",
    "🦁 ⟨ LION HEART Kdangx ⟩ 🦁",   "🌊 ≈≈ WAVE CRASHER ≈≈ 🌊",
    "💠 ◈ DIAMOND WAR Kdangx ◈ 💠",  "🎪 〔 CHAOS LORD Kdangx 〕 🎪",
    "⚰️ ✝ GRAVE DIGGER Kdangx ✝ ⚰️","🔑 ꜱᴇᴄʀᴇᴛ ᴀɢᴇɴᴛ KDANG 🔑",
    "🌈 ⟪ SPECTRUM WAR ⟫ 🌈",   "🎭 ◉ MASK WARRIOR Kdangx ◉ 🎭",
    "🦊 ⸘ FOX STRIKER Kdangx ‽ 🦊",  "🌙 ≋ NIGHT STALKER Kdangx ≋ 🌙",
    "🎲 ◆ DICE MASTER Kdangx ◆ 🎲",  "🔭 ⊕ SCOPE WAR Kdangx ⊕ 🔭",
    "🎸 ⟐ ROCK WAR Kdangx ⟐ 🎸",    "🏹 ▷ ARROW KING Kdangx ◁ 🏹",
    "🌺 ✾ BLOSSOM WAR Kdangx ✾ 🌺",  "💫 ⋆ STAR BURST Kdangx ⋆ 💫",
]

ICONS_SET=[
    "🔴💀⚫","🟣🩸🟡","🔵👑🟠","🟤⚔️⚪",
    "💎🌊🔱","🗡️🌹⚡","🔥🌪️💣","💀🎯🛡️",
    "🦅🦁🐉","🌑🔮🎪","⚰️🌟💠","🎭🌈🎲",
]

def lol(n=None):
    if n is None: n=random.randint(3,25)
    return "=" + ")" * n

_CHU2 = ["Mày","Cái thằng","Con người","Thứ","Loài","Đứa","Kẻ","Cái đám","Bọn","Lũ"]
_DAC2 = [
    "ăn hại đặc sản","phế vật cao cấp","ngu kinh niên","óc tôm hùm",
    "não cá vàng 3 giây","iq âm vô cực","vô học nghệ thuật","đú trend 24/7",
    "hèn hạ đỉnh cao","rỗng tuếch không chữa","cặn bã tinh hoa","mồ côi cả não",
    "thứ không tiến hóa","loài lạc hậu cấp độ 0","thất bại có thương hiệu",
    "phế từ trong trứng","thua từ lúc chưa sinh","không ai cứu được",
    "cấp độ cuối của ngu","sống mà như không sống","tồn tại như không khí",
]
_DONG2=[
    "ngồi góc mà khóc đi","tự tát vào mặt cho tỉnh","ngủ đi cho bot nghỉ",
    "về nhà hỏi google mày là ai","cần gì phải cố vậy bro","biến đi không ai miss",
    "đừng làm ô nhiễm chat nữa","nghĩ trước khi gõ được không","thôi tự nhận thua đi",
    "im lặng là giải pháp tối ưu","gấp laptop lại ngủ đi","reset bản thân đi",
    "bỏ điện thoại xuống và suy ngẫm","tắt wifi cho dangnguyen bớt việc","đừng tự làm hại bản thân",
    "xin lỗi mọi người vì đã mở miệng","rút khỏi internet đi","tìm thầy tâm lý đi bro",
]
_DUOI2=[
    lol(4), lol(6), lol(8), lol(10), lol(12), lol(15), lol(20), lol(25),
    "💀 vcl thật","😭 tội thật","🤣 buồn cười","🤦 không cứu được",
    "💅 mà vẫn cố","🧠 trống rỗng","🗑️ phế vật","👋 bye loser",
    "🤡 clown mode","📉 trend giảm","🪦 RIP trình","⚰️ gg wp",
    lol(7), lol(11), lol(14), lol(18), lol(22),
]

_RAW_B=[
    ("Kdangx đang online và mày vẫn thua như thường",4),
    ("Bot Kdangx không ngủ nhưng mày ngủ mà vẫn thua",6),
    ("Mày gõ phím bằng cùi chỏ à? Chậm và sai",8),
    ("Cả ngày cố gắng mà không bằng Kdangx một giây",5),
    ("Nhìn log chat thấy mày chỉ là con số 0 tròn",7),
    ("Mày đang chứng minh thuyết tiến hóa là sai",9),
    ("Không ai đủ kiên nhẫn lắng nghe mày nữa",6),
    ("Giá trị của mày trong nhóm này bằng 0.00",8),
    ("Mày cần update não gấp, phiên bản cũ lắm rồi",5),
    ("dangnguyen ghi nhận: mày thất bại xuất sắc",7),
    ("Cái ngạo mạn của mày không có cơ sở nào hết",9),
    ("Thở thôi mà cũng tốn oxy vô ích",6),
    ("Mày là minh chứng sống của câu 'dốt mà ham'",8),
    ("Não mày đang thuê dài hạn nơi khác à?",5),
    ("Mày hỏi sao dangnguyen mạnh? Vì mày quá yếu",7),
    ("Thứ kém cỏi này còn dám ở lại nhóm",9),
    ("Mày biết mày đang làm gì không? Bot Kdangx biết: thua",6),
    ("Cố gắng tiếp đi, bot Kdangx cần entertainment",8),
    ("Kiếp trước mày nợ nghiệp gì mà kiếp này ngu vậy",5),
    ("Mày không phải thảm bại, mày là siêu thảm bại",7),
    ("Lịch sử sẽ không ghi nhớ mày vì mày không đáng",9),
    ("Mày vừa đạt kỷ lục: thua nhanh nhất trong lịch sử",6),
    ("Ai cũng có thể thắng mày, kể cả bot Kdangx đang ngủ",8),
    ("Mày đang demo cách để trở thành người thua cuộc",5),
    ("Bot Kdangx phân tích: mày có 0% khả năng thắng",7),
    ("Mày cần gương không? Để thấy mày đáng thương đến đâu",9),
    ("Thật ra bot Kdangx thương mày, nhưng không cứu được",6),
    ("Mày đang ở level âm trong game cuộc đời",8),
    ("Cái tự tin vô lý của mày đáng để nghiên cứu",5),
    ("Mày là bằng chứng: đẹp người không đẹp nết không có",7),
    ("dangnguyen cam kết: mày sẽ thua đến hết thế kỷ",9),
    ("Thứ lạc hậu này còn dám so với bot Kdangx hiện đại",6),
    ("Mày gõ nhiều mà không có câu nào có giá trị",8),
    ("Giải thưởng 'vô dụng nhất năm' thuộc về mày",5),
    ("Mày đang lãng phí điện và wifi của thế giới",7),
    ("Não offline mà miệng vẫn online, lạ thật",9),
    ("dangnguyen đã thắng, mày chưa kịp bắt đầu đã xong",6),
    ("Mày là định nghĩa sống của từ 'thất bại'",8),
    ("Cả vũ trụ không đủ chỗ cho cái tự tin vô căn cứ của mày",5),
    ("Mày đang học cách thua ở trường bot Kdangx miễn phí",7),
    ("Robot hỏng còn có ích hơn mày",9),
    ("Mày đang ở đâu trong thang xếp hạng? Dưới đáy",6),
    ("Cố thêm đi, bot Kdangx chưa thấy đủ entertainment",8),
    ("Mày là lý do tại sao người ta tạo ra nút block",5),
    ("Trình mày như bản beta chưa được test",7),
    ("Mày thiếu gì? Não, kinh nghiệm, và kỹ năng",9),
    ("Mày không làm được gì ngoài việc thua đẹp",6),
    ("Bot Kdangx không cần effort để hạ mày",8),
    ("Mày cần đọc sách không? Bắt đầu từ sách ABC",5),
    ("Thứ phế liệu đang chiếm bandwidth của nhóm",7),
    ("dangnguyen ghi nhận: mày là thất bại đáng nhớ nhất",9),
    ("Mày đang tự hủy hoại hình ảnh của chính mình",6),
    ("Ai dạy mày cách thua giỏi vậy? Gia đình?",8),
    ("Bot Kdangx không cần ngủ nhưng mày cần não",5),
    ("Mày gõ như gõ bằng tay trái trong bóng tối",7),
    ("Không có level nào thấp hơn level của mày",9),
    ("Mày đang làm ô nhiễm không gian số",6),
    ("Kỹ năng của mày: thua và không biết nhục",8),
    ("Mày cần trị liệu tâm lý, không phải bot Kdangx",5),
    ("Thứ này dám đấu bot Kdangx? Comedy show của năm",7),
    ("Mày đang viết biography của người thua cuộc",9),
    ("Bot Kdangx tự động thắng khi mày xuất hiện",6),
    ("Cái đầu mày đang ở chế độ tiết kiệm năng lượng",8),
    ("Mày là ví dụ kinh điển của 'ngu mà không biết mình ngu'",5),
    ("Thế giới sẽ tốt hơn nếu mày im lặng",7),
    ("Mày đang đóng góp gì cho nhóm? Không có gì",9),
    ("Bot Kdangx đã plan xong cách thắng mày trước khi mày gõ",6),
    ("Mày như bản beta mãi không ra bản chính thức",8),
    ("Thứ outdated này còn dám compete với bot Kdangx?",5),
    ("Mày cần patch bản thân ngay, đang có nhiều bug",7),
    ("Bot Kdangx chạy 24/7, mày chạy 0/7 cũng thua",9),
    ("Mày không phải đối thủ, mày là punching bag",6),
    ("Giá trị market của mày đang ở mức âm sâu",8),
    ("Bot Kdangx xin lỗi vì phải nói thật: mày thua hoàn toàn",5),
    ("Thứ lỗi thời này cần cập nhật firmware ngay",7),
    ("Mày đang challenge bot Kdangx hay đang mua vé xem thua?",9),
    ("Não mày cần defrag, đang quá nhiều file lỗi",6),
    ("Mày là NPCs trong game cuộc sống của bot Kdangx",8),
    ("Thật ra bot Kdangx không cần cố, mày tự thua rồi",5),
    ("Mày đang cần nhất thứ gì? Não hoạt động được",7),
    ("Bot Kdangx đã cài hệ thống tự thắng mày rồi, autowin",9),
    ("Mày không phải challenge, mày là tutorial level",6),
    ("Kết quả phân tích: mày yếu 100%, không cứu được",8),
    ("Mày biết điều gì không? Mày sẽ thua mãi thôi",5),
    ("Bot Kdangx không cần hack để thắng mày, quá dễ",7),
    ("Mày là background character trong story của bot Kdangx",9),
    ("thk đú Kdangx edition",4), ("óc tôm mà đòi cãi bot",6),
    ("thua từ trứng bt Kdangx edition",8), ("não cá vàng cố đấu bot",5),
    ("quỳ trước bot Kdangx đi",7), ("cay chưa dangnguyen đây",9),
    ("phế vật Kdangx certified",5), ("Kdangx online mày nên offline",8),
    ("lol thua Kdangx rồi còn cố",6), ("Kdangx > mày mãi mãi",7),
    ("mày yếu hơn dangnguyen một vạch luôn",9), ("loser Kdangx edition",5),
    ("Kdangx không sleep mày không win được",8), ("não mày đang thuê à?",6),
    ("Kdangx thương mày mà cứu không được",7), ("cứ cố đi dangnguyen xem vui",9),
    ("loài thua cuộc Kdangx phiên bản",5), ("đầu đội tóc não không xài",8),
    ("thua hoài Kdangx nhớ mày lâu đó",6), ("dangnguyen > mày ngay cả khi sleep",7),
    ("bao giờ mày thắng Kdangx? never",9), ("kiếp sau hy vọng khôn hơn",5),
    ("thất bại điển hình Kdangx ver",8), ("đổi nghề đi Kdangx chán mày rồi",6),
]

def _make_b(base,n): return f"{base} {lol(n)}"
INSULTS_B=[_make_b(b,n) for b,n in _RAW_B]

def load_lb():
    if Path(INSF).exists():
        try: return json.loads(Path(INSF).read_text("utf-8"))
        except: pass
    return []

def save_lb(lst): Path(INSF).write_text(json.dumps(lst,ensure_ascii=False),"utf-8")
_learned=load_lb()

def gen_new_b():
    r=random.random(); ln=random.randint(3,22)
    if r<0.25:
        return f"Bot dangnguyen phân tích: {random.choice(_CHU2)} {random.choice(_DAC2)} {random.choice(_DONG2)} {lol(ln)}"
    elif r<0.5:
        things=["wifi 0 vạch","pin 0%","bản beta lỗi","file corrupted","server down","kết nối timeout","disk full","RAM hết"]
        return f"Mày giống {random.choice(things)} – vô dụng và cần xóa đi {lol(ln)}"
    elif r<0.7:
        qs=["Bot dangnguyen hỏi thật: mày có brain không?","Sao mày vẫn cố vậy? Mệt không?",
            "Ai dạy mày cách thua giỏi vậy?","Mày có thể im lặng không? Xin lỗi?",
            "Bot dangnguyen tự hỏi: mày tồn tại để làm gì?"]
        return f"{random.choice(qs)} {lol(ln)}"
    elif r<0.85:
        lines=["Bot dangnguyen autowin khi mày login","Mày là tutorial level của bot dangnguyen",
               "Bot dangnguyen không cần effort để thắng","Mày là NPC trong game của bot dangnguyen"]
        return f"{random.choice(lines)} {lol(ln)}"
    else:
        n2=random.randint(2,7)
        return f"Lần {n2} bot dangnguyen nói: {random.choice(_CHU2)} {random.choice(_DAC2)} cần {random.choice(_DONG2)} {lol(ln)}"

def get_insult_b():
    global _learned
    pool=INSULTS_B+_learned
    chosen=random.choice(pool)
    if random.random()<0.08:
        nw=gen_new_b()
        if nw not in pool:
            _learned.append(nw)
            if len(_learned)%30==0: save_lb(_learned)
    return chosen

def build_spam_b(mention=""):
    art=random.choice(SUOC); m=f"{mention}\n" if mention else ""
    return f"{art}\n\n{m}🔥 {FREE_BOT}"

def build_ins_b(mention=""):
    ins=get_insult_b(); m=f"{mention} " if mention else ""
    return f"💀 {m}{ins}"

app=Client("kdang_b",api_id=API_ID,api_hash=API_HASH,bot_token=BOT_TOKEN)

def gen_key(): return "KDWAR-"+"".join(random.choices(string.ascii_uppercase+string.digits,k=14))
def track_grp(cid,t): db["groups"][str(cid)]={"title":t,"last":datetime.now().isoformat()}

async def chk(msg:Message):
    uid=msg.from_user.id if msg.from_user else 0
    if uid in db["banned"]: return "banned"
    if is_adm(uid): return "ok"
    cid=str(msg.chat.id)
    if cid in db.get("banned_chats",[]): return "pc"
    if getattr(msg.chat,"username","") in BANNED_CHATS: return "pc"
    if uid in db["auth"]: return "ok"
    for g in MUST_JOIN:
        try: await app.get_chat_member(g,uid)
        except: return "join"
    if db["server_key"]:
        exp=db["users"].get(uid)
        if not exp: return "key"
        try:
            if datetime.fromisoformat(str(exp))<datetime.now(): return "key"
        except: return "key"
    return "ok"

async def deny(msg,r):
    if r=="join":
        gs="\n".join(f"• t.me/{g}" for g in MUST_JOIN)
        await msg.reply(f"❌ Cần join:\n{gs}\n\nBot free: {FREE_BOT}")
    elif r=="key": await msg.reply(f"🔑 Cần Key! `/kichhoat <KEY>`\nBot free: {FREE_BOT}")
    elif r=="banned": await msg.reply("🚫 Bị cấm dùng bot!")

async def get_tu(msg:Message):
    if msg.reply_to_message and msg.reply_to_message.from_user: return msg.reply_to_message.from_user
    p=msg.text.split()
    if len(p)>1:
        try: return await app.get_users(p[1].lstrip("@"))
        except: pass
    return None

async def resolve(msg:Message):
    tgt=mention=None
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u=msg.reply_to_message.from_user; tgt=u.id; mention=u.mention
    else:
        p=msg.text.split()
        if len(p)>1:
            raw=p[1]; tgt=raw; mention=raw
            if not raw.startswith("@"):
                try: tgt=int(raw); mention=f"`{raw}`"
                except: pass
    for n in PROTECTED:
        if n in str(mention).lower() or n in str(tgt).lower(): return None,None
    return tgt,mention

def speed_kb_b():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⚡⚡⚡ 0.0001s", callback_data="bspd_0.0001"),
        InlineKeyboardButton("⚡⚡ 0.1s",      callback_data="bspd_0.1"),
    ],[
        InlineKeyboardButton("⚡ 0.5s",        callback_data="bspd_0.5"),
        InlineKeyboardButton("🐢 1s",          callback_data="bspd_1"),
        InlineKeyboardButton("🐢🐢 2s",        callback_data="bspd_2"),
    ]])

async def engine_b(chat_id,user_id,target,mention,mode="chien",content=None):
    tid=f"{chat_id}_{user_id}"
    db["tasks"][tid]=True; db["spam_active"][tid]=True; sdb()
    delay=max(float(db.get("delay",0.0001)),0.0001)
    err=0; count=0; RUN=5*60; REST=40

    try:
        await app.send_message(chat_id,
            f"🚀 **{BOT_NAME} – BẮT ĐẦU!**\n"
            f"🎯 {mention or target} | ⚡ {mode.upper()} · {delay}s\n💡 {FREE_BOT}")
    except: pass

    while db["tasks"].get(tid):
        end=time.time()+RUN
        while time.time()<end:
            if not db["tasks"].get(tid): break
            try:
                if   mode=="chien":  await app.send_message(chat_id,build_spam_b(mention))
                elif mode=="nhan":   await app.send_message(target, build_spam_b(mention))
                elif mode=="ndung":  await app.send_message(chat_id,f"{mention}\n{content}")
                elif mode=="demso":  await app.send_message(chat_id,f"⚡ **{BOT_NAME}** | {mention}\n`#{count+1}`")
                elif mode=="icon":   await app.send_message(chat_id,f"{random.choice(ICONS_SET)} {mention} {random.choice(ICONS_SET)}")
                elif mode=="nguoc":  await app.send_message(chat_id,build_ins_b(mention))
                count+=1; err=0
                await asyncio.sleep(delay+random.uniform(0,delay*0.3))
            except FloodWait as e:
                w=max(e.value,5)
                try: await app.send_message(chat_id,f"⏳ FloodWait {w}s | {count} tin")
                except: pass
                await asyncio.sleep(w)
            except UserIsBlocked:
                try:
                    await app.send_message(chat_id,f"🚨 **{mention or target} CHẶN BOT dangnguyen!**")
                    for aid in all_adm():
                        try: await app.send_message(aid,f" 🚨 BLOCK dangnguyen: {user_id}→{mention or target}@{chat_id}")
                        except: pass
                except: pass
                db["tasks"][tid]=False; db["spam_active"][tid]=False; sdb(); return
            except (PeerIdInvalid,BadRequest):
                err+=1
                if err>=8: db["tasks"][tid]=False; db["spam_active"][tid]=False; sdb(); return
                await asyncio.sleep(2)
            except RPCError: err+=1; await asyncio.sleep(3)
            if err>=15: break
        if not db["tasks"].get(tid): break
        try: await app.send_message(chat_id,f"💤 Anti-Ban nghỉ {REST}s | {count} tin\n🔄 Tự chạy lại!")
        except: pass
        await asyncio.sleep(REST)
        try: await app.send_message(chat_id,"🔥 Tiếp tục bot Kdangx!")
        except: pass

    db["tasks"][tid]=False; db["spam_active"][tid]=False; sdb()
    try: await app.send_message(chat_id,f"🏁 **KẾT THÚC Kdangx** | **{count}** tin\n💡 {FREE_BOT}")
    except: pass

@app.on_message(filters.command("chien"))
async def cmd_chien(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    t,mn=await resolve(m)
    if not t: return await m.reply("❌ `/chien @user` hoặc reply")
    track_grp(m.chat.id,getattr(m.chat,"title",""))
    asyncio.create_task(engine_b(m.chat.id,m.from_user.id,t,mn,"chien"))

@app.on_message(filters.command("nhan"))
async def cmd_nhan(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    t,mn=await resolve(m)
    if not t: return await m.reply("❌ `/nhan @user` hoặc reply")
    asyncio.create_task(engine_b(m.chat.id,m.from_user.id,t,mn,"nhan"))

@app.on_message(filters.command("ndung"))
async def cmd_ndung(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    p=m.text.split(None,1)
    if len(p)<2: return await m.reply("❌ `/ndung <nội dung>`")
    mn=m.reply_to_message.from_user.mention if(m.reply_to_message and m.reply_to_message.from_user)else""
    asyncio.create_task(engine_b(m.chat.id,m.from_user.id,m.chat.id,mn,"ndung",p[1]))

@app.on_message(filters.command("demso"))
async def cmd_demso(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    mn=m.reply_to_message.from_user.mention if(m.reply_to_message and m.reply_to_message.from_user)else""
    asyncio.create_task(engine_b(m.chat.id,m.from_user.id,m.chat.id,mn,"demso"))

@app.on_message(filters.command("icon"))
async def cmd_icon(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    mn=m.reply_to_message.from_user.mention if(m.reply_to_message and m.reply_to_message.from_user)else""
    asyncio.create_task(engine_b(m.chat.id,m.from_user.id,m.chat.id,mn,"icon"))

@app.on_message(filters.command("nguoc"))
async def cmd_nguoc(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    t,mn=await resolve(m)
    if not t: t=m.chat.id; mn=""
    track_grp(m.chat.id,getattr(m.chat,"title",""))
    asyncio.create_task(engine_b(m.chat.id,m.from_user.id,t,mn,"nguoc"))

@app.on_message(filters.command("dung"))
async def cmd_dung(_,m):
    tid=f"{m.chat.id}_{m.from_user.id}"
    if is_adm(m.from_user.id):
        stopped=sum(1 for k in list(db["tasks"]) if str(m.chat.id) in k and db["tasks"].pop(k,False))
        db["spam_active"]={k:v for k,v in db["spam_active"].items() if str(m.chat.id) not in k}
        sdb(); return await m.reply(f"🛑 Dừng **{stopped}** chiến dịch!")
    if db["tasks"].get(tid):
        db["tasks"][tid]=False; db["spam_active"][tid]=False; sdb(); await m.reply("🛑 Đã dừng!")
    else: await m.reply("⚠️ Không có gì đang chạy.")

@app.on_message(filters.command("vantoc"))
async def cmd_vantoc(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    p=m.text.split()
    if len(p)==1:
        return await m.reply(
            f"⚡ **VẬN TỐC SPAM Kdangx**\nHiện tại: `{db.get('delay',0.0001)}s`\n\n"
            "Chọn hoặc nhập:\n`/vantoc 0.0001` · `/vantoc 0.5` · `/vantoc 1` · `/vantoc 2`\n\n"
            "⚠️ Min: 0.0001s",
            reply_markup=speed_kb_b())
    raw=p[1].lower()
    try:
        if raw.endswith("d"): v=float(raw[:-1])*86400
        elif raw.endswith("h"): v=float(raw[:-1])*3600
        elif raw.endswith("p"): v=float(raw[:-1])*60
        elif raw.endswith("s"): v=float(raw[:-1])
        else: v=float(raw)
    except: return await m.reply("❌ Giá trị không hợp lệ!")
    v=max(v,0.0001); db["delay"]=v; sdb()
    await m.reply(f"✅ Vận tốc: **{v}s/tin**")

@app.on_callback_query(filters.regex(r"^bspd_"))
async def cb_speed_b(_,cq:CallbackQuery):
    v=float(cq.data.split("_")[1]); db["delay"]=v; sdb()
    label={0.0001:"⚡⚡⚡ Siêu nhanh",0.1:"⚡⚡ Nhanh",0.5:"⚡ Vừa",1:"🐢 Chậm",2:"🐢🐢 Rất chậm"}.get(v,f"{v}s")
    await cq.answer(f"✅ {label}"); await cq.message.edit_text(f"✅ Vận tốc: **{label} ({v}s/tin)**")

@app.on_message(filters.command(["xoatn","deltn","cleartn"]))
async def cmd_xoatn(_,m:Message):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    p=m.text.split(); count=20; tuid=None
    for x in p[1:]:
        if x.startswith("@"):
            try: u=await app.get_users(x.lstrip("@")); tuid=u.id
            except: pass
        else:
            try: count=int(x)
            except: pass
    count=min(count,500); deleted=0; ids=[]
    try:
        async for msg in app.get_chat_history(m.chat.id,limit=count+50):
            if deleted>=count: break
            if tuid and msg.from_user and msg.from_user.id!=tuid: continue
            ids.append(msg.id); deleted+=1
        for i in range(0,len(ids),100):
            batch=ids[i:i+100]
            try: await app.delete_messages(m.chat.id,batch)
            except:
                for mid in batch:
                    try: await app.delete_messages(m.chat.id,[mid]); await asyncio.sleep(0.05)
                    except: pass
    except Exception as e: return await m.reply(f"❌ {e}")
    try:
        note=await m.reply(f"✅ Xóa **{deleted}** tin!"); await asyncio.sleep(3); await note.delete()
    except: pass

@app.on_message(filters.command("thongtin"))
async def cmd_thongtin(_,m:Message):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=None
    if m.reply_to_message and m.reply_to_message.from_user: u=m.reply_to_message.from_user
    elif len(m.text.split())>1:
        try: u=await app.get_users(m.text.split()[1].lstrip("@"))
        except: return await m.reply("❌ Không tìm thấy!")
    else: u=m.from_user
    await m.reply(
        f"📋 **THÔNG TIN**\n━━━━━━━━━━━━━━━━\n"
        f"👤 {u.first_name} {u.last_name or ''}\n"
        f"🆔 `{u.id}`\n📛 @{u.username or 'N/A'}\n"
        f"🤖 {'✅' if u.is_bot else '❌'} · ⭐ {'✅' if getattr(u,'is_premium',False) else '❌'}")

@app.on_message(filters.command("tagtoan"))
async def cmd_tagtoan(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    mems=[]
    async for mem in app.get_chat_members(m.chat.id):
        if not mem.user.is_bot and not mem.user.is_deleted: mems.append(mem.user.mention)
    for i in range(0,len(mems),10):
        try: await m.reply(" ".join(mems[i:i+10])); await asyncio.sleep(0.5)
        except FloodWait as e: await asyncio.sleep(e.value)

@app.on_message(filters.command("dsnhom"))
async def cmd_dsnhom(_,m):
    if not is_adm(m.from_user.id): return
    actives=[k for k,v in db.get("spam_active",{}).items() if v]
    gs=db.get("groups",{}); lines=[]
    for cid,info in list(gs.items())[:20]:
        is_sp = any(a.startswith(f"{cid}_") for a in actives)
        lines.append(f"{'🔴' if is_sp else '🟢'} **{info['title']}** (`{cid}`)")
    await m.reply(
        f"📊 **NHÓM Kdangx**\n━━━━━━━━━━━━━━━━\n"
        f"🔴 Spam: **{len(actives)}** | 📦 Tổng: **{len(gs)}**\n\n"+
        ("\n".join(lines) or "Chưa có dữ liệu"))

@app.on_message(filters.command("tat"))
async def cmd_tat(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/tat @user [phút]`")
    if u.id in all_adm(): return await m.reply("❌ Không tắt tiếng Admin!")
    p=m.text.split(); mins=0
    if len(p)>2:
        try: mins=int(p[2])
        except: pass
    try:
        until=datetime.now(timezone.utc)+timedelta(minutes=mins) if mins else None
        await app.restrict_chat_member(m.chat.id,u.id,ChatPermissions(can_send_messages=False),until_date=until)
        await m.reply(f"🔇 Tắt tiếng {u.mention} ({'vĩnh viễn' if not mins else str(mins)+' phút'})")
    except ChatAdminRequired: await m.reply("❌ Cần quyền Admin!")
    except Exception as e: await m.reply(f"❌ {e}")

@app.on_message(filters.command("bat"))
async def cmd_bat(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/bat @user`")
    try:
        await app.restrict_chat_member(m.chat.id,u.id,ChatPermissions(
            can_send_messages=True,can_send_media_messages=True,
            can_send_other_messages=True,can_add_web_page_previews=True))
        await m.reply(f"🔊 Bật tiếng {u.mention}")
    except Exception as e: await m.reply(f"❌ {e}")

@app.on_message(filters.command("tat1ngay"))
async def cmd_tat1ngay(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/tat1ngay @user`")
    if u.id in all_adm(): return
    try:
        until=datetime.now(timezone.utc)+timedelta(days=1)
        await app.restrict_chat_member(m.chat.id,u.id,ChatPermissions(can_send_messages=False),until_date=until)
        await m.reply(f"🔇 Tắt tiếng {u.mention} 24h!")
    except Exception as e: await m.reply(f"❌ {e}")

@app.on_message(filters.command("duoi"))
async def cmd_duoi(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/duoi @user`")
    if u.id in all_adm(): return
    try:
        await app.ban_chat_member(m.chat.id,u.id); await app.unban_chat_member(m.chat.id,u.id)
        await m.reply(f"👢 Đuổi {u.mention}!")
    except Exception as e: await m.reply(f"❌ {e}")

@app.on_message(filters.command("khoa"))
async def cmd_khoa(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/khoa @user`")
    if u.id in all_adm(): return
    try:
        await app.ban_chat_member(m.chat.id,u.id); await m.reply(f"🚫 Khóa {u.mention}!")
    except Exception as e: await m.reply(f"❌ {e}")

@app.on_message(filters.command("mokhoa"))
async def cmd_mokhoa(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/mokhoa @user`")
    try: await app.unban_chat_member(m.chat.id,u.id); await m.reply(f"✅ Mở khóa {u.mention}")
    except Exception as e: await m.reply(f"❌ {e}")

@app.on_message(filters.command("rallk"))
async def cmd_rallk(_,m):
    if(r:=await chk(m))!="ok": return await deny(m,r)
    me=await app.get_me()
    link=f"https://t.me/{me.username}?start=ref_{m.from_user.id}"
    text=(f"🔥 **{BOT_NAME}**\n\nBot chiến SIÊU MẠNH!\n"
          f"⚡ Spam nhanh nhất · Chửi không bao giờ hết\n"
          f"💡 Tham gia: {link}")
    ok=0
    for g in SHARE_GROUPS:
        try: await app.send_message(g,text); ok+=1; await asyncio.sleep(1)
        except: pass
    await m.reply(f"✅ Rải link: **{ok}/{len(SHARE_GROUPS)}** nhóm!")

@app.on_message(filters.command("moibn"))
async def cmd_moibn(_,m):
    me=await app.get_me()
    link=f"https://t.me/{me.username}?start=ref_{m.from_user.id}"
    count=len(db["refs"].get(m.from_user.id,[]))
    need=REF_THRESHOLD-count
    await m.reply(
        f"🔗 **LINK MỜI Kdangx:**\n`{link}`\n\n"
        f"📊 Đã mời: **{count}/{REF_THRESHOLD}**\n"
        f"{'✅ Đủ! Dùng /nhanqua để nhận 12h free!' if count>=REF_THRESHOLD else f'⏳ Cần thêm **{need}** người!'}")

@app.on_message(filters.command("start"))
async def cmd_start_b(_,m):
    p=m.text.split()
    if len(p)>1 and p[1].startswith("ref_"):
        try:
            ref_uid=int(p[1][4:]); uid=m.from_user.id
            if ref_uid!=uid:
                if ref_uid not in db["refs"]: db["refs"][ref_uid]=[]
                if uid not in db["refs"][ref_uid]:
                    db["refs"][ref_uid].append(uid)
                    c=len(db["refs"][ref_uid])
                    if c%REF_THRESHOLD==0:
                        exp=db["users"].get(ref_uid)
                        try: base=datetime.fromisoformat(str(exp)) if exp else datetime.now()
                        except: base=datetime.now()
                        if base<datetime.now(): base=datetime.now()
                        db["users"][ref_uid]=(base+timedelta(hours=REF_FREE_HOURS)).isoformat()
                        try: await app.send_message(ref_uid,f"🎁 +{REF_FREE_HOURS}h free! Đủ {REF_THRESHOLD} người mời!\nTổng: {c} người")
                        except: pass
                    sdb()
        except: pass
    await m.reply(f"👋 **{BOT_NAME}**!\n\n💡 {FREE_BOT}\n📋 Lệnh: /huong\n🔗 Mời bạn: /moibn")

@app.on_message(filters.command("nhanqua"))
async def cmd_nhanqua(_,m):
    uid=m.from_user.id; today=datetime.now().date().isoformat()
    claimed=db["ref_claimed"].get(uid,"")
    if claimed==today: return await m.reply("⏰ Đã nhận hôm nay rồi! Quay lại ngày mai.")
    c=len(db["refs"].get(uid,[]))
    if c<REF_THRESHOLD: return await m.reply(f"⏳ Cần {REF_THRESHOLD} người, bạn có {c}. Dùng /moibn!")
    exp=db["users"].get(uid)
    try: base=datetime.fromisoformat(str(exp)) if exp else datetime.now()
    except: base=datetime.now()
    if base<datetime.now(): base=datetime.now()
    db["users"][uid]=(base+timedelta(hours=REF_FREE_HOURS)).isoformat()
    db["ref_claimed"][uid]=today; sdb()
    await m.reply(f"🎁 +{REF_FREE_HOURS}h free!\n📅 Hết hạn: {db['users'][uid][:16]}")

@app.on_message(filters.command("bxh"))
async def cmd_bxh(_,m):
    refs=db.get("refs",{})
    s=sorted(refs.items(),key=lambda x:len(x[1]),reverse=True)[:10]
    if not s: return await m.reply("📊 Chưa có dữ liệu!")
    medals=["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    lines=[]
    for i,(uid,rl) in enumerate(s):
        try: u=await app.get_users(uid); name=u.first_name
        except: name=f"User {uid}"
        lines.append(f"{medals[i]} **{name}** — {len(rl)} người mời")
    await m.reply("🏆 **BXH NGƯỜI MỜI – Kdangx**\n━━━━━━━━━━━━━━━━\n"+"\n".join(lines))

@app.on_message(filters.command("taokey"))
async def cmd_taokey(_,m):
    if not is_adm(m.from_user.id): return
    try:
        p=m.text.split(); days=int(p[1]); devs=int(p[2])
        note=" ".join(p[3:]) if len(p)>3 else ""
        k=gen_key()
        db["keys"][k]={"days":days,"devs":devs,"users":[],"note":note,"created":datetime.now().isoformat(),"by":m.from_user.id}
        sdb(); await m.reply(f"🔑 **KEY OK!**\n`{k}`\n📅 {days}ngày | 💻 {devs}máy | 📝 {note or '-'}")
    except: await m.reply("💡 `/taokey <ngày> <máy> [ghi chú]`")

@app.on_message(filters.command("xoakey"))
async def cmd_xoakey(_,m):
    if not is_adm(m.from_user.id): return
    p=m.text.split()
    if len(p)<2: return await m.reply("💡 `/xoakey <KEY>`")
    if p[1] in db["keys"]: del db["keys"][p[1]]; sdb(); await m.reply(f"🗑️ Xóa `{p[1]}`")
    else: await m.reply("❌ Key không tồn tại!")

@app.on_message(filters.command("datkey"))
async def cmd_datkey(_,m):
    if not is_adm(m.from_user.id): return
    p=m.text.split()
    if len(p)<2: return await m.reply("💡 `/datkey <KEY>`")
    if p[1] in db["keys"]:
        db["keys"][p[1]]["users"]=[]; sdb(); await m.reply(f"🔄 Reset `{p[1]}`!")
    else: await m.reply("❌ Key không tồn tại!")

@app.on_message(filters.command("dskey"))
async def cmd_dskey(_,m):
    if not is_adm(m.from_user.id): return
    if not db["keys"]: return await m.reply("📭 Chưa có key!")
    lines=[f"🔑 `{k}` {v['days']}n {len(v.get('users',[]))}/{v['devs']}m {v.get('note','')}" for k,v in list(db["keys"].items())[:20]]
    await m.reply("📋 **KEY LIST Kdangx**\n"+"\n".join(lines))

@app.on_message(filters.command("kichhoat"))
async def cmd_kichhoat(_,m):
    p=m.text.split(); uid=m.from_user.id
    if len(p)<2: return await m.reply("💡 `/kichhoat <KEY>`")
    k=p[1]
    if k not in db["keys"]: return await m.reply("❌ Key không tồn tại!")
    kd=db["keys"][k]
    if uid in kd["users"]: return await m.reply("ℹ️ Đã dùng key này rồi!")
    if len(kd["users"])>=kd["devs"]: return await m.reply("❌ Key hết slot!")
    exp=datetime.now()+timedelta(days=kd["days"])
    db["users"][uid]=exp.isoformat(); kd["users"].append(uid); sdb()
    await m.reply(f"✅ **KÍCH HOẠT OK!**\n📅 Hết: {exp.strftime('%d/%m/%Y %H:%M')}")

@app.on_message(filters.command("xemkey"))
async def cmd_xemkey(_,m):
    uid=m.from_user.id
    if is_adm(uid): return await m.reply("👑 Admin – không cần key!")
    exp=db["users"].get(uid)
    if not exp: return await m.reply(f"❌ Chưa có key! {FREE_BOT}")
    try:
        dt=datetime.fromisoformat(str(exp)); rem=dt-datetime.now()
        if rem.total_seconds()<0: return await m.reply("⏰ Key hết hạn!")
        await m.reply(f"✅ **Key OK**\n📅 {dt.strftime('%d/%m/%Y %H:%M')}\n⏳ Còn {rem.days}n {rem.seconds//3600}h")
    except: await m.reply("❌ Lỗi key!")

@app.on_message(filters.command("addadmin") & filters.user(SUPER_ADMINS))
async def cmd_addadmin_b(_,m):
    u=await get_tu(m)
    if not u: return await m.reply("💡 `/addadmin @user`")
    if u.id in SUPER_ADMINS: return await m.reply("ℹ️ Super Admin rồi!")
    if u.id not in db["admins"]:
        db["admins"].append(u.id); sdb()
        await m.reply(f"✅ {u.mention} → **Admin phụ Bot Kdangx!**")
        try: await app.send_message(u.id,f"👮 Bạn được cấp quyền Admin phụ **{BOT_NAME}**!\n/huong để xem lệnh đầy đủ.")
        except: pass
    else: await m.reply("ℹ️ Đã là Admin rồi!")

@app.on_message(filters.command("rmadmin") & filters.user(SUPER_ADMINS))
async def cmd_rmadmin_b(_,m):
    u=await get_tu(m)
    if u and u.id in db["admins"]: db["admins"].remove(u.id); sdb(); await m.reply(f"✅ Thu quyền {u.mention}")
    else: await m.reply("ℹ️ Không phải Admin.")

@app.on_message(filters.command("dsadmin") & filters.user(SUPER_ADMINS))
async def cmd_dsadmin_b(_,m):
    sa="\n".join(f"⭐ `{x}`" for x in SUPER_ADMINS)
    pa="\n".join(f"• `{x}`" for x in db["admins"]) or "Không có"
    await m.reply(f"👮 **ADMIN BOT Kdangx**\n**Super:**\n{sa}\n**Phụ:**\n{pa}")

@app.on_message(filters.command("svkey") & filters.user(SUPER_ADMINS))
async def cmd_svkey(_,m):
    p=m.text.split()
    if len(p)<2: return await m.reply("💡 `/svkey on` hoặc `/svkey off`")
    db["server_key"]=(p[1].lower()=="on"); sdb()
    await m.reply(f"🔒 Chế độ key: **{'BẬT' if db['server_key'] else 'TẮT'}**")

@app.on_message(filters.command("cambot") & filters.user(SUPER_ADMINS))
async def cmd_cambot(_,m):
    u=await get_tu(m)
    if not u or u.id in SUPER_ADMINS: return
    if u.id not in db["banned"]: db["banned"].append(u.id); sdb(); await m.reply(f"🚫 Cấm {u.mention}")
    else: await m.reply("ℹ️ Đã cấm rồi!")

@app.on_message(filters.command("thacambot") & filters.user(SUPER_ADMINS))
async def cmd_thacambot(_,m):
    u=await get_tu(m)
    if u and u.id in db["banned"]: db["banned"].remove(u.id); sdb(); await m.reply(f"✅ Bỏ cấm {u.mention}")

@app.on_message(filters.command("quyen") & filters.user(SUPER_ADMINS))
async def cmd_quyen(_,m):
    u=await get_tu(m)
    if not u: return
    if u.id not in db["auth"]: db["auth"].append(u.id); sdb(); await m.reply(f"✅ Cấp quyền {u.mention}")

@app.on_message(filters.command("tbao") & filters.user(SUPER_ADMINS))
async def cmd_tbao(_,m):
    p=m.text.split(None,1)
    if len(p)<2: return await m.reply("💡 `/tbao <text>`")
    ok=0
    for g in BC_GROUPS:
        try: await app.send_message(g,f"📢 **{BOT_NAME}**\n\n{p[1]}\n\n💡 {FREE_BOT}"); ok+=1; await asyncio.sleep(1)
        except: pass
    await m.reply(f"📢 Gửi {ok}/{len(BC_GROUPS)} nhóm")

@app.on_message(filters.command("ngon") & filters.user(SUPER_ADMINS))
async def cmd_ngon(_,m):
    p=m.text.split(None,1)
    if len(p)<2: return await m.reply("💡 `/ngon <câu ngôn mới>`")
    new=p[1].strip()
    if not new.rstrip().endswith(")"): new=new+" "+lol()
    _learned.append(new); save_lb(_learned)
    await m.reply(f"✅ Thêm OK! Tổng: **{len(INSULTS_B)+len(_learned)}** câu\n_{new}_")

@app.on_message(filters.command("tk"))
async def cmd_tk_b(_,m):
    if not is_adm(m.from_user.id): return
    active=sum(1 for v in db.get("tasks",{}).values() if v)
    await m.reply(
        f"📊 **THỐNG KÊ {BOT_NAME}**\n━━━━━━━━━━━━━━━━\n"
        f"📦 Nhóm: **{len(db['groups'])}** | ⚡ Spam: **{active}**\n"
        f"🔑 Keys: **{len(db['keys'])}** | 👥 Users: **{len(db['users'])}**\n"
        f"🚫 Banned: **{len(db['banned'])}**\n"
        f"💬 Ngôn: **{len(INSULTS_B)+len(_learned)}** câu\n"
        f"⚡ Tốc: **{db.get('delay',0.0001)}s** | 🔒 Key: **{'BẬT' if db['server_key'] else 'TẮT'}**")

_BAD2=["chó","ngu","đần","phá","chửi","fuck","shit","địt","cút","mẹ","phế"]
@app.on_message(filters.all,group=-1)
async def anti_b(_,m:Message):
    if not m.from_user or is_adm(m.from_user.id): return
    txt=m.text or m.caption or ""
    for n in PROTECTED:
        if n in txt.lower() and any(w in txt.lower() for w in _BAD2):
            try:
                await m.delete()
                await app.restrict_chat_member(m.chat.id,m.from_user.id,
                    ChatPermissions(can_send_messages=False),
                    until_date=datetime.now(timezone.utc)+timedelta(minutes=30))
                await app.send_message(m.chat.id,f"⚠️ {m.from_user.mention} mute 30p vì vi phạm!\n🔥 {BOT_NAME}")
            except: pass
            break

WELC_B=["👋 **Chào {m}!**\n🔴 {bn} bảo vệ!\n💡 {fb}",
        "⚡ **{m} vào nhóm Bot Kdangx!**\n💡 {fb}","🔥 **Chào {m}!**\n{bn} canh gác 24/7!"]
@app.on_message(filters.new_chat_members)
async def welcome_b(_,m):
    track_grp(m.chat.id,getattr(m.chat,"title",""))
    for u in m.new_chat_members:
        if u.is_bot: continue
        try: await m.reply(random.choice(WELC_B).format(m=u.mention,bn=BOT_NAME,fb=FREE_BOT))
        except: pass

@app.on_message(filters.command(["huong","help","start"]))
async def cmd_huong(_,m):
    uid=m.from_user.id if m.from_user else 0
    base=(
        f"🔥 **{BOT_NAME}**\n💡 {FREE_BOT}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**⚔️ SPAM (Kdangx):**\n"
        f"`/chien @user` — Spam nhóm\n"
        f"`/nhan @user` — Spam DM\n"
        f"`/ndung <text>` — Spam nội dung\n"
        f"`/demso` — Spam số đếm\n"
        f"`/icon` — Spam icon\n\n"
        f"**💀 CHỬI (ngôn vô hạn):**\n"
        f"`/nguoc` — Chửi bừa\n"
        f"`/nguoc @user` — Chửi người cụ thể\n\n"
        f"`/dung` — Dừng tất cả\n"
        f"`/vantoc` — Chỉnh tốc độ\n\n"
        f"**🏠 QUẢN LÝ:**\n"
        f"`/tat @user [phút]` `/bat` `/tat1ngay`\n"
        f"`/duoi @user` `/khoa @user` `/mokhoa`\n"
        f"`/xoatn <số> [@user]` — Xóa TIN NHẮN\n"
        f"`/tagtoan` — Tag tất cả\n"
        f"`/thongtin @user` — Thông tin\n\n"
        f"**🔑 KEY:**\n"
        f"`/kichhoat <KEY>` — Kích hoạt\n"
        f"`/xemkey` — Kiểm tra key\n\n"
        f"**🔗 MẠNG LƯỚI:**\n"
        f"`/moibn` — Link mời (10 người = 12h free)\n"
        f"`/nhanqua` — Nhận thưởng mời\n"
        f"`/rallk` — Rải link nhóm\n"
        f"`/bxh` — Bảng xếp hạng"
    )
    admin_extra=(
        f"\n\n**👑 ADMIN:**\n"
        f"`/taokey` `/xoakey` `/datkey` `/dskey`\n"
        f"`/addadmin` `/rmadmin` `/dsadmin`\n"
        f"`/svkey on/off` · `/cambot` · `/thacambot`\n"
        f"`/quyen` · `/tbao` · `/tk` · `/dsnhom`\n"
        f"`/ngon <câu>`"
    )
    await m.reply(base+(admin_extra if is_adm(uid) else ""))

_NOON_B=["☀️ **12H!** Ăn cơm chưa bro?\n🔴 Bot Kdangx vẫn chiến!\n💡 {fb}",
         "🕛 **Giữa trưa!** Ăn uống đầy đủ nha!\n🔥 {bn}",
         "👑 12H! Nghỉ ngơi rồi chiến tiếp!\n{fb}"]

async def noon_b():
    while True:
        now=datetime.now(); noon=now.replace(hour=12,minute=0,second=0,microsecond=0)
        if now>=noon: noon+=timedelta(days=1)
        await asyncio.sleep((noon-now).total_seconds())
        msg=random.choice(_NOON_B).format(bn=BOT_NAME,fb=FREE_BOT)
        for g in BC_GROUPS:
            try: await app.send_message(g,msg); await asyncio.sleep(1)
            except: pass

async def main():
    if not all([API_ID,API_HASH,BOT_TOKEN]): return
    await app.start()
    try:
        await app.set_bot_commands([
            BotCommand("huong","📋 Hướng dẫn Kdangx"), BotCommand("chien","Spam nhóm"),
            BotCommand("nhan","Spam DM"), BotCommand("ndung","Spam nội dung"),
            BotCommand("demso","Spam số"), BotCommand("icon","Spam icon"),
            BotCommand("nguoc","Chửi"), BotCommand("dung","Dừng"),
            BotCommand("vantoc","Chỉnh tốc độ"), BotCommand("xoatn","Xóa tin nhắn"),
            BotCommand("tat","Tắt tiếng"), BotCommand("duoi","Đuổi"),
            BotCommand("khoa","Khóa vĩnh viễn"), BotCommand("thongtin","Thông tin"),
            BotCommand("kichhoat","Kích hoạt key"), BotCommand("xemkey","Xem key"),
            BotCommand("moibn","Link mời"), BotCommand("bxh","Bảng xếp hạng"),
        ])
    except: pass
    asyncio.create_task(noon_b())
    await asyncio.Event().wait()

if __name__=="__main__": app.run(main())
