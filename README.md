# ManagerBot
# 🛡️ DISCORD MODERATION & SERVER MANAGEMENT BOT

A multi-purpose Discord management bot built with `discord.py` and `SQLite3`. Packed with automated moderation, price board creation, server backup/restore capabilities, custom verification views, and detailed audit history tracking.

---

## 📑 TABLE OF CONTENTS
1. [Key Features](#-key-features)
2. [Command Reference](#-command-reference)
3. [Database Structure](#-database-structure)
4. [Installation & Setup](#-installation--setup)
5. [Security & Self-Hosting Advice](#-security--self-hosting-advice)

---

## 🌟 KEY FEATURES

### 🔨 1. Moderation & Audit Cases
- **Punishment Actions**: `/ban`, `/kick`, `/timeout`, `/untimeout`, `/mute`, `/unmute` with permission hierarchy checks.
- **Warning System**: Issue, list, and clear warnings for members (`/warn`, `/unwarn`, `/clearwarn`)[cite: 3].
- **Audit Case Logging**: Automatically creates and logs unique Case IDs in SQLite for moderation actions[cite: 3].

### 🤖 2. Auto-Moderation & Protection
- **Banned Words & Link Filter**: Deletes messages containing forbidden keywords or unauthorized URLs[cite: 3].
- **Anti-Spam**: Rate-limits user messages within short time windows and applies automatic timeouts upon violation[cite: 3].
- **Anti-Nuke**: Monitors channel deletions via Audit Logs and bans malicious actors[cite: 3].

### 🛒 3. Interactive Price Board System
- Full CRUD system for custom product catalog embeds (`/price create`, `/price add`, `/price set`, `/price stock`, etc.)[cite: 3].
- **Live Auto-Update**: Modifying prices or inventory automatically updates published price embeds[cite: 3].

### 💾 4. Server Backup & Restoration
- **Backup Snapshot**: Captures full server architecture including roles, permissions, categories, text/voice channel layouts, and topics (`/backup`)[cite: 3].
- **Restore Engine**: Purges current layout and reconstructs server structure from a selected backup ID (`/restore`)[cite: 3].

### ⚙️ 5. Server Utilities & Onboarding
- **Button Verification**: Single-click role verification using persistent UI components (`/setverify`)[cite: 3].
- **Welcome & Leave Messages**: Customizable entry/exit notifications with placeholders like `{user}` and `{server}`[cite: 3].
- **Auto-Role**: Automatically assigns designated roles to newly joined members (`/setautorole`)[cite: 3].
- **Interactive Help Menu**: Multi-category select dropdown navigation (`/help`)[cite: 3].

---

## 📜 COMMAND REFERENCE

### 🛡️ Moderation & Member Management
| Command | Permission | Description |
| :--- | :--- | :--- |
| `/ban` | Ban Members | Bans a member with optional message purge days[cite: 3]. |
| `/kick` | Kick Members | Kicks a member from the server[cite: 3]. |
| `/timeout` | Moderate Members | Applies a temporary timeout (in minutes)[cite: 3]. |
| `/untimeout` | Moderate Members | Removes timeout from a member[cite: 3]. |
| `/warn` | Moderate Members | Issues a warning to a user[cite: 3]. |
| `/unwarn` | Moderate Members | Removes a specific warning by Warn ID[cite: 3]. |
| `/clearwarn` | Moderate Members | Clears all warnings for a user[cite: 3]. |
| `/mute` / `/unmute` | Moderate Members | Mutes (28-day timeout) or unmutes a user[cite: 3]. |
| `/history` | Moderate Members | Views moderation history (warnings and cases)[cite: 3]. |
| `/case` | Moderate Members | Fetches details for a specific case ID[cite: 3]. |

### 💬 Channel & Message Management
| Command | Permission | Description |
| :--- | :--- | :--- |
| `/clear` | Manage Messages | Deletes up to 100 messages[cite: 3]. |
| `/purgebot` | Manage Messages | Deletes up to 100 bot messages[cite: 3]. |
| `/slowmode` | Manage Channels | Sets channel slowmode delay[cite: 3]. |
| `/lock` / `/unlock` | Manage Channels | Locks or unlocks channel text permissions[cite: 3]. |
| `/announce` | Manage Messages | Sends a plain text announcement to a channel[cite: 3]. |
| `/embed` | Manage Messages | Sends a customized Embed message[cite: 3]. |
| `/poll` | Manage Messages | Creates a multi-option reaction poll[cite: 3]. |
| `/giveaway` | Manage Messages | Hosts an automated reaction giveaway[cite: 3]. |

### 🛒 Price Board Management (`/price`)
| Subcommand | Description |
| :--- | :--- |
| `/price create` | Creates a new price board instance[cite: 3]. |
| `/price edit` | Renames an existing price board[cite: 3]. |
| `/price add` | Adds a product, price, and stock count[cite: 3]. |
| `/price remove` | Removes a product from a board[cite: 3]. |
| `/price set` | Updates the price of an existing product[cite: 3]. |
| `/price stock` | Updates the available stock of a product[cite: 3]. |
| `/price embed` | Customizes title, description, and hex color[cite: 3]. |
| `/price preview` | Sends a private preview embed[cite: 3]. |
| `/price publish` | Publishes the live embed to a channel[cite: 3]. |
| `/price delete` | Deletes a price board and associated items[cite: 3]. |

### 🤖 AutoMod & Server Config
| Command | Permission | Description |
| :--- | :--- | :--- |
| `/automod` | Manage Server | Toggles word and link filtering[cite: 3]. |
| `/antispam` | Manage Server | Enables anti-spam with customizable threshold[cite: 3]. |
| `/antinuke` | Manage Server | Toggles channel deletion protection[cite: 3]. |
| `/backup` | Manage Server | Creates a snapshot backup of server structure[cite: 3]. |
| `/restore` | Manage Server | Restores server channels and roles from a backup[cite: 3]. |
| `/setwelcome` | Manage Server | Configures welcome channel and message[cite: 3]. |
| `/setleave` | Manage Server | Configures leave channel and message[cite: 3]. |
| `/setautorole` | Manage Server | Sets the default role for new members[cite: 3]. |
| `/setverify` | Manage Server | Sends a button verification panel to a channel[cite: 3]. |

---

## 🗄️ DATABASE STRUCTURE

The bot uses `bot_database.db` (SQLite) with the following primary tables[cite: 3]:
- **`config`**: Key-value storage for server settings (welcome, leave, log channels, autorole)[cite: 3].
- **`warns`**: User warning history with moderator IDs, timestamps, and reasons[cite: 3].
- **`cases`**: Formal moderation logs (bans, kicks, timeouts)[cite: 3].
- **`automod`**: Server settings for anti-spam thresholds, anti-nuke toggles, and banned word lists[cite: 3].
- **`backups`**: JSON-serialized server structure snapshots[cite: 3].
- **`price_boards` & `price_items`**: Board configurations, active channel/message bindings, and product listings[cite: 3].

---

## 🚀 INSTALLATION & SETUP

### 1. Prerequisites
- Python `3.10` or higher.
- Required dependencies:
  ```bash
  pip install discord.py
