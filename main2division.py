import pathlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --- DATOS 24/25 FINAL - puedes cambiar los numeros, el formato se queda igual que 1ª ---
# (PJ, PTS, G, E, P, GF, GC) - DG se calcula
TABLA_24_25 = [
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

def get_logo_path(equipo_key):
    k = normaliza(equipo_key)
    for lk, path in logos.items():
        if k in lk or lk in k:
            return str(path)
    return None

# Documento
fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
pdf_file = f"Informe_LaLiga_Hypermotion_{datetime.now().strftime('%Y-%m-%d')}.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
styles = getSampleStyleSheet()
story = []
story.append(Paragraph(f"<b>LaLiga Hypermotion - {fecha}</b>", styles['Title']))
story.append(Paragraph("Jornada 42 - Clasificacion Final 24/25", styles['Normal']))
story.append(Spacer(1, 12))

# Cabecera igual que 1ª
data = [["#", "", "Equipo", "PJ", "PTS", "G", "E", "P", "GF", "GC", "DG"]]

for i, (eq, pj, pts, g, e, p, gf, gc) in enumerate(TABLA_24_25, 1):
    dg = gf-gc
    dg_str = f"+{dg}" if dg>0 else str(dg)
    # logo como texto para que lo pintemos luego, pero metemos placeholder
    data.append([str(i), eq, eq.replace("-"," ").title(), pj, pts, g, e, p, gf, gc, dg_str])

# Estilo tabla identico a tu foto de 1ª
table = Table(data, colWidths=[25, 25, 130, 28, 32, 25, 25, 25, 32, 32, 32])
style = TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.black),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('ALIGN', (2,1), (2,-1), 'LEFT'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,0), 9),
    ('FONTSIZE', (0,1), (-1,-1), 8),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke]),
])
# Colores como en 1ª: 1-2 ascenso directo (rosa), 3-6 playoff (amarillo claro), 19-22 descenso (rojo claro)
for r in range(1, 3): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#e8c4e8"))
for r in range(3, 7): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#fff2b2"))
for r in range(19, 23): style.add('BACKGROUND', (0,r), (-1,r), colors.HexColor("#ffb3b3"))
style.add('FONTNAME', (4,1), (4,-1), 'Helvetica-Bold') # PTS en negrita

table.setStyle(style)
story.append(table)

# Ahora dibujamos los escudos encima de la columna 1 (truco igual que en 1ª)
def draw_logos(canvas, doc):
    canvas.saveState()
    # posicion de la tabla
    y_start = 580
    # pintamos logo por logo
    for idx, (eq, *_) in enumerate(TABLA_24_25):
        logo_path = get_logo_path(eq)
        if logo_path:
            y = y_start - (idx*18.2)
            try:
                canvas.drawImage(ImageReader(logo_path), 56, y-2, 12, 12, mask='auto')
            except: pass
    canvas.restoreState()

doc.build(story, onFirstPage=draw_logos, onLaterPages=draw_logos)
print(f"PDF creado: {pdf_file}")
