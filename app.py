import streamlit as st
import pandas as pd
import re
from collections import Counter
from datetime import datetime, timedelta

st.set_page_config(
    page_title="INDIVIDUAL 2",
    page_icon="🧠",
    layout="centered"
)

GRANJITA_ID = "1JpJgdyqu3HP4TlNyDocQ7WQjnsDfkUMP4Aj3q97TmHY"
LOTTO_ID = "1Wm31ULE_YckLHEaek8Kre42UMdglkli-QeLpHxzFf-I"

ANIMALITOS_DICT = {
    0: "Delfín", 1: "Carnero", 2: "Toro", 3: "Ciempiés", 4: "Alacrán",
    5: "León", 6: "Rana", 7: "Perico", 8: "Ratón", 9: "Águila",
    10: "Tigre", 11: "Gato", 12: "Caballo", 13: "Mono", 14: "Paloma",
    15: "Zorro", 16: "Oso", 17: "Pavo", 18: "Burro", 19: "Chivo",
    20: "Cochino", 21: "Gallo", 22: "Camello", 23: "Cebra", 24: "Iguana",
    25: "Gallina", 26: "Vaca", 27: "Perro", 28: "Zamuro", 29: "Elefante",
    30: "Caimán", 31: "Lapa", 32: "Ardilla", 33: "Pescado", 34: "Venado",
    35: "Jirafa", 36: "Culebra", 100: "Ballena"
}

DIAS = {0: "LUNES", 1: "MARTES", 2: "MIÉRCOLES", 3: "JUEVES", 4: "VIERNES", 5: "SÁBADO", 6: "DOMINGO"}

HORAS_RANGO = list(range(8, 20))


def ahora_venezuela():
    return datetime.utcnow() - timedelta(hours=4)


def fmt_num(n):
    if n == 100: return "00"
    if n == 0: return "0"
    return f"{n:02d}"


def extraer_hora(hora_str):
    m = re.match(r'^(\d+):(\d+)\s*(AM|PM)$', str(hora_str).strip().upper())
    if not m: return 99
    h = int(m.group(1))
    suf = m.group(3)
    if suf == "AM":
        if h == 12: h = 0
    else:
        if h != 12: h += 12
    return h


def formatear_hora(hora_num):
    if hora_num == 0: return "12:00 AM"
    if hora_num < 12: return f"{hora_num:02d}:00 AM"
    if hora_num == 12: return "12:00 PM"
    return f"{hora_num-12:02d}:00 PM"


@st.cache_data(ttl=120)
def cargar_hoja(sheet_id, nombre):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df_raw = pd.read_csv(url, header=None)
        filas_enc = []
        for f in range(len(df_raw)):
            v = str(df_raw.iloc[f, 0]).strip().lower()
            if v == "hora":
                filas_enc.append(f)
        registros = []
        for idx, fe in enumerate(filas_enc):
            ff = filas_enc[idx + 1] if idx + 1 < len(filas_enc) else len(df_raw)
            fechas_col = {}
            for col in range(1, len(df_raw.columns)):
                v = str(df_raw.iloc[fe, col]).strip()
                if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', v):
                    try:
                        fd = pd.to_datetime(v, format="%d/%m/%Y", errors="coerce")
                        if pd.notna(fd): fechas_col[col] = fd
                    except: pass
            ffd = min(ff, fe + 13)
            for col, fd in fechas_col.items():
                for fila in range(fe + 1, ffd):
                    hv = str(df_raw.iloc[fila, 0]).strip()
                    v = str(df_raw.iloc[fila, col]).strip()
                    if not v or v.lower() == "nan" or v.lower() == "hora":
                        continue
                    m = re.search(r'\((\d+)\)', v)
                    if m:
                        ns = m.group(1)
                        n = 100 if ns == "00" else int(ns)
                        hora_n = extraer_hora(hv)
                        if hora_n == 99:
                            continue
                        registros.append({
                            "fecha_dt": fd,
                            "fecha": fd.strftime("%d/%m/%Y"),
                            "hora_num": hora_n,
                            "numero": n,
                            "loteria": nombre
                        })
        df = pd.DataFrame(registros)
        if not df.empty:
            df = df.sort_values(["fecha_dt", "hora_num"], kind="stable").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error {nombre}: {e}")
        return pd.DataFrame()


