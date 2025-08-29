import asyncio
import random
import discord
from discord import app_commands
import logging
import os
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

# ---------- 環境變數 ----------
load_dotenv()
logging.basicConfig(level=logging.INFO)

# ---------- 指令同步設定 ----------
# SYNC_GLOBAL=1 則同步到全域；未設或為其他值時只同步到指定 Guild（秒生效）
SYNC_GLOBAL = os.getenv("SYNC_GLOBAL", "").strip() == "1"
# 從環境變數讀取 Guild ID（優先），否則用檔案裡的常數
ENV_GUILD_ID = os.getenv("GUILD_ID")

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
GUILD_ID = int(ENV_GUILD_ID) if ENV_GUILD_ID else 1366939723943383183  # ← 你的伺服器 ID

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        try:
            if SYNC_GLOBAL:
                logging.info("Syncing application commands: GLOBAL mode")
                # 先清除全域舊指令（例如舊的 /draw），再同步
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
            else:
                guild = discord.Object(id=GUILD_ID)
                logging.info(f"Syncing application commands to Guild {GUILD_ID}")
                await self.tree.sync(guild=guild)
                cmds = await self.tree.fetch_commands(guild=guild)
                logging.info(f"Guild {GUILD_ID} commands now: {[c.name for c in cmds]}")
        except discord.Forbidden as e:
            logging.error("Failed to sync commands (Forbidden: Missing Access). "
                          "請確認：1) Bot 已被邀請進入該伺服器；2) 邀請時包含 scope=applications.commands；3) GUILD_ID 正確。")
            # 可選：嘗試退回全域同步，避免完全不可用
            try:
                logging.info("Fallback: trying GLOBAL sync...")
                await self.tree.sync()
            except Exception:
                logging.exception("Fallback global sync also failed")
                raise
        except Exception:
            logging.exception("Unexpected error during command sync")
            raise

client = MyClient()


# Helper function to send a random image
async def _send_random_image(interaction: discord.Interaction):
    # 先告訴 Discord「我在處理」，避免 3 秒逾時
    await interaction.response.defer(thinking=True)

    img = await get_random_image()
    if not img:
        await interaction.followup.send("目前沒有圖片，請稍後再試。")
        return

    embed = discord.Embed()
    embed.set_image(url=img["url"])
    await interaction.followup.send(embed=embed)


@client.tree.command(name="王月之書", description="今天的聖旨", guild=discord.Object(id=GUILD_ID))
async def itsuki_book(interaction: discord.Interaction):
    try:
        await _send_random_image(interaction)
    except Exception as e:
        await interaction.followup.send(f"出錯了：{e}")


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")
client.run(TOKEN)