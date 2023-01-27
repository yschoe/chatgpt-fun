'''

Fri, Jan 27, 2023 11:59:33 AM

Prompt: Write something like jpanel in python so that I can call functions
to draw lines and circles.

ChatGPT: In Python, you can use the tkinter library to create a GUI
application with a drawing area, similar to a JPanel in Java. Here is
an example of how you can create a simple drawing area in a tkinter
application that allows you to draw lines and circles by calling
functions:

ChatGPT: This code defines a DrawingArea class that inherits from
tkinter.Canvas, which is a widget that allows you to draw shapes and
lines. The DrawingArea class has two methods draw_line and draw_circle
that can be used to draw lines and circles on the canvas respectively. It
also has three methods on_left_button_press, on_left_button_drag,
and on_left_button_release that are used to handle mouse events on the
canvas. When the left mouse button is pressed, the on_left_button_press
method is called and stores the starting coordinates of the line to be
drawn. When the left mouse button is dragged, the on_left_button_drag
method is called, which uses the stored starting coordinates and the
current mouse coordinates to draw a line on the canvas. When the left
mouse button is released, the on_left_button_release method is called,
which draws the last segment of the line.

The MainWindow class creates an instance of the DrawingArea class and ...

'''

import tkinter as tk

class DrawingArea(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)
        self.bind("<Button-1>", self.on_left_button_press)
        self.bind("<B1-Motion>", self.on_left_button_drag)
        self.bind("<ButtonRelease-1>", self.on_left_button_release)

    def draw_line(self, start_x, start_y, end_x, end_y):
        self.create_line(start_x, start_y, end_x, end_y)

    def draw_circle(self, x, y, radius):
        self.create_oval(x-radius, y-radius, x+radius, y+radius)

    def on_left_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_left_button_drag(self, event):
        self.draw_line(self.start_x, self.start_y, event.x, event.y)
        self.start_x = event.x
        self.start_y = event.y

    def on_left_button_release(self, event):
        self.draw_line(self.start_x, self.start_y, event.x, event.y)

class MainWindow(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.drawing_area = DrawingArea(self)
        self.drawing_area.pack()

if __name__ == "__main__":
    main_window = MainWindow()
    main_window.mainloop()
