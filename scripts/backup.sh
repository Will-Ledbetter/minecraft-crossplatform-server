#!/bin/bash
# Automated Minecraft world backup to S3
set -e

BACKUP_BUCKET="$1"
SERVER_DIR="/opt/minecraft/server"
BACKUP_DIR="/tmp/mc-backup"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="world-backup-${TIMESTAMP}.tar.gz"

if [ -z "$BACKUP_BUCKET" ]; then
  echo "Usage: $0 <s3-bucket-name>"
  exit 1
fi

echo "[$(date)] Starting backup..."

# Tell server to save and disable autosave temporarily
screen -S minecraft -p 0 -X stuff "say §eBackup starting...$(printf '\r')" 2>/dev/null || true
screen -S minecraft -p 0 -X stuff "save-all$(printf '\r')" 2>/dev/null || true
sleep 5
screen -S minecraft -p 0 -X stuff "save-off$(printf '\r')" 2>/dev/null || true
sleep 2

# Create backup
mkdir -p "$BACKUP_DIR"
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" -C "$SERVER_DIR" world world_nether world_the_end 2>/dev/null || \
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" -C "$SERVER_DIR" world

# Re-enable autosave
screen -S minecraft -p 0 -X stuff "save-on$(printf '\r')" 2>/dev/null || true
screen -S minecraft -p 0 -X stuff "say §aBackup complete!$(printf '\r')" 2>/dev/null || true

# Upload to S3
aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" "s3://${BACKUP_BUCKET}/backups/${BACKUP_FILE}"

# Cleanup local temp
rm -rf "$BACKUP_DIR"

echo "[$(date)] Backup uploaded: s3://${BACKUP_BUCKET}/backups/${BACKUP_FILE}"
