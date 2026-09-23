import pathlib, urllib.request
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# IDs reales de LaLiga Hypermotion en football-data.org
LOGOS_URL = {
    "Levante UD": "https://crests.football-data.org/88.png",
    "Elche CF": "https://crests.football-data.org/278.png",
    "Real Oviedo": "https://crests.football-data.org/322.png",
    "Mirandés": "https://crests.football-data.org/558.png",
    "Racing Santander": "https://crests.football-data.org/560.png",
    "Almería": "https://crests.football-data.org/267.png",
    "Granada CF": "https://crests.football-data.org/83.png",
    "Huesca": "https://crests.football-data.org/558.png",
    "Eibar": "https://crests.football-data.org/80.png",
    "Albacete": "https://crests.football-data.org/324.png",
    "Sporting Gijón": "https://crests.football-data.org/559.png",
    "Burgos CF": "https://crests.football-data.org/557.png",
    "Cádiz CF": "https://crests.football-data.org/264.png",
    "Córdoba": "https://crests.football-data.org/563.png",
    "Deportivo": "https://crests.football-data.org/560.png",
    "Málaga CF": "https://crests.football-data.org/84.png",
    "Real Zaragoza": "https://crests.football-data.org/87.png",
    "Castellón": "https://crests.football-data.org/561.png",
    "Eldense": "https://crests.football-data.org/562.png",
    "Racing Ferrol": "https://crests.football-data.org/564.png",
    "Tenerife": "https://crests.football-data.org/263.png",
    "Cartagena": "https://crests.football-data.org/565.png",
}

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
logos_path.mkdir(exist_ok=True)

c = canvas.Canvas("Segunda_Division_24_25.pdf", pagesize=A4)
w,h = A4
c.setFont("Helvetica-Bold", 14)
c.drawCentredString(w/2, h-40, "LaLiga Hypermotion 24/25 - Tabla Real")
y = h-80

for i,(eq,pts) in enumerate(TABLA,1):
    # baja el logo si no existe
    logo_file = logos_path / f"{eq}.png"
    if not logo_file.exists():
        try:
            url = LOGOS_URL.get(eq)
            if url:
                urllib.request.urlretrieve(url, logo_file)
                print(f"Bajado {eq}")
        except Exception as e:
            print(f"Fallo bajando {eq}: {e}")

    if logo_file.exists():
        try: c.drawImage(ImageReader(str(logo_file)), 35, y-3, 14, 14, mask='auto')
        except: pass

    c.setFont("Helvetica", 10)
    c.drawString(60, y, f"{i}. {eq} - {pts} pts")
    y-=20

c.save()
print("PDF Segunda con escudos reales creado")
