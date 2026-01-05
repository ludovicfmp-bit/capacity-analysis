import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time

st.set_page_config(page_title="Analyse Capacité TV", page_icon="📊", layout="wide")

st.title("📊 Analyse Capacité Horaire TV")

# Sidebar pour upload et configuration
with st.sidebar:
    st.header("📁 Fichiers")

    # Upload OCC_TV
    uploaded_occ = st.file_uploader("Charger fichier OCC_TV", type=['csv'], key='occ')

    # Upload optionnel R_Capas
    uploaded_rcapas = st.file_uploader("Charger R_Capas (optionnel)", type=['xlsx', 'xls'], key='rcapas')

    # Upload optionnel Regulations
    uploaded_regs = st.file_uploader("Charger T_Regulations (optionnel)", type=['xlsx', 'xls'], key='regs')

# Main content
if uploaded_occ is None:
    st.info("👈 Commencez par charger un fichier OCC_TV dans la barre latérale")
    st.markdown("""
    ### 📝 Instructions
    1. **Chargez** votre fichier OCC_TV (format CSV)
    2. L'app **détectera automatiquement** le TV (colonne B)
    3. Configurez les **seuils** SUSTAIN et PEAK
    4. Lancez l'**analyse** !

    #### 🎯 Optionnel
    - Chargez **R_Capas** pour récupérer automatiquement les seuils
    - Chargez **T_Regulations** pour croiser avec les régulations
    """)
    st.stop()

# Lire le fichier OCC
try:
    occ_df = pd.read_csv(uploaded_occ, sep=';')

    # Auto-détection du TV (colonne B = ID)
    tv_detected = occ_df['ID'].iloc[0]

    st.success(f"✅ **TV détecté: {tv_detected}**")

    # Informations sur les données
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📍 Secteur", tv_detected)
    with col2:
        st.metric("📅 Jours de données", len(occ_df))
    with col3:
        date_min = occ_df['Date'].min()
        date_max = occ_df['Date'].max()
        st.metric("📆 Période", f"{date_min} → {date_max}")

except Exception as e:
    st.error(f"❌ Erreur lors de la lecture du fichier: {e}")
    st.stop()

# Configuration des seuils
st.divider()
st.subheader("🎯 Configuration des seuils")

# Essayer de charger depuis R_Capas si fourni
default_sustain = 0.6
default_peak = 1.0

if uploaded_rcapas:
    try:
        rcapas_df = pd.read_excel(uploaded_rcapas)
        # Chercher le TV dans R_Capas
        tv_row = rcapas_df[rcapas_df['Airspace'] == tv_detected]
        if not tv_row.empty:
            # Colonnes I = PEAK 11, K = SUSTAIN 11
            if 'PEAK 11' in rcapas_df.columns:
                default_peak = float(tv_row['PEAK 11'].iloc[0])
            if 'SUSTAIN 11' in rcapas_df.columns:
                default_sustain = float(tv_row['SUSTAIN 11'].iloc[0])
            st.success(f"✅ Seuils récupérés depuis R_Capas")
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire R_Capas: {e}")

col1, col2 = st.columns(2)
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

if sustain >= peak:
    st.error("⚠️ SUSTAIN doit être inférieur à PEAK")
    st.stop()

# Mode d'analyse
st.divider()
col1, col2 = st.columns([2, 1])
with col1:
    analysis_mode = st.radio(
        "Mode d'analyse",
        ["📅 Tous les créneaux", "⚠️ Régulations uniquement"],
        horizontal=True
    )
with col2:
    analyze_btn = st.button("🚀 Analyser", type="primary", use_container_width=True)

