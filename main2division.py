import pathlib, json, re
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

out_dir = pathlib.Path("informes")
historial_file = out_dir / "historial_hypermotion.json"
log_file = out_dir / "ejecuciones.log"

MAPEO = {
    "ceuta":"ceuta","ad ceuta":"ceuta","ad ceuta fc":"ceuta",
    "castellon":"castellon","cd castellon":"castellon","castellon":"castellon",
    "eibar":"eibar","sd eibar":"eibar",
    "mallorca":"mallorca","real mallorca":"mallorca","rcd mallorca":"mallorca",
    "almeria":"almeria","ud almeria":"almeria","almeria":"almeria",
    "burgos":"burgos","cf burgos":"burgos","burgos cf":"burgos",
    "sabadell":"sabadell","ce sabadell":"sabadell","ce sabadell fc":"sabadell",
    "leganes":"leganes","cd leganes":"leganes","leganes":"leganes",
    "girona":"girona","girona fc":"girona",
    "sporting":"sporting-gijon","sporting gijon":"sporting-gijon","real sporting":"sporting-gijon","real sporting de gijon":"sporting-gijon",
    "tenerife":"tenerife","cd tenerife":"tenerife",
    "las palmas":"las-palmas","ud las palmas":"las-palmas",
    "real sociedad":"real-sociedad-b","real sociedad b":"real-sociedad-b",
    "real oviedo":"real-oviedo","oviedo":"real-oviedo",
    "granada":"granada","granada cf":"granada",
    "celta":"celta-fortuna","celta fortuna":"celta-fortuna",
    "cordoba":"cordoba","cordoba":"cordoba",
    "eldense":"eldense","cf eldense":"eldense","cd eldense":"eldense",
    "valladolid":"valladolid","real valladolid":"valladolid",
    "cadiz":"cadiz","cadiz":"cadiz",
    "andorra":"andorra","fc andorra":"andorra",
    "albacete":"albacete",
}

PARTIDOS = {}

def log_mensaje(m):
    print(m)
    with open(log_file,'a',encoding='utf-8') as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {m}\n")

def normaliza(s):
    s = s.lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]',' ',s)
    return s.strip()

def clave_equipo(nombre):
    n = normaliza(nombre)
    for k in sorted(MAPEO.keys(), key=len, reverse=True):
        if k in n:
            return MAPEO[k]
    return None

def cargar_partidos():
    global PARTIDOS
    PARTIDOS = {v: [] for v in set(MAPEO.values())}
    with open(historial_file,'r',encoding='utf-8') as f:
        root = json.load(f)
    jornadas = root.get("jornadas", [])
    total_en_json = 0
    cargados = 0
    for j in jornadas:
        for p in j.get("partidos", []):
            total_en_json += 1
            gl = p.get("goles_local")
            gv = p.get("goles_visitante")
            if gl is None or gv is None:
                continue
            if p.get("estado")!= "finalizado":
                continue
            fecha = str(p.get("fecha","2026-09-28"))[:10]
            local = p.get("local","")
            visitante = p.get("visitante","")
            kh = clave_equipo(local)
            ka = clave_equipo(visitante)
            if not kh or not ka:
                continue
            gol = f"{int(gl)}-{int(gv)}"
            if any(x[0]==fecha and x[4]==gol for x in PARTIDOS[kh]):
                continue
            rh = "V" if gl>gv else "D" if gl<gv else "E"
            ra = "D" if rh=="V" else "V" if rh=="D" else "E"
            texto = f"{local} {gol} {visitante}"
            PARTIDOS[kh].append((fecha, texto, rh, "", gol))
            PARTIDOS[ka].append((fecha, "", ra, texto, gol))
            cargados += 1
    log_mensaje(f"JSON: {len(jornadas)} jornadas, {total_en_json} registros, {cargados} finalizados")
    return PARTIDOS

def recalcular(d):
    t = []
    for eq, lista in d.items():
        if not lista:
            continue
        pj = len(lista)
        g = 0
        e = 0
        p = 0
        for _, _, r, _, _ in lista:
            if r == 'V':
                g += 1
            elif r == 'E':
                e += 1
            elif r == 'D':
                p += 1
        gf = 0
        gc = 0
        for _, en_casa, _, _, gol in lista:
            try:
                gl, gv = map(int, gol.split("-"))
                if en_casa!= "":
                    gf += gl
                    gc += gv
                else:
                    gf += gv
                    gc += gl
            except:
                pass
        t.append((eq, pj, g*3+e, g, e, p, gf, gc))
    t.sort(key=lambda x: (x[2], x[6]-x[7], x[6]), reverse=True)
    return t

