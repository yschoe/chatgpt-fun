'''
Initially made with Clause, fixed with ChatGPT


Claude prompt:
  YC
Write a code in python to simulate the braitenberg vehicle. Make it possible to specify in the environment the following. 
1. each vehicle's configuration: ls-lw to represent left-sensor to right-wheel, etc. so that ls-lw:rs-rw will describe a single vehicle with left sensor to left wheel and right-sensor to right wheel configuration. Take multiple such strings to keep on adding more vehicles.
2. number of stand-alone lights in the environment: -l <number>.
3. whether the vehicles should carry a light on them: -v.

Once this is given, simulate it and animate it.

  ...

YC

Nothing is moving.

  ...

YC

It is running past the light, when it should be attracted. Also, make it possible to toggle the trajectory display using a keyboard input "t".

   ...

YC

Make it so that when the vehicle is closer to the light, the attraction/replusion is stronger.


   ...

 -- from here on, I switched to ChatGPT

   ...

YC

Here's a code for the breitenberg vehicle. The problem is that it will not show the correct attractive/repulsive behavior. 


Choe: After this, it showed reasonable yet incorrect behavior. Need to fix it further.
- I added a small code to reset the trajectory when the vehicle wraps around at the borders.

'''

# Previous imports and class definitions remain the same
import numpy as np
import pygame
import argparse
from dataclasses import dataclass
from typing import List, Tuple
import math
from collections import deque

@dataclass
class Vehicle:
    x: float
    y: float
    angle: float  # in radians
    left_sensor: float
    right_sensor: float
    speed: float = 3.0
    size: float = 20
    connections: List[Tuple[str, str]] = None
    has_light: bool = False
    trajectory: deque = None
    vtype = None # True = attractive, False = repulsive
    
    def __post_init__(self):
        self.trajectory = deque(maxlen=200)

class Light:
    def __init__(self, x: float, y: float, intensity: float = 1000):
        self.x = x
        self.y = y
        self.intensity = intensity

