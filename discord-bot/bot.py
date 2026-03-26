"""
Minecraft Server Discord Bot
- Server status & player list
- Start/stop EC2 instance
- Player join/leave notifications (via RCON polling)
"""

import os
import asyncio
import random
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from mcstatus import JavaServer
import boto3

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
MC_HOST = os.getenv("MC_SERVER_HOST", "127.0.0.1")
MC_JAVA_PORT = int(os.getenv("MC_JAVA_PORT", "25565"))
MC_BEDROCK_PORT = int(os.getenv("MC_BEDROCK_PORT", "19132"))
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
EC2_INSTANCE_ID = os.getenv("EC2_INSTANCE_ID", "")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Track online players for join/leave notifications
previous_players: set[str] = set()


def get_ec2_client():
    return boto3.client("ec2", region_name=AWS_REGION)


async def query_server():
    """Query the Minecraft server status."""
    try:
        server = JavaServer.lookup(f"{MC_HOST}:{MC_JAVA_PORT}")
        status = await server.async_status()
        return status
    except Exception:
        return None


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    if CHANNEL_ID:
        player_watch.start()


@bot.command(name="status")
async def server_status(ctx):
    """Show server status, player count, and connection info."""
    status = await query_server()

    if status is None:
        embed = discord.Embed(
            title="🔴 Server Offline",
            description="The Minecraft server is not responding.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    players_online = status.players.online
    max_players = status.players.max
    player_names = []
    if status.players.sample:
        player_names = [p.name for p in status.players.sample]

    embed = discord.Embed(
        title="🟢 Server Online",
        description=status.description if isinstance(status.description, str) else "Minecraft Server",
        color=discord.Color.green(),
    )
    embed.add_field(name="Players", value=f"{players_online}/{max_players}", inline=True)
    embed.add_field(name="Version", value=status.version.name, inline=True)
    embed.add_field(name="Latency", value=f"{status.latency:.0f}ms", inline=True)
    embed.add_field(name="Java", value=f"`{MC_HOST}:{MC_JAVA_PORT}`", inline=True)
    embed.add_field(name="Bedrock", value=f"`{MC_HOST}:{MC_BEDROCK_PORT}`", inline=True)

    if player_names:
        embed.add_field(name="Online", value=", ".join(player_names), inline=False)

    await ctx.send(embed=embed)


@bot.command(name="players")
async def player_list(ctx):
    """Show who's currently online."""
    status = await query_server()

    if status is None:
        await ctx.send("🔴 Server is offline.")
        return

    if not status.players.sample or status.players.online == 0:
        await ctx.send("No players online right now.")
        return

    names = [p.name for p in status.players.sample]
    embed = discord.Embed(
        title=f"👥 Players Online ({status.players.online}/{status.players.max})",
        description="\n".join(f"• {name}" for name in names),
        color=discord.Color.blue(),
    )
    await ctx.send(embed=embed)


@bot.command(name="serverstart")
@commands.has_permissions(administrator=True)
async def start_server(ctx):
    """Start the EC2 instance (admin only)."""
    if not EC2_INSTANCE_ID:
        await ctx.send("⚠️ EC2 instance ID not configured.")
        return

    try:
        ec2 = get_ec2_client()
        ec2.start_instances(InstanceIds=[EC2_INSTANCE_ID])
        await ctx.send("🚀 Starting the Minecraft server... Give it a couple minutes to boot up.")
    except Exception as e:
        await ctx.send(f"❌ Failed to start server: {e}")


@bot.command(name="serverstop")
@commands.has_permissions(administrator=True)
async def stop_server(ctx):
    """Stop the EC2 instance (admin only)."""
    if not EC2_INSTANCE_ID:
        await ctx.send("⚠️ EC2 instance ID not configured.")
        return

    try:
        ec2 = get_ec2_client()
        ec2.stop_instances(InstanceIds=[EC2_INSTANCE_ID])
        await ctx.send("🛑 Stopping the Minecraft server... World has been saved.")
    except Exception as e:
        await ctx.send(f"❌ Failed to stop server: {e}")


@bot.command(name="ip")
async def show_ip(ctx):
    """Show server connection info."""
    embed = discord.Embed(title="🌐 Server Connection Info", color=discord.Color.purple())
    embed.add_field(name="☕ Java Edition", value=f"`{MC_HOST}:{MC_JAVA_PORT}`", inline=False)
    embed.add_field(name="📱 Bedrock Edition", value=f"Address: `{MC_HOST}`\nPort: `{MC_BEDROCK_PORT}`", inline=False)
    embed.set_footer(text="Bedrock = Xbox, PlayStation, Switch, iOS, Android, Windows 10")
    await ctx.send(embed=embed)


RCON_PASSWORD = os.getenv("RCON_PASSWORD", "mc-rcon-2026")
RCON_PORT = int(os.getenv("RCON_PORT", "25575"))


def rcon_command(cmd):
    """Send a command via RCON and return the response."""
    try:
        from mcrcon import MCRcon
        with MCRcon(MC_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            return mcr.command(cmd)
    except Exception as e:
        return None


@bot.command(name="coords")
async def player_coords(ctx):
    """Show coordinates of all online players."""
    status = await query_server()

    if status is None:
        await ctx.send("🔴 Server is offline.")
        return

    if not status.players.sample or status.players.online == 0:
        await ctx.send("No players online right now.")
        return

    names = [p.name for p in status.players.sample]
    embed = discord.Embed(
        title="📍 Player Coordinates",
        color=discord.Color.gold(),
    )

    for name in names:
        result = rcon_command(f"data get entity {name} Pos")
        if result and "[" in result:
            # Parse [x, y, z] from response
            try:
                coords_str = result[result.index("["):result.index("]")+1]
                coords_str = coords_str.replace("[", "").replace("]", "")
                parts = coords_str.split(",")
                x = int(float(parts[0].strip().rstrip("d")))
                y = int(float(parts[1].strip().rstrip("d")))
                z = int(float(parts[2].strip().rstrip("d")))
                embed.add_field(name=name, value=f"X: {x}  Y: {y}  Z: {z}", inline=False)
            except (ValueError, IndexError):
                embed.add_field(name=name, value="Could not read position", inline=False)
        else:
            embed.add_field(name=name, value="Could not read position", inline=False)

    await ctx.send(embed=embed)

def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


@bot.command(name="ask")
async def ask_ai(ctx, *, question: str):
    """Ask an AI a Minecraft question."""
    async with ctx.typing():
        try:
            import json
            bedrock = get_bedrock_client()
            response = bedrock.invoke_model(
                modelId="us.amazon.nova-pro-v1:0",
                body=json.dumps({
                    "inferenceConfig": {"maxTokens": 500},
                    "system": [{"text": "You are a helpful Minecraft expert. Give concise, practical answers about Minecraft gameplay, crafting, redstone, mobs, biomes, enchantments, and strategies. Keep answers under 300 words. If the question is not about Minecraft, politely redirect to Minecraft topics."}],
                    "messages": [{"role": "user", "content": [{"text": question}]}],
                }),
                contentType="application/json",
            )
            result = json.loads(response["body"].read())
            answer = result["output"]["message"]["content"][0]["text"]

            # Discord has a 2000 char limit, truncate if needed
            if len(answer) > 1900:
                answer = answer[:1900] + "..."

            embed = discord.Embed(
                title=f"🤖 {question[:100]}",
                description=answer,
                color=discord.Color.teal(),
            )
            embed.set_footer(text="Powered by AI • Ask me anything about Minecraft!")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Couldn't get an answer: {e}")


# --- Minecraft Tips ---
MINECRAFT_TIPS = [
    "💡 Torches placed on the left wall will always lead you back to the exit in a cave.",
    "💡 Crouch while placing blocks on edges to avoid falling off.",
    "💡 Beds explode in the Nether and End — use them as weapons against the Ender Dragon!",
    "💡 Fortune III on a diamond ore block can give you up to 4 diamonds.",
    "💡 You can put a carpet on a fence to make a gate only you can jump over — mobs can't.",
    "💡 Holding a shield blocks 100% of damage from most melee and projectile attacks.",
    "💡 Piglins won't attack you if you wear at least one piece of gold armor.",
    "💡 Water buckets are the best tool in the game — clutch falls, lava, and mob farms.",
    "💡 Villagers struck by lightning become witches. Protect your village!",
    "💡 Foxes can hold items in their mouths. Give one a sword and it'll use it in combat.",
    "💡 Composters turn excess crops into bone meal. Great for automatic farms.",
    "💡 Ender pearls can teleport you through walls if thrown at the right angle.",
    "💡 Smite V does more damage to undead mobs than Sharpness V.",
    "💡 You can use a boat to safely descend from any height — no fall damage.",
    "💡 Cats scare away creepers and phantoms. Keep them around your base!",
    "💡 Honey blocks don't stick to slime blocks — useful for complex redstone.",
    "💡 Respawn anchors work in the Nether like beds work in the Overworld.",
    "💡 Looting III on a sword increases rare mob drops significantly.",
    "💡 You can dye leather armor and combine colors for custom looks.",
    "💡 Scaffolding is the fastest way to build tall structures. Craft it with bamboo and string.",
]


@bot.command(name="weather")
async def mc_weather(ctx, setting: str = None):
    """Check or change in-game weather. Usage: !weather [clear|rain|thunder]"""
    if setting and setting.lower() in ("clear", "rain", "thunder"):
        result = rcon_command(f"weather {setting.lower()}")
        if result is not None:
            icons = {"clear": "☀️", "rain": "🌧️", "thunder": "⛈️"}
            await ctx.send(f"{icons.get(setting.lower(), '🌤️')} Weather set to **{setting.lower()}**")
        else:
            await ctx.send("🔴 Couldn't reach the server.")
    elif setting:
        await ctx.send("⚠️ Use `!weather clear`, `!weather rain`, or `!weather thunder`")
    else:
        await ctx.send("🌤️ Current weather can't be queried via RCON.\nUse `!weather clear`, `!weather rain`, or `!weather thunder` to set it.")


@bot.command(name="time")
async def mc_time(ctx, setting: str = None):
    """Check or set in-game time. Usage: !time [day|night|noon|midnight]"""
    if setting and setting.lower() in ("day", "night", "noon", "midnight"):
        result = rcon_command(f"time set {setting.lower()}")
        if result is not None:
            icons = {"day": "🌅", "night": "🌙", "noon": "☀️", "midnight": "🌑"}
            await ctx.send(f"{icons.get(setting.lower(), '🕐')} Time set to **{setting.lower()}**")
        else:
            await ctx.send("🔴 Couldn't reach the server.")
    else:
        result = rcon_command("time query daytime")
        if result:
            try:
                ticks = int(result.split()[-1])
                hours = (ticks // 1000 + 6) % 24
                minutes = (ticks % 1000) * 60 // 1000
                period = "AM" if hours < 12 else "PM"
                display_hour = hours % 12 or 12
                phase = "☀️ Day" if 6 <= hours < 18 else "🌙 Night"
                await ctx.send(f"🕐 In-game time: **{display_hour}:{minutes:02d} {period}** ({phase})")
            except (ValueError, IndexError):
                await ctx.send(f"🕐 Server says: {result}")
        else:
            await ctx.send("🔴 Couldn't reach the server.")


@bot.command(name="tip")
async def mc_tip(ctx):
    """Get a random Minecraft tip."""
    tip = random.choice(MINECRAFT_TIPS)
    embed = discord.Embed(
        title="🎮 Minecraft Tip",
        description=tip,
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed)


@bot.command(name="roll")
async def dice_roll(ctx, dice: str = "1d6"):
    """Roll dice. Usage: !roll 2d20, !roll 1d6, !roll 3d8"""
    try:
        parts = dice.lower().split("d")
        num_dice = int(parts[0]) if parts[0] else 1
        sides = int(parts[1])

        if num_dice < 1 or num_dice > 20 or sides < 2 or sides > 100:
            await ctx.send("⚠️ Keep it between 1-20 dice with 2-100 sides.")
            return

        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls)

        if num_dice == 1:
            await ctx.send(f"🎲 You rolled a **{total}** (d{sides})")
        else:
            rolls_str = " + ".join(str(r) for r in rolls)
            await ctx.send(f"🎲 You rolled **{total}** ({rolls_str}) — {num_dice}d{sides}")
    except (ValueError, IndexError):
        await ctx.send("⚠️ Format: `!roll 2d20` (number of dice **d** sides)")


@bot.command(name="poll")
async def create_poll(ctx, *, question: str):
    """Create a quick yes/no poll. Usage: !poll Should we reset the nether?"""
    embed = discord.Embed(
        title="📊 Poll",
        description=question,
        color=discord.Color.orange(),
    )
    embed.set_footer(text=f"Asked by {ctx.author.display_name} • React to vote!")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await msg.add_reaction("🤷")


@bot.command(name="leaderboard")
async def leaderboard(ctx):
    """Show player stats from the server."""
    status = await query_server()
    if status is None:
        await ctx.send("🔴 Server is offline.")
        return

    if not status.players.sample or status.players.online == 0:
        await ctx.send("No players online to check stats for.")
        return

    names = [p.name for p in status.players.sample]
    embed = discord.Embed(
        title="🏆 Player Leaderboard",
        color=discord.Color.gold(),
    )

    # Try to get kills, deaths, and playtime for each player
    stats = []
    for name in names:
        kills_result = rcon_command(f"scoreboard players get {name} playerKillCount") or ""
        deaths_result = rcon_command(f"scoreboard players get {name} deathCount") or ""

        kills = 0
        deaths = 0
        try:
            if "has" in kills_result:
                kills = int(kills_result.split()[-1])
        except (ValueError, IndexError):
            pass
        try:
            if "has" in deaths_result:
                deaths = int(deaths_result.split()[-1])
        except (ValueError, IndexError):
            pass

        kd = f"{kills / deaths:.1f}" if deaths > 0 else f"{kills}.0"
        stats.append((name, kills, deaths, kd))

    # Sort by kills descending
    stats.sort(key=lambda x: x[1], reverse=True)

    for i, (name, kills, deaths, kd) in enumerate(stats):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        embed.add_field(
            name=f"{medal} {name}",
            value=f"⚔️ Kills: {kills} | 💀 Deaths: {deaths} | K/D: {kd}",
            inline=False,
        )

    embed.set_footer(text="Stats from scoreboard objectives • Kill counts track player kills only")
    await ctx.send(embed=embed)


S3_BACKUP_BUCKET = os.getenv("S3_BACKUP_BUCKET", "minecraft-world-backups")


@bot.command(name="backup")
@commands.has_permissions(administrator=True)
async def manual_backup(ctx):
    """Trigger a manual world backup to S3 (admin only)."""
    await ctx.send("💾 Starting world backup... This may take a minute.")
    try:
        result = rcon_command("save-all")
        if result is None:
            await ctx.send("🔴 Couldn't reach the server for save.")
            return

        # Wait for save to complete
        await asyncio.sleep(5)

        # Trigger the backup script on the server via RCON say + we'll run it via SSH isn't possible
        # Instead, use S3 directly — run the backup command on the EC2 instance
        import subprocess
        proc = await asyncio.create_subprocess_exec(
            "ssh", "-i", "/home/ec2-user/.ssh/minecraft-key.pem",
            "-o", "StrictHostKeyChecking=no",
            "ec2-user@localhost",
            f"sudo /opt/minecraft/scripts/backup.sh {S3_BACKUP_BUCKET}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        if proc.returncode == 0:
            await ctx.send(f"✅ Backup complete! Saved to S3 bucket `{S3_BACKUP_BUCKET}`")
        else:
            # Fallback: try running the script directly (bot is on the same machine)
            proc2 = await asyncio.create_subprocess_exec(
                "sudo", "/opt/minecraft/scripts/backup.sh", S3_BACKUP_BUCKET,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout2, stderr2 = await asyncio.wait_for(proc2.communicate(), timeout=120)
            if proc2.returncode == 0:
                await ctx.send(f"✅ Backup complete! Saved to S3 bucket `{S3_BACKUP_BUCKET}`")
            else:
                error_msg = stderr2.decode()[:200] if stderr2 else "Unknown error"
                await ctx.send(f"❌ Backup failed: {error_msg}")
    except asyncio.TimeoutError:
        await ctx.send("❌ Backup timed out after 2 minutes.")
    except Exception as e:
        await ctx.send(f"❌ Backup failed: {e}")


@tasks.loop(seconds=30)
async def player_watch():
    """Poll server every 30s and announce joins/leaves."""
    global previous_players
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    status = await query_server()

    if status is None:
        if previous_players:
            previous_players.clear()
        return

    current_players: set[str] = set()
    if status.players.sample:
        current_players = {p.name for p in status.players.sample}

    joined = current_players - previous_players
    left = previous_players - current_players

    for name in joined:
        await channel.send(f"🟢 **{name}** joined the server! ({status.players.online} online)")

    for name in left:
        await channel.send(f"🔴 **{name}** left the server.")

    previous_players = current_players


@player_watch.before_loop
async def before_player_watch():
    await bot.wait_until_ready()


if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: Set DISCORD_TOKEN in your .env file")
        exit(1)
    bot.run(TOKEN)
