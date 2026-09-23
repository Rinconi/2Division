import pathlib
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

TABLA = [
    ("levante", 79), ("elche", 77), ("oviedo", 75),
    ("mirandes", 75), ("racing-santander", 71), ("almeria", 69),
    ("granada", 65), ("huesca", 64), ("eibar", 58),
    ("albacete", 58), ("sportinggijon", 56), ("burgos", 54),
    ("cadiz", 54), ("cordoba", 53), ("deportivo", 53),
    ("malaga", 53), ("zaragoza", 51), ("castellon", 49),
    ("eldense", 45), ("racing-ferrol", 30), ("tenerife", 23),
    ("cartagena", 23),
]

logos_path = pathlib.Path("logos")
logos_dict = {p.stem.lower(): p for p in logos_path.glob("*.png")}

c = canvas.Canvas("Segunda_Division_24_25.pdf", pagesize=A4)
w,h = A4
c.setFont("Helvetica-Bold", 14)
c.drawCentredString(w/2, h-40, "LaLiga Hypermotion 24/25")
y = h-80

for i,(eq,pts) in enumerate(TABLA,1):
    p = logos_dict.get(eq.lower())
    if p and p.exists():
        try:
            c.drawImage(ImageReader(str(p)), 35, y-3, 14, 14, mask='auto')
        except Exception as e:
            print(f"Error {eq}: {e}")
    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"{i}. {eq} - {pts} pts")
    y -= 20

c.save()
print(f"PDF creado con {len(logos_dict)} logos encontrados")
