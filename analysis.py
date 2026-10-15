"""Cohort retention (SQL), revenue vs CAC, Power User / At-Risk tagging, and a back-test of the At-Risk rule."""
import sqlite3, json
import pandas as pd

WEEKS = 26
CAC = {"referral": 12, "search": 28, "social": 35, "outbound": 55}  # assumed USD per signup
PRICE = {"basic": 15, "pro": 40}                                    # assumed USD per month
users = pd.read_csv("data/users.csv"); act = pd.read_csv("data/activity.csv")

con = sqlite3.connect(":memory:"); users.to_sql("users", con); act.to_sql("activity", con)
ret = pd.read_sql(open("sql/retention.sql").read(), con)
last_signup = users.groupby(users.signup_date.str[:7]).sw.max()
ret = ret[ret.apply(lambda r: r.m <= (WEEKS - last_signup[r.cohort]) // 4 - 1, axis=1)]  # fully observed cells only
cohorts = [{"cohort": c, "cells": g.retention.tolist()} for c, g in ret.groupby("cohort")]

aw = act.groupby("user_id").size().rename("active_weeks")
u = users.join(aw, on="user_id").fillna({"active_weeks": 0})
u["revenue"] = u.plan.map(PRICE) * u.active_weeks / 4.33   # revenue to date
ch = u.groupby("channel").agg(users=("user_id", "count"), revenue=("revenue", "mean")).reset_index()
ch["cac"] = ch.channel.map(CAC); ch["ratio"] = (ch.revenue / ch.cac).round(2); ch["revenue"] = ch.revenue.round(1)

def tag(snap):
    p = act[act.cw < snap]
    rec = p[p.cw >= snap - 2].groupby("user_id").sessions.mean()
    pri = p[(p.cw < snap - 2) & (p.cw >= snap - 6)].groupby("user_id").sessions.mean()
    d = pd.DataFrame({"recent": rec, "prior": pri}).dropna(subset=["prior"]).fillna(0)
    d = d[d.prior >= 2]; d["at_risk"] = d.recent < .5 * d.prior
    return d

# Back-test: tag as of 4 weeks ago, then check who really stopped coming back
bt = tag(WEEKS - 4); gone = ~bt.index.isin(act[act.cw >= WEEKS - 4].user_id.unique())
bt["gone"] = gone
risk_rate, base_rate = bt[bt.at_risk].gone.mean() * 100, bt[~bt.at_risk].gone.mean() * 100

now = tag(WEEKS); risky = now[now.at_risk]
lastw = act[act.cw >= WEEKS - 2].groupby("user_id").agg(s=("sessions", "mean"), f=("features", "mean"))
power = lastw[(lastw.s >= lastw.s.quantile(.9)) & (lastw.f >= 4)]
t = pd.concat([power.rename(columns={"s": "recent"}).assign(prior=0, tag="power")[["recent", "prior", "tag"]],
               risky.assign(tag="at_risk")[["recent", "prior", "tag"]]]).reset_index().merge(users[["user_id", "channel", "plan"]])
t.to_csv("data/tagged.csv", index=False)

out = {"users": len(users), "cohorts": cohorts, "channels": ch.to_dict("records"), "power": len(power), "at_risk": len(risky),
       "backtest": {"n": int(len(bt)), "flagged": int(bt.at_risk.sum()), "risk_rate": round(risk_rate, 1), "base_rate": round(base_rate, 1)}}
open("data.js", "w").write("const DATA = " + json.dumps(out) + ";")
print(json.dumps({k: v for k, v in out.items() if k != "cohorts"}, indent=1))
print("M0->M3 retention, Jan cohort:", cohorts[0]["cells"])
