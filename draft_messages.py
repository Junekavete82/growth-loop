"""Drafts outreach for tagged accounts. Template mode works offline; set GROQ_API_KEY to let an LLM write instead.
Every number in an LLM draft is checked against the real facts. Drafts are only written to a file for a person to approve."""
import os, re
import pandas as pd

t = pd.read_csv("data/tagged.csv")
TEMPLATE = {"power": "Hi! Account {id} has been using the product about {now} times a week. Would you share a short case study on how your team uses it?",
            "at_risk": "Account {id}: weekly sessions fell from {before} to {now}. Suggested step: a 15-minute check-in call this week."}

def llm(prompt):
    import requests
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", timeout=30,
                      headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
                      json={"model": "llama-3.1-8b-instant", "temperature": .3, "messages": [{"role": "user", "content": prompt}]})
    return r.json()["choices"][0]["message"]["content"]

lines, mode = ["# Drafts: PENDING HUMAN APPROVAL (nothing has been sent)\n"], "template" if "GROQ_API_KEY" not in os.environ else "llm"
for tag in ("power", "at_risk"):
    for r in t[t.tag == tag].head(3).itertuples():
        f = {"id": r.user_id, "now": round(r.recent, 1), "before": round(r.prior, 1)}
        text = TEMPLATE[tag].format(**f)
        if mode == "llm":
            cand = llm(f"Write a friendly 2-sentence message for a SaaS customer-success team. Use ONLY these facts: {f}. Tag: {tag}.")
            ok = {str(v) for v in f.values()}
            text = cand if all(n in ok for n in re.findall(r"\d+\.?\d*", cand)) else text  # reject invented numbers
        lines.append(f"- [{tag}] {text}")
open("drafts.md", "w").write("\n".join(lines) + "\n")
print(f"Wrote drafts.md using {mode} mode")
