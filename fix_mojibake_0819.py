import os

def fix_mojibake(file_path):
    print(f"Fixing {file_path}...")
    try:
        # Read the file as UTF-8 (which contains the mojibake characters)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # The mojibake happened because UTF-8 bytes were interpreted as Shift-JIS.
        # To fix it: content -> encode to Shift-JIS -> decode from UTF-8
        # However, some characters might not be reversible if they aren't in Shift-JIS.
        # We use 'replace' or 'ignore' to handle potential errors, but ideally 'strict' should work for classic mojibake.
        
        # We need to skip the UTF-8 BOM if present in the string
        if content.startswith('\ufeff'):
            content = content[1:]

        fixed_content = content.encode('shift-jis', errors='replace').decode('utf-8', errors='replace')
        
        # Write back as UTF-8 without BOM (or with, depending on project style, but UTF-8 is safer)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("Successfully fixed.")
    except Exception as e:
        print(f"Error fixing file: {e}")

if __name__ == "__main__":
    target = r"C:\develop\ai-news-site\presentations\day_slides\day_slide_2025_08_19.html"
    if os.path.exists(target):
        fix_mojibake(target)
    else:
        print(f"File not found: {target}")
