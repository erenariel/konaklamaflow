"""Illustrative local compute latency only, not real check-in or PMS latency."""
import json
from pathlib import Path
from statistics import median
from time import perf_counter_ns
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from konaklamaflow.operations import plan_operations

source=json.loads((ROOT/'examples/operations-demo.json').read_text(encoding='utf-8'))
for _ in range(30):plan_operations(source,'2026-11-12','14:01')
samples=[]
for _ in range(500):
    start=perf_counter_ns()
    plan_operations(source,'2026-11-12','14:01')
    samples.append((perf_counter_ns()-start)/1_000_000)
samples.sort()
print(f'LOCAL SYNTHETIC COMPUTE ONLY: N=500, P50={median(samples):.3f}ms, P95={samples[int(len(samples)*.95)-1]:.3f}ms')
print('NOT measured: network, actual PMS, external APIs, identity verification, KBS, payments, guest wait, human approval.')
