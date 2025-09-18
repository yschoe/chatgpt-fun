#!/usr/bin/env python3
"""
Terrarium-in-a-bottle: a minimal but lively sealed-ecosystem simulation with Pygame.

Features
- Scalar environment: water, nutrients, O2/CO2, temperature, light (diurnal cycle)
- Primary producers: wall algae grid + a single moss/plant biomass pool
- Consumers: Herbivores (e.g., nematode/mites) + Predators (e.g., micro-arthropods)
- Behaviors: random walk + biased motion to food, mating, predation, aging
- Energetics: photosynthesis in light, organism respiration, detritus nutrient loop
- Controls: buttons [−speed] [pause] [+speed] [spawn] [stats] [reset]
- CLI overrides for initial resources and caps

Run
  python terrarium_sim_pygame.py --width 900 --height 700 --water 1.0 --o2 0.21 --algae-init 0.25 \
      --herbivores 35 --predators 6 --animal-cap 120 --tick-ms 40 --seed 42

Notes
- Units are normalized (0..1 for environment pools). Rates are toy but qualitatively plausible.
- The code is organized to be easy to tweak rather than perfectly biophysical.
"""
import argparse
import math
import random
import sys
from dataclasses import dataclass, field
from typing import Tuple, List

import pygame

Vec = pygame.math.Vector2

# ------------------------------ Utilities ---------------------------------

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

# ------------------------------ Environment --------------------------------

@dataclass
class Environment:
    water: float = 0.8         # 0..1
    nutrients: float = 0.4     # 0..1; detritus pool that feeds algae/plant
    o2: float = 0.21           # fraction of air (toy)
    co2: float = 0.0006        # fraction (toy ~600ppm)
    temp_c: float = 22.0
    light_phase: float = 0.0   # 0..1 (phase of day-night cycle)
    day_length_s: float = 120.0

    def light(self, dt):
        """Return current light level 0..1 and update phase (simple sine day)."""
        self.light_phase = (self.light_phase + dt / self.day_length_s) % 1.0
        # daylight centered at phase 0.25 (noon). Use half-wave rectified sine
        ang = 2 * math.pi * self.light_phase
        raw = math.sin(ang)
        return max(0.0, raw)

# ------------------------------ Algae Grid ---------------------------------

