import json, pathlib, re, unicodedata, requests
from datetime import datetime, timedelta

FILE = pathlib.Path("informes/historial_hypermotion.json")

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c)!='Mn')
    return re.sub(r'[^a-z0-9]','',s)

# --- FUENTE 1: ESPN (GRATIS, SIN KEY) ---
def from_espn(jornada_num, fecha_inicio):
    try:
        # ESPN funciona por rango de fechas, no por jornada
        # Buscamos 4 dias alrededor de la fecha esperada de la jornada
        d = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        dates = f"{d.strftime('%Y%m%d')}-{(d+timedelta(days=4)).strftime('%Y%m%d')}"
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/esp.2/scoreboard?dates={dates}"
        j = requests.get(url, timeout=15).json()
        fixtures=[]
        for ev in j.get("events",[]):
            # ESPN da equipos y fecha
            comp = ev["competitions"][0]
            local = comp["competitors"][0]["team"]["displayName"]
            vis = comp["competitors"][1]["team"]["displayName"]
            # Ajusta orden si visitante es home
            if comp["competitors"][0].get("homeAway")=="away":
                local, vis = vis, local
            fecha = ev["date"][:10]
            fixtures.append({
                "fecha": fecha, "local": local, "visitante": vis,
                "goles_local": None, "goles_visitante": None, "estado": "pendiente"
            })
        if len(fixtures)>=8: # una jornada tiene 11
            print(f"ESPN: {len(fixtures)} partidos")
            return fixtures[:11]
    except Exception as e:
        print(f"ESPN fallo: {e}")
    return []

# --- FUENTE 2: RESULTADOS-FUTBOL.COM ---
def from_resultados_futbol(jornada_num):
    try:
        url = f"https://www.resultados-futbol.com/laliga2/grupo1/jornada{jornada_num}"
        html = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=15).text
        partidos=[]
        # busca "Eldense - Real Oviedo"
        for m in re.finditer(r'>([^<]+?)\s*-\s*([^<]+?)<', html):
            loc, vis = m.groups()
            if len(loc)<4 or len(vis)<4: continue
            if "Jornada" in loc: continue
            if any(x in loc for x in ["Clasific","Goleadores"]): continue
            partidos.append({
                "fecha": f"2026-10-0{2 if jornada_num==8 else 1}",
                "local": loc.strip(), "visitante": vis.strip(),
                "goles_local": None, "goles_visitante": None, "estado": "pendiente"
            })
        # quitar duplicados
        uniq=[]
        seen=set()
        for p in partidos:
            k=norm(p["local"])+norm(p["visitante"])
            if k not in seen:
                seen.add(k); uniq.append(p)
        if len(uniq)>=8:
            print(f"Resultados-Futbol: {len(uniq)} partidos")
            return uniq[:11]
    except Exception as e:
        print(f"Resultados-Futbol fallo: {e}")
    return []

# --- FUENTE 3: API-FOOTBALL (1 PETICION SOLO) ---
def from_api_football(jornada_num):
    # Pon aqui tu key si quieres, si no lo saltamos para no gastar
    # KEY = "tu_key"
    # url = f"https://v3.football.api-sports.io/fixtures?league=89&season=2026&round=Regular Season - {jornada_num}"
    # Solo 1 request por run
    return []

def get_fixtures_multi(jornada_num):
    # Intentamos en orden barato -> caro
    fecha_estimada = {8:"2026-10-02", 9:"2026-10-10", 10:"2026-10-17"}.get(jornada_num, "2026-10-02")

    f = from_espn(jornada_num, fecha_estimada)
    if f: return f

    f = from_resultados_futbol(jornada_num)
    if f: return f

    f = from_api_football(jornada_num)
    if f: return f

    print("Todas las webs fallaron")
    return []

# --- MAIN ---
data = json.loads(FILE.read_text(encoding='utf-8'))
pendientes = sum(1 for j in data["jornadas"] for p in j["partidos"] if p.get("estado")!="finalizado" or p.get("goles_local") is None)
print(f"Pendientes: {pendientes}")

if pendientes < 3:
    ultima = max(j["jornada"] for j in data["jornadas"])
    sig = ultima + 1
    if sig not in [j["jornada"] for j in data["jornadas"]]:
        print(f"Ultima {ultima}, creando {sig} desde web...")
        fixtures = get_fixtures_multi(sig)
        if fixtures:
            data["jornadas"].append({"jornada": sig, "partidos": fixtures})
            print(f"✅ Jornada {sig} creada desde web con {len(fixtures)} partidos")
        else:
            print(f"Jornada {sig} aun no publicada en ninguna web")
else:
    print(f"Hay {pendientes} pendientes, no creo nueva jornada")

# --- RESULTADOS VAVEL/ESPN ---
try:
    # ESPN para resultados finalizados
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.2/scoreboard?dates=20260928-20261006"
    j = requests.get(url, timeout=15).json()
    web={}
    for ev in j.get("events",[]):
        if ev["status"]["type"]["completed"]:
            comp=ev["competitions"][0]
            gl = int(comp["competitors"][0]["score"])
            gv = int(comp["competitors"][1]["score"])
            loc = comp["competitors"][0]["team"]["displayName"]
            vis = comp["competitors"][1]["team"]["displayName"]
            web[f"{norm(loc)}|{norm(vis)}"]=(gl,gv)
            web[f"{norm(vis)}|{norm(loc)}"]=(gv,gl)

    for jj in data["jornadas"]:
        for p in jj["partidos"]:
            if p.get("goles_local") is not None: continue
            k=f"{norm(p['local'])}|{norm(p['visitante'])}"
            if k in web:
                gl,gv=web[k]
                p["goles_local"]=gl; p["goles_visitante"]=gv; p["estado"]="finalizado"
                print(f"Rellenado: {p['local']} {gl}-{gv} {p['visitante']}")
except Exception as e:
    print(f"Error rellenando resultados: {e}")

FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print("Guardado OK respetando estructura")
