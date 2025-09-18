#!/usr/bin/env python3
"""
https://chatgpt.com/share/68cc618a-ac40-8005-a783-97fb9a8c9e6f

Persistent Simulation Toy — v2 (stabilized energy + livelier institutions)

Changes vs v1 (to stop blow‑ups & make dynamics move):
1) **Progressive metabolism**: base + proportional to stored energy.
2) **Spoilage/leakage**: agents lose a % of stored energy each year; institutions lose admin % of budgets.
3) **Energy caps**: hard cap per agent to prevent runaway hoarding.
4) **Learning cooperation**: agents nudge their coop_bias after each interaction based on realized payoff.
5) **Institution churn**: auto‑dissolve when tiny & broke; auto‑found new clubs when unaffiliated clusters appear.
6) **Drought shocks**: occasional regional resource collapses.
7) **Dashboard metric fix**: coop rate now measured from recent interactions, not static bias.

Run:
  python sim_anim_v2.py --ticks 100000 --animate --interval 120

Deps: pip install numpy matplotlib
"""
from __future__ import annotations
import argparse, json, math, random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# ----------------------- Parameters (defaults) -----------------------
DEFAULTS = dict(
    W=40, H=40, N_AGENTS=300,
    R_MAX=10.0, G=0.12,              # slightly slower resource growth
    HARVEST_ALPHA=0.45,              # a touch lower than v1
    COOP_SHARE=0.18,
    METABOLISM_BASE=0.6,             # progressive metabolism = base + k*energy
    METABOLISM_K=0.015,
    START_ENERGY=5.0,
    ENERGY_CAP=20.0,                 # hard cap per agent
    REPUTATION_STEP=0.2,
    MEM_K=10,
    YEAR_TICKS=10,
    VOTE_PERIOD_YEARS=50,
    SNAP_EVERY_TICKS=1000,
    SPOILAGE=0.05,                   # yearly % loss of stored energy
    ADMIN_LEAK=0.02,                 # yearly budget admin leak
    MONITOR_BASE=0.02,               # denom in sanction probability
    DROUGHT_EVERY_YEARS=1500,
    DROUGHT_SIZE=8,
    DROUGHT_LEN_TICKS=300,
    NEW_CLUB_SCAN_YEARS=5,           # look for clusters to found new club
    NEW_CLUB_MIN_CLUSTER=10,
    NEW_CLUB_RADIUS=2,
    DISSOLVE_MIN_MEM=3,
    DISSOLVE_MIN_BUDGET=0.1,
    DISSOLVE_GRACE_YEARS=20,
)

# ----------------------- Utilities -----------------------
def torus(x: int, y: int, W: int, H: int) -> Tuple[int, int]:
    return x % W, y % H

@dataclass
class Institution:
    id: int
    tau: float = 0.1
    sanc: float = 0.1
    delta: float = 0.1
    budget: float = 0.0
    members: set = field(default_factory=set)
    broke_years: int = 0
    def describe(self):
        return dict(id=self.id, tau=self.tau, sanc=self.sanc, delta=self.delta,
                    budget=round(self.budget,2), members=len(self.members))

