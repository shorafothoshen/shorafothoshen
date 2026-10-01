"""Builds every card in assets/ (dark UI, same layout as the reference design).
Run:  python build.py        (reads assets/stats.json if it exists)"""
import base64, glob, html, json, math, os, re, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

# ----------------------------------------------------------------- theme
CARD, BORDER = "#0d1320", "#1f2a44"
WHITE, TEXT, MUTED, BLUE = "#f1f5f9", "#94a3b8", "#64748b", "#3b82f6"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"
W = 900
esc = html.escape

# --------------------------------------------------------- your content
ABOUT = ("I'm a 4th year Computer Science & Engineering student at BUBT, focused on full-stack "
         "development and passionate about building real-world applications. I enjoy building web "
         "applications, real-time systems and APIs with Django, React and Next.js, love exploring "
         "mobile apps, and also enjoy IoT projects where I use AI. Currently, I'm focused on improving "
         "my skills, solving problems and building projects that make an impact.")
BOLD_WORDS = ["Django", "React", "Next.js", "BUBT", "IoT"]
ABOUT_CHIPS = ["Full-Stack Developer", "CSE Student", "BUBT"]
LEARNING = ["Django Channels (WebSocket)", "Advanced React & Next.js", "React Native", "DevOps & Cloud",
            "Advanced System Design", "Data Structures & Algorithms", "AI & Machine Learning",
            "IoT projects with AI integration"]

TECH = [  # (column title, cell width, columns per row, [(label, icon key)])
    ("Languages", 54, 3, [("Python", "python"), ("JavaScript", "javascript"), ("TypeScript", "typescript"),
                          ("C", "c"), ("C++", "cplusplus"), ("Java", "java")]),
    ("Frontend", 54, 3, [("HTML", "html5"), ("CSS", "css3"), ("Tailwind CSS", "tailwindcss"),
                         ("React", "react"), ("Next.js", "nextjs"), ("React Native", "react")]),
    ("Backend", 54, 2, [("Django", "django"), ("DRF", "@drf"), ("Node.js", "nodejs"), ("Express", "express")]),
    ("Database", 54, 2, [("MySQL", "mysql"), ("PostgreSQL", "postgresql"), ("MongoDB", "mongodb")]),
    ("Real-time", 68, 1, [("WebSockets", "@ws"), ("Channels", "@channels")]),
    ("Tools", 54, 3, [("Git", "git"), ("GitHub", "github"), ("VS Code", "vscode"),
                      ("Postman", "postman"), ("Docker", "docker"), ("Linux", "linux")]),
]

PROJECTS = [  # slug, title, description, tags, thumb kind, (color1, color2)
    ("crime360", "Crime360", "Crime reporting platform with OTP, NID verification & real-time notifications.",
     ["Django", "React", "Channels"], "ui", ("#7f1d1d", "#1e293b")),
    ("online-school", "Online School", "Full-stack learning platform with role-based access, course & assignment system.",
     ["Django", "React", "MySQL"], "ui", ("#1d4ed8", "#0f172a")),
    ("chat-app", "Real-time Chat App", "WebSocket based chat app with online users and message notifications.",
     ["React", "Django", "WebSocket"], "chat", ("#6d28d9", "#0f172a")),
    ("esp32-navigation", "ESP32 Smart Blind Navigation", "AI-powered object detection with YOLO, Blynk and ESP32-S3.",
     ["ESP32", "YOLO", "IoT"], "chip", ("#065f46", "#0f172a")),
    ("nextjs-portfolio", "Next.js Portfolio", "Modern portfolio website with Next.js, Tailwind and daisyUI.",
     ["Next.js", "Tailwind", "daisyUI"], "ui", ("#0e7490", "#0f172a")),
    ("library", "Library Management", "Book issue/return system with user management and fine calculation.",
     ["Django", "MySQL"], "ui", ("#b45309", "#0f172a")),
]
CHIP = {"Django": "#44b78b", "React": "#61dafb", "Channels": "#44b78b", "MySQL": "#f29111", "WebSocket": "#a78bfa",
        "ESP32": "#f87171", "YOLO": "#facc15", "IoT": "#34d399", "Next.js": "#e2e8f0", "Tailwind": "#38bdf8",
        "daisyUI": "#fbbf24"}

