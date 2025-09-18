#!/usr/bin/env python3
"""
Terrarium-in-a-bottle: a minimal sealed-ecosystem simulation with Pygame.

Enhancements:
- Environment space is a torus (wrap-around edges).
- Critters (herbivore-like) with vanishing trails.
- Algae and Plant biomass that grow and reproduce.
- Nutrients decay to zero if no producers exist.

Run:
  python terrarium_sim_pygame.py --width 900 --height 700 --herbivores 80 --animal-cap 200
"""
import argparse
import math
import random
from dataclasses import dataclass, field
from typing import List

import pygame

Vec = pygame.math.Vector2

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

@dataclass
class Environment:
    water: float = 0.8
    nutrients: float = 0.4
    o2: float = 0.21
    co2: float = 0.0006
    temp_c: float = 22.0
    light_phase: float = 0.0
    day_length_s: float = 120.0

    def light(self, dt):
        self.light_phase = (self.light_phase + dt / self.day_length_s) % 1.0
        ang = 2 * math.pi * self.light_phase
        raw = math.sin(ang)
        return max(0.0, raw)

class AlgaeGrid:
    def __init__(self, w, h, cell=10, init_level=0.2):
        self.cell = cell
        self.cols = w // cell
        self.rows = h // cell
        self.grid = [[max(0.0, min(1.0, random.gauss(init_level, 0.05)))
                      for _ in range(self.cols)] for _ in range(self.rows)]

    def total_biomass(self):
        return sum(sum(row) for row in self.grid) / (self.cols * self.rows)

    def sample(self, pos: Vec):
        c = int(pos.x // self.cell) % self.cols
        r = int(pos.y // self.cell) % self.rows
        return self.grid[r][c]

    def eat(self, pos: Vec, amount: float) -> float:
        c = int(pos.x // self.cell) % self.cols
        r = int(pos.y // self.cell) % self.rows
        take = min(self.grid[r][c], amount)
        self.grid[r][c] -= take
        return take

    def grow(self, env: Environment, dt: float):
        light = env.light(0)
        r_max = 0.3
        total_before = self.total_biomass()
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.grid[r][c]
                lim = min(1.0, 0.2 + 0.8*light) * min(1.0, 0.3 + 0.7*env.nutrients) * min(1.0, env.water)
                growth = r_max * lim * x * (1 - x) * dt
                resp = 0.02 * (1.0 - light) * x * dt
                x = x + growth - resp
                self.grid[r][c] = clamp(x, 0.0, 1.0)
                if random.random() < 0.0005 * dt:
                    self.grid[r][c] = clamp(self.grid[r][c] + 0.2, 0.0, 1.0)
        ps = 0.02 * light * self.total_biomass() * dt
        env.o2 = clamp(env.o2 + ps - 0.01 * (1.0 - light) * dt, 0.0, 0.35)
        env.co2 = clamp(env.co2 - 0.8 * ps + 0.005 * (1.0 - light) * dt, 0.0, 0.01)
        net = self.total_biomass() - total_before
        env.nutrients = clamp(env.nutrients - max(0.0, net)*0.05 - 0.001*dt, 0.0, 1.0)

    def draw(self, surf):
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.grid[r][c]
                if x <= 0.005:
                    continue
                g = int(30 + 200 * x)
                color = (20, g, 20)
                pygame.draw.rect(surf, color, (c*self.cell, r*self.cell, self.cell, self.cell))

@dataclass
class Plant:
    biomass: float = 0.3

    def update(self, env: Environment, dt: float):
        light = env.light(0)
        before = self.biomass
        growth = 0.15 * light * env.nutrients * self.biomass * (1 - self.biomass) * dt
        resp = 0.01 * (1.0 - light) * self.biomass * dt
        self.biomass = clamp(self.biomass + growth - resp, 0.0, 1.0)
        if random.random() < 0.0003 * dt:
            self.biomass = clamp(self.biomass + 0.1, 0.0, 1.0)
        delta = self.biomass - before
        env.nutrients = clamp(env.nutrients - max(0.0, delta)*0.05, 0.0, 1.0)
        env.o2 = clamp(env.o2 + 0.015 * light * self.biomass * dt - 0.006 * (1.0 - light) * dt, 0.0, 0.35)
        env.co2 = clamp(env.co2 - 0.012 * light * self.biomass * dt + 0.003 * (1.0 - light) * dt, 0.0, 0.01)

    def draw(self, surf, center, radius_max):
        r = int(radius_max * math.sqrt(self.biomass))
        if r <= 0:
            return
        pygame.draw.circle(surf, (40, 130, 40), center, r)
        pygame.draw.circle(surf, (30, 90, 30), center, int(0.7*r), width=2)

@dataclass
class Critter:
    pos: Vec
    vel: Vec
    energy: float
    age: float = 0.0
    max_age: float = 1500.0
    speed: float = 35.0
    sense: float = 40.0
    size: int = 2
    repro_threshold: float = 1.1
    trail: List[Vec] = field(default_factory=list)

    def alive(self):
        return self.energy > 0 and self.age < self.max_age

    def step(self, dt, w, h, bias: Vec = None):
        jitter = Vec(random.uniform(-1, 1), random.uniform(-1, 1)) * 0.5
        v = self.vel * 0.1 + jitter * 0.9
        if bias is not None:
            v = v + bias * 0.3
        if v.length() == 0:
            v = Vec(1, 0)
        v = v.normalize() * self.speed
        self.pos = Vec((self.pos.x + v.x * dt) % w, (self.pos.y + v.y * dt) % h)
        self.vel = v
        self.energy -= 0.02 * dt
        self.age += dt
        # update trail
        self.trail.append(self.pos)
        if len(self.trail) > 100:
            self.trail.pop(0)

    def can_reproduce(self):
        return self.energy >= self.repro_threshold

    def forage_bias(self, algae: AlgaeGrid) -> Vec:
        best_dir = Vec(0, 0); best = -1
        for _ in range(5):
            ang = random.uniform(0, 2*math.pi)
            d = Vec(math.cos(ang), math.sin(ang))
            probe = self.pos + d * self.sense
            val = algae.sample(probe)
            if val > best:
                best, best_dir = val, d
        return best_dir

    def eat(self, algae: AlgaeGrid, dt: float):
        take = algae.eat(self.pos, 0.2 * dt)
        self.energy += 2.0 * take

    def draw(self, surf):
        # draw trail with fading alpha
        for i, p in enumerate(self.trail):
            alpha = int(255 * (i+1)/len(self.trail))
            col = (180, 220, 120, alpha)
            trail_surf = pygame.Surface((4,4), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, col, (2,2), 2)
            surf.blit(trail_surf, (int(p.x)-2, int(p.y)-2))
        # draw critter body
        pygame.draw.circle(surf, (180, 220, 120), (int(self.pos.x), int(self.pos.y)), self.size)

class Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.hover = False
    def handle(self, ev):
        if ev.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            self.action()
    def draw(self, surf, font):
        color = (60, 60, 60) if not self.hover else (90, 90, 90)
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, (150, 150, 150), self.rect, 2, border_radius=8)
        txt = font.render(self.label, True, (230, 230, 230))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

class Simulation:
    def __init__(self, args):
        self.w, self.h = args.width, args.height
        self.env = Environment()
        self.algae = AlgaeGrid(self.w, self.h, cell=8, init_level=args.algae_init)
        self.plant = Plant(biomass=0.3)
        self.critters: List[Critter] = []
        for _ in range(args.herbivores):
            self.critters.append(self._mk_critter())
        self.time_scale = 1.0
        self.paused = False
        self.args = args

    def _mk_critter(self):
        return Critter(pos=Vec(random.uniform(0, self.w), random.uniform(0, self.h)),
                       vel=Vec(random.uniform(-1,1), random.uniform(-1,1)), energy=1.0,
                       max_age=random.uniform(900, 2000), repro_threshold=1.1)

    def update(self, dt):
        if self.paused:
            return
        dt *= self.time_scale
        self.algae.grow(self.env, dt)
        self.plant.update(self.env, dt)
        for c in self.critters:
            bias = c.forage_bias(self.algae)
            c.step(dt, self.w, self.h, bias)
            c.eat(self.algae, dt)
            self.env.o2 = clamp(self.env.o2 - 0.0001 * dt, 0.0, 0.35)
            self.env.co2 = clamp(self.env.co2 + 0.00008 * dt, 0.0, 0.01)
        before = len(self.critters)
        self.critters = [c for c in self.critters if c.alive()]
        deaths = before - len(self.critters)
        self.env.nutrients = clamp(self.env.nutrients + 0.01 * deaths, 0.0, 1.0)
        self._reproduce()
        self.env.water = clamp(self.env.water - 0.00001 * dt + 0.000005 * dt, 0.0, 1.0)
        self.env.temp_c = 21.0 + 1.5 * math.sin(2*math.pi*self.env.light_phase)

    def _reproduce(self):
        if len(self.critters) < self.args.animal_cap:
            random.shuffle(self.critters)
            for i in range(0, len(self.critters)-1, 2):
                a, b = self.critters[i], self.critters[i+1]
                if a.can_reproduce() and b.can_reproduce() and (a.pos - b.pos).length() < 12:
                    child = self._mk_critter()
                    child.pos = (a.pos + b.pos) / 2
                    child.energy = 0.7
                    a.energy *= 0.65; b.energy *= 0.65
                    self.critters.append(child)
                    if len(self.critters) >= self.args.animal_cap:
                        break

    def draw(self, surf, font):
        surf.fill((12, 12, 18))
        self.algae.draw(surf)
        self.plant.draw(surf, (self.w//2, self.h//2), radius_max=min(self.w, self.h)//4)
        for c in self.critters:
            c.draw(surf)
        hud = f"O2 {self.env.o2:0.3f}  CO2 {self.env.co2:0.4f}  Nutr {self.env.nutrients:0.2f}  Water {self.env.water:0.2f}  Plant {self.plant.biomass:0.2f}  Algae {self.algae.total_biomass():0.2f}  Critters {len(self.critters)}  x{self.time_scale:0.1f}"
        text = font.render(hud, True, (230, 230, 230))
        surf.blit(text, (10, 8))

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--width', type=int, default=900)
    parser.add_argument('--height', type=int, default=700)
    parser.add_argument('--tick-ms', type=int, default=50)
    parser.add_argument('--algae-init', type=float, default=0.20)
    parser.add_argument('--herbivores', type=int, default=80)
    parser.add_argument('--animal-cap', type=int, default=200)
    args = parser.parse_args(argv)

    pygame.init()
    screen = pygame.display.set_mode((args.width, args.height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas', 16)

    sim = Simulation(args)

    # UI buttons
    btns = []
    margin = 6; bw = 110; bh = 28
    def add_btn(x, y, label, action):
        btns.append(Button((x, y, bw, bh), label, action))
    # place at bottom-right
    add_btn(args.width - (bw+margin)*3, args.height - (bh+margin), '− speed', lambda: setattr(sim, 'time_scale', max(0.1, sim.time_scale/1.5)))
    add_btn(args.width - (bw+margin)*2, args.height - (bh+margin), 'pause/res', lambda: setattr(sim, 'paused', not sim.paused))
    add_btn(args.width - (bw+margin)*1, args.height - (bh+margin), '+ speed', lambda: setattr(sim, 'time_scale', min(50.0, sim.time_scale*1.5)))

    running = True
    base_tick = args.tick_ms
    while running:
        for ev in pygame.event.get():
            # handle buttons (mouse move/click)
            for b in btns:
                b.handle(ev)
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    sim.time_scale = min(50.0, sim.time_scale * 1.5)
                elif ev.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                    sim.time_scale = max(0.1, sim.time_scale / 1.5)
                elif ev.key == pygame.K_SPACE:
                    sim.paused = not sim.paused
        dt = base_tick / 1000.0
        sim.update(dt)
        sim.draw(screen, font)
        # draw buttons
        for b in btns:
            b.draw(screen, font)
        pygame.display.flip()
        clock.tick(1000 // base_tick)
    pygame.quit()

if __name__ == '__main__':
    main()

