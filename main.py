"""
AirQual CM — Backend FastAPI
Équipe AlphaInfera · IndabaX Cameroon 2026

Charge best_model_rf.joblib et expose /predict pour l'app Flutter.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import numpy as np
import joblib
import json
import math
import os
from datetime import datetime

# ── Chargement des artefacts ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

try:
    rf_model       = joblib.load(os.path.join(MODELS_DIR, 'best_model_rf.joblib'))
    le_region      = joblib.load(os.path.join(MODELS_DIR, 'label_encoder_region.joblib'))
    with open(os.path.join(MODELS_DIR, 'features.json'))      as f: FEATURES      = json.load(f)
    with open(os.path.join(MODELS_DIR, 'global_stats.json'))  as f: GLOBAL_STATS  = json.load(f)
    
    import pandas as pd
    CITY_PROFILES = pd.read_csv(os.path.join(MODELS_DIR, 'city_profiles.csv'))
    RISK_TABLE    = pd.read_csv(os.path.join(MODELS_DIR, 'risk_table.csv'))

    CITY_ENC_MAP = {
        name: i
        for i, name in enumerate(sorted(CITY_PROFILES['city'].tolist()))
    }
    print(f"✓ Modèle RF chargé  ({len(FEATURES)} features)")
    print(f"✓ {len(CITY_PROFILES)} profils de villes chargés")
    MODEL_LOADED = True
except Exception as e:
    print(f"⚠️  Modèle non chargé : {e}")
    MODEL_LOADED = False

# ── App FastAPI ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AirQual CM API",
    description="Prédiction PM2.5 au Cameroun — AlphaInfera · IndabaX 2026",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schémas Pydantic ──────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    # Variables météo (viennent de Open-Meteo)
    temperature_2m_mean:          float = Field(..., description="Temp. moyenne (°C)")
    temperature_2m_max:           float = Field(..., description="Temp. max (°C)")
    temperature_2m_min:           float = Field(..., description="Temp. min (°C)")
    precipitation_sum:            float = Field(0.0,  description="Précipitations (mm)")
    wind_speed_10m_max:           float = Field(..., description="Vent max (km/h)")
    wind_gusts_10m_max:           float = Field(0.0,  description="Rafales max (km/h)")
    shortwave_radiation_sum:      float = Field(..., description="Radiation solaire (MJ/m²)")
    et0_fao_evapotranspiration:   float = Field(0.0,  description="Évapotranspiration (mm)")
    sunshine_duration:            float = Field(0.0,  description="Durée ensoleillement (s)")
    daylight_duration:            float = Field(86400.0, description="Durée jour (s)")

    # Localisation
    latitude:  float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    city:      str   = Field(..., description="Nom de la ville")
    region:    str   = Field(..., description="Région")

    # Optionnels — calculés automatiquement si absents
    temp_lag1:  Optional[float] = None
    temp_lag7:  Optional[float] = None
    wind_lag1:  Optional[float] = None
    temp_roll7: Optional[float] = None


class PredictResponse(BaseModel):
    pm25:              float
    level:             str
    level_en:          str
    health_advice_fr:  str
    health_advice_en:  str
    aggravating_factors: list[str]
    feature_values:    dict


class ForecastRequest(BaseModel):
    city:    str
    region:  str
    latitude:  float
    longitude: float
    days:      int = Field(7, ge=1, le=16)
    # Liste de données météo journalières (depuis Open-Meteo /forecast)
    daily_temps_max:   list[float]
    daily_temps_min:   list[float]
    daily_precip:      list[float]
    daily_wind:        list[float]
    daily_radiation:   list[float]
    daily_et0:         list[float] = []


# ── Helpers ───────────────────────────────────────────────────────────────────
LEVEL_LABELS_FR = {
    'good':       'Bon',
    'moderate':   'Modéré',
    'elevated':   'Élevé',
    'high':       'Très élevé',
    'very_high':  'Dangereux',
    'hazardous':  'Extrêmement dangereux',
}
LEVEL_LABELS_EN = {
    'good':       'Good',
    'moderate':   'Moderate',
    'elevated':   'Elevated',
    'high':       'High',
    'very_high':  'Very High',
    'hazardous':  'Hazardous',
}
HEALTH_ADVICE_FR = {
    'good':       'La qualité de l\'air est satisfaisante. Profitez des activités extérieures.',
    'moderate':   'Qualité acceptable. Les personnes sensibles devraient limiter les efforts prolongés dehors.',
    'elevated':   'Groupes sensibles (enfants, personnes âgées, asthmatiques) : limitez les activités extérieures.',
    'high':       'Mauvaise qualité de l\'air. Réduisez les activités physiques intenses à l\'extérieur.',
    'very_high':  'Dangereux. Évitez toute activité extérieure. Portez un masque si vous sortez.',
    'hazardous':  'Urgence sanitaire. Restez à l\'intérieur, fermez les fenêtres. Consultez un médecin.',
}
HEALTH_ADVICE_EN = {
    'good':       'Air quality is satisfactory. Enjoy outdoor activities.',
    'moderate':   'Acceptable quality. Sensitive people should limit prolonged outdoor exertion.',
    'elevated':   'Sensitive groups (children, elderly, asthmatics): limit outdoor activities.',
    'high':       'Poor air quality. Reduce intense outdoor physical activity.',
    'very_high':  'Hazardous. Avoid outdoor activity. Wear a mask if you go out.',
    'hazardous':  'Health emergency. Stay indoors, close windows. Consult a doctor if symptoms appear.',
}


def pm25_to_level(pm25: float) -> str:
    if pm25 <= 12:  return 'good'
    if pm25 <= 15:  return 'moderate'
    if pm25 <= 25:  return 'elevated'
    if pm25 <= 35:  return 'high'
    if pm25 <= 55:  return 'very_high'
    return 'hazardous'


def encode_region(region: str) -> int:
    """Encode region, fallback to 0 if unknown."""
    try:
        return int(le_region.transform([region])[0])
    except Exception:
        return 0


def encode_city(city: str) -> int:
    """Encode city, fallback to 0 if unknown."""
    return CITY_ENC_MAP.get(city, 0)


def build_feature_vector(
    req,
    date: datetime = None,
    temp_lag1: float = None,
    temp_lag7: float = None,
    wind_lag1: float = None,
    temp_roll7: float = None,
) -> np.ndarray:
    """Construire le vecteur de 24 features dans l'ordre exact du modèle."""
    if date is None:
        date = datetime.utcnow()

    month      = date.month
    day_of_year = date.timetuple().tm_yday

    sunshine_ratio = req.sunshine_duration / (req.daylight_duration + 1e-6)
    temp_amplitude = req.temperature_2m_max - req.temperature_2m_min
    is_no_wind     = 1 if req.wind_speed_10m_max < 5 else 0
    is_no_rain     = 1 if req.precipitation_sum < 0.1 else 0
    is_dry_season  = 1 if month in [11, 12, 1, 2, 3] else 0
    month_sin      = math.sin(2 * math.pi * month / 12)
    month_cos      = math.cos(2 * math.pi * month / 12)

    # Lag features — use provided or fall back to current value
    t_lag1  = temp_lag1  if temp_lag1  is not None else req.temperature_2m_mean
    t_lag7  = temp_lag7  if temp_lag7  is not None else req.temperature_2m_mean
    w_lag1  = wind_lag1  if wind_lag1  is not None else req.wind_speed_10m_max
    t_roll7 = temp_roll7 if temp_roll7 is not None else req.temperature_2m_mean

    region_enc = encode_region(req.region)
    city_enc   = encode_city(req.city)

    feature_map = {
        'temperature_2m_mean':         req.temperature_2m_mean,
        'temperature_2m_max':          req.temperature_2m_max,
        'temperature_2m_min':          req.temperature_2m_min,
        'precipitation_sum':           req.precipitation_sum,
        'wind_speed_10m_max':          req.wind_speed_10m_max,
        'wind_gusts_10m_max':          req.wind_gusts_10m_max,
        'shortwave_radiation_sum':     req.shortwave_radiation_sum,
        'et0_fao_evapotranspiration':  req.et0_fao_evapotranspiration,
        'sunshine_ratio':              sunshine_ratio,
        'temp_amplitude':              temp_amplitude,
        'is_no_wind':                  is_no_wind,
        'is_no_rain':                  is_no_rain,
        'is_dry_season':               is_dry_season,
        'month_sin':                   month_sin,
        'month_cos':                   month_cos,
        'day_of_year':                 day_of_year,
        'temp_lag1':                   t_lag1,
        'temp_lag7':                   t_lag7,
        'wind_lag1':                   w_lag1,
        'temp_roll7':                  t_roll7,
        'latitude':                    req.latitude,
        'longitude':                   req.longitude,
        'region_enc':                  region_enc,
        'city_enc':                    city_enc,
    }

    vec = np.array([feature_map[f] for f in FEATURES], dtype=np.float32)
    return vec, feature_map


