from PIL import Image
from pathlib import Path

# === CONFIG ===
INPUT_PATH = "splash_bg.jpg"   # change to your file
OUTPUT_PATH = "assets/essu_background.jpg"
TARGET_SIZE = (1920, 1080)
JPEG_QUALITY = 85


def convert_background():
    input_file = Path(INPUT_PATH)
    output_file = Path(OUTPUT_PATH)

    if not input_file.exists():
        print("Input background not found.")
        return

    img = Image.open(input_file).convert("RGB")

    # Smart resize with aspect ratio preservation (crop to fill)
    img_ratio = img.width / img.height
    target_ratio = TARGET_SIZE[0] / TARGET_SIZE[1]

    if img_ratio > target_ratio:
        # Wider → crop width
        new_height = img.height
        new_width = int(target_ratio * new_height)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, new_height))
    else:
        # Taller → crop height
        new_width = img.width
        new_height = int(new_width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, new_width, top + new_height))

    img = img.resize(TARGET_SIZE, Image.LANCZOS)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_file, "JPEG", quality=JPEG_QUALITY, optimize=True)

    print("Background converted successfully.")
    print(f"Saved to: {output_file}")
    print(f"Final size: {TARGET_SIZE}")


if __name__ == "__main__":
    convert_background()