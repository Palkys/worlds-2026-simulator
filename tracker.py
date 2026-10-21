import streamlit as st
import json
import os

st.set_page_config(page_title="Worlds 2026 Swiss Bracket", layout="wide")

STATE_FILE = "swiss_state.json"

# 1. NAČTENÍ ULOŽENÉHO STAVU PŘI STARTU
if "loaded" not in st.session_state:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                for k, v in saved_data.items():
                    st.session_state[k] = v
        except:
            pass # Pokud by byl soubor poškozený, ignorujeme ho
    st.session_state["loaded"] = True

# Hlavička s tlačítkem pro Reset
col_title, col_btn = st.columns([5, 1])
with col_title:
    st.title("🏆 LoL Worlds 2026 - Kompletní Swiss Stage")
with col_btn:
    # Tlačítko pro vymazání celé historie (reset aplikace i souboru)
    if st.button("🔄 Začít znovu", use_container_width=True):
        st.session_state.clear()
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        st.rerun()

st.write("Vyberte vítěze z každého zápasu. Váš postup se automaticky ukládá – i po obnovení stránky (F5) zůstane vše vyplněné.")

# 1. kolo (pevně dané)
round_1_matches = [
    ("Gen.G", "Invictus Gaming"), ("Team Liquid", "CTBC Flying Oyster"),
    ("Anyone's Legend", "Karmine Corp"), ("G2 Esports", "Dplus KIA"),
    ("Hanwha Life Esports", "Top Esports"), ("LOS", "T1"),
    ("Team Secret Whales", "LYON"), ("Bilibili Gaming", "Movistar KOI")
]

all_teams = [t for match in round_1_matches for t in match]

# Dynamické proměnné pro skóre a historii
scores = {team: {'W': 0, 'L': 0} for team in all_teams}
history = {team: set() for team in all_teams}

def update_stats(winner, loser):
    scores[winner]['W'] += 1
    scores[loser]['L'] += 1
    history[winner].add(loser)
    history[loser].add(winner)

# Vykreslení 1. kola
def render_pool(pool_name, matches, round_num):
    st.markdown(f"### {pool_name}")
    all_resolved = True
    
    for i, match in enumerate(matches):
        with st.container(border=True):
            # U první skupiny se index None použije jen, pokud hodnota není v session_state
            key = f"r{round_num}_{pool_name}_{i}"
            winner = st.radio(
                f"**Zápas {i+1}**", 
                match, 
                key=key, 
                index=None if key not in st.session_state else (0 if st.session_state[key] == match[0] else 1),
                horizontal=True
            )
            if winner:
                loser = match[1] if winner == match[0] else match[0]
                update_stats(winner, loser)
            else:
                all_resolved = False
                
    return all_resolved

# Vykreslení manuálních skupin s filtrací a ochranou proti odvetám
def render_manual_pool(pool_name, teams, round_num):
    st.markdown(f"### {pool_name}")
    num_matches = len(teams) // 2
    
    if num_matches == 0:
        return True

    st.caption("Sestavte zápasy (týmy už nemohou hrát proti těm, které dříve potkaly):")
    
    def get_selected_in_pool():
        selected = set()
        for i in range(num_matches):
            for j in (1, 2):
                val = st.session_state.get(f"sel_{round_num}_{pool_name}_{i}_{j}", "---")
                if val != "---":
                    selected.add(val)
        return selected

    matches = []
    all_matchups_valid = True
    
    # UI pro výběr dvojic
    for i in range(num_matches):
        c1, c2, c3 = st.columns([3, 1, 3])
        
        # Tým 1
        key1 = f"sel_{round_num}_{pool_name}_{i}_1"
        curr1 = st.session_state.get(key1, "---")
        used_teams = get_selected_in_pool()
        avail1 = ["---"] + sorted(list(set(teams) - used_teams | ({curr1} if curr1 != "---" else set())))
        
        with c1:
            t1 = st.selectbox("Tým 1", avail1, key=key1, label_visibility="collapsed")
            
        with c2:
            st.markdown("<div style='text-align: center; margin-top: 5px;'>vs</div>", unsafe_allow_html=True)
            
        # Tým 2
        key2 = f"sel_{round_num}_{pool_name}_{i}_2"
        curr2 = st.session_state.get(key2, "---")
        used_teams = get_selected_in_pool()
        avail2 = ["---"] + sorted(list(set(teams) - used_teams | ({curr2} if curr2 != "---" else set())))
        
        with c3:
            t2 = st.selectbox("Tým 2", avail2, key=key2, label_visibility="collapsed")
            
        if t1 != "---" and t2 != "---":
            if t2 in history[t1]:
                st.error(f"❌ Odveta! Týmy **{t1}** a **{t2}** už spolu na turnaji hrály. Změňte los.")
                all_matchups_valid = False
            else:
                matches.append((t1, t2))
        else:
            all_matchups_valid = False
            
    all_resolved = False
    
    if all_matchups_valid and len(matches) == num_matches:
        st.caption("Vyberte vítěze:")
        all_resolved = True
        for i, match in enumerate(matches):
            with st.container(border=True):
                key = f"rm_{round_num}_{pool_name}_{i}"
                winner = st.radio(
                    f"**Zápas {i+1}**", 
                    match, 
                    key=key, 
                    index=None if key not in st.session_state else (0 if st.session_state[key] == match[0] else 1), 
                    horizontal=True
                )
                
                if winner:
                    loser = match[1] if winner == match[0] else match[0]
                    update_stats(winner, loser)
                else:
                    all_resolved = False
                    
    return all_resolved


