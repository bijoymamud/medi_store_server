#!/bin/bash
# MediShop Automated PostgreSQL Database Backup Script
# Can be scheduled via a Cron job in production (e.g. daily at midnight)

# Configurations
DB_USER=${POSTGRES_USER:-"postgres"}
DB_NAME=${POSTGRES_DB:-"medistore"}
DB_HOST=${POSTGRES_HOST:-"localhost"}
BACKUP_DIR=${BACKUP_DIR:-"./backups"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/medistore_backup_$TIMESTAMP.sql"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting database backup at $(date)..."

# Execute pg_dump
# If running inside docker container, we can use pg_dump directly.
# If running on host, it connects to DB_HOST.
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -F p -f "$BACKUP_FILE"

if [ $? -eq 0 ]; then
  echo "Backup successfully created: $BACKUP_FILE"
  
  # Compress backup to save disk space
  gzip "$BACKUP_FILE"
  echo "Compressed backup: ${BACKUP_FILE}.gz"
  
  # Housekeeping: Keep only the last 7 days of backups
  find "$BACKUP_DIR" -type f -name "*.gz" -mtime +7 -delete
  echo "Cleaned up backups older than 7 days."
else
  echo "Error: Database backup failed!" >&2
  exit 1
fi
