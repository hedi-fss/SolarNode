#!/usr/bin/env python3
"""Generate scenario comparison figures for the report."""
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.simulation import SimulationService

os.makedirs('figures', exist_ok=True)

sim = SimulationService()

# 1. PDR vs Node Density for different patterns (terrain=rural)
patterns = ['random', 'grid', 'clustered']
densities = [10, 25, 50, 75, 100]
plt.figure(figsize=(10,6))
for pattern in patterns:
    pdrs = []
    for n in densities:
        res = sim.run_scenario_with_pattern(n_nodes=n, pattern=pattern, terrain='rural', runs=20)
        pdrs.append(res['pdr'])
    plt.plot(densities, pdrs, marker='o', label=pattern.capitalize())
plt.xlabel('Number of Nodes')
plt.ylabel('Packet Delivery Ratio (%)')
plt.title('PDR vs Node Density by Deployment Pattern')
plt.legend()
plt.grid(True)
plt.savefig('figures/pdr_vs_density.png', dpi=300)
plt.close()

# 2. PDR vs Terrain (fixed 50 nodes, random pattern)
terrains = ['urban', 'rural', 'forest', 'desert']
pdrs = []
for t in terrains:
    res = sim.run_scenario_with_pattern(n_nodes=50, pattern='random', terrain=t, runs=20)
    pdrs.append(res['pdr'])
plt.figure(figsize=(8,5))
plt.bar(terrains, pdrs, color=['#ff6b6b','#4ecdc4','#ffd93d','#6c5ce7'])
plt.ylabel('Packet Delivery Ratio (%)')
plt.title('PDR by Terrain Type (50 nodes, random deployment)')
plt.grid(axis='y')
plt.savefig('figures/pdr_vs_terrain.png', dpi=300)
plt.close()

print("✅ Scenario figures generated in figures/")
