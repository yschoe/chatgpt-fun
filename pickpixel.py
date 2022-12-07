import tkinter as tk
from PIL import Image, ImageTk

# Set the name of the image file to be loaded
filename = "image.png"

# Load the image file and create a Tkinter PhotoImage object
image = Image.open(filename)
photo = ImageTk.PhotoImage(image)

# Set up the Tkinter window
root = tk.Tk()
root.title("Image Click Demo")

# Create a Tkinter Canvas widget and display the image on it
canvas = tk.Canvas(root, width=image.width, height=image.height)
canvas.pack()
canvas.create_image(0, 0, anchor=tk.NW, image=photo)

# Bind a callback function to the left mouse button click event
def on_click(event):
    # Print the (x,y) coordinate of the clicked pixel to the console
    print(f"Clicked pixel: ({event.x}, {event.y})")

canvas.bind("<Button-1>", on_click)

# Start the Tkinter event loop
root.mainloop()