def get_logo(eq):
    p = pathlib.Path("logos")
    if not p.exists():
        return None
    def norm(s):
        return s.lower().replace("-","").replace("_","").replace(" ","")
    logos = {norm(x.stem): x for x in p.glob("*.png")}
    k = norm(eq)
    for lk, path in logos.items():
        if k in lk or lk in k:
            return str(path)
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
    st_sub = styles['Normal'].clone('sub')
    st_sub.alignment = TA_CENTER
    st_sub.fontSize = 13
    st_sub.fontName = 'Helvetica-Bold'
    st_sub.spaceAfter = 10
    J = max(len(v) for v in PARTIDOS.values()) if any(PARTIDOS.values()) else 0
    story.append(Paragraph(f"Clasificacion EN VIVO - Jornada {J}", st_sub))
    story.append(Spacer(1,12))
    data = [["#","","Equipo","PJ","PTS","G","E","P","GF","GC","DG"]]
    for i,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
        dg = gf-gc
        dg_str = f"+{dg}" if dg>0 else str(dg)
        lp = get_logo(eq)
        img = Image(lp,14,14) if lp and pathlib.Path(lp).exists() else ""
        data.append([str(i),img,eq.replace("-"," ").title(),str(pj),str(pts),str(g),str(e),str(p),str(gf),str(gc),dg_str])
    table = Table(data,colWidths=[22,20,125,28,32,25,25,25,32,32,32])
    st = TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1B3B29")),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ALIGN',(0,0),(-1,-1),'CENTER'),('ALIGN',(2,1),(2,-1),'LEFT'),('GRID',(0,0),(-1,-1),0.3,colors.black),('FONTSIZE',(0,0),(-1,-1),9)])
    for r in range(1,len(data)):
        if r <= 2:
            bg = colors.HexColor("#D4EDDA")
        elif r <= 6:
            bg = colors.HexColor("#FFF3CD")
        elif r >= 19:
            bg = colors.HexColor("#F8D7DA")
        elif r % 2 == 0:
            bg = colors.HexColor("#FFFFFF")
        else:
            bg = colors.HexColor("#F8F9FA")
        st.add('BACKGROUND',(0,r),(-1,r),bg)
    table.setStyle(st)
    story.append(table)
    story.append(PageBreak())
    for idx,(eq,pj,pts,g,e,p,gf,gc) in enumerate(TABLA,1):
        casa_v = 0; casa_e = 0; casa_d = 0; fuera_v = 0; fuera_e = 0; fuera_d = 0
        for _,c,r,_,_ in PARTIDOS[eq]:
            if c!= "":
                if r == 'V': casa_v+=1
                elif r == 'E': casa_e+=1
                else: casa_d+=1
            else:
                if r == 'V': fuera_v+=1
                elif r == 'E': fuera_e+=1
                else: fuera_d+=1
        lp = get_logo(eq)
        st_big = styles['Normal'].clone(f'b{idx}'); st_big.fontSize=20; st_big.fontName='Helvetica-Bold'
        st_pj = styles['Normal'].clone(f'p{idx}'); st_pj.fontSize=12; st_pj.fontName='Helvetica-Bold'
        if lp and pathlib.Path(lp).exists():
            hdr = [[Image(lp,60,60),Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",st_big)],["",Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",st_pj)]]
            ht = Table(hdr,colWidths=[70,400])
            ht.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('SPAN',(0,0),(0,1))]))
        else:
            hdr = [[Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>",st_big)],[Paragraph(f"PJ:{pj} G:{g} E:{e} P:{p} GF:{gf} GC:{gc} DG:{gf-gc}",st_pj)]]
            ht = Table(hdr,colWidths=[470])
        story.append(ht); story.append(Spacer(1,10))
        cajas = [[Paragraph(f"<b>EN CASA:</b> {casa_v}V - {casa_e}E - {casa_d}D",styles['Normal']),Paragraph(f"<b>FUERA:</b> {fuera_v}V - {fuera_e}E - {fuera_d}D",styles['Normal'])]]
        cb = Table(cajas,colWidths=[150,150])
        cb.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),colors.HexColor("#E8F5E9")),('BACKGROUND',(1,0),(1,0),colors.HexColor("#FFEBEE")),('BOX',(0,0),(-1,-1),0.5,colors.black)]))
        story.append(cb); story.append(Spacer(1,12))
        cs = styles['Normal'].clone(f'c{idx}'); cs.alignment=TA_CENTER
        story.append(Paragraph(f"<b>Partidos J1-{J}</b>",cs)); story.append(Spacer(1,6))
        pd = [["Fecha","EN CASA","R","FUERA","GOL"]]
        for row in PARTIDOS[eq]:
            pd.append(list(row))
        pt = Table(pd,colWidths=[70,170,25,170,40])
        ps = TableStyle([('BACKGROUND',(0,0),(-1,0),colors.black),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8)])
        for ri in range(1,len(pd)):
            res = pd[ri][2]
            if res == 'V':
                ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#b6f5b6"))
            elif res == 'D':
                ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#ffb3b3"))
            elif res == 'E':
                ps.add('BACKGROUND',(2,ri),(2,ri),colors.HexColor("#fff2b2"))
        pt.setStyle(ps); story.append(pt); story.append(PageBreak())
    doc.build(story)
    log_mensaje(f"PDF generado: {pdf_file}")

if __name__=="__main__":
    log_mensaje("="*70)
    cargar_partidos()
    generar_pdf()
    log_mensaje("COMPLETADO")
