import json, pathlib, re, unicodedata, requests

FILE = pathlib.Path("informes/historial_hypermotion.json")

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c)!='Mn').strip()

def get_finalizados():
    resultados = {}
    try:
        url = "https://www.marca.com/futbol/segunda-division/calendario.html"
        html = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15).text
        # Solo coge los que ya tienen marcador tipo 1 - 0
        for m in re.finditer(r'title="([^"]+)\s+(\d+)\s*-\s*(\d+)\s+([^"]+)"', html):
            local, gl, gv, vis = m.groups()
            if len(local) < 3 or len(vis) < 3: continue
            clave = f"{norm(local)}|{norm(vis)}"
            resultados[clave] = (int(gl), int(gv))
            print(f"Web: {local} {gl}-{gv} {vis}")
    except Exception as e:
        print(f"Error leyendo web: {e}")
    return resultados

data = json.loads(FILE.read_text(encoding='utf-8'))
web = get_finalizados()

cambios = 0
for j in data["jornadas"]:
    for p in j["partidos"]:
        if p.get("estado") == "finalizado" and p.get("goles_local") is not None:
            continue # este ya está, lo saltamos
        clave = f"{norm(p['local'])}|{norm(p['visitante'])}"
        if clave in web:
            gl, gv = web[clave]
            p["goles_local"] = gl
            p["goles_visitante"] = gv
            p["estado"] = "finalizado"
            cambios += 1
            print(f"AÑADIDO: {p['local']} {gl}-{gv} {p['visitante']}")

FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Listo. {cambios} partidos nuevos añadidos.")
