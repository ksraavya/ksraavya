#!/usr/bin/env python3
import os, json, urllib.request
from datetime import datetime, timezone, timedelta

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
OUTPUT = "dist/activity-graph.svg"

def fetch_contributions(username, token):
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=30)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    variables = {"login": username, "from": from_date.strftime("%Y-%m-%dT00:00:00Z"), "to": to_date.strftime("%Y-%m-%dT23:59:59Z")}
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=payload,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "activity-graph-generator"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    days = []
    for week in data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            days.append(day)
    return sorted(days, key=lambda d: d["date"])[-31:]

days = fetch_contributions(USERNAME, TOKEN)
counts = [d["contributionCount"] for d in days]
dates  = [d["date"] for d in days]
max_c  = max(counts) if max(counts) > 0 else 1
n      = len(days)
W, H = 800, 200
PAD_L, PAD_R, PAD_T, PAD_B = 40, 24, 50, 40
GRAPH_W = W - PAD_L - PAD_R
GRAPH_H = H - PAD_T - PAD_B

def x(i): return PAD_L + i * GRAPH_W / (n - 1)
def y(c): return PAD_T + GRAPH_H - (c / max_c) * GRAPH_H

BG="#0d1117"; GRID="#1f2937"; LINE_CLR="#6E40C9"
POINT_CLR="#ffffff"; TEXT_CLR="#a0aec0"; TITLE_CLR="#e2e8f0"

lines = []
def w(s): lines.append(s)
w(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
w(f'  <rect width="{W}" height="{H}" rx="8" fill="{BG}"/>')
w(f'  <text x="{W//2}" y="22" text-anchor="middle" font-family="monospace" font-size="13" font-weight="600" fill="{TITLE_CLR}">Sraavya\'s Contribution Graph</text>')
for i in range(1, 5):
    gy = PAD_T + i * GRAPH_H / 4
    w(f'  <line x1="{PAD_L}" y1="{gy:.1f}" x2="{W-PAD_R}" y2="{gy:.1f}" stroke="{GRID}" stroke-width="1"/>')
label_indices = list(range(0, n, 7))
if (n-1) not in label_indices: label_indices.append(n-1)
for i in label_indices:
    w(f'  <text x="{x(i):.1f}" y="{H-PAD_B+16}" text-anchor="middle" font-family="monospace" font-size="10" fill="{TEXT_CLR}">{dates[i][5:]}</text>')
pts = [(x(i), y(counts[i])) for i in range(n)]
area_pts = [(PAD_L, PAD_T+GRAPH_H)] + pts + [(x(n-1), PAD_T+GRAPH_H)]
w(f'  <polygon points="{" ".join(f"{px:.1f},{py:.1f}" for px,py in area_pts)}" fill="{LINE_CLR}" fill-opacity="0.15"/>')
path = "M " + " L ".join(f"{x(i):.1f},{y(counts[i]):.1f}" for i in range(n))
w(f'  <path d="{path}" fill="none" stroke="{LINE_CLR}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
for i in range(n):
    px, py, c = x(i), y(counts[i]), counts[i]
    w(f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{POINT_CLR}" stroke="{LINE_CLR}" stroke-width="1.5"><title>{dates[i]}: {c} contribution{"s" if c != 1 else ""}</title></circle>')
w(f'  <line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{PAD_T+GRAPH_H}" stroke="{GRID}" stroke-width="1"/>')
w(f'  <line x1="{PAD_L}" y1="{PAD_T+GRAPH_H}" x2="{W-PAD_R}" y2="{PAD_T+GRAPH_H}" stroke="{GRID}" stroke-width="1"/>')
w('</svg>')

os.makedirs("dist", exist_ok=True)
with open(OUTPUT, "w") as f: f.write("\n".join(lines))
print(f"Done: {n} days, max {max_c}")
