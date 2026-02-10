import os
from PIL import Image

# Define paths
input_path = os.path.join('static', 'icon.png')
output_path = os.path.join('static', 'readme_icon.png')

def optimize_image():
    if not os.path.exists(input_path):
        print(f"❌ Error: Could not find {input_path}")
        return

    try:
        with Image.open(input_path) as img:
            # Calculate new height maintaining aspect ratio, aiming for 250px width
            aspect_ratio = img.height / img.width
            new_width = 250
            new_height = int(new_width * aspect_ratio)
            
            # Resize using high-quality Lanczos resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as optimized PNG
            img.save(output_path, optimize=True)
            print(f"✅ Success! Created {output_path} ({new_width}x{new_height})")
            
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    optimize_image()