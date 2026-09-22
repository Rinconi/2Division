import requests, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

# URL CORRECTA para standings
URL = "https://site.api.espn.com/apis/v2/sports/soccer/esp.2/standings?season=2025"
print(f"Pidiendo ESPN: {URL}")
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(URL, headers=headers, timeout=20)
print(f"Status: {r.status_code}")
r.raise_for_status()
data = r.json()

print(f"Keys: {list(data.keys())}")

# ESPN v2 estructura: standings -> entries o children -> standings
table = []
try:
    # formato más común v2
    if 'standings' in data:
        # standings es lista
        for group in data['standings']:
            if 'standings' in group and 'entries' in group['standings']:
                table = group['standings']['entries']
                break
            if 'entries' in group:
                table = group['entries']
                break
    if not table and 'children' in data:
        table = data['children'][0]['standings']['entries']
except Exception as e:
    print(f"Error parseando: {e}")
    print(str(data)[:2000])

if not table:
    raise SystemExit(f"No se encontró tabla. Dump: {str(data)[:2000]}")

print(f"Tabla OK: {len(table)} equipos")

pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Arial","B",16)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0,10,f"Clasificacion LaLiga2 - {now.strftime('%d/%m/%Y')}",ln=True,align="C")
pdf.ln(5)
pdf.set_font("Arial","B",10)
pdf.cell(10,8,"#",1); pdf.cell(60,8,"Equipo",1); pdf.cell(15,8,"PJ",1); pdf.cell(15,8,"PTS",1); pdf.ln()
pdf.set_font("Arial","",10)
for entry in table:
    team = entry['team']['displayName']
    stats = {s['name']: s['value'] for s in entry['stats']}
    pdf.cell(10,8,str(stats.get('rank','')),1)
    pdf.cell(60,8,team[:28],1)
    pdf.cell(15,8,str(stats.get('gamesPlayed','')),1)
    pdf.cell(15,8,str(stats.get('points','')),1)
    pdf.ln()

pathlib.Path("informes").mkdir(exist_ok=True)
out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF OK: {out}")
