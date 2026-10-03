import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def generate_synthetic_sensor_dataset(num_samples=1200):
    """
    Generates synthetic HC-SR04 ultrasonic time-series sensor data for training and evaluation.
    Distance (cm): closer = denser/longer queue.
    Features:
      - distance: raw reading (cm)
      - rolling_avg_dist: 5-sample smoothed average
      - rate_of_change: gradient of distance over time
      - hour_of_day: 0-23
      - day_of_week: 0-6
    Labels:
      - 0: Short Wait (Distance > 250 cm)
      - 1: Medium Wait (100 cm <= Distance <= 250 cm)
      - 2: Long / Congested Wait (Distance < 100 cm)
    """
    np.random.seed(42)
    timestamps = pd.date_range("2026-09-01", periods=num_samples, freq="15s")
    
    # Distance profile with noise and congestion spikes
    base_dist = np.random.uniform(30, 380, num_samples)
    dist_series = pd.Series(base_dist)
    
    rolling_avg = dist_series.rolling(window=5, min_periods=1).mean().values
    rate_of_change = np.gradient(rolling_avg)
    
    hours = timestamps.hour.values
    days = timestamps.dayofweek.values

    # Determine ground-truth queue state
    labels = []
    for d in rolling_avg:
        if d < 100:
            labels.append(2)  # Long
        elif d <= 250:
            labels.append(1)  # Medium
        else:
            labels.append(0)  # Short

    df = pd.DataFrame({
        "raw_distance": base_dist,
        "rolling_avg_dist": rolling_avg,
        "rate_of_change": rate_of_change,
        "hour_of_day": hours,
        "day_of_week": days,
        "queue_state": labels
    })
    return df


def train_and_compare_classifiers():
    """Trains Random Forest and SVM classifiers to validate sensor-based queue classification."""
    print("\n[ML Pipeline] Generating calibrated sensor dataset...")
    df = generate_synthetic_sensor_dataset()

    X = df[["raw_distance", "rolling_avg_dist", "rate_of_change", "hour_of_day", "day_of_week"]]
    y = df["queue_state"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # 1. Random Forest Classifier
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_preds)

    # 2. Support Vector Machine (RBF Kernel) baseline
    svm = SVC(kernel="rbf", C=1.0)
    svm.fit(X_train, y_train)
    svm_preds = svm.predict(X_test)
    svm_acc = accuracy_score(y_test, svm_preds)

    print("\n" + "=" * 50)
    print("CLASSIFIER BENCHMARK (SENSOR TIME-SERIES)")
    print("=" * 50)
    print(f"Random Forest Accuracy : {rf_acc * 100:.2f}%")
    print(f"SVM Baseline Accuracy  : {svm_acc * 100:.2f}%")
    print("\nDetailed Random Forest Report:")
    print(classification_report(y_test, rf_preds, target_names=["Short Wait", "Medium Wait", "Long Wait"]))

    return rf, svm

if __name__ == "__main__":
    train_and_compare_classifiers()
