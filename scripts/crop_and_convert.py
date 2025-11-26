import os
from PIL import Image
import sys

def process_image(input_path, output_folder):
    """
    Crop bottom 5% of image (watermark area) and convert to WebP format
    """
    try:
        img = Image.open(input_path)
        width, height = img.size
        
        # Crop bottom 5% - keep top 95%
        crop_height = int(height * 0.95)
        cropped_img = img.crop((0, 0, width, crop_height))
        
        # Create output filename with .webp extension
        filename = os.path.basename(input_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}.webp"
        output_path = os.path.join(output_folder, output_filename)
        
        # Save as WebP format
        cropped_img.save(output_path, 'WEBP', quality=90)
        print(f"✓ Processed: {filename} -> {output_filename}")
        return True
        
    except Exception as e:
        print(f"✗ Error processing {input_path}: {e}")
        return False

def main():
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Source directory with images
    source_dir = os.path.join(project_root, '来自_3Dalia_的照片和图片组合_Shutterstock_投稿者Shutterstock')
    output_folder = os.path.join(project_root, 'output')
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    
    # Process all image files
    if os.path.isdir(source_dir):
        image_files = [f for f in os.listdir(source_dir) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        
        if not image_files:
            print(f"No image files found in {source_dir}")
            return
        
        print(f"Found {len(image_files)} images to process...")
        success_count = 0
        
        for filename in image_files:
            input_path = os.path.join(source_dir, filename)
            if process_image(input_path, output_folder):
                success_count += 1
        
        print(f"\nCompleted! Successfully processed {success_count}/{len(image_files)} images")
    else:
        print(f"Source directory not found: {source_dir}")

if __name__ == "__main__":
    main()
