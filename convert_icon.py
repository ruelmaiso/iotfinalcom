from PIL import Image

img = Image.open("download.jpg").convert("RGBA")
img.save(
    "assets/branding/app_icon.ico",
    format="ICO",
    sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]
)

print("Created assets/branding/app_icon.ico")