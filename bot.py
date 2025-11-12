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

# ---------- Firebase 初始化 ----------
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "storageBucket": "itsukibook-1001.firebasestorage.app"
    })
    db = firestore.client()
    logging.info("Firebase 初始化成功")
except Exception as e:
    logging.error(f"Firebase 初始化失敗: {e}")
    raise

# ---------- 快取管理 ----------
class ImageCache:
    """圖片快取管理器，提供執行緒安全的快取操作"""
    def __init__(self, ttl_seconds: int = 60):
        self.cache = []
        self.ttl = ttl_seconds
        self.last_fetch = 0.0
        self._lock = asyncio.Lock()

    def need_refresh(self) -> bool:
        """檢查是否需要重新載入快取"""
        import time
        return (time.time() - self.last_fetch) > self.ttl or not self.cache

    def _fetch_images(self) -> list:
        """同步獲取圖片資料（在執行緒池中執行）"""
        try:
            docs = db.collection("images").stream()
            images = []
            for doc in docs:
                data = doc.to_dict() or {}
                url = data.get("imageUrl")
                if url:
                    images.append({
                        "url": url,
                        "name": data.get("name", "未命名圖片"),
                        "text": data.get("text", "")
                    })
            logging.info(f"成功載入 {len(images)} 張圖片到快取")
            return images
        except Exception as e:
            logging.error(f"獲取圖片資料失敗: {e}")
            raise

    async def refresh(self):
        """非同步刷新快取"""
        async with self._lock:
            if not self.need_refresh():
                return

            loop = asyncio.get_running_loop()
            self.cache = await loop.run_in_executor(None, self._fetch_images)
            import time
            self.last_fetch = time.time()

    async def get_random(self):
        """獲取隨機圖片"""
        if self.need_refresh():
            await self.refresh()

        if not self.cache:
            logging.warning("快取中沒有圖片")
            return None

        return random.choice(self.cache)

# 全域快取實例
_image_cache = ImageCache(ttl_seconds=60)

async def get_random_image():
    """獲取隨機圖片（向後相容的接口）"""
    return await _image_cache.get_random()

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
    """發送隨機圖片到 Discord"""
    try:
        # 先告訴 Discord「我在處理」，避免 3 秒逾時
        await interaction.response.defer(thinking=True)

        img = await get_random_image()
        if not img:
            await interaction.followup.send("目前沒有圖片，請稍後再試。")
            logging.warning(f"用戶 {interaction.user} 請求圖片但快取為空")
            return

        embed = discord.Embed(
            title=img.get("name", "王月之書"),
            description=img.get("text", ""),
            color=discord.Color.purple()
        )
        embed.set_image(url=img["url"])
        await interaction.followup.send(embed=embed)
        logging.info(f"成功發送圖片給用戶 {interaction.user}: {img.get('name', 'Unknown')}")

    except Exception as e:
        logging.error(f"發送圖片時發生錯誤: {e}", exc_info=True)
        try:
            await interaction.followup.send(f"抱歉，發生了一些錯誤，請稍後再試。")
        except:
            pass


@client.tree.command(name="王月之書", description="今天的聖旨", guild=discord.Object(id=GUILD_ID))
async def itsuki_book(interaction: discord.Interaction):
    """王月之書指令：隨機抽取一張圖片"""
    await _send_random_image(interaction)


TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in environment variables")
client.run(TOKEN)