class Agent:
    _id = 0
    def __init__(self, world: 'World'):
        Agent._id += 1
        self.id = Agent._id
        self.world = world
        self.x = random.randrange(world.W)
        self.y = random.randrange(world.H)
        self.energy = world.START_ENERGY
        self.reps: Dict[int, float] = defaultdict(float)
        self.mem_order = deque(maxlen=world.MEM_K)
        self.inst: Optional[int] = None
        self.coop_bias = random.uniform(-0.2, 0.2)
    def move(self):
        W,H=self.world.W,self.world.H
        best=(self.x,self.y); best_r=self.world.R[self.x,self.y]
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0: continue
                nx,ny=torus(self.x+dx,self.y+dy,W,H)
                r=self.world.R[nx,ny]
                if r>best_r: best=(nx,ny); best_r=r
        self.x,self.y=best
    def harvest(self)->float:
        crowd=self.world.occ[self.x,self.y]
        r=self.world.R[self.x,self.y]
        take=self.world.HARVEST_ALPHA*r/(1+0.35*max(0,crowd-1))
        take=min(take,r)
        self.world.R[self.x,self.y]-=take
        self.energy=min(self.world.ENERGY_CAP,self.energy+take)
        return take
    def choose_partner(self, here_ids: List[int]):
        if len(here_ids)<=1: return None
        others=[aid for aid in here_ids if aid!=self.id]
        def score(aid:int):
            rep=self.reps[aid]
            halo=0.0
            other_inst=self.world.agent[aid].inst
            if self.inst and other_inst==self.inst: halo=0.05
            return rep+halo+random.uniform(-0.05,0.05)
        return max(others,key=score)
    def decide_coop(self, partner_id:int)->bool:
        base=self.coop_bias+self.reps[partner_id]
        if self.inst and self.world.agent[partner_id].inst==self.inst:
            base+=self.world.insts[self.inst].delta
        p=1/(1+math.exp(-3*base))
        return random.random()<p
    def update_rep(self, partner_id:int, delta:float):
        v=self.reps[partner_id]+delta
        self.reps[partner_id]=max(-1.0,min(1.0,v))
        self.mem_order.append(partner_id)
        if len(self.mem_order)>self.world.MEM_K:
            old=self.mem_order.popleft(); self.reps[old]*=0.9
    def learn_from_payoff(self, payoff:float, cooperated:bool):
        # small nudges: if cooperation paid, increase bias; else decrease (and vice versa)
        step=0.02
        if cooperated:
            self.coop_bias += step if payoff>0 else -step
        else:
            self.coop_bias += -step if payoff>0 else step
        self.coop_bias=max(-1.0,min(1.0,self.coop_bias))
    def pay_metabolism(self)->bool:
        burn=self.world.METABOLISM_BASE + self.world.METABOLISM_K*self.energy
        self.energy -= burn
        return self.energy>0
    def join_leave_rule(self, year:int):
        if year%1!=0: return
        if self.inst and (self.energy<0.4*self.world.START_ENERGY) and random.random()<0.3:
            self.world.insts[self.inst].members.discard(self.id); self.inst=None
        if not self.inst and self.world.insts and random.random()<0.15:
            cand=max(self.world.insts.values(), key=lambda I: I.budget)
            self.inst=cand.id; cand.members.add(self.id); cand.budget+=0.05

