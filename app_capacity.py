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

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📝 Fichiers requis

        #### 1️⃣ LOAD_XXX.csv
        - **Charges horaires** par créneau d'1 heure
        - Format : `0:00-1:00`, `1:00-2:00`...
        - Exemple : `10:00-11:00 = 48 avions`

        #### 2️⃣ OCC_XXX.csv
        - **Occupation minute par minute**
        - Format : `0:00`, `0:01`, `0:02`...
        - Exemple : `10:00 = 7 avions`
        """)

    with col2:
        st.markdown("""
        ### 🎯 Fonctionnalités

        ✅ **Auto-détection** du TV (colonne B)  
        ✅ **Comparaison** charges/occupation  
        ✅ **Analyse** vs seuils SUSTAIN/PEAK  
        ✅ **Détection** des écarts et pics  
        ✅ **Visualisations** interactives  
        ✅ **Export** CSV des résultats  

        ### 🔒 Sécurité
        - Vos fichiers restent **locaux**
        - Aucune donnée **stockée** sur serveur
        """)

    st.stop()

# Lire les fichiers
try:
    # LOAD
    load_df = pd.read_csv(uploaded_load, sep=';')
    tv_load = load_df['ID'].iloc[0]

    # OCC
    occ_df = pd.read_csv(uploaded_occ, sep=';')
    tv_occ = occ_df['ID'].iloc[0]

    # Vérifier que c'est le même TV
    if tv_load != tv_occ:
    st.warning(f"⚠️ TV différent détecté : LOAD={tv_load}, OCC={tv_occ}")
    st.info("Continuer l'analyse malgré l'incohérence...")
    # st.stop()  # Désactivé temporairement

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
            # Colonnes I = PEAK 11, K = SUSTAIN 11
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
        min_value=0.0, 
        max_value=5.0,
        value=default_sustain, 
        step=0.1,
        help="Seuil minimal pour maintenir le secteur ouvert"
    )
with col2:
    peak = st.number_input(
        "PEAK 11 (avions/min)", 
        min_value=0.0, 
        max_value=5.0,
        value=default_peak, 
        step=0.1,
        help="Seuil de dégroupement"
    )
with col3:
    st.metric("📌 Source seuils", seuils_source)

if sustain >= peak:
    st.error("⚠️ **SUSTAIN doit être inférieur à PEAK**")
    st.stop()

# Conversion seuils pour différentes granularités
sustain_hourly = sustain * 60  # avions/heure
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
                # Extraire l'heure de début (ex: "10:00-11:00" → 10)
                hour = int(col.split(':')[0])

                # Statut basé sur charge horaire
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

                # Statut basé sur occupation minute
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
            st.divider()
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

            # Graphiques comparatifs
            st.markdown("### 📊 Distribution des statuts")
            col1, col2 = st.columns(2)

            with col1:
                fig_load = go.Figure(data=[go.Pie(
                    labels=['> PEAK', 'Normal', '< SUSTAIN'],
                    values=[slots_above_peak, slots_normal, slots_below_sustain],
                    marker=dict(colors=['#ff4b4b', '#00c851', '#ffa000']),
                    hole=0.4,
                    title="LOAD (charges horaires)"
                )])
                fig_load.update_layout(height=350)
                st.plotly_chart(fig_load, use_container_width=True)

            with col2:
                fig_occ = go.Figure(data=[go.Pie(
                    labels=['> PEAK', 'Normal', '< SUSTAIN'],
                    values=[minutes_above_peak, minutes_normal, minutes_below_sustain],
                    marker=dict(colors=['#ff4b4b', '#00c851', '#ffa000']),
                    hole=0.4,
                    title="OCC (occupation minute)"
                )])
                fig_occ.update_layout(height=350)
                st.plotly_chart(fig_occ, use_container_width=True)

            # Capacité horaire
            st.markdown("### 🎯 Capacité théorique")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Capacité max", f"{peak_hourly:.0f} av/h")
            with col2:
                utilization = (avg_load / peak_hourly) * 100
                st.metric("Utilisation moyenne", f"{utilization:.1f}%")
            with col3:
                st.metric("Marge disponible", f"{peak_hourly - avg_load:.0f} av/h")

        elif analysis_type == "🔍 Analyse détaillée jour":
            st.divider()
            st.subheader("📅 Analyse par jour")

            # Sélection date
            available_dates = sorted(load_df['Date'].unique())
            selected_date = st.selectbox("Sélectionner une date", available_dates)

            # Filtrer les données
            df_load_day = df_load_analysis[df_load_analysis['Date'] == selected_date]
            df_occ_day = df_occ_analysis[df_occ_analysis['Date'] == selected_date]

            # Graphique LOAD (horaire)
            st.markdown("### 📊 Charges horaires (LOAD)")
            fig_load = go.Figure()

            fig_load.add_trace(go.Bar(
                x=df_load_day['Hour'],
                y=df_load_day['Load'],
                name='Charge',
                marker_color='#1f77b4',
                hovertemplate='Heure: %{x}h<br>Charge: %{y} av<extra></extra>'
            ))

            fig_load.add_hline(y=peak_hourly, line_dash="dash", line_color="red",
                              annotation_text=f"PEAK ({peak_hourly:.0f} av/h)")
            fig_load.add_hline(y=sustain_hourly, line_dash="dash", line_color="orange",
                              annotation_text=f"SUSTAIN ({sustain_hourly:.0f} av/h)")

            fig_load.update_layout(
                title=f"Charges horaires - {selected_date}",
                xaxis_title="Heure",
                yaxis_title="Charge (avions/heure)",
                height=400
            )
            st.plotly_chart(fig_load, use_container_width=True)

            # Graphique OCC (minute)
            st.markdown("### 📊 Occupation minute par minute (OCC)")

            # Sous-échantillonner pour lisibilité (toutes les 10 minutes)
            df_occ_day_sample = df_occ_day.iloc[::10]

            fig_occ = go.Figure()

            fig_occ.add_trace(go.Scatter(
                x=df_occ_day_sample['Time'],
                y=df_occ_day_sample['Occupation'],
                mode='lines+markers',
                name='Occupation',
                line=dict(color='#2ca02c', width=2),
                marker=dict(size=4),
                hovertemplate='%{x}<br>Occupation: %{y} av<extra></extra>'
            ))

            fig_occ.add_hline(y=peak, line_dash="dash", line_color="red",
                             annotation_text=f"PEAK ({peak:.1f} av/min)")
            fig_occ.add_hline(y=sustain, line_dash="dash", line_color="orange",
                             annotation_text=f"SUSTAIN ({sustain:.1f} av/min)")

            fig_occ.update_layout(
                title=f"Occupation minute - {selected_date}",
                xaxis_title="Heure",
                yaxis_title="Occupation (avions/minute)",
                height=400
            )

            # Afficher un point toutes les heures
            hours_display = [f"{h}:00" for h in range(0, 24)]
            fig_occ.update_xaxes(
                tickmode='array',
                tickvals=hours_display,
                ticktext=hours_display
            )

            st.plotly_chart(fig_occ, use_container_width=True)

            # Stats du jour
            st.markdown("### 📈 Statistiques de la journée")
            col1, col2, col3 = st.columns(3)
            with col1:
                max_load = df_load_day['Load'].max()
                peak_hour = df_load_day[df_load_day['Load'] == max_load]['Hour'].iloc[0]
                st.metric("Pic LOAD", f"{max_load:.0f} av", f"à {peak_hour}h")
            with col2:
                max_occ = df_occ_day['Occupation'].max()
                peak_time = df_occ_day[df_occ_day['Occupation'] == max_occ]['Time'].iloc[0]
                st.metric("Pic OCC", f"{max_occ:.0f} av", f"à {peak_time}")
            with col3:
                daily_total = df_load_day['Load'].sum()
                st.metric("Total journée", f"{daily_total:.0f} av")

        else:  # Comparaison LOAD vs OCC
            st.divider()
            st.subheader("📈 Comparaison LOAD vs OCC")

            st.info("💡 **LOAD** = Charges agrégées par heure | **OCC** = Occupation détaillée minute par minute")

            # Sélection date
            available_dates = sorted(load_df['Date'].unique())
            selected_date = st.selectbox("Sélectionner une date", available_dates)

            # Données du jour
            df_load_day = df_load_analysis[df_load_analysis['Date'] == selected_date]
            df_occ_day = df_occ_analysis[df_occ_analysis['Date'] == selected_date]

            # Agréger OCC par heure pour comparaison
            df_occ_day['Hour'] = df_occ_day['Time'].apply(lambda x: int(x.split(':')[0]))
            occ_hourly = df_occ_day.groupby('Hour')['Occupation'].agg(['mean', 'max', 'min']).reset_index()
            occ_hourly['mean_hourly'] = occ_hourly['mean'] * 60  # Convertir en av/h
            occ_hourly['max_hourly'] = occ_hourly['max'] * 60
            occ_hourly['min_hourly'] = occ_hourly['min'] * 60

            # Graphique comparatif
            fig = go.Figure()

            # LOAD (barres)
            fig.add_trace(go.Bar(
                x=df_load_day['Hour'],
                y=df_load_day['Load'],
                name='LOAD (charge horaire)',
                marker_color='#1f77b4',
                opacity=0.7
            ))

            # OCC moyenne (ligne)
            fig.add_trace(go.Scatter(
                x=occ_hourly['Hour'],
                y=occ_hourly['mean_hourly'],
                name='OCC moyenne (×60)',
                mode='lines+markers',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=8)
            ))

            # Bandes min/max OCC
            fig.add_trace(go.Scatter(
                x=occ_hourly['Hour'],
                y=occ_hourly['max_hourly'],
                name='OCC max',
                mode='lines',
                line=dict(color='rgba(44, 160, 44, 0.3)', dash='dash'),
                showlegend=False
            ))

            fig.add_trace(go.Scatter(
                x=occ_hourly['Hour'],
                y=occ_hourly['min_hourly'],
                name='OCC min',
                mode='lines',
                line=dict(color='rgba(44, 160, 44, 0.3)', dash='dash'),
                fill='tonexty',
                fillcolor='rgba(44, 160, 44, 0.1)',
                showlegend=False
            ))

            # Seuils
            fig.add_hline(y=peak_hourly, line_dash="dash", line_color="red",
                         annotation_text=f"PEAK ({peak_hourly:.0f})")
            fig.add_hline(y=sustain_hourly, line_dash="dash", line_color="orange",
                         annotation_text=f"SUSTAIN ({sustain_hourly:.0f})")

            fig.update_layout(
                title=f"Comparaison LOAD vs OCC - {selected_date}",
                xaxis_title="Heure",
                yaxis_title="Avions/heure",
                height=500,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Analyse des écarts
            st.markdown("### 🔍 Analyse des écarts")

            # Merger les données
            comparison = df_load_day.merge(
                occ_hourly[['Hour', 'mean_hourly', 'max_hourly']], 
                on='Hour', 
                how='left'
            )
            comparison['Écart'] = comparison['Load'] - comparison['mean_hourly']
            comparison['Écart %'] = (comparison['Écart'] / comparison['Load'] * 100).round(1)

            # Identifier les écarts significatifs (>10%)
            significant_gaps = comparison[abs(comparison['Écart %']) > 10]

            if len(significant_gaps) > 0:
                st.warning(f"⚠️ **{len(significant_gaps)} créneaux avec écart > 10%**")

                st.dataframe(
                    significant_gaps[['Hour', 'Load', 'mean_hourly', 'Écart', 'Écart %']].rename(columns={
                        'Hour': 'Heure',
                        'Load': 'LOAD (av/h)',
                        'mean_hourly': 'OCC moy (av/h)',
                        'Écart': 'Écart (av/h)',
                        'Écart %': 'Écart %'
                    }),
                    use_container_width=True
                )
            else:
                st.success("✅ **Aucun écart significatif détecté** (< 10%)")

            # Stats comparatives
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_ecart = comparison['Écart'].mean()
                st.metric("Écart moyen", f"{avg_ecart:.1f} av/h")
            with col2:
                max_ecart = comparison['Écart'].max()
                st.metric("Écart max", f"{max_ecart:.1f} av/h")
            with col3:
                correlation = comparison['Load'].corr(comparison['mean_hourly'])
                st.metric("Corrélation", f"{correlation:.2f}")

        # Export CSV
        st.divider()
        st.markdown("### 💾 Export des données")

        col1, col2 = st.columns(2)
        with col1:
            csv_load = df_load_analysis.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger analyse LOAD (CSV)",
                data=csv_load,
                file_name=f"analyse_load_{tv_detected}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        with col2:
            csv_occ = df_occ_analysis.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger analyse OCC (CSV)",
                data=csv_occ,
                file_name=f"analyse_occ_{tv_detected}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

st.markdown("---")
st.markdown("*Analyse de capacité horaire - Confrontation LOAD vs OCC avec seuils SUSTAIN/PEAK*")
