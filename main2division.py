import pathlib, json, requests, re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

PARTIDOS = {
    "castellon": [("2026-08-14","","V","Real Sociedad B 0-1 Castellón","0-1"),("2026-08-23","Castellón 0-0 Sabadell","E","","0-0"),("2026-08-31","", "V","Celta Fortuna 1-2 Castellón","1-2"),("2026-09-06","Castellón 2-0 Albacete","V","","2-0"),("2026-09-12","","V","Girona 1-2 Castellón","1-2"),("2026-09-19","Castellón 5-0 Tenerife","V","","5-0")],
    "eibar": [("2026-08-16","Eibar 1-3 Tenerife","D","","1-3"),("2026-08-23","Eibar 1-0 Valladolid","V","","1-0"),("2026-08-30","","V","Andorra 0-1 Eibar","0-1"),("2026-09-06","Eibar 3-0 Granada","V","","3-0"),("2026-09-14","","V","Celta Fortuna 0-4 Eibar","0-4"),("2026-09-19","","V","Eldense 1-2 Eibar","1-2")],
    "mallorca": [("2026-08-15","Mallorca 2-0 Valladolid","V","","2-0"),("2026-08-24","","D","Granada 2-0 Mallorca","2-0"),("2026-08-30","Mallorca 3-0 Ceuta","V","","3-0"),("2026-09-05","","E","Eldense 0-0 Mallorca","0-0"),("2026-09-13","Mallorca 2-0 Sabadell","V","","2-0"),("2026-09-19","","V","Real Sociedad B 0-1 Mallorca","0-1")],
    "almeria": [("2026-08-17","Almería 3-0 Eldense","V","","3-0"),("2026-08-23","","D","Tenerife 1-0 Almería","1-0"),("2026-08-29","","D","Sabadell 1-0 Almería","1-0"),("2026-09-06","Almería 3-2 Cádiz","V","","3-2"),("2026-09-12","","V","Córdoba 0-2 Almería","0-2"),("2026-09-20","Almería 2-0 Celta Fortuna","V","","2-0")],
    "burgos": [("2026-08-16","Burgos 3-2 Córdoba","V","","3-2"),("2026-08-23","","D","Sporting 1-0 Burgos","1-0"),("2026-08-31","Burgos 2-2 Real Sociedad B","E","","2-2"),("2026-09-06","","E","Real Oviedo 0-0 Burgos","0-0"),("2026-09-11","Burgos 3-1 Ceuta","V","","3-1"),("2026-09-20","","V","Las Palmas 1-2 Burgos","1-2")],
    "sabadell": [("2026-08-17","","E","Sporting 0-0 Sabadell","0-0"),("2026-08-23","","E","Castellón 0-0 Sabadell","0-0"),("2026-08-29","Sabadell 1-0 Almería","V","","1-0"),("2026-09-07","Sabadell 3-2 Córdoba","V","","3-2"),("2026-09-13","","D","Mallorca 2-0 Sabadell","2-0"),("2026-09-20","Sabadell 3-1 Real Oviedo","V","","3-1")],
    "leganes": [("2026-08-16","","E","Girona 1-1 Leganés","1-1"),("2026-08-22","","V","Real Oviedo 0-1 Leganés","0-1"),("2026-08-29","Leganés 1-0 Eldense","V","","1-0"),("2026-09-04","","E","Las Palmas 0-0 Leganés","0-0"),("2026-09-13","","D","Tenerife 2-0 Leganés","2-0"),("2026-09-20","Leganés 3-2 Granada","V","","3-2")],
    "girona": [("2026-08-16","Girona 1-1 Leganés","E","","1-1"),("2026-08-21","","D","Córdoba 2-1 Girona","2-1"),("2026-08-29","Girona 5-2 Las Palmas","V","","5-2"),("2026-09-05","","V","Sporting 0-2 Girona","0-2"),("2026-09-12","Girona 1-2 Castellón","D","","1-2"),("2026-09-19","","V","Cádiz 1-2 Girona","1-2"),("2026-09-25","Girona 2-0 Albacete","V","","2-0")],
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
    "albacete": [("2026-08-16","","D","Las Palmas 2-1 Albacete","2-1"),("2026-08-22","Albacete 1-2 Real Sociedad B","D","","1-2"),("2026-08-30","Albacete 0-1 Real Oviedo","D","","0-1"),("2026-09-06","","D","Castellón 2-0 Albacete","2-0"),("2026-09-12","","E","Granada 1-1 Albacete","1-1"),("2026-09-18","Albacete 1-2 Córdoba","D","","1-2"),("2026-09-25","","D","Girona 2-0 Albacete","2-0")],
    "ceuta": [("2026-08-15","","D","Andorra 5-1 Ceuta","5-1"),("2026-08-22","Ceuta 0-2 Las Palmas","D","","0-2"),("2026-08-30","","D","Mallorca 3-0 Ceuta","3-0"),("2026-09-05","Ceuta 0-2 Celta Fortuna","D","","0-2"),("2026-09-11","","D","Burgos 3-1 Ceuta","3-1"),("2026-09-20","Ceuta 1-1 Valladolid","E","","1-1"),("2026-09-26","Ceuta 3-1 Real Sociedad B","V","","3-1")],
}

