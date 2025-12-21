import os

def update_indexes_1221():
    index_path = "presentations/day_slides_index.html"
    if not os.path.exists(index_path):
        print(f"Index file not found: {index_path}")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # New entry for 12/21
    new_entry = '<li><a href="day_slides/day_slide_2025_12_21.html" aria-describedby="slide-2025-12-21"><span class="date">2025/12/21</span><span class="slide-title">FunctionGemma: 実用的なオンデバイスAIエージェント</span></a></li>'
    
    # Check if already exists to avoid duplication
    if 'day_slide_2025_12_21.html' in content:
        print("Entry already exists in index.")
        return

    marker = '<ul class="slides">'
    if marker in content:
        parts = content.split(marker)
        second_part = parts[1]
        li_marker = '<li>'
        if li_marker in second_part:
            li_parts = second_part.split(li_marker, 1)
            updated_content = parts[0] + marker + li_parts[0] + new_entry + "\n" + li_marker + li_parts[1]
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print(f"Updated {index_path}")
        else:
            print("Could not find <li> marker in index file.")
    else:
        print("Could not find <ul class=\"slides\"> marker in index file.")

if __name__ == "__main__":
    update_indexes_1221()
