# ChatGPT generated
# See https://chat.openai.com/share/25af2358-aa1d-4141-bdfb-abd0c9511b44 
# for the full prompt history

import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class NavigationEnvironment:
    def __init__(self, n=100, m=200, r=10, agent_x=50, agent_y=50):
        self.n = n
        self.m = m
        self.r = r
        self.agent_x = agent_x
        self.agent_y = agent_y
        self.objects = []

        for _ in range(m):
            object_x = np.random.randint(0, n)
            object_y = np.random.randint(0, n)
            self.objects.append((object_x, object_y))

    def get_sensor_readings(self):
        sensor_readings = [0] * 8

        for obj_x, obj_y in self.objects:
            distance = math.sqrt((self.agent_x - obj_x) ** 2 + (self.agent_y - obj_y) ** 2)
            if distance <= self.r:
                angle = math.atan2(obj_y - self.agent_y, obj_x - self.agent_x)
                angle_deg = math.degrees(angle)
                if angle_deg < 0:
                    angle_deg += 360

                sensor_index = int(angle_deg / 45)
                sensor_readings[sensor_index] = distance

        return sensor_readings

    def plot_environment(self):
        fig, ax = plt.subplots()
        ax.set_aspect('equal', 'box')

        # Plot objects
        for obj_x, obj_y in self.objects:
            ax.add_patch(plt.Circle((obj_x, obj_y), 0.5, color='red'))

        # Plot objects within the radius
        objects_within_radius = [(obj_x, obj_y) for obj_x, obj_y in self.objects if
                                 math.sqrt((self.agent_x - obj_x) ** 2 + (self.agent_y - obj_y) ** 2) <= self.r]
        for obj_x, obj_y in objects_within_radius:
            ax.add_patch(plt.Circle((obj_x, obj_y), 0.5, color='green'))

        # Plot agent and the circle around it
        agent_circle = plt.Circle((self.agent_x, self.agent_y), self.r, fill=False, color='blue')
        ax.add_patch(agent_circle)
        ax.add_patch(plt.Circle((self.agent_x, self.agent_y), 1, color='blue'))

        # Plot pie slice boundaries
        for i in range(8):
            angle = math.radians(i * 45)
            x1 = self.agent_x
            y1 = self.agent_y
            x2 = x1 + self.r * math.cos(angle)
            y2 = y1 + self.r * math.sin(angle)
            plt.plot([x1, x2], [y1, y2], 'k')

        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
	# only part manually changed: np.around() below
        sensor_readings = np.around(self.get_sensor_readings())
        plt.title(f"Sensor Readings: {sensor_readings}")
        plt.show()

if __name__ == "__main__":
    env = NavigationEnvironment(m=200)
    env.plot_environment()
