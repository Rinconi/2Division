import pathlib, json, requests, re
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

# Directorio y archivo
out_dir = pathlib.Path("informes")
out_dir.mkdir(exist_ok=True)
historial_file = out_dir / "historial_hypermotion.json"
log_file = out_dir / "ejecuciones.log"

# MAPEO de equipos
MAPEO = {
    "ceuta":"ceuta","ad ceuta":"ceuta",
    "castellon":"castellon","cd castellon":"castellon","castellón":"castellon",
    "eibar":"eibar","sd eibar":"eibar",
    "mallorca":"mallorca","real mallorca":"mallorca","rcd mallorca":"mallorca",
    "almeria":"almeria","ud almería":"almeria","almería":"almeria",
    "burgos":"burgos","cf burgos":"burgos",
    "sabadell":"sabadell","ce sabadell":"sabadell",
    "leganes":"leganes","cd leganés":"leganes","leganés":"leganes",
    "girona":"girona","cf girona":"girona",
    "sporting":"sporting-gijon","sporting gijon":"sporting-gijon","real sporting":"sporting-gijon",
    "tenerife":"tenerife","cd tenerife":"tenerife",
    "las palmas":"las-palmas","ud las palmas":"las-palmas",
    "real sociedad":"real-sociedad-b","real sociedad b":"real-sociedad-b",
    "real oviedo":"real-oviedo",
    "granada":"granada","granada cf":"granada",
    "celta":"celta-fortuna","celta fortuna":"celta-fortuna","rc celta":"celta-fortuna",
    "cordoba":"cordoba","córdoba":"cordoba",
    "eldense":"eldense","cf eldense":"eldense",
    "valladolid":"valladolid","real valladolid":"valladolid",
    "cadiz":"cadiz","cádiz":"cadiz",
    "andorra":"andorra","fc andorra":"andorra",
    "albacete":"albacete","albacete bp":"albacete",
}

