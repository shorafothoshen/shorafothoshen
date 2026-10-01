"""Fetches real numbers from GitHub (GraphQL) and writes assets/stats.json.
Needs env GH_TOKEN (and optionally GH_USER). Private contributions are counted
when the token is a PAT with `read:user` + `repo` scopes."""
import datetime as dt, json, os, urllib.request

USER = os.environ.get("GH_USER", "shorafothoshen")
TOKEN = os.environ["GH_TOKEN"]

def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-stats"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]

base = gql("""query($u:String!){ user(login:$u){ createdAt followers{totalCount} following{totalCount}
  repositories(ownerAffiliations:OWNER, first:100){ totalCount nodes{ isFork
    languages(first:8, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } } } }""", {"u": USER})["user"]

now = dt.datetime.now(dt.timezone.utc)
first_year = int(base["createdAt"][:4])
commits, days = 0, {}
for y in range(first_year, now.year + 1):
    frm = f"{y}-01-01T00:00:00Z"
    to = min(now, dt.datetime(y, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    c = gql("""query($u:String!,$f:DateTime!,$t:DateTime!){ user(login:$u){ contributionsCollection(from:$f,to:$t){
      totalCommitContributions restrictedContributionsCount
      contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } } } }""",
            {"u": USER, "f": frm, "t": to})["user"]["contributionsCollection"]
    commits += c["totalCommitContributions"] + c["restrictedContributionsCount"]
    for w in c["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]

dates = sorted(days)
# longest streak
longest = run = 0
prev = None
for d in dates:
    cur = dt.date.fromisoformat(d)
    run = run + 1 if (days[d] > 0 and prev and (cur - prev).days == 1 and days[prev.isoformat()] > 0) else (1 if days[d] > 0 else 0)
    longest, prev = max(longest, run), cur
# current streak (today may still be empty)
today = now.date()
cursor = today if days.get(today.isoformat(), 0) > 0 else today - dt.timedelta(days=1)
streak = 0
while days.get(cursor.isoformat(), 0) > 0:
    streak += 1
    cursor -= dt.timedelta(days=1)
recent = [days.get((today - dt.timedelta(days=i)).isoformat(), 0) for i in range(13, -1, -1)]

# languages across non-fork repos
sizes = {}
for r in base["repositories"]["nodes"]:
    if r["isFork"]:
        continue
    for e in r["languages"]["edges"]:
        sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
total = sum(sizes.values()) or 1
top = sorted(sizes.items(), key=lambda kv: -kv[1])
langs = [{"name": n, "pct": round(v * 100 / total, 1)} for n, v in top[:5]]
langs.append({"name": "Others", "pct": round(100 - sum(l["pct"] for l in langs), 1)})

out = dict(commits=commits, repos=base["repositories"]["totalCount"], followers=base["followers"]["totalCount"],
           following=base["following"]["totalCount"], streak=streak, longest=longest, recent=recent, languages=langs)
os.makedirs("assets", exist_ok=True)
json.dump(out, open("assets/stats.json", "w"), indent=2)
print(out)
