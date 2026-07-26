import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio
import json
import datetime
import re
import os
from typing import List, Optional

DB_FILE = "bot_database.db"

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            guild_id TEXT,
            key TEXT,
            value TEXT,
            PRIMARY KEY (guild_id, key)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            moderator_id TEXT,
            reason TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            moderator_id TEXT,
            action TEXT,
            reason TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS automod (
            guild_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 0,
            spam_enabled INTEGER DEFAULT 0,
            antinuke_enabled INTEGER DEFAULT 0,
            max_messages INTEGER DEFAULT 5,
            banned_words TEXT DEFAULT '[]'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            data TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            board_name TEXT,
            title TEXT DEFAULT 'Price Board',
            description TEXT DEFAULT '',
            color TEXT DEFAULT '2f3136',
            channel_id TEXT DEFAULT '0',
            message_id TEXT DEFAULT '0',
            UNIQUE(guild_id, board_name)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id TEXT,
            product_name TEXT,
            price TEXT,
            stock TEXT
        )
    """)
    conn.commit()
    conn.close()

def db_execute(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def db_fetch(query: str, params: tuple = ()) -> List:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_fetch_one(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()
    return row

class VerifyView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="Xác Minh", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message("Không tìm thấy role xác Minh.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("Bạn đã được xác minh.", ephemeral=True)
            return
        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Xác minh thành công.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Bot không có quyền cấp role.", ephemeral=True)

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="👥 Thành Viên", value="members", description="Quản lý thành viên"),
            discord.SelectOption(label="💬 Tin Nhắn", value="messages", description="Quản lý tin nhắn"),
            discord.SelectOption(label="🎭 Vai Trò & Biệt Danh", value="roles", description="Quản lý vai trò"),
            discord.SelectOption(label="📢 Máy Chủ", value="server", description="Thông báo và sự kiện"),
            discord.SelectOption(label="🛒 Bảng Giá", value="price", description="Quản lý bảng giá"),
            discord.SelectOption(label="📜 Nhật Ký", value="logs", description="Xem lịch sử và log"),
            discord.SelectOption(label="🤖 Hệ Thống", value="advanced", description="Automod và bảo mật"),
            discord.SelectOption(label="⚙️ Cài Đặt", value="config", description="Cấu hình bot"),
            discord.SelectOption(label="ℹ️ Khác", value="other", description="Lệnh tiện ích"),
        ]
        super().__init__(placeholder="Chọn danh mục...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = discord.Embed(color=discord.Color.blue())
        if category == "members":
            embed.title = "👥 Thành Viên"
            embed.description = """
            `/ban` Cấm thành viên
            `/kick` Trục xuất thành viên
            `/timeout` Cách ly thành viên
            `/untimeout` Hủy cách ly
            `/warn` Cảnh cáo thành viên
            `/unwarn` Xóa cảnh cáo
            `/clearwarn` Xóa toàn bộ cảnh cáo
            `/mute` Tắt tiếng
            `/unmute` Mở tiếng
            """
        elif category == "messages":
            embed.title = "💬 Tin Nhắn"
            embed.description = """
            `/clear` Xóa tin nhắn
            `/slowmode` Bật chế độ chậm
            `/lock` Khóa kênh
            `/unlock` Mở khóa kênh
            `/purgebot` Xóa tin nhắn bot
            """
        elif category == "roles":
            embed.title = "🎭 Vai Trò & Biệt Danh"
            embed.description = """
            `/role add` Thêm vai trò
            `/role remove` Xóa vai trò
            `/role create` Tạo vai trò
            `/role delete` Xóa vai trò
            `/nickname` Đổi biệt danh
            """
        elif category == "server":
            embed.title = "📢 Máy Chủ"
            embed.description = """
            `/announce` Gửi thông báo
            `/embed` Gửi tin nhắn embed
            `/poll` Tạo biểu quyết
            `/giveaway` Tạo phát quà
            """
        elif category == "price":
            embed.title = "🛒 Bảng Giá"
            embed.description = """
            `/price create` Tạo bảng giá
            `/price edit` Sửa tên bảng giá
            `/price add` Thêm sản phẩm
            `/price remove` Xóa sản phẩm
            `/price set` Cập nhật giá
            `/price stock` Cập nhật tồn kho
            `/price embed` Tùy chỉnh embed
            `/price preview` Xem trước
            `/price publish` Đăng bảng giá
            `/price delete` Xóa bảng giá
            """
        elif category == "logs":
            embed.title = "📜 Nhật Ký"
            embed.description = """
            `/logs` Cài đặt kênh log
            `/modlogs` Cài đặt kênh mod log
            `/case` Kiểm tra case
            `/history` Xem lịch sử vi phạm
            """
        elif category == "advanced":
            embed.title = "🤖 Hệ Thống"
            embed.description = """
            `/automod` Quét từ cấm, link rác
            `/antispam` Chống spam
            `/antinuke` Chống phá hoại
            `/backup` Sao lưu server
            `/restore` Khôi phục server
            """
        elif category == "config":
            embed.title = "⚙️ Cài Đặt"
            embed.description = """
            `/config` Xem cấu hình
            `/setwelcome` Tin nhắn chào mừng
            `/setleave` Tin nhắn rời đi
            `/setlog` Cài đặt log
            `/setautorole` Cấp role tự động
            `/setverify` Xác minh button
            """
        elif category == "other":
            embed.title = "ℹ️ Khác"
            embed.description = """
            `/userinfo` Thông tin người dùng
            `/serverinfo` Thông tin server
            `/avatar` Ảnh đại diện
            `/ping` Độ trễ bot
            `/help` Menu trợ giúp
            """
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

class ModBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.spam_cache = {}

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/help"))

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        
        automod_data = db_fetch_one("SELECT * FROM automod WHERE guild_id = ?", (str(message.guild.id),))
        if automod_data and automod_data[1]:
            banned_words = json.loads(automod_data[5])
            if any(word in message.content.lower() for word in banned_words):
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} tin nhắn chứa từ cấm.", delete_after=5)
                except discord.Forbidden:
                    pass
            if "http://" in message.content or "https://" in message.content or "www." in message.content:
                try:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} không được gửi link.", delete_after=5)
                except discord.Forbidden:
                    pass

        if automod_data and automod_data[2]:
            max_messages = automod_data[4]
            user_id = str(message.author.id)
            current_time = datetime.datetime.now()
            if user_id not in self.spam_cache:
                self.spam_cache[user_id] = []
            self.spam_cache[user_id].append(current_time)
            self.spam_cache[user_id] = [t for t in self.spam_cache[user_id] if (current_time - t).seconds < 5]
            if len(self.spam_cache[user_id]) > max_messages:
                try:
                    await message.author.timeout(datetime.timedelta(minutes=1), reason="Spam")
                    await message.channel.send(f"{message.author.mention} đã bị timeout vì spam.", delete_after=5)
                except discord.Forbidden:
                    pass

    async def on_member_join(self, member):
        autorole_data = db_fetch_one("SELECT value FROM config WHERE guild_id = ? AND key = 'autorole'", (str(member.guild.id),))
        if autorole_data:
            role = member.guild.get_role(int(autorole_data[0]))
            if role:
                try:
                    await member.add_roles(role)
                except discord.Forbidden:
                    pass
        
        welcome_data = db_fetch_one("SELECT value FROM config WHERE guild_id = ? AND key = 'welcome'", (str(member.guild.id),))
        if welcome_data:
            try:
                channel_id, message = welcome_data[0].split(":", 1)
                channel = member.guild.get_channel(int(channel_id))
                if channel:
                    message = message.replace("{user}", member.mention).replace("{server}", member.guild.name)
                    await channel.send(message)
            except:
                pass

    async def on_member_remove(self, member):
        leave_data = db_fetch_one("SELECT value FROM config WHERE guild_id = ? AND key = 'leave'", (str(member.guild.id),))
        if leave_data:
            try:
                channel_id, message = leave_data[0].split(":", 1)
                channel = member.guild.get_channel(int(channel_id))
                if channel:
                    message = message.replace("{user}", member.name).replace("{server}", member.guild.name)
                    await channel.send(message)
            except:
                pass

    async def on_guild_channel_delete(self, channel):
        antinuke_data = db_fetch_one("SELECT antinuke_enabled FROM automod WHERE guild_id = ?", (str(channel.guild.id),))
        if antinuke_data and antinuke_data[0]:
            try:
                async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                    if entry.user.bot or entry.user.guild.owner == entry.user:
                        return
                    await channel.guild.ban(entry.user, reason="Antinuke: Xóa kênh trái phép")
            except discord.Forbidden:
                pass

bot = ModBot()

@bot.tree.command(name="ban", description="Cấm thành viên")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do", delete_messages_days: int = 0):
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Bạn không thể cấm người có role cao hơn hoặc bằng mình.", ephemeral=True)
        return
    try:
        await user.ban(reason=reason, delete_message_days=delete_messages_days)
        case_id = db_fetch_one("SELECT COUNT(*) FROM cases WHERE guild_id = ?", (str(interaction.guild.id),))[0] + 1
        db_execute("INSERT INTO cases (guild_id, user_id, moderator_id, action, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (str(interaction.guild.id), str(user.id), str(interaction.user.id), "BAN", reason, str(datetime.datetime.now())))
        await interaction.response.send_message(f"Đã cấm {user.mention}. Case #{case_id}")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền cấm người này.", ephemeral=True)

@bot.tree.command(name="kick", description="Trục xuất thành viên")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do"):
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Bạn không thể trục xuất người có role cao hơn hoặc bằng mình.", ephemeral=True)
        return
    try:
        await user.kick(reason=reason)
        case_id = db_fetch_one("SELECT COUNT(*) FROM cases WHERE guild_id = ?", (str(interaction.guild.id),))[0] + 1
        db_execute("INSERT INTO cases (guild_id, user_id, moderator_id, action, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (str(interaction.guild.id), str(user.id), str(interaction.user.id), "KICK", reason, str(datetime.datetime.now())))
        await interaction.response.send_message(f"Đã trục xuất {user.mention}. Case #{case_id}")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền trục xuất người này.", ephemeral=True)

@bot.tree.command(name="timeout", description="Cách ly thành viên")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, user: discord.Member, duration_minutes: int, reason: str = "Không có lý do"):
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Bạn không thể cách ly người có role cao hơn hoặc bằng mình.", ephemeral=True)
        return
    try:
        await user.timeout(datetime.timedelta(minutes=duration_minutes), reason=reason)
        case_id = db_fetch_one("SELECT COUNT(*) FROM cases WHERE guild_id = ?", (str(interaction.guild.id),))[0] + 1
        db_execute("INSERT INTO cases (guild_id, user_id, moderator_id, action, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (str(interaction.guild.id), str(user.id), str(interaction.user.id), "TIMEOUT", reason, str(datetime.datetime.now())))
        await interaction.response.send_message(f"Đã cách ly {user.mention} trong {duration_minutes} phút. Case #{case_id}")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền cách ly người này.", ephemeral=True)

@bot.tree.command(name="untimeout", description="Hủy cách ly thành viên")
@app_commands.checks.has_permissions(moderate_members=True)
async def untimeout(interaction: discord.Interaction, user: discord.Member):
    try:
        await user.timeout(None, reason="Hủy cách ly")
        await interaction.response.send_message(f"Đã hủy cách ly {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền hủy cách ly người này.", ephemeral=True)

@bot.tree.command(name="warn", description="Cảnh cáo thành viên")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do"):
    if user.top_role >= interaction.user.top_role:
        await interaction.response.send_message("Bạn không thể cảnh cáo người có role cao hơn hoặc bằng mình.", ephemeral=True)
        return
    try:
        db_execute("INSERT INTO warns (guild_id, user_id, moderator_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (str(interaction.guild.id), str(user.id), str(interaction.user.id), reason, str(datetime.datetime.now())))
        warn_id = db_fetch_one("SELECT id FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1", (str(interaction.guild.id), str(user.id)))[0]
        await interaction.response.send_message(f"Đã cảnh cáo {user.mention}. Warn ID: #{warn_id}")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

async def warn_id_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    user = interaction.namespace.user
    if not user:
        return [app_commands.Choice(name="Chọn user trước", value="0")]
    rows = db_fetch("SELECT id FROM warns WHERE guild_id = ? AND user_id = ?", (str(interaction.guild.id), str(user.id)))
    return [app_commands.Choice(name=f"ID: {row[0]}", value=str(row[0])) for row in rows if current in str(row[0])][:25]

@bot.tree.command(name="unwarn", description="Xóa 1 lần cảnh cáo cụ thể")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.autocomplete(warn_id=warn_id_autocomplete)
async def unwarn(interaction: discord.Interaction, user: discord.Member, warn_id: str):
    try:
        db_execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ? AND id = ?", (str(interaction.guild.id), str(user.id), int(warn_id)))
        await interaction.response.send_message(f"Đã xóa cảnh cáo #{warn_id} của {user.mention}.")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="clearwarn", description="Xóa toàn bộ cảnh cáo của user")
@app_commands.checks.has_permissions(moderate_members=True)
async def clearwarn(interaction: discord.Interaction, user: discord.Member):
    try:
        db_execute("DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (str(interaction.guild.id), str(user.id)))
        await interaction.response.send_message(f"Đã xóa toàn bộ cảnh cáo của {user.mention}.")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@bot.tree.command(name="mute", description="Tắt tiếng thành viên")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, user: discord.Member, reason: str = "Không có lý do"):
    try:
        await user.timeout(datetime.timedelta(days=28), reason=reason)
        await interaction.response.send_message(f"Đã tắt tiếng {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền tắt tiếng người này.", ephemeral=True)

@bot.tree.command(name="unmute", description="Mở tiếng thành viên")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, user: discord.Member):
    try:
        await user.timeout(None, reason="Mở tiếng")
        await interaction.response.send_message(f"Đã mở tiếng {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền mở tiếng người này.", ephemeral=True)

@bot.tree.command(name="clear", description="Xóa số lượng tin nhắn chỉ định")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Số lượng phải từ 1 đến 100.", ephemeral=True)
        return
    try:
        await interaction.response.defer()
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Đã xóa {len(deleted)} tin nhắn.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("Bot không có quyền xóa tin nhắn.", ephemeral=True)

@bot.tree.command(name="slowmode", description="Bật chế độ chậm cho kênh")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int):
    try:
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Đã đặt chế độ chậm {seconds} giây.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền chỉnh sửa kênh.", ephemeral=True)

@bot.tree.command(name="lock", description="Khóa kênh hiện tại")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message("Đã khóa kênh.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền chỉnh sửa kênh.", ephemeral=True)

@bot.tree.command(name="unlock", description="Mở khóa kênh hiện tại")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):
    try:
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
        await interaction.response.send_message("Đã mở khóa kênh.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền chỉnh sửa kênh.", ephemeral=True)

@bot.tree.command(name="purgebot", description="Chỉ xóa các tin nhắn của Bot")
@app_commands.checks.has_permissions(manage_messages=True)
async def purgebot(interaction: discord.Interaction, amount: int):
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Số lượng phải từ 1 đến 100.", ephemeral=True)
        return
    try:
        await interaction.response.defer()
        deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author == bot.user)
        await interaction.followup.send(f"Đã xóa {len(deleted)} tin nhắn của bot.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("Bot không có quyền xóa tin nhắn.", ephemeral=True)

role = app_commands.Group(name="role", description="Quản lý vai trò")
bot.tree.add_command(role)

@role.command(name="add", description="Thêm vai trò cho thành viên")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_add(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    try:
        await user.add_roles(role)
        await interaction.response.send_message(f"Đã thêm role {role.mention} cho {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền quản lý role.", ephemeral=True)

@role.command(name="remove", description="Xóa vai trò của thành viên")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_remove(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    try:
        await user.remove_roles(role)
        await interaction.response.send_message(f"Đã xóa role {role.mention} của {user.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền quản lý role.", ephemeral=True)

@role.command(name="create", description="Tạo vai trò mới")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_create(interaction: discord.Interaction, name: str, color: str):
    try:
        color = discord.Color(int(color.strip("#"), 16))
        await interaction.guild.create_role(name=name, color=color)
        await interaction.response.send_message(f"Đã tạo role {name}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền tạo role.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Mã màu không hợp lệ.", ephemeral=True)

@role.command(name="delete", description="Xóa vai trò")
@app_commands.checks.has_permissions(manage_roles=True)
async def role_delete(interaction: discord.Interaction, role: discord.Role):
    try:
        await role.delete()
        await interaction.response.send_message(f"Đã xóa role {role.name}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền xóa role.", ephemeral=True)

@bot.tree.command(name="nickname", description="Đổi biệt danh thành viên")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nickname(interaction: discord.Interaction, user: discord.Member, new_nickname: str):
    try:
        await user.edit(nick=new_nickname)
        await interaction.response.send_message(f"Đã đổi biệt danh {user.mention} thành {new_nickname}.")
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền đổi biệt danh.", ephemeral=True)

@bot.tree.command(name="announce", description="Gửi thông báo công khai")
@app_commands.checks.has_permissions(manage_messages=True)
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    try:
        await channel.send(message)
        await interaction.response.send_message(f"Đã gửi thông báo đến {channel.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền gửi tin nhắn.", ephemeral=True)

@bot.tree.command(name="embed", description="Gửi tin nhắn dạng Embed")
@app_commands.checks.has_permissions(manage_messages=True)
async def embed(interaction: discord.Interaction, channel: discord.TextChannel, title: str, description: str, color: str = "2f3136"):
    try:
        embed_color = discord.Color(int(color.strip("#"), 16))
        embed_msg = discord.Embed(title=title, description=description, color=embed_color)
        await channel.send(embed=embed_msg)
        await interaction.response.send_message(f"Đã gửi embed đến {channel.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền gửi tin nhắn.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("Mã màu không hợp lệ.", ephemeral=True)

@bot.tree.command(name="poll", description="Tạo cuộc biểu quyết")
@app_commands.checks.has_permissions(manage_messages=True)
async def poll(interaction: discord.Interaction, question: str, options: str):
    option_list = [opt.strip() for opt in options.split(",")]
    if len(option_list) < 2 or len(option_list) > 10:
        await interaction.response.send_message("Số lượng lựa chọn phải từ 2 đến 10.", ephemeral=True)
        return
    emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    description = "\n".join([f"{emoji_list[i]} {opt}" for i, opt in enumerate(option_list)])
    embed = discord.Embed(title=question, description=description, color=discord.Color.gold())
    try:
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for i in range(len(option_list)):
            await message.add_reaction(emoji_list[i])
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền gửi tin nhắn.", ephemeral=True)

async def giveaway_task(message: discord.Message, duration_minutes: int, winners: int, prize: str):
    await asyncio.sleep(duration_minutes * 60)
    reactions = message.reactions
    participants = []
    for reaction in reactions:
        if reaction.emoji == "🎉":
            async for user in reaction.users():
                if not user.bot:
                    participants.append(user)
    if not participants:
        await message.channel.send(f"Không có người tham gia giveaway {prize}.")
        return
    winner_list = random.sample(participants, min(winners, len(participants)))
    winner_mentions = ", ".join([w.mention for w in winner_list])
    await message.channel.send(f"Chúc mừng {winner_mentions} đã thắng {prize}!")

@bot.tree.command(name="giveaway", description="Hệ thống phát quà")
@app_commands.checks.has_permissions(manage_messages=True)
async def giveaway(interaction: discord.Interaction, duration_minutes: int, winners: int, prize: str):
    embed = discord.Embed(title="🎉 Giveaway!", description=f"Prize: {prize}\nWinners: {winners}\nTime: {duration_minutes} minutes", color=discord.Color.gold())
    embed.set_footer(text="React 🎉 to enter")
    try:
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎉")
        asyncio.create_task(giveaway_task(message, duration_minutes, winners, prize))
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền gửi tin nhắn.", ephemeral=True)

async def price_board_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    rows = db_fetch("SELECT board_name FROM price_boards WHERE guild_id = ?", (str(interaction.guild.id),))
    return [app_commands.Choice(name=row[0], value=row[0]) for row in rows if current.lower() in row[0].lower()][:25]

async def price_product_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    board_name = interaction.namespace.board_name
    if not board_name:
        return [app_commands.Choice(name="Chọn bảng giá trước", value="none")]
    board_data = db_fetch_one("SELECT id FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        return []
    board_id = board_data[0]
    rows = db_fetch("SELECT product_name FROM price_items WHERE board_id = ?", (str(board_id),))
    return [app_commands.Choice(name=row[0], value=row[0]) for row in rows if current.lower() in row[0].lower()][:25]

async def update_published_embed(board_name: str):
    board_data = db_fetch_one("SELECT * FROM price_boards WHERE board_name = ?", (board_name,))
    if not board_data or board_data[6] == '0' or board_data[7] == '0':
        return
    guild = bot.get_guild(int(board_data[1]))
    if not guild:
        return
    channel = guild.get_channel(int(board_data[6]))
    if not channel:
        return
    try:
        message = await channel.fetch_message(int(board_data[7]))
    except:
        return
    items = db_fetch("SELECT product_name, price, stock FROM price_items WHERE board_id = ?", (str(board_data[0]),))
    description = board_data[4] + "\n\n"
    for item in items:
        description += f"**{item[0]}**\nGiá: {item[1]} | Tồn: {item[2]}\n\n"
    embed = discord.Embed(title=board_data[3], description=description, color=discord.Color(int(board_data[5], 16)))
    await message.edit(embed=embed)

price = app_commands.Group(name="price", description="Quản lý bảng giá")
bot.tree.add_command(price)

@price.command(name="create", description="Tạo một bảng giá mới")
async def price_create(interaction: discord.Interaction, board_name: str):
    try:
        db_execute("INSERT INTO price_boards (guild_id, board_name) VALUES (?, ?)", (str(interaction.guild.id), board_name))
        await interaction.response.send_message(f"Đã tạo bảng giá {board_name}.", ephemeral=True)
    except sqlite3.IntegrityError:
        await interaction.response.send_message("Tên bảng giá đã tồn tại.", ephemeral=True)

@price.command(name="edit", description="Chỉnh sửa tên bảng giá")
@app_commands.autocomplete(board_name=price_board_autocomplete)
async def price_edit(interaction: discord.Interaction, board_name: str, new_name: str):
    try:
        db_execute("UPDATE price_boards SET board_name = ? WHERE guild_id = ? AND board_name = ?", (new_name, str(interaction.guild.id), board_name))
        await interaction.response.send_message(f"Đã đổi tên bảng giá thành {new_name}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@price.command(name="add", description="Thêm sản phẩm mới")
@app_commands.autocomplete(board_name=price_board_autocomplete)
async def price_add(interaction: discord.Interaction, board_name: str, product_name: str, price: str, stock: str):
    board_data = db_fetch_one("SELECT id FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    board_id = board_data[0]
    db_execute("INSERT INTO price_items (board_id, product_name, price, stock) VALUES (?, ?, ?, ?)", (str(board_id), product_name, price, stock))
    await interaction.response.send_message(f"Đã thêm sản phẩm {product_name}.", ephemeral=True)
    await update_published_embed(board_name)

@price.command(name="remove", description="Xóa sản phẩm")
@app_commands.autocomplete(board_name=price_board_autocomplete, product_name=price_product_autocomplete)
async def price_remove(interaction: discord.Interaction, board_name: str, product_name: str):
    board_data = db_fetch_one("SELECT id FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    board_id = board_data[0]
    db_execute("DELETE FROM price_items WHERE board_id = ? AND product_name = ?", (str(board_id), product_name))
    await interaction.response.send_message(f"Đã xóa sản phẩm {product_name}.", ephemeral=True)
    await update_published_embed(board_name)

@price.command(name="set", description="Cập nhật giá")
@app_commands.autocomplete(board_name=price_board_autocomplete, product_name=price_product_autocomplete)
async def price_set(interaction: discord.Interaction, board_name: str, product_name: str, new_price: str):
    board_data = db_fetch_one("SELECT id FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    board_id = board_data[0]
    db_execute("UPDATE price_items SET price = ? WHERE board_id = ? AND product_name = ?", (new_price, str(board_id), product_name))
    await interaction.response.send_message(f"Đã cập nhật giá {product_name} thành {new_price}.", ephemeral=True)
    await update_published_embed(board_name)

@price.command(name="stock", description="Cập nhật số lượng tồn kho")
@app_commands.autocomplete(board_name=price_board_autocomplete, product_name=price_product_autocomplete)
async def price_stock(interaction: discord.Interaction, board_name: str, product_name: str, new_stock: str):
    board_data = db_fetch_one("SELECT id FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    board_id = board_data[0]
    db_execute("UPDATE price_items SET stock = ? WHERE board_id = ? AND product_name = ?", (new_stock, str(board_id), product_name))
    await interaction.response.send_message(f"Đã cập nhật tồn kho {product_name} thành {new_stock}.", ephemeral=True)
    await update_published_embed(board_name)

@price.command(name="embed", description="Tùy chỉnh Embed hiển thị")
@app_commands.autocomplete(board_name=price_board_autocomplete)
async def price_embed(interaction: discord.Interaction, board_name: str, title: str, description: str, hex_color: str):
    db_execute("UPDATE price_boards SET title = ?, description = ?, color = ? WHERE guild_id = ? AND board_name = ?", (title, description, hex_color.strip("#"), str(interaction.guild.id), board_name))
    await interaction.response.send_message(f"Đã cập nhật embed bảng giá {board_name}.", ephemeral=True)

@price.command(name="preview", description="Xem trước giao diện Embed")
@app_commands.autocomplete(board_name=price_board_autocomplete)
async def price_preview(interaction: discord.Interaction, board_name: str):
    board_data = db_fetch_one("SELECT * FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    items = db_fetch("SELECT product_name, price, stock FROM price_items WHERE board_id = ?", (str(board_data[0]),))
    description = board_data[4] + "\n\n"
    for item in items:
        description += f"**{item[0]}**\nGiá: {item[1]} | Tồn: {item[2]}\n\n"
    embed = discord.Embed(title=board_data[3], description=description, color=discord.Color(int(board_data[5], 16)))
    await interaction.response.send_message(embed=embed, ephemeral=True)

@price.command(name="publish", description="Đăng bảng giá lên một kênh cụ thể")
@app_commands.autocomplete(board_name=price_board_autocomplete)
async def price_publish(interaction: discord.Interaction, board_name: str, channel: discord.TextChannel):
    board_data = db_fetch_one("SELECT * FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    items = db_fetch("SELECT product_name, price, stock FROM price_items WHERE board_id = ?", (str(board_data[0]),))
    description = board_data[4] + "\n\n"
    for item in items:
        description += f"**{item[0]}**\nGiá: {item[1]} | Tồn: {item[2]}\n\n"
    embed = discord.Embed(title=board_data[3], description=description, color=discord.Color(int(board_data[5], 16)))
    try:
        message = await channel.send(embed=embed)
        db_execute("UPDATE price_boards SET channel_id = ?, message_id = ? WHERE guild_id = ? AND board_name = ?", (str(channel.id), str(message.id), str(interaction.guild.id), board_name))
        await interaction.response.send_message(f"Đã đăng bảng giá {board_name} đến {channel.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền gửi tin nhắn.", ephemeral=True)

@price.command(name="delete", description="Xóa toàn bộ dữ liệu bảng giá")
@app_commands.autocomplete(board_name=price_board_autocomplete)
async def price_delete(interaction: discord.Interaction, board_name: str):
    board_data = db_fetch_one("SELECT id FROM price_boards WHERE guild_id = ? AND board_name = ?", (str(interaction.guild.id), board_name))
    if not board_data:
        await interaction.response.send_message("Không tìm thấy bảng giá.", ephemeral=True)
        return
    board_id = board_data[0]
    db_execute("DELETE FROM price_items WHERE board_id = ?", (str(board_id),))
    db_execute("DELETE FROM price_boards WHERE id = ?", (str(board_id),))
    await interaction.response.send_message(f"Đã xóa bảng giá {board_name}.", ephemeral=True)

@bot.tree.command(name="logs", description="Cài đặt kênh log tổng hợp")
@app_commands.checks.has_permissions(manage_guild=True)
async def logs(interaction: discord.Interaction, channel: discord.TextChannel):
    db_execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)", (str(interaction.guild.id), "log", str(channel.id)))
    await interaction.response.send_message(f"Đã đặt kênh log tổng hợp là {channel.mention}.", ephemeral=True)

@bot.tree.command(name="modlogs", description="Cài đặt kênh log riêng cho đội ngũ Admin/Mod")
@app_commands.checks.has_permissions(manage_guild=True)
async def modlogs(interaction: discord.Interaction, channel: discord.TextChannel):
    db_execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)", (str(interaction.guild.id), "modlog", str(channel.id)))
    await interaction.response.send_message(f"Đã đặt kênh mod log là {channel.mention}.", ephemeral=True)

async def case_id_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    rows = db_fetch("SELECT id FROM cases WHERE guild_id = ?", (str(interaction.guild.id),))
    return [app_commands.Choice(name=f"Case #{row[0]}", value=str(row[0])) for row in rows if current in str(row[0])][:25]

@bot.tree.command(name="case", description="Kiểm tra chi tiết một vụ xử lý vi phạm")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.autocomplete(case_id=case_id_autocomplete)
async def case(interaction: discord.Interaction, case_id: str):
    case_data = db_fetch_one("SELECT * FROM cases WHERE guild_id = ? AND id = ?", (str(interaction.guild.id), int(case_id)))
    if not case_data:
        await interaction.response.send_message("Không tìm thấy case.", ephemeral=True)
        return
    user = interaction.guild.get_member(int(case_data[2]))
    moderator = interaction.guild.get_member(int(case_data[3]))
    embed = discord.Embed(title=f"Case #{case_data[0]}", color=discord.Color.blue())
    embed.add_field(name="User", value=user.mention if user else case_data[2], inline=True)
    embed.add_field(name="Moderator", value=moderator.mention if moderator else case_data[3], inline=True)
    embed.add_field(name="Action", value=case_data[4], inline=True)
    embed.add_field(name="Reason", value=case_data[5], inline=True)
    embed.add_field(name="Timestamp", value=case_data[6], inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="history", description="Xem lịch sử vi phạm của user")
@app_commands.checks.has_permissions(moderate_members=True)
async def history(interaction: discord.Interaction, user: discord.Member):
    warns = db_fetch("SELECT id, reason, timestamp FROM warns WHERE guild_id = ? AND user_id = ?", (str(interaction.guild.id), str(user.id)))
    cases = db_fetch("SELECT id, action, reason, timestamp FROM cases WHERE guild_id = ? AND user_id = ?", (str(interaction.guild.id), str(user.id)))
    embed = discord.Embed(title=f"Lịch sử vi phạm của {user.name}", color=discord.Color.red())
    warn_text = "\n".join([f"ID {w[0]}: {w[1]} ({w[2]})" for w in warns]) if warns else "Không có"
    case_text = "\n".join([f"Case #{c[0]}: {c[1]} - {c[2]} ({c[3]})" for c in cases]) if cases else "Không có"
    embed.add_field(name="Warns", value=warn_text, inline=False)
    embed.add_field(name="Cases", value=case_text, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def enable_disable_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name="enable", value="enable"), app_commands.Choice(name="disable", value="disable")]

async def automod_type_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name="words", value="words"), app_commands.Choice(name="links", value="links")]

@bot.tree.command(name="automod", description="Hệ thống tự động quét và chặn")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.autocomplete(enable_disable=enable_disable_autocomplete, type=automod_type_autocomplete)
async def automod(interaction: discord.Interaction, enable_disable: str, type: str):
    enabled = 1 if enable_disable == "enable" else 0
    db_execute("INSERT OR IGNORE INTO automod (guild_id) VALUES (?)", (str(interaction.guild.id),))
    if type == "words":
        db_execute("UPDATE automod SET enabled = ? WHERE guild_id = ?", (enabled, str(interaction.guild.id)))
    elif type == "links":
        db_execute("UPDATE automod SET enabled = ? WHERE guild_id = ?", (enabled, str(interaction.guild.id)))
    await interaction.response.send_message(f"Đã {enable_disable} automod cho {type}.", ephemeral=True)

@bot.tree.command(name="antispam", description="Chống spam tin nhắn liên tục")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.autocomplete(enable_disable=enable_disable_autocomplete)
async def antispam(interaction: discord.Interaction, enable_disable: str, max_messages: int = 5):
    enabled = 1 if enable_disable == "enable" else 0
    db_execute("INSERT OR IGNORE INTO automod (guild_id) VALUES (?)", (str(interaction.guild.id),))
    db_execute("UPDATE automod SET spam_enabled = ?, max_messages = ? WHERE guild_id = ?", (enabled, max_messages, str(interaction.guild.id)))
    await interaction.response.send_message(f"Đã {enable_disable} antispam với max messages = {max_messages}.", ephemeral=True)

@bot.tree.command(name="antinuke", description="Bảo vệ server, check hành vi phá hoại")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.autocomplete(enable_disable=enable_disable_autocomplete)
async def antinuke(interaction: discord.Interaction, enable_disable: str):
    enabled = 1 if enable_disable == "enable" else 0
    db_execute("INSERT OR IGNORE INTO automod (guild_id) VALUES (?)", (str(interaction.guild.id),))
    db_execute("UPDATE automod SET antinuke_enabled = ? WHERE guild_id = ?", (enabled, str(interaction.guild.id)))
    await interaction.response.send_message(f"Đã {enable_disable} antinuke.", ephemeral=True)

@bot.tree.command(name="backup", description="Tạo bản sao lưu cấu trúc server")
@app_commands.checks.has_permissions(manage_guild=True)
async def backup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    backup_data = {
        "name": guild.name,
        "roles": [],
        "categories": [],
        "channels": []
    }
    for role in guild.roles:
        if role.name != "@everyone":
            backup_data["roles"].append({
                "name": role.name,
                "color": str(role.color),
                "permissions": role.permissions.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable
            })
    for category in guild.categories:
        cat_data = {
            "name": category.name,
            "position": category.position,
            "permissions": [],
            "channels": []
        }
        for role, overwrite in category.overwrites.items():
            cat_data["permissions"].append({
                "role_name": role.name if isinstance(role, discord.Role) else "@everyone",
                "allow": overwrite.pair()[0].value,
                "deny": overwrite.pair()[1].value
            })
        for channel in category.channels:
            cat_data["channels"].append({
                "name": channel.name,
                "type": str(channel.type),
                "position": channel.position,
                "topic": getattr(channel, 'topic', None)
            })
        backup_data["categories"].append(cat_data)
    for channel in guild.channels:
        if channel.category is None and channel.type != discord.ChannelType.category:
            backup_data["channels"].append({
                "name": channel.name,
                "type": str(channel.type),
                "position": channel.position,
                "topic": getattr(channel, 'topic', None)
            })
    db_execute("INSERT INTO backups (guild_id, data, timestamp) VALUES (?, ?, ?)", (str(guild.id), json.dumps(backup_data), str(datetime.datetime.now())))
    await interaction.followup.send("Đã tạo bản sao lưu server.", ephemeral=True)

async def backup_id_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    rows = db_fetch("SELECT id, timestamp FROM backups WHERE guild_id = ?", (str(interaction.guild.id),))
    return [app_commands.Choice(name=f"Backup #{row[0]} - {row[1]}", value=str(row[0])) for row in rows if current in str(row[0])][:25]

@bot.tree.command(name="restore", description="Khôi phục server từ bản sao lưu")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.autocomplete(backup_id=backup_id_autocomplete)
async def restore(interaction: discord.Interaction, backup_id: str):
    await interaction.response.defer(ephemeral=True)
    backup_data = db_fetch_one("SELECT data FROM backups WHERE guild_id = ? AND id = ?", (str(interaction.guild.id), int(backup_id)))
    if not backup_data:
        await interaction.followup.send("Không tìm thấy bản sao lưu.", ephemeral=True)
        return
    data = json.loads(backup_data[0])
    guild = interaction.guild
    for channel in guild.channels:
        try:
            await channel.delete()
        except:
            pass
    for role in guild.roles:
        if role.name != "@everyone":
            try:
                await role.delete()
            except:
                pass
    for role_data in data["roles"]:
        try:
            color = discord.Color(int(role_data["color"].strip("#"), 16)) if role_data["color"] != "0" else discord.Color.default()
            await guild.create_role(
                name=role_data["name"],
                color=color,
                permissions=discord.Permissions(permissions=role_data["permissions"]),
                hoist=role_data["hoist"],
                mentionable=role_data["mentionable"]
            )
        except:
            pass
    for channel_data in data["channels"]:
        try:
            if channel_data["type"] == "text":
                await guild.create_text_channel(name=channel_data["name"], position=channel_data["position"], topic=channel_data["topic"])
            elif channel_data["type"] == "voice":
                await guild.create_voice_channel(name=channel_data["name"], position=channel_data["position"])
        except:
            pass
    for cat_data in data["categories"]:
        try:
            overwrites = {}
            for perm in cat_data["permissions"]:
                role = discord.utils.get(guild.roles, name=perm["role_name"]) or guild.default_role
                overwrites[role] = discord.PermissionOverwrite.from_pair(discord.Permissions(perm["allow"]), discord.Permissions(perm["deny"]))
            category = await guild.create_category(name=cat_data["name"], position=cat_data["position"], overwrites=overwrites)
            for chan in cat_data["channels"]:
                if chan["type"] == "text":
                    await guild.create_text_channel(name=chan["name"], category=category, position=chan["position"], topic=chan["topic"])
                elif chan["type"] == "voice":
                    await guild.create_voice_channel(name=chan["name"], category=category, position=chan["position"])
        except:
            pass
    await interaction.followup.send("Đã khôi phục server từ bản sao lưu.", ephemeral=True)

@bot.tree.command(name="config", description="Xem toàn bộ cấu hình hiện tại của Bot")
@app_commands.checks.has_permissions(manage_guild=True)
async def config(interaction: discord.Interaction):
    configs = db_fetch("SELECT key, value FROM config WHERE guild_id = ?", (str(interaction.guild.id),))
    embed = discord.Embed(title="Cấu hình Bot", color=discord.Color.blue())
    for key, value in configs:
        embed.add_field(name=key, value=value, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="setwelcome", description="Kênh và tin nhắn chào mừng")
@app_commands.checks.has_permissions(manage_guild=True)
async def setwelcome(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    db_execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)", (str(interaction.guild.id), "welcome", f"{channel.id}:{message}"))
    await interaction.response.send_message(f"Đã đặt welcome channel là {channel.mention}.", ephemeral=True)

@bot.tree.command(name="setleave", description="Kênh và tin nhắn khi thành viên rời đi")
@app_commands.checks.has_permissions(manage_guild=True)
async def setleave(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    db_execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)", (str(interaction.guild.id), "leave", f"{channel.id}:{message}"))
    await interaction.response.send_message(f"Đã đặt leave channel là {channel.mention}.", ephemeral=True)

async def log_type_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    return [app_commands.Choice(name="log", value="log"), app_commands.Choice(name="modlog", value="modlog"), app_commands.Choice(name="welcome", value="welcome"), app_commands.Choice(name="leave", value="leave")]

@bot.tree.command(name="setlog", description="Bật/tắt và chọn kênh cho từng loại log cụ thể")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.autocomplete(type=log_type_autocomplete)
async def setlog(interaction: discord.Interaction, type: str, channel: discord.TextChannel):
    db_execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)", (str(interaction.guild.id), type, str(channel.id)))
    await interaction.response.send_message(f"Đã đặt {type} channel là {channel.mention}.", ephemeral=True)

@bot.tree.command(name="setautorole", description="Tự động cấp role khi thành viên mới tham gia")
@app_commands.checks.has_permissions(manage_guild=True)
async def setautorole(interaction: discord.Interaction, role: discord.Role):
    db_execute("INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)", (str(interaction.guild.id), "autorole", str(role.id)))
    await interaction.response.send_message(f"Đã đặt autorole là {role.mention}.", ephemeral=True)

@bot.tree.command(name="setverify", description="Hệ thống xác minh bằng Button")
@app_commands.checks.has_permissions(manage_guild=True)
async def setverify(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
    embed = discord.Embed(title="Xác Minh", description="Nhấn nút bên dưới để xác minh.", color=discord.Color.green())
    view = VerifyView(role.id)
    try:
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Đã gửi verify button đến {channel.mention}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Bot không có quyền gửi tin nhắn.", ephemeral=True)

@bot.tree.command(name="userinfo", description="Xem thông tin chi tiết tài khoản")
async def userinfo(interaction: discord.Interaction, user: discord.Member):
    embed = discord.Embed(title=f"Thông tin {user.name}", color=user.color)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Nickname", value=user.display_name, inline=True)
    embed.add_field(name="Joined", value=user.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Created", value=user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    roles = ", ".join([r.mention for r in user.roles if r.name != "@everyone"])
    embed.add_field(name="Roles", value=roles if roles else "None", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="serverinfo", description="Xem thông tin chi tiết Server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"Thông tin {guild.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="avatar", description="Lấy ảnh đại diện chất lượng cao")
async def avatar(interaction: discord.Interaction, user: discord.Member):
    embed = discord.Embed(title=f"Avatar của {user.name}", color=discord.Color.blue())
    embed.set_image(url=user.display_avatar.url)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Kiểm tra độ trễ của Bot và API")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Độ trễ: {latency}ms.", ephemeral=True)

@bot.tree.command(name="help", description="Menu hướng dẫn trực quan")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Menu Trợ Giúp", description="Chọn danh mục bên dưới để xem lệnh.", color=discord.Color.blue())
    view = HelpView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

initialize_database()
bot.run("")