def log_mensaje(msg):
    """Escribe en log y consola"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(msg)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg + "\n")

def normaliza_nombre(s):
    """Normaliza nombres de equipos para búsqueda"""
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]',' ',s)
    return s.strip()

def clave_equipo(nombre_espn):
    """Obtiene la clave de equipo del mapeo"""
    n = normaliza_nombre(nombre_espn)
    for k, v in MAPEO.items():
        if k in n: 
            return v
    return None

def cargar_partidos():
    """Carga PARTIDOS desde JSON, o crea estructura vacía"""
    global PARTIDOS
    if historial_file.exists():
        try:
            with open(historial_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                PARTIDOS = {k: [tuple(x) for x in v] for k, v in data.items()}
            log_mensaje(f"✅ Cargados partidos desde {historial_file.name}")
            return PARTIDOS
        except Exception as e:
            log_mensaje(f"❌ Error cargando JSON: {e}")
    
    PARTIDOS = {
        "castellon": [], "eibar": [], "mallorca": [], "almeria": [], "burgos": [],
        "sabadell": [], "leganes": [], "girona": [], "sporting-gijon": [], "tenerife": [],
        "las-palmas": [], "real-sociedad-b": [], "real-oviedo": [], "granada": [],
        "celta-fortuna": [], "cordoba": [], "eldense": [], "valladolid": [], "cadiz": [],
        "andorra": [], "albacete": [], "ceuta": [],
    }
    log_mensaje("⚠️  Estructura PARTIDOS vacía (JSON no encontrado)")
    return PARTIDOS

def guardar_partidos():
    """Guarda PARTIDOS en JSON"""
    with open(historial_file, 'w', encoding='utf-8') as f:
        json.dump({k:[list(x) for x in v] for k,v in PARTIDOS.items()}, f, ensure_ascii=False, indent=2)
    log_mensaje(f"✅ JSON guardado: {historial_file}")

def extrae_resultado(ev):
    """Extrae el marcador del evento de varias formas posibles"""
    hs = ev.get("homeScore", {}).get("current") if isinstance(ev.get("homeScore"), dict) else ev.get("homeScore")
    aws = ev.get("awayScore", {}).get("current") if isinstance(ev.get("awayScore"), dict) else ev.get("awayScore")
    if hs is None: hs = ev.get("score", {}).get("home")
    if aws is None: aws = ev.get("score", {}).get("away")
    try: hs = int(hs) if hs is not None else None
    except: hs = None
    try: aws = int(aws) if aws is not None else None
    except: aws = None
    return hs, aws

def extrae_fecha(ev):
    """Extrae la fecha del evento con zona horaria correcta"""
    ts = ev.get("startTimestamp") or ev.get("timestamp")
    if ts:
        try:
            ts_int = int(ts)
            return datetime.fromtimestamp(ts_int, tz=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
        except: pass
    fecha_raw = ev.get("date", "2026-09-27")
    return fecha_raw[:10] if fecha_raw else "2026-09-27"

def partido_existe(clave_home, clave_away, fecha, marcador):
    """Verifica si un partido ya existe en el historial de forma robusta"""
    for equipo in [clave_home, clave_away]:
        for partido_local in PARTIDOS.get(equipo, []):
            if len(partido_local) >= 5 and partido_local[0] == fecha and partido_local[4] == marcador:
                return True
    return False

def fetch_toda_jornada(debug=False):
    """Obtiene partidos nuevos de la API con trazas DEBUG avanzadas"""
    global PARTIDOS
    nuevos = 0
    contadores = {"sin_equipos": 0, "sin_marcador": 0, "no_mapeado_home": 0, "no_mapeado_away": 0, "no_mapeado_ambos": 0, "ya_existe": 0, "con_error": 0}
    no_mapeados = []
    debug_count = 0
    
    log_mensaje("🔄 Buscando partidos nuevos en la API...")
    BASE = "https://worldcup26.ir"
    headers = {"User-Agent": "Mozilla/5.0"}
    endpoints = [
        f"{BASE}/get/soccer/esp.2/fixtures?status=all&from=20260901&to=20261231&limit=500",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260926",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260927",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260928",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260929",
        f"{BASE}/get/soccer/esp.2/scoreboard?dates=20260930",
    ]
    eventos = []
    for url in endpoints:
        try:
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                data = r.json()
                batch = data.get("events") or data.get("matches") or data.get("data") or data
                if isinstance(batch, dict): batch = batch.get("events", [])
                if isinstance(batch, list): eventos.extend(batch)
        except Exception as e: log_mensaje(f" ✗ Error en endpoint: {e}")

    vistos = set()
    unicos = []
    for ev in eventos:
        eid = str(ev.get("id") or ev.get("eventId") or ev.get("slug"))
        if eid not in vistos:
            vistos.add(eid)
            unicos.append(ev)

    log_mensaje(f"📊 Eventos unicos recuperados: {len(unicos)}")

    for ev in unicos:
        try:
            if debug and debug_count < 3:
                log_mensaje(f"\n🔍 [DEBUG] EVENTO {debug_count}:\n{json.dumps(ev, indent=2)}\n" + "="*40)
                debug_count += 1
            
            home = ev.get("homeTeam",{}).get("name") or ev.get("home",{}).get("name") or ev.get("homeTeam")
            away = ev.get("awayTeam",{}).get("name") or ev.get("away",{}).get("name") or ev.get("awayTeam")
            if isinstance(home, dict): home = home.get("name")
            if isinstance(away, dict): away = away.get("name")
            
            if not home or not away:
                contadores["sin_equipos"] += 1
                continue

            hs, aws = extrae_resultado(ev)
            if hs is None or aws is None:
                contadores["sin_marcador"] += 1
                continue

            fecha_real = extrae_fecha(ev)
            gol = f"{int(hs)}-{int(aws)}"
            clave_home, clave_away = clave_equipo(home), clave_equipo(away)
            
            if not clave_home or not clave_away:
                if not clave_home and not clave_away: contadores["no_mapeado_ambos"] += 1
                elif not clave_home: contadores["no_mapeado_home"] += 1
                else: contadores["no_mapeado_away"] += 1
                no_mapeados.append(f"{home} vs {away}")
                continue

            if partido_existe(clave_home, clave_away, fecha_real, gol):
                contadores["ya_existe"] += 1
                continue

            rh = "V" if int(hs)>int(aws) else "D" if int(hs)<int(aws) else "E"
            ra = "D" if rh=="V" else "V" if rh=="D" else "E"
            texto = f"{home} {gol} {away}"
            
            PARTIDOS[clave_home].append((fecha_real, texto, rh, "", gol))
            PARTIDOS[clave_away].append((fecha_real, "", ra, texto, gol))
            log_mensaje(f"  ✅ Agregado: {texto} ({fecha_real})")
            nuevos += 1
        except Exception as e:
            contadores["con_error"] += 1
            import traceback
            log_mensaje(f"  💥 ERROR: {e}\n{traceback.format_exc()}")
            continue

    log_mensaje("\n📊 AUDITORIA DE EVENTOS DESCARTADOS Y FILTRADOS")
    log_mensaje(f"  ▶️ Nuevos partidos agregados:     {nuevos}")
    log_mensaje(f"  ⚠️ Saltados por falta de marcador: {contadores['sin_marcador']}")
    log_mensaje(f"  ✓ Saltados porque ya existian:     {contadores['ya_existe']}")
    log_mensaje(f"  ❌ Error mapeo (Local no existe):  {contadores['no_mapeado_home']}")
    log_mensaje(f"  ❌ Error mapeo (Visita no existe): {contadores['no_mapeado_away']}")
    log_mensaje(f"  ❌ Error mapeo (Ninguno existe):   {contadores['no_mapeado_ambos']}")
    log_mensaje(f"  💥 Errores ocultos (Excepciones):  {contadores['con_error']}")
    return nuevos
def recalcular(d):
    """Recalcula la tabla de clasificación"""
    t = []
    for eq, lista in d.items():
        if not lista: continue
        pj = len(lista)
        g = sum(1 for _, _, r, _, _ in lista if r == 'V')
        e = sum(1 for _, _, r, _, _ in lista if r == 'E')
        p = sum(1 for _, _, r, _, _ in lista if r == 'D')
        gf = gc = 0
        for fecha, en_casa, resultado, fuera, gol in lista:
            if "-" in gol:
                try:
                    gol_local, gol_visitante = map(int, gol.split("-"))
                    if en_casa != "": gf += gol_local; gc += gol_visitante
                    else: gf += gol_visitante; gc += gol_local
                except: pass
        t.append((eq, pj, g*3 + e, g, e, p, gf, gc))
    t.sort(key=lambda x: (x[2], x[6]-x[7], x[6]), reverse=True)
    return t

def mostrar_clasificacion(tabla):
    """Muestra la clasificación en consola"""
    log_mensaje("\n" + "="*90 + "\nCLASIFICACIÓN ACTUAL\n" + "="*90)
    for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(tabla, 1):
        dg = gf - gc
        dg_str = f"+{dg}" if dg > 0 else str(dg)
        log_mensaje(f"{i:<4} {eq.replace('-', ' ').title():<25} {pj:<4} {pts:<4} {gf:<3} {gc:<3} {dg_str:<4}")

def get_logo(eq):
    """Obtiene el logo de un equipo si existe"""
    logos_path = pathlib.Path("logos")
    if not logos_path.exists(): return None
    logos = {p.stem.lower().replace("-",""): p for p in logos_path.glob("*.png")}
    return str(logos.get(eq.lower().replace("-",""))) if eq.lower().replace("-","") in logos else None

def generar_pdf():
    """Genera el PDF con la clasificación y fichas de equipos"""
    fecha_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
    pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"
    doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
    
    TABLA = recalcular(PARTIDOS)
    story.append(Paragraph("<b>LaLiga Hypermotion - Clasificación</b>", styles['Title']))
    
    data = [["#","","Equipo","PJ","PTS","G","E","P","GF","GC","DG"]]
    for i,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
        dg = gf-gc
        dg_str = f"+{dg}" if dg>0 else str(dg)
        lp = get_logo(eq)
        img = Image(lp, width=14, height=14) if lp and pathlib.Path(lp).exists() else ""
        data.append([str(i),img,eq.replace("-"," ").title(),str(pj),str(pts),str(g),str(e),str(p),str(gf),str(gc),dg_str])
    
    table = Table(data, colWidths=[22,20,125,28,32,25,25,25,32,32,32])
    st = TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1B3B29")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID',(0,0),(-1,-1),0.3,colors.black)
    ])
    table.setStyle(st)
    story.append(table)
    doc.build(story)
    log_mensaje(f"✅ PDF generado: {pdf_file}")

if __name__ == "__main__":
    PARTIDOS = cargar_partidos()
    nuevos = fetch_toda_jornada(debug=True)
    if nuevos > 0: guardar_partidos()
    TABLA = recalcular(PARTIDOS)
    mostrar_clasificacion(TABLA)
    generar_pdf()
