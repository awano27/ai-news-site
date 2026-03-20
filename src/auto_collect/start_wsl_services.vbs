Set objShell = CreateObject("WScript.Shell")
' Start WSL services (cron, docker, ollama)
objShell.Run "wsl -d Ubuntu -- bash -c ""sudo service cron start && sudo service docker start && OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &""", 0, True
' Wait 10 seconds for services to start
WScript.Sleep 10000
' Run auto-collection if today's file doesn't exist yet
objShell.Run "wsl -d Ubuntu -- bash -c ""test -f /mnt/c/develop/ai-news-site/input/day/$(date +%m%d).txt || (cd /mnt/c/develop/ai-news-site && python3 -m src.auto_collect.main >> /mnt/c/develop/ai-news-site/logs/auto_collect/$(date +%Y%m%d).log 2>&1)""", 0, False
