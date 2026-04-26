#!/bin/bash
# Daily AI News Auto-Collector + Weekly/Monthly Reports
#
# Role: secondary (override) path. Cloud workflow at 06:00 JST already
# produced today's report without X bookmarks. This script pulls that
# commit, regenerates via local Ollama (which DOES read the Obsidian
# vault for X bookmarks), and pushes the override so the X tab fills in.
#
# crontab entries:
#   0 23 * * *   daily collection (8:00 AM JST — after Cloud's 06:00 commit)
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

# Pull Cloud's commit before regenerating. Without this, the local push
# below would be rejected as non-fast-forward whenever Cloud already ran.
git pull --rebase --autostash >> "$LOG_FILE" 2>&1 || {
    echo "$(date): git pull failed — aborting to avoid divergent push" >> "$LOG_FILE"
    exit 1
}

case "${1:-daily}" in
    daily)
        echo "$(date): Starting daily collection (override)" >> "$LOG_FILE"
        # --force: regenerate over Cloud's commit so X bookmarks fill in.
        python3 -m src.auto_collect.main --force >> "$LOG_FILE" 2>&1
        echo "$(date): Daily collection complete" >> "$LOG_FILE"

        # Push the local override. Same path set as the Cloud workflow.
        if [ -n "$(git status --porcelain)" ]; then
            git add input/day/*.txt presentations/auto_daily_report.html \
                    presentations/auto_daily_report.json \
                    presentations/daily_reports/ \
                    public-pages/api/auto_daily_report/ \
                    public-pages/news/ daily-news/ 2>/dev/null || true
            git add -A presentations/ input/ public-pages/ daily-news/ 2>/dev/null || true
            git commit -m "chore(report): local override $(date +%F)" >> "$LOG_FILE" 2>&1
            git push >> "$LOG_FILE" 2>&1 && \
                echo "$(date): Pushed local override" >> "$LOG_FILE" || \
                echo "$(date): Push failed (manual resolution needed)" >> "$LOG_FILE"
        else
            echo "$(date): No changes after local run (Cloud's output already current)" >> "$LOG_FILE"
        fi
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
