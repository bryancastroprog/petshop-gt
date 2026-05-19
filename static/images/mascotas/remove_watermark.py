from PIL import Image
import os

folder = r"C:\Users\USUARIO\Documents\Quantum Axis\CLIENTES\Petshop GT\WEBSITE\static\images\mascotas"
files = [f for f in os.listdir(folder) if f.lower().endswith('.png') and not f.startswith('remove')]

CROP_PCT = 0.10  # cortar 10% desde abajo y derecha

for filename in files:
    path = os.path.join(folder, filename)
    img = Image.open(path).convert('RGB')
    w, h = img.size
    cut_x = int(w * CROP_PCT)
    cut_y = int(h * CROP_PCT)
    img = img.crop((0, 0, w - cut_x, h - cut_y))
    img = img.resize((w, h), Image.LANCZOS)
    img.save(path, 'PNG')
    print(f"OK: {filename}")

print("Done.")
