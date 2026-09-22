import requests
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

# ESPN - LaLiga2 es esp.2
URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.2/standings?region=es&lang=es"
print(f"Pidiendo ESPN: {URL}")
r = requests.get(URL, timeout=20)
r.raise_for_status()
data = r.json()

# ESPN tiene la tabla en children[0].standings.entries
table = data['children'][0]['standings']['entries']
print(f"Tabla OK: {len(table)} equipos")

# Crear PDF simple como el de 1ª
pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0, 10, f"Clasificacion LaLiga2 - {now.strftime('%d/%m/%Y')}", ln=True, align="C")
pdf.ln(5)
pdf.set_font("Arial", "B", 10)
pdf.cell(10, 8, "#", 1)
pdf.cell(60, 8, "Equipo", 1)
pdf.cell(15, 8, "PJ", 1)
pdf.cell(15, 8, "PTS", 1)
pdf.ln()

pdf.set_font("Arial", "", 10)
for entry in table:
    team = entry['team']['displayName']
    stats = {s['name']: s['value'] for s in entry['stats']}
    pdf.cell(10, 8, str(stats.get('rank', '')), 1)
    pdf.cell(60, 8, team[:28], 1)
    pdf.cell(15, 8, str(stats.get('gamesPlayed', '')), 1)
    pdf.cell(15, 8, str(stats.get('points', '')), 1)
    pdf.ln()

pathlib.Path("informes").mkdir(exist_ok=True)
out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF generado: {out}")
