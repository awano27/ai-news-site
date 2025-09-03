#!/usr/bin/env python3
import subprocess
import os

# Change to the correct directory
os.chdir(r'C:\Users\yoshitaka\ai-news-site')

print("Adding 9/4 slide to git...")
subprocess.run(['git', 'add', 'presentations/day_slides/day_slide_2025_09_04.html'], check=True)

print("Checking git status...")
result = subprocess.run(['git', 'status'], capture_output=True, text=True)
print(result.stdout)

print("Committing changes...")
commit_msg = """feat(9/4): add Gaia AI Phone slide - world's first on-device AI smartphone

- Complete slide with privacy-focused features and Web3 integration
- Comprehensive technical specs and implementation guide  
- Business use cases for PDM/CS workflows
- Total score: 90.5/100 with breakdown
- Links to official resources and documentation

🤖 Generated with Claude Code"""

subprocess.run(['git', 'commit', '-m', commit_msg], check=True)

print("Pushing to GitHub...")
subprocess.run(['git', 'push', 'origin', 'main'], check=True)

print("✅ Successfully deployed 9/4 slide!")