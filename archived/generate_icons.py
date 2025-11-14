#!/usr/bin/env python3
"""
Generate app icons for PWA installation
Creates icons in multiple sizes with a simple, recognizable design
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory if it doesn't exist
ICONS_DIR = os.path.join(os.path.dirname(__file__), "media", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# Icon sizes needed for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
MASKABLE_SIZES = [192, 512]

# App colors (matching manifest)
BACKGROUND_COLOR = (20, 13, 82)  # #140d52 - dark purple
ACCENT_COLOR = (230, 87, 255)     # #e657ff - bright purple/pink
TEXT_COLOR = (255, 255, 255)      # white

def create_icon(size, is_maskable=False):
    """Create a single icon with the app logo/symbol"""
    # Create image with background
    img = Image.new('RGB', (size, size), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    
    # For maskable icons, add safe zone padding (20%)
    padding = int(size * 0.2) if is_maskable else int(size * 0.1)
    inner_size = size - (2 * padding)
    
    # Draw a stylized "P" for Parlay in the center
    # Using geometric shapes for consistency across sizes
    
    # Calculate dimensions based on inner size
    letter_width = inner_size * 0.6
    letter_height = inner_size * 0.8
    stroke_width = max(int(inner_size * 0.15), 2)
    
    # Center position
    center_x = size // 2
    center_y = size // 2
    
    # Draw vertical line of "P"
    x1 = center_x - letter_width // 4
    y1 = center_y - letter_height // 2
    x2 = x1
    y2 = center_y + letter_height // 2
    draw.line([(x1, y1), (x2, y2)], fill=ACCENT_COLOR, width=stroke_width)
    
    # Draw rounded top of "P"
    bubble_radius = letter_width // 2
    bubble_center_x = x1 + bubble_radius
    bubble_center_y = y1 + bubble_radius
    
    # Draw circle for the bubble part
    bbox = [
        bubble_center_x - bubble_radius,
        bubble_center_y - bubble_radius,
        bubble_center_x + bubble_radius,
        bubble_center_y + bubble_radius
    ]
    draw.ellipse(bbox, outline=ACCENT_COLOR, width=stroke_width)
    
    # Add a subtle dollar sign or money symbol if size is large enough
    if size >= 192:
        symbol_size = inner_size * 0.25
        symbol_x = center_x + letter_width // 4
        symbol_y = center_y + letter_height // 4
        
        try:
            # Try to use a system font
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(symbol_size))
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        draw.text((symbol_x, symbol_y), "$", fill=ACCENT_COLOR, font=font, anchor="mm")
    
    return img

def generate_all_icons():
    """Generate all required icon sizes"""
    print("Generating PWA app icons...")
    
    # Generate regular icons
    for size in ICON_SIZES:
        icon = create_icon(size, is_maskable=False)
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(ICONS_DIR, filename)
        icon.save(filepath, "PNG")
        print(f"✓ Created {filename}")
    
    # Generate maskable icons (for Android adaptive icons)
    for size in MASKABLE_SIZES:
        icon = create_icon(size, is_maskable=True)
        filename = f"icon-maskable-{size}x{size}.png"
        filepath = os.path.join(ICONS_DIR, filename)
        icon.save(filepath, "PNG")
        print(f"✓ Created {filename} (maskable)")
    
    print(f"\n✅ All icons generated in {ICONS_DIR}")
    print("Icons are ready for PWA installation!")

if __name__ == "__main__":
    try:
        generate_all_icons()
    except ImportError:
        print("ERROR: Pillow (PIL) is not installed.")
        print("Install it with: pip install Pillow")
        print("\nAlternatively, you can:")
        print("1. Use an online PWA icon generator: https://www.pwabuilder.com/imageGenerator")
        print("2. Create icons manually and save them in media/icons/")
        print("   Required sizes: 72x72, 96x96, 128x128, 144x144, 152x152,")
        print("                   192x192, 384x384, 512x512")
        print("   Plus maskable: 192x192, 512x512")
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nIf generation fails, you can use an online tool:")
        print("https://www.pwabuilder.com/imageGenerator")
