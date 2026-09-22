import requests, pathlib, os, json
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

KEY = os.getenv("API_FOOTBALL_KEY")
HEADERS = {"x-apisports-key": KEY} if KEY else {}

def try_api_football():
    for season in [2024, 2023, 2025, 2022]:
        url = f"https://v3.football.api-sports.io/standings?league=141&season={season}"
        print(f"Probando API-FOOTBALL {season}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            j = r.json()
            print(f" Status {r.status_code} results={j.get('results')} len_resp={len(j.get('response',[]))} errors={j.get('errors')}")
            if j.get('response'):
                t = j['response'][0]['league']['standings'][0]
                if len(t) >= 20:
                    # normalizar
                    norm = []
                    for x in t:
                        norm.append({
                            'rank': x['rank'], 'teamName': x['team']['name'],
                            'teamIconUrl': x['team']['logo'], 'points': x['points'],
                            'won': x['all']['win'], 'draw': x['all']['draw'], 'lost': x['all']['lose'],
                            'goals': x['all']['goals']['for'], 'opp': x['all']['goals']['against'],
                            'diff': x['goalsDiff']
                        })
                    return norm, f"API-FOOTBALL {season}"
        except Exception as e:
            print(f" Fallo: {e}")
    return None

def try_openliga():
    for url in [
        "https://api.openligadb.de/getbltable/laliga2/2024",
        "https://api.openligadb.de/getbltable/laliga2/2023"
    ]:
        print(f"Probando {url}")
        try:
            r = requests.get(url, timeout=15)
            j = r.json()
            if j and len(j) >= 20:
                norm = []
                for x in j:
                    norm.append({
                        'rank': x['rank'], 'teamName': x['teamName'],
                        'teamIconUrl': x.get('teamIconUrl'), 'points': x['points'],
                        'won': x['won'], 'draw': x['draw'], 'lost': x['lost'],
                        'goals': x['goals'], 'opp': x['opponentGoals'],
                        'diff': x['goals']-x['opponentGoals']
                    })
                return norm, "OpenLigaDB"
        except Exception as e:
            print(f" Fallo OpenLiga: {e}")
    return None

table_data = try_api_football()
if not table_data:
    print("API-FOOTBALL vacio -> usando OpenLigaDB")
    table_data = try_openliga()

if not table_data:
    raise SystemExit("Las 2 APIs vacias, prueba en 5 min")

table, origen = table_data
print(f"OK con {origen}: {len(table)} equipos")

# Logos
pathlib.Path("informes").mkdir(exist_ok=True)
pathlib.Path("/tmp/logos2").mkdir(parents=True, exist_ok=True)
for t in table:
    try:
        p = f"/tmp/logos2/{t['teamName']}.png"
        if t['teamIconUrl'] and not pathlib.Path(p).exists():
            open(p,'wb').write(requests.get(t['teamIconUrl'], timeout=10).content)
        t['_logo'] = p if pathlib.Path(p).exists() else None
    except:
        t['_logo'] = None

# PDF CENTRADO - tus columnas
pdf = fpdf.FPDF('L','mm','A4')
pdf.add_page()
pdf.set_font("Arial","B",14)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0,10,f"Clasificacion LaLiga2 ({origen}) - {now.strftime('%d/%m/%Y')}", ln=True, align="C")
pdf.ln(4)

cols = [("POS",10),("LOGO",12),("EQUIPO",60),("PJ",10),("PTS",10),("G",10),("E",10),("P",10),("GF",10),("GC",10),("DG",12)]
total_w = sum(w for _,w in cols)
x0 = (pdf.w - total_w)/2

pdf.set_font("Arial","B",9)
pdf.set_x(x0)
for n,w in cols: pdf.cell(w,7,n,1,0,'C')
pdf.ln()

pdf.set_font("Arial","",9)
for t in sorted(table, key=lambda x: x['points'], reverse=True):
    pdf.set_x(x0)
    pdf.cell(10,7,str(t['rank']),1,0,'C')
    x,y = pdf.get_x(), pdf.get_y()
    pdf.cell(12,7,"",1,0,'C')
    if t['_logo']:
        try: pdf.image(t['_logo'], x+1, y+0.5, w=6, h=6)
        except: pass
    pdf.cell(60,7,t['teamName'][:28],1,0,'L')
    pj = t['won']+t['draw']+t['lost']
    pdf.cell(10,7,str(pj),1,0,'C')
    pdf.cell(10,7,str(t['points']),1,0,'C')
    pdf.cell(10,7,str(t['won']),1,0,'C')
    pdf.cell(10,7,str(t['draw']),1,0,'C')
    pdf.cell(10,7,str(t['lost']),1,0,'C')
    pdf.cell(10,7,str(t['goals']),1,0,'C')
    pdf.cell(10,7,str(t['opp']),1,0,'C')
    pdf.cell(12,7,str(t['diff']),1,0,'C')
    pdf.ln()

out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF CREADO: {out}")
