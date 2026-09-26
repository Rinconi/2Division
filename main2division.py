import pathlib, json, requests, re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

# ========= SEED J1-J6 =========
PARTIDOS = {
    "castellon": [("2026-08-14","","V","Real Sociedad B 0-1 Castellón","0-1"),("2026-08-23","Castellón 0-0 Sabadell","E","","0-0"),("2026-08-31","", "V","Celta Fortuna 1-2 Castellón","1-2"),("2026-09-06","Castellón 2-0 Albacete","V","","2-0"),("2026-09-12","","V","Girona 1-2 Castellón","1-2"),("2026-09-19","Castellón 5-0 Tenerife","V","","5-0")],
    "eibar": [("2026-08-16","Eibar 1-3 Tenerife","D","","1-3"),("2026-08-23","Eibar 1-0 Valladolid","V","","1-0"),("2026-08-30","","V","Andorra 0-1 Eibar","0-1"),("2026-09-06","Eibar 3-0 Granada","V","","3-0"),("2026-09-14","","V","Celta Fortuna 0-4 Eibar","0-4"),("2026-09-19","","V","Eldense 1-2 Eibar","1-2")],
    "mallorca": [("2026-08-15","Mallorca 2-0 Valladolid","V","","2-0"),("2026-08-24","","D","Granada 2-0 Mallorca","2-0"),("2026-08-30","Mallorca 3-0 Ceuta","V","","3-0"),("2026-09-05","","E","Eldense 0-0 Mallorca","0-0"),("2026-09-13","Mallorca 2-0 Sabadell","V","","2-0"),("2026-09-19","","V","Real Sociedad B 0-1 Mallorca","0-1")],
    "almeria": [("2026-08-17","Almería 3-0 Eldense","V","","3-0"),("2026-08-23","","D","Tenerife 1-0 Almería","1-0"),("2026-08-29","","D","Sabadell 1-0 Almería","1-0"),("2026-09-06","Almería 3-2 Cádiz","V","","3-2"),("2026-09-12","","V","Córdoba 0-2 Almería","0-2"),("2026-09-20","Almería 2-0 Celta Fortuna","V","","2-0")],
    "burgos": [("2026-08-16","Burgos 3-2 Córdoba","V","","3-2"),("2026-08-23","","D","Sporting 1-0 Burgos","1-0"),("2026-08-31","Burgos 2-2 Real Sociedad B","E","","2-2"),("2026-09-06","","E","Real Oviedo 0-0 Burgos","0-0"),("2026-09-11","Burgos 3-1 Ceuta","V","","3-1"),("2026-09-20","","V","Las Palmas 1-2 Burgos","1-2")],
    "sabadell": [("2026-08-17","","E","Sporting 0-0 Sabadell","0-0"),("2026-08-23","","E","Castellón 0-0 Sabadell","0-0"),("2026-08-29","Sabadell 1-0 Almería","V","","1-0"),("2026-09-07","Sabadell 3-2 Córdoba","V","","3-2"),("2026-09-13","","D","Mallorca 2-0 Sabadell","2-0"),("2026-09-20","Sabadell 3-1 Real Oviedo","V","","3-1")],
    "leganes": [("2026-08-16","","E","Girona 1-1 Leganés","1-1"),("2026-08-22","","V","Real Oviedo 0-1 Leganés","0-1"),("2026-08-29","Leganés 1-0 Eldense","V","","1-0"),("2026-09-04","","E","Las Palmas 0-0 Leganés","0-0"),("2026-09-13","","D","Tenerife 2-0 Leganés","2-0"),("2026-09-20","Leganés 3-2 Granada","V","","3-2")],
    "girona": [("2026-08-16","Girona 1-1 Leganés","E","","1-1"),("2026-08-21","","D","Córdoba 2-1 Girona","2-1"),("2026-08-29","Girona 5-2 Las Palmas","V","","5-2"),("2026-09-05","","V","Sporting 0-2 Girona","0-2"),("2026-09-12","Girona 1-2 Castellón","D","","1-2"),("2026-09-19","","V","Cádiz 1-2 Girona","1-2")],
    "sporting-gijon": [("2026-08-17","Sporting 0-0 Sabadell","E","","0-0"),("2026-08-23","Sporting 1-0 Burgos","V","","1-0"),("2026-08-28","","V","Tenerife 0-1 Sporting","0-1"),("2026-09-05","Sporting 0-2 Girona","D","","0-2"),("2026-09-13","Sporting 0-1 Eldense","D","","0-1"),("2026-09-19","","V","Andorra 1-3 Sporting","1-3")],
    "tenerife": [("2026-08-16","","V","Eibar 1-3 Tenerife","1-3"),("2026-08-23","Tenerife 1-0 Almería","V","","1-0"),("2026-08-28","Tenerife 0-1 Sporting","D","","0-1"),("2026-09-05","","E","Real Sociedad B 1-1 Tenerife","1-1"),("2026-09-13","Tenerife 2-0 Leganés","V","","2-0"),("2026-09-19","","D","Castellón 5-0 Tenerife","5-0")],
    "las-palmas": [("2026-08-16","Las Palmas 2-1 Albacete","V","","2-1"),("2026-08-22","","V","Ceuta 0-2 Las Palmas","0-2"),("2026-08-29","","D","Girona 5-2 Las Palmas","5-2"),("2026-09-04","Las Palmas 0-0 Leganés","E","","0-0"),("2026-09-13","","V","Cádiz 0-1 Las Palmas","0-1"),("2026-09-20","Las Palmas 1-2 Burgos","D","","1-2")],
    "real-sociedad-b": [("2026-08-14","Real Sociedad B 0-1 Castellón","D","","0-1"),("2026-08-22","","V","Albacete 1-2 Real Sociedad B","1-2"),("2026-08-31","","E","Burgos 2-2 Real Sociedad B","2-2"),("2026-09-05","Real Sociedad B 1-1 Tenerife","E","","1-1"),("2026-09-12","","V","Andorra 1-3 Real Sociedad B","1-3"),("2026-09-19","Real Sociedad B 0-1 Mallorca","D","","0-1")],
    "real-oviedo": [("2026-08-16","Real Oviedo 0-0 Granada","E","","0-0"),("2026-08-22","Real Oviedo 0-1 Leganés","D","","0-1"),("2026-08-30","","V","Albacete 0-1 Real Oviedo","0-1"),("2026-09-06","Real Oviedo 0-0 Burgos","E","","0-0"),("2026-09-13","","V","Valladolid 0-3 Real Oviedo","0-3"),("2026-09-20","","D","Sabadell 3-1 Real Oviedo","3-1")],
    "granada": [("2026-08-16","","E","Real Oviedo 0-0 Granada","0-0"),("2026-08-24","Granada 2-0 Mallorca","V","","2-0"),("2026-08-30","","V","Córdoba 1-3 Granada","1-3"),("2026-09-06","","D","Eibar 3-0 Granada","3-0"),("2026-09-12","Granada 1-1 Albacete","E","","1-1"),("2026-09-20","","D","Leganés 3-2 Granada","3-2")],
    "celta-fortuna": [("2026-08-16","","E","Cádiz 0-0 Celta Fortuna","0-0"),("2026-08-24","Celta Fortuna 4-2 Andorra","V","","4-2"),("2026-08-31","Celta Fortuna 1-2 Castellón","D","","1-2"),("2026-09-05","","V","Ceuta 0-2 Celta Fortuna","0-2"),("2026-09-14","Celta Fortuna 0-4 Eibar","D","","0-4"),("2026-09-20","","D","Almería 2-0 Celta Fortuna","2-0")],
    "cordoba": [("2026-08-16","","D","Burgos 3-2 Córdoba","3-2"),("2026-08-21","Córdoba 2-1 Girona","V","","2-1"),("2026-08-30","Córdoba 1-3 Granada","D","","1-3"),("2026-09-07","","D","Sabadell 3-2 Córdoba","3-2"),("2026-09-12","Córdoba 0-2 Almería","D","","0-2"),("2026-09-18","","V","Albacete 1-2 Córdoba","1-2")],
    "eldense": [("2026-08-17","","D","Almería 3-0 Eldense","3-0"),("2026-08-22","Eldense 2-2 Cádiz","E","","2-2"),("2026-08-29","","D","Leganés 1-0 Eldense","1-0"),("2026-09-05","Eldense 0-0 Mallorca","E","","0-0"),("2026-09-13","","V","Sporting 0-1 Eldense","0-1"),("2026-09-19","Eldense 1-2 Eibar","D","","1-2")],
    "valladolid": [("2026-08-15","","D","Mallorca 2-0 Valladolid","2-0"),("2026-08-23","","D","Eibar 1-0 Valladolid","1-0"),("2026-08-30","","E","Cádiz 1-1 Valladolid","1-1"),("2026-09-05","Valladolid 1-0 Andorra","V","","1-0"),("2026-09-13","Valladolid 0-3 Real Oviedo","D","","0-3"),("2026-09-20","","E","Ceuta 1-1 Valladolid","1-1")],
    "cadiz": [("2026-08-16","Cádiz 0-0 Celta Fortuna","E","","0-0"),("2026-08-22","","E","Eldense 2-2 Cádiz","2-2"),("2026-08-30","Cádiz 1-1 Valladolid","E","","1-1"),("2026-09-06","","D","Almería 3-2 Cádiz","3-2"),("2026-09-13","Cádiz 0-1 Las Palmas","D","","0-1"),("2026-09-19","Cádiz 1-2 Girona","D","","1-2")],
    "andorra": [("2026-08-15","Andorra 5-1 Ceuta","V","","5-1"),("2026-08-24","","D","Celta Fortuna 4-2 Andorra","4-2"),("2026-08-30","Andorra 0-1 Eibar","D","","0-1"),("2026-09-05","","D","Valladolid 1-0 Andorra","1-0"),("2026-09-12","Andorra 1-3 Real Sociedad B","D","","1-3"),("2026-09-19","Andorra 1-3 Sporting","D","","1-3")],
    "albacete": [("2026-08-16","","D","Las Palmas 2-1 Albacete","2-1"),("2026-08-22","Albacete 1-2 Real Sociedad B","D","","1-2"),("2026-08-30","Albacete 0-1 Real Oviedo","D","","0-1"),("2026-09-06","","D","Castellón 2-0 Albacete","2-0"),("2026-09-12","","E","Granada 1-1 Albacete","1-1"),("2026-09-18","Albacete 1-2 Córdoba","D","","1-2")],
    "ceuta": [("2026-08-15","","D","Andorra 5-1 Ceuta","5-1"),("2026-08-22","Ceuta 0-2 Las Palmas","D","","0-2"),("2026-08-30","","D","Mallorca 3-0 Ceuta","3-0"),("2026-09-05","Ceuta 0-2 Celta Fortuna","D","","0-2"),("2026-09-11","","D","Burgos 3-1 Ceuta","3-1"),("2026-09-20","Ceuta 1-1 Valladolid","E","","1-1")],
}

