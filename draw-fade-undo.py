'''

Mon Feb 13 10:05:36 PM CST 2023

Prompt: Write a python code to show a white canvas and draw on it with the mouse in black, and add a button that will fade the saturation of the current stuff on the canvas so that new drawing would look very dark.
...

and several iterations later, adding undo feature, and some manual edits,
here's the final version. 

Ctrl-f to save screenshot file and fade out existing drawing.
Ctrl-z to undo : this is very primitive -- will undo fixed number of points 
Ctrl-q to quit 

Here's the full prompt: https://chat.openai.com/share/0f81a0bd-69c8-4c10-ab76-92017d9d8df7

Yoonsuck Choe

'''

import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
from datetime import datetime 

objects = []
start_x = 0
start_y = 0


def fade_saturation():

    save_screenshot() 

    items = canvas.find_all()
    for item in items:
        color = canvas.itemcget(item, "fill")
        if color == "black":
            canvas.itemconfig(item, fill="gray55")
        elif color == "gray55":
            canvas.itemconfig(item, fill="gray63")
        elif color == "gray63":
            canvas.itemconfig(item, fill="gray67")


def save_screenshot():
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
    file_path = "draw-fade-"+timestamp+".png"
    if file_path:
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        x1 = x + canvas.winfo_width()
        y1 = y + canvas.winfo_height()
        ImageGrab.grab().crop((x, y, x1, y1)).save(file_path)


def handle_key(event):
  fade_saturation()


def start_drawing(event):
  global start_x, start_y, objects
  start_x, start_y = event.x, event.y


def continue_drawing(event):
  global start_x, start_y, objects
  x, y = event.x, event.y
  # objects.append(canvas.create_line(start_x, start_y, x, y, width=7, fill="black"))
  objects.append(canvas.create_oval(x-3, y-3, x+3, y+3, outline="", fill="black"))
  start_x, start_y = x, y


def stop_drawing(event):
  pass


def undo(event):

  global start_x, start_y, objects

  for i in range(1,50): 
    if objects:
       canvas.delete(objects.pop())
  canvas.update()

root = tk.Tk()
root.title("Canvas with fading saturation")

root.bind("<Control-f>",handle_key) 

canvas = tk.Canvas(root, bg="white", height=800, width=1900)
canvas.pack()

fade_button = tk.Button(root, text="Fade and Save [Ctrl-f]", command=fade_saturation)
fade_button.pack()

undo_button = tk.Button(root, text="Undo [Ctrl-Z]", command=undo)
undo_button.pack()

quit_button = tk.Button(root, text="Quit", command=exit)
quit_button.pack()

canvas.bind("<Button-1>", start_drawing)
canvas.bind("<B1-Motion>", continue_drawing)
canvas.bind("<ButtonRelease-1>", stop_drawing)
root.bind("<Control-z>", undo)

root.mainloop()