class World:
    def __init__(self,args):
        for k,v in DEFAULTS.items(): setattr(self,k,v)
        self.W,self.H=args.grid
        self.N_AGENTS=args.agents
        self.YEAR_TICKS=args.year_ticks
        self.R=np.full((self.W,self.H), self.R_MAX*0.5, dtype=np.float32)
        self.occ=np.zeros((self.W,self.H), dtype=np.int32)
        self.t=0; self.year=0
        self.insts:Dict[int,Institution]={}
        self.next_inst_id=1
        self.agents:List[Agent]=[]
        self.agent:Dict[int,Agent]={}
        self.annals:List[dict]=[]
        # dashboard metrics
        self.mt=[]; self.m_coop=[]; self.m_inst=[]; self.m_energy=[]
        self._recent_coops=deque(maxlen=2000)  # rolling interaction outcomes
        # drought state
        self._drought_until=-1; self._drought_mask=None
    def init_world(self):
        I=Institution(self.next_inst_id, tau=0.12, sanc=0.12, delta=0.12)
        self.insts[I.id]=I; self.next_inst_id+=1
        for _ in range(self.N_AGENTS):
            a=Agent(self)
            if random.random()<0.4: a.inst=I.id; I.members.add(a.id)
            self.agents.append(a); self.agent[a.id]=a
    def map_occupancy(self):
        self.occ.fill(0)
        for a in self.agents: self.occ[a.x,a.y]+=1
    def step_resources(self):
        r=self.R
        if self._drought_until>=self.t and self._drought_mask is not None:
            r[self._drought_mask]=0.0
        r = r + self.G*r*(1 - r/self.R_MAX)
        np.clip(r,0.0,self.R_MAX,out=r)
        self.R=r
    def maybe_drought(self):
        if self.year>0 and self.year%self.DROUGHT_EVERY_YEARS==0 and self._drought_until<self.t:
            x0=random.randrange(self.W-self.DROUGHT_SIZE)
            y0=random.randrange(self.H-self.DROUGHT_SIZE)
            mask=np.zeros_like(self.R, dtype=bool)
            mask[x0:x0+self.DROUGHT_SIZE, y0:y0+self.DROUGHT_SIZE]=True
            self._drought_mask=mask
            self._drought_until=self.t + self.DROUGHT_LEN_TICKS
            self.annals.append({"event":"drought","t":self.t,"year":self.year,"region":(x0,y0)})
    def interact_phase(self):
        cell_to_ids:Dict[Tuple[int,int],List[int]]=defaultdict(list)
        for a in self.agents: cell_to_ids[(a.x,a.y)].append(a.id)
        for ids in cell_to_ids.values():
            for aid in ids:
                a=self.agent[aid]
                pid=a.choose_partner(ids)
                if pid is None: continue
                p=self.agent[pid]
                e0_a, e0_p = a.energy, p.energy
                coop_a=a.decide_coop(pid); coop_p=p.decide_coop(a.id)
                if coop_a and coop_p:
                    share=self.COOP_SHARE*min(a.energy,p.energy)
                    a.energy=min(self.ENERGY_CAP,a.energy+share)
                    p.energy=min(self.ENERGY_CAP,p.energy+share)
                    a.update_rep(pid,+self.REPUTATION_STEP); p.update_rep(a.id,+self.REPUTATION_STEP)
                    self._recent_coops.append(1.0)
                elif coop_a and not coop_p:
                    steal=self.COOP_SHARE*a.energy; steal=min(steal,a.energy)
                    a.energy-=steal; p.energy=min(self.ENERGY_CAP,p.energy+steal)
                    a.update_rep(pid,-self.REPUTATION_STEP); p.update_rep(a.id,+self.REPUTATION_STEP/2)
                    self._recent_coops.append(0.0); self.sanction(exploiter=p, victim=a)
                elif not coop_a and coop_p:
                    steal=self.COOP_SHARE*p.energy; steal=min(steal,p.energy)
                    p.energy-=steal; a.energy=min(self.ENERGY_CAP,a.energy+steal)
                    a.update_rep(pid,+self.REPUTATION_STEP/2); p.update_rep(a.id,-self.REPUTATION_STEP)
                    self._recent_coops.append(0.0); self.sanction(exploiter=a, victim=p)
                else:
                    a.update_rep(pid,-0.05); p.update_rep(a.id,-0.05)
                    self._recent_coops.append(0.0)
                # learning updates (payoff = delta energy)
                a.learn_from_payoff(a.energy-e0_a, cooperated=coop_a)
                p.learn_from_payoff(p.energy-e0_p, cooperated=coop_p)
    def sanction(self, exploiter:Agent, victim:Agent):
        if victim.inst and exploiter.inst==victim.inst:
            I=self.insts[victim.inst]
            denom=len(I.members)*self.MONITOR_BASE + 1e-6
            p=min(1.0, I.budget/denom)
            if random.random()<p:
                fine=I.sanc
                exploiter.energy-=fine; I.budget+=fine
                exploiter.coop_bias -= 0.03  # sanctions also teach
    def fiscal_phase(self):
        # yearly: taxes, stipends, admin leak, votes
        if self.t % self.YEAR_TICKS == 0:
            for a in self.agents:
                if a.inst and a.energy>self.START_ENERGY:
                    I=self.insts[a.inst]
                    gain=a.energy-self.START_ENERGY
                    tax=min(a.energy, I.tau*gain)
                    a.energy-=tax; I.budget+=tax
                if a.inst and a.energy<self.METABOLISM_BASE*3:
                    I=self.insts[a.inst]
                    stipend=min(0.4, I.budget)
                    a.energy=min(self.ENERGY_CAP, a.energy+stipend); I.budget-=stipend
            # admin leakage & broke tracking
            for I in list(self.insts.values()):
                leak=I.budget*self.ADMIN_LEAK
                I.budget-=leak
                if I.budget<self.DISSOLVE_MIN_BUDGET and len(I.members)<self.DISSOLVE_MIN_MEM:
                    I.broke_years+=1
                else:
                    I.broke_years=0
            # votes
            if self.year>0 and self.year % self.VOTE_PERIOD_YEARS==0:
                for I in self.insts.values():
                    if not I.members: continue
                    slates=[(
                        float(np.clip(I.tau + random.uniform(-0.07,0.07),0.0,0.35)),
                        float(np.clip(I.sanc+ random.uniform(-0.07,0.07),0.0,0.35)),
                        float(np.clip(I.delta+random.uniform(-0.07,0.07),0.0,0.35)),
                    ) for _ in range(2)]
                    votes=[0,0]
                    for aid in list(I.members):
                        a=self.agent.get(aid); 
                        if not a: continue
                        pref = 0 if (a.energy + random.uniform(-1,1)) > self.START_ENERGY else 1
                        votes[pref]+=1
                    pick=0 if votes[0]>=votes[1] else 1
                    I.tau,I.sanc,I.delta=slates[pick]
    def churn_institutions(self):
        # dissolve
        for iid in list(self.insts.keys()):
            I=self.insts[iid]
            if I.broke_years>=self.DISSOLVE_GRACE_YEARS:
                for aid in list(I.members):
                    a=self.agent.get(aid)
                    if a: a.inst=None
                del self.insts[iid]
                self.annals.append({"event":"dissolve","year":self.year,"id":iid})
        # found new ones around clusters of unaffiliated agents
        if self.year%self.NEW_CLUB_SCAN_YEARS==0:
            # grid scan
            for x in range(0,self.W, self.NEW_CLUB_RADIUS+1):
                for y in range(0,self.H, self.NEW_CLUB_RADIUS+1):
                    cnt=0; sample=None
                    for dx in range(-self.NEW_CLUB_RADIUS,self.NEW_CLUB_RADIUS+1):
                        for dy in range(-self.NEW_CLUB_RADIUS,self.NEW_CLUB_RADIUS+1):
                            nx,ny=torus(x+dx,y+dy,self.W,self.H)
                            for a in self.agents:
                                if a.x==nx and a.y==ny and a.inst is None:
                                    cnt+=1; sample=a
                    if cnt>=self.NEW_CLUB_MIN_CLUSTER and sample:
                        iid=self.next_inst_id; self.next_inst_id+=1
                        I=Institution(iid, tau=0.1+random.uniform(-0.05,0.1),
                                      sanc=0.1+random.uniform(-0.05,0.1),
                                      delta=0.1+random.uniform(-0.05,0.1),
                                      budget=1.0)
                        self.insts[iid]=I
                        # recruit nearby unaffiliated
                        for a in self.agents:
                            if abs(a.x-x)<=self.NEW_CLUB_RADIUS and abs(a.y-y)<=self.NEW_CLUB_RADIUS and a.inst is None:
                                if random.random()<0.7:
                                    a.inst=iid; I.members.add(a.id)
                        self.annals.append({"event":"found","year":self.year,"id":iid,"members":len(I.members)})
    def yearly_maintenance(self):
        # agent spoilage; institution admin leak handled in fiscal_phase
        for a in self.agents:
            a.energy *= (1.0 - self.SPOILAGE)
            if a.energy>self.ENERGY_CAP: a.energy=self.ENERGY_CAP
    def mortality_and_join(self):
        survivors:List[Agent]=[]
        for a in self.agents:
            alive=a.pay_metabolism()
            if alive:
                a.join_leave_rule(self.year); survivors.append(a)
            else:
                na=Agent(self)
                if random.random()<0.25 and self.insts:
                    I=random.choice(list(self.insts.values()))
                    na.inst=I.id; I.members.add(na.id); I.budget+=0.03
                survivors.append(na); self.agent[na.id]=na
        self.agents=survivors
    def log_metrics(self):
        if self.t % self.YEAR_TICKS == 0:
            self.year=self.t//self.YEAR_TICKS
            coop_rate = float(np.mean(self._recent_coops)) if self._recent_coops else 0.0
            avg_energy=float(np.mean([a.energy for a in self.agents]))
            self.mt.append(self.year)
            self.m_coop.append(coop_rate)
            self.m_inst.append(len([I for I in self.insts.values() if I.members]))
            self.m_energy.append(avg_energy)
    # -------------- main step --------------
    def step_once(self):
        self.t += 1
        for a in self.agents: a.move()
        self.map_occupancy()
        for a in self.agents: a.harvest()
        self.interact_phase()
        self.fiscal_phase()
        if self.t % self.YEAR_TICKS == 0:
            self.yearly_maintenance()
            self.maybe_drought()
            self.churn_institutions()
        self.mortality_and_join()
        self.step_resources()
        self.log_metrics()

