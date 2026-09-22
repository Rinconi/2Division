import os, requests, pathlib, time
from datetime import datetime
from zoneinfo import ZoneInfo
import fpdf, cairosvg

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN") or os.getenv("FOOTBALL_TOKEN")
HEADERS = {"X-Auth-Token": TOKEN}
BASE = "https://api.football-data.org/v4/competitions/SD" # <--- CAMBIO A 2DA
now_spain = datetime.now(ZoneInfo("Europe/Madrid"))
LESIONES_CACHE = None
PARTIDOS_TODOS_CACHE = None
POSICIONES_CACHE = {}

def clean(s):
    if not s: return ""
    return str(s).encode('latin-1','ignore').decode('latin-1')

# --- TABLA LALIGA 2 ---
stand = requests.get(f"{BASE}/standings", headers=HEADERS, timeout=20).json()
table = stand["standings"][0]["table"]

# --- ESCUDOS ---
pathlib.Path("logos").mkdir(exist_ok=True)
crest_by_id = {}
for r in table:
    tid = r["team"]["id"]
    url = r["team"]["crest"]
    dest = f"logos/{tid}.png"
    if not os.path.exists(dest):
        try:
            data = requests.get(url, timeout=15).content
            if url.endswith(".svg") or b"<svg" in data[:500]:
                cairosvg.svg2png(bytestring=data, write_to=dest)
            else:
                open(dest,"wb").write(data)
        except: pass
    if os.path.exists(dest):
        crest_by_id[tid] = dest

# --- PARTIDOS ---
def get_todos_partidos():
    global PARTIDOS_TODOS_CACHE
    if PARTIDOS_TODOS_CACHE is not None:
        return PARTIDOS_TODOS_CACHE
    try:
        season = now_spain.year if now_spain.month >= 7 else now_spain.year - 1
        url = f"{BASE}/matches?season={season}"
        print(f"Cargando partidos SD de {season}...")
        data = requests.get(url, headers=HEADERS, timeout=25).json()
        PARTIDOS_TODOS_CACHE = data.get("matches", [])
        return PARTIDOS_TODOS_CACHE
    except Exception as e:
        print(f"Error partidos: {e}")
        PARTIDOS_TODOS_CACHE = []
        return PARTIDOS_TODOS_CACHE

def get_partidos(team_id):
    todos = get_todos_partidos()
    if not todos: return []
    res = [m for m in todos if m.get("homeTeam",{}).get("id")==team_id or m.get("awayTeam",{}).get("id")==team_id]
    jugados = [m for m in res if m.get("status")=="FINISHED"]
    return sorted(jugados, key=lambda x: x["utcDate"])

# --- COMUNIAZO 2DA DIVISION ---
from bs4 import BeautifulSoup
TEAMS_LALIGA2 = ["Albacete","Almería","Andorra","Burgos","Cádiz","Castellón","Ceuta","Córdoba","Cultural","Deportivo","Eibar","Granada","Huesca","Las Palmas","Leganés","Málaga","Mirandés","Racing","Real Sociedad B","Valladolid","Sporting","Tenerife","Zaragoza","Elche","Levante","Oviedo"]
POS_MAP = {"PT":"POR","POR":"POR","DF":"DEF","DEF":"DEF","MC":"MED","MED":"MED","DL":"DEL","DEL":"DEL"}

