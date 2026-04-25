# 🚀 AirQual CM — Déploiement Backend FastAPI
**Équipe AlphaInfera · IndabaX Cameroon 2026**

---

## 📁 Structure du projet

```
airqual_backend/
├── main.py                  ← API FastAPI (point d'entrée)
├── requirements.txt         ← dépendances Python
├── Procfile                 ← config Render/Railway
├── render.yaml              ← config auto-deploy Render
├── runtime.txt              ← version Python
├── start.sh                 ← lancement Linux/Mac
├── start.bat                ← lancement Windows
├── DEPLOY.md                ← ce fichier
└── models/                  ← ⚠️ REMPLIR avec tes fichiers Colab
    ├── best_model_rf.joblib
    ├── features.json
    ├── label_encoder_region.joblib
    ├── city_profiles.csv
    ├── risk_table.csv
    ├── global_stats.json
    └── city_enc_map.json
```

---

## ⚠️ ÉTAPE 0 — Générer les fichiers modèles (OBLIGATOIRE)

Avant tout déploiement, tu dois avoir les 7 fichiers de modèles.

### Dans Google Colab (Notebook_AlphaInfera.ipynb) :

Exécute la cellule d'export (Section 10) :

```python
import joblib, json, os

EXPORT_DIR = './airqual_backend/models'
os.makedirs(EXPORT_DIR, exist_ok=True)

# 1. Modèle RF
joblib.dump(fitted_models['RF Optimise (GridSearch)'],
            f'{EXPORT_DIR}/best_model_rf.joblib')

# 2. Features
with open(f'{EXPORT_DIR}/features.json', 'w') as f:
    json.dump(FEATURES, f, indent=2)

# 3. LabelEncoder région
joblib.dump(le_region, f'{EXPORT_DIR}/label_encoder_region.joblib')

# 4. Profils villes
city_profile.to_csv(f'{EXPORT_DIR}/city_profiles.csv', index=False)

# 5. Table de risque
risk_export.to_csv(f'{EXPORT_DIR}/risk_table.csv', index=False)

# 6. Stats globales
with open(f'{EXPORT_DIR}/global_stats.json', 'w') as f:
    json.dump(global_stats, f, indent=2, ensure_ascii=False)

# 7. Encodage villes
with open(f'{EXPORT_DIR}/city_enc_map.json', 'w') as f:
    json.dump(city_enc_map, f, indent=2)

print("✓ 7 fichiers exportés dans", EXPORT_DIR)
```

**Télécharger** les fichiers depuis Colab → **les placer dans `models/`**

---

## 🖥️ OPTION A — Test local (Windows/Mac/Linux)

### Windows
```bat
# Double-cliquer sur start.bat
# OU dans PowerShell :
cd airqual_backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Linux / Mac
```bash
cd airqual_backend
chmod +x start.sh
./start.sh
```

### Tester que ça marche
```bash
curl http://localhost:8000/health
# → {"status":"ok","model":"RF Optimise (GridSearch)","model_loaded":true}

# Documentation interactive
# Ouvrir : http://localhost:8000/docs
```

### Tester /predict
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temperature_2m_mean": 32.5,
    "temperature_2m_max": 38.0,
    "temperature_2m_min": 26.0,
    "precipitation_sum": 0.0,
    "wind_speed_10m_max": 4.2,
    "wind_gusts_10m_max": 6.5,
    "shortwave_radiation_sum": 22.0,
    "et0_fao_evapotranspiration": 5.8,
    "sunshine_duration": 36000,
    "daylight_duration": 43200,
    "latitude": 10.59,
    "longitude": 14.32,
    "city": "Maroua",
    "region": "Extreme-Nord"
  }'
```

---

## ☁️ OPTION B — Déploiement Render.com (GRATUIT, recommandé)

### Étape 1 — Préparer un repo GitHub

```bash
# Dans le dossier airqual_backend/
git init
git add .
# IMPORTANT : inclure le dossier models/ avec tes fichiers !
git add models/
git commit -m "AirQual CM API - AlphaInfera"
```

Créer un repo sur [github.com](https://github.com) → pousser :
```bash
git remote add origin https://github.com/TON_USERNAME/airqual-cm-api.git
git branch -M main
git push -u origin main
```

### Étape 2 — Déployer sur Render

1. Aller sur **[render.com](https://render.com)** → créer un compte gratuit
2. Cliquer **"New +"** → **"Web Service"**
3. Connecter ton compte GitHub → sélectionner `airqual-cm-api`
4. Remplir les champs :

| Champ | Valeur |
|-------|--------|
| **Name** | `airqual-cm-api` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | `Free` |

5. Cliquer **"Create Web Service"**
6. Attendre ~3 minutes que le build finisse
7. Copier l'URL : `https://airqual-cm-api.onrender.com`

### Étape 3 — Tester l'URL de production
```bash
curl https://airqual-cm-api.onrender.com/health
# → {"status":"ok","model_loaded":true}
```

### ⚠️ Limite plan gratuit Render
Le service s'endort après 15 min d'inactivité → 1er appel lent (30-50s).
Pour un hackathon c'est suffisant. Pour production : plan payant ($7/mois).

---

## ☁️ OPTION C — Déploiement Railway.app (alternatif)

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Se connecter
railway login

# Dans le dossier airqual_backend/
railway init
railway up

# L'URL est affichée automatiquement
# ex: https://airqual-cm-api-production.up.railway.app
```

---

## ☁️ OPTION D — Déploiement sur un VPS (Ubuntu)

```bash
# Sur le serveur VPS (connexion SSH)
sudo apt update && sudo apt install python3-pip python3-venv -y

# Cloner le projet
git clone https://github.com/TON_USERNAME/airqual-cm-api.git
cd airqual-cm-api

# Environnement virtuel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Lancer avec gunicorn (production)
pip install gunicorn
gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 --daemon

# Avec nginx (optionnel, pour HTTPS)
sudo apt install nginx -y
```

---

## 🔗 ÉTAPE FINALE — Connecter Flutter à l'API déployée

Une fois l'URL obtenue (ex: `https://airqual-cm-api.onrender.com`),
modifier dans le projet Flutter :

```
airqual_cm/lib/services/open_meteo_service.dart  →  ligne 8
```

```dart
// Remplacer :
const String _kBackendUrl = 'http://10.0.2.2:8000';

// Par ton URL de production :
const String _kBackendUrl = 'https://airqual-cm-api.onrender.com';
```

Puis rebuild l'APK :
```bash
cd airqual_cm
flutter build apk --release
```

---

## 🧪 Endpoints disponibles

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Info API |
| GET | `/health` | Statut du serveur + modèle |
| POST | `/predict` | Prédiction PM2.5 courante (1 jour) |
| POST | `/forecast` | Prévisions PM2.5 (N jours) |
| GET | `/cities` | Toutes les villes + risque PM2.5 |
| GET | `/stats` | Statistiques globales + MAE/R2 |
| GET | `/model/features` | Features + importances RF |

**Documentation interactive complète :**
`https://TON_URL/docs`

---

## 🔁 Résumé ultra-rapide

```bash
# 1. Copier tes modèles Colab dans models/
# 2. Pousser sur GitHub
# 3. Déployer sur render.com (gratuit)
# 4. Copier l'URL dans Flutter → open_meteo_service.dart
# 5. flutter build apk --release
# ✅ APK fonctionne avec le vrai modèle RF !
```

---

*AirQual CM · AlphaInfera · IndabaX Cameroon 2026*