PROBLEM_SOLVING = [("LeetCode", "520+ solved", "#f59e0b"), ("Codeforces", "200+ solved", "#3b82f6"),
                   ("CodeChef", "50+ solved", "#a16207")]

DEFAULT_STATS = dict(commits=2310, repos=40, followers=12, following=12, streak=28, longest=54,
                     recent=[1, 2, 1, 3, 2, 1, 4, 2, 3, 1, 2, 2, 3, 1],
                     languages=[dict(name="Python", pct=40.2), dict(name="JavaScript", pct=24.8),
                                dict(name="TypeScript", pct=14.6), dict(name="Java", pct=6.1),
                                dict(name="C++", pct=4.9), dict(name="Others", pct=10.0)])
LANG_COLORS = ["#3b82f6", "#facc15", "#2dd4bf", "#f87171", "#a78bfa", "#22c55e", "#fb923c", "#e879f9"]

# --------------------------------------------------------------- helpers
def svg(w, h, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">{inner}</svg>')

def save(name, content):
    with open(os.path.join(ASSETS, name + ".svg"), "w", encoding="utf-8") as f:
        f.write(content)

def card(x, y, w, h):
    return (f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="14" fill="{CARD}" '
            f'stroke="{BORDER}" stroke-width="1"/>')

GLYPHS = {
    "user": '<circle cx="8" cy="5" r="3"/><path d="M2 15c0-3.5 2.7-5.5 6-5.5s6 2 6 5.5"/>',
    "rocket": '<path d="M8 1c3 2 4 5 3.5 8L8 12.5 4.5 9C4 6 5 3 8 1z"/><circle cx="8" cy="6" r="1.2"/><path d="M4.5 10 2 12l2.5-.5M11.5 10 14 12l-2.5-.5M8 13v2.5"/>',
    "code": '<path d="M5 4 1.5 8 5 12M11 4l3.5 4L11 12M9.3 2.5 6.7 13.5"/>',
    "folder": '<path d="M1.5 3.5h4.2l1.6 1.8h7.2v8.2H1.5z"/>',
    "chart": '<path d="M2 14V2M2 14h12"/><rect x="4.5" y="8" width="2" height="5"/><rect x="8" y="5" width="2" height="8"/><rect x="11.5" y="9" width="2" height="4"/>',
    "flame": '<path d="M8 1.5c.5 3 3.5 4 3.5 7.5a3.5 3.5 0 0 1-7 0c0-1.5.8-2.4 1.5-3 .2 1 .6 1.5 1.2 1.7C7 6.5 7 4 8 1.5z"/>',
    "globe": '<circle cx="8" cy="8" r="6.5"/><path d="M1.5 8h13M8 1.5c-3 3.5-3 9.5 0 13M8 1.5c3 3.5 3 9.5 0 13"/>',
    "check": '<circle cx="8" cy="8" r="6.5"/><path d="M5 8.2l2.2 2.2L11 6"/>',
}

def head(x, y, glyph, title):
    return (f'<g transform="translate({x},{y-14})" fill="none" stroke="#60a5fa" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{GLYPHS[glyph]}</g>'
            f'<text x="{x+26}" y="{y}" font-family="{FONT}" font-size="17" font-weight="700" fill="{WHITE}">{esc(title)}</text>')

def rich(line):
    out, pat = esc(line), "|".join(re.escape(w) for w in BOLD_WORDS)
    return re.sub(f"({pat})", rf'<tspan font-weight="700" fill="{WHITE}">\1</tspan>', out)

def paragraph(txt, x, y, chars, step=22, size=13.5):
    return "".join(f'<text x="{x}" y="{y+i*step}" font-family="{FONT}" font-size="{size}" fill="{TEXT}">{rich(l)}</text>'
                   for i, l in enumerate(textwrap.wrap(txt, chars)))

def chips(tags, x, y, h=22):
    out = ""
    for t in tags:
        w = int(len(t) * 6.7 + 20)
        c = CHIP.get(t, "#60a5fa")
        out += (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{c}" fill-opacity=".13" '
                f'stroke="{c}" stroke-opacity=".4"/><text x="{x+w/2}" y="{y+h/2+4}" text-anchor="middle" '
                f'font-family="{FONT}" font-size="11" font-weight="600" fill="{c}">{esc(t)}</text>')
        x += w + 8
    return out

def icon_data(key):
    s = open(os.path.join(ROOT, "icons", key + ".svg"), encoding="utf-8").read()
    if key == "nextjs":
        s = s.replace('<circle cx="64" cy="64" r="64"/>',
                      '<circle cx="64" cy="64" r="61" fill="#0b1220" stroke="#94a3b8" stroke-width="4"/>')
    elif key in ("express", "linux"):
        s = s.replace("<svg ", '<svg fill="#e2e8f0" ', 1)
    elif key == "github":
        s = s.replace("#181616", "#e2e8f0")
    elif key == "django":
        s = s.replace("#092e20", "#44b78b")
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode()).decode()

