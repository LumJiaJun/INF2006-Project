import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder


RANDOM_STATE = 42
TEST_SIZE = 0.2
PRICE_SCOPE_QUANTILE = 0.99
TARGET = "price"
CATEGORICAL_FEATURES = [
    "city",
    "neighbourhood",
    "property_type",
    "room_type",
    "instant_bookable",
    "host_is_superhost",
    "host_identity_verified",
]
NUMERIC_FEATURES = [
    "latitude",
    "longitude",
    "accommodates",
    "bedrooms",
    "minimum_nights",
    "review_scores_rating",
    "host_total_listings_count",
    "amenities_count",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
SOURCE_FEATURES = [feature for feature in FEATURES if feature != "amenities_count"] + ["amenities"]


def parse_args():
    parser = argparse.ArgumentParser(description="Train and evaluate Airbnb price models.")
    parser.add_argument("--listings", type=Path, required=True)
    parser.add_argument("--model-output", type=Path, required=True)
    parser.add_argument("--metrics-output", type=Path, required=True)
    return parser.parse_args()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_training_data(path):
    frame = pd.read_csv(
        path,
        usecols=SOURCE_FEATURES + [TARGET],
        encoding="utf-8",
        encoding_errors="replace",
        low_memory=False,
    )
    frame[TARGET] = pd.to_numeric(frame[TARGET], errors="coerce")
    for feature in NUMERIC_FEATURES:
        if feature == "amenities_count":
            continue
        frame[feature] = pd.to_numeric(frame[feature], errors="coerce")

    amenities = frame.pop("amenities").fillna("[]").astype(str).str.strip()
    frame["amenities_count"] = amenities.str.count('", "') + 1
    frame.loc[amenities.isin(["", "[]"]), "amenities_count"] = 0

    source_rows = len(frame)
    valid = frame[TARGET].notna() & (frame[TARGET] > 0) & (frame["accommodates"] > 0)
    frame = frame.loc[valid].copy()
    frame["minimum_nights"] = frame["minimum_nights"].clip(upper=365)

    cleaning = {
        "source_rows": int(source_rows),
        "training_eligible_rows": int(len(frame)),
        "excluded_rows": int(source_rows - len(frame)),
        "rules": [
            "price must be numeric and greater than zero",
            "accommodates must be greater than zero",
            "minimum_nights is capped at 365",
        ],
    }
    return frame, cleaning


def apply_price_scope(train_features, test_features, train_target, test_target):
    training_prices = pd.DataFrame(
        {
            "city": train_features["city"],
            "price": train_target,
        }
    )
    thresholds = training_prices.groupby("city")["price"].quantile(PRICE_SCOPE_QUANTILE)
    train_thresholds = train_features["city"].map(thresholds)
    test_thresholds = test_features["city"].map(thresholds)
    train_mask = train_target <= train_thresholds
    test_mask = test_target <= test_thresholds

    scope = {
        "quantile": PRICE_SCOPE_QUANTILE,
        "threshold_source": "training partition only",
        "city_maximum_supported_price": {
            city: float(value) for city, value in thresholds.items()
        },
        "excluded_train_rows": int((~train_mask).sum()),
        "excluded_test_rows": int((~test_mask).sum()),
        "reason": "Limit V1 to the typical city market and reduce extreme luxury-listing influence.",
    }
    return (
        train_features.loc[train_mask],
        test_features.loc[test_mask],
        train_target.loc[train_mask],
        test_target.loc[test_mask],
        scope,
    )


def build_models():
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]
    )
    one_hot_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    min_frequency=50,
                ),
            ),
        ]
    )
    ridge_preprocessor = ColumnTransformer(
        [
            ("categorical", one_hot_pipeline, CATEGORICAL_FEATURES),
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ]
    )

    target_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                TargetEncoder(
                    target_type="continuous",
                    smooth="auto",
                    cv=5,
                    shuffle=True,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    tree_numeric_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median", add_indicator=True))]
    )
    gradient_preprocessor = ColumnTransformer(
        [
            ("categorical", target_pipeline, CATEGORICAL_FEATURES),
            ("numeric", tree_numeric_pipeline, NUMERIC_FEATURES),
        ]
    )

    return {
        "median_baseline": TransformedTargetRegressor(
            regressor=DummyRegressor(strategy="median"),
            func=np.log1p,
            inverse_func=np.expm1,
        ),
        "ridge_regression": TransformedTargetRegressor(
            regressor=Pipeline(
                [
                    ("preprocessor", ridge_preprocessor),
                    ("model", Ridge(alpha=10.0, solver="lsqr")),
                ]
            ),
            func=np.log1p,
            inverse_func=np.expm1,
        ),
        "histogram_gradient_boosting": TransformedTargetRegressor(
            regressor=Pipeline(
                [
                    ("preprocessor", gradient_preprocessor),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            learning_rate=0.08,
                            max_iter=250,
                            max_leaf_nodes=31,
                            min_samples_leaf=40,
                            l2_regularization=1.0,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
            func=np.log1p,
            inverse_func=np.expm1,
        ),
    }


def metric_values(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(root_mean_squared_error(actual, predicted)),
        "r2": float(r2_score(actual, predicted)),
    }


def evaluate_model(model, features, target):
    predicted = np.maximum(model.predict(features), 0)
    result = {
        "overall_local_currency_units": metric_values(target, predicted),
        "log_price": metric_values(np.log1p(target), np.log1p(predicted)),
        "by_city_local_currency_units": {},
    }

    city_normalized_mae = []
    for city in sorted(features["city"].unique()):
        city_mask = features["city"] == city
        city_actual = target.loc[city_mask]
        city_predicted = predicted[city_mask.to_numpy()]
        city_metrics = metric_values(city_actual, city_predicted)
        city_median = float(city_actual.median())
        city_metrics["median_actual_price"] = city_median
        city_metrics["normalized_mae"] = (
            float(city_metrics["mae"] / city_median) if city_median > 0 else None
        )
        result["by_city_local_currency_units"][city] = city_metrics
        if city_metrics["normalized_mae"] is not None:
            city_normalized_mae.append(city_metrics["normalized_mae"])

    result["median_city_normalized_mae"] = float(np.median(city_normalized_mae))
    return result


def training_metadata(frame, cleaning, scope, dataset_path):
    return {
        "model_version": "1.0.0",
        "target": TARGET,
        "target_interpretation": "nightly price in the selected city's local currency",
        "dataset": {
            "file": dataset_path.name,
            "sha256": sha256(dataset_path),
        },
        "features": {
            "categorical": CATEGORICAL_FEATURES,
            "numeric": NUMERIC_FEATURES,
        },
        "cleaning": cleaning,
        "price_scope": scope,
        "split": {
            "strategy": "random train-test split stratified by city",
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
        },
        "observed_categories": {
            feature: sorted(frame[feature].dropna().astype(str).unique().tolist())
            for feature in CATEGORICAL_FEATURES
        },
        "city_neighbourhoods": {
            city: sorted(rows["neighbourhood"].dropna().astype(str).unique().tolist())
            for city, rows in frame.groupby("city")
        },
        "city_coordinate_ranges": {
            city: {
                "latitude": {
                    "minimum": float(rows["latitude"].min()),
                    "maximum": float(rows["latitude"].max()),
                },
                "longitude": {
                    "minimum": float(rows["longitude"].min()),
                    "maximum": float(rows["longitude"].max()),
                },
            }
            for city, rows in frame.groupby("city")
        },
        "observed_numeric_ranges": {
            feature: {
                "minimum": float(frame[feature].min()),
                "maximum": float(frame[feature].max()),
            }
            for feature in NUMERIC_FEATURES
        },
        "limitations": [
            "Prices use different local currencies across cities.",
            "Overall raw-currency metrics are not directly comparable across cities.",
            "Historical listing prices may not represent current market conditions.",
            "The dataset contains encoding replacements and missing feature values.",
            "The estimate does not include every factor that can affect an Airbnb price.",
            "V1 excludes prices above the training partition's city-specific 99th percentile.",
        ],
    }


def main():
    args = parse_args()
    if not args.listings.is_file():
        raise FileNotFoundError(f"Listings dataset not found: {args.listings}")

    frame, cleaning = load_training_data(args.listings)
    features = frame[FEATURES]
    target = frame[TARGET]
    train_features, test_features, train_target, test_target = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=features["city"],
    )
    (
        train_features,
        test_features,
        train_target,
        test_target,
        scope,
    ) = apply_price_scope(train_features, test_features, train_target, test_target)

    models = build_models()
    evaluations = {}
    fitted_models = {}
    for name, model in models.items():
        print(f"Training {name}...")
        model.fit(train_features, train_target)
        evaluations[name] = evaluate_model(model, test_features, test_target)
        fitted_models[name] = model

    selected_name = min(
        evaluations,
        key=lambda name: evaluations[name]["median_city_normalized_mae"],
    )
    metadata = training_metadata(frame, cleaning, scope, args.listings)
    metadata["train_rows"] = int(len(train_features))
    metadata["test_rows"] = int(len(test_features))
    metadata["selection_metric"] = "median_city_normalized_mae"
    metadata["selected_model"] = selected_name
    metadata["evaluations"] = evaluations

    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": fitted_models[selected_name], "metadata": metadata},
        args.model_output,
        compress=3,
    )
    metadata["model_artifact"] = {
        "file": args.model_output.name,
        "sha256": sha256(args.model_output),
        "size_bytes": args.model_output.stat().st_size,
    }

    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Selected {selected_name}")
    print(f"Wrote model to {args.model_output}")
    print(f"Wrote evaluation to {args.metrics_output}")


if __name__ == "__main__":
    main()
