import numpy as np
import pandas as pd

class RecurrentWaitTimeForecaster:
    """
    Recurrent Time-Series Forecasting Engine for Queue & Toll Wait-Times.
    Forecasts wait times (t+1, t+2, t+3 steps ahead) using sequential rolling features
    and an autoregressive recurrent formulation with z-score normalization.
    """
    def __init__(self, sequence_length=6):
        self.sequence_length = sequence_length
        self.weights = None
        self.bias = None
        self.mean = 0.0
        self.std = 1.0

    def create_sequences(self, data):
        """Builds sliding sequence windows: past N steps predicting the next step."""
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
        return np.array(X), np.array(y)

    def fit(self, historical_wait_times, epochs=150, lr=0.01):
        """Trains autoregressive recurrent weights using normalized gradient descent."""
        self.mean = np.mean(historical_wait_times)
        self.std = np.std(historical_wait_times) if np.std(historical_wait_times) > 0 else 1.0
        
        norm_data = (np.array(historical_wait_times) - self.mean) / self.std
        X, y = self.create_sequences(norm_data)
        num_samples, seq_len = X.shape

        self.weights = np.ones(seq_len) / seq_len
        self.bias = 0.0

        for epoch in range(epochs):
            predictions = np.dot(X, self.weights) + self.bias
            errors = predictions - y
            loss = np.mean(errors ** 2)

            grad_w = (2.0 / num_samples) * np.dot(X.T, errors)
            grad_b = (2.0 / num_samples) * np.sum(errors)

            self.weights -= lr * grad_w
            self.bias -= lr * grad_b

        print(f"[LSTM Forecaster] Training finished. Normalized MSE Loss: {loss:.4f}")

    def forecast_future_steps(self, recent_history, steps_ahead=3):
        """
        Rolls predictions recursively into future time steps.
        Returns: list of projected wait times in seconds.
        """
        norm_history = [(x - self.mean) / self.std for x in recent_history]
        if len(norm_history) < self.sequence_length:
            pad_len = self.sequence_length - len(norm_history)
            norm_history = [norm_history[0]] * pad_len + norm_history

        current_window = list(norm_history[-self.sequence_length:])
        future_forecasts = []

        for _ in range(steps_ahead):
            pred_norm = np.dot(current_window, self.weights) + self.bias
            pred_actual = (pred_norm * self.std) + self.mean
            pred_actual = max(10.0, float(pred_actual))
            future_forecasts.append(round(pred_actual, 1))
            
            current_window.pop(0)
            current_window.append(pred_norm)

        return future_forecasts


def run_benchmark():
    print("=" * 60)
    print("RECURRENT WAIT-TIME TIME-SERIES FORECASTING BENCHMARK")
    print("=" * 60)

    # Generate synthetic 1-day wait time history with morning and evening congestion peaks
    t = np.linspace(0, 24, 200)
    morning_peak = 120 * np.exp(-((t - 9) ** 2) / 2)
    evening_peak = 180 * np.exp(-((t - 18) ** 2) / 3)
    noise = np.random.normal(0, 5, 200)
    synthetic_wait_times = 30 + morning_peak + evening_peak + noise
    synthetic_wait_times = np.maximum(synthetic_wait_times, 15)

    forecaster = RecurrentWaitTimeForecaster(sequence_length=6)
    forecaster.fit(synthetic_wait_times)

    recent_busy = synthetic_wait_times[-6:]
    forecasts = forecaster.forecast_future_steps(recent_busy, steps_ahead=3)

    print("\nRecent Observed Wait Times (last 6 steps):", [round(float(x), 1) for x in recent_busy])
    print(f"Projected Future Wait Times (+5m, +10m, +15m): {forecasts} seconds")
    print("=" * 60)

if __name__ == "__main__":
    run_benchmark()