def obtener_semana_actual(hoy):
    dia_semana = hoy.weekday()
    lunes = hoy - timedelta(days=dia_semana)
    dias = []
    for j in range(7):
        d = lunes + timedelta(days=j)
        if d <= hoy:
            dias.append(d)
    return dias


def analizar_semana(df_g, df_l, dias_semana):
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_semana]
    g = df_g[df_g["fecha"].isin(fechas_str)]
    l = df_l[df_l["fecha"].isin(fechas_str)]
    comb = pd.concat([g, l], ignore_index=True)
    if comb.empty:
        return Counter()
    return Counter(comb["numero"].tolist())


def elegir_inteligente(df_g, df_l, dias_semana, hoy_str, hora):
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_semana]

    g_sem = df_g[df_g["fecha"].isin(fechas_str)]
    l_sem = df_l[df_l["fecha"].isin(fechas_str)]
    comb_sem = pd.concat([g_sem, l_sem], ignore_index=True)

    g_h = df_g[(df_g["fecha"].isin(fechas_str)) & (df_g["hora_num"] == hora)]
    l_h = df_l[(df_l["fecha"].isin(fechas_str)) & (df_l["hora_num"] == hora)]
    comb_h = pd.concat([g_h, l_h], ignore_index=True)

    g_hoy = df_g[df_g["fecha"] == hoy_str]
    l_hoy = df_l[df_l["fecha"] == hoy_str]
    comb_hoy = pd.concat([g_hoy, l_hoy], ignore_index=True)

    if comb_sem.empty:
        return [], "Sin data"

    conteo_hora = Counter(comb_h["numero"].tolist()) if not comb_h.empty else Counter()
    conteo_semana = Counter(comb_sem["numero"].tolist())
    conteo_hoy = Counter(comb_hoy["numero"].tolist()) if not comb_hoy.empty else Counter()

    scores = {}
    for num in ANIMALITOS_DICT.keys():
        s = 0
        s += conteo_hora.get(num, 0) * 5
        s += conteo_semana.get(num, 0) * 1

        veces_hoy = conteo_hoy.get(num, 0)
        if veces_hoy >= 2:
            s -= 8
        elif veces_hoy == 1:
            s -= 2

        if veces_hoy == 0 and conteo_semana.get(num, 0) >= 3:
            s += 3

        scores[num] = s

    ordenados = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = [n for n, sc in ordenados[:3] if sc > 0]

    if not top:
        return [], "Sin candidatos"

    if len(top) >= 3:
        s1 = scores[top[0]]
        s2 = scores[top[1]]
        s3 = scores[top[2]]
        if s3 >= s2 * 0.85 and s3 >= 3:
            return top[:3], "3 animalitos"
    return top[:2], "2 animalitos"


def calcular_fijos_dia_v2(df_g, df_l, dias_semana, hoy_str):
    fechas_str = [d.strftime("%d/%m/%Y") for d in dias_semana]
    g_sem = df_g[df_g["fecha"].isin(fechas_str)]
    l_sem = df_l[df_l["fecha"].isin(fechas_str)]
    comb_sem = pd.concat([g_sem, l_sem], ignore_index=True)

    g_hoy = df_g[df_g["fecha"] == hoy_str]
    l_hoy = df_l[df_l["fecha"] == hoy_str]
    comb_hoy = pd.concat([g_hoy, l_hoy], ignore_index=True)

    conteo_semana = Counter(comb_sem["numero"].tolist())
    conteo_hoy = Counter(comb_hoy["numero"].tolist()) if not comb_hoy.empty else Counter()

    scores = {}
    for num in ANIMALITOS_DICT.keys():
        s = conteo_semana.get(num, 0)
        veces_hoy = conteo_hoy.get(num, 0)
        if veces_hoy >= 2:
            s -= 5
        scores[num] = s

    ordenados = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [n for n, _ in ordenados[:3]]


