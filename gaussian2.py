'''
ChatGPT fun by Yoonsuck Choe

Note: This is a revised version of gaussian.py. I added the extra sentence
at the end "Show the animation for a single normal distribution, and
plot each sample one by one."

The prompt was:

Write a python code to show an animation where (x,y) values are sampled
from a two demensional normal distribution of mean (0,0) and the identity
matrix as the covariance matrix. Show the animation for a single normal
distribution, and plot each sample one by one.

The explanation by chatGPT was:

This program uses the np.random.multivariate_normal() function to
sample points from a normal distribution with mean (0, 0) and an
identity matrix as the covariance matrix. The update() function is
called repeatedly by the animation framework to sample a new point and
update the animation. The animation shows how the points are distributed
according to the normal distribution. This program is not particularly
efficient or readable, but it does provide a visual demonstration of a
normal distribution using an animation.

'''
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Set up the figure and axes for the animation
fig, ax = plt.subplots()
ax.set_xlim(-5, 5)
ax.set_ylim(-5, 5)
line, = ax.plot([], [], 'o', markersize=3)

# Initialize the data for the animation
xdata, ydata = [], []

# This function will be called repeatedly by the animation framework
def update(frame):
    # Sample a random point from the normal distribution
    x, y = np.random.multivariate_normal([0, 0], [[1, 0], [0, 1]])
    # Update the data for the animation
    xdata.append(x)
    ydata.append(y)
    line.set_data(xdata, ydata)
    return line,

# Set up the animation
ani = animation.FuncAnimation(fig, update, frames=100, interval=100, blit=True)

# Show the animation
plt.show()