def get_lesiones_comuniazo_all():
    global LESIONES_CACHE
    if LESIONES_CACHE is not None:
        return LESIONES_CACHE
    try:
        # Comuniazo segunda
        r = requests.get("https://www.comuniazo.com/lesionados-segunda-division", headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        if r.status_code!= 200:
            r = requests.get("https://www.comuniazo.com/lesionados", headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")
        lines = [l.strip() for l in soup.get_text(separator="\n").split("\n") if l.strip() and len(l.strip())>1]
        data = {}
        current_team = None
        for i, line in enumerate(lines):
            for tm in TEAMS_LALIGA2:
                if tm.lower() in line.lower() and len(line) < 30:
                    current_team = tm
                    if tm not in data: data[tm] = {}
                    break
            if current_team and "Baja" in line:
                jugador = ""; lesion = ""; pos = ""; baja = line
                if i >= 2:
                    posible_jug = lines[i-2]; posible_les = lines[i-1]
                    if i >= 3 and lines[i-3].upper() in POS_MAP:
                        pos = POS_MAP[lines[i-3].upper()]; jugador = posible_jug; lesion = posible_les
                    else:
                        jugador = posible_jug; lesion = posible_les
                if not jugador or len(jugador) > 35 or "Baja" in jugador or len(jugador) < 3:
                    continue
                if jugador not in data[current_team]:
                    data[current_team][jugador] = {"jugador": jugador, "pos": pos if pos else "-", "lesion": lesion, "baja": baja}
        print(f"Comuniazo 2ª OK: {sum(len(v) for v in data.values())} bajas")
        LESIONES_CACHE = data
        return data
    except Exception as e:
        print(f"Error Comuniazo 2ª: {e}"); return {}

def get_mapa_posiciones(team_id):
    if team_id in POSICIONES_CACHE: return POSICIONES_CACHE[team_id]
    try:
        data = requests.get(f"https://api.football-data.org/v4/teams/{team_id}", headers=HEADERS, timeout=15).json()
        mapa = {}
        for p in data.get("squad", []):
            nombre = p.get("name","").lower(); short = p.get("shortName","").lower()
            pos_api = p.get("position","")
            if "Goalkeeper" in pos_api: pos = "POR"
            elif "Defence" in pos_api: pos = "DEF"
            elif "Midfield" in pos_api: pos = "MED"
            elif "Offence" in pos_api or "Forward" in pos_api: pos = "DEL"
            else: pos = "-"
            mapa[nombre] = pos; mapa[nombre.split()[-1]] = pos
            if short: mapa[short] = pos
        POSICIONES_CACHE[team_id] = mapa
        return mapa
    except: return {}

def buscar_posicion(team_id, nombre_jugador):
    mapa = get_mapa_posiciones(team_id); nj = nombre_jugador.lower()
    if nj in mapa: return mapa[nj]
    for k,v in mapa.items():
        if k in nj or nj in k: return v
    return "-"

def get_lesiones_equipo(team_name, team_id):
    all_data = get_lesiones_comuniazo_all(); lista = []
    for k,v in all_data.items():
        if k.lower() in team_name.lower() or team_name.lower() in k.lower():
            lista = list(v.values()); break
    for d in lista:
        if d.get("pos","-") == "-" or d.get("pos") == "":
            d["pos"] = buscar_posicion(team_id, d["jugador"])
    return lista[:10]

# --- PDF ---
pdf = fpdf.FPDF('P','mm','A4')
pdf.set_margins(10,10,10); pdf.set_auto_page_break(auto=True, margin=12); pdf.add_page()
w = [8, 10, 48, 11, 12, 10, 10, 10, 11, 11, 11]; headers = ["#", "", "Equipo", "PJ", "PTS", "G", "E", "P", "GF", "GC", "DG"]
total_w = sum(w); x_start = (210 - total_w) / 2
pdf.set_font("Helvetica","B",13); pdf.cell(0,7,f"LaLiga 2Division - {now_spain.strftime('%d/%m/%Y %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica","",10); pdf.cell(0,6,f"Jornada {table[0]['playedGames']} - Clasificacion", align="C", new_x="LMARGIN", new_y="NEXT"); pdf.ln(3)
pdf.set_x(x_start); pdf.set_font("Helvetica","B",9); pdf.set_fill_color(0,0,0); pdf.set_text_color(255,255,255)
for i, txt in enumerate(headers): pdf.cell(w[i],8,txt,1,align="C",fill=True)
pdf.ln(); pdf.set_text_color(0,0,0)
for pos, row in enumerate(table,1):
    if pos<=2: pdf.set_fill_color(210,195,255) # Ascenso directo
    elif pos<=6: pdf.set_fill_color(255,228,181) # Playoff
    elif pos>=19: pdf.set_fill_color(255,182,182) # Descenso (4)
    else: pdf.set_fill_color(255,255,255)
    pdf.set_x(x_start); pdf.set_font("Helvetica","",8); pdf.cell(w[0],6.5,str(pos),1,align="C",fill=True)
    x = pdf.get_x(); y = pdf.get_y(); pdf.cell(w[1],6.5,"",1,fill=True)
    logo = crest_by_id.get(row["team"]["id"])
    if logo:
        try: pdf.image(logo, x=x+1, y=y+0.7, w=5, h=5)
        except: pass
    pdf.set_font("Helvetica","B",8.5); pdf.cell(w[2],6.5,clean(row["team"]["shortName"]),1,fill=True)
    pdf.set_font("Helvetica","",8); pdf.cell(w[3],6.5,str(row["playedGames"]),1,align="C",fill=True)
    pdf.set_font("Helvetica","B",9); pdf.cell(w[4],6.5,str(row["points"]),1,align="C",fill=True); pdf.set_font("Helvetica","",8)
    pdf.cell(w[5],6.5,str(row["won"]),1,align="C",fill=True); pdf.cell(w[6],6.5,str(row["draw"]),1,align="C",fill=True)
    pdf.cell(w[7],6.5,str(row["lost"]),1,align="C",fill=True); pdf.cell(w[8],6.5,str(row["goalsFor"]),1,align="C",fill=True)
    pdf.cell(w[9],6.5,str(row["goalsAgainst"]),1,align="C",fill=True)
    dg = row["goalsFor"] - row["goalsAgainst"]; pdf.cell(w[10],6.5,f"{'+' if dg>0 else ''}{dg}",1,align="C",fill=True); pdf.ln()
pdf.ln(5)
if pdf.get_y() > 260: pdf.add_page()
lx = x_start; ly = pdf.get_y()
pdf.set_fill_color(210,195,255); pdf.rect(lx, ly, 4, 4, 'F'); pdf.set_xy(lx+6, ly-0.5); pdf.cell(35,5,"1-2 Ascenso")
pdf.set_fill_color(255,228,181); pdf.rect(lx+45, ly, 4, 4, 'F'); pdf.set_xy(lx+51, ly-0.5); pdf.cell(35,5,"3-6 Playoff")
pdf.set_fill_color(255,182,182); pdf.rect(lx+90, ly, 4, 4, 'F'); pdf.set_xy(lx+96, ly-0.5); pdf.cell(35,5,"19-22 Descenso")
pdf.ln(8); pdf.set_font("Helvetica","I",7); pdf.set_x(x_start); pdf.cell(total_w,4,f"Fuente: football-data.org | Lesiones: Comuniazo.com | Generado: {now_spain.strftime('%d/%m/%Y %H:%M')} Europe/Madrid", align="C")

# FICHAS
for row in table:
    pdf.add_page(); team = row["team"]["name"]; tid = row["team"]["id"]
    logo = crest_by_id.get(tid)
    if logo:
        try: pdf.image(logo, x=12, y=10, w=20, h=20)
        except: pass
    pdf.set_xy(36,12); pdf.set_font("Helvetica","B",14); pdf.cell(0,8,clean(f"{team} - Pos {row['position']} | {row['points']} pts"))
    pdf.set_xy(36,20); pdf.set_font("Helvetica","",9); pdf.cell(0,6,clean(f"PJ:{row['playedGames']} G:{row['won']} E:{row['draw']} P:{row['lost']} GF:{row['goalsFor']} GC:{row['goalsAgainst']}"))
    pdf.set_xy(12,34); pdf.set_font("Helvetica","B",11)
    max_jornada = max([m.get("matchday",0) for m in (PARTIDOS_TODOS_CACHE or []) if m.get("status")=="FINISHED"], default=7)
    pdf.set_fill_color(166,166,166)
    pdf.cell(0, 7, f" Partidos jugados (Jornada 1-{max_jornada}) - Casa / Resultado / Fuera ", border=1, ln=1, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica","B",10)
    pdf.set_fill_color(52,58,64); pdf.set_text_color(255,255,255)
    pdf.cell(22,6,"Fecha",1,align="C",fill=True); pdf.cell(58,6,"EN CASA",1,align="C",fill=True); pdf.cell(12,6,"R",1,align="C",fill=True); pdf.cell(58,6,"FUERA",1,align="C",fill=True); pdf.cell(20,6,"GOL",1,align="C",fill=True); pdf.ln()
    pdf.set_font("Helvetica","",9); pdf.set_text_color(0,0,0)
    partidos = get_partidos(tid)
    for m in partidos:
        fecha = m["utcDate"][:10]; home = m["homeTeam"]["shortName"]; away = m["awayTeam"]["shortName"]
        hs = m["score"]["fullTime"]["home"]; aw = m["score"]["fullTime"]["away"]
        if hs is None or aw is None: continue
        is_home = m["homeTeam"]["id"] == tid
        if hs == aw: res="E"; cr,cg,cb =255,255,150
        elif (is_home and hs > aw) or (not is_home and aw > hs): res="V"; cr,cg,cb =180,255,180
        else: res="D"; cr,cg,cb =255,80,80
        pdf.cell(22,6,fecha,1,0,"C")
        if is_home:
            pdf.cell(58,6,f"{home} {hs}-{aw} {away}",1,0,"L")
            pdf.set_fill_color(cr,cg,cb); pdf.cell(12,6,res,1,0,"C",True); pdf.set_fill_color(255,255,255)
            pdf.cell(58,6,"",1,0,"L"); pdf.cell(20,6,f"{hs}-{aw}",1,1,"C")
        else:
            pdf.cell(58,6,"",1,0,"L")
            pdf.set_fill_color(cr,cg,cb); pdf.cell(12,6,res,1,0,"C",True); pdf.set_fill_color(255,255,255)
            pdf.cell(58,6,f" {home} {hs}-{aw} {away}",1,0,"L"); pdf.cell(20,6,f"{hs}-{aw}",1,1,"C")
    if not partidos:
        pdf.cell(0,6,clean(f"Sin partidos - {team}"),1,align="C"); pdf.ln()
    pdf.ln(4); pdf.set_font("Helvetica","B",11); pdf.set_fill_color(166,166,166)
    pdf.cell(0,8," Lesiones / Bajas / Sancionados (de Comuniazo) ", fill=True, new_x="LMARGIN", new_y="NEXT"); pdf.ln(2)
    lesiones = get_lesiones_equipo(team, tid)
    if not lesiones:
        pdf.set_font("Helvetica","",9); pdf.cell(0,6,clean("Sin lesiones registradas"), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica","B",8); pdf.set_fill_color(60,60,60); pdf.set_text_color(255,255,255)
        pdf.cell(45,6," Jugador",1,fill=True); pdf.cell(15,6,"Pos",1,align="C",fill=True); pdf.cell(70,6," Lesion",1,fill=True); pdf.cell(42,6," Baja",1,align="C",fill=True); pdf.ln(); pdf.set_text_color(0,0,0)
        for i, d in enumerate(lesiones[:10]):
            if i%2==0: pdf.set_fill_color(255,255,255)
            else: pdf.set_fill_color(240,240,240)
            pdf.set_font("Helvetica","B",8); pdf.cell(45,6,clean(f" {d['jugador'][:20]}"),1,fill=True); pdf.set_font("Helvetica","",8); pdf.cell(15,6,clean(d.get("pos","-")),1,align="C",fill=True); pdf.cell(70,6,clean(f" {d['lesion'][:38]}"),1,fill=True); pdf.cell(42,6,clean(f" {d['baja'][:22]}"),1,align="C",fill=True); pdf.ln()

pathlib.Path("informes").mkdir(exist_ok=True); out = f"informes/Informe_LaLiga2_{now_spain.strftime('%Y-%m-%d')}.pdf"; pdf.output(out); print(f"OK: {out}")
