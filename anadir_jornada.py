import json, pathlib, re, unicodedata, requests
from bs4 import BeautifulSoup

FILE = pathlib.Path("informes/historial_hypermotion.json")

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9]','',s)

MESES = {"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06",
         "julio":"07","agosto":"08","septiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}

def parse_fecha(texto):
    # texto tipo "2 de octubre de 2026"
    m = re.search(r'(\d+)\s+de\s+(\w+)\s+de\s+(\d+)', texto.lower())
    if not m: return "2026-10-01"
    dia, mes_txt, anio = m.groups()
    mes = MESES.get(mes_txt, "10")
    return f"{anio}-{mes}-{int(dia):02d}"

def get_fixtures_jornada(num_jornada):
    """Busca en Vavel el calendario de la jornada num_jornada"""
    url = "https://www.vavel.com/es/data/laliga-hypermotion/2026/"
    headers = {"User-Agent":"Mozilla/5.0"}
    html = requests.get(url, headers=headers, timeout=20).text

    # Vavel viene en markdown: ### Viernes, 2 de octubre de 2026 · Jornada 8
    fixtures = []
    # Separamos por bloques de Jornada
    bloques = re.split(r'Jornada\s+(\d+)', html)
    # bloques = [antes, num, contenido, num, contenido...]
    for i in range(1, len(bloques), 2):
        try:
            nj = int(bloques[i])
            if nj!= num_jornada: continue
            contenido = bloques[i+1]
            # saca fecha del encabezado anterior
            # busca todas las fechas dentro del bloque
            fechas = re.findall(r'(?:Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo),\s+([^\n·]+)', contenido)
            # busca partidos tipo | Eldense vs Real Oviedo |
            partidos_bloque = re.findall(r'\|\s*([^|]+?)\s+vs\s+([^|]+?)\s*\|', contenido, re.IGNORECASE)

            # asigna fecha por orden (Vavel agrupa por dia)
            # Simplificación: si hay varias fechas, las repartimos
            idx_fecha = 0
            for local, vis in partidos_bloque:
                if "Partido" in local or "Hora" in local: continue
                local = local.strip()
                vis = vis.strip()
                fecha_str = parse_fecha(fechas[idx_fecha]) if idx_fecha < len(fechas) else "2026-10-01"
                # cuando cambia de dia en la tabla, avanza fecha
                # truco: cada 3-4 partidos cambia de dia en el html de Vavel, lo dejamos simple
                fixtures.append({
                    "fecha": fecha_str,
                    "local": local,
                    "visitante": vis,
                    "goles_local": None,
                    "goles_visitante": None,
                    "estado": "pendiente"
                })
            # Si no sacamos fecha bien, actualizamos con el primer encabezado que tengamos cerca
            if fixtures:
                print(f"Encontrados {len(fixtures)} partidos para jornada {num_jornada} en Vavel")
                return fixtures
        except Exception as e:
            continue
    print(f"No se encontró jornada {num_jornada} en Vavel")
    return []

# --- 1. CARGA ---
data = json.loads(FILE.read_text(encoding='utf-8'))

# --- 2. CONTAR PENDIENTES ---
pendientes = sum(1 for j in data["jornadas"] for p in j["partidos"] if p.get("estado")!="finalizado" or p.get("goles_local") is None)
print(f"Pendientes actuales: {pendientes}")

# --- 3. SI HAY POCOS PENDIENTES, CREAR SIGUIENTE JORNADA ---
if pendientes < 3:
    ultima = max(j["jornada"] for j in data["jornadas"])
    siguiente = ultima + 1
    print(f"Ultima jornada es {ultima}. Intentando crear la {siguiente}")
    if siguiente not in [j["jornada"] for j in data["jornadas"]]:
        fixtures = get_fixtures_jornada(siguiente)
        if fixtures:
            data["jornadas"].append({"jornada": siguiente, "partidos": fixtures})
            print(f"✅ Jornada {siguiente} creada con {len(fixtures)} partidos")
        else:
            print(f"Jornada {siguiente} aun no publicada")
else:
    print(f"Hay {pendientes} pendientes, no creo jornada nueva. Solo actualizo resultados.")

# --- 4. BUSCAR RESULTADOS FINALIZADOS EN VAVEL ---
try:
    headers={"User-Agent":"Mozilla/5.0"}
    html=requests.get("https://www.vavel.com/es/data/laliga-hypermotion/2026/", headers=headers, timeout=20).text
    web={}
    for m in re.finditer(r'([A-Za-z\s\.]{3,25}?)\s+(\d+)\s*-\s*(\d+)\s+([A-Za-z\s\.]{3,25})', html):
        loc,gl,gv,vis=m.groups()
        web[f"{norm(loc)}|{norm(vis)}"]=(int(gl),int(gv))

    for j in data["jornadas"]:
        for p in j["partidos"]:
            if p.get("goles_local") is not None: continue
            k=f"{norm(p['local'])}|{norm(p['visitante'])}"
            for wk,(gl,gv) in web.items():
                if norm(p['local']) in wk and norm(p['visitante']) in wk:
                    p["goles_local"]=gl
                    p["goles_visitante"]=gv
                    p["estado"]="finalizado"
                    print(f"Rellenado: {p['local']} {gl}-{gv} {p['visitante']}")
                    break
except Exception as e:
    print(f"Error resultados: {e}")

FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print("Guardado OK - respetando estructura")
