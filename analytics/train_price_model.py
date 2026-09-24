"""
Trains and evaluates the StaySphere nightly price estimator.

Target: price
Features: city, property_type, room_type, accommodates, bedrooms,
          minimum_nights, review_scores_rating

Models compared: Linear Regression (baseline) vs Random Forest.
Evaluation: train/test split, MAE, RMSE, R^2, actual-vs-predicted plot,
residual plot, feature importance.

Run:
    cd analytics
    python3 train_price_model.py [path/to/listings.csv]

Outputs:
    ../src/backend/app/ml_model/price_model.joblib   (best model + encoders + metrics)
    figures/actual_vs_predicted.png
    figures/residuals.png
    figures/feature_importance.png
    figures/metrics.json
"""
import json
import os
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "..", "data", "sample", "dummy_listings.csv")
MODEL_OUT = os.path.join(HERE, "..", "src", "backend", "app", "ml_model", "price_model.joblib")
FIGURES_DIR = os.path.join(HERE, "figures")

FEATURE_CATEGORICAL = ["city", "property_type", "room_type"]
FEATURE_NUMERIC = ["accommodates", "bedrooms", "minimum_nights", "review_scores_rating"]
FEATURE_COLUMNS = FEATURE_CATEGORICAL + FEATURE_NUMERIC
TARGET = "price"


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    before = len(df)
    df = df.drop_duplicates(subset=["listing_id"])
    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET])
    after = len(df)
    print(f"Loaded {before} rows, {after} rows after dropping duplicates/missing.")
    return df


def encode_features(df: pd.DataFrame):
    df = df.copy()
    encoders = {}
    for col in FEATURE_CATEGORICAL:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
    return df, encoders


def evaluate(name, model, X_test, y_test):
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = r2_score(y_test, preds)
    print(f"[{name}] MAE={mae:.2f}  RMSE={rmse:.2f}  R2={r2:.3f}")
    return {"mae": mae, "rmse": rmse, "r2": r2}, preds


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)

    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    df = load_data(csv_path)

    df_encoded, encoders = encode_features(df)
    X = df_encoded[FEATURE_COLUMNS]
    y = df_encoded[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Baseline
    baseline = LinearRegression()
    baseline.fit(X_train, y_train)
    baseline_metrics, _ = evaluate("LinearRegression (baseline)", baseline, X_test, y_test)

    # Candidate
    rf = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_metrics, rf_preds = evaluate("RandomForestRegressor", rf, X_test, y_test)

    # Pick the better model by RMSE
    if rf_metrics["rmse"] <= baseline_metrics["rmse"]:
        best_name, best_model, best_metrics, best_preds = "RandomForestRegressor", rf, rf_metrics, rf_preds
    else:
        best_name, best_model, best_metrics, best_preds = "LinearRegression", baseline, baseline_metrics, baseline.predict(X_test)

    print(f"Selected model: {best_name}")

    # Actual vs predicted
    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, best_preds, alpha=0.4, s=15)
    lims = [min(y_test.min(), best_preds.min()), max(y_test.max(), best_preds.max())]
    plt.plot(lims, lims, "r--", label="Perfect prediction")
    plt.xlabel("Actual price")
    plt.ylabel("Predicted price")
    plt.title(f"Actual vs Predicted — {best_name}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "actual_vs_predicted.png"), dpi=120)
    plt.close()

    # Residuals
    residuals = y_test.values - best_preds
    plt.figure(figsize=(6, 4))
    plt.scatter(best_preds, residuals, alpha=0.4, s=15)
    plt.axhline(0, color="r", linestyle="--")
    plt.xlabel("Predicted price")
    plt.ylabel("Residual (actual - predicted)")
    plt.title(f"Residuals — {best_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "residuals.png"), dpi=120)
    plt.close()

    # Feature importance (only meaningful for tree models)
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        order = np.argsort(importances)[::-1]
        plt.figure(figsize=(6, 4))
        plt.bar(range(len(FEATURE_COLUMNS)), importances[order])
        plt.xticks(range(len(FEATURE_COLUMNS)), [FEATURE_COLUMNS[i] for i in order], rotation=45, ha="right")
        plt.title(f"Feature importance — {best_name}")
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "feature_importance.png"), dpi=120)
        plt.close()

    metrics_out = {
        "selected_model": best_name,
        "baseline_linear_regression": baseline_metrics,
        "random_forest": rf_metrics,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "features": FEATURE_COLUMNS,
        "target": TARGET,
    }
    with open(os.path.join(FIGURES_DIR, "metrics.json"), "w") as f:
        json.dump(metrics_out, f, indent=2)

    bundle = {
        "model": best_model,
        "model_version": best_name,
        "encoders": encoders,
        "feature_columns": FEATURE_COLUMNS,
        "metrics": best_metrics,
    }
    joblib.dump(bundle, MODEL_OUT)
    print(f"Saved model bundle to {MODEL_OUT}")
    print(f"Saved metrics/figures to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