def custom_icon(kind, x, y, s=34):
    if kind == "@drf":
        return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="8" fill="#a30000"/>'
                f'<text x="{x+s/2}" y="{y+s/2+5}" text-anchor="middle" font-family="{FONT}" font-size="13" '
                f'font-weight="800" fill="#fff">DRF</text>')
    if kind == "@ws":
        return (f'<g transform="translate({x},{y})"><rect width="{s}" height="{s}" rx="8" fill="#0c4a6e"/>'
                f'<g stroke="#22d3ee" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M8 12h18M22 8l4 4-4 4M26 23H8M12 19l-4 4 4 4"/></g></g>')
    if kind == "@channels":
        return (f'<g transform="translate({x},{y})"><rect width="{s}" height="{s}" rx="8" fill="#0c4b33"/>'
                f'<g fill="#44b78b"><rect x="8" y="8" width="18" height="4.5" rx="2.2"/>'
                f'<rect x="8" y="15" width="12" height="4.5" rx="2.2"/><rect x="8" y="22" width="18" height="4.5" rx="2.2"/></g></g>')

def item(label, key, cx, y, cell):
    s = 34
    ix = cx + (cell - s) / 2
    g = (custom_icon(key, ix, y, s) if key.startswith("@") else
         f'<image x="{ix}" y="{y}" width="{s}" height="{s}" xlink:href="{icon_data(key)}"/>')
    words = label.split(" ") if len(label) > 10 else [label]
    for i, wd in enumerate(words):
        g += (f'<text x="{cx+cell/2}" y="{y+s+14+i*11}" text-anchor="middle" font-family="{FONT}" '
              f'font-size="9.5" fill="{TEXT}">{esc(wd)}</text>')
    return g

# ------------------------------------------------------ 1. about + learning
def build_header():
    H, aw = 276, 548
    out = card(0, 0, aw, H) + head(24, 40, "user", "About Me")
    out += paragraph(ABOUT, 24, 74, 66)
    out += chips(ABOUT_CHIPS, 24, H - 44)
    lx, lw = aw + 16, W - aw - 16
    out += card(lx, 0, lw, H) + head(lx + 24, 40, "rocket", "Currently Learning")
    for i, t in enumerate(LEARNING):
        y = 76 + i * 25
        out += (f'<g transform="translate({lx+24},{y-11})" stroke="#60a5fa" stroke-width="1.6" fill="none" stroke-linecap="round">'
                f'<rect x="0" y="3" width="9" height="5" rx="2.5" transform="rotate(-35 4.5 5.5)"/>'
                f'<rect x="5" y="6" width="9" height="5" rx="2.5" transform="rotate(-35 9.5 8.5)"/></g>'
                f'<text x="{lx+48}" y="{y}" font-family="{FONT}" font-size="13.5" fill="#cbd5e1">{esc(t)}</text>')
    save("header", svg(W, H, out))

