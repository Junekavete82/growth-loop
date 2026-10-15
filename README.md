# Growth Loop: Product-Led Growth Analytics

**Data: Simulated data.** There are no real customers here. `generate_data.py` creates 3,000 made-up SaaS users over 26 weeks (seeded, so every run gives the same data). Prices, acquisition costs and churn behaviour are my own assumptions, listed below.

**Live dashboard:** https://junekavete82.github.io/growth-loop/ (enable GitHub Pages for this repo)

## Executive summary (for a non-technical CEO)
A SaaS company wants to know who sticks, which marketing channels pay back, and which accounts need a human this week. This project answers all three from usage data, then drafts the follow-up messages for a person to approve.

- **Retention:** In the January signup cohort, 97% of users were active in the first 4 weeks, 61% in month 2, and 35% in month 4. Most of the loss happens early.
- **Channels:** Referral pays back fastest (revenue to date is 4.0x its acquisition cost). Search is 1.6x and social 1.2x. Outbound is 0.76x, so it has not yet earned back what it cost.
- **At-Risk accounts:** The rule flags accounts whose weekly usage fell by more than half. Tagged as of 4 weeks ago, 61.9% of flagged accounts stopped coming back, against 10.6% of other engaged accounts. That is about 5.8x higher.
- **Today's lists:** 111 Power Users (candidates for a case-study request) and 435 At-Risk accounts (for a customer success call).

## How it works
1. `generate_data.py` simulates users and weekly activity. Low engagement raises the chance of churning.
2. `sql/retention.sql` computes cohort retention in SQL (a CTE for cohort sizes, a join to activity, and a count of distinct active users).
3. `analysis.py` adds revenue to date vs CAC by channel, tags Power Users and At-Risk accounts, and back-tests the At-Risk rule. It writes `data.js` for the dashboard.
4. `draft_messages.py` writes outreach drafts to `drafts.md`. Offline it uses templates. If `GROQ_API_KEY` is set, a Groq LLM writes the text, and any number not in the real facts causes the draft to be rejected. Nothing is ever sent automatically.

Run it: `pip install -r requirements.txt`, then `python generate_data.py`, `python analysis.py`, `python draft_messages.py`. Open `index.html` to see the dashboard.

## Definitions and assumptions
- Active in a week means 1 or more sessions. A month is a 4-week block after signup.
- Power User: top 10% of sessions per week over the last 2 weeks, with 4 or more features used.
- At-Risk: averaged 2+ sessions a week in the earlier period, but the last 2 weeks are under half of that.
- Assumed prices: basic $15 a month, pro $40 a month. Assumed CAC: referral $12, search $28, social $35, outbound $55. Revenue to date = price x active weeks / 4.33.

## Limitations (please read)
- The data is simulated and built so that low engagement raises churn. The back-test therefore checks that the pipeline works, not how accurate it would be on real customers.
- Some flagged accounts already had zero recent sessions, so the rule catches drifting accounts more than it predicts early.
- Retention is shown only for fully observed cells. Revenue to date is not lifetime value, because young cohorts are still paying.
- Next step: run it on real product data, and compare the rule against a simple model such as logistic regression.

## Demo script (30 seconds)
1. "This is a simulated SaaS product with 3,000 users." Show the dashboard header.
2. "Each row is a signup month. Most users drop off in the first two months." Point at the heatmap.
3. "Referral pays back four times its cost; outbound hasn't paid back yet." Point at the channel table.
4. "These accounts' usage fell by half. Last month's flags were 6x more likely to stop coming back." Point at the back-test card.
5. Open `drafts.md`: "The system drafts the message, and a person approves it. Nothing sends itself."

## Questions I should be ready to answer
- Why simulated data? Real customer data is private, and I label the data clearly instead of pretending.
- Why is M0 retention below 100%? Some users have no sessions in their first 4 weeks.
- What would you change with real data? Replace the rule with a model, validate it on a holdout, and add confidence intervals.
