import requests, pathlib, os, json
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

KEY = os.getenv("API_FOOTBALL_KEY")
if not KEY:
    raise SystemExit("Falta secret API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": KEY}
table = []

for season in [2024, 2023, 2025]:
    URL = f"https://v3.football.api-sports.io/standings?league=141&season={season}"
    print(f"Probando {season}")
    r = requests.get(URL, headers=HEADERS, timeout=20)
    data = r.json()
    if data.get('response'):
        table = data['response'][0]['league']['standings'][0]
        print(f"OK {season}: {len(table)} equipos")
        break

if not table:
    raise SystemExit("Sin datos de Segunda")

# carpetas
pathlib.Path("informes").mkdir(exist_ok=True)
pathlib.Path("/tmp/logos2").mkdir(parents=True, exist_ok=True)

# descargar logos
for t in table:
    tid = t['team']['id']
    logo_url = t['team']['logo']
    path = f"/tmp/logos2/{tid}.png"
    if not pathlib.Path(path).exists():
        try:
            img = requests.get(logo_url, timeout=10).content
            open(path, 'wb').write(img)
        except: pass
    t['_logo_path'] = path if pathlib.Path(path).exists() else None

# PDF centrado
pdf = fpdf.FPDF(orientation='L', format='A4')
pdf.add_page()
pdf.set_font("Arial","B",18)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0,12,f"Clasificacion LaLiga Hypermotion 2Division - {now.strftime('%d/%m/%Y')}",ln=True,align="C")
pdf.ln(8)

# Anchos columnas
cols = [
    ("POS",12), ("LOGO",12), ("EQUIPO",65), ("PJ",12), ("PTS",12),
    ("G",12), ("E",12), ("P",12), ("GF",12), ("GC",12), ("DG",14)
]
total_w = sum(w for _,w in cols)
x_start = (pdf.w - total_w) / 2 # centrar

# cabecera
pdf.set_font("Arial","B",10)
pdf.set_x(x_start)
for name,w in cols:
    pdf.cell(w,9,name,1,0,'C')
pdf.ln()

# filas
pdf.set_font("Arial","",10)
for t in table:
    pdf.set_x(x_start)
    # POS
    pdf.cell(cols[0][1],9,str(t['rank']),1,0,'C')
    # LOGO
    x = pdf.get_x(); y = pdf.get_y()
    pdf.cell(cols[1][1],9,"",1,0,'C')
    if t['_logo_path']:
        try: pdf.image(t['_logo_path'], x+1, y+1, w=7, h=7)
        except: pass
    # resto
    pdf.cell(cols[2][1],9,t['team']['name'][:30],1,0,'L')
    pdf.cell(cols[3][1],9,str(t['all']['played']),1,0,'C')
    pdf.cell(cols[4][1],9,str(t['points']),1,0,'C')
    pdf.cell(cols[5][1],9,str(t['all']['win']),1,0,'C')
    pdf.cell(cols[6][1],9,str(t['all']['draw']),1,0,'C')
    pdf.cell(cols[7][1],9,str(t['all']['lose']),1,0,'C')
    pdf.cell(cols[8][1],9,str(t['all']['goals']['for']),1,0,'C')
    pdf.cell(cols[9][1],9,str(t['all']['goals']['against']),1,0,'C')
    dg = t['goalsDiff']
    pdf.cell(cols[10][1],9,str(dg),1,0,'C')
    pdf.ln()

out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF OK CENTRADO: {out} con {len(table)} equipos")
