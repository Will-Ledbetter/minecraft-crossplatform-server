# Minecraft AI Bot

An AI-powered Minecraft player that joins your server and responds to natural language commands in chat. Built with Mineflayer and Amazon Bedrock Nova Pro.

## How It Works

The bot connects to a Minecraft server as a real player using the Mineflayer protocol library. When a player mentions the bot's name in chat, the message is sent to Amazon Bedrock (Nova Pro) which interprets the natural language and returns a structured game action. The bot then executes it using A* pathfinding, block interaction, and entity tracking.

The LLM only handles language understanding. All gameplay — navigation, mining, combat, inventory — is deterministic code, keeping API costs minimal (~$5-15/month).

## Features

- **Resource Collection** — Chops trees, mines ores, gathers materials with smart exploration
- **Navigation** — Pathfinds to players, coordinates, or home base
- **Combat** — Attacks mobs on command and defends itself automatically
- **Inventory** — Deposits items into a home chest, drops items for players
- **Crafting** — Crafts items at crafting tables
- **Smart Behavior** — Uses doors, closes them behind, sleeps in beds, eats when low on health
- **Surface Awareness** — Stays above ground for surface blocks, goes underground for ores
- **Auto-Return** — Returns to home base after completing tasks

## Commands

Talk to the bot in Minecraft chat by saying its name:

| Command | What it does |
|---|---|
| `Bot, come here` | Walks to you |
| `Bot, follow me` | Follows you around |
| `Bot, go get 10 oak_log` | Collects resources |
| `Bot, go to 100 64 -200` | Walks to coordinates |
| `Bot, attack zombie` | Fights a specific mob |
| `Bot, deposit` | Dumps inventory into home chest |
| `Bot, drop 5 oak_log` | Drops items at your feet |
| `Bot, craft crafting_table` | Crafts an item |
| `Bot, home` | Returns to base |
| `Bot, sleep` | Goes to bed at home |
| `Bot, status` | Reports health, position, inventory |
| `Bot, stop` | Cancels current task |

## Setup

### Prerequisites
- Node.js 18+
- A Minecraft server (Paper/Spigot)
- A Minecraft Java Edition account for the bot
- AWS account with Bedrock access (Nova Pro model)

### Installation

```bash
# Clone and install
cd ai-bot
npm install

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
node bot.js
```

### First Run — Microsoft Auth

Since Minecraft uses Microsoft authentication, the bot will prompt you on first run:

```
To sign in, use a web browser to open https://www.microsoft.com/link and use the code XXXXXXXX
```

Go to that URL, enter the code, and sign in with the Microsoft account that owns the bot's Minecraft license. This only needs to be done once.

### Running as a Service (Linux)

```bash
sudo cp minecraft-aibot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable minecraft-aibot
sudo systemctl start minecraft-aibot
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MC_HOST` | `localhost` | Minecraft server address |
| `MC_PORT` | `25565` | Minecraft server port |
| `BOT_USERNAME` | `AISteve` | Bot's Minecraft username |
| `BOT_NAME` | `Steve` | Name players use in chat to talk to the bot |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `HOME_X` | `0` | Home chest X coordinate |
| `HOME_Y` | `64` | Home chest Y coordinate |
| `HOME_Z` | `0` | Home chest Z coordinate |

## LinkedIn Post

[See it in action](https://www.linkedin.com/posts/will-ledbetter-114318167_what-if-you-could-have-an-assitant-in-minecraft-activity-7444149600137113600-OTAl?utm_source=share&utm_medium=member_desktop&rcm=ACoAACe8W6ABz_yW6tZUwf4zTku75hhXakj6lxU)

## Architecture

```
Player Chat → Mineflayer (protocol) → Amazon Bedrock Nova Pro → Structured Action → Game Execution
```

- **Mineflayer** — Minecraft protocol library, handles connection, world state, physics
- **mineflayer-pathfinder** — A* pathfinding for navigation
- **Amazon Bedrock Nova Pro** — Natural language understanding (command interpretation only)
- **Node.js** — Runtime

## Cost

The LLM is only called when a player gives a command. Typical usage:
- ~$0.001-0.003 per command (Bedrock Nova Pro)
- ~200-500 commands per play session
- **~$5-15/month** for casual use

## Tech Stack

Node.js, Mineflayer, mineflayer-pathfinder, AWS Bedrock (Nova Pro), dotenv
