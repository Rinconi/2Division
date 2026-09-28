# CELDA RESULTADOS 2a DIVISION -> JSON SCRAPING resultados-futbol.com (SIN API KEY)
import requests, json, re
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# 2a Division 25/26
URL = "https://www.resultados-futbol.com/segunda/grupo1"

print(f"Bajando {URL}...")
r = requests.get(URL, headers=headers, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

resultados = []

# La web tiene una tabla con clase 'vevent' por cada partido
partidos = soup.select("tr.vevent")
if not partidos:
    # Plan B por si cambian clase: busca todas las filas con resultado x-y
    partidos = soup.find_all("tr", string=re.compile(r"\d+ - \d+"))

print(f"Filas encontradas: {len(partidos)}")

for p in partidos:
    try:
        # Estructura tipica: local - resultado - visitante
        equipos = p.select("a")
        if len(equipos) < 2:
            continue

        local = equipos[0].get_text(strip=True)
        visitante = equipos[1].get_text(strip=True)

        # El marcador
        marcador_tag = p.select_one("a.clase") or p.select_one(".clase") or p.find(string=re.compile(r"\d+ - \d+"))
        if not marcador_tag:
            continue

        marcador = marcador_tag.get_text(strip=True) if hasattr(marcador_tag, 'get_text') else str(marcador_tag).strip()
        if "-" not in marcador:
            continue

        # Limpiar marcador 2 - 1 -> 2-1
        marcador = marcador.replace(" ", "")
        gl, gv = marcador.split("-")

        # Solo si ya se ha jugado (numerico)
        if not gl.isdigit():
            continue

        # Jornada y fecha (si está)
        jornada_tag = p.find_previous("th")
        jornada = jornada_tag.get_text(strip=True) if jornada_tag else "?"

        fecha_tag = p.select_one(".fecha") or p.select_one("td.fecha")
        fecha = fecha_tag.get_text(strip=True) if fecha_tag else ""

        resultados.append({
            "jornada": jornada,
            "fecha": fecha,
            "local": local,
            "visitante": visitante,
            "goles_local": int(gl),
            "goles_visitante": int(gv),
            "resultado": f"{gl}-{gv}"
        })
    except Exception as e:
        continue

# Si el raspado directo falla por cambio de web, usamos plan B con pandas (mucho mas robusto)
if len(resultados) < 20:
    print("Plan A flojo, probando Plan B con pandas...")
    import pandas as pd
    try:
        tables = pd.read_html(URL, flavor='bs4')
        for df in tables:
            # Busca tabla que tenga Local y Visitante
            cols = [str(c).lower() for c in df.columns]
            if any('local' in c or 'equipo' in c for c in cols):
                print(f"Tabla encontrada con {len(df)} filas")
                # Aquí lo adaptamos
                for _, row in df.iterrows():
                    try:
                        txt = " ".join([str(x) for x in row.values])
                        m = re.search(r'(\d+)\s*-\s*(\d+)', txt)
                        if m:
                            # Intentar sacar equipos
                            resultados.append({
                                "jornada": "",
                                "fecha": "",
                                "local": str(row.values[0]),
                                "visitante": str(row.values[-1]),
                                "goles_local": int(m.group(1)),
                                "goles_visitante": int(m.group(2)),
                                "resultado": f"{m.group(1)}-{m.group(2)}"
                            })
                    except:
                        pass
    except Exception as e:
        print(f"Error plan B: {e}")

# Ordenar y guardar
nombre = "resultados_2A_25_26_jugados.json"
with open(nombre, "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print(f"\n✅ JSON CREADO: {nombre}")
print(f"Total partidos jugados: {len(resultados)}")
if resultados:
    print(json.dumps(resultados[:5], ensure_ascii=False, indent=2))
else:
    print("⚠️ La web ha cambiado estructura. Dime y te preparo la versión con fbref.com que es mas estable.")