MAPEO = {"ceuta":"ceuta","ad ceuta":"ceuta","castellon":"castellon","cd castellon":"castellon","eibar":"eibar","sd eibar":"eibar","mallorca":"mallorca","real mallorca":"mallorca","rcd mallorca":"mallorca","almeria":"almeria","ud almeria":"almeria","burgos":"burgos","burgos cf":"burgos","sabadell":"sabadell","ce sabadell":"sabadell","leganes":"leganes","cd leganes":"leganes","girona":"girona","girona fc":"girona","sporting":"sporting-gijon","gijon":"sporting-gijon","sporting de gijon":"sporting-gijon","tenerife":"tenerife","cd tenerife":"tenerife","las palmas":"las-palmas","ud las palmas":"las-palmas","real sociedad b":"real-sociedad-b","real sociedad de futbol b":"real-sociedad-b","sanse":"real-sociedad-b","real sociedad ii":"real-sociedad-b","oviedo":"real-oviedo","real oviedo":"real-oviedo","granada":"granada","granada cf":"granada","celta fortuna":"celta-fortuna","celta b":"celta-fortuna","cordoba":"cordoba","cordoba cf":"cordoba","eldense":"eldense","cd eldense":"eldense","valladolid":"valladolid","real valladolid":"valladolid","cadiz":"cadiz","cadiz cf":"cadiz","andorra":"andorra","fc andorra":"andorra","albacete":"albacete","albacete bp":"albacete"}

# ✅ CREAR out_dir AL INICIO
out_dir = pathlib.Path("informes")
out_dir.mkdir(exist_ok=True)
historial_file = out_dir / "historial_hypermotion.json"

def normaliza_nombre(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]',' ',s)
    return s.strip()

def clave_equipo(nombre_espn):
    n = normaliza_nombre(nombre_espn)
    for k,v in MAPEO.items():
        if k in n: return v
    return None

#if historial_file.exists():
#    try:
#        j = json.loads(historial_file.read_text(encoding='utf-8'))
#        for k,v in j.items():
#            if len(v) > len(PARTIDOS.get(k,[])): PARTIDOS[k] = [tuple(x) for x in v]
#    except: pass

