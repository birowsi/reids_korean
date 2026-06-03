from PIL import Image

img = Image.open('nerv.png')
pixels = img.load()
width, height = img.size

min_y = height
max_y = 0

for y in range(height):
    for x in range(width):
        p = pixels[x, y]
        if p != 0: # Assuming 0 is black/background
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            
print(f"Non-black pixels are between Y: {min_y} and {max_y}")
print(f"Height used: {max_y - min_y + 1}")