class BraitenbergSimulation:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Braitenberg Vehicle Simulation")
        
        self.vehicles: List[Vehicle] = []
        self.lights: List[Light] = []
        self.clock = pygame.time.Clock()
        self.show_trajectory = False
        
    def calculate_sensor_response(self, distance: float, intensity: float) -> float:
        """Calculate non-linear sensor response based on distance."""
        # Parameters for non-linear response
        max_distance = 400  # Maximum effective distance
        min_distance = 20   # Distance of maximum effect
        
        if distance < min_distance:
            distance = min_distance
        
        if distance > max_distance:
            return 0
        
        # Create a non-linear response that increases dramatically at close range
        # Using inverse square law with additional exponential scaling
        normalized_dist = (max_distance - distance) / (max_distance - min_distance)
        response = intensity * (normalized_dist ** 2) * math.exp(normalized_dist - 1)
        
        return response
    
    def calculate_sensor_values(self, vehicle: Vehicle) -> Tuple[float, float]:
        """Calculate sensor values based on light sources with non-linear response."""
        left_value = 0
        right_value = 0
        
        # Sensor positions (offset from vehicle center)
        sensor_offset = vehicle.size / 2
        left_sensor_x = vehicle.x + math.cos(vehicle.angle - math.pi/4) * sensor_offset
        left_sensor_y = vehicle.y + math.sin(vehicle.angle - math.pi/4) * sensor_offset
        right_sensor_x = vehicle.x + math.cos(vehicle.angle + math.pi/4) * sensor_offset
        right_sensor_y = vehicle.y + math.sin(vehicle.angle + math.pi/4) * sensor_offset
        
        for light in self.lights:
            # Calculate distances to sensors
            left_dist = math.sqrt((left_sensor_x - light.x)**2 + (left_sensor_y - light.y)**2)
            right_dist = math.sqrt((right_sensor_x - light.x)**2 + (right_sensor_y - light.y)**2)
            
            # Calculate non-linear response for each sensor
            left_value += self.calculate_sensor_response(left_dist, light.intensity)
            right_value += self.calculate_sensor_response(right_dist, light.intensity)
            
        # Also consider lights from other vehicles with the same non-linear response
        for other_vehicle in self.vehicles:
            if other_vehicle.has_light and other_vehicle != vehicle:
                left_dist = math.sqrt((left_sensor_x - other_vehicle.x)**2 + 
                                    (left_sensor_y - other_vehicle.y)**2)
                right_dist = math.sqrt((right_sensor_x - other_vehicle.x)**2 + 
                                     (right_sensor_y - other_vehicle.y)**2)
                
                # Use lower intensity for vehicle lights
                vehicle_intensity = 500
                left_value += self.calculate_sensor_response(left_dist, vehicle_intensity)
                right_value += self.calculate_sensor_response(right_dist, vehicle_intensity)
        
        return left_value, right_value
 
    def update_vehicle(self, vehicle: Vehicle):
        """Update vehicle position and orientation based on sensor values."""
        left_value, right_value = self.calculate_sensor_values(vehicle)
        vehicle.left_sensor = left_value
        vehicle.right_sensor = right_value
    
        # Calculate wheel speeds based on connections for attraction or repulsion
        left_wheel = 0
        right_wheel = 0
    
        for sensor, wheel in vehicle.connections:
            sensor_value = left_value if sensor == 'ls' else right_value
            if wheel == 'lw':
                left_wheel += sensor_value
            else:  # 'rw'
                right_wheel += sensor_value
    
        # Adjust wheel behavior based on vehicle type (attractive or repulsive)
        if vehicle.connections == [('ls', 'lw'), ('rs', 'rw')]:  # Attraction
            left_wheel *= 3.0
            right_wheel *= 3.0
            vehicle.vtype = True
        elif vehicle.connections == [('ls', 'rw'), ('rs', 'lw')]:  # Repulsion
            # Invert and scale down values for repulsive effect
            left_wheel = -right_value * 3.0
            right_wheel = -left_value * 3.0
            vehicle.vtype = False
    
        # Normalize wheel speeds for smoother movement
        max_wheel_speed = max(abs(left_wheel), abs(right_wheel), 1)
        left_wheel /= max_wheel_speed
        right_wheel /= max_wheel_speed
    
        # Update position and angle
        average_speed = (left_wheel + right_wheel) * vehicle.speed / 2
        angular_velocity = (right_wheel - left_wheel) * vehicle.speed / vehicle.size * 50
    
        # Adjust angle scaling for responsiveness
        vehicle.angle += angular_velocity * 0.15
        vehicle.x += math.cos(vehicle.angle) * average_speed
        vehicle.y += math.sin(vehicle.angle) * average_speed
    
        # Store position for trajectory
        vehicle.trajectory.append((int(vehicle.x), int(vehicle.y)))
    
        # Bookkeeping and wrap-around
        vx, vy = vehicle.x, vehicle.y
        vehicle.x = vehicle.x % self.width
        vehicle.y = vehicle.y % self.height
    
        if abs(vx - vehicle.x) > (self.width - 10) or abs(vy - vehicle.y) > (self.height - 10):
            vehicle.trajectory.clear()



    # Rest of the class implementation remains the same
    def add_vehicle(self, x: float, y: float, connections_str: str, has_light: bool = False):
        connections = []
        for conn in connections_str.split(':'):
            sensor, wheel = conn.split('-')
            connections.append((sensor, wheel))
            
        vehicle = Vehicle(
            x=x,
            y=y,
            angle=np.random.random() * 2 * np.pi,
            left_sensor=0,
            right_sensor=0,
            connections=connections,
            has_light=has_light
        )
        self.vehicles.append(vehicle)
    
    def add_light(self, x: float, y: float):
        self.lights.append(Light(x, y))
    
    def draw(self):
        self.screen.fill((0, 0, 0))  # Black background
    
        if self.show_trajectory:
            for vehicle in self.vehicles:
                if len(vehicle.trajectory) > 1:
                    pygame.draw.lines(self.screen, (0, 100, 0), False, 
                                      list(vehicle.trajectory), 1)
    
        for light in self.lights:
            pygame.draw.circle(self.screen, (255, 255, 0), 
                               (int(light.x), int(light.y)), 10)
    
        for vehicle in self.vehicles:
            # Skip drawing if vehicle is too close to the boundary
            if (vehicle.x < 10 or vehicle.x > self.width - 10 or 
                vehicle.y < 10 or vehicle.y > self.height - 10):
                continue
    
            # Draw vehicle body
            points = [
                (vehicle.x + math.cos(vehicle.angle) * vehicle.size,
                 vehicle.y + math.sin(vehicle.angle) * vehicle.size),
                (vehicle.x + math.cos(vehicle.angle + 2.4) * vehicle.size / 2,
                 vehicle.y + math.sin(vehicle.angle + 2.4) * vehicle.size / 2),
                (vehicle.x + math.cos(vehicle.angle - 2.4) * vehicle.size / 2,
                 vehicle.y + math.sin(vehicle.angle - 2.4) * vehicle.size / 2),
            ]
            if vehicle.vtype:
                pygame.draw.polygon(self.screen, (0, 255, 0), points)  # Green for attractive
            else:
                pygame.draw.polygon(self.screen, (255, 0, 0), points)  # Red for repulsive
    
            # Draw sensors
            sensor_offset = vehicle.size / 2
            left_sensor_pos = (
                int(vehicle.x + math.cos(vehicle.angle - math.pi / 4) * sensor_offset),
                int(vehicle.y + math.sin(vehicle.angle - math.pi / 4) * sensor_offset)
            )
            right_sensor_pos = (
                int(vehicle.x + math.cos(vehicle.angle + math.pi / 4) * sensor_offset),
                int(vehicle.y + math.sin(vehicle.angle + math.pi / 4) * sensor_offset)
            )
    
            left_intensity = min(255, int(vehicle.left_sensor))
            right_intensity = min(255, int(vehicle.right_sensor))
            pygame.draw.circle(self.screen, (255, left_intensity, left_intensity), left_sensor_pos, 4)
            pygame.draw.circle(self.screen, (255, right_intensity, right_intensity), right_sensor_pos, 4)
    
            if vehicle.has_light:
                pygame.draw.circle(self.screen, (255, 255, 0), 
                                   (int(vehicle.x), int(vehicle.y)), 6)
    
        font = pygame.font.Font(None, 24)
        trajectory_status = "ON" if self.show_trajectory else "OFF"
        text = font.render(f"Trajectory: {trajectory_status} (Toggle: T); Quit: ESC", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
    
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_t:
                        self.show_trajectory = not self.show_trajectory
                        if not self.show_trajectory:
                            for vehicle in self.vehicles:
                                vehicle.trajectory.clear()
                    elif event.key == pygame.K_l:
                        # Toggle light for each vehicle
                        for vehicle in self.vehicles:
                            vehicle.has_light = not vehicle.has_light
    
            for vehicle in self.vehicles:
                self.update_vehicle(vehicle)
    
            self.draw()
            self.clock.tick(60)
    
        pygame.quit()

def main():
    parser = argparse.ArgumentParser(description='Braitenberg Vehicle Simulation') # \n usage: python brait.py -l 5 ls-rw:rs-lw ls-lw:rs-rw')
    parser.add_argument('configs', nargs='+', help='Vehicle configurations (e.g., ls-lw:rs-rw)')
    parser.add_argument('-l', '--lights', type=int, default=3, 
                        help='Number of standalone lights')
    parser.add_argument('-v', '--vehicle-lights', action='store_true',
                        help='Enable lights on vehicles')
    
    args = parser.parse_args()
    
    sim = BraitenbergSimulation()
    
    # Add standalone lights
    for _ in range(args.lights):
        x = np.random.randint(0, sim.width)
        y = np.random.randint(0, sim.height)
        sim.add_light(x, y)
    
    # Add vehicles
    for config in args.configs:
        x = np.random.randint(0, sim.width)
        y = np.random.randint(0, sim.height)
        sim.add_vehicle(x, y, config, args.vehicle_lights)
    
    sim.run()

if __name__ == "__main__":
    main()

