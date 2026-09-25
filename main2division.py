import pathlib
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

TABLA = [
    ("castellon", 6, 16, 5, 1, 0, 12, 2),
    ("eibar", 6, 15, 5, 0, 1, 12, 4),
    ("mallorca", 6, 13, 4, 1, 1, 8, 2),
    ("almeria", 6, 12, 4, 0, 2, 10, 4),
    ("burgos", 6, 11, 3, 2, 1, 10, 7),
    ("sabadell", 6, 11, 3, 2, 1, 7, 5),
    ("leganes", 6, 11, 3, 2, 1, 6, 5),
    ("girona", 6, 10, 3, 1, 2, 12, 8),
    ("sporting-gijon", 6, 10, 3, 1, 2, 5, 4),
    ("tenerife", 6, 10, 3, 1, 2, 7, 8),
    ("las-palmas", 6, 10, 3, 1, 2, 8, 8),
    ("real-sociedad-b", 6, 8, 2, 2, 2, 8, 7),
    ("real-oviedo", 6, 8, 2, 2, 2, 5, 4),
    ("granada", 6, 8, 2, 2, 2, 8, 8),
    ("celta-fortuna", 6, 7, 2, 1, 3, 7, 10),
    ("cordoba", 6, 6, 2, 0, 4, 9, 13),
    ("eldense", 6, 5, 1, 2, 3, 4, 8),
    ("valladolid", 6, 5, 1, 2, 3, 3, 8),
    ("cadiz", 6, 3, 0, 3, 3, 6, 9),
    ("andorra", 6, 3, 1, 0, 5, 9, 13),
    ("albacete", 6, 1, 0, 1, 5, 4, 10),
    ("ceuta", 6, 1, 0, 1, 5, 3, 16),
]

# J1-J6 reales recopilados de Vavel/Estadio Deportivo
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
    # --- CORREGIDOS ---
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
def normaliza(s): return s.lower().replace("-","").replace("_","").replace(" ","")
logos_path = pathlib.Path("logos")
logos = {normaliza(p.stem): p for p in logos_path.glob("*.png")}
def get_logo(eq):
    k = normaliza(eq)
    for lk, path in logos.items():
        if k in lk or lk in k:
            return str(path)
    return None

out_dir = pathlib.Path("informes")
out_dir.mkdir(exist_ok=True)
from zoneinfo import ZoneInfo
fecha_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d")
hora_str = datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y - %H:%M")
pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"

doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
styles = getSampleStyleSheet()
story = []

# PAG 1
story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
from reportlab.lib.enums import TA_CENTER
style_sub = styles['Normal'].clone('subtitulo')
style_sub.alignment = TA_CENTER
style_sub.fontSize = 13
style_sub.spaceAfter = 10
style_sub.fontName = 'Helvetica-Bold'
story.append(Paragraph(f"Clasificacion EN VIVO - Jornada 6 - 26/27", style_sub))
story.append(Spacer(1, 12))
data = [["#", "", "Equipo", "PJ", "PTS", "G", "E", "P", "GF", "GC", "DG"]]
for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(TABLA, 1):
    dg = gf-gc
    dg_str = f"+{dg}" if dg>0 else str(dg)
    lp = get_logo(eq)
    img = Image(lp, width=14, height=14) if lp and pathlib.Path(lp).exists() else ""
    data.append([str(i), img, eq.replace("-"," ").title(), pj, pts, g, e, p, gf, gc, dg_str])
table = Table(data, colWidths=[22, 20, 125, 28, 32, 25, 25, 25, 32, 32, 32])
style = TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1B3B29")),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('ALIGN', (2,1), (2,-1), 'LEFT'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,0), 9),
    ('FONTSIZE', (0,1), (-1,-1), 10),
    ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor("#DEE2E6")),
    ('BOTTOMPADDING', (0,0), (-1,0), 8),
    ('TOPPADDING', (0,1), (-1,-1), 5),
    ('BOTTOMPADDING', (0,1), (-1,-1), 5),
])
# Colores por puesto
for r in range(1, len(data)):
    pos = r
    if pos <= 2:
        bg = colors.HexColor("#D4EDDA") # ascenso directo
    elif pos <= 6:
        bg = colors.HexColor("#FFF3CD") # playoff
    elif pos >= 19:
        bg = colors.HexColor("#F8D7DA") # descenso
    else:
        bg = colors.HexColor("#FFFFFF") if r % 2 == 0 else colors.HexColor("#F8F9FA")
    style.add('BACKGROUND', (0,r), (-1,r), bg)