# ------------------------------------------------------------ 2. tech stack
def build_tech():
    H = 262
    out = card(0, 0, W, H) + head(26, 40, "code", "Tech Stack")
    widths = [c[1] * c[2] for c in TECH]
    gap = (W - 52 - sum(widths)) / (len(TECH) - 1)
    x = 26
    for (title, cell, per, items), cw in zip(TECH, widths):
        out += f'<text x="{x}" y="82" font-family="{FONT}" font-size="12.5" font-weight="700" fill="{WHITE}">{esc(title)}</text>'
        for i, (label, key) in enumerate(items):
            out += item(label, key, x + (i % per) * cell, 98 + (i // per) * 80, cell)
        x += cw + gap
    save("techstack", svg(W, H, out))

# ----------------------------------------------------------------- 3. projects
def build_projects_header():
    out = (head(4, 28, "folder", "Featured Projects") +
           f'<text x="{W-4}" y="28" text-anchor="end" font-family="{FONT}" font-size="13" font-weight="600" fill="{BLUE}">View all projects →</text>')
    save("projects-header", svg(W, 44, out))

def thumb(slug, kind, c1, c2, x, y, w, h):
    clip = f'<clipPath id="c-{slug}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/></clipPath>'
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = os.path.join(ASSETS, "thumbs", f"{slug}.{ext}")
        if os.path.exists(p):
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext
            b = base64.b64encode(open(p, "rb").read()).decode()
            return (clip + f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" '
                    f'clip-path="url(#c-{slug})" xlink:href="data:image/{mime};base64,{b}"/>')
    g = (clip + f'<linearGradient id="t-{slug}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
         f'<stop offset="1" stop-color="{c2}"/></linearGradient>'
         f'<g clip-path="url(#c-{slug})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#t-{slug})"/>'
         f'<rect x="{x+14}" y="{y+12}" width="{w-28}" height="{h-12}" rx="7" fill="#0b1220" fill-opacity=".92"/>'
         f'<circle cx="{x+26}" cy="{y+23}" r="2.5" fill="#f87171"/><circle cx="{x+35}" cy="{y+23}" r="2.5" fill="#facc15"/>'
         f'<circle cx="{x+44}" cy="{y+23}" r="2.5" fill="#4ade80"/>')
    bx, by = x + 26, y + 36
    if kind == "chat":
        for i, (side, ww) in enumerate([("l", 90), ("r", 70), ("l", 60)]):
            xx = bx if side == "l" else x + w - 26 - ww
            g += f'<rect x="{xx}" y="{by+i*17}" width="{ww}" height="12" rx="6" fill="{"#334155" if side=="l" else "#7c3aed"}"/>'
    elif kind == "chip":
        g += (f'<rect x="{x+w/2-26}" y="{by-2}" width="52" height="40" rx="5" fill="#064e3b" stroke="#34d399"/>'
              + "".join(f'<rect x="{x+w/2-22+i*10}" y="{by-8}" width="4" height="6" fill="#34d399"/>'
                        f'<rect x="{x+w/2-22+i*10}" y="{by+38}" width="4" height="6" fill="#34d399"/>' for i in range(5))
              + f'<rect x="{x+w/2-12}" y="{by+8}" width="24" height="20" rx="3" fill="#10b981" fill-opacity=".5"/>')
    else:
        g += (f'<rect x="{bx}" y="{by}" width="38" height="46" rx="4" fill="#1e293b"/>'
              f'<rect x="{bx+46}" y="{by}" width="{w-130}" height="10" rx="3" fill="#334155"/>'
              f'<rect x="{bx+46}" y="{by+16}" width="{(w-130)*.6}" height="8" rx="3" fill="#1e293b"/>'
              f'<rect x="{bx+46}" y="{by+30}" width="{(w-130)*.8}" height="16" rx="4" fill="{c1}" fill-opacity=".8"/>')
    return g + "</g>"

def build_projects():
    PW, PH = 290, 248
    for slug, name, desc, tags, kind, (c1, c2) in PROJECTS:
        out = card(0, 0, PW, PH) + thumb(slug, kind, c1, c2, 12, 12, PW - 24, 108)
        out += f'<text x="16" y="144" font-family="{FONT}" font-size="14.5" font-weight="700" fill="{WHITE}">{esc(name)}</text>'
        for i, l in enumerate(textwrap.wrap(desc, 44)):
            out += f'<text x="16" y="{163+i*15}" font-family="{FONT}" font-size="11" fill="{TEXT}">{esc(l)}</text>'
        out += chips(tags, 16, PH - 36, 20)
        save(slug, svg(PW, PH, out))

# ----------------------------------------------------------------- 4. stats
def load_stats():
    p = os.path.join(ASSETS, "stats.json")
    s = dict(DEFAULT_STATS)
    if os.path.exists(p):
        s.update(json.load(open(p)))
    return s

def build_stats(s):
    # row 1: GitHub stats + streak
    H, w1 = 212, 560
    out = card(0, 0, w1, H) + head(24, 40, "chart", "GitHub Stats")
    boxes = [("Total Commits", f"{s['commits']:,}"), ("Total Repositories", f"{s['repos']:,}"),
             ("Followers", f"{s['followers']:,}"), ("Following", f"{s['following']:,}")]
    bw = (w1 - 48 - 16) / 2
    for i, (lab, val) in enumerate(boxes):
        bx, by = 24 + (i % 2) * (bw + 16), 62 + (i // 2) * 72
        out += (f'<rect x="{bx}" y="{by}" width="{bw}" height="62" rx="10" fill="#111a2e" stroke="{BORDER}"/>'
                f'<text x="{bx+16}" y="{by+24}" font-family="{FONT}" font-size="12" fill="{MUTED}">{lab}</text>'
                f'<text x="{bx+16}" y="{by+50}" font-family="{FONT}" font-size="24" font-weight="800" fill="{WHITE}">{val}</text>')
    sx, sw = w1 + 16, W - w1 - 16
    out += card(sx, 0, sw, H) + head(sx + 22, 40, "flame", "Contribution Streak")
    out += (f'<text x="{sx+22}" y="112" font-family="{FONT}" font-size="54" font-weight="800" fill="{WHITE}">{s["streak"]}</text>'
            f'<text x="{sx+22+len(str(s["streak"]))*31+10}" y="112" font-family="{FONT}" font-size="15" fill="{TEXT}">days</text>')
    shades = ["#1e293b", "#14532d", "#16a34a", "#22c55e", "#4ade80"]
    for i, c in enumerate(s["recent"][-14:]):
        out += f'<rect x="{sx+22+i*17.5}" y="132" width="14" height="14" rx="3" fill="{shades[min(c,4)]}"/>'
    out += f'<text x="{sx+22}" y="178" font-family="{FONT}" font-size="12.5" fill="{TEXT}">Longest streak: {s["longest"]} days</text>'
    save("stats-1", svg(W, H, out))

    # row 2: languages + problem solving
    H, w2 = 236, 440
    langs = s["languages"]
    out = card(0, 0, w2, H) + head(24, 40, "globe", "Top Languages")
    for i, l in enumerate(langs):
        c, y = LANG_COLORS[i % len(LANG_COLORS)], 82 + i * 25
        out += (f'<circle cx="32" cy="{y-4}" r="5" fill="{c}"/>'
                f'<text x="48" y="{y}" font-family="{FONT}" font-size="13" fill="#cbd5e1">{esc(l["name"])}</text>'
                f'<text x="190" y="{y}" text-anchor="end" font-family="{FONT}" font-size="13" font-weight="700" fill="{WHITE}">{l["pct"]:.1f}%</text>')
    cx, cy, r = 322, 128, 52
    C, off = 2 * math.pi * r, 0
    for i, l in enumerate(langs):
        seg = C * l["pct"] / 100
        out += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LANG_COLORS[i % len(LANG_COLORS)]}" stroke-width="18" '
                f'stroke-dasharray="{max(seg-2,0.1):.2f} {C-max(seg-2,0.1):.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        off += seg
    n = len([l for l in langs if l["name"] != "Others"])
    out += (f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-family="{FONT}" font-size="22" font-weight="800" fill="{WHITE}">{n}</text>'
            f'<text x="{cx}" y="{cy+22}" text-anchor="middle" font-family="{FONT}" font-size="10" fill="{TEXT}">languages</text>')

    px = w2 + 16
    out += card(px, 0, W - px, H) + head(px + 24, 40, "check", "Problem Solving")
    for i, (name, val, col) in enumerate(PROBLEM_SOLVING):
        y = 62 + i * 56
        out += (f'<rect x="{px+20}" y="{y}" width="{W-px-40}" height="46" rx="10" fill="#111a2e" stroke="{BORDER}"/>'
                f'<circle cx="{px+46}" cy="{y+23}" r="13" fill="{col}" fill-opacity=".18" stroke="{col}"/>'
                f'<text x="{px+46}" y="{y+28}" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="800" fill="{col}">{name[0]}</text>'
                f'<text x="{px+70}" y="{y+28}" font-family="{FONT}" font-size="14" font-weight="600" fill="#e2e8f0">{name}</text>'
                f'<text x="{W-px-34+px}" y="{y+28}" text-anchor="end" font-family="{FONT}" font-size="14" font-weight="800" fill="{BLUE}">{val}</text>')
    save("stats-2", svg(W, H, out))

if __name__ == "__main__":
    build_header(); build_tech(); build_projects_header(); build_projects(); build_stats(load_stats())
    print("built:", ", ".join(sorted(os.path.basename(p) for p in glob.glob(ASSETS + "/*.svg"))))
