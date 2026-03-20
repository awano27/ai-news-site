#!/bin/bash
# Daily AI News Auto-Collector + Weekly/Monthly Reports
# crontab entries:
#   0 22 * * *   daily collection (7:00 AM JST)
#   30 22 * * 0  weekly report (Sunday 7:30 AM JST)
#   0 23 1 * *   monthly report (1st of month 8:00 AM JST)

set -e

PROJECT_DIR="/mnt/c/develop/ai-news-site"
LOG_DIR="${PROJECT_DIR}/logs/auto_collect"
LOG_FILE="${LOG_DIR}/$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "$(date): Starting Ollama..." >> "$LOG_FILE"
    OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve >> /tmp/ollama.log 2>&1 &
    sleep 5
fi

cd "$PROJECT_DIR"

case "${1:-daily}" in
    daily)
        echo "$(date): Starting daily collection" >> "$LOG_FILE"
        python3 -m src.auto_collect.main >> "$LOG_FILE" 2>&1
        echo "$(date): Daily collection complete" >> "$LOG_FILE"
        ;;
    weekly)
        echo "$(date): Generating weekly report" >> "$LOG_FILE"
        python3 -c "from src.auto_collect.report_generator import generate_weekly_report; generate_weekly_report()" >> "$LOG_FILE" 2>&1
        echo "$(date): Weekly report complete" >> "$LOG_FILE"
        ;;
    monthly)
        echo "$(date): Generating monthly report" >> "$LOG_FILE"
        python3 -c "from src.auto_collect.report_generator import generate_monthly_report; generate_monthly_report()" >> "$LOG_FILE" 2>&1
        echo "$(date): Monthly report complete" >> "$LOG_FILE"
        ;;
esac
