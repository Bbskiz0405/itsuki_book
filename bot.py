import asyncio
import random
import discord
from discord import app_commands
import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore, storage

# ---------- 環境變數 ----------
load_dotenv()

# ---------- Firebase ----------
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "storageBucket": "itsukibook-1001.firebasestorage.app"  # 依你的 bucket 調整
})
db = firestore.client()

# 簡單快取，避免每次都去抓整個 collection
IMAGES_CACHE = []
CACHE_TTL_SEC = 60  # 快取 60 秒
_last_fetch_ts = 0.0

def _need_refresh() -> bool:
    import time
    return (time.time() - _last_fetch_ts) > CACHE_TTL_SEC or not IMAGES_CACHE

def _refresh_images_cache():
    """同步抓資料（在工作執行緒跑），避免阻塞事件迴圈太久。"""
    global IMAGES_CACHE, _last_fetch_ts
    docs = db.collection("images").stream()
    IMAGES_CACHE = []
    for d in docs:
        data = d.to_dict() or {}
        url = data.get("imageUrl")
        if url:
            IMAGES_CACHE.append({
                "url": url,
                "name": data.get("name", "未命名圖片"),
                "text": data.get("text", "")
            })
    import time
    _last_fetch_ts = time.time()

async def get_random_image():
    # Firestore SDK 是同步 I/O，丟到執行緒池避免卡住事件迴圈
    if _need_refresh():
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _refresh_images_cache)

    if not IMAGES_CACHE:
        return None
    return random.choice(IMAGES_CACHE)

# ---------- Discord ----------
class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # 若只想同步到特定伺服器，可以改成：await self.tree.sync(guild=discord.Object(YOUR_GUILD_ID))
        await self.tree.sync()

client = MyClient()

@client.tree.command(name="draw", description="隨機抽一張玥之書的圖片")
async def draw(interaction: discord.Interaction):
    try:
        # 1) 先告訴 Discord「我在處理」，避免 3 秒逾時
        await interaction.response.defer(thinking=True)

        # 2) 取圖（可能要花 1~2 秒）
        img = await get_random_image()
        if not img:
            await interaction.followup.send("目前沒有圖片，請稍後再試。")
            return

        # 3) 回覆（使用 followup，而不是 response.send_message）
        embed = discord.Embed(title=img["name"], description=img["text"])
        embed.set_image(url=img["url"])
        await interaction.followup.send(embed=embed)

    except Exception as e:
        # 發生錯誤也要回一則訊息，這樣就不會吃到逾時
        await interaction.followup.send(f"出錯了：{e}")

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")
client.run(TOKEN)