def mostrar_dia(df_g, df_l, fecha_str, nombre_dia):
    g_dia = df_g[df_g["fecha"] == fecha_str]
    l_dia = df_l[df_l["fecha"] == fecha_str]
    if g_dia.empty and l_dia.empty:
        return False
    st.markdown(f"**{nombre_dia} {fecha_str}**")
    horas = set()
    for df_dia in [g_dia, l_dia]:
        if not df_dia.empty:
            horas.update(df_dia["hora_num"].unique())
    for hora_num in sorted(horas):
        lineas = []
        for df_dia, letra in [(g_dia, "G"), (l_dia, "L")]:
            if not df_dia.empty:
                fila = df_dia[df_dia["hora_num"] == hora_num]
                if not fila.empty:
                    num = int(fila.iloc[0]["numero"])
                    lineas.append(f"{fmt_num(num)} {ANIMALITOS_DICT[num]} ({letra})")
        if lineas:
            st.write(f"**{formatear_hora(hora_num)}** → {' · '.join(lineas)}")
    st.markdown("")
    return True


def main():
    st.title("🧠 INDIVIDUAL 2")
    st.caption("Lógica humana · Fijos del Día · Granjita + Lotto")

    if st.button("🔄 Recargar datos"):
        st.cache_data.clear()
        st.rerun()

    with st.spinner("Leyendo las 2 loterías..."):
        df_g = cargar_hoja(GRANJITA_ID, "GRANJITA")
        df_l = cargar_hoja(LOTTO_ID, "LOTTO")

    if df_g.empty or df_l.empty:
        st.error("No se pudieron cargar las loterías.")
        return

    ahora = ahora_venezuela()
    hoy = ahora.date()
    hoy_str = hoy.strftime("%d/%m/%Y")
    hora_actual = ahora.hour
    minuto_actual = ahora.minute

    proxima_hora = None
    for h in HORAS_RANGO:
        if h > hora_actual:
            proxima_hora = h
            break
        elif h == hora_actual and minuto_actual >= 55:
            if h + 1 in HORAS_RANGO:
                proxima_hora = h + 1
                break

    # ÚLTIMO RESULTADO
    st.markdown("## 🎯 ÚLTIMO RESULTADO")

    g_hoy = df_g[df_g["fecha"] == hoy_str]
    l_hoy = df_l[df_l["fecha"] == hoy_str]

    ult_hora_g = int(g_hoy["hora_num"].max()) if not g_hoy.empty else None
    ult_hora_l = int(l_hoy["hora_num"].max()) if not l_hoy.empty else None
    ult_hora_comun = max([h for h in [ult_hora_g, ult_hora_l] if h is not None], default=None)

    if ult_hora_comun is not None:
        st.markdown(f"**🕐 {formatear_hora(ult_hora_comun)}**")
        fila_g = g_hoy[g_hoy["hora_num"] == ult_hora_comun] if not g_hoy.empty else pd.DataFrame()
        fila_l = l_hoy[l_hoy["hora_num"] == ult_hora_comun] if not l_hoy.empty else pd.DataFrame()

        col1, col2 = st.columns(2)
        with col1:
            if not fila_g.empty:
                num_g = int(fila_g.iloc[0]["numero"])
                st.info(f"🏦 **GRANJITA**\n\n{fmt_num(num_g)} {ANIMALITOS_DICT[num_g]}")
            else:
                st.warning("🏦 GRANJITA\n\nSin resultado")
        with col2:
            if not fila_l.empty:
                num_l = int(fila_l.iloc[0]["numero"])
                st.info(f"🏦 **LOTTO**\n\n{fmt_num(num_l)} {ANIMALITOS_DICT[num_l]}")
            else:
                st.warning("🏦 LOTTO\n\nSin resultado")

    minutos_restantes = 60 - minuto_actual if proxima_hora else 0
    st.info(f"📊 Data: {len(df_g) + len(df_l)} sorteos · 🕐 {ahora.strftime('%H:%M')} · Próxima hora en {minutos_restantes} min")

    dias_semana = obtener_semana_actual(hoy)
    conteo_sem = analizar_semana(df_g, df_l, dias_semana)

    # FIJOS DEL DÍA V2
    st.markdown("---")
    st.markdown("## 🏆 FIJOS DEL DÍA (Lógica Inteligente)")
    st.caption("Los 3 con mejor patrón")

    fijos = calcular_fijos_dia_v2(df_g, df_l, dias_semana, hoy_str)
    for num in fijos:
        veces = conteo_sem.get(num, 0)
        st.success(f"**{fmt_num(num)} {ANIMALITOS_DICT[num]}** — {veces} veces esta semana")

    # PRÓXIMA JUGADA
    st.markdown("---")
    st.markdown("## 🎯 PRÓXIMA JUGADA")

    if proxima_hora is None:
        st.warning("Ya terminó el día. Esperá mañana.")
    else:
        st.markdown(f"### ⏰ Para las **{formatear_hora(proxima_hora)}**")

        elegidos, razon = elegir_inteligente(df_g, df_l, dias_semana, hoy_str, proxima_hora)

        repes_hoy = Counter(g_hoy["numero"].tolist() + l_hoy["numero"].tolist())

        if not elegidos:
            st.warning("No hay candidatos.")
        else:
            if len(elegidos) == 1:
                num = elegidos[0]
                veces = conteo_sem.get(num, 0)
                gastado = " ⚠️ GASTADO" if repes_hoy.get(num, 0) >= 2 else ""
                st.success(f"## 🔥 {fmt_num(num)} {ANIMALITOS_DICT[num]}{gastado}\n\n**MUY FUERTE** ({veces} veces esta semana)")
            elif len(elegidos) == 3:
                st.warning("### 🎯 3 ANIMALITOS")
                for num in elegidos:
                    veces = conteo_sem.get(num, 0)
                    repes = repes_hoy.get(num, 0)
                    gastado = f" ⚠️ (ya salió {repes}x hoy)" if repes >= 2 else ""
                    st.markdown(f"- **{fmt_num(num)} {ANIMALITOS_DICT[num]}** ({veces} veces){gastado}")
            else:
                st.info("### 🎯 2 ANIMALITOS")
                for num in elegidos:
                    veces = conteo_sem.get(num, 0)
                    repes = repes_hoy.get(num, 0)
                    gastado = f" ⚠️ (ya salió {repes}x hoy)" if repes >= 2 else ""
                    st.markdown(f"- **{fmt_num(num)} {ANIMALITOS_DICT[num]}** ({veces} veces){gastado}")

    # HISTORIAL DE HOY
    st.markdown("---")
    st.markdown("## 📊 HISTORIAL DE HOY")

    aciertos_simples = 0
    total_horas = 0

    for hora in HORAS_RANGO:
        g_h = g_hoy[g_hoy["hora_num"] == hora] if not g_hoy.empty else pd.DataFrame()
        l_h = l_hoy[l_hoy["hora_num"] == hora] if not l_hoy.empty else pd.DataFrame()

        if g_h.empty and l_h.empty:
            continue

        total_horas += 1
        elegidos, _ = elegir_inteligente(df_g, df_l, dias_semana, hoy_str, hora)

        nums_salidos = set()
        if not g_h.empty:
            nums_salidos.add(int(g_h.iloc[0]["numero"]))
        if not l_h.empty:
            nums_salidos.add(int(l_h.iloc[0]["numero"]))

        acierto = sum(1 for n in elegidos if n in nums_salidos)
        if acierto > 0:
            aciertos_simples += 1

        if acierto == 0:
            emoji = "❌"
        elif acierto == 1:
            emoji = "✅"
        else:
            emoji = "✅✅"

        pred_str = " + ".join([f"{fmt_num(n)}" for n in elegidos])
        salio_str = " · ".join([f"{fmt_num(n)} {ANIMALITOS_DICT[n]}" for n in sorted(nums_salidos)])

        st.write(f"**{emoji} {formatear_hora(hora)}** · Dijo: {pred_str} · Salió: {salio_str}")

    st.markdown("---")
    st.markdown(f"## 📈 DESEMPEÑO DEL DÍA")
    st.markdown(f"### ✅ {aciertos_simples} aciertos de {total_horas} horas")
    if total_horas > 0:
        pct = aciertos_simples / total_horas * 100
        st.markdown(f"### 📊 {pct:.1f}% de acierto")

    # VISTA DÍA POR DÍA
    st.markdown("---")
    st.markdown("## 📅 ANÁLISIS DÍA POR DÍA")
    for dia in dias_semana:
        fecha_str = dia.strftime("%d/%m/%Y")
        nombre = DIAS[dia.weekday()]
        mostrar_dia(df_g, df_l, fecha_str, nombre)


if __name__ == "__main__":
    main()
