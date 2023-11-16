#!/usr/bin/python

import sys
from PIL import Image, ImageDraw, ImageFont
import os
import math

def truncate_filename(filename, max_length=30):
    """Truncate filename if longer than max_length."""
    if len(filename) > max_length:
        filename = filename[:max_length - 3] + "..."
    return filename

def is_image_file(file_path):
    """Check if the file is a valid image file."""
    try:
        Image.open(file_path).verify()
        return True
    except (IOError, SyntaxError):
        return False

def create_photo_index(image_files, output_folder='photo_index', thumbnail_size=200, rows=5, cols=8, max_filename_length=30):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Filter out non-image files and corrupted files
    image_files = [file for file in image_files if is_image_file(file)]

    # Calculate the number of images needed
    num_images = math.ceil(len(image_files) / (rows * cols))

    for index in range(num_images):
        # Calculate the range of image files for the current index
        start = index * rows * cols
        end = min((index + 1) * rows * cols, len(image_files))

        # Create a blank index image
        index_size = (thumbnail_size * cols, thumbnail_size * rows)
        index_image = Image.new('RGB', index_size, color='white')
        draw = ImageDraw.Draw(index_image)

        # Load font for text
        font = ImageFont.load_default()

        for i, image_file in enumerate(image_files[start:end]):
            # Open the image file and check integrity
            try:
                img = Image.open(image_file)

                # Resize the image to fit in n * n pixels
                img.thumbnail((thumbnail_size, thumbnail_size))

            except OSError as e:
                print(f"Skipping corrupted file: {image_file} - {e}")
                continue

            # Calculate the position to paste the thumbnail
            row = i // cols
            col = i % cols
            position = (col * thumbnail_size, row * thumbnail_size)

            # Paste the thumbnail onto the index image
            index_image.paste(img, position)

            # Get the filename without extension
            filename = os.path.splitext(os.path.basename(image_file))[0]

            # Truncate filename if longer than max_filename_length
            truncated_filename = truncate_filename(filename, max_filename_length)

            # Draw the truncated filename as an overlay on top of the thumbnail
            text_position = (position[0] + 5, position[1] + 5)
            draw.text(text_position, truncated_filename, font=font, fill='black')

        # Save the resulting photo index
        index_image.save(os.path.join(output_folder, f'photo_index_{index + 1}.png'))

if __name__ == "__main__":
    # Check if command line arguments are provided
    if len(sys.argv) < 2:
        print("Usage: python script.py image1.jpg image2.png ...")
        sys.exit(1)

    # Get the list of image files from command line arguments
    image_files = sys.argv[1:]

    # Specify the output folder
    output_folder = 'photo_index'

    # Specify the thumbnail size, rows, columns, and max filename length
    thumbnail_size = 200
    rows = 5
    cols = 8
    max_filename_length = 30

    # Create the photo index
    create_photo_index(image_files, output_folder, thumbnail_size, rows, cols, max_filename_length)

