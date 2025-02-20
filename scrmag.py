#!/usr/bin/python
'''
https://chatgpt.com/share/67b75a63-4244-8005-a776-d6db349fbe38

Usage:

  left click and hold to magnify
     - release to go back to normal pass-through mode
  right click to exit from application

  tried to make [esc] to exit app, but does not work.

'''
import cv2
import numpy as np
import pyautogui
import pynput
from pynput.mouse import Controller, Listener
import tkinter as tk
from PIL import Image, ImageTk

mouse = Controller()
box_size = 150
scale = 3

class MagnifierApp:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.canvas = tk.Canvas(root, width=box_size, height=box_size, highlightthickness=0)
        self.canvas.pack()
        self.img = None
        self.magnifying = False
        self.magnified_image = None
        self.listener = Listener(on_click=self.on_click, on_release=self.on_release, on_press=self.on_press, on_move=self.on_move)
        self.listener.start()
        self.root.bind("<Escape>", self.exit_application)
        self.update_display()
    
    def update_display(self):
        x, y = mouse.position
        x -= box_size // 2
        y -= box_size // 2
        if self.magnifying and self.magnified_image:
            img = self.magnified_image
            self.root.geometry(f"{box_size * scale}x{box_size * scale}+{x}+{y}")
        else:
            self.root.withdraw()
            img = pyautogui.screenshot(region=(x, y, box_size, box_size))
            self.root.deiconify()
            self.root.geometry(f"{box_size}x{box_size}+{x}+{y}")
        self.img = ImageTk.PhotoImage(img)
        self.canvas.config(width=img.width, height=img.height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img)
        self.root.after(50, self.update_display)

    def on_press(self,key):
        print("key pressed")
        if key == key.esc:
            self.root.destroy()
    
    def on_click(self, x, y, button, pressed):
        if button == pynput.mouse.Button.left and pressed:
            x, y = mouse.position
            x -= box_size // 2
            y -= box_size // 2
            img = pyautogui.screenshot(region=(x, y, box_size, box_size))
            self.magnified_image = img.resize((box_size * scale, box_size * scale), Image.LANCZOS)
            self.magnifying = True
        elif button == pynput.mouse.Button.right and pressed:
            '''
            self.magnifying = False
            self.magnified_image = None
            '''
            self.root.destroy()
        elif button == pynput.mouse.Button.left and not pressed:
            self.magnifying = False
            self.magnified_image = None

    def on_move(self,x,y):
        return
        # self.update_display() 
    
    def on_release(self, button):
        if button == pynput.mouse.Button.left:
            self.magnifying = False
            self.magnified_image = None
    
    def exit_application(self, event):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MagnifierApp(root)
    root.mainloop()
