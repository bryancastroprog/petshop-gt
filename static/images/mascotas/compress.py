from PIL import Image
import os

folder = r"C:\Users\USUARIO\Documents\Quantum Axis\CLIENTES\Petshop GT\WEBSITE\static\images\mascotas"
files = [f for f in os.listdir(folder) if f.lower().endswith('.png') and not f.startswith(('remove','compress'))]

TARGET_SIZE = (800, 800)
QUALITY     = 82

for filename in files:
    src = os.path.join(folder, filename)
    dst = os.path.join(folder, filename.replace('.png', '.jpg'))

    img = Image.open(src).convert('RGB')
    orig_w, orig_h = img.size

    img = img.resize(TARGET_SIZE, Image.LANCZOS)
    img.save(dst, 'JPEG', quality=QUALITY, optimize=True, progressive=True)

    orig_kb = os.path.getsize(src) // 1024
    new_kb  = os.path.getsize(dst) // 1024
    os.remove(src)  # eliminar el PNG original
    print(f"{filename:30s}  {orig_kb:>5} KB  ->  {new_kb:>4} KB  ({filename.replace('.png','.jpg')})")

print("\nDone.")