# --- MAPEO NOMBRES ESPN -> NUESTRAS CLAVES ---
MAPEO = {
    "ceuta": "ceuta", "ad ceuta": "ceuta",
    "castellon": "castellon", "cd castellon": "castellon",
    "eibar": "eibar", "sd eibar": "eibar",
    "mallorca": "mallorca", "real mallorca": "mallorca", "rcd mallorca": "mallorca",
    "almeria": "almeria", "ud almeria": "almeria",
    "burgos": "burgos", "burgos cf": "burgos",
    "sabadell": "sabadell", "ce sabadell": "sabadell",
    "leganes": "leganes", "cd leganes": "leganes",
    "girona": "girona", "girona fc": "girona",
    "sporting": "sporting-gijon", "gijon": "sporting-gijon", "sporting de gijon": "sporting-gijon",
    "tenerife": "tenerife", "cd tenerife": "tenerife",
    "las palmas": "las-palmas", "ud las palmas": "las-palmas",
    "real sociedad b": "real-sociedad-b", "real sociedad de futbol b": "real-sociedad-b", "sanse": "real-sociedad-b",
    "oviedo": "real-oviedo", "real oviedo": "real-oviedo",
    "granada": "granada", "granada cf": "granada",
    "celta fortuna": "celta-fortuna", "celta b": "celta-fortuna", "celta de vigo b": "celta-fortuna",
    "cordoba": "cordoba", "cordoba cf": "cordoba",
    "eldense": "eldense", "cd eldense": "eldense",
    "valladolid": "valladolid", "real valladolid": "valladolid",
    "cadiz": "cadiz", "cadiz cf": "cadiz",
    "andorra": "andorra", "fc andorra": "andorra",
    "albacete": "albacete", "albacete bp": "albacete",
}

