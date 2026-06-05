import os
import asyncio
import random
import string
from datetime import datetime, timedelta
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from database import init_db, get_user_language, set_user_language
from products import PRODUCTS
import aiosqlite

load_dotenv()

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_PATH = "shop.db"
CLICK_NUMBER = "+998915311102"
PAYME_NUMBER = "+998915311102"

def gen_order_id():
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

def gen_promo_code():
    return "REF-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

TEXTS = {
    "uz": {
        "welcome": "🛍 Xush kelibsiz! Mahsulot tanlang:",
        "select_amount": "Miqdor tanlang:",
        "promo_ask": "Promo kod bormi? Kiriting yoki o'tkazib yuboring:",
        "skip": "⏭ O'tkazib yuborish",
        "select_payment": "To'lov usulini tanlang:",
        "order_created": "✅ Buyurtma qabul qilindi!\n\nBuyurtma ID: {order_id}\nMahsulot: {product}\nNarx: ${price}\n\nTo'lov amalga oshirilgach tasdiqlang.",
        "paid_confirm": "✅ To'lovni tasdiqladingiz. Admin tekshiradi.",
        "status_paid": "💰 To'lov qabul qilindi!\n\nBuyurtma: {order_id}",
        "status_delivered": "✅ Yetkazildi!\n\nBuyurtma: {order_id}",
        "status_cancelled": "❌ Bekor qilindi.\n\nBuyurtma: {order_id}",
        "no_orders": "Buyurtmalar yo'q.",
        "language_set": "🇺🇿 Til o'zbekchaga o'zgartirildi!",
    },
    "ru": {
        "welcome": "🛍 Добро пожаловать! Выберите товар:",
        "select_amount": "Выберите количество:",
        "promo_ask": "Есть промокод? Введите или пропустите:",
        "skip": "⏭ Пропустить",
        "select_payment": "Выберите способ оплаты:",
        "order_created": "✅ Заказ принят!\n\nID заказа: {order_id}\nТовар: {product}\nЦена: ${price}\n\nПосле оплаты нажмите подтвердить.",
        "paid_confirm": "✅ Вы подтвердили оплату. Ожидайте проверки.",
        "status_paid": "💰 Оплата получена!\n\nЗаказ: {order_id}",
        "status_delivered": "✅ Доставлено!\n\nЗаказ: {order_id}",
        "status_cancelled": "❌ Отменено.\n\nЗаказ: {order_id}",
        "no_orders": "Заказов нет.",
        "language_set": "🇷🇺 Язык изменён на русский!",
    }
}

class OrderState(StatesGroup):
    waiting_promo = State()
    waiting_payment_confirm = State()
    waiting_broadcast = State()
    waiting_message = State()
    waiting_note = State()
    waiting_language = State()
