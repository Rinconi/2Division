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
    hs = None
    aws = None
    
    if isinstance(ev.get("homeScore"), dict):
        hs = ev.get("homeScore", {}).get("current")
    if isinstance(ev.get("awayScore"), dict):
        aws = ev.get("awayScore", {}).get("current")
    
    if hs is None: hs = ev.get("homeScore")
    if aws is None: aws = ev.get("awayScore")
    
    if hs is None: hs = ev.get("score", {}).get("home")
    if aws is None: aws = ev.get("score", {}).get("away")
    
    if isinstance(hs, str):
        try: hs = int(hs)
        except: hs = None
    if isinstance(aws, str):
        try: aws = int(aws)
        except: aws = None
    
    return hs, aws

def extrae_fecha(ev):
    """Extrae la fecha del evento con zona horaria correcta"""
    ts = ev.get("startTimestamp") or ev.get("timestamp")
    
    if ts:
        try:
            ts_int = int(ts) if isinstance(ts, str) else ts
            fecha_real = datetime.fromtimestamp(ts_int, tz=ZoneInfo("UTC"))\
                .astimezone(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
            return fecha_real
        except:
            pass
    
    fecha_raw = ev.get("date", "2026-09-27")
    if fecha_raw:
        return fecha_raw[:10]
    
    return "2026-09-27"

def partido_existe(clave_home, clave_away, fecha, marcador):
    """Verifica si un partido ya existe en el historial de forma robusta"""
    for equipo in [clave_home, clave_away]:
        for partido_local in PARTIDOS.get(equipo, []):
            try:
                fecha_local = partido_local[0]
                gol = partido_local[4]
                if fecha_local == fecha and gol == marcador:
                    return True
            except:
                pass
    return False

def fetch_toda_jornada(debug=False):
    """Obtiene partidos nuevos de la API con trazas DEBUG avanzadas"""
    global PARTIDOS
    nuevos = 0
    
    contadores = {
        "sin_equipos": 0,
        "sin_marcador": 0,
        "no_mapeado_home": 0,
        "no_mapeado_away": 0,
        "no_mapeado_ambos": 0,
        "ya_existe": 0,
        "con_error": 0
    }
    
    no_mapeados = []
    debug_count = 0
    
    log_mensaje("\n🔄 Buscando partidos nuevos en la API...")
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
            log_mensaje(f" -> {r.status_code} ({len(r.text)} bytes)")
            if r.status_code != 200: 
                continue
            data = r.json()
            batch = data.get("events") or data.get("matches") or data.get("data") or data
            if isinstance(batch, dict): 
                batch = batch.get("events", [])
            if isinstance(batch, list) and len(batch) > 0:
                eventos.extend(batch)
        except Exception as e:
            log_mensaje(f" ✗ Error en endpoint {url}: {e}")

    vistos = set()
    unicos = []
    for ev in eventos:
        eid = str(ev.get("id") or ev.get("eventId") or ev.get("source",{}).get("event_key") or ev.get("slug"))
        if eid in vistos: 
            continue
        vistos.add(eid)
        unicos.append(ev)

    log_mensaje(f"📊 Eventos únicos recuperados: {len(unicos)}
")

    for ev in unicos:
        try:
            if debug and debug_count < 3:
                log_mensaje(f"\n🔍 [DEBUG] ESTRUCTURA COMPLETA DEL EVENTO {debug_count}:")
                log_mensaje(json.dumps(ev, indent=2))
                log_mensaje("="*50)
                debug_count += 1
            
            home = ev.get("homeTeam",{}).get("name") or ev.get("home",{}).get("name") or ev.get("homeTeam")
            away = ev.get("awayTeam",{}).get("name") or ev.get("away",{}).get("name") or ev.get("awayTeam")
            
            if isinstance(home, dict): home = home.get("name")
            if isinstance(away, dict): away = away.get("name")
            
            if not home or not away:
                contadores["sin_equipos"] += 1
                if debug:
                    log_mensaje(f"  ⚠️  Descartado: Datos de equipos ausentes (home: {home}, away: {away})")
                continue

            hs, aws = extrae_resultado(ev)
            if hs is None or aws is None:
                contadores["sin_marcador"] += 1
                if debug:
                    log_mensaje(f"  ⚠️  Descartado (Sin Marcador): {home} vs {away} [hs={hs}, aws={aws}]")
                continue

            fecha_real = extrae_fecha(ev)
            gol = f"{int(hs)}-{int(aws)}"

            clave_home = clave_equipo(home)
            clave_away = clave_equipo(away)
            
            if not clave_home or not clave_away:
                if not clave_home and not clave_away:
                    contadores["no_mapeado_ambos"] += 1
                elif not clave_home:
                    contadores["no_mapeado_home"] += 1
                else:
                    contadores["no_mapeado_away"] += 1
                    
                no_mapeados.append(f"{home} vs {away}")
                if debug:
                    log_mensaje(f"  ❌ Descartado (Error Mapeo): '{home}' ({clave_home}) vs '{away}' ({clave_away})")
                continue

            if partido_existe(clave_home, clave_away, fecha_real, gol):
                contadores["ya_existe"] += 1
                if debug:
                    log_mensaje(f"  ✓ Descartado (Ya Registrado): {home} {gol} {away} ({fecha_real})")
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
            log_mensaje(f"  💥 ERROR CRÍTICO procesando evento: {e}")
            import traceback
            log_mensaje(traceback.format_exc())
            continue

    log_mensaje("\n" + "="*50)
    log_mensaje("📊 AUDITORÍA DE EVENTOS DESCARTADOS Y FILTRADOS")
    log_mensaje("="*50)
    log_mensaje(f"  ▶️ Nuevos partidos agregados:     {nuevos}")
    log_mensaje(f"  ⚠️ Saltados por falta de marcador: {contadores['sin_marcador']}")
    log_mensaje(f"  ✓ Saltados porque ya existían:     {contadores['ya_existe']}")
    log_mensaje(f"  ❌ Error mapeo (Local no existe):  {contadores['no_mapeado_home']}")
    log_mensaje(f"  ❌ Error mapeo (Visita no existe): {contadores['no_mapeado_away']}")
    log_mensaje(f"  ❌ Error mapeo (Ninguno existe):   {contadores['no_mapeado_ambos']}")
    log_mensaje(f"  ⚠️ Estructuras rotas/sin equipos:  {contadores['sin_equipos']}")
    log_mensaje(f"  💥 Errores ocultos (Excepciones):  {contadores['con_error']}")
    log_mensaje("="*50)
    
    if no_mapeados:
        log_mensaje(f"\n⚠️  Listado de cadenas de texto no mapeadas ({len(set(no_mapeados))}):")
        for eq in sorted(set(no_mapeados)):
            log_mensaje(f"   - {eq}")
    
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
                    if en_casa != "":
                        gf += gol_local; gc += gol_visitante
                    else:
                        gf += gol_visitante; gc += gol_local
                except: pass
        t.append((eq, pj, g*3 + e, g, e, p, gf, gc))
    t.sort(key=lambda x: (x[2], x[6]-x[7], x[6]), reverse=True)
    return t

def mostrar_clasificacion(tabla):
    """Muestra la clasificación en consola"""
    log_mensaje("\n" + "="*90)
    log_mensaje("CLASIFICACIÓN ACTUAL")
    log_mensaje("="*90)
    log_mensaje(f"{'POS':<4} {'EQUIPO':<25} {'PJ':<4} {'PTS':<4} {'G':<3} {'E':<3} {'P':<3} {'GF':<3} {'GC':<3} {'DG':<4}")
    log_mensaje("-"*90)
    for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(tabla, 1):
        dg = gf - gc
        dg_str = f"+{dg}" if dg > 0 else str(dg)
        eq_name = eq.replace("-", " ").title()
        log_mensaje(f"{i:<4} {eq_name:<25} {pj:<4} {pts:<4} {g:<3} {e:<3} {p:<3} {gf:<3} {gc:<3} {dg_str:<4}")
    log_mensaje("="*90)

def get_logo(eq):
    """Obtiene el logo de un equipo si existe"""
    logos_path = pathlib.Path("logos")
    if not logos_path.exists(): return None
    def normaliza(s): return s.lower().replace("-","").replace("_","").replace(" ","")
    logos = {normaliza(p.stem): p for p in logos_path.glob("*.png")}
    k = normaliza(eq)
    for lk, path in logos.items():
        if k in lk or lk in k: return str(path)
    return None

def generar_pdf():
    """Genera el PDF con la clasificación y fichas de equipos"""
    fecha_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
    hora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y - %H:%M")
    pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"
    
    doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
    
    TABLA = recalcular(PARTIDOS)
    story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
    style_sub = styles['Normal'].clone('subtitulo')
    style_sub.alignment = TA_CENTER; style_sub.fontSize = 13; style_sub.spaceAfter = 10; style_sub.fontName = 'Helvetica-Bold'
    
    J = max(len(v) for v in PARTIDOS.values()) if PARTIDOS.values() else 0
    story.append(Paragraph(f"Clasificacion EN VIVO - Jornada {J}", style_sub))
    story.append(Spacer(1,12))
    
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
        ('ALIGN',(2,1),(2,-1),'LEFT'),
        ('GRID',(0,0),(-1,-1),0.3,colors.black),
        ('FONTSIZE',(0,0),(-1,-1),9)
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
        
        lp = get_logo(eq)
        style_team_big = styles['Normal'].clone(f'team_big_{idx}'); style_team_big.fontSize = 20; style_team_big.fontName = 'Helvetica-Bold'
        style_pj_big = styles['Normal'].clone(f'pj_big_{idx}'); style_pj_big.fontSize = 12; style_pj_big.fontName = 'Helvetica-Bold'
        
        if lp and pathlib.Path(lp).exists():
            logo_img = Image(lp, width=60, height=60)
            header_data = [[logo_img,Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],["",Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
            ht = Table(header_data, colWidths=[70,400])
            ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('SPAN',(0,0),(0,1))]))
        else:
            header_data = [[Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],[Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
            ht = Table(header_data, colWidths=[470])
        
        story.append(ht); story.append(Spacer(1,10))
        cajas_data = [[Paragraph(f"<b>EN CASA:</b> {casa_v}V - {casa_e}E - {casa_d}D",styles['Normal']),Paragraph(f"<b>FUERA:</b> {fuera_v}V - {fuera_e}E - {fuera_d}D",styles['Normal'])]]
        cajas = Table(cajas_data, colWidths=[150,150])
        cajas.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor("#E8F5E9")),('BACKGROUND',(1,0),(1,0),colors.HexColor("#FFEBEE")),('BOX',(0,0),(-1,-1),0.5,colors.black)]))
        story.append(cajas); story.append(Spacer(1,12))
        
        center_style = styles['Normal'].clone(f'centered_{idx}'); center_style.alignment = TA_CENTER
        story.append(Paragraph(f"<b>Partidos J1-{J}</b>",center_style)); story.append(Spacer(1,6))
        
        pd = [["Fecha","EN CASA","R","FUERA","GOL"]]
        for row in PARTIDOS[eq]: pd.append(list(row))
        
        pt = Table(pd, colWidths=[70,170,25,170,40])
        ps = TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.black), ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('ALIGN',(0,0),(-1,-1),'CENTER'), ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,-1),8)
        ])
        
        for ri in range(1,len(pd)):
            res = pd[ri][2]
            if res=='V': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#b6f5b6"))
            elif res=='D': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#ffb3b3"))
            elif res=='E': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#fff2b2"))
        
        pt.setStyle(ps); story.append(pt); story.append(PageBreak())
    
    doc.build(story)
    log_mensaje(f"✅ PDF generado: {pdf_file}")

# MAIN
if __name__ == "__main__":
    log_mensaje("\n" + "=" * 70)
    log_mensaje("🏆 LALIGA HYPERMOTION - ACTUALIZAR CLASIFICACIÓN")
    log_mensaje("=" * 70)
    
    PARTIDOS = cargar_partidos()
    
    nuevos = fetch_toda_jornada(debug=True)
    
    if nuevos > 0:
        guardar_partidos()
        log_mensaje(f"\n✅ {nuevos} partidos nuevos añadidos")
    else:
        log_mensaje("\n✓ Sin cambios en los datos")
    
    TABLA = recalcular(PARTIDOS)
    J = max(len(v) for v in PARTIDOS.values()) if PARTIDOS.values() else 0
    log_mensaje(f"\n📊 Jornadas jugadas: {J}")
    mostrar_clasificacion(TABLA)
    
    log_mensaje("\n📄 Generando informe PDF...")
    generar_pdf()
    
    log_mensaje("\n" + "=" * 70)
    log_mensaje("✅ PROCESO COMPLETADO")
    log_mensaje("=" * 70 + "\n")
