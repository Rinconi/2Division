import json, pathlib, re, unicodedata, requests

FILE = pathlib.Path("informes/historial_hypermotion.json")

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c)!='Mn').strip()

data = json.loads(FILE.read_text(encoding='utf-8'))

# Resultado real verificado J7
web = {"cd leganes|cd castellon": (0,2,"2026-09-28")}

cambios = 0
for j in data["jornadas"]:
    num = j.get("numero") or j.get("jornada") or j.get("id") or "?"
    for p in j["partidos"]:
        if p.get("estado")!="finalizado" or p.get("goles_local") is None:
            clave = f"{norm(p['local'])}|{norm(p['visitante'])}"
            if clave in web:
                gl,gv,fecha = web[clave]
                p["goles_local"]=gl
                p["goles_visitante"]=gv
                p["estado"]="finalizado"
                if fecha: p["fecha"]=fecha
                cambios+=1
                print(f"ARREGLADO J{num}: {p['local']} {gl}-{gv} {p['visitante']}")

FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Total arreglados: {cambios}")