def fetch_laliga2_matches():
    """Obtiene partidos de LaLiga2 desde livescoreFootball"""
    try:
        # Probar endpoint
        url = "https://worldcup26.ir/api/matches"
        params = {"league_id": 308, "season": 2026}
        
        print(f"🔄 Consultando: {url}")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Respuesta recibida: {len(data)} partidos")
            return data if isinstance(data, list) else data.get("matches", [])
        else:
            print(f"✗ Error {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def procesar_partidos(matches):
    """Procesa partidos y retorna tuplas en formato tu JSON"""
    partidos = []
    
    for match in matches:
        try:
            fecha = match.get("date", "")[:10]  # YYYY-MM-DD
            home_team = match.get("home_team", {}).get("name", "")
            away_team = match.get("away_team", {}).get("name", "")
            home_score = match.get("home_score")
            away_score = match.get("away_score")
            
            # Verificar que tenga resultado
            if home_score is None or away_score is None:
                continue
            
            gol = f"{home_score}-{away_score}"
            texto_home = f"{home_team} {gol} {away_team}"
            
            # Determinar resultado
            if home_score > away_score:
                result_home, result_away = "V", "D"
            elif home_score < away_score:
                result_home, result_away = "D", "V"
            else:
                result_home, result_away = "E", "E"
            
            clave_h = clave_equipo(home_team)
            clave_a = clave_equipo(away_team)
            
            if clave_h and clave_a:
                partidos.append({
                    "fecha": fecha,
                    "home_team": home_team,
                    "away_team": away_team,
                    "clave_home": clave_h,
                    "clave_away": clave_a,
                    "resultado_home": result_home,
                    "resultado_away": result_away,
                    "gol": gol,
                    "texto": texto_home
                })
        except Exception as e:
            print(f"  ⚠️  Error procesando partido: {e}")
    
    return partidos

def actualizar_json(nuevos_partidos):
    """Actualiza historial_hypermotion.json"""
    global PARTIDOS

    agregados = 0
    
    for p in nuevos_partidos:
        # Verificar si ya existe
        ya_existe = any(
            x[4] == p["gol"] and p["home_team"] in x[1]
            for x in PARTIDOS.get(p["clave_home"], [])
        )
        
        if ya_existe:
            print(f"  ✓ Ya existe: {p['texto']}")
            continue
        
        # Agregar para equipo local
        PARTIDOS[p["clave_home"]].append([
            p["fecha"],
            p["texto"],
            p["resultado_home"],
            "",
            p["gol"]
        ])
        
        # Agregar para equipo visitante
        PARTIDOS[p["clave_away"]].append([
            p["fecha"],
            "",
            p["resultado_away"],
            p["texto"],
            p["gol"]
        ])
        
        print(f"  ✅ Agregado: {p['texto']}")
        agregados += 1

    guardar_partidos()
    print(f"\n📊 {agregados} partidos nuevos\n")
    return agregados

def guardar_partidos():
    """Guarda PARTIDOS en JSON"""
    with open(historial_file, 'w', encoding='utf-8') as f:
        json.dump({k:[list(x) for x in v] for k,v in PARTIDOS.items()}, f, ensure_ascii=False, indent=2)

def fetch_toda_jornada():
    global PARTIDOS
    nuevos = 0
    print("Buscando partidos nuevos...")
    print("Consultando LivescoreFootball API J7 (worldcup26.ir)...")

    BASE = "https://worldcup26.ir"
    headers = {"User-Agent": "Mozilla/5.0"}

    endpoints = [
        f"{BASE}/get/soccer/esp.2/fixtures?status=all&from=20260926&to=20260928&limit=100",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260927",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260926",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260928",
    ]

    eventos = []
    for url in endpoints:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            print(f" -> {url} -> {r.status_code} len {len(r.text)}")
            if r.status_code != 200: continue
            data = r.json()
            batch = data.get("events") or data.get("matches") or data.get("data") or data
            if isinstance(batch, dict): batch = batch.get("events", [])
            if isinstance(batch, list) and len(batch) > 0:
                eventos.extend(batch)
        except Exception as e:
            print(f"Error {url}: {e}")

    vistos = set()
    unicos = []
    for ev in eventos:
        eid = str(ev.get("id") or ev.get("eventId") or ev.get("source",{}).get("event_key") or ev.get("slug"))
        if eid in vistos: continue
        vistos.add(eid)
        unicos.append(ev)

    print(f"Eventos totales recuperados: {len(unicos)}")

    for ev in unicos:
        try:
            home = ev.get("homeTeam",{}).get("name") or ev.get("home",{}).get("name") or ev.get("homeTeam")
            away = ev.get("awayTeam",{}).get("name") or ev.get("away",{}).get("name") or ev.get("awayTeam")
            
            if isinstance(home, dict): home = home.get("name")
            if isinstance(away, dict): away = away.get("name")

            hs = ev.get("homeScore",{}).get("current")
            aws = ev.get("awayScore",{}).get("current")
            
            if hs is None: hs = ev.get("homeScore") or ev.get("score",{}).get("home")
            if aws is None: aws = ev.get("awayScore") or ev.get("score",{}).get("away")
            if hs is None or aws is None: continue

            gol = f"{int(hs)}-{int(aws)}"
            ts = ev.get("startTimestamp") or ev.get("timestamp")
            if ts:
                fecha_real = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
            else:
                fecha_real = ev.get("date","2026-09-27")[:10]

            clave_home = clave_equipo(home)
            clave_away = clave_equipo(away)
            if not clave_home or not clave_away: continue

            ya = any(fecha_real==x[0] and gol==x[4] for x in PARTIDOS.get(clave_home,[]))
            if ya: continue

            rh = "V" if int(hs)>int(aws) else "D" if int(hs)<int(aws) else "E"
            ra = "D" if rh=="V" else "V" if rh=="D" else "E"
            texto = f"{home} {gol} {away}"
            PARTIDOS[clave_home].append((fecha_real, texto, rh, "", gol))
            PARTIDOS[clave_away].append((fecha_real, "", ra, texto, gol))
            print(f"AUTO NUEVO Livescore: {texto}")
            nuevos+=1
        except Exception as e:
            continue

    print(f"Nuevos partidos detectados: {nuevos}")
    return nuevos

def recalcular(d):
    t=[]
    for eq,lista in d.items():
        if not lista: continue
        pj=len(lista)
        g=sum(1 for _,_,r,_,_ in lista if r=='V')
        e=sum(1 for _,_,r,_,_ in lista if r=='E')
        p=sum(1 for _,_,r,_,_ in lista if r=='D')
        gf=gc=0
        for _,cc,_,_,gol in lista:
            if "-" in gol:
                try:
                    a,b=map(int,gol.split("-"))
                    if cc!="": gf+=a; gc+=b
                    else: gf+=b; gc+=a
                except: pass
        t.append((eq,pj,g*3+e,g,e,p,gf,gc))
    t.sort(key=lambda x:(x[2],x[6]-x[7],x[6]),reverse=True)
    return t

def generar_pdf():
    """Genera el PDF con la clasificación"""
    def normaliza(s): 
        return s.lower().replace("-","").replace("_","").replace(" ","")
    
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
    story=[]
    
    TABLA = recalcular(PARTIDOS)
    
    story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
    style_sub = styles['Normal'].clone('subtitulo')
    style_sub.alignment=TA_CENTER
    style_sub.fontSize=13
    style_sub.spaceAfter=10
    style_sub.fontName='Helvetica-Bold'
    
    J = max(len(v) for v in PARTIDOS.values()) if PARTIDOS.values() else 0
    story.append(Paragraph(f"Clasificacion EN VIVO - Jornada {J}", style_sub))
    story.append(Spacer(1,12))
    
    data = [["#","","Equipo","PJ","PTS","G","E","P","GF","GC","DG"]]
    for i,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
        dg = gf-gc
        dg_str = f"+{dg}" if dg>0 else str(dg)
        lp = get_logo(eq)
        img = Image(lp, width=14, height=14) if lp and pathlib.Path(lp).exists() else ""
        data.append([str(i),img,eq.replace("-"," "),str(pj),str(pts),str(g),str(e),str(p),str(gf),str(gc),dg_str])
    
    table = Table(data, colWidths=[22,20,125,28,32,25,25,25,32,32,32])
    st = TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1B3B29")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('ALIGN',(2,1),(2,-1),'LEFT'),
        ('GRID',(0,0),(-1,-1),0.3,colors.black)
    ])
    
    for r in range(1,len(data)):
        if r<=2: bg = colors.HexColor("#D4EDDA")
        elif r<=6: bg = colors.HexColor("#FFF3CD")
        elif r>=19: bg = colors.HexColor("#F8D7DA")
        elif r%2==0: bg = colors.HexColor("#FFFFFF")
        else: bg = colors.HexColor("#F8F9FA")
        st.add('BACKGROUND',(0,r),(-1,r),bg)
    
    table.setStyle(st)
    story.append(table)
    story.append(PageBreak())
    
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
        style_team_big=styles['Normal'].clone(f'team_big_{idx}')
        style_team_big.fontSize=20
        style_team_big.fontName='Helvetica-Bold'
        style_pj_big=styles['Normal'].clone(f'pj_big_{idx}')
        style_pj_big.fontSize=12
        style_pj_big.fontName='Helvetica-Bold'
        
        if lp and pathlib.Path(lp).exists():
            logo_img=Image(lp,width=60,height=60)
            header_data=[[logo_img,Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],["",Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
            ht=Table(header_data,colWidths=[70,400])
            ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('SPAN',(0,0),(0,1))]))
        else:
            header_data=[[Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],[Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
            ht=Table(header_data,colWidths=[470])
        
        story.append(ht)
        story.append(Spacer(1,10))
        
        cajas_data=[[Paragraph(f"<b>EN CASA:</b> {casa_v}V - {casa_e}E - {casa_d}D",styles['Normal']),Paragraph(f"<b>FUERA:</b> {fuera_v}V - {fuera_e}E - {fuera_d}D",styles['Normal'])]]
        cajas=Table(cajas_data,colWidths=[150,150])
        cajas.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor("#E8F5E9")),('BACKGROUND',(1,0),(1,0),colors.HexColor("#FFEBEE")),('BOX',(0,0),(-1,-1),0.5,colors.black)]))
        story.append(cajas)
        story.append(Spacer(1,12))
        
        center_style=styles['Normal'].clone(f'centered_{idx}')
        center_style.alignment=TA_CENTER
        story.append(Paragraph(f"<b>Partidos J1-{J}</b>",center_style))
        story.append(Spacer(1,6))
        
        pd=[["Fecha","EN CASA","R","FUERA","GOL"]]
        for row in PARTIDOS[eq]:
            pd.append(list(row))
        
        pt=Table(pd,colWidths=[70,170,25,170,40])
        ps=TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.black),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,-1),8)
        ])
        
        for ri in range(1,len(pd)):
            res = pd[ri][2]
            if res=='V': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#b6f5b6"))
            elif res=='D': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#ffb3b3"))
            elif res=='E': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#fff2b2"))
        
        pt.setStyle(ps)
        story.append(pt)
        story.append(PageBreak())
    
    doc.build(story)
    print(f"PDF J{J} OK - {pdf_file}")

# ✅ ORDEN CORRECTO: Buscar partidos primero, luego generar PDF
if __name__ == "__main__":
    print("=" * 60)
    print("🔄 ACTUALIZAR LaLiga2 - Partidos Nuevos")
    print("=" * 60 + "\n")
    
    print("Buscando partidos nuevos...")
    nuevos = fetch_toda_jornada()
    print(f"Nuevos partidos detectados: {nuevos}\n")
    
    guardar_partidos()
    
    print("Generando PDF...")
    generar_pdf()

