'''
12/29/2022

Prompt: Write a python code for a timer, with a simple graphical user interface where the user can click on the time duration.

ChatGPT: Here is a simple example of a timer with a graphical user interface (GUI) using the tkinter module in Python:
'''
import tkinter as tk

class Timer:
    def __init__(self, parent):
        # Create a label to display the time
        self.time_label = tk.Label(parent, text="0:00", font=("Helvetica", 48))
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
        
        # Set the timer to 0
        self.time = 0
        
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
        # Reset the timer to 0
        self.time = 0
        self.time_label.config(text="0:00")
    
    def update_time(self):
        # Increment the timer and update the time label
        if self.running:
            self.time += 1
            minutes, seconds = divmod(self.time, 60)
            time_string = f"{minutes}:{seconds:02d}"
            self.time_label.config(text=time_string)
            self.time_label.after(1000, self.update_time)

# Create the main window
root = tk.Tk()
root.title("Timer")

# Create an instance of the Timer class and pack it into the main window
timer = Timer(root)

# Run the main loop
root.mainloop()