def get_aggravating_factors(feature_map: dict) -> list[str]:
    factors = []
    if feature_map.get('is_no_wind'):     factors.append('low_wind')
    if feature_map.get('is_no_rain'):     factors.append('no_rain')
    if feature_map['temperature_2m_mean'] > 35: factors.append('high_temp')
    if feature_map['shortwave_radiation_sum'] > 20: factors.append('high_radiation')
    if feature_map.get('is_dry_season'):  factors.append('harmattan')
    return factors


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "app": "AirQual CM API",
        "team": "AlphaInfera",
        "model_loaded": MODEL_LOADED,
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "model": "RF Optimise (GridSearch)", "model_loaded": MODEL_LOADED}


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
def predict(req: PredictRequest):
    """
    Prédit le PM2.5 pour une localité à partir des variables météo Open-Meteo.
    Utilisé par l'app Flutter pour la valeur courante.
    """
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    vec, feature_map = build_feature_vector(req)
    pm25 = float(rf_model.predict(vec.reshape(1, -1))[0])
    pm25 = max(0.0, round(pm25, 2))
    level = pm25_to_level(pm25)
    factors = get_aggravating_factors(feature_map)

    return PredictResponse(
        pm25=pm25,
        level=level,
        level_en=LEVEL_LABELS_EN[level],
        health_advice_fr=HEALTH_ADVICE_FR[level],
        health_advice_en=HEALTH_ADVICE_EN[level],
        aggravating_factors=factors,
        feature_values={k: round(float(v), 4) for k, v in feature_map.items()},
    )