st.divider()

# --- KOLO 1 ---
st.header("Kolo 1")
done_1 = render_pool("Skupina 0-0", round_1_matches, 1)

# HLAVNÍ LOGIKA KASKÁDY (pokud není kolo hotové, uložíme stav a zastavíme běh)
if not done_1:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in st.session_state.items() if k != "loaded"}, f)
    st.stop()

st.divider()

# --- KOLO 2 ---
st.header("Kolo 2")
pool_1_0 = [t for t, s in scores.items() if s['W'] == 1 and s['L'] == 0]
pool_0_1 = [t for t, s in scores.items() if s['W'] == 0 and s['L'] == 1]

col1, col2 = st.columns(2)
with col1:
    done_2_1 = render_manual_pool("Skupina 1-0 (Vítězové)", pool_1_0, 2)
with col2:
    done_2_2 = render_manual_pool("Skupina 0-1 (Poražení)", pool_0_1, 2)

if not (done_2_1 and done_2_2):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in st.session_state.items() if k != "loaded"}, f)
    st.stop()

st.divider()

# --- KOLO 3 ---
st.header("Kolo 3")
pool_2_0 = [t for t, s in scores.items() if s['W'] == 2 and s['L'] == 0]
pool_1_1 = [t for t, s in scores.items() if s['W'] == 1 and s['L'] == 1]
pool_0_2 = [t for t, s in scores.items() if s['W'] == 0 and s['L'] == 2]

col1, col2, col3 = st.columns(3)
with col1:
    done_3_1 = render_manual_pool("Skupina 2-0 (Postupové)", pool_2_0, 3)
with col2:
    done_3_2 = render_manual_pool("Skupina 1-1 (Střed)", pool_1_1, 3)
with col3:
    done_3_3 = render_manual_pool("Skupina 0-2 (Eliminační)", pool_0_2, 3)

if not (done_3_1 and done_3_2 and done_3_3):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in st.session_state.items() if k != "loaded"}, f)
    st.stop()

st.divider()

# --- KOLO 4 ---
st.header("Kolo 4")
pool_2_1 = [t for t, s in scores.items() if s['W'] == 2 and s['L'] == 1]
pool_1_2 = [t for t, s in scores.items() if s['W'] == 1 and s['L'] == 2]

col1, col2 = st.columns(2)
with col1:
    done_4_1 = render_manual_pool("Skupina 2-1 (Postupové)", pool_2_1, 4)
with col2:
    done_4_2 = render_manual_pool("Skupina 1-2 (Eliminační)", pool_1_2, 4)

if not (done_4_1 and done_4_2):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in st.session_state.items() if k != "loaded"}, f)
    st.stop()

st.divider()

# --- KOLO 5 ---
st.header("Kolo 5")
pool_2_2 = [t for t, s in scores.items() if s['W'] == 2 and s['L'] == 2]

done_5 = render_manual_pool("Skupina 2-2 (Rozhodující zápasy)", pool_2_2, 5)

if not done_5:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in st.session_state.items() if k != "loaded"}, f)
    st.stop()

st.divider()

# --- FINÁLNÍ VÝSLEDKY & EXPORT ---
st.header("🏁 Konec Swiss Stage - Výsledky")

col_adv, col_elim = st.columns(2)
with col_adv:
    st.success("✅ Týmy postupující do Play-off (Knockout Stage)")
    for t, s in scores.items():
        if s['W'] == 3:
            st.write(f"**{t}** (Skóre: 3-{s['L']})")

with col_elim:
    st.error("❌ Týmy vyřazené z turnaje")
    for t, s in scores.items():
        if s['L'] == 3:
            st.write(f"**{t}** (Skóre: {s['W']}-3)")

st.divider()
st.subheader("📋 Export pro sdílení")

export_text = "🏆 **Moje LoL Worlds 2026 Swiss Pick'em** 🏆\n\n"
export_text += "🟢 **Postupují (3-0):** " + ", ".join([t for t, s in scores.items() if s['W'] == 3 and s['L'] == 0]) + "\n"
export_text += "🟡 **Postupují (3-1):** " + ", ".join([t for t, s in scores.items() if s['W'] == 3 and s['L'] == 1]) + "\n"
export_text += "🟠 **Postupují (3-2):** " + ", ".join([t for t, s in scores.items() if s['W'] == 3 and s['L'] == 2]) + "\n\n"
export_text += "🔴 **Vyřazeni (2-3):** " + ", ".join([t for t, s in scores.items() if s['W'] == 2 and s['L'] == 3]) + "\n"
export_text += "🟤 **Vyřazeni (1-3):** " + ", ".join([t for t, s in scores.items() if s['W'] == 1 and s['L'] == 3]) + "\n"
export_text += "⚫ **Vyřazeni (0-3):** " + ", ".join([t for t, s in scores.items() if s['W'] == 0 and s['L'] == 3])

st.code(export_text, language="markdown")

# Uložení stavu na úplném konci (když je celá stage hotová)
with open(STATE_FILE, "w", encoding="utf-8") as f:
    json.dump({k: v for k, v in st.session_state.items() if k != "loaded"}, f)