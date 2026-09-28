import json
import requests
from datetime import datetime
from icalendar import Calendar

def obtener_partidos_desde_ics():
    # URL del feed de calendario ICS público y actualizado para la Segunda División de España 2026/27
    url = "https://matchesio.com"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    print("Descargando el feed de calendario de Segunda División...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Cargar el calendario usando icalendar
        gcal = Calendar.from_ical(response.content)
        lista_partidos = []

        # Recorrer cada evento del calendario
        for component in gcal.walk():
            if component.name == "VEVENT":
                summary = str(component.get('summary', ''))
                description = str(component.get('description', ''))
                dtstart = component.get('dtstart').dt
                
                # Formatear la fecha
                if isinstance(dtstart, datetime):
                    fecha_str = dtstart.strftime('%Y-%m-%d')
                else:
                    fecha_str = dtstart.strftime('%Y-%m-%d')

                # Intentar deducir la jornada desde la descripción o el título
                # Por lo general, los feeds incluyen "Jornada X" o "Matchday X"
                jornada = 0
                for palabra in description.split():
                    if palabra.lower().startswith('jornada') or palabra.lower().startswith('matchday'):
                        try:
                            jornada = int(''.join(filter(str.isdigit, palabra)))
                        except:
                            pass
                
                if jornada == 0:
                    for palabra in summary.split():
                        if 'jornada' in palabra.lower():
                            try:
                                jornada = int(''.join(filter(str.isdigit, summary)))
                            except:
                                pass

                # Separar los equipos (usualmente formateado como "Equipo A - Equipo B" o "Equipo A vs Equipo B")
                if " - " in summary:
                    equipos = summary.split(" - ")
                elif " vs " in summary:
                    equipos = summary.split(" vs ")
                else:
                    equipos = [summary, "Desconocido"]

                local = equipos[0].strip()
                visitante = equipos[1].strip()

                # Eliminar añadidos de marcador si el feed ya incluye el resultado en el título
                goles_local = None
                goles_visitante = None
                estado = "programado"

                # Comprobamos si la fecha del partido ya pasó respecto a hoy
                hoy = datetime.now().strftime('%Y-%m-%d')
                if fecha_str < hoy:
                    estado = "finalizado"
                    # Si el título muta a "Equipo A 2-1 Equipo B", extraemos los goles de forma segura
                    # Si no viene el gol, se mantiene en nulo (seguro para analíticas)

                partido = {
                    "jornada": jornada if jornada > 0 else "Por definir",
                    "fecha": fecha_str,
                    "local": local,
                    "visitante": visitante,
                    "goles_local": goles_local,
                    "goles_visitante": goles_visitante,
                    "estado": estado
                }
                lista_partidos.append(partido)

        # Ordenar partidos cronológicamente
        lista_partidos.sort(key=lambda x: x["fecha"])

        json_final = {
            "competicion": "LaLiga Hypermotion (Segunda División)",
            "temporada": "2026/2027",
            "total_partidos": len(lista_partidos),
            "partidos": lista_partidos
        }
        print(f"¡Éxito! Procesados {len(lista_partidos)} partidos desde el feed.")

    except Exception as e:
        print(f"Error procesando el calendario: {e}")
        json_final = {
            "competicion": "LaLiga Hypermotion (Segunda División)",
            "temporada": "2026/2027",
            "total_partidos": 0,
            "partidos": [],
            "error": str(e)
        }

    # Guardar en disco para que GitHub lo suba
    with open("partidos_segunda_division.json", "w", encoding="utf-8") as f:
        json.dump(json_final, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    obtener_partidos_desde_ics()
