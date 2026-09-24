import pathlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

TABLA = [
    ("levante", 42, 79, 22, 13, 7, 69, 42),
    ("elche", 42, 77, 21, 14, 7, 59, 34),
    ("oviedo", 42, 75, 21, 12, 9, 56, 39),
    ("mirandes", 42, 75, 22, 9, 11, 59, 40),
    ("racing-santander", 42, 71, 20, 11, 11, 65, 51),
    ("almeria", 42, 69, 19, 12, 11, 72, 55),
    ("granada", 42, 65, 18, 11, 13, 69, 54),
    ("huesca", 42, 64, 18, 10, 14, 58, 49),
    ("eibar", 42, 58, 15, 13, 14, 44, 41),
    ("albacete", 42, 58, 15, 13, 14, 57, 67),
    ("sportinggijon", 42, 56, 14, 14, 14, 57, 54),
    ("burgos", 42, 54, 15, 9, 18, 41, 48),
    ("cadiz", 42, 54, 14, 12, 16, 39, 45),
    ("cordoba", 42, 53, 14, 11, 17, 59, 63),
    ("deportivo", 42, 53, 13, 14, 15, 56, 54),
    ("malaga", 42, 53, 12, 17, 13, 42, 46),
    ("zaragoza", 42, 51, 13, 12, 17, 56, 63),
    ("castellon", 42, 49, 14, 7, 21, 65, 63),
    ("eldense", 42, 45, 11, 12, 19, 44, 63),
    ("racing-ferrol", 42, 30, 6, 12, 24, 22, 64),
    ("tenerife", 42, 23, 5, 8, 29, 30, 63),
    ("cartagena", 42, 23, 5, 8, 29, 33, 78),
]

def normaliza(s): return s.lower().replace("-","").replace("_","").replace(" ","")
logos_path = pathlib.Path("logos")
logos = {normaliza(p.stem): p for p in logos_path.glob("*.png")}
def get_logo(eq):
    k = normaliza(eq)
    for lk, path in logos.items():
        if k in lk or lk in k:
            return str(path)
    return None

# Crea carpeta informes/
out_dir = pathlib.Path("informes")
out_dir.mkdir(exist_ok=True)
fecha_str = datetime.now().strftime("%Y-%m-%d")
hora_str = datetime.now().strftime("%d/%m/%Y %H:%M")
pdf_file = out_dir / f"Informe_LaLiga_Hypermotion_{fecha_str}.pdf"

doc = SimpleDocTemplate(str(pdf_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
styles = getSampleStyleSheet()
story = []
story.append(Paragraph(f"<b>LaLiga Hypermotion - {hora_str}</b>", styles['Title']))
story.append(Paragraph("Jornada 42 - Clasificacion Final 24/25", styles['Normal']))
story.append(Spacer(1, 12))

data = [["#", "", "Equipo", "PJ", "PTS", "G", "E", "P", "GF", "GC", "DG"]]
for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(TABLA, 1):
    dg = gf-gc
    dg_str = f"+{dg}" if dg>0 else str(dg)
    logo_path = get_logo(eq)
    if logo_path:
        img = Image(logo_path, width=14, height=14)
    else:
        img = ""
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
for r in range(1, 3): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#e8c4e8"))
for r in range(3, 7): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#fff2b2"))
for r in range(19, 23): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#ffb3b3"))
style.add('FONTNAME', (4,1), (4,-1), 'Helvetica-Bold')
table.setStyle(style)
story.append(table)
story.append(Spacer(1, 14))

# LEYENDA
story.append(Paragraph("<b>Leyenda:</b>", styles['Normal']))
leyenda_data = [
    [Paragraph('<font color="#e8a0e8">■</font> Ascenso directo a LaLiga EA Sports', styles['Normal'])],
    [Paragraph('<font color="#e6d27a">■</font> Playoff de ascenso', styles['Normal'])],
    [Paragraph('<font color="#ff8a8a">■</font> Descenso a Primera RFEF', styles['Normal'])],
]
leyenda_table = Table(leyenda_data, colWidths=[300])
leyenda_table.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
story.append(leyenda_table)

doc.build(story)
print(f"PDF creado en {pdf_file}")
