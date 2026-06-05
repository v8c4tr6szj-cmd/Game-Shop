import asyncio, logging, os, random, string
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiosqlite

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8474872902:AAGhhyeuBppkusI1pRMhq5kWXw6Lb9Lfrwg"
ADMIN_ID = 8605680300
CLICK_NUMBER = "+998915311102"
PAYME_NUMBER = "+998915311102"
DB_PATH = "shop.db"
router = Router()

PRODUCTS = {
    "pubg": {"name": "🎮 PUBG UC", "items": [
        {"id": "pubg_60", "name": "60 UC", "price": 1.0},
        {"id": "pubg_300", "name": "300 UC", "price": 4.5},
        {"id": "pubg_600", "name": "600 UC", "price": 9.0},
        {"id": "pubg_1800", "name": "1800 UC", "price": 25.0}]},
    "freefire": {"name": "💎 Free Fire Diamond", "items": [
        {"id": "ff_100", "name": "100 Diamond", "price": 1.0},
        {"id": "ff_310", "name": "310 Diamond", "price": 2.4},
        {"id": "ff_520", "name": "520 Diamond", "price": 4.0},
        {"id": "ff_1060", "name": "1060 Diamond", "price": 8.0}]},
    "roblox": {"name": "🟡 Roblox Robux", "items": [
        {"id": "roblox_400", "name": "400 Robux", "price": 5.0},
        {"id": "roblox_800", "name": "800 Robux", "price": 10.0},
        {"id": "roblox_1700", "name": "1700 Robux", "price": 20.0}]},
    "steam": {"name": "🎁 Steam Gift Card", "items": [
        {"id": "steam_5", "name": "$5 Steam", "price": 6.0},
        {"id": "steam_10", "name": "$10 Steam", "price": 11.0},
        {"id": "steam_20", "name": "$20 Steam", "price": 22.0}]},
    "mlbb": {"name": "💠 Mobile Legends", "items": [
        {"id": "mlbb_86", "name": "86 Diamond", "price": 1.5},
        {"id": "mlbb_172", "name": "172 Diamond", "price": 3.0},
        {"id": "mlbb_429", "name": "429 Diamond", "price": 7.0}]},
    "brawl": {"name": "💎 Brawl Stars", "items": [
        {"id": "brawl_30", "name": "30 Gems", "price": 2.0},
        {"id": "brawl_80", "name": "80 Gems", "price": 5.0},
        {"id": "brawl_170", "name": "170 Gems", "price": 10.0}]},
    "clash": {"name": "⚔️ Clash of Clans", "items": [
        {"id": "coc_80", "name": "80 Gems", "price": 1.0},
        {"id": "coc_500", "name": "500 Gems", "price": 5.0},
        {"id": "coc_1200", "name": "1200 Gems", "price": 10.0}]},
    "valorant": {"name": "🔫 Valorant VP", "items": [
        {"id": "val_475", "name": "475 VP", "price": 5.0},
        {"id": "val_1000", "name": "1000 VP", "price": 10.0},
        {"id": "val_2050", "name": "2050 VP", "price": 20.0}]},
    "fortnite": {"name": "🏆 Fortnite V-Bucks", "items": [
        {"id": "fn_1000", "name": "1000 V-Bucks", "price": 8.0},
        {"id": "fn_2800", "name": "2800 V-Bucks", "price": 20.0}]},
    "genshin": {"name": "✨ Genshin Impact", "items": [
        {"id": "gs_60", "name": "60 Crystals", "price": 1.0},
        {"id": "gs_300", "name": "300 Crystals", "price": 5.0},
        {"id": "gs_980", "name": "980 Crystals", "price": 15.0}]},
}

