'''
chatgpt fun by Yoonsuck Choe

Note: There was a small bug. I just had to manually move a single line
in the code.

Note: Click on several pixels, then close the window, and the coordinates
will be printed in the console.

The prompt was:

Write code in python with a graphical user interface where you can load
a image file (with a specific name), and click on the pixel to print
out the clicked pixel's (x,y) coordinate in the console.

The explanation by chatGPT was:

This program uses the Tkinter and PIL libraries to create a graphical
user interface that allows the user to load an image file and click on
a pixel to print out its (x,y) coordinate in the console. The program
first loads the specified image file and creates a Tkinter PhotoImage
object to display the image on a Tkinter Canvas widget. The on_click()
callback function is bound to the left mouse button click event on the
canvas, and it prints the (x,y) coordinate of the clicked pixel to the
console when the event is triggered. This program is not particularly
efficient or readable, but it does provide the basic functionality of
loading an image and clicking on a pixel to print its coordinate.

'''

import tkinter as tk
from PIL import Image, ImageTk

# Set the name of the image file to be loaded
filename = "image.png"

# Load the image file and create a Tkinter PhotoImage object
root = tk.Tk() # Yoonsuck Choe - This was moved here from below
image = Image.open(filename)
photo = ImageTk.PhotoImage(image)

# Set up the Tkinter window
#root = tk.Tk() : Yoonsuck Choe - This had to be moved above.
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