# Analyse
if analyze_btn:
    with st.spinner("🔄 Analyse en cours..."):

        # Extraire les colonnes minute (colonnes 4 à 1443 = 1440 minutes)
        minute_cols = occ_df.columns[4:]

        # Créer un DataFrame long pour l'analyse
        analysis_data = []

        for idx, row in occ_df.iterrows():
            date = row['Date']
            for col in minute_cols:
                # Extraire l'heure de la colonne (format: "0:00 - Duration 11 Min")
                time_str = col.split(' - ')[0]
                occ_value = row[col]

                # Déterminer le statut
                if occ_value >= peak:
                    status = "PEAK"
                elif occ_value < sustain:
                    status = "SOUS-SUSTAIN"
                else:
                    status = "NORMAL"

                analysis_data.append({
                    'Date': date,
                    'Time': time_str,
                    'Occupation': occ_value,
                    'Status': status
                })

        df_analysis = pd.DataFrame(analysis_data)

        # Calculer les statistiques globales
        total_minutes = len(df_analysis)
        minutes_above_peak = len(df_analysis[df_analysis['Status'] == 'PEAK'])
        minutes_below_sustain = len(df_analysis[df_analysis['Status'] == 'SOUS-SUSTAIN'])
        minutes_normal = len(df_analysis[df_analysis['Status'] == 'NORMAL'])

        pct_above_peak = (minutes_above_peak / total_minutes) * 100
        pct_below_sustain = (minutes_below_sustain / total_minutes) * 100
        pct_normal = (minutes_normal / total_minutes) * 100

        capacity_hourly = peak * 60

        # Afficher les résultats
        st.divider()
        st.subheader("📈 Résultats de l'analyse")

        # Métriques globales
        st.markdown("### 📊 Statistiques globales")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "⚠️ Temps > PEAK",
                f"{pct_above_peak:.1f}%",
                f"{minutes_above_peak:,} min"
            )
        with col2:
            st.metric(
                "✅ Temps normal",
                f"{pct_normal:.1f}%",
                f"{minutes_normal:,} min"
            )
        with col3:
            st.metric(
                "📉 Temps < SUSTAIN",
                f"{pct_below_sustain:.1f}%",
                f"{minutes_below_sustain:,} min"
            )
        with col4:
            st.metric(
                "🎯 Capacité théorique",
                f"{capacity_hourly:.0f} av/h"
            )

        # Graphique de distribution
        st.markdown("### 📊 Distribution des statuts")
        fig_pie = go.Figure(data=[go.Pie(
            labels=['> PEAK (dégroupement)', 'Normal', '< SUSTAIN (sous-charge)'],
            values=[minutes_above_peak, minutes_normal, minutes_below_sustain],
            marker=dict(colors=['#ff4b4b', '#00c851', '#ffa000']),
            hole=0.4
        )])
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

        # Graphique temporel d'une journée type
        st.markdown("### 📅 Profil journée type")

        # Sélection d'une date
        available_dates = df_analysis['Date'].unique()
        selected_date = st.selectbox("Sélectionner une date", available_dates)

        df_day = df_analysis[df_analysis['Date'] == selected_date].copy()

        # Convertir Time en format numérique pour le graphique
        df_day['TimeNum'] = df_day['Time'].apply(lambda x: 
            int(x.split(':')[0]) * 60 + int(x.split(':')[1])
        )
        df_day = df_day.sort_values('TimeNum')

        # Créer le graphique
        fig = go.Figure()

        # Ligne d'occupation
        fig.add_trace(go.Scatter(
            x=df_day['Time'],
            y=df_day['Occupation'],
            mode='lines',
            name='Occupation',
            line=dict(color='#1f77b4', width=2),
            hovertemplate='%{x}<br>Occupation: %{y} av<extra></extra>'
        ))

        # Ligne PEAK
        fig.add_hline(
            y=peak, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"PEAK ({peak} av/min)",
            annotation_position="right"
        )

        # Ligne SUSTAIN
        fig.add_hline(
            y=sustain, 
            line_dash="dash", 
            line_color="orange",
            annotation_text=f"SUSTAIN ({sustain} av/min)",
            annotation_position="right"
        )

        fig.update_layout(
            title=f"Occupation du {selected_date}",
            xaxis_title="Heure",
            yaxis_title="Occupation (avions)",
            height=500,
            hovermode='x unified'
        )

        # Afficher un point toutes les 60 minutes pour la lisibilité
        fig.update_xaxes(
            tickmode='array',
            tickvals=[f"{h}:00" for h in range(0, 24)],
            ticktext=[f"{h:02d}:00" for h in range(0, 24)]
        )

        st.plotly_chart(fig, use_container_width=True)

        # Statistiques par heure
        st.markdown("### ⏰ Statistiques par heure de la journée")
        df_day['Hour'] = df_day['Time'].apply(lambda x: int(x.split(':')[0]))
        hourly_stats = df_day.groupby('Hour').agg({
            'Occupation': ['mean', 'max', 'min']
        }).round(2)
        hourly_stats.columns = ['Moyenne', 'Max', 'Min']

        fig_hourly = go.Figure()
        fig_hourly.add_trace(go.Bar(
            x=hourly_stats.index,
            y=hourly_stats['Moyenne'],
            name='Moyenne',
            marker_color='#1f77b4'
        ))
        fig_hourly.add_hline(y=peak, line_dash="dash", line_color="red")
        fig_hourly.add_hline(y=sustain, line_dash="dash", line_color="orange")
        fig_hourly.update_layout(
            title="Occupation moyenne par heure",
            xaxis_title="Heure",
            yaxis_title="Occupation (avions)",
            height=400
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

        # Export CSV
        st.divider()
        st.markdown("### 💾 Export des données")

        csv = df_analysis.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger l'analyse complète (CSV)",
            data=csv,
            file_name=f"analyse_capacite_{tv_detected}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

st.markdown("---")
st.markdown("*Développé pour l'analyse de capacité des TV*")