# ----------------------- Animation / CLI -----------------------
def run(args):
    random.seed(args.seed); np.random.seed(args.seed)
    w=World(args); w.init_world()
    # Figure
    if args.animate:
        if args.no_dashboard:
            fig,ax0=plt.subplots(1,1,figsize=(7,6)); ax_list=[ax0]
        else:
            fig=plt.figure(figsize=(12,6))
            gs=fig.add_gridspec(2,3,width_ratios=[1.1,0.9,0.9],height_ratios=[1,1])
            ax0=fig.add_subplot(gs[:,0]); ax1=fig.add_subplot(gs[0,1]); ax2=fig.add_subplot(gs[1,1]); ax3=fig.add_subplot(gs[:,2])
            ax_list=[ax0,ax1,ax2,ax3]
        ax0.set_title("Resources + agents (institutions colored)")
        im=ax0.imshow(w.R.T, origin='lower', interpolation='nearest', vmin=0, vmax=w.R_MAX)
        scat=ax0.scatter([],[], s=8, alpha=0.9)
        txt=ax0.text(0.02,0.98,'', transform=ax0.transAxes, va='top', ha='left', fontsize=9,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.6))
        ax0.set_xlim(-0.5,w.W-0.5); ax0.set_ylim(-0.5,w.H-0.5)
        if not args.no_dashboard:
            ax1.set_title("Cooperation (rolling)"); ax1.set_ylim(0,1); line1,=ax1.plot([],[])
            ax2.set_title("# Institutions"); line2,=ax2.plot([],[])
            ax3.set_title("Avg energy"); line3,=ax3.plot([],[])
    def update(_):
        w.step_once()
        im.set_data(w.R.T)
        xs=[a.x for a in w.agents]; ys=[a.y for a in w.agents]
        colors=[]
        for a in w.agents:
            if a.inst is None: colors.append((0.5,0.5,0.5))
            else:
                r=((a.inst*37)%255)/255.0; g=((a.inst*73)%255)/255.0; b=((a.inst*19)%255)/255.0
                colors.append((r,g,b))
        scat.set_offsets(np.c_[xs,ys]); scat.set_color(colors)
        txt.set_text(f"tick {w.t} (year {w.year})\n#agents {len(w.agents)} | #inst {len([I for I in w.insts.values() if I.members])}")
        if not args.no_dashboard and len(w.mt)>2:
            K=600; t=np.array(w.mt[-K:]); c=np.array(w.m_coop[-K:]); n=np.array(w.m_inst[-K:]); e=np.array(w.m_energy[-K:])
            line1.set_data(t,c); ax1.set_xlim(t.min(), t.max())
            line2.set_data(t,n); ax2.set_xlim(t.min(), t.max()); ax2.set_ylim(0, max(5, n.max()+1) if n.size else 5)
            line3.set_data(t,e); ax3.set_xlim(t.min(), t.max()); ax3.set_ylim(0, max(2, e.max()+1) if e.size else 2)
        return ax_list
    if args.animate:
        frames=args.ticks if args.save_mp4 else None
        ani=animation.FuncAnimation(plt.gcf(), update, interval=args.interval, frames=frames, blit=False)
        if args.save_mp4:
            ani.save(args.save_mp4, fps=1000.0/max(1.0,args.interval))
        plt.tight_layout(); plt.show()
    else:
        for _ in range(args.ticks): w.step_once()
        print(json.dumps({"years":w.year, "inst":{i:I.describe() for i,I in w.insts.items()}}, indent=2))

# ----------------------- CLI -----------------------

def parse_args(argv=None):
    p=argparse.ArgumentParser(description="Persistent simulation v2")
    p.add_argument('--ticks', type=int, default=20000)
    p.add_argument('--year_ticks', type=int, default=DEFAULTS['YEAR_TICKS'])
    p.add_argument('--grid', type=int, nargs=2, default=[DEFAULTS['W'], DEFAULTS['H']])
    p.add_argument('--agents', type=int, default=DEFAULTS['N_AGENTS'])
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--animate', action='store_true'); p.add_argument('--no-animate', dest='animate', action='store_false'); p.set_defaults(animate=True)
    p.add_argument('--interval', type=int, default=120)
    p.add_argument('--no-dashboard', action='store_true')
    p.add_argument('--save_mp4', type=str, default='')
    return p.parse_args(argv)

if __name__=='__main__':
    args=parse_args(); run(args)

