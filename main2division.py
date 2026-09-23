import pathlib
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

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
# coge todos los png, aunque se llamen 263.png
logos_files = sorted(logos_path.glob("*.png"))
print(f"Tengo {len(logos_files)} logos en /logos")

c = canvas.Canvas("Segunda_Division_24_25.pdf", pagesize=A4)
w,h = A4
c.setFont("Helvetica-Bold", 15)
c.drawCentredString(w/2, h-40, "LaLiga Hypermotion 24/25 - Tabla Real")
y = h-80
c.setFont("Helvetica", 11)

for i, (equipo, pts) in enumerate(TABLA):
    # si hay logos, usa uno para cada equipo
    if i < len(logos_files):
        try:
            c.drawImage(ImageReader(str(logos_files[i])), 35, y-4, 16, 16, mask='auto')
        except Exception as e:
            print(f"Error con {logos_files[i]}: {e}")

    c.drawString(60, y, f"{i+1}. {equipo}")
    c.drawRightString(400, y, f"{pts} pts")
    y -= 24
    if y < 50:
        c.showPage()
        y = h-50

c.save()
print("PDF con logos numericos creado")
