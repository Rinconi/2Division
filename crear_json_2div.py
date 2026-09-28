import json
import requests

def obtener_partidos():
    # Usamos los repositorios abiertos de openfootball para la Segunda División de España (es2)
    # Temporada actual 2026/2027
    url = "https://githubusercontent.com"
    
    print("Descargando datos oficiales del campeonato...")
    response = requests.get(url)
    
    if response.status_code != 200:
        print("La base de datos central de openfootball aún no tiene el JSON de esta temporada.")
        print("Generando un JSON estructurado de contingencia...")
        
        # En caso de que la temporada esté recién empezando en openfootball, aseguramos la creación del archivo
        json_vacio = {
            "competicion": "LaLiga Hypermotion (Segunda División)",
            "temporada": "2026/2027",
            "total_partidos": 0,
            "partidos": []
        }
        with open("partidos_segunda_division.json", "w", encoding="utf-8") as f:
            json.dump(json_vacio, f, ensure_ascii=False, indent=2)
        return

    data = response.json()
    lista_partidos = []

    # Procesar las jornadas y partidos de openfootball
    for round_data in data.get("rounds", []):
        # Intentar extraer el número de la jornada (ej: "Round 1" -> 1)
        nombre_jornada = round_data.get("name", "")
        jornada = int(''.join(filter(str.isdigit, nombre_jornada))) if any(char.isdigit() for char in nombre_jornada) else nombre_jornada
        
        for match in round_data.get("matches", []):
            goles_local = match.get("score", {}).get("ft", [None, None])[0]
            goles_visitante = match.get("score", {}).get("ft", [None, None])[1]
            
            estado = "finalizado" if goles_local is not None else "programado"
            
            partido = {
                "jornada": jornada,
                "fecha": match.get("date", ""),
                "local": match.get("team1", ""),
                "visitante": match.get("team2", ""),
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "estado": estado
            }
            lista_partidos.append(partido)

    # Estructura final uniforme
    json_final = {
        "competicion": "LaLiga Hypermotion (Segunda División)",
        "temporada": "2026/2027",
        "total_partidos": len(lista_partidos),
        "partidos": lista_partidos
    }

    # Guardar asegurando el nombre exacto que busca Git
    with open("partidos_segunda_division.json", "w", encoding="utf-8") as f:
        json.dump(json_final, f, ensure_ascii=False, indent=2)
        
    print(f"¡Éxito! Archivo generado con {len(lista_partidos)} partidos.")

if __name__ == "__main__":
    obtener_partidos()
