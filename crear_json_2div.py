import json
import requests
from bs4 import BeautifulSoup

def hacer_scraping_segunda():
    # URL del calendario de Segunda División de la temporada actual
    url = "https://bdfutbol.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("Extrayendo datos de la web de BDFutbol...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"No se pudo acceder a la página. Código de estado: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    lista_partidos = []

    # Cada jornada está contenida en una tabla con la clase 'calendari'
    tablas_jornada = soup.find_all('table', class_='calendari')

    for num_jornada, tabla in enumerate(tablas_jornada, start=1):
        filas = tabla.find_all('tr')
        
        for fila in filas:
            columnas = fila.find_all('td')
            # Aseguramos que sea una fila de partido válida (debe tener el nombre de los equipos y resultado)
            if len(columnas) >= 3:
                # Extraer texto de las columnas eliminando espacios extra
                equipo_local = columnas[0].get_text(strip=True)
                resultado_txt = columnas[1].get_text(strip=True)
                equipo_visitante = columnas[2].get_text(strip=True)
                
                # Opcional: intentar buscar una fecha si está disponible en la fila
                fecha = ""
                if len(columnas) > 3:
                    fecha = columnas[3].get_text(strip=True)

                # Procesar el resultado (ejemplo: "2-1" o " - ")
                if "-" in resultado_txt and resultado_txt.replace("-", "").strip() != "":
                    try:
                        goles = resultado_txt.split("-")
                        goles_local = int(goles[0].strip())
                        goles_visitante = int(goles[1].strip())
                        estado = "finalizado"
                    except ValueError:
                        goles_local = None
                        goles_visitante = None
                        estado = "programado"
                else:
                    goles_local = None
                    goles_visitante = None
                    estado = "programado"

                # Guardar el partido estructurado
                partido = {
                    "jornada": num_jornada,
                    "fecha_raw": fecha,
                    "local": equipo_local,
                    "visitante": equipo_visitante,
                    "goles_local": goles_local,
                    "goles_visitante": goles_visitante,
                    "estado": estado
                }
                lista_partidos.append(partido)

    # Estructura final de tu JSON
    json_final = {
        "competicion": "LaLiga Hypermotion (Segunda División)",
        "temporada": "2026/2027",
        "total_partidos": len(lista_partidos),
        "partidos": lista_partidos
    }

    # Guardar en el archivo JSON local
    nombre_archivo = "partidos_segunda_division.json"
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(json_final, f, ensure_ascii=False, indent=2)

    print(f"¡Éxito! El archivo '{nombre_archivo}' ha sido creado con {len(lista_partidos)} partidos.")

if __name__ == "__main__":
    hacer_scraping_segunda()
