import pathlib, urllib.request
pathlib.Path("logos").mkdir(exist_ok=True)

# Estos son los 22 de Hypermotion 24/25 con nombre igual que en Primera
MAPA = {
    "levante.png": "https://crests.football-data.org/88.png",
    "elche.png": "https://crests.football-data.org/278.png",
    "real-oviedo.png": "https://crests.football-data.org/322.png",
    "mirandes.png": "https://crests.football-data.org/558.png",
    "racing-santander.png": "https://crests.football-data.org/560.png",
    "almeria.png": "https://crests.football-data.org/267.png",
    "granada.png": "https://crests.football-data.org/83.png",
    "huesca.png": "https://crests.football-data.org/299.png",
    "eibar.png": "https://crests.football-data.org/80.png",
    "albacete.png": "https://crests.football-data.org/324.png",
    "sporting-gijon.png": "https://crests.football-data.org/560.png",
    "burgos.png": "https://crests.football-data.org/557.png",
    "cadiz.png": "https://crests.football-data.org/264.png",
    "cordoba.png": "https://crests.football-data.org/563.png",
    "deportivo.png": "https://crests.football-data.org/560.png",
    "malaga.png": "https://crests.football-data.org/84.png",
    "real-zaragoza.png": "https://crests.football-data.org/87.png",
    "castellon.png": "https://crests.football-data.org/560.png",
    "eldense.png": "https://crests.football-data.org/562.png",
    "racing-ferrol.png": "https://crests.football-data.org/564.png",
    "tenerife.png": "https://crests.football-data.org/263.png",
    "cartagena.png": "https://crests.football-data.org/565.png",
}

opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent','Mozilla/5.0')]
urllib.request.install_opener(opener)

for nombre, url in MAPA.items():
    try:
        urllib.request.urlretrieve(url, f"logos/{nombre}")
        print(f"OK {nombre}")
    except Exception as e:
        print(f"Fallo {nombre}: {e}")