def normaliza_nombre(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]',' ',s)
    s = s.strip()
    return s

def clave_equipo(nombre_espn):
    n = normaliza_nombre(nombre_espn)
    for k,v in MAPEO.items():
        if k in n: return v
    return None

out_dir = pathlib.Path("informes"); out_dir.mkdir(exist_ok=True)
historial_file = out_dir / "historial_hypermotion.json"
if historial_file.exists():
    try:
        j = json.loads(historial_file.read_text(encoding='utf-8'))
        for k,v in j.items():
            if len(v) > len(PARTIDOS.get(k,[])): PARTIDOS[k] = [tuple(x) for x in v]
    except: pass

# Parche J7 ya jugado
if len(PARTIDOS["girona"]) == 6:
    PARTIDOS["girona"].append(("2026-09-25","Girona 2-0 Albacete","V","","2-0"))
    PARTIDOS["albacete"].append(("2026-09-25","","D","Girona 2-0 Albacete","2-0"))
if len(PARTIDOS["ceuta"]) == 6:
    PARTIDOS["ceuta"].append(("2026-09-26","Ceuta 3-1 Real Sociedad B","V","","3-1"))
    PARTIDOS["real-sociedad-b"].append(("2026-09-26","","D","Ceuta 3-1 Real Sociedad B","3-1"))

