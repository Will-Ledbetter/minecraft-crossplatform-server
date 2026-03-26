#!/bin/bash
# Automated Minecraft world backup to S3 (systemd version)
set -e

BUCKET="minecraft-world-backups-257641257020"
SERVER_DIR="/opt/minecraft/server"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="world-backup-${TIMESTAMP}.tar.gz"

echo "[$(date)] Starting backup..."

# Create backup from world directories
cd /tmp
tar -czf "${BACKUP_FILE}" -C "$SERVER_DIR" world world_nether world_the_end 2>/dev/null || \
tar -czf "${BACKUP_FILE}" -C "$SERVER_DIR" world

# Upload to S3
aws s3 cp "/tmp/${BACKUP_FILE}" "s3://${BUCKET}/backups/${BACKUP_FILE}" --region us-east-1

# Cleanup
rm -f "/tmp/${BACKUP_FILE}"

echo "[$(date)] Backup uploaded: s3://${BUCKET}/backups/${BACKUP_FILE}"
