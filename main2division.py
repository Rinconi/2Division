import pathlib, requests
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

def get_live_table():
    url = "https://site.api.espn.com/apis/v2/sports/soccer/esp.2/standings?season=2025"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        entries = data['children'][0]['standings']['entries']
        tabla = []
        for e in entries:
            team = e['team']
            name = team['displayName']
            # stats: W D L PTS GF GC etc
            stats = {s['name']: s['value'] for s in e['stats']}
            # normalizamos nombre para tu carpeta logos
            key = name.lower().replace(" ","-")
            tabla.append((
                key,
                int(stats.get('gamesPlayed',0)),
                int(stats.get('points',0)),
                int(stats.get('wins',0)),
                int(stats.get('ties',0)),
                int(stats.get('losses',0)),
                int(stats.get('pointsFor',0)),
                int(stats.get('pointsAgainst',0))
            ))
        print(f"Datos en vivo obtenidos: {len(tabla)} equipos")
        return tabla
    except Exception as ex:
        print(f"Fallo API, usando datos de respaldo: {ex}")
        # respaldo por si cae ESPN
        return [
            ("racing-santander", 6, 16, 5,1,0,12,2),
            ("eibar", 6, 15, 5,0,1,12,4),
        ]

TABLA = get_live_table()

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
fecha_str = datetime.now().strftime("%Y-%m-%d")
hora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"

doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
styles = getSampleStyleSheet()
story = []
story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
story.append(Paragraph(f"Clasificacion EN VIVO - Jornada actual 25/26", styles['Normal']))
story.append(Spacer(1, 12))

data = [["#", "", "Equipo", "PJ", "PTS", "G", "E", "P", "GF", "GC", "DG"]]
for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(TABLA, 1):
    dg = gf-gc
    dg_str = f"+{dg}" if dg>0 else str(dg)
    logo_path = get_logo(eq)
    img = Image(logo_path, width=14, height=14) if logo_path and pathlib.Path(logo_path).exists() else ""
    nombre = eq.replace("-"," ").title()
    data.append([str(i), img, nombre, pj, pts, g, e, p, gf, gc, dg_str])

table = Table(data, colWidths=[22, 20, 125, 28, 32, 25, 25, 25, 32, 32, 32])
style = TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.black),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('ALIGN', (2,1), (2,-1), 'LEFT'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,0), 9),
    ('FONTSIZE', (0,1), (-1,-1), 8),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f9f9f9")]),
])
# Colores como ayer
if len(data) > 3:
    for r in range(1, 3): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#e8c4e8"))
    for r in range(3, 7): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#fff2b2"))
    for r in range(len(data)-3, len(data)): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#ffb3b3"))
style.add('FONTNAME', (4,1), (4,-1), 'Helvetica-Bold')
table.setStyle(style)
story.append(table)
story.append(Spacer(1, 14))
story.append(Paragraph("<b>Leyenda:</b>", styles['Normal']))
leyenda = [
    [Paragraph('<font color="#e8a0e8">■</font> Ascenso directo a LaLiga EA Sports', styles['Normal'])],
    [Paragraph('<font color="#e6d27a">■</font> Playoff de ascenso', styles['Normal'])],
    [Paragraph('<font color="#ff8a8a">■</font> Descenso a Primera RFEF', styles['Normal'])],
]
lt = Table(leyenda, colWidths=[300])
lt.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 8)]))
story.append(lt)
doc.build(story)
print(f"PDF creado en {pdf_file}")
