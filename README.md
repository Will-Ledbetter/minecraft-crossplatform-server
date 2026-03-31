# Minecraft Cross-Platform Server on AWS

A Minecraft server running on AWS EC2 that supports **all platforms simultaneously**:
- Java Edition (PC/Mac/Linux) — port 25565
- Bedrock Edition (Xbox, PlayStation, Switch, iOS, Android, Windows 10) — port 19132

Uses **GeyserMC** to bridge Bedrock players into the Java server.

## LinkedIn Post

[See it in action](https://www.linkedin.com/posts/will-ledbetter-114318167_minecraft-is-back-for-me-i-recently-heard-activity-7442794850284081152-zq0f?utm_source=share&utm_medium=member_desktop&rcm=ACoAACe8W6ABz_yW6tZUwf4zTku75hhXakj6lxU)

## Architecture
- **EC2 Instance** (t3.medium or larger) with Elastic IP
- **Paper MC** server (high-performance Java server)
- **GeyserMC + Floodgate** plugins for cross-platform support
- **S3** for automated world backups
- **CloudFormation** for infrastructure as code

## Quick Start

1. Configure your settings in `config/server.env`
2. Deploy infrastructure: `aws cloudformation deploy --template-file infra/cloudformation.yaml --stack-name minecraft-server --capabilities CAPABILITY_IAM`
3. SSH into the instance and the setup script runs automatically via UserData

## Connecting
- **Java Edition**: `<elastic-ip>:25565`
- **Bedrock Edition**: Add server with `<elastic-ip>` port `19132`
