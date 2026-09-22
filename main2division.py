import requests, pathlib, os, json
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

KEY = os.getenv("API_FOOTBALL_KEY")
if not KEY:
    raise SystemExit("Falta secret API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": KEY}

table = []
for season in [2025, 2024, 2023]:
    URL = f"https://v3.football.api-sports.io/standings?league=141&season={season}"
    print(f"Probando: {URL}")
    r = requests.get(URL, headers=HEADERS, timeout=20)
    print(f"Status: {r.status_code}")
    if r.status_code!= 200:
        print(r.text[:500])
        continue
    data = r.json()
    print(f"Respuesta keys: {list(data.keys())}, response len: {len(data.get('response',[]))}")
    if not data.get('response'):
        print(f"Vacio para {season}, errors: {data.get('errors')}, results: {data.get('results')}")
        continue
    try:
        table = data['response'][0]['league']['standings'][0]
        print(f"Tabla OK con temporada {season}: {len(table)} equipos")
        break
    except Exception as e:
        print(f"Error parseando {season}: {e}")
        print(json.dumps(data)[:1000])

if not table:
    raise SystemExit("API-FOOTBALL devolvio vacio para 2025,2024,2023. Revisa que tu key este activada y que tengas peticiones restantes.")

# PDF
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
