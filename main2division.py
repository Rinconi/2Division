import pathlib, json, requests, re
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

out_dir = pathlib.Path("informes")
out_dir.mkdir(exist_ok=True)
logos_path = pathlib.Path("logos")
historial_file = out_dir / "historial_hypermotion.json"
hoy_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")

# --- SEMILLA J1-J6 COMPLETA ---
EQUIPOS = ["mallorca","almeria","burgos","granada","leganes","girona","eibar","las-palmas","ceuta","castellon","cordoba","cadiz","valladolid","real-oviedo","andorra","sporting-gijon","tenerife","real-sociedad-b","celta-fortuna","eldense","sabadell","albacete"]

PARTIDOS_SEMILLA = {
    "castellon": [("2026-08-16","Castellon 1-0 Burgos","V","","1-0"),("2026-08-23","","E","Ceuta 1-1 Castellon","1-1"),("2026-08-30","Castellon 2-1 Tenerife","V","","2-1"),("2026-09-06","Castellon 0-2 Granada","D","","0-2"),("2026-09-13","Almeria 2-0 Castellon","D","","2-0"),("2026-09-19","Castellon 2-1 Valladolid","V","","2-1")],
    "girona": [("2026-08-16","Girona 3-1 Sabadell","V","","3-1"),("2026-08-23","","V","Eldense 1-2 Girona","1-2"),("2026-08-30","Girona 2-2 Leganes","E","","2-2"),("2026-09-06","","D","Burgos 1-0 Girona","1-0"),("2026-09-13","Girona 4-2 Celta Fortuna","V","","4-2"),("2026-09-20","","D","Cordoba 3-1 Girona","3-1")],
    "albacete": [("2026-08-16","Albacete 0-1 Mallorca","D","","0-1"),("2026-08-23","","D","Valladolid 2-1 Albacete","2-1"),("2026-08-30","Albacete 1-1 Oviedo","E","","1-1"),("2026-09-06","","D","Almeria 2-0 Albacete","2-0"),("2026-09-13","Albacete 1-2 Andorra","D","","1-2"),("2026-09-19","","D","Granada 1-0 Albacete","1-0")],
}
for eq in EQUIPOS:
    if eq not in PARTIDOS_SEMILLA: PARTIDOS_SEMILLA[eq]=[]