class AlgaeGrid:
    """Simple wall biofilm represented by coarse grid storing biomass 0..1."""
    def __init__(self, w, h, cell=10, init_level=0.2):
        self.cell = cell
        self.cols = w // cell
        self.rows = h // cell
        self.grid = [[max(0.0, min(1.0, random.gauss(init_level, 0.05)))
                      for _ in range(self.cols)] for _ in range(self.rows)]

    def total_biomass(self):
        return sum(sum(row) for row in self.grid) / (self.cols * self.rows)

    def sample(self, pos: Vec):
        c = int(clamp(pos.x // self.cell, 0, self.cols - 1))
        r = int(clamp(pos.y // self.cell, 0, self.rows - 1))
        return self.grid[r][c]

    def eat(self, pos: Vec, amount: float) -> float:
        c = int(clamp(pos.x // self.cell, 0, self.cols - 1))
        r = int(clamp(pos.y // self.cell, 0, self.rows - 1))
        take = min(self.grid[r][c], amount)
        self.grid[r][c] -= take
        return take

    def grow(self, env: Environment, dt: float):
        light = env.light(0)  # peeking current light without advancing
        r_max = 0.3  # max growth rate per second at high light and nutrients
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.grid[r][c]
                # Monod-like limitation by light, nutrients, water
                lim = min(1.0, 0.2 + 0.8*light) * min(1.0, 0.3 + 0.7*env.nutrients) * min(1.0, env.water)
                growth = r_max * lim * x * (1 - x) * dt  # logistic
                resp = 0.02 * (1.0 - light) * x * dt     # dark respiration
                x = x + growth - resp
                self.grid[r][c] = clamp(x, 0.0, 1.0)
        # Lateral spread of algae (reproduction/colonization)
        spread = 0.05
        newgrid = [row[:] for row in self.grid]
        for rr in range(self.rows):
            for cc in range(self.cols):
                nbrs = []
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    r2 = (rr + dr) % self.rows
                    c2 = (cc + dc) % self.cols
                    nbrs.append(self.grid[r2][c2])
                avg = sum(nbrs) / len(nbrs)
                newgrid[rr][cc] = clamp(self.grid[rr][cc] + spread * (avg - self.grid[rr][cc]) * dt, 0.0, 1.0)
        self.grid = newgrid

        # Gas exchange: photosynthesis -> O2 up, CO2 down when light
        ps = 0.02 * light * self.total_biomass() * dt
        env.o2 = clamp(env.o2 + ps - 0.01 * (1.0 - light) * dt, 0.05, 0.35)
        env.co2 = clamp(env.co2 - 0.8 * ps + 0.005 * (1.0 - light) * dt, 0.0002, 0.01)
        # Nutrient uptake and recycling (slow leak from detritus)
        # env.nutrients = clamp(env.nutrients - 0.01 * light * dt + 0.003 * dt, 0.0, 1.0)
        env.nutrients = clamp(env.nutrients - 0.01 * light * dt - 0.001 * dt, 0.0, 1.0)


    def draw(self, surf):
        # draw faint green tiles based on biomass
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.grid[r][c]
                if x <= 0.005:
                    continue
                g = int(30 + 200 * x)
                color = (20, g, 20)
                pygame.draw.rect(surf, color, (c*self.cell, r*self.cell, self.cell, self.cell))

# ------------------------------ Plant Pool ---------------------------------

@dataclass
class Plant:
    biomass: float = 0.2  # 0..1

    def update(self, env: Environment, dt: float):
        light = env.light(0)
        growth = 0.15 * light * env.nutrients * self.biomass * (1 - self.biomass) * dt
        resp = 0.01 * (1.0 - light) * self.biomass * dt
        self.biomass = clamp(self.biomass + growth - resp, 0.0, 1.0)
        env.nutrients = clamp(env.nutrients - 0.02 * light * dt, 0.0, 1.0)
        env.o2 = clamp(env.o2 + 0.015 * light * self.biomass * dt - 0.006 * (1.0 - light) * dt, 0.05, 0.35)
        env.co2 = clamp(env.co2 - 0.012 * light * self.biomass * dt + 0.003 * (1.0 - light) * dt, 0.0002, 0.01)

    def draw(self, surf, center: Tuple[int, int], radius_max: int):
        # represent biomass as concentric mossy disk
        r = int(radius_max * math.sqrt(self.biomass))
        if r <= 0:
            return
        pygame.draw.circle(surf, (40, 130, 40), center, r)
        pygame.draw.circle(surf, (30, 90, 30), center, int(0.7*r), width=2)

# ------------------------------ Animals ------------------------------------

@dataclass
class Animal:
    pos: Vec
    vel: Vec
    energy: float
    age: float = 0.0
    max_age: float = 2000.0
    speed: float = 30.0
    sense: float = 40.0
    size: int = 2
    kind: str = "herbivore"   # or "predator"
    repro_threshold: float = 1.2

    def alive(self):
        return self.energy > 0 and self.age < self.max_age

    def step(self, dt, w, h, bias: Vec = None):
        jitter = Vec(random.uniform(-1, 1), random.uniform(-1, 1))
        v = self.vel * 0.6 + jitter * 0.8
        # occasional random reorientation “twitch”
        if random.random() < 0.05:
            v.rotate_ip(random.uniform(-45, 45))
        if v.length() == 0:
            v = Vec(1, 0)
        v = v.normalize() * self.speed
        self.pos += v * dt
        
        # torus wrap (no bouncing)
        if self.pos.x < 0: self.pos.x += w
        if self.pos.x >= w: self.pos.x -= w
        if self.pos.y < 0: self.pos.y += h
        if self.pos.y >= h: self.pos.y -= h
        
        self.vel = v

    def can_reproduce(self):
        return self.energy >= self.repro_threshold

@dataclass
class Herbivore(Animal):
    kind: str = "herbivore"
    speed: float = 35.0
    size: int = 2

    def forage_bias(self, algae: AlgaeGrid) -> Vec:
        # sample a few directions, move toward higher algae
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

@dataclass
class Predator(Animal):
    kind: str = "predator"
    speed: float = 45.0
    size: int = 3

    def hunt_bias(self, prey: List[Herbivore]) -> Tuple[Vec, Herbivore]:
        target = None
        best_d2 = self.sense**2
        for h in prey:
            d2 = (h.pos - self.pos).length_squared()
            if d2 < best_d2:
                best_d2 = d2
                target = h
        if target is None:
            return Vec(0, 0), None
        dir = (target.pos - self.pos)
        if dir.length() > 0:
            dir = dir.normalize()
        return dir, target

    def try_eat(self, target: Herbivore) -> bool:
        if (target.pos - self.pos).length() < (self.size + target.size + 2):
            self.energy += 0.6
            target.energy = -1  # kill
            return True
        return False

# ------------------------------ UI Widgets ---------------------------------

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

class PlantPatch:
    def __init__(self, pos: Vec, biomass: float = 0.3):
        self.pos = pos
        self.biomass = biomass  # 0..1

    def update(self, env: Environment, dt: float):
        light = env.light(0)
        # logistic growth + light & nutrient limitation
        growth = 0.12 * light * env.nutrients * self.biomass * (1 - self.biomass) * dt
        resp = 0.01 * (1.0 - light) * self.biomass * dt
        self.biomass = clamp(self.biomass + growth - resp, 0.0, 1.0)
        # nutrient uptake and gas exchange
        env.nutrients = clamp(env.nutrients - 0.02 * light * dt * max(0.2, self.biomass), 0.0, 1.0)
        env.o2 = clamp(env.o2 + 0.010 * light * self.biomass * dt - 0.004 * (1.0 - light) * dt, 0.05, 0.35)
        env.co2 = clamp(env.co2 - 0.008 * light * self.biomass * dt + 0.003 * (1.0 - light) * dt, 0.0002, 0.01)


# ------------------------------ Simulation ---------------------------------

class Simulation:
    def __init__(self, args):
        self.w, self.h = args.width, args.height
        self.env = Environment(water=args.water, o2=args.o2, co2=args.co2, light_phase=0.0,
                               day_length_s=args.day_length)
        self.algae = AlgaeGrid(self.w, self.h, cell=8, init_level=args.algae_init)
        self.plants: List[PlantPatch] = []
        for _ in range(args.plants):
            self.plants.append(
                PlantPatch(
                    pos=Vec(random.uniform(0, self.w), random.uniform(0, self.h)),
                    biomass=0.25 + random.random() * 0.2
                )
            )

        self.plant = Plant(biomass=args.plant_init)
        self.herbivores: List[Herbivore] = []
        self.predators: List[Predator] = []
        self.spawn_initial(args)
        self.time_scale = 1.0
        self.running = True
        self.paused = False
        self.args = args


    def spawn_initial(self, args):
        for _ in range(args.herbivores):
            self.herbivores.append(self._mk_herbivore())

    def _mk_herbivore(self):
        return Herbivore(pos=Vec(random.uniform(0, self.w), random.uniform(0, self.h)),
                         vel=Vec(random.uniform(-1,1), random.uniform(-1,1)), energy=1.0,
                         max_age=random.uniform(800, 2000), repro_threshold=1.1)

    def _mk_predator(self):
        return Predator(pos=Vec(random.uniform(0, self.w), random.uniform(0, self.h)),
                        vel=Vec(random.uniform(-1,1), random.uniform(-1,1)), energy=1.2,
                        max_age=random.uniform(900, 2200), repro_threshold=1.6)

    def update(self, dt):
        if self.paused:
            return
        dt *= self.time_scale
        light = self.env.light(dt)
        # Primary producers
        self.algae.grow(self.env, dt)
        # Plants grow, reproduce, and die
        for p in self.plants[:]:
            p.update(self.env, dt)
            # reproduction: spawn a nearby patch if large enough
            if p.biomass > 0.6 and len(self.plants) < self.args.plant_cap and random.random() < 0.02 * dt:
                offset = Vec(random.uniform(-30, 30), random.uniform(-30, 30))
                new_pos = Vec((p.pos.x + offset.x) % self.w, (p.pos.y + offset.y) % self.h)
                self.plants.append(PlantPatch(pos=new_pos, biomass=0.2))
                p.biomass *= 0.85
            # senescence: tiny patches recycle to nutrients and disappear
            if p.biomass <= 0.02:
                self.env.nutrients = clamp(self.env.nutrients + 0.05, 0.0, 1.0)
                self.plants.remove(p)
        
        self.plant.update(self.env, dt)
        # Animal behaviors
        # Herbivores forage
        for h in self.herbivores:
            bias = h.forage_bias(self.algae)
            h.step(dt, self.w, self.h, bias)
            # eat algae underfoot
            h.eat(self.algae, dt)
            # respiration: consume O2
            self.env.o2 = clamp(self.env.o2 - 0.0001 * dt, 0.05, 0.35)
            self.env.co2 = clamp(self.env.co2 + 0.00008 * dt, 0.0002, 0.01)
        # Clean up dead / old; recycle to nutrients
        before_h = len(self.herbivores)
        before_p = len(self.predators)
        self.herbivores = [h for h in self.herbivores if h.alive()]
        self.predators = [p for p in self.predators if p.alive()]
        death_count = (before_h - len(self.herbivores)) + (before_p - len(self.predators))
        self.env.nutrients = clamp(self.env.nutrients + 0.01 * death_count, 0.0, 1.0)
        # Reproduction (simple: need nearby mate + energy threshold + cap)
        self._reproduce()
        # Leakages in sealed bottle (very small to keep dynamics stable)
        self.env.water = clamp(self.env.water - 0.00001 * dt + 0.000005 * dt, 0.2, 1.0)
        # If producers are completely absent, nutrients slowly drift toward zero
        if self.algae.total_biomass() < 1e-4:
            # (If you add plant patches in part B, also include their biomass in this check)
            self.env.nutrients = clamp(self.env.nutrients - 0.002 * dt, 0.0, 1.0)

        # Temperature slight daily wave
        self.env.temp_c = 21.0 + 1.5 * math.sin(2*math.pi*self.env.light_phase)

    def _reproduce(self):
        # Herbivores
        if len(self.herbivores) < self.args.animal_cap:
            random.shuffle(self.herbivores)
            for i in range(0, len(self.herbivores)-1, 2):
                a, b = self.herbivores[i], self.herbivores[i+1]
                if a.can_reproduce() and b.can_reproduce() and (a.pos - b.pos).length() < 12:
                    child = self._mk_herbivore()
                    child.pos = (a.pos + b.pos) / 2
                    child.energy = 0.7
                    a.energy *= 0.65; b.energy *= 0.65
                    self.herbivores.append(child)
                    if len(self.herbivores) >= self.args.animal_cap:
                        break

    def draw(self, surf, font):
        surf.fill((12, 12, 18))
        # algae tiles
        self.algae.draw(surf)
        # plant
        #self.plant.draw(surf, (self.w//2, self.h//2), radius_max=min(self.w, self.h)//4)
        # draw plants
        for p in self.plants:
            rad = max(2, int(8 * math.sqrt(p.biomass)))
            pygame.draw.circle(surf, (40, 130, 40), (int(p.pos.x), int(p.pos.y)), rad)
            pygame.draw.circle(surf, (30, 90, 30), (int(p.pos.x), int(p.pos.y)), max(1, rad // 2), width=2)
        # animals
        for h in self.herbivores:
            pygame.draw.circle(surf, (180, 220, 120), (int(h.pos.x), int(h.pos.y)), h.size)
        for p in self.predators:
            pygame.draw.circle(surf, (220, 120, 120), (int(p.pos.x), int(p.pos.y)), p.size)
        # HUD
        light = self.env.light(0)
        hud = f"Light {light:0.2f}  O2 {self.env.o2:0.3f}  CO2 {self.env.co2:0.4f}  Nutr {self.env.nutrients:0.2f}  Water {self.env.water:0.2f}  Plant {self.plant.biomass:0.2f}  Algae {self.algae.total_biomass():0.2f}  H {len(self.herbivores)}  x{self.time_scale:0.1f}"
        # hud = f"O2 {self.env.o2:0.3f}  CO2 {self.env.co2:0.4f}  Nutr {self.env.nutrients:0.2f}  Water {self.env.water:0.2f}  Plants {len(self.plants)}  Critters {len(self.critters)}  x{self.time_scale:0.1f}"

        text = font.render(hud, True, (230, 230, 230))
        surf.blit(text, (10, 8))

# ------------------------------ Main / App ---------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Sealed terrarium simulation (Pygame)")
    parser.add_argument('--width', type=int, default=900)
    parser.add_argument('--height', type=int, default=700)
    parser.add_argument('--tick-ms', type=int, default=50, help='Base tick in ms (smaller is faster)')
    parser.add_argument('--day-length', type=float, default=120.0, help='Seconds per simulated day')
    # Environment overrides
    parser.add_argument('--water', type=float, default=0.85)
    parser.add_argument('--o2', type=float, default=0.21)
    parser.add_argument('--co2', type=float, default=0.0006)
    parser.add_argument('--algae-init', type=float, default=0.20)
    parser.add_argument('--plant-init', type=float, default=0.30)
    # Animals
    parser.add_argument('--herbivores', type=int, default=25)
    parser.add_argument('--animal-cap', type=int, default=100)
    # RNG
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--plants', type=int, default=3)
    parser.add_argument('--plant-cap', type=int, default=20)


    args = parser.parse_args(argv)
    if args.seed is not None:
        random.seed(args.seed)

    pygame.init()
    pygame.display.set_caption("Terrarium in a Bottle – sealed ecosystem sim")
    screen = pygame.display.set_mode((args.width, args.height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas', 16)

    sim = Simulation(args)

    # UI buttons
    btns = []
    margin = 6; bw = 110; bh = 28
    def add_btn(x, y, label, action):
        btns.append(Button((x, y, bw, bh), label, action))
    add_btn(args.width - (bw+margin)*5, args.height - (bh+margin), '− speed', lambda: setattr(sim, 'time_scale', max(0.1, sim.time_scale/1.5)))
    add_btn(args.width - (bw+margin)*4, args.height - (bh+margin), 'pause/res', lambda: setattr(sim, 'paused', not sim.paused))
    add_btn(args.width - (bw+margin)*3, args.height - (bh+margin), '+ speed', lambda: setattr(sim, 'time_scale', min(50.0, sim.time_scale*1.5)))
    add_btn(args.width - (bw+margin)*2, args.height - (bh+margin), 'spawn', lambda: [sim.herbivores.append(sim._mk_herbivore()) if len(sim.herbivores)<args.animal_cap else None])
    def stats_action():
        # small pulse of printout; could be extended to CSV logging
        print(f"t={pygame.time.get_ticks()/1000:.1f}s light={sim.env.light(0):.2f} O2={sim.env.o2:.3f} CO2={sim.env.co2:.4f} nutr={sim.env.nutrients:.2f} plant={sim.plant.biomass:.2f} algae={sim.algae.total_biomass():.2f} H={len(sim.herbivores)} P={len(sim.predators)}")
    add_btn(args.width - (bw+margin)*1, args.height - (bh+margin), 'stats', stats_action)

    # Reset button on the left corner
    def do_reset():
        nonlocal sim
        sim = Simulation(args)
    btn_reset = Button((margin, args.height - (bh+margin), 90, bh), 'reset', do_reset)

    running = True
    base_tick = args.tick_ms

    while running:
        # Events
        for ev in pygame.event.get():
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
            btn_reset.handle(ev)
            for b in btns:
                b.handle(ev)

        # Update
        dt = base_tick / 1000.0
        sim.update(dt)

        # Draw
        sim.draw(screen, font)
        btn_reset.draw(screen, font)
        for b in btns:
            b.draw(screen, font)
        pygame.display.flip()

        clock.tick(1000 // base_tick)

    pygame.quit()

if __name__ == '__main__':
    main()


