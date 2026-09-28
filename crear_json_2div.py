import json
import requests

def obtener_datos_laliga_oficial():
    # URL de la API interna oficial de LaLiga
    url = "https://laliga.com"
    
    # Parámetros necesarios para filtrar las jornadas del campeonato
    params = {
        "limit": "500",      # Trae todos los partidos del tirón
        "offset": "0",
        "lang": "es-ES"      # Fuerza el idioma español en los nombres de equipos
    }
    
    # Cabeceras estándar que simulan la petición del navegador oficial
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.laliga.com/",
        "Origin": "https://www.laliga.com"
    }
    
    print("Conectando con la API oficial de LaLiga...")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Acceder al bloque de partidos devuelto por la infraestructura de LaLiga
        fixtures = data.get("container", [])
        if not fixtures:
            print("No se encontró estructura de partidos en la respuesta.")
            return
            
        lista_partidos = []
        
        for item in fixtures:
            # Extraer número de jornada limpio
            jornada_txt = item.get("week", "0")
            jornada = int(jornada_txt) if jornada_txt.isdigit() else 0
            
            # Formatear fecha (YYYY-MM-DD)
            fecha_raw = item.get("date", "")
            fecha = fecha_raw[:10] if fecha_raw else "Por definir"
            
            # Equipos
            equipo_local = item.get("home_team", {}).get("nickname", "Desconocido")
            equipo_visitante = item.get("away_team", {}).get("nickname", "Desconocido")
            
            # Evaluar estado y goles según los metadatos de LaLiga
            status = item.get("status", "").upper()
            
            if status in ["FINISHED", "COMPLETED", "FT"]:
                estado = "finalizado"
                goles_local = item.get("home_score")
                goles_visitante = item.get("away_score")
            elif status in ["LIVE", "PLAYING", "1H", "2H"]:
                estado = "en_curso"
                goles_local = item.get("home_score")
                goles_visitante = item.get("away_score")
            else:
                estado = "programado"
                goles_local = None
                goles_visitante = None
                
            partido = {
                "jornada": jornada,
                "fecha": fecha,
                "local": equipo_local,
                "visitante": equipo_visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "estado": estado
            }
            lista_partidos.append(partido)
            
        # Ordenar el JSON secuencialmente por jornadas
        lista_partidos.sort(key=lambda x: (x["jornada"], x["fecha"]))
        
        # Estructura maestra del JSON solicitado
        json_final = {
            "competicion": "LaLiga Hypermotion (Segunda División)",
            "temporada": "2026/2027",
            "total_partidos_extraidos": len(lista_partidos),
            "partidos": lista_partidos
        }
        
        # Guardar en local para el despliegue del bot de GitHub
        nombre_archivo = "partidos_segunda_division.json"
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(json_final, f, ensure_ascii=False, indent=2)
            
        print(f"¡Hecho! Archivo '{nombre_archivo}' actualizado con los datos oficiales de LaLiga.")
        
    except Exception as e:
        print(f"Error crítico al leer de LaLiga: {e}")

if __name__ == "__main__":
    obtener_datos_laliga_oficial()
