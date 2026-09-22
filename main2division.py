import requests, pathlib, os
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

KEY = os.getenv("API_FOOTBALL_KEY")
if not KEY:
    raise SystemExit("Falta secret API_FOOTBALL_KEY")

URL = "https://v3.football.api-sports.io/standings?league=140&season=2025"
headers = {"x-apisports-key": KEY}
print(f"Pidiendo API-FOOTBALL Segunda: {URL}")
r = requests.get(URL, headers=headers, timeout=20)
print(f"Status: {r.status_code}")
r.raise_for_status()
data = r.json()
table = data['response'][0]['league']['standings'][0]
print(f"Tabla OK: {len(table)} equipos")

pdf = fpdf.FPDF(); pdf.add_page()
pdf.set_font("Arial","B",16)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0,10,f"Clasificacion LaLiga2 - {now.strftime('%d/%m/%Y')}",ln=True,align="C")
pdf.ln(5)
pdf.set_font("Arial","B",10)
pdf.cell(10,8,"#",1); pdf.cell(60,8,"Equipo",1); pdf.cell(15,8,"PJ",1); pdf.cell(15,8,"PTS",1); pdf.ln()
pdf.set_font("Arial","",10)
for t in table:
    pdf.cell(10,8,str(t['rank']),1)
    pdf.cell(60,8,t['team']['name'][:28],1)
    pdf.cell(15,8,str(t['all']['played']),1)
    pdf.cell(15,8,str(t['points']),1)
    pdf.ln()

pathlib.Path("informes").mkdir(exist_ok=True)
out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF OK: {out}")