@app.post("/forecast", tags=["Prediction"])
def forecast(req: ForecastRequest):
    """
    Prédit le PM2.5 pour les N prochains jours.
    Utilisé par l'app Flutter pour les prévisions.
    """
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    n = min(req.days, len(req.daily_temps_max))
    results = []
    temp_history = []

    for i in range(n):
        date = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        date = date + timedelta(days=i + 1)

        temp_mean = (req.daily_temps_max[i] + req.daily_temps_min[i]) / 2
        et0 = req.daily_et0[i] if i < len(req.daily_et0) else 0.0

        # Simple request-like object
        class _Req:
            pass
        r = _Req()
        r.temperature_2m_mean        = temp_mean
        r.temperature_2m_max         = req.daily_temps_max[i]
        r.temperature_2m_min         = req.daily_temps_min[i]
        r.precipitation_sum          = req.daily_precip[i]
        r.wind_speed_10m_max         = req.daily_wind[i]
        r.wind_gusts_10m_max         = req.daily_wind[i] * 1.4
        r.shortwave_radiation_sum    = req.daily_radiation[i]
        r.et0_fao_evapotranspiration = et0
        r.sunshine_duration          = 36000.0
        r.daylight_duration          = 43200.0
        r.latitude                   = req.latitude
        r.longitude                  = req.longitude
        r.city                       = req.city
        r.region                     = req.region

        lag1  = temp_history[-1] if len(temp_history) >= 1 else temp_mean
        lag7  = temp_history[-7] if len(temp_history) >= 7 else temp_mean
        roll7 = float(np.mean(temp_history[-7:])) if temp_history else temp_mean

        vec, feature_map = build_feature_vector(
            r, date=date,
            temp_lag1=lag1, temp_lag7=lag7,
            wind_lag1=req.daily_wind[i-1] if i > 0 else req.daily_wind[0],
            temp_roll7=roll7,
        )

        pm25 = float(rf_model.predict(vec.reshape(1, -1))[0])
        pm25 = max(0.0, round(pm25, 2))
        level = pm25_to_level(pm25)

        results.append({
            "date":       date.strftime("%Y-%m-%d"),
            "pm25":       pm25,
            "level":      level,
            "level_fr":   LEVEL_LABELS_FR[level],
            "level_en":   LEVEL_LABELS_EN[level],
            "temp_max":   req.daily_temps_max[i],
            "temp_min":   req.daily_temps_min[i],
            "precip":     req.daily_precip[i],
            "wind":       req.daily_wind[i],
            "radiation":  req.daily_radiation[i],
        })
        temp_history.append(temp_mean)

    # Alert: days with elevated PM2.5
    alert_days = [r for r in results if r['pm25'] > 25]

    return {
        "city":       req.city,
        "region":     req.region,
        "forecast":   results,
        "alert":      len(alert_days) > 0,
        "alert_days": len(alert_days),
        "model":      "RF Optimise (GridSearch)",
    }


@app.get("/cities", tags=["Data"])
def get_cities():
    """Liste toutes les villes avec leur profil climatique et PM2.5 moyen."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Données non chargées")
    return RISK_TABLE.to_dict(orient='records')


@app.get("/stats", tags=["Data"])
def get_stats():
    """Statistiques globales du modèle et du dataset."""
    return GLOBAL_STATS


@app.get("/model/features", tags=["Model"])
def get_features():
    """Liste des features dans l'ordre exact attendu par le modèle."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    importances = dict(zip(FEATURES, rf_model.feature_importances_.tolist()))
    return {
        "features": FEATURES,
        "n_features": len(FEATURES),
        "importances": dict(sorted(importances.items(), key=lambda x: -x[1])),
    }
