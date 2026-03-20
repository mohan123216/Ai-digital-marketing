import os
from datetime import datetime
from typing import Dict, Tuple

import joblib
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBRegressor

from config import settings

logger = logging.getLogger(__name__)


class CampaignPredictor:
    """Predict ROI and conversion rate for marketing campaigns."""

    def __init__(self):
        self.roi_model = None
        self.conversion_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.training_rows = 0
        self.metrics = {"roi": {}, "conversion": {}}
        self.is_trained = False

    def prepare_features(self, df: pd.DataFrame, training: bool = True):
        """Prepare model-ready feature matrix and targets."""
        data = df.copy()

        if "Duration_days" not in data.columns and "Duration" in data.columns:
            data["Duration_days"] = data["Duration"].astype(str).str.extract(r"(\d+)").astype(float)

        numeric_cols = ["Duration_days", "Acquisition_Cost", "CTR", "Clicks", "Impressions", "Engagement_Score"]
        for col in numeric_cols:
            if col not in data.columns:
                data[col] = 0
            if col == "Acquisition_Cost":
                data[col] = pd.to_numeric(
                    data[col].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
                    errors="coerce",
                )
            else:
                data[col] = pd.to_numeric(data[col], errors="coerce")

        missing_ctr = data["CTR"].isna() | (data["CTR"] == 0)
        if missing_ctr.any():
            impressions = data["Impressions"].replace(0, 1)
            data.loc[missing_ctr, "CTR"] = (data.loc[missing_ctr, "Clicks"] / impressions[missing_ctr]) * 100

        data[numeric_cols] = data[numeric_cols].fillna(0)

        categorical_cols = ["Channel_Used", "Customer_Segment", "Location", "Product_Type"]
        for col in categorical_cols:
            if col not in data.columns:
                data[col] = "Unknown"

            if training:
                le = LabelEncoder()
                data[f"{col}_encoded"] = le.fit_transform(data[col].astype(str))
                self.label_encoders[col] = le
            else:
                le = self.label_encoders.get(col)
                if le is None:
                    data[f"{col}_encoded"] = 0
                else:
                    data[f"{col}_encoded"] = data[col].astype(str).apply(
                        lambda value: le.transform([value])[0] if value in le.classes_ else -1
                    )

        feature_cols = [
            "Channel_Used_encoded",
            "Customer_Segment_encoded",
            "Location_encoded",
            "Product_Type_encoded",
            "Duration_days",
            "Acquisition_Cost",
            "CTR",
            "Clicks",
            "Impressions",
            "Engagement_Score",
        ]

        self.feature_names = [col for col in feature_cols if col in data.columns]
        X = data[self.feature_names].fillna(0)

        if training:
            y_roi = pd.to_numeric(data["ROI"], errors="coerce").fillna(0)
            y_conversion = pd.to_numeric(data["Conversion_Rate"], errors="coerce").fillna(0)
            return X, y_roi, y_conversion

        return X

    def _cross_validate_sampled(self, model, X_train, y_train, cv: int = 3, max_samples: int = 50000):
        """Run CV on a capped sample to keep startup time practical."""
        if len(X_train) > max_samples:
            rng = np.random.RandomState(settings.RANDOM_STATE)
            indices = rng.choice(len(X_train), size=max_samples, replace=False)
            X_sample = X_train[indices]
            y_sample = y_train.iloc[indices]
        else:
            X_sample = X_train
            y_sample = y_train

        return cross_val_score(model, X_sample, y_sample, cv=cv, scoring="r2")

    def train(self, df: pd.DataFrame) -> Dict:
        """Train ROI and conversion models."""
        logger.info("=" * 60)
        logger.info("TRAINING PREDICTION MODELS")
        logger.info("=" * 60)

        X, y_roi, y_conversion = self.prepare_features(df, training=True)
        self.training_rows = len(X)

        logger.info(f"Training with {len(self.feature_names)} features: {self.feature_names}")
        logger.info(f"Target ROI: mean={y_roi.mean():.2f}, std={y_roi.std():.2f}")
        logger.info(f"Target Conversion Rate: mean={y_conversion.mean():.4f}, std={y_conversion.std():.4f}")

        X_train, X_test, y_roi_train, y_roi_test, y_conv_train, y_conv_test = train_test_split(
            X, y_roi, y_conversion, test_size=settings.TEST_SIZE, random_state=settings.RANDOM_STATE
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        logger.info("Training ROI model...")
        self.roi_model = RandomForestRegressor(
            n_estimators=settings.N_ESTIMATORS,
            max_depth=settings.MAX_DEPTH,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=settings.RANDOM_STATE,
            n_jobs=-1,
        )
        self.roi_model.fit(X_train_scaled, y_roi_train)

        roi_pred = self.roi_model.predict(X_test_scaled)
        roi_rmse = np.sqrt(mean_squared_error(y_roi_test, roi_pred))
        roi_mae = mean_absolute_error(y_roi_test, roi_pred)
        roi_r2 = r2_score(y_roi_test, roi_pred)
        roi_cv_scores = self._cross_validate_sampled(self.roi_model, X_train_scaled, y_roi_train, cv=3)

        self.metrics["roi"] = {
            "rmse": float(roi_rmse),
            "mae": float(roi_mae),
            "r2": float(roi_r2),
            "cv_r2_mean": float(roi_cv_scores.mean()),
            "cv_r2_std": float(roi_cv_scores.std()),
        }

        logger.info(f"ROI model metrics: R2={roi_r2:.4f}, RMSE={roi_rmse:.4f}, MAE={roi_mae:.4f}")

        logger.info("Training conversion model (XGBoost regressor)...")
        self.conversion_model = XGBRegressor(
            n_estimators=350,
            max_depth=6,
            learning_rate=0.06,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective="reg:squarederror",
            random_state=settings.RANDOM_STATE,
            n_jobs=-1,
        )
        self.conversion_model.fit(X_train_scaled, y_conv_train)

        conv_pred = self.conversion_model.predict(X_test_scaled)
        conv_rmse = np.sqrt(mean_squared_error(y_conv_test, conv_pred))
        conv_mae = mean_absolute_error(y_conv_test, conv_pred)
        conv_r2 = r2_score(y_conv_test, conv_pred)
        conv_cv_scores = self._cross_validate_sampled(self.conversion_model, X_train_scaled, y_conv_train, cv=3)

        self.metrics["conversion"] = {
            "rmse": float(conv_rmse),
            "mae": float(conv_mae),
            "r2": float(conv_r2),
            "cv_r2_mean": float(conv_cv_scores.mean()),
            "cv_r2_std": float(conv_cv_scores.std()),
        }

        logger.info(f"Conversion model metrics: R2={conv_r2:.4f}, RMSE={conv_rmse:.4f}, MAE={conv_mae:.4f}")

        self.is_trained = True
        self.save_models()
        return self.metrics

    def predict(self, features_dict: Dict) -> Dict[str, float]:
        """Predict ROI and conversion rate for a new campaign."""
        if not self.is_trained:
            raise ValueError("Models are not trained. Call train() first.")

        input_df = pd.DataFrame([features_dict])
        X = self.prepare_features(input_df, training=False)

        for feature in self.feature_names:
            if feature not in X.columns:
                X[feature] = 0

        X = X[self.feature_names]
        X_scaled = self.scaler.transform(X)

        predicted_roi = float(self.roi_model.predict(X_scaled)[0])
        predicted_conversion = float(self.conversion_model.predict(X_scaled)[0])

        roi_confidence = self._calculate_confidence(self.roi_model, X_scaled, predicted_roi, target="roi")
        conv_confidence = self._calculate_confidence(
            self.conversion_model, X_scaled, predicted_conversion, target="conversion"
        )
        confidence = (roi_confidence + conv_confidence) / 2

        return {
            "predicted_roi": predicted_roi,
            "predicted_conversion_rate": float(max(0.0, min(1.0, predicted_conversion))),
            "confidence_score": float(min(0.95, max(settings.MIN_CONFIDENCE_THRESHOLD, confidence))),
        }

    def _calculate_confidence(self, model, X_scaled, prediction: float, target: str) -> float:
        """Estimate confidence from model uncertainty."""
        if hasattr(model, "estimators_"):
            predictions = [tree.predict(X_scaled)[0] for tree in model.estimators_]
            confidence = 1 - (np.std(predictions) / (abs(prediction) + 0.1))
            return float(max(0.3, min(0.95, confidence)))

        rmse = float(self.metrics.get(target, {}).get("rmse", 0.0))
        normalizer = 0.2 if target == "conversion" else max(abs(prediction), 1.0)
        confidence = 1 - (rmse / (normalizer + 1e-9))
        return float(max(0.3, min(0.95, confidence)))

    def save_models(self):
        """Save trained models and preprocessors."""
        joblib.dump(self.roi_model, os.path.join(settings.MODEL_PATH, "roi_model.pkl"))
        joblib.dump(self.conversion_model, os.path.join(settings.MODEL_PATH, "conversion_model.pkl"))
        joblib.dump(self.scaler, os.path.join(settings.MODEL_PATH, "scaler.pkl"))
        joblib.dump(self.label_encoders, os.path.join(settings.MODEL_PATH, "encoders.pkl"))
        joblib.dump(self.feature_names, os.path.join(settings.MODEL_PATH, "feature_names.pkl"))
        joblib.dump(self.training_rows, os.path.join(settings.MODEL_PATH, "training_rows.pkl"))
        logger.info(f"Models saved to {settings.MODEL_PATH}")

    def load_models(self):
        """Load trained models from disk."""
        self.roi_model = joblib.load(os.path.join(settings.MODEL_PATH, "roi_model.pkl"))
        self.conversion_model = joblib.load(os.path.join(settings.MODEL_PATH, "conversion_model.pkl"))
        self.scaler = joblib.load(os.path.join(settings.MODEL_PATH, "scaler.pkl"))
        self.label_encoders = joblib.load(os.path.join(settings.MODEL_PATH, "encoders.pkl"))
        self.feature_names = joblib.load(os.path.join(settings.MODEL_PATH, "feature_names.pkl"))
        self.training_rows = joblib.load(os.path.join(settings.MODEL_PATH, "training_rows.pkl"))
        self.is_trained = True
        logger.info("Models loaded successfully")

    def get_model_metrics(self) -> Dict:
        """Get current model performance metrics."""
        return {
            "roi_model_r2": self.metrics["roi"].get("r2", 0.0),
            "roi_model_rmse": self.metrics["roi"].get("rmse", 0.0),
            "conversion_model_r2": self.metrics["conversion"].get("r2", 0.0),
            "conversion_model_rmse": self.metrics["conversion"].get("rmse", 0.0),
            "feature_importance": dict(zip(self.feature_names, self.roi_model.feature_importances_)) if self.roi_model is not None else {},
            "last_trained": datetime.now().isoformat(),
            "data_records": self.training_rows,
        }
