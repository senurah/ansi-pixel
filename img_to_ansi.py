from PIL import Image


def image_to_ansi(image_path: str, target_width: int = 40) -> list[str]:
    img = Image.open(image_path).convert("RGBA")
    
    # 1. Auto-crop white/transparent border
    bg = Image.new("RGBA", img.size, (255, 255, 255, 0))
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # 2. Resize keeping aspect ratio
    aspect = img.height / img.width
    # Target height must be even because each line renders 2 vertical pixels
    target_height = int(target_width * aspect)
    if target_height % 2 != 0:
        target_height += 1
        
    img = img.resize((target_width, target_height), Image.Resampling.NEAREST)

    lines = []
    # 3. Process pairs of vertical rows
    for y in range(0, target_height, 2):
        line = ""
        for x in range(target_width):
            top_r, top_g, top_b, top_a = img.getpixel((x, y))
            bot_r, bot_g, bot_b, bot_a = img.getpixel((x, y + 1))

            # Treat near-transparent or pure white margins as empty space
            top_empty = top_a < 128 or (top_r > 245 and top_g > 245 and top_b > 245)
            bot_empty = bot_a < 128 or (bot_r > 245 and bot_g > 245 and bot_b > 245)

            if top_empty and bot_empty:
                line += "\033[0m "
            elif top_empty and not bot_empty:
                # Top empty, bottom colored: lower half block
                line += f"\033[0m\033[38;2;{bot_r};{bot_g};{bot_b}m▄"
            elif not top_empty and bot_empty:
                # Top colored, bottom empty: upper half block
                line += f"\033[0m\033[38;2;{top_r};{top_g};{top_b}m▀"
            else:
                # Both colored: top is FG (▀), bottom is BG
                line += f"\033[38;2;{top_r};{top_g};{top_b}m\033[48;2;{bot_r};{bot_g};{bot_b}m▀"

        line += "\033[0m"
        lines.append(line)
        
    return lines