# ========= FULL AUTO TODA LA JORNADA =========
def fetch_toda_jornada():
    madrid = ZoneInfo("Europe/Madrid")
    hoy = datetime.now(madrid)
    fechas = [(hoy - timedelta(days=i)).strftime("%Y%m%d") for i in range(0,4)] # busca ultimos 4 dias
    nuevos = 0
    for fecha_api in fechas:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.2/scoreboard?dates={fecha_api}"
            r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
            data = r.json()
            for ev in data.get("events",[]):
                league = ev.get("competitions",[{}])[0].get("notes",[])
                # filtramos solo segunda division españa (esp.2)
                if ev.get("competitions",[{}])[0].get("type",{}).get("id")!= "1": # opcional
                    pass
                comp = ev["competitions"][0]
                if not comp["status"]["type"]["completed"]: continue
                c = comp["competitors"]
                if len(c) < 2: continue
                home = c[0] if c[0]["homeAway"]=="home" else c[1]
                away = c[1] if c[0]["homeAway"]=="home" else c[0]
                home_name = home["team"]["displayName"]
                away_name = away["team"]["displayName"]
                clave_home = clave_equipo(home_name)
                clave_away = clave_equipo(away_name)
                if not clave_home or not clave_away: continue
                gol = f"{home['score']}-{away['score']}"
                fecha_real = comp["date"][:10] # YYYY-MM-DD
                # evita duplicados por fecha+gol
                ya = any(fecha_real in x[0] and gol in x[4] for x in PARTIDOS.get(clave_home,[]))
                if ya: continue
                # resultado
                hs = int(home['score']); aws = int(away['score'])
                if hs > aws: rh, ra = "V","D"
                elif hs < aws: rh, ra = "D","V"
                else: rh, ra = "E","E"
                texto = f"{home_name} {gol} {away_name}"
                PARTIDOS[clave_home].append((fecha_real, texto, rh, "", gol))
                PARTIDOS[clave_away].append((fecha_real, "", ra, texto, gol))
                print(f"AUTO NUEVO: {texto}")
                nuevos += 1
        except Exception as e:
            print(f"Fetch {fecha_api} pendiente: {e}")
    return nuevos

print("Buscando partidos nuevos...")
nuevos = fetch_toda_jornada()
print(f"Nuevos partidos detectados: {nuevos}")

def recalcular(d):
    t=[]
    for eq,lista in d.items():
        if not lista: continue
        pj=len(lista); g=sum(1 for _,_,r,_,_ in lista if r=='V'); e=sum(1 for _,_,r,_,_ in lista if r=='E'); p=sum(1 for _,_,r,_,_ in lista if r=='D')
        gf=gc=0
        for _,cc,_,_,gol in lista:
            if "-" in gol:
                try:
                    a,b=map(int,gol.split("-"));
                    if cc!="": gf+=a; gc+=b
                    else: gf+=b; gc+=a
                except: pass
        t.append((eq,pj,g*3+e,g,e,p,gf,gc))
    t.sort(key=lambda x:(x[2],x[6]-x[7],x[6]),reverse=True); return t

TABLA = recalcular(PARTIDOS)
historial_file.write_text(json.dumps({k:[list(x) for x in v] for k,v in PARTIDOS.items()},ensure_ascii=False,indent=2),encoding='utf-8')

def normaliza(s): return s.lower().replace("-","").replace("_","").replace(" ","")
logos_path = pathlib.Path("logos")
logos = {normaliza(p.stem): p for p in logos_path.glob("*.png")} if logos_path.exists() else {}
def get_logo(eq):
    k = normaliza(eq)
    for lk, path in logos.items():
        if k in lk or lk in k: return str(path)
    return None

