# 📊 Analyse Capacité Horaire TV

Application Streamlit pour analyser la capacité horaire des secteurs de contrôle aérien (TV) en confrontant les charges réelles avec les seuils SUSTAIN et PEAK.

## 🎯 Fonctionnalités

- ✅ **Auto-détection du TV** depuis le fichier OCC
- ✅ **Upload de fichiers** (OCC_TV, R_Capas, T_Regulations)
- ✅ **Configuration des seuils** SUSTAIN 11 et PEAK 11
- ✅ **Analyse multi-jours** avec statistiques globales
- ✅ **Visualisations interactives** (Plotly)
- ✅ **Export CSV** des résultats

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Étapes

1. **Cloner le repository**
```bash
git clone https://github.com/VOTRE_USERNAME/capacity-analysis.git
cd capacity-analysis
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer l'application**
```bash
streamlit run app_capacity.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📁 Structure des fichiers

```
capacity-analysis/
├── app_capacity.py          # Application principale
├── requirements.txt         # Dépendances Python
├── README.md               # Ce fichier
└── .gitignore              # Fichiers à ignorer
```

## 📊 Format des données

### Fichier OCC_TV (obligatoire)
```csv
Date;ID;Airspace Type;Stat Name;0:00 - Duration 11 Min;0:01 - Duration 11 Min;...
15/05/2025;LFEKHN;TV;Stat_Occupancies_11_Actual;4;2;3;...
```

### Fichier R_Capas (optionnel)
Excel avec colonnes:
- `Airspace` : Code du secteur (ex: LFEKHN)
- `SUSTAIN 11` : Seuil minimal (avions/min)
- `PEAK 11` : Seuil de dégroupement (avions/min)

### Fichier T_Regulations (optionnel)
Excel avec colonnes:
- `TV Id` : Code du secteur
- `Regulation Start Date` : Date
- `WEF` : Début régulation
- `TIL` : Fin régulation
- `Regulation Reason Name` : Type (C, W, S...)

## 🎮 Utilisation

1. **Charger un fichier OCC_TV** dans la barre latérale
2. Le TV est **détecté automatiquement** (colonne B)
3. *Optionnel* : Charger R_Capas pour récupérer les seuils
4. **Configurer** SUSTAIN et PEAK si nécessaire
5. Cliquer sur **🚀 Analyser**
6. **Explorer** les résultats et graphiques
7. **Exporter** les données en CSV

## 📈 Métriques calculées

| Métrique | Description |
|----------|-------------|
| **% Temps > PEAK** | Pourcentage de temps nécessitant un dégroupement |
| **% Temps normal** | Pourcentage de temps dans la plage optimale |
| **% Temps < SUSTAIN** | Pourcentage de temps en sous-charge |
| **Capacité horaire** | PEAK × 60 avions/heure |

## 🖼️ Aperçu

### Interface principale
- 📊 Métriques globales
- 🥧 Graphique de distribution
- 📅 Profil journalier avec seuils
- ⏰ Statistiques horaires

### Export
- 💾 CSV complet avec tous les calculs
- Format: `Date`, `Time`, `Occupation`, `Status`

## 🛠️ Développement

### Ajouter des fonctionnalités

Le code est structuré pour faciliter les extensions:

```python
# Ajouter une nouvelle analyse dans app_capacity.py
def analyze_regulations(df_analysis, regs_df, peak):
    # Votre code ici
    pass
```

### Tester localement

```bash
streamlit run app_capacity.py
```

## 📝 TODO

- [ ] Croisement avec les régulations (justifiées/injustifiées)
- [ ] Statistiques multi-mois agrégées
- [ ] Comparaison entre plusieurs TV
- [ ] Détection automatique des pics non régulés
- [ ] Export PDF des rapports

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer:

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -am 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📄 Licence

MIT License - voir le fichier LICENSE pour plus de détails

## 👤 Auteur

Développé pour l'analyse de capacité des secteurs de contrôle aérien.

## 📧 Support

Pour toute question ou problème, ouvrez une [issue](https://github.com/VOTRE_USERNAME/capacity-analysis/issues).
