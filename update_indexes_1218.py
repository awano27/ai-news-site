import os

def update_indexes_1218():
    index_path = "presentations/day_slides_index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # New entry for 12/18
    new_entry = '<li><a href="day_slides/day_slide_2025_12_18.html" aria-describedby="slide-2025-12-18"><span class="date">2025/12/18</span><span class="slide-title">Gemini 3 Flash: Google、知能と速度を両立した新モデル</span></a></li>'
    
    # Insert at the top of the list (after the <ul> tag or before the first <li>)
    # Looking for the first <li> inside <ul class="slides">
    marker = '<ul class="slides">'
    if marker in content:
        parts = content.split(marker)
        # Find the first <li> in the second part and insert before it
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
    update_indexes_1218()