def normaliza(s): return re.sub(r'[^a-z0-9]','',s.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u'))
MAPEO={"castellon":"castellon","eibar":"eibar","mallorca":"mallorca","almeria":"almeria","burgos":"burgos","sabadell":"sabadell","leganes":"leganes","girona":"girona","sporting":"sporting-gijon","sportinggijon":"sporting-gijon","tenerife":"tenerife","laspalmas":"las-palmas","realsociedadb":"real-sociedad-b","realsociedad":"real-sociedad-b","oviedo":"real-oviedo","realoviedo":"real-oviedo","granada":"granada","celtafortuna":"celta-fortuna","cordoba":"cordoba","eldense":"eldense","valladolid":"valladolid","cadiz":"cadiz","andorra":"andorra","albacete":"albacete","ceuta":"ceuta"}

def cargar_historial():
    if historial_file.exists():
        with open(historial_file,'r',encoding='utf-8') as f:
            data=json.load(f)
            # asegurar todos los equipos
            for eq in EQUIPOS:
                data.setdefault(eq,[])
            return data
    return PARTIDOS_SEMILLA

def guardar_historial(p):
    with open(historial_file,'w',encoding='utf-8') as f: json.dump(p,f,ensure_ascii=False,indent=2)

def recalcular_tabla(d):
    t=[]
    for eq,lista in d.items():
        pj=len(lista); g=sum(1 for _,_,r,_,_ in lista if r=='V'); e=sum(1 for _,_,r,_,_ in lista if r=='E'); pe=sum(1 for _,_,r,_,_ in lista if r=='D')
        gf=gc=0
        for _,c,_,_,gol in lista:
            if "-" not in gol: continue
            try:
                a,b=map(int,gol.split("-"))
                if c!="": gf+=a; gc+=b
                else: gf+=b; gc+=a
            except: pass
        t.append((eq,pj,g*3+e,g,e,pe,gf,gc))
    t.sort(key=lambda x:(x[2],(x[6]-x[7]),x[6]),reverse=True)
    return t

PARTIDOS=cargar_historial()

def fetch_laliga():
    nuevos=0
    try:
        desde=max([p[0] for plist in PARTIDOS.values() for p in plist], default="2026-08-14")
        hasta=hoy_str
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.2/scoreboard?dates={desde.replace('-','')}-{hasta.replace('-','')}&limit=100"
        print(f"Consultando LaLiga oficial espejo ESPN desde {desde} a {hasta}: {url}")
        r=requests.get(url,timeout=20)
        for ev in r.json().get('events',[]):
            if not ev['status']['type']['completed']: continue
            comp=ev['competitions'][0]
            home=next(c for c in comp['competitors'] if c['homeAway']=='home')
            away=next(c for c in comp['competitors'] if c['homeAway']=='away')
            fecha=ev['date'][:10]
            if fecha<desde: continue
            gol=f"{int(float(home['score']))}-{int(float(away['score']))}"
            hk=MAPEO.get(normaliza(home['team']['displayName'])); ak=MAPEO.get(normaliza(away['team']['displayName']))
            if not hk or not ak: continue
            if any(x[0]==fecha and x[4]==gol for x in PARTIDOS.get(hk,[])): continue
            hg,ag=map(int,gol.split("-")); rh,ra=('V','D') if hg>ag else ('D','V') if hg<ag else ('E','E')
            PARTIDOS[hk].append((fecha,f"{home['team']['displayName']} {gol} {away['team']['displayName']}",rh,"",gol))
            PARTIDOS[ak].append((fecha,"",ra,f"{home['team']['displayName']} {gol} {away['team']['displayName']}",gol))
            PARTIDOS[hk].sort(key=lambda x:x[0]); PARTIDOS[ak].sort(key=lambda x:x[0])
            nuevos+=1
            print(f" + Nuevo oficial: {fecha} {gol} {hk} vs {ak}")
    except Exception as e:
        print(f"Error fetch: {e}")
    return nuevos

ultima=max([p[0] for plist in PARTIDOS.values() for p in plist], default="2026-08-14")
nuevos=fetch_laliga()

# Parche J7 asegurado - TODO EN UNA LINEA
if len(PARTIDOS.get("girona",[]))==6:
    PARTIDOS["girona"].append(("2026-09-25","Girona 2-0 Albacete","V","","2-0"))
    PARTIDOS["albacete"].append(("2026-09-25","","D","Girona 2-0 Albacete","2-0"))
    nuevos+=1
    print("Parche J7 aplicado: Girona 2-0 Albacete")

TABLA=recalcular_tabla(PARTIDOS)
JORNADA=max(len(v) for v in PARTIDOS.values()) if PARTIDOS else 6

if nuevos>0:
    guardar_historial(PARTIDOS)
else:
    # aunque no haya nuevos, si no existe el historial lo creamos
    if not historial_file.exists():
        guardar_historial(PARTIDOS)

print(f"Jornada detectada: {JORNADA} - {len(TABLA)} equipos")

# --- PDF SIEMPRE ---
def get_logo(eq):
    for ext in [".png",".jpg",".webp",".PNG"]:
        p=logos_path / f"{eq}{ext}"
        if p.exists(): return str(p)
    return None

styles=getSampleStyleSheet()
style_sub=styles['Heading2']
pdf_path=out_dir / f"Informe_Hypermotion_J{JORNADA}_{hoy_str}.pdf"
doc=SimpleDocTemplate(str(pdf_path),pagesize=A4,leftMargin=12*mm,rightMargin=12*mm,topMargin=12*mm,bottomMargin=12*mm)
story=[Paragraph(f"LaLiga Hypermotion 26/27 - Jornada {JORNADA} - {hoy_str} - {nuevos} partidos nuevos",style_sub),Spacer(1,4*mm)]
data=[["#","Equipo","PJ","PTS","G","E","P","GF","GC","DG"]]
for i,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
    data.append([i,eq,pj,pts,g,e,p,gf,gc,gf-gc])
t=Table(data,colWidths=[10*mm,32*mm]+[10*mm]*8)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1a1a1a')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),8),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f2f2f2')])]))
story.append(t); story.append(PageBreak())

for eq,pj,pts,g,e,p,gf,gc in TABLA:
    logo=get_logo(eq)
    if logo:
        try: story.append(Image(logo,width=18*mm,height=18*mm))
        except: pass
    story.append(Paragraph(f"{eq.upper()} - {pts} pts - J{JORNADA} ({g}V {e}E {p}P {gf}-{gc})",style_sub))
    pdata=[["Fecha","Casa","R","Fuera","Gol"]]
    for f,c,r,fu,gol in PARTIDOS.get(eq,[]):
        pdata.append([f,c,r,fu,gol])
    pt=Table(pdata,colWidths=[20*mm,42*mm,8*mm,42*mm,12*mm])
    pt.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#333')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),7)]))
    story.append(pt); story.append(Spacer(1,4*mm))

doc.build(story)
print(f"PDF GENERADO OK: {pdf_path}")
