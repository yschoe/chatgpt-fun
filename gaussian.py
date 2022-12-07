'''
ChatGPT fun : Yoonsuck Choe

Note: This did not give the desired result, so I further elaborated it
in gaussian2.py.

The prompt was:

Write a python code to show an animation where (x,y) values are sampled
from a two demensional normal distribution of mean (0,0) and the identity
matrix as the covariance matrix.

The explanation by chatGPT was:
Choe: Please see the explanation in gaussian2.py, which was similar.

'''
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Generate random samples from a two-dimensional normal distribution
def generate_samples(n):
    return np.random.multivariate_normal([0, 0], [[1, 0], [0, 1]], n)

# Set up the figure and axes for the animation
fig, ax = plt.subplots()
ax.set_xlim(-4, 4)
ax.set_ylim(-4, 4)
scatter = ax.scatter([], [])

# This function will be called repeatedly by the animation framework
def update(frame):
    # Generate a new set of random samples
    samples = generate_samples(100)
    # Update the data for the scatter plot
    scatter.set_offsets(samples)
    return scatter,

# Set up the animation
ani = animation.FuncAnimation(fig, update, frames=100, interval=100, blit=True)

# Show the animation
plt.show()

