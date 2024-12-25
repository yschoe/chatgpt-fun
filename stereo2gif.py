import sys
from PIL import Image, ImageSequence

def stereo_to_gif(input_filename):
    try:
        # Open the stereo image
        img = Image.open(input_filename)
        width, height = img.size

        if width % 2 != 0:
            print("Error: Image width is not divisible by 2.")
            return

        # Calculate dimensions of each half
        half_width = width // 2

        # Split into left and right images
        left_image = img.crop((0, 0, half_width, height))
        right_image = img.crop((half_width, 0, width, height))

        # Create a GIF animation from the two frames
        gif_filename = input_filename.rsplit('.', 1)[0] + '_stereo.gif'
        frames = [left_image, right_image]

        # Save the GIF
        frames[0].save(
            gif_filename,
            save_all=True,
            append_images=frames[1:],
            duration=1300,  # milliseconds per frame
            loop=0
        )
        print(f"GIF animation saved as {gif_filename}")

    except FileNotFoundError:
        print(f"Error: File '{input_filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <stereo_image_filename>")
    else:
        stereo_to_gif(sys.argv[1])

