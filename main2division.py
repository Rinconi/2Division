import pathlib, glob
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# TABLA REAL 24/25 - 22 equipos
TABLA = [
    ("Levante UD", 79), ("Elche CF", 77), ("Real Oviedo", 75),
    ("Mirandés", 75), ("Racing Santander", 71), ("Almería", 69),
    ("Granada CF", 65), ("Huesca", 64), ("Eibar", 58),
    ("Albacete", 58), ("Sporting Gijón", 56), ("Burgos CF", 54),
    ("Cádiz CF", 54), ("Córdoba", 53), ("Deportivo", 53),
    ("Málaga CF", 53), ("Real Zaragoza", 51), ("Castellón", 49),
    ("Eldense", 45), ("Racing Ferrol", 30), ("Tenerife", 23),
    ("Cartagena", 23),
]

logos_path = pathlib.Path("logos")
# mapeo de nombres a archivos
logos_files = {p.stem.lower(): p for p in logos_path.glob("*.png")}

def buscar_logo(nombre_equipo):
    n = nombre_equipo.lower()
    for key, path in logos_files.items():
        if key in n or n in key:
            return path
    return None

c = canvas.Canvas("Segunda_Division_24_25.pdf", pagesize=A4)
w, h = A4
c.setFont("Helvetica-Bold", 18)
c.drawCentredString(w/2, h-50, "LaLiga Hypermotion 24/25 - Tabla Real")

y = h - 90
c.setFont("Helvetica", 11)
for i, (equipo, pts) in enumerate(TABLA, 1):
    logo = buscar_logo(equipo)
    if logo:
        try:
            c.drawImage(ImageReader(str(logo)), 40, y-4, 16, 16, mask='auto')
        except:
            pass
    c.drawString(65, y, f"{i}. {equipo}")
    c.drawString(350, y, f"{pts} pts")
    y -= 22

c.save()
print("PDF creado con logos locales, sin tocar API")
