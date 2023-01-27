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


Prompt: Make the right button to draw circles.

ChatGPT: Here is an updated version of the code that allows you to draw
circles by clicking and dragging with the right mouse button:

... <explantion omitted>

Prompt: draw circle does not work

ChatGPT: I apologize, it looks like there was a mistake in the code
I provided. The draw_circle function should create an oval with the
given center and radius, but in the previous code it was creating an
oval with opposite corners determined by x-radius, y-radius, x+radius,
y+radius. Here is the corrected version of the draw_circle function:

Also, the on_right_button_drag and on_right_button_release event, were
not deleting the previous circle, it was only drawing circles, this is a
corrected version of those events, that also delete the previous circles:

I apologize for any confusion caused by the previous code. Please let
me know if you have any other questions.

Prompt: So, what's the final code?

ChatGPT: Here is the final code that allows you to create a drawing
panel and draw lines and circles on it using your mouse:

You can run this code in your python environment and it will create
a window where you can draw lines and circles with your mouse. Left
button is used to draw lines and right button is used to draw circles.
Please let me know if you ...

Prompt: Keep the completed circles.

ChatGPT: Here is the modified code that will keep the circles drawn on
the panel:

In this code, I removed the delete statement from the on_right_button_drag
and on_right_button_release functions, this way the circles drawn will
remain on the panel.  Please let me know if you have any further question.

'''

import tkinter as tk

class DrawingPanel(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.start_x = None
        self.start_y = None
        self.bind("<Button-1>", self.on_left_button_press)
        self.bind("<B1-Motion>", self.on_left_button_drag)
        self.bind("<ButtonRelease-1>", self.on_left_button_release)
        self.bind("<Button-3>", self.on_right_button_press)
        self.bind("<B3-Motion>", self.on_right_button_drag)
        self.bind("<ButtonRelease-3>", self.on_right_button_release)

    def on_left_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_left_button_drag(self, event):
        self.create_line(self.start_x, self.start_y, event.x, event.y, tags="line")
        self.start_x = event.x
        self.start_y = event.y

    def on_left_button_release(self, event):
        self.create_line(self.start_x, self.start_y, event.x, event.y, tags="line")

    def on_right_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_right_button_drag(self, event):
        radius = ((event.x - self.start_x)**2 + (event.y - self.start_y)**2)**0.5
        self.draw_circle(self.start_x, self.start_y, radius)

    def on_right_button_release(self, event):
        radius = ((event.x - self.start_x)**2 + (event.y - self.start_y)**2)**0.5
        self.draw_circle(self.start_x, self.start_y, radius)

    def draw_circle(self, x, y, radius):
        self.create_oval(x-radius, y-radius, x+radius, y+radius, outline='black',width=2,tags="circle")


if __name__ == "__main__":
    root = tk.Tk()
    dp = DrawingPanel(root, width=500, height=500, background="white")
    dp.pack()
    root.mainloop()

