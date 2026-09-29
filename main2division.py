import pathlib, json, re
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

PARTIDOS = {}

def log_mensaje(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(msg)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {msg}\n")

def normaliza_nombre(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]',' ',s)
    return s.strip()

def clave_equipo(nombre_espn):
    n = normaliza_nombre(nombre_espn)
    for k, v in MAPEO.items():
        if k in n:
            return v
    return None

def cargar_partidos():
    global PARTIDOS
    # inicializa vacio con todas las claves
    PARTIDOS = {v: [] for v in set(MAPEO.values())}

    if not historial_file.exists():
        log_mensaje("❌ No existe historial")
        return PARTIDOS

    try:
        with open(historial_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # tu archivo es una lista o un dict que contiene una lista
        if isinstance(data, dict):
            # busca la lista dentro: puede estar en "partidos", "historial", etc
            lista = data.get("partidos") or data.get("historial") or data.get("data") or []
            # si el dict es del formato antiguo {equipo: [[...]]} lo detectamos
            if not lista and any(isinstance(v, list) for v in data.values()):
                # es formato antiguo, cargamos tal cual
                PARTIDOS = {k: [tuple(x) for x in v if len(x)==5] for k,v in data.items()}
                log_mensaje(f"✅ Cargado formato antiguo: {len(PARTIDOS)} equipos")
                return PARTIDOS
        else:
            lista = data # es directamente una lista []

        count = 0
        pendientes = 0
        for p in lista:
            if not isinstance(p, dict): continue
            if p.get("estado") == "pendiente":
                pendientes+=1
                continue

            gl = p.get("goles_local")
            gv = p.get("goles_visitante")
            if gl is None or gv is None:
                pendientes+=1
                continue

            fecha = p.get("fecha","2026-09-28")[:10]
            local = p.get("local","")
            visitante = p.get("visitante","")

            kh = clave_equipo(local)
            ka = clave_equipo(visitante)
            if not kh or not ka:
                log_mensaje(f"⚠️ No mapeado: {local} vs {visitante}")
                continue

            gol = f"{int(gl)}-{int(gv)}"
            rh = "V" if int(gl)>int(gv) else "D" if int(gl)<int(gv) else "E"
            ra = "D" if rh=="V" else "V" if rh=="D" else "E"
            texto = f"{local} {gol} {visitante}"

            # evitar duplicados
            if any(x[0]==fecha and x[4]==gol for x in PARTIDOS.get(kh,[])):
                continue

            PARTIDOS[kh].append((fecha, texto, rh, "", gol))
            PARTIDOS[ka].append((fecha, "", ra, texto, gol))
            count+=1

        log_mensaje(f"✅ Cargados {count} partidos finalizados desde JSON ({pendientes} pendientes ignorados)")
        return PARTIDOS

    except Exception as e:
        log_mensaje(f"❌ Error cargando JSON nuevo formato: {e}")
        import traceback
        log_mensaje(traceback.format_exc())
        return PARTIDOS

def recalcular(d):
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
                    gl, gv = map(int, gol.split("-"))
                    es_local = (en_casa!= "")
                    if es_local: gf+=gl; gc+=gv
                    else: gf+=gv; gc+=gl
                except: pass
        t.append((eq, pj, g*3 + e, g, e, p, gf, gc))
    t.sort(key=lambda x: (x[2], x[6]-x[7], x[6]), reverse=True)
    return t

def mostrar_clasificacion(tabla):
    log_mensaje("\n" + "="*90)
    log_mensaje("CLASIFICACIÓN ACTUAL")
    log_mensaje("="*90)
    for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(tabla, 1):
        log_mensaje(f"{i} {eq} {pj} {pts}")

def get_logo(eq):
    logos_path = pathlib.Path("logos")
    if not logos_path.exists(): return None
    def normaliza(s): return s.lower().replace("-","").replace("_","").replace(" ","")
    logos = {normaliza(p.stem): p for p in logos_path.glob("*.png")}
    k = normaliza(eq)
    for lk, path in logos.items():
        if k in lk or lk in k: return str(path)
    return None

def generar_pdf():
    fecha_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
    hora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y - %H:%M")
    pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"
    doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
    TABLA = recalcular(PARTIDOS)
    story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
    style_sub = styles['Normal'].clone('subtitulo')
    style_sub.alignment = TA_CENTER
    style_sub.fontSize = 13
    style_sub.spaceAfter = 10
    style_sub.fontName = 'Helvetica-Bold'
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
    st = TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1B3B29")),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ALIGN',(0,0),(-1,-1),'CENTER'),('ALIGN',(2,1),(2,-1),'LEFT'),('GRID',(0,0),(-1,-1),0.3,colors.black),('FONTSIZE',(0,0),(-1,-1),9)])
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
        style_team_big = styles['Normal'].clone(f'team_big_{idx}')
        style_team_big.fontSize = 20
        style_team_big.fontName = 'Helvetica-Bold'
        style_pj_big = styles['Normal'].clone(f'pj_big_{idx}')
        style_pj_big.fontSize = 12
        style_pj_big.fontName = 'Helvetica-Bold'
        if lp and pathlib.Path(lp).exists():
            logo_img = Image(lp, width=60, height=60)
            header_data = [[logo_img,Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],["",Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
            ht = Table(header_data, colWidths=[70,400])
            ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('SPAN',(0,0),(0,1))]))
        else:
            header_data = [[Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",style_team_big)],[Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",style_pj_big)]]
            ht = Table(header_data, colWidths=[470])
        story.append(ht)
        story.append(Spacer(1,10))
        cajas_data = [[Paragraph(f"<b>EN CASA:</b> {casa_v}V - {casa_e}E - {casa_d}D",styles['Normal']),Paragraph(f"<b>FUERA:</b> {fuera_v}V - {fuera_e}E - {fuera_d}D",styles['Normal'])]]
        cajas = Table(cajas_data, colWidths=[150,150])
        cajas.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor("#E8F5E9")),('BACKGROUND',(1,0),(1,0),colors.HexColor("#FFEBEE")),('BOX',(0,0),(-1,-1),0.5,colors.black)]))
        story.append(cajas)
        story.append(Spacer(1,12))
        center_style = styles['Normal'].clone(f'centered_{idx}')
        center_style.alignment = TA_CENTER
        story.append(Paragraph(f"<b>Partidos J1-{J}</b>",center_style))
        story.append(Spacer(1,6))
        pd = [["Fecha","EN CASA","R","FUERA","GOL"]]
        for row in PARTIDOS[eq]: pd.append(list(row))
        pt = Table(pd, colWidths=[70,170,25,170,40])
        ps = TableStyle([('BACKGROUND',(0,0),(-1,0),colors.black),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8)])
        for ri in range(1,len(pd)):
            res = pd[ri][2]
            if res=='V': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#b6f5b6"))
            elif res=='D': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#ffb3b3"))
            elif res=='E': ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#fff2b2"))
        pt.setStyle(ps)
        story.append(pt)
        story.append(PageBreak())
    doc.build(story)
    log_mensaje(f"✅ PDF generado: {pdf_file}")

# MAIN - AHORA 100% JSON
if __name__ == "__main__":
    log_mensaje("\n" + "=" * 70)
    log_mensaje("🏆 LALIGA HYPERMOTION - MODO JSON")
    log_mensaje("=" * 70)
    PARTIDOS = cargar_partidos()
    TABLA = recalcular(PARTIDOS)
    J = max(len(v) for v in PARTIDOS.values()) if PARTIDOS.values() else 0
    log_mensaje(f"\n📊 Jornadas jugadas: {J}")
    mostrar_clasificacion(TABLA)
    log_mensaje("\n📄 Generando informe PDF...")
    generar_pdf()
    log_mensaje("\n✅ PROCESO COMPLETADO - SIN APIS\n")
