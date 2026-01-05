import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.set_page_config(page_title="Analyse Capacité TV", page_icon="📊", layout="wide")

st.title("📊 Analyse Capacité Horaire TV")

# Sidebar pour upload et configuration
with st.sidebar:
    st.header("📁 Fichiers de données")

    # Upload LOAD (obligatoire)
    uploaded_load = st.file_uploader(
        "1️⃣ Charger LOAD (charges horaires)", 
        type=['csv'], 
        key='load',
        help="Fichier LOAD_XXX.csv avec charges par heure"
    )

    # Upload OCC (obligatoire)
    uploaded_occ = st.file_uploader(
        "2️⃣ Charger OCC (occupation minute)", 
        type=['csv'], 
        key='occ',
        help="Fichier OCC_XXX.csv avec occupation minute par minute"
    )

    st.divider()
    st.header("⚙️ Fichiers optionnels")

    # Upload optionnel R_Capas
    uploaded_rcapas = st.file_uploader(
        "R_Capas (seuils auto)", 
        type=['xlsx', 'xls'], 
        key='rcapas',
        help="Charge automatiquement SUSTAIN et PEAK"
    )

    # Upload optionnel Regulations
    uploaded_regs = st.file_uploader(
        "T_Regulations (croisement)", 
        type=['xlsx', 'xls'], 
        key='regs',
        help="Pour croiser avec les régulations"
    )

# Main content
if uploaded_load is None or uploaded_occ is None:
    st.info("👈 **Commencez par charger les fichiers LOAD et OCC dans la barre latérale**")
    st.stop()

# Lire les fichiers
try:
    # LOAD
    load_df = pd.read_csv(uploaded_load, sep=';')
    tv_load = load_df['ID'].iloc[0]

    # OCC
    occ_df = pd.read_csv(uploaded_occ, sep=';')
    tv_occ = occ_df['ID'].iloc[0]

    # Vérifier que c'est le même TV (avec tolérance)
    if tv_load != tv_occ:
        st.warning(f"⚠️ TV différent détecté : LOAD={tv_load}, OCC={tv_occ}")
        st.info("Continuer l'analyse malgré l'incohérence...")
        # st.stop()  # Désactivé pour continuer

    tv_detected = tv_load
    st.success(f"✅ **TV détecté : {tv_detected}**")

    # Informations sur les données
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📍 Secteur", tv_detected)
    with col2:
        st.metric("📅 Jours (LOAD)", len(load_df))
    with col3:
        st.metric("📅 Jours (OCC)", len(occ_df))
    with col4:
        date_range = f"{load_df['Date'].min()} → {load_df['Date'].max()}"
        st.metric("📆 Période", date_range)

except Exception as e:
    st.error(f"❌ **Erreur lors de la lecture des fichiers :** {e}")
    st.stop()

# Configuration des seuils
st.divider()
st.subheader("🎯 Configuration des seuils")

# Essayer de charger depuis R_Capas si fourni
default_sustain = 0.6
default_peak = 1.0
seuils_source = "Valeurs par défaut"

if uploaded_rcapas:
    try:
        rcapas_df = pd.read_excel(uploaded_rcapas)
        # Chercher le TV dans R_Capas
        tv_row = rcapas_df[rcapas_df['Airspace'] == tv_detected]
        if not tv_row.empty:
            if 'SUSTAIN 11' in rcapas_df.columns:
                default_sustain = float(tv_row['SUSTAIN 11'].iloc[0])
            if 'PEAK 11' in rcapas_df.columns:
                default_peak = float(tv_row['PEAK 11'].iloc[0])
            seuils_source = "R_Capas"
            st.success(f"✅ Seuils récupérés depuis **R_Capas**")
        else:
            st.warning(f"⚠️ TV {tv_detected} non trouvé dans R_Capas")
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire R_Capas : {e}")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    sustain = st.number_input(
        "SUSTAIN 11 (avions/min)", 
        min_value=0, 
        max_value=30,
        value=default_sustain, 
        step=1
    )
with col2:
    peak = st.number_input(
        "PEAK 11 (avions/min)", 
        min_value=0, 
        max_value=30,
        value=default_peak, 
        step=1
    )
with col3:
    st.metric("📌 Source seuils", seuils_source)

if sustain >= peak:
    st.error("⚠️ **SUSTAIN doit être inférieur à PEAK**")
    st.stop()

# Conversion seuils pour différentes granularités
sustain_hourly = sustain * 60
peak_hourly = peak * 60

st.caption(f"💡 Seuils convertis : SUSTAIN = {sustain_hourly:.0f} av/h | PEAK = {peak_hourly:.0f} av/h")

# Mode d'analyse
st.divider()
col1, col2 = st.columns([3, 1])
with col1:
    analysis_type = st.radio(
        "Type d'analyse",
        ["📊 Vue d'ensemble", "🔍 Analyse détaillée jour", "📈 Comparaison LOAD vs OCC"],
        horizontal=True
    )
with col2:
    analyze_btn = st.button("🚀 Analyser", type="primary", use_container_width=True)