fecha_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
hora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y - %H:%M")
pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"
doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
styles = getSampleStyleSheet()
story=[]; story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
style_sub = styles['Normal'].clone('subtitulo'); style_sub.alignment=TA_CENTER; style_sub.fontSize=13; style_sub.spaceAfter=10; style_sub.fontName='Helvetica-Bold'
J = max(len(v) for v in PARTIDOS.values())
story.append(Paragraph(f"Clasificacion EN VIVO - Jornada {J} - 26/27", style_sub)); story.append(Spacer(1,12))
data = [["#","","Equipo","PJ","PTS","G","E","P","GF","GC","DG"]]
for i,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
    dg = gf-gc; dg_str = f"+{dg}" if dg>0 else str(dg); lp = get_logo(eq); img = Image(lp, width=14, height=14) if lp and pathlib.Path(lp).exists() else ""; data.append([str(i),img,eq.replace("-"," ").title(),pj,pts,g,e,p,gf,gc,dg_str])
table = Table(data, colWidths=[22,20,125,28,32,25,25,25,32,32,32])
st = TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1B3B29")),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ALIGN',(0,0),(-1,-1),'CENTER'),('ALIGN',(2,1),(2,-1),'LEFT'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#DEE2E6")),('FONTSIZE',(0,0),(-1,0),9),('FONTSIZE',(0,1),(-1,-1),10)])
for r in range(1,len(data)):
    bg = colors.HexColor("#D4EDDA") if r<=2 else colors.HexColor("#FFF3CD") if r<=6 else colors.HexColor("#F8D7DA") if r>=19 else colors.HexColor("#FFFFFF") if r%2==0 else colors.HexColor("#F8F9FA")
    st.add('BACKGROUND',(0,r),(-1,r),bg)
table.setStyle(st); story.append(table); story.append(PageBreak())
for idx,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
    casa_v=casa_e=casa_d=fuera_v=fuera_e=fuera_d=0
    for f,c,r,fu,gol in PARTIDOS[eq]:
        if c!="":
            if r=='V': casa_v+=1
            elif r=='E': casa_e+=1
            else: casa_d+=1
        else:
            if r=='V': fuera_v+=1
            elif r=='E': fuera_e+=1
            else: fuera_d+=1
    lp=get_logo(eq)
    style_team_big=styles['Normal'].clone(f'team_big_{idx}'); style_team_big.fontSize=20; style_team_big.fontName='Helvetica-Bold'
    style_pj_big=styles['Normal'].clone(f'pj_big_{idx}'); style_pj_big.fontSize=12; style_pj_big.fontName='Helvetica-Bold'
    if lp and pathlib.Path(lp).exists():
        logo_img=Image(lp,width=60,height=60)
        header_data=[[logo_img,Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],["",Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
        ht=Table(header_data,colWidths=[70,400]); ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('SPAN',(0,0),(0,1))]))
    else:
        header_data=[[Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],[Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
        ht=Table(header_data,colWidths=[470])
    story.append(ht); story.append(Spacer(1,10))
    cajas_data=[[Paragraph(f"<b>EN CASA:</b> {casa_v}V - {casa_e}E - {casa_d}D",styles['Normal']),Paragraph(f"<b>FUERA:</b> {fuera_v}V - {fuera_e}E - {fuera_d}D",styles['Normal'])]]
    cajas=Table(cajas_data,colWidths=[150,150]); cajas.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor("#E8F5E9")),('BACKGROUND',(1,0),(1,0),colors.HexColor("#FFEBEE")),('BOX',(0,0),(0,0),1,colors.HexColor("#2E7D32")),('BOX',(1,0),(1,0),1,colors.HexColor("#C62828")),('ALIGN',(0,0),(-1,-1),'CENTER')]))
    story.append(cajas); story.append(Spacer(1,12))
    center_style=styles['Normal'].clone(f'centered_{idx}'); center_style.alignment=TA_CENTER
    story.append(Paragraph(f"<b>Partidos J1-{J}</b>",center_style)); story.append(Spacer(1,6))
    pd=[["Fecha","EN CASA","R","FUERA","GOL"]]
    for row in PARTIDOS[eq]: pd.append(list(row))
    pt=Table(pd,colWidths=[70,170,25,170,40])
    ps=TableStyle([('BACKGROUND',(0,0),(-1,0),colors.black),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),('GRID',(0,0),(-1,-1),0.4,colors.grey)])
    for ri in range(1,len(pd)):
        res = pd[ri][2]
        if res=='V': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#b6f5b6"))
        elif res=='D': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#ffb3b3"))
        elif res=='E': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#fff2b2"))
    pt.setStyle(ps); story.append(pt); story.append(PageBreak())
doc.build(story)
print(f"PDF J{J} OK - {pdf_file}")
