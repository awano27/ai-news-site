#!/usr/bin/env python3
"""
Batch update all day slides with the perfect scrolling fixes from the 08/27 template.
This script applies viewport changes, scrolling CSS, and Reveal.js configuration updates.
"""

import os
import re
from pathlib import Path

# List of slides that need updating (from the original request)
SLIDES_TO_UPDATE = [
    "day_slide_2025_08_04.html",  # Already updated
    "day_slide_2025_08_05.html",  # Already updated 
    "day_slide_2025_08_06.html",  # Already updated
    "day_slide_2025_08_08.html",
    "day_slide_2025_08_09.html",
    "day_slide_2025_08_10.html",
    "day_slide_2025_08_11.html",
    "day_slide_2025_08_12.html",
    "day_slide_2025_08_13.html",
    "day_slide_2025_08_14.html",
    "day_slide_2025_08_15.html",
    "day_slide_2025_08_16.html",
    "day_slide_2025_08_17.html",
    "day_slide_2025_08_18.html",
    "day_slide_2025_08_19.html",
    "day_slide_2025_08_20.html",
    "day_slide_2025_08_22.html",
    "day_slide_2025_07_30.html",
    "day_slide_2025_08_02.html"
]

# Perfect scrolling CSS to add
SCROLLING_CSS = """        
        /* Scrolling fixes and responsive improvements */
        html, body {
            height: 100%;
            overflow-y: auto !important;
            overflow-x: hidden;
            -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
        }
        
        .reveal {
            position: relative !important;
            height: auto !important;
            min-height: 100vh;
            overflow: visible !important;
        }
        
        .reveal .slides {
            position: relative !important;
            width: 100% !important;
            height: auto !important;
            top: 0 !important;
            left: 0 !important;
            margin: 0 !important;
            padding: 20px !important;
            text-align: center !important;
            overflow: visible !important;
            transform: none !important;
        }
        
        .reveal .slides section {
            position: relative !important;
            width: 100% !important;
            max-width: 1200px !important;
            height: auto !important;
            min-height: auto !important;
            top: auto !important;
            left: auto !important;
            margin: 0 auto 30px auto !important;
            padding: 20px !important;
            display: block !important;
            overflow: visible !important;
            transform: none !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        
        /* Hide reveal.js controls for scrolling mode */
        .reveal .controls,
        .reveal .progress,
        .reveal .playback,
        .reveal .slide-number {
            display: none !important;
        }
        
        /* Responsive design improvements */
        @media screen and (max-width: 768px) {
            .reveal .slides section {
                padding: 15px !important;
                margin: 0 10px 20px 10px !important;
            }
            
            .reveal h1 {
                font-size: 1.8em !important;
            }
            
            .reveal h2 {
                font-size: 1.5em !important;
            }
            
            .reveal h3 {
                font-size: 1.3em !important;
            }
            
            .stats-grid {
                grid-template-columns: 1fr !important;
            }
        }
        
        @media screen and (max-width: 480px) {
            .reveal .slides section {
                padding: 10px !important;
                margin: 0 5px 15px 5px !important;
            }
            
            .reveal h1 {
                font-size: 1.5em !important;
            }
            
            .content-card {
                padding: 1rem !important;
            }
        }
"""

# Perfect Reveal.initialize configuration
PERFECT_REVEAL_CONFIG = """        Reveal.initialize({
            embedded: true,
            width: '100%',
            height: '100%',
            margin: 0,
            minScale: 1,
            maxScale: 1,
            hash: false,
            controls: false,  // Disable slide navigation controls for scrolling
            controlsLayout: 'edges',
            controlsBackArrows: 'faded',
            progress: false,  // Disable progress bar for scrolling
            center: false,
            transition: 'none',  // Disable transitions for scrolling
            backgroundTransition: 'none',
            keyboard: false,  // Disable keyboard navigation for scrolling
            overview: false,  // Disable overview mode
            touch: false,     // Disable touch navigation for scrolling
            loop: false,
            fragments: false  // Disable fragment animations
        });"""

def update_slide_file(file_path):
    """Update a single slide file with scrolling fixes"""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"Processing {file_path.name}...")
        
        # 1. Fix viewport meta tag (change user-scalable=no to user-scalable=yes)
        content = re.sub(
            r'user-scalable=no', 
            'user-scalable=yes', 
            content
        )
        
        # Also handle cases where there's maximum-scale with user-scalable=no
        content = re.sub(
            r'maximum-scale=1\.0,\s*user-scalable=no', 
            'user-scalable=yes', 
            content
        )
        
        # 2. Add scrolling CSS before the closing </style> tag
        # Look for various patterns of style closing
        if '</style>' in content:
            # Find the last occurrence of </style> and add CSS before it
            style_end = content.rfind('</style>')
            if style_end != -1:
                content = content[:style_end] + SCROLLING_CSS + '\n    </style>' + content[style_end + 8:]
        
        # 3. Replace Reveal.initialize configuration
        # Look for various Reveal.initialize patterns
        reveal_pattern = r'Reveal\.initialize\s*\(\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}\s*\)\s*;'
        if re.search(reveal_pattern, content, re.DOTALL):
            content = re.sub(reveal_pattern, PERFECT_REVEAL_CONFIG + ';', content, flags=re.DOTALL)
        
        # Write the updated content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Successfully updated {file_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing {file_path.name}: {e}")
        return False

def main():
    """Main function to batch update all slides"""
    presentations_dir = Path("presentations/day_slides")
    
    if not presentations_dir.exists():
        print(f"Error: {presentations_dir} directory not found!")
        return
    
    updated_count = 0
    skipped_count = 0
    
    # Process all slides in the list (skip already updated ones)
    already_updated = ["day_slide_2025_08_04.html", "day_slide_2025_08_05.html", "day_slide_2025_08_06.html"]
    
    for slide_name in SLIDES_TO_UPDATE:
        if slide_name in already_updated:
            print(f"⏭ Skipping {slide_name} (already updated)")
            skipped_count += 1
            continue
            
        file_path = presentations_dir / slide_name
        
        if not file_path.exists():
            print(f"⚠ Warning: {slide_name} not found, skipping")
            continue
        
        if update_slide_file(file_path):
            updated_count += 1
    
    print(f"\n🎉 Batch update completed!")
    print(f"Updated: {updated_count} slides")
    print(f"Skipped: {skipped_count} slides (already updated)")
    print(f"Total processed: {updated_count + skipped_count} slides")

if __name__ == "__main__":
    main()