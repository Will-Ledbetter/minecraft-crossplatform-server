#!/bin/bash
# Install BedrockConnect DNS server on the Minecraft EC2 instance
# This lets Xbox/Switch players connect without relying on public DNS
# Run this via SSH on the EC2 instance

set -e

echo "=== Installing BedrockConnect ==="

# Create directory
sudo mkdir -p /opt/bedrockconnect
cd /opt/bedrockconnect

# Download latest BedrockConnect
LATEST_URL=$(curl -s https://api.github.com/repos/Pugmatt/BedrockConnect/releases/latest | python3 -c "
import sys, json
assets = json.load(sys.stdin)['assets']
for a in assets:
    if a['name'].endswith('.jar'):
        print(a['browser_download_url'])
        break
")

echo "Downloading: $LATEST_URL"
sudo curl -L -o BedrockConnect.jar "$LATEST_URL"

# Create config with our server pre-loaded
sudo tee serverlist.json > /dev/null << 'EOF'
[
  {
    "name": "Our Minecraft Server",
    "iconUrl": "",
    "address": "127.0.0.1",
    "port": 19132
  }
]
EOF

# Create systemd service
sudo tee /etc/systemd/system/bedrockconnect.service > /dev/null << 'SERVICE'
[Unit]
Description=BedrockConnect DNS Server
After=network.target

[Service]
User=root
WorkingDirectory=/opt/bedrockconnect
ExecStart=/usr/bin/java -jar BedrockConnect.jar nodb=true custom_servers=/opt/bedrockconnect/serverlist.json
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable bedrockconnect
sudo systemctl start bedrockconnect

echo "=== BedrockConnect installed and running ==="
echo "Console players can use this server's IP as their DNS server"
