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

def normaliza(s):
    return s.lower().replace("-","").replace("_","").replace(" ","")

logos_path = pathlib.Path("logos")
logos = {}
for p in logos_path.glob("*.png"):
    logos[normaliza(p.stem)] = p

print(f"Logos encontrados en GitHub: {list(logos.keys())}")

c = canvas.Canvas("Segunda_Division_24_25.pdf", pagesize=A4)
w,h = A4
c.setFont("Helvetica-Bold", 16)
c.drawCentredString(w/2, h-40, "LaLiga Hypermotion 24/25")
y = h-80
c.setFont("Helvetica", 11)

for i,(eq,pts) in enumerate(TABLA,1):
    eq_norm = normaliza(eq)
    # busca coincidencia: si "oviedo" está dentro de "realoviedo" lo pilla
    encontrado = None
    for k,p in logos.items():
        if eq_norm in k or k in eq_norm:
            encontrado = p
            break
    if encontrado:
        try:
            c.drawImage(ImageReader(str(encontrado)), 40, y-4, 18, 18, mask='auto')
        except Exception as e:
            print(f"Error dibujando {eq}: {e}")
    else:
        print(f"NO ENCONTRADO: {eq}")
    
    c.drawString(70, y, f"{i}. {eq} - {pts} pts")
    y -= 24

c.save()
print("PDF creado")
