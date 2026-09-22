import requests, pathlib, os
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

KEY = os.getenv("API_FOOTBALL_KEY")
URL = "https://v3.football.api-sports.io/standings?league=141&season=2024"
HEADERS = {"x-apisports-key": KEY}

print(f"Pidiendo: {URL}")
r = requests.get(URL, headers=HEADERS, timeout=20)
print(f"Status: {r.status_code}")
data = r.json()
table = data['response'][0]['league']['standings'][0]
print(f"OK {len(table)} equipos - Levante primero")

pathlib.Path("informes").mkdir(exist_ok=True)
pathlib.Path("/tmp/logos2").mkdir(parents=True, exist_ok=True)

for t in table:
    url = t['team']['logo']
    p = f"/tmp/logos2/{t['team']['id']}.png"
    if not pathlib.Path(p).exists():
        try:
            open(p,'wb').write(requests.get(url,timeout=10).content)
        except: pass
    t['_logo'] = p if pathlib.Path(p).exists() else None

# PDF horizontal y centrado
pdf = fpdf.FPDF(orientation='L', format='A4')
pdf.add_page()
pdf.set_font("Arial","B",16)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0,12,f"Clasificacion LaLiga2 - {now.strftime('%d/%m/%Y')}", ln=True, align="C")
pdf.ln(6)

# Tus columnas exactas
cols = [
    ("POS",10), ("LOGO",12), ("EQUIPO",58), ("PJ",10), ("PTS",12),
    ("G",10), ("E",10), ("P",10), ("GF",10), ("GC",10), ("DG",12)
]
total = sum(w for _,w in cols)
x0 = (pdf.w - total)/2 # centrado

pdf.set_font("Arial","B",9)
pdf.set_x(x0)
for name,w in cols:
    pdf.cell(w,8,name,1,0,'C')
pdf.ln()

pdf.set_font("Arial","",9)
for t in table:
    pdf.set_x(x0)
    # POS
    pdf.cell(cols[0][1],8,str(t['rank']),1,0,'C')
    # LOGO
    x,y = pdf.get_x(), pdf.get_y()
    pdf.cell(cols[1][1],8,"",1,0,'C')
    if t['_logo']:
        try: pdf.image(t['_logo'], x+1, y+1, w=6, h=6)
        except: pass
    # EQUIPO
    pdf.cell(cols[2][1],8,t['team']['name'][:28],1,0,'L')
    # PJ PTS G E P GF GC DG
    pdf.cell(cols[3][1],8,str(t['all']['played']),1,0,'C')
    pdf.cell(cols[4][1],8,str(t['points']),1,0,'C')
    pdf.cell(cols[5][1],8,str(t['all']['win']),1,0,'C')
    pdf.cell(cols[6][1],8,str(t['all']['draw']),1,0,'C')
    pdf.cell(cols[7][1],8,str(t['all']['lose']),1,0,'C')
    pdf.cell(cols[8][1],8,str(t['all']['goals']['for']),1,0,'C')
    pdf.cell(cols[9][1],8,str(t['all']['goals']['against']),1,0,'C')
    pdf.cell(cols[10][1],8,str(t['goalsDiff']),1,0,'C')
    pdf.ln()

out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF FINAL OK: {out}")
