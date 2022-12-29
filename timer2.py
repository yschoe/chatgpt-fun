'''
12/29/2022

Prompt 1: Write a python code for a timer, with a simple graphical user interface where the user can click on the time duration.

... see timer.py

Prompt 2: Make it a countdown timer, where the initial time can be specified.

ChatGPT: To make the timer a countdown timer, you can modify the code as follows:

ChatGPT: This code creates a countdown timer with a GUI that consists of a label to display the time, and three buttons to start, stop, and reset the timer. The timer is initialized to the specified initial time, and is decremented every second while the running flag is True. The time is displayed in minutes and seconds, and the timer

'''

import tkinter as tk

class Timer:
    def __init__(self, parent, initial_time):
        # Create a label to display the time
        self.time_label = tk.Label(parent, text=initial_time, font=("Helvetica", 48))
        self.time_label.pack()
        
        # Create a start button
        self.start_button = tk.Button(parent, text="Start", command=self.start)
        self.start_button.pack()
        
        # Create a stop button
        self.stop_button = tk.Button(parent, text="Stop", command=self.stop)
        self.stop_button.pack()
        
        # Create a reset button
        self.reset_button = tk.Button(parent, text="Reset", command=self.reset)
        self.reset_button.pack()
        
        # Set the timer to the initial time
        self.time = self.parse_time(initial_time)
        
        # Flag to keep track of whether the timer is running
        self.running = False
        
    def start(self):
        # Start the timer if it is not already running
        if not self.running:
            self.running = True
            self.update_time()
    
    def stop(self):
        # Stop the timer if it is running
        self.running = False
    
    def reset(self):
        # Reset the timer to the initial time
        self.time = self.parse_time(self.time_label['text'])
        self.time_label.config(text=self.time_label['text'])
    
    def update_time(self):
        # Decrement the timer and update the time label
        if self.running:
            self.time -= 1
            if self.time < 0:
                self.time = 0
                self.running = False
            minutes, seconds = divmod(self.time, 60)
            time_string = f"{minutes}:{seconds:02d}"
            self.time_label.config(text=time_string)
            self.time_label.after(1000, self.update_time)
    
    def parse_time(self, time_string):
        # Parse a time string in the format "X:YY" into a number of seconds
        minutes, seconds = time_string.split(":")
        return int(minutes) * 60 + int(seconds)

# Create the main window
root = tk.Tk()
root.title("Countdown Timer")

# Set the initial time
initial_time = "5:00"

# Create an instance of the Timer class and pack it into the main window
timer = Timer(root, initial_time)

# Run the main loop
root.mainloop()