# Analyse
if analyze_btn:
    with st.spinner("🔄 Analyse en cours..."):

        # === TRAITEMENT LOAD (charges horaires) ===
        load_cols = [col for col in load_df.columns if ':' in col and '-' in col]

        load_analysis = []
        for idx, row in load_df.iterrows():
            date = row['Date']
            for col in load_cols:
                load_value = row[col]
                hour = int(col.split(':')[0])

                if load_value >= peak_hourly:
                    status = "PEAK"
                elif load_value < sustain_hourly:
                    status = "SOUS-SUSTAIN"
                else:
                    status = "NORMAL"

                load_analysis.append({
                    'Date': date,
                    'Hour': hour,
                    'Slot': col,
                    'Load': load_value,
                    'Status': status
                })

        df_load_analysis = pd.DataFrame(load_analysis)

        # === TRAITEMENT OCC (occupation minute) ===
        minute_cols = [col for col in occ_df.columns if 'Duration 11 Min' in col]

        occ_analysis = []
        for idx, row in occ_df.iterrows():
            date = row['Date']
            for col in minute_cols:
                time_str = col.split(' - ')[0]
                occ_value = row[col]

                if occ_value >= peak:
                    status = "PEAK"
                elif occ_value < sustain:
                    status = "SOUS-SUSTAIN"
                else:
                    status = "NORMAL"

                occ_analysis.append({
                    'Date': date,
                    'Time': time_str,
                    'Occupation': occ_value,
                    'Status': status
                })

        df_occ_analysis = pd.DataFrame(occ_analysis)

        # === AFFICHAGE SELON LE TYPE ===

        if analysis_type == "📊 Vue d'ensemble":
            st.subheader("📈 Statistiques globales")

            # Stats LOAD
            st.markdown("### 🔷 Charges horaires (LOAD)")
            total_slots = len(df_load_analysis)
            slots_above_peak = len(df_load_analysis[df_load_analysis['Status'] == 'PEAK'])
            slots_below_sustain = len(df_load_analysis[df_load_analysis['Status'] == 'SOUS-SUSTAIN'])
            slots_normal = len(df_load_analysis[df_load_analysis['Status'] == 'NORMAL'])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "⚠️ Créneaux > PEAK",
                    f"{(slots_above_peak/total_slots*100):.1f}%",
                    f"{slots_above_peak} créneaux"
                )
            with col2:
                st.metric(
                    "✅ Créneaux normaux",
                    f"{(slots_normal/total_slots*100):.1f}%",
                    f"{slots_normal} créneaux"
                )
            with col3:
                st.metric(
                    "📉 Créneaux < SUSTAIN",
                    f"{(slots_below_sustain/total_slots*100):.1f}%",
                    f"{slots_below_sustain} créneaux"
                )
            with col4:
                avg_load = df_load_analysis['Load'].mean()
                st.metric(
                    "📊 Charge moyenne",
                    f"{avg_load:.1f} av/h"
                )

            # Stats OCC
            st.markdown("### 🔶 Occupation minute (OCC)")
            total_minutes = len(df_occ_analysis)
            minutes_above_peak = len(df_occ_analysis[df_occ_analysis['Status'] == 'PEAK'])
            minutes_below_sustain = len(df_occ_analysis[df_occ_analysis['Status'] == 'SOUS-SUSTAIN'])
            minutes_normal = len(df_occ_analysis[df_occ_analysis['Status'] == 'NORMAL'])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "⚠️ Minutes > PEAK",
                    f"{(minutes_above_peak/total_minutes*100):.1f}%",
                    f"{minutes_above_peak:,} min"
                )
            with col2:
                st.metric(
                    "✅ Minutes normales",
                    f"{(minutes_normal/total_minutes*100):.1f}%",
                    f"{minutes_normal:,} min"
                )
            with col3:
                st.metric(
                    "📉 Minutes < SUSTAIN",
                    f"{(minutes_below_sustain/total_minutes*100):.1f}%",
                    f"{minutes_below_sustain:,} min"
                )
            with col4:
                avg_occ = df_occ_analysis['Occupation'].mean()
                st.metric(
                    "📊 Occupation moyenne",
                    f"{avg_occ:.2f} av/min"
                )

            # Graphiques
            st.markdown("### 📊 Distribution des statuts")
            col1, col2 = st.columns(2)

            with col1:
                fig_load = go.Figure(data=[go.Pie(
                    labels=['> PEAK', 'Normal', '< SUSTAIN'],
                    values=[slots_above_peak, slots_normal, slots_below_sustain],
                    marker=dict(colors=['#ff4b4b', '#00c851', '#ffa000']),
                    hole=0.4
                )])
                fig_load.update_layout(height=350)
                st.plotly_chart(fig_load, use_container_width=True)

            with col2:
                fig_occ = go.Figure(data=[go.Pie(
                    labels=['> PEAK', 'Normal', '< SUSTAIN'],
                    values=[minutes_above_peak, minutes_normal, minutes_below_sustain],
                    marker=dict(colors=['#ff4b4b', '#00c851', '#ffa000']),
                    hole=0.4
                )])
                fig_occ.update_layout(height=350)
                st.plotly_chart(fig_occ, use_container_width=True)

        else:
            st.info("Cliquez '🚀 Analyser' pour voir les résultats !")

        # Export
        st.divider()
        st.markdown("### 💾 Export")
        csv_load = df_load_analysis.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger analyse (CSV)",
            data=csv_load,
            file_name=f"analyse_{tv_detected}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

st.markdown("---")
st.markdown("*Analyse LOAD + OCC - LFEKHN TV*")
