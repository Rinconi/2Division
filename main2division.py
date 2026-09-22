import requests, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf

def get_es2():
    for season in [2024, 2023]:
        url = f"https://api.openligadb.de/getbltable/es2/{season}"
        print(f"Probando {url}")
        try:
            r = requests.get(url, timeout=15)
            print(f"Status {r.status_code} len={len(r.text)}")
            j = r.json()
            if j and len(j) >= 18:
                return j
        except Exception as e:
            print(f"Fallo: {e}")
    return None

table = get_es2()

# Si todo falla, usamos tu tabla buena de la foto para no dejarte sin PDF
if not table:
    print("APIs caidas, usando datos backup Levante 2024/25")
    table = [
        {"rank":1,"teamName":"Levante","points":79,"won":22,"draw":13,"lost":7,"goals":69,"opponentGoals":42,"teamIconUrl":None},
        {"rank":2,"teamName":"Elche","points":77,"won":22,"draw":11,"lost":9,"goals":59,"opponentGoals":34,"teamIconUrl":None},
        {"rank":3,"teamName":"Real Oviedo","points":75,"won":21,"draw":12,"lost":9,"goals":56,"opponentGoals":42,"teamIconUrl":None},
        {"rank":4,"teamName":"Mirandes","points":75,"won":22,"draw":9,"lost":11,"goals":59,"opponentGoals":40,"teamIconUrl":None},
        {"rank":5,"teamName":"Racing Santander","points":71,"won":20,"draw":11,"lost":11,"goals":65,"opponentGoals":51,"teamIconUrl":None},
        {"rank":6,"teamName":"Almeria","points":69,"won":19,"draw":12,"lost":11,"goals":72,"opponentGoals":55,"teamIconUrl":None},
        {"rank":7,"teamName":"Granada","points":65,"won":18,"draw":11,"lost":13,"goals":65,"opponentGoals":54,"teamIconUrl":None},
        {"rank":8,"teamName":"Huesca","points":64,"won":18,"draw":10,"lost":14,"goals":58,"opponentGoals":49,"teamIconUrl":None},
        {"rank":9,"teamName":"Eibar","points":58,"won":15,"draw":13,"lost":14,"goals":44,"opponentGoals":41,"teamIconUrl":None},
        {"rank":10,"teamName":"Albacete","points":58,"won":15,"draw":13,"lost":14,"goals":57,"opponentGoals":57,"teamIconUrl":None},
        {"rank":11,"teamName":"Sporting Gijon","points":56,"won":14,"draw":14,"lost":14,"goals":57,"opponentGoals":54,"teamIconUrl":None},
        {"rank":12,"teamName":"Burgos","points":54,"won":15,"draw":9,"lost":18,"goals":41,"opponentGoals":48,"teamIconUrl":None},
        {"rank":13,"teamName":"Cadiz","points":53,"won":13,"draw":14,"lost":15,"goals":55,"opponentGoals":53,"teamIconUrl":None},
        {"rank":14,"teamName":"Cordoba","points":53,"won":14,"draw":11,"lost":17,"goals":59,"opponentGoals":63,"teamIconUrl":None},
        {"rank":15,"teamName":"Deportivo","points":53,"won":13,"draw":14,"lost":15,"goals":56,"opponentGoals":54,"teamIconUrl":None},
        {"rank":16,"teamName":"Malaga","points":53,"won":12,"draw":17,"lost":13,"goals":42,"opponentGoals":46,"teamIconUrl":None},
        {"rank":17,"teamName":"Castellon","points":49,"won":14,"draw":7,"lost":21,"goals":65,"opponentGoals":63,"teamIconUrl":None},
        {"rank":18,"teamName":"Real Zaragoza","points":49,"won":12,"draw":13,"lost":17,"goals":56,"opponentGoals":63,"teamIconUrl":None},
        {"rank":19,"teamName":"Eldense","points":45,"won":11,"draw":12,"lost":19,"goals":40,"opponentGoals":57,"teamIconUrl":None},
        {"rank":20,"teamName":"Racing Ferrol","points":30,"won":6,"draw":12,"lost":24,"goals":22,"opponentGoals":64,"teamIconUrl":None},
        {"rank":21,"teamName":"Tenerife","points":30,"won":8,"draw":6,"lost":28,"goals":35,"opponentGoals":64,"teamIconUrl":None},
        {"rank":22,"teamName":"Cartagena","points":23,"won":6,"draw":5,"lost":31,"goals":33,"opponentGoals":78,"teamIconUrl":None},
    ]

print(f"Tabla lista: {len(table)} equipos")

pathlib.Path("informes").mkdir(exist_ok=True)
pathlib.Path("/tmp/logos2").mkdir(parents=True, exist_ok=True)
for t in table:
    url = t.get('teamIconUrl')
    if not url: 
        t['_logo']=None; continue
    p = f"/tmp/logos2/{t['teamName']}.png"
    try:
        if not pathlib.Path(p).exists():
            open(p,'wb').write(requests.get(url,timeout=8).content)
        t['_logo']=p
    except:
        t['_logo']=None

pdf = fpdf.FPDF('L','mm','A4')
pdf.add_page()
pdf.set_font("Arial","B",14)
now = datetime.now(ZoneInfo("Europe/Madrid"))
pdf.cell(0,10,f"Clasificacion LaLiga2 - {now.strftime('%d/%m/%Y')} - {len(table)} equipos", ln=True, align="C")
pdf.ln(4)

cols = [("POS",10),("LOGO",12),("EQUIPO",60),("PJ",10),("PTS",10),("G",10),("E",10),("P",10),("GF",10),("GC",10),("DG",12)]
total = sum(w for _,w in cols)
x0 = (pdf.w-total)/2

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
    pdf.cell(10,7,str(t['opponentGoals']),1,0,'C')
    pdf.cell(12,7,str(t['goals']-t['opponentGoals']),1,0,'C')
    pdf.ln()

out = f"informes/Informe_LaLiga2_{now.strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF OK: {out}")
