import os, requests

os.makedirs("logos", exist_ok=True)

# Logos oficiales HD (Wikipedia SVG -> PNG 500px)
LOGOS = {
    "levante.png": "https://upload.wikimedia.org/wikipedia/en/7d/Levante_UD_logo.png",
    "elche.png": "https://upload.wikimedia.org/wikipedia/en/a/a3/Elche_CF_logo.png",
    "oviedo.png": "https://upload.wikimedia.org/wikipedia/en/6/6e/Real_Oviedo_logo.png",
    "mirandes.png": "https://upload.wikimedia.org/wikipedia/en/2/2e/CD_Mirand%C3%A9s_logo.png",
    "racing-santander.png": "https://upload.wikimedia.org/wikipedia/en/4/47/Racing_de_Santander_logo.png",
    "almeria.png": "https://upload.wikimedia.org/wikipedia/en/2/2d/UD_Almeria_logo.png",
    "granada.png": "https://upload.wikimedia.org/wikipedia/en/6/6a/Granada_CF_logo.png",
    "huesca.png": "https://upload.wikimedia.org/wikipedia/en/b/b9/SD_Huesca_logo.png",
    "eibar.png": "https://upload.wikimedia.org/wikipedia/en/4/46/SD_Eibar_logo.png",
    "albacete.png": "https://upload.wikimedia.org/wikipedia/en/6/6e/Albacete_Balompi%C3%A9_logo.png",
    "sportinggijon.png": "https://upload.wikimedia.org/wikipedia/en/6/6c/Sporting_Gijon_logo.png",
    "burgos.png": "https://upload.wikimedia.org/wikipedia/en/c/c2/Burgos_CF_logo.png",
    "cadiz.png": "https://upload.wikimedia.org/wikipedia/en/8/86/Cadiz_CF_logo.png",
    "cordoba.png": "https://upload.wikimedia.org/wikipedia/en/5/5a/C%C3%B3rdoba_CF_logo.png",
    "deportivo.png": "https://upload.wikimedia.org/wikipedia/en/2/2e/Deportivo_de_La_Coru%C3%B1a_logo.png",
    "malaga.png": "https://upload.wikimedia.org/wikipedia/en/6/6f/M%C3%A1laga_CF_logo.png",
    "zaragoza.png": "https://upload.wikimedia.org/wikipedia/en/c/c2/Real_Zaragoza_logo.png",
    "castellon.png": "https://upload.wikimedia.org/wikipedia/en/6/6e/CD_Castell%C3%B3n_logo.png",
    "eldense.png": "https://upload.wikimedia.org/wikipedia/en/3/3d/CD_Eldense_logo.png",
    "racing-ferrol.png": "https://upload.wikimedia.org/wikipedia/en/f/f1/Racing_Club_de_Ferrol_logo.png",
    "tenerife.png": "https://upload.wikimedia.org/wikipedia/en/1/19/CD_Tenerife_logo.png",
    "cartagena.png": "https://upload.wikimedia.org/wikipedia/en/5/56/FC_Cartagena_logo.png",
}

headers = {"User-Agent": "Mozilla/5.0"}
for nombre, url in LOGOS.items():
    r = requests.get(url, headers=headers, timeout=15)
    if r.status_code == 200:
        with open(f"logos/{nombre}", "wb") as f:
            f.write(r.content)
        print(f"OK {nombre} {len(r.content)//1000}KB")
    else:
        print(f"FALLO {nombre} {r.status_code}")

print("Listo - 22 logos en logos/")
