import aiosqlite
import os

DB_PATH = "shop.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                product_id TEXT,
                product_name TEXT,
                amount TEXT,
                price REAL,
                final_price REAL,
                promo_code TEXT,
                status TEXT DEFAULT 'pending',
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timeout_notified_at TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                discount INTEGER,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER PRIMARY KEY,
                rewarded INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_languages (
                user_id INTEGER PRIMARY KEY,
                language TEXT DEFAULT 'ru'
            )
        """)
        await db.commit()

async def get_user_language(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT language FROM user_languages WHERE user_id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 'ru'

async def set_user_language(user_id, lang):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO user_languages (user_id, language) VALUES (?,?)", (user_id, lang))
        await db.commit()
