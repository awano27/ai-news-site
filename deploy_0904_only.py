#!/usr/bin/env python3
import subprocess
import os

# Change to the correct directory
os.chdir(r'C:\Users\yoshitaka\ai-news-site')

print("Resetting staged files...")
subprocess.run(['git', 'reset'], check=True)

print("Adding only 9/4 slide to git...")
subprocess.run(['git', 'add', 'presentations/day_slides/day_slide_2025_09_04.html'], check=True)

print("Checking git status...")
result = subprocess.run(['git', 'status'], capture_output=True, text=True)
print(result.stdout)

print("Committing 9/4 slide...")
commit_msg = "feat(9/4): add Gaia AI Phone slide - world's first on-device AI smartphone"

subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

print("Pushing to GitHub...")
subprocess.run(['git', 'push', 'origin', 'main'], check=True)

print("✅ Successfully deployed 9/4 slide!")