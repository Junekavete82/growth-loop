"""Generates SIMULATED SaaS usage data. No real customers. Seeded, so results reproduce."""
import os
import numpy as np, pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)
N, WEEKS, START = 3000, 26, date(2026, 1, 5)
# channel: (share of signups, weekly churn hazard, assumed CAC in USD)
CHANNELS = {"referral": (.20, .035, 12), "search": (.35, .05, 28), "social": (.30, .07, 35), "outbound": (.15, .06, 55)}
names = list(CHANNELS)
channel = rng.choice(names, N, p=[CHANNELS[c][0] for c in names])
plan = rng.choice(["basic", "pro"], N, p=[.7, .3])
sw = rng.integers(0, 22, N)  # signup week, so everyone is observable for 4+ weeks
users = pd.DataFrame({"user_id": range(N), "sw": sw,
                      "signup_date": [(START + timedelta(weeks=int(w))).isoformat() for w in sw],
                      "channel": channel, "plan": plan})
rows = []
for u in range(N):
    lam = rng.gamma(2.5, 1.4)  # starting sessions per week
    base = CHANNELS[channel[u]][1] * (0.7 if plan[u] == "pro" else 1)
    for cw in range(sw[u], WEEKS):
        if cw > sw[u]:
            lam *= rng.uniform(.88, 1.03)                      # engagement drifts down over time
            if rng.random() < base * (2.2 if lam < 1.2 else 1):  # low engagement raises churn risk
                break
        s = int(rng.poisson(lam))
        if s > 0:
            rows.append((u, cw, s, int(np.clip(rng.normal(2 + lam * .6, 1), 1, 8))))
act = pd.DataFrame(rows, columns=["user_id", "cw", "sessions", "features"])
os.makedirs("data", exist_ok=True)
users.to_csv("data/users.csv", index=False); act.to_csv("data/activity.csv", index=False)
print(f"SIMULATED data: {len(users)} users, {len(act)} weekly activity rows")
