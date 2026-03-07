from PIL import Image
from pathlib import Path

# === CONFIG ===
INPUT_PATH = "essuo.png"   # change to your file
OUTPUT_PATH = "assets/essu_logo.png"
TARGET_SIZE = (512, 512)


def convert_logo():
    input_file = Path(INPUT_PATH)
    output_file = Path(OUTPUT_PATH)

    if not input_file.exists():
        print("Input logo not found.")
        return

    img = Image.open(input_file)

    # Preserve transparency if present
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")

    img = img.resize(TARGET_SIZE, Image.LANCZOS)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_file, "PNG", optimize=True)

    print("Logo converted successfully.")
    print(f"Saved to: {output_file}")
    print(f"Final size: {TARGET_SIZE}")


if __name__ == "__main__":
    convert_logo()