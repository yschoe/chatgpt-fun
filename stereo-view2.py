import glob
import argparse
from PIL import Image, ImageTk, ExifTags
import tkinter as tk
from screeninfo import get_monitors
import os


class ImageViewer(tk.Tk):
    def __init__(self, image_files, screen_width, screen_height):
        super().__init__()
        self.image_files = image_files
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.index = 0

        self.title("Image Viewer")
        self.attributes('-fullscreen', True)
        self.configure(bg='black')

        self.canvas = tk.Canvas(self, width=screen_width, height=screen_height, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.bind("<Right>", self.next_image)
        self.bind("<Left>", self.prev_image)
        self.bind("<s>", self.save_stereo_view)
        self.bind("<q>", self.quit)
        self.bind("<Escape>", self.quit)  # Allow Escape to quit fullscreen

        self.display_images()

    def display_images(self):
        self.canvas.delete("all")

        self.left_image = Image.open(self.image_files[self.index])
        self.left_image = self.rotate_image_exif(self.left_image)
        self.left_image = self.scale_image(self.left_image, self.screen_width // 2, self.screen_height)

        self.left_photo = ImageTk.PhotoImage(self.left_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.left_photo)

        if self.index + 1 < len(self.image_files):
            self.right_image = Image.open(self.image_files[self.index + 1])
            self.right_image = self.rotate_image_exif(self.right_image)
            self.right_image = self.scale_image(self.right_image, self.screen_width // 2, self.screen_height)

            self.right_photo = ImageTk.PhotoImage(self.right_image)
            self.canvas.create_image(self.screen_width // 2, 0, anchor=tk.NW, image=self.right_photo)

    def rotate_image_exif(self, image):
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(orientation, 1)
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        except Exception as e:
            print(f"Error rotating image: {e}")
        return image

    def scale_image(self, image, target_width, target_height):
        img_width, img_height = image.size
        if img_width > img_height:
            # Landscape
            scale_factor = target_width / img_width
        else:
            # Portrait
            scale_factor = target_height / img_height

        new_size = (int(img_width * scale_factor), int(img_height * scale_factor))
        return image.resize(new_size) #, Image.ANTIALIAS)

    def save_stereo_view(self, event):
        if self.index + 1 >= len(self.image_files):
            print("Cannot save stereo view. Not enough images.")
            return

        # Combine left and right images
        combined_width = self.left_image.width + self.right_image.width
        combined_height = max(self.left_image.height, self.right_image.height)

        combined_image = Image.new("RGB", (combined_width, combined_height))
        combined_image.paste(self.left_image, (0, 0))
        combined_image.paste(self.right_image, (self.left_image.width, 0))

        # Crop black regions
        bbox = combined_image.getbbox()
        cropped_image = combined_image.crop(bbox)

        # Generate filename
        left_file = os.path.basename(self.image_files[self.index])
        right_file = os.path.basename(self.image_files[self.index + 1])
        save_name = f"{os.path.splitext(left_file)[0]}_{os.path.splitext(right_file)[0]}.jpg"

        # Save the image
        cropped_image.save(save_name)
        print(f"Stereo view saved as {save_name}")

    def next_image(self, event):
        if self.index + 2 < len(self.image_files):
            self.index += 1
            self.display_images()

    def prev_image(self, event):
        if self.index > 0:
            self.index -= 1
            self.display_images()

    def quit(self, event):
        self.destroy()


def main():
    parser = argparse.ArgumentParser(description='Display images side by side with navigation.')
    parser.add_argument('pattern', type=str, help='Wildcard pattern to match image files')
    parser.add_argument('--reverse', action='store_true', help='Reverse the order of the images')
    args = parser.parse_args()

    # Detect screen dimensions
    screen = get_monitors()[0]
    screen_width = screen.width
    screen_height = screen.height

    # Get the list of image files using the provided wildcard pattern
    image_files = glob.glob(args.pattern)
    image_files.sort()  # Ensure the list is sorted

    if args.reverse:
        image_files.reverse()

    if len(image_files) < 2:
        print("Need at least two images to display.")
        return

    app = ImageViewer(image_files, screen_width, screen_height)
    app.mainloop()


if __name__ == "__main__":
    main()

