#!/usr/bin/env python3
"""
Batch standardize remaining day slides with the 08/27 excellent styling
"""

import os
import re

def standardize_slide(filepath):
    """Apply the three standardization changes to a slide"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Change 1: Add scrolling CSS before closing </style>
    scrolling_css = """
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
        }"""
    
    # Find chart-container and add CSS before closing </style>
    chart_pattern = r'(\s+\.chart-container\s*\{[^}]+\})\s*\n\s*\n\s*\n\s*\n\s*</style>'
    if re.search(chart_pattern, content):
        content = re.sub(chart_pattern, r'\1' + scrolling_css + '\n    </style>', content)
    
    # Change 2: Replace Reveal.initialize configuration
    new_reveal_config = """        Reveal.initialize({
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
    
    # Replace Reveal.initialize block
    reveal_pattern = r'        Reveal\.initialize\(\{[^}]*hash: true,[^}]*controls: true,[^}]*plugins: \[RevealMarkdown, RevealHighlight, RevealNotes\]\s*\}\);'
    content = re.sub(reveal_pattern, new_reveal_config, content, flags=re.DOTALL)
    
    # Write the updated content back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

# List of remaining slides to process
slides = [
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

base_path = "presentations/day_slides"
success_count = 0

for slide in slides:
    filepath = os.path.join(base_path, slide)
    if os.path.exists(filepath):
        try:
            standardize_slide(filepath)
            print(f"✅ Standardized {slide}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to standardize {slide}: {e}")
    else:
        print(f"⚠️  File not found: {slide}")

print(f"\n🎉 Successfully standardized {success_count} slides!")