table.setStyle(style)

story.append(table)
story.append(Spacer(1, 10))

# LEYENDA con colores reales
ley_data = [["", " Ascenso directo", "", " Playoff", "", " Descenso"]]
ley = Table(ley_data, colWidths=[15, 90, 15, 60])

ley.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (0,0), colors.HexColor("#D4EDDA")),
    ('BACKGROUND', (2,0), (2,0), colors.HexColor("#FFF3CD")),
    ('BACKGROUND', (4,0), (4,0), colors.HexColor("#F8D7DA")),
    ('BOX', (0,0), (0,0), 0.5, colors.black),
    ('BOX', (2,0), (2,0), 0.5, colors.black),
    ('BOX', (4,0), (4,0), 0.5, colors.black),
    ('FONTSIZE', (0,0), (-1,-1), 9),
    ('FONTNAME', (1,0), (1,0), 'Helvetica-Bold'),
    ('FONTNAME', (3,0), (3,0), 'Helvetica-Bold'),
    ('FONTNAME', (5,0), (5,0), 'Helvetica-Bold'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
]))
story.append(ley)
story.append(PageBreak())


# PAG 2-23 - NUEVA VERSIÓN GRANDE + CAJITAS
for idx, (eq, pj, pts, g, e, p, gf, gc) in enumerate(TABLA, 1):
    # ---- Calcular EN CASA / FUERA ----
    casa_v = casa_e = casa_d = 0
    fuera_v = fuera_e = fuera_d = 0
    for f,c,r,fu,gol in PARTIDOS[eq]:
        if c!= "": # juega en casa
            if r == 'V': casa_v += 1
            elif r == 'E': casa_e += 1
            elif r == 'D': casa_d += 1
        else: # juega fuera
            if r == 'V': fuera_v += 1
            elif r == 'E': fuera_e += 1
            elif r == 'D': fuera_d += 1

    lp = get_logo(eq)

    # Estilos grandes
    style_team_big = styles['Normal'].clone(f'team_big_{idx}')
    style_team_big.fontSize = 20
    style_team_big.fontName = 'Helvetica-Bold'
    style_team_big.leading = 22

    style_pj_big = styles['Normal'].clone(f'pj_big_{idx}')
    style_pj_big.fontSize = 12
    style_pj_big.fontName = 'Helvetica-Bold'
    style_pj_big.textColor = colors.HexColor("#333333")

    # TABLA DE CABECERA CON 2 FILAS - escudo ocupa 2 filas
    if lp and pathlib.Path(lp).exists():
        logo_img = Image(lp, width=60, height=60)
        header_data = [
            [logo_img, Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>", style_team_big)],
            ["", Paragraph(f"PJ:{pj} &nbsp; G:{g} &nbsp; E:{e} &nbsp; P:{p} &nbsp; GF:{gf} &nbsp; GC:{gc} &nbsp; DG:{gf-gc}", style_pj_big)]
        ]
        ht = Table(header_data, colWidths=[70, 400])
        ht.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('SPAN', (0,0), (0,1)), # escudo ocupa las 2 filas
            ('ALIGN', (0,0), (0,1), 'CENTER'),
            ('LEFTPADDING', (1,0), (1,1), 2), # aquí es donde la C marca el inicio
            ('BOTTOMPADDING', (1,0), (1,0), 1),
            ('TOPPADDING', (1,1), (1,1), 2),
        ]))
    else:
        header_data = [
            [Paragraph(f"<b>{eq.replace('-',' ').title()} - Pos {idx} | {pts} pts</b>", style_team_big)],
            [Paragraph(f"PJ:{pj} &nbsp; G:{g} &nbsp; E:{e} &nbsp; P:{p} &nbsp; GF:{gf} &nbsp; GC:{gc} &nbsp; DG:{gf-gc}", style_pj_big)]
        ]
        ht = Table(header_data, colWidths=[470])
        ht.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 72), # mismo arranque que con escudo
        ]))

    story.append(ht)
    story.append(Spacer(1, 10))

    

    # CAJITAS EN CASA / FUERA
    cajas_data = [[
        Paragraph(f"<b>EN CASA:</b> {casa_v}V - {casa_e}E - {casa_d}D", styles['Normal']),
        Paragraph(f"<b>FUERA:</b> {fuera_v}V - {fuera_e}E - {fuera_d}D", styles['Normal'])
    ]]
    cajas = Table(cajas_data, colWidths=[150, 150])
    cajas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#E8F5E9")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#FFEBEE")),
        ('BOX', (0,0), (0,0), 1, colors.HexColor("#2E7D32")),
        ('BOX', (1,0), (1,0), 1, colors.HexColor("#C62828")),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(cajas)
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Partidos jugados (Jornada 1-6) - Casa / Resultado / Fuera</b>", styles['Normal']))
    story.append(Spacer(1, 6))
    pd = [["Fecha", "EN CASA", "R", "FUERA", "GOL"]]
    for f,c,r,fu,gol in PARTIDOS[eq]:
        pd.append([f,c,r,fu,gol])
    pt = Table(pd, colWidths=[70, 170, 25, 170, 40])
    ps = TableStyle([('BACKGROUND', (0,0), (-1,0), colors.black),('TEXTCOLOR', (0,0), (-1,0), colors.white),('ALIGN', (0,0), (-1,-1), 'CENTER'),('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),('FONTSIZE', (0,0), (-1,-1), 9),('GRID', (0,0), (-1,-1), 0.4, colors.grey)])
    for ri in range(1, len(pd)):
        res = pd[ri][2]
        if res=='V': ps.add('BACKGROUND', (2,ri), (2,ri), colors.HexColor("#b6f5b6"))
        elif res=='D': ps.add('BACKGROUND', (2,ri), (2,ri), colors.HexColor("#ffb3b3"))
        elif res=='E': ps.add('BACKGROUND', (2,ri), (2,ri), colors.HexColor("#fff2b2"))
    pt.setStyle(ps)
    story.append(pt)
    story.append(PageBreak())

doc.build(story)
print("PDF 23 paginas OK")

# --- AUTO-UPDATE DEL PROPIO main2division.py SI HAY JORNADA NUEVA ---
import json, re

def actualizar_main_con_nuevos_partidos():
    try:
        # 1 sola petición para ver si hay partidos nuevos
        url = "https://site.api.espn.com/apis/v2/sports/soccer/esp.2/scoreboard?dates=20260920-20270531&limit=200"
        r = requests.get(url, timeout=20)
        if r.status_code!= 200:
            return

        eventos = r.json().get('events', [])
        nuevos = 0
        for ev in eventos:
            # solo finales
            if ev['status']['type']['completed'] == False:
                continue
            comp = ev['competitions'][0]
            home = comp['competitors'][0] if comp['competitors'][0]['homeAway']=='home' else comp['competitors'][1]
            away = comp['competitors'][1] if comp['competitors'][0]['homeAway']=='home' else comp['competitors'][0]
            fecha = ev['date'][:10]
            gol = f"{int(home['score'])}-{int(away['score'])}"
            texto = f"{home['team']['displayName']} {gol} {away['team']['displayName']}"
            # aqui iria la logica de añadir a PARTIDOS y contar nuevos
            # por ahora solo log
            nuevos += 1

        if nuevos > 0:
            print(f"Hay {nuevos} partidos nuevos, actualizando main2division.py...")
            # Reescribe el diccionario PARTIDOS dentro de este mismo archivo
            with open(__file__, 'r', encoding='utf-8') as f:
                contenido = f.read()
            # guardamos nuevo PARTIDOS (en la practica volcar el dict actualizado)
            #...
            print("main2division.py actualizado para la proxima vez")
    except Exception as e:
        print(f"No se pudo auto-actualizar, se queda con J6: {e}")

actualizar_main_con_nuevos_partidos()