class OrderState(StatesGroup):
    waiting_promo = State()
    waiting_message = State()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY, user_id INTEGER, username TEXT, full_name TEXT,
            product_name TEXT, price REAL, final_price REAL, promo_code TEXT,
            status TEXT DEFAULT 'pending', note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY, discount INTEGER, max_uses INTEGER, used_count INTEGER DEFAULT 0)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER, referred_id INTEGER PRIMARY KEY, rewarded INTEGER DEFAULT 0)""")
        await db.commit()

def gen_order_id():
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def main_kb():
    buttons = [[InlineKeyboardButton(text=v["name"], callback_data=f"cat_{k}")] for k,v in PRODUCTS.items()]
    buttons.append([InlineKeyboardButton(text="📞 Support", callback_data="support")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def amounts_kb(key, items):
    buttons = [[InlineKeyboardButton(text=f"{i['name']} — ${i['price']}", callback_data=f"item_{key}_{i['id']}")] for i in items]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Click", callback_data=f"pay_click_{order_id}")],
        [InlineKeyboardButton(text="💳 Payme", callback_data=f"pay_payme_{order_id}")]])

def confirm_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lovni tasdiqlayman", callback_data=f"confirm_{order_id}")]])

def admin_kb(order_id, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Paid", callback_data=f"apaid_{order_id}_{user_id}")],
        [InlineKeyboardButton(text="✅ Delivered", callback_data=f"adeliv_{order_id}_{user_id}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"acancel_{order_id}_{user_id}")],
        [InlineKeyboardButton(text="💬 Message", callback_data=f"amsg_{user_id}")]])
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await init_db()
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Admin Panel\n\n/orders /pending /paid\n/addpromo /delpromo /promos\n/broadcast /stats /customers\n/search /export /dashboard", reply_markup=main_kb())
    else:
        await message.answer("🛍 Xush kelibsiz! Mahsulot tanlang:", reply_markup=main_kb())

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🛍 Mahsulot tanlang:", reply_markup=main_kb())

@router.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    await call.message.answer("📞 Support: @admin_username")

@router.callback_query(F.data.startswith("cat_"))
async def select_cat(call: CallbackQuery):
    key = call.data[4:]
    if key not in PRODUCTS:
        return
    await call.message.edit_text("Miqdor tanlang:", reply_markup=amounts_kb(key, PRODUCTS[key]["items"]))

@router.callback_query(F.data.startswith("item_"))
async def select_item(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_", 2)
    key, item_id = parts[1], parts[2]
    product = PRODUCTS.get(key)
    item = next((i for i in product["items"] if i["id"] == item_id), None)
    await state.update_data(product_name=f"{product['name']} {item['name']}", price=item["price"])
    await call.message.edit_text("Promo kod bormi? Yoki o'tkazib yuboring:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_promo")]]))
    await state.set_state(OrderState.waiting_promo)

@router.callback_query(F.data == "skip_promo")
async def skip_promo(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = gen_order_id()
    await state.update_data(order_id=order_id, final_price=data["price"], promo_code=None)
    await call.message.edit_text("To'lov usulini tanlang:", reply_markup=payment_kb(order_id))

@router.message(OrderState.waiting_promo)
async def check_promo(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT discount, max_uses, used_count FROM promo_codes WHERE code=?", (code,)) as c:
            row = await c.fetchone()
    if not row:
        await message.answer("❌ Noto'g'ri kod:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_promo")]]))
        return
    discount, max_uses, used_count = row
    if max_uses and used_count >= max_uses:
        await message.answer("❌ Kod tugagan.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_promo")]]))
        return
    final_price = round(data["price"] * (1 - discount/100), 2)
    order_id = gen_order_id()
    await state.update_data(order_id=order_id, promo_code=code, final_price=final_price)
    await message.answer(f"✅ {discount}% chegirma! Narx: ${data['price']} → ${final_price}", reply_markup=payment_kb(order_id))

@router.callback_query(F.data.startswith("pay_"))
async def select_payment(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    pay_type = parts[1]
    data = await state.get_data()
    number = CLICK_NUMBER if pay_type == "click" else PAYME_NUMBER
    order_id = data["order_id"]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO orders (id,user_id,username,full_name,product_name,price,final_price,promo_code) VALUES (?,?,?,?,?,?,?,?)",
            (order_id, call.from_user.id, call.from_user.username, call.from_user.full_name,
             data["product_name"], data["price"], data["final_price"], data.get("promo_code")))
        await db.commit()
    await call.message.edit_text(
        f"💳 {pay_type.capitalize()} orqali to'lang:\nRaqam: {number}\nSumma: ${data['final_price']}\nBuyurtma: {order_id}",
        reply_markup=confirm_kb(order_id))

@router.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(call: CallbackQuery, state: FSMContext, bot: Bot):
    order_id = call.data[8:]
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM orders WHERE id=?", (order_id,)) as c:
            order = await c.fetchone()
    if not order:
        return
    await call.message.edit_text("✅ To'lov tasdiqlandi! Admin tekshiradi.")
    await state.clear()
    await bot.send_message(ADMIN_ID,
        f"🆕 Yangi buyurtma!\nID: {order_id}\nMijoz: {call.from_user.full_name} (@{call.from_user.username})\nMahsulot: {order[4]}\nNarx: ${order[6]}",
        reply_markup=admin_kb(order_id, call.from_user.id))

@router.callback_query(F.data.startswith("apaid_"))
async def admin_paid(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id, user_id = parts[1], int(parts[2])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
        await db.commit()
    await bot.send_message(user_id, f"💰 To'lov qabul qilindi!\nBuyurtma: {order_id}")
    await call.answer("✅ Paid!")

@router.callback_query(F.data.startswith("adeliv_"))
async def admin_delivered(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id, user_id = parts[1], int(parts[2])
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT note FROM orders WHERE id=?", (order_id,)) as c:
            row = await c.fetchone()
        await db.execute("UPDATE orders SET status='delivered' WHERE id=?", (order_id,))
        await db.commit()
    text = f"✅ Yetkazildi!\nBuyurtma: {order_id}"
    if row and row[0]:
        text += f"\n\n📝 {row[0]}"
    await bot.send_message(user_id, text)
    await call.answer("✅ Delivered!")

@router.callback_query(F.data.startswith("acancel_"))
async def admin_cancel(call: CallbackQuery, bot: Bot):
    parts = call.data.split("_")
    order_id, user_id = parts[1], int(parts[2])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
        await db.commit()
    await bot.send_message(user_id, f"❌ Buyurtma bekor qilindi.\nBuyurtma: {order_id}")
    await call.answer("❌ Cancelled!")

@router.callback_query(F.data.startswith("amsg_"))
async def admin_msg(call: CallbackQuery, state: FSMContext):
    user_id = int(call.data[5:])
    await state.update_data(target_user=user_id)
    await call.message.answer("✏️ Xabar yozing:")
    await state.set_state(OrderState.waiting_message)

@router.message(OrderState.waiting_message)
async def send_msg(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        await bot.send_message(data["target_user"], f"📩 Support:\n\n{message.text}")
        await message.answer("✅ Yuborildi!")
    except:
        await message.answer("❌ Yuborib bo'lmadi!")
    await state.clear()
@router.message(Command("orders"))
async def cmd_orders(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, full_name, product_name, final_price, status FROM orders ORDER BY created_at DESC LIMIT 20") as c:
            rows = await c.fetchall()
    if not rows:
        await message.answer("Buyurtmalar yo'q.")
        return
    text = "📋 Buyurtmalar:\n\n"
    for r in rows:
        text += f"{'✅' if r[4]=='delivered' else '⏳' if r[4]=='pending' else '💰' if r[4]=='paid' else '❌'} {r[0]} — {r[2]} ${r[3]} ({r[1]})\n"
    await message.answer(text)

@router.message(Command("pending"))
async def cmd_pending(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, full_name, product_name, final_price FROM orders WHERE status='pending'") as c:
            rows = await c.fetchall()
    if not rows:
        await message.answer("Kutayotgan buyurtmalar yo'q.")
        return
    text = "⏳ Pending:\n\n"
    for r in rows:
        text += f"• {r[0]} — {r[2]} ${r[3]} ({r[1]})\n"
    await message.answer(text)

@router.message(Command("paid"))
async def cmd_paid(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, full_name, product_name, final_price FROM orders WHERE status='paid'") as c:
            rows = await c.fetchall()
    if not rows:
        await message.answer("To'langan buyurtmalar yo'q.")
        return
    text = "💰 Paid:\n\n"
    for r in rows:
        text += f"• {r[0]} — {r[2]} ${r[3]} ({r[1]})\n"
    await message.answer(text)

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*), SUM(final_price) FROM orders") as c:
            total = await c.fetchone()
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'") as c:
            pending = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status='delivered'") as c:
            delivered = (await c.fetchone())[0]
        async with db.execute("SELECT product_name, COUNT(*) as cnt FROM orders GROUP BY product_name ORDER BY cnt DESC LIMIT 5") as c:
            top = await c.fetchall()
    text = f"📊 Statistika:\n\nJami: {total[0]} buyurtma\nDaromad: ${total[1] or 0:.2f}\nKutayotgan: {pending}\nYetkazilgan: {delivered}\n\n🏆 Top mahsulotlar:\n"
    for i, r in enumerate(top, 1):
        text += f"{i}. {r[0]} — {r[1]} ta\n"
    await message.answer(text)

@router.message(Command("addpromo"))
async def cmd_addpromo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Format: /addpromo KOD CHEGIRMA [MAX_FOYDALANISH]")
        return
    code = parts[1].upper()
    discount = int(parts[2])
    max_uses = int(parts[3]) if len(parts) > 3 else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO promo_codes (code, discount, max_uses) VALUES (?,?,?)", (code, discount, max_uses))
        await db.commit()
    await message.answer(f"✅ Promo kod qo'shildi: {code} — {discount}%")

@router.message(Command("delpromo"))
async def cmd_delpromo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Format: /delpromo KOD")
        return
    code = parts[1].upper()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM promo_codes WHERE code=?", (code,))
        await db.commit()
    await message.answer(f"✅ {code} o'chirildi!")

@router.message(Command("promos"))
async def cmd_promos(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code, discount, max_uses, used_count FROM promo_codes") as c:
            rows = await c.fetchall()
    if not rows:
        await message.answer("Promo kodlar yo'q.")
        return
    text = "🎟 Promo kodlar:\n\n"
    for r in rows:
        uses = f"{r[3]}/{r[2]}" if r[2] else f"{r[3]}/∞"
        text += f"• {r[0]} — {r[1]}% ({uses} marta)\n"
    await message.answer(text)

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("📢 Yubormoqchi bo'lgan xabarni yozing:")

@router.message(Command("customers"))
async def cmd_customers(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT full_name, username, user_id, COUNT(*) as cnt, SUM(final_price) FROM orders GROUP BY user_id ORDER BY SUM(final_price) DESC LIMIT 25") as c:
            rows = await c.fetchall()
    if not rows:
        await message.answer("Mijozlar yo'q.")
        return
    text = "👥 Mijozlar:\n\n"
    for r in rows:
        text += f"• {r[0]} @{r[1]} — {r[3]} buyurtma, ${r[4]:.2f}\n"
    await message.answer(text)

@router.message(Command("dashboard"))
async def cmd_dashboard(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*), SUM(final_price) FROM orders WHERE date(created_at)=?", (today,)) as c:
            today_data = await c.fetchone()
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'") as c:
            pending = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status='delivered'") as c:
            delivered = (await c.fetchone())[0]
    text = f"📊 Dashboard — Bugun:\n\nBuyurtmalar: {today_data[0]}\nDaromad: ${today_data[1] or 0:.2f}\n\nPending: {pending}\nDelivered: {delivered}"
    await message.answer(text)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
