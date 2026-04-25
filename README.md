# AirQual CM — Backend FastAPI

**Équipe AlphaInfera · IndabaX Cameroon 2026**

Backend Python qui charge `best_model_rf.joblib` et expose une API REST appelée par l'app Flutter.

---

## 📁 Structure attendue

```
airqual_backend/
├── main.py
├── requirements.txt
└── models/                        ← coller tes fichiers Colab ici
    ├── best_model_rf.joblib       ← ton vrai modèle RF
    ├── features.json
    ├── label_encoder_region.joblib
    ├── city_profiles.csv
    ├── risk_table.csv
    ├── global_stats.json
    └── city_enc_map.json
```

---

## 🚀 Lancement local

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Coller tes modèles dans models/
mkdir models
# → copier tes 7 fichiers ici

# 3. Lancer le serveur
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Tester
curl http://localhost:8000/health
# → {"status":"ok","model":"RF Optimise (GridSearch)","model_loaded":true}

# 5. Documentation interactive
# Ouvrir http://localhost:8000/docs
```

---

## 🌐 Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Info API |
| GET | `/health` | Santé du serveur |
| POST | `/predict` | Prédiction PM2.5 courante |
| POST | `/forecast` | Prévisions N jours |
| GET | `/cities` | Liste toutes les villes |
| GET | `/stats` | Stats globales du modèle |
| GET | `/model/features` | Features + importances |

---

## 📡 Déploiement pour Flutter

### Option A — Render.com (gratuit)
```bash
# 1. Créer un repo GitHub avec ces fichiers + le dossier models/
# 2. Sur render.com → New Web Service
# 3. Build command : pip install -r requirements.txt
# 4. Start command : uvicorn main:app --host 0.0.0.0 --port $PORT
# 5. Copier l'URL (ex: https://airqual-cm.onrender.com)
```

### Option B — Railway.app
```bash
railway init
railway up
# → URL auto-générée
```

### Option C — Local (test réseau local)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
# Flutter utilise : http://TON_IP_LOCAL:8000
```

---

## 🔗 Intégration dans Flutter

Une fois déployé, modifier dans `lib/services/open_meteo_service.dart` :

```dart
static const String _apiBaseUrl = 'https://TON_URL_BACKEND';
```

Le service Flutter enverra les données Open-Meteo au backend,
qui les passera dans le vrai RF et renverra le PM2.5 prédit.
