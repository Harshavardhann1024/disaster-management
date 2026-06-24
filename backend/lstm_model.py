"""
lstm_model.py — EcoRescue LSTM Risk Prediction Module
======================================================
Framework : PyTorch 2.x  (TensorFlow not available on Python 3.14)
Purpose   : Train a 1-layer LSTM on ZoneHistory risk_score time-series
            and predict the next risk score for any zone.

Data source : ZoneHistory table
  - zone_id       INT
  - risk_score    FLOAT   ← this is what we train / predict on
  - detected_people INT
  - recorded_at   TIMESTAMP

API (used by main.py):
  train_lstm(zone_id)   → str   (status message)
  predict_next(zone_id) → dict  {zone_id, predicted_risk_score, predicted_level}
  save_to_history(...)  → None  (insert a new reading)
"""

import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
SEQUENCE_LEN = 10          # how many past readings to feed the LSTM
HIDDEN_SIZE  = 64          # LSTM hidden units
EPOCHS       = 40          # training epochs
BATCH_SIZE   = 16
LR           = 0.001       # Adam learning rate
MAX_SCORE    = 200.0       # normalization ceiling (risk_score cap)

MODEL_DIR = Path(__file__).parent / "lstm_models"
MODEL_DIR.mkdir(exist_ok=True)

DB_CFG = {
    "host":       "localhost",
    "user":       "root",
    "password":   "Harsha@2426",
    "database":   "ecorescue",
    "autocommit": True,
}

# ──────────────────────────────────────────
# DB HELPER
# ──────────────────────────────────────────
def _get_db():
    import mysql.connector
    return mysql.connector.connect(**DB_CFG)


# ──────────────────────────────────────────
# RISK LABEL HELPER
# ──────────────────────────────────────────
def get_risk_label(score: float) -> str:
    if score >= 100:
        return "Severe"
    elif score >= 70:
        return "Elevated"
    elif score >= 40:
        return "Caution"
    return "Safe"


# ──────────────────────────────────────────
# DATABASE I/O
# ──────────────────────────────────────────
def fetch_history(zone_id: int, limit: int = 200) -> list:
    """Fetch ordered risk_score history for a zone."""
    conn = _get_db()
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT risk_score FROM ZoneHistory
        WHERE zone_id = %s
        ORDER BY recorded_at ASC
        LIMIT %s
        """,
        (zone_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [float(r[0]) for r in rows]


def save_to_history(zone_id: int, risk_score: float, detected_people: int):
    """Insert one new reading into ZoneHistory."""
    conn = _get_db()
    cur  = conn.cursor()
    cur.execute(
        """
        INSERT INTO ZoneHistory (zone_id, risk_score, detected_people)
        VALUES (%s, %s, %s)
        """,
        (zone_id, risk_score, detected_people),
    )
    cur.close()
    conn.close()


# ──────────────────────────────────────────
# SYNTHETIC SEED DATA (fallback when DB empty)
# ──────────────────────────────────────────
def _generate_seed_data(zone_id: int) -> list:
    rng  = np.random.default_rng(seed=zone_id * 42)
    base = rng.uniform(20, 80)
    data = []
    for i in range(50):
        noise = rng.uniform(-8, 8)
        val   = float(np.clip(base + noise + i * 0.3, 0, 150))
        data.append(round(val, 2))
    return data


# ──────────────────────────────────────────
# LSTM MODEL DEFINITION
# ──────────────────────────────────────────
class LSTMPredictor(nn.Module):
    """
    Single-layer LSTM → fully-connected output.
    Input  shape: (batch, seq_len, 1)  — normalised risk scores
    Output shape: (batch, 1)           — next normalised risk score
    """
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=1,
            hidden_size=HIDDEN_SIZE,
            num_layers=1,
            batch_first=True,
        )
        self.fc = nn.Linear(HIDDEN_SIZE, 1)

    def forward(self, x):
        out, _ = self.lstm(x)       # (batch, seq_len, hidden)
        out     = out[:, -1, :]     # take last time-step
        return self.fc(out)         # (batch, 1)


# ──────────────────────────────────────────
# MODEL FILE PATH
# ──────────────────────────────────────────
def _model_path(zone_id: int) -> Path:
    return MODEL_DIR / f"zone_{zone_id}.pth"


# ──────────────────────────────────────────
# DATA PREPARATION
# ──────────────────────────────────────────
def _prepare_sequences(data: list):
    """
    Turn flat list of floats into supervised (X, y) tensors.
    Normalises to [0, 1] using MAX_SCORE.
    Returns: X_tensor (N, seq_len, 1), y_tensor (N, 1), nothing else.
    """
    arr = np.array(data, dtype=np.float32) / MAX_SCORE   # normalise

    X, y = [], []
    for i in range(len(arr) - SEQUENCE_LEN):
        X.append(arr[i : i + SEQUENCE_LEN])
        y.append(arr[i + SEQUENCE_LEN])

    X_tensor = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)  # (N, seq, 1)
    y_tensor = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1)  # (N, 1)
    return X_tensor, y_tensor


# ──────────────────────────────────────────
# PUBLIC API — TRAIN
# ──────────────────────────────────────────
def train_lstm(zone_id: int) -> str:
    """
    Train LSTM on ZoneHistory data for one zone.
    Saves weights to lstm_models/zone_<id>.pth
    Returns a human-readable status string.
    """
    print(f"[LSTM] Training zone {zone_id}...")

    # 1. Load data
    data = fetch_history(zone_id, limit=300)
    if len(data) < SEQUENCE_LEN + 1:
        data = _generate_seed_data(zone_id)
        print(f"[LSTM] Zone {zone_id}: not enough DB rows, using seed data.")

    # 2. Prepare sequences
    X_tensor, y_tensor = _prepare_sequences(data)
    n_samples = X_tensor.size(0)
    print(f"[LSTM] Zone {zone_id}: {len(data)} readings -> {n_samples} sequences")

    # 3. Build model + optimizer
    model     = LSTMPredictor()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn   = nn.MSELoss()

    # 4. Train
    model.train()
    for epoch in range(EPOCHS):
        perm = torch.randperm(n_samples)
        epoch_loss = 0.0
        for start in range(0, n_samples, BATCH_SIZE):
            idx      = perm[start : start + BATCH_SIZE]
            bX, by   = X_tensor[idx], y_tensor[idx]
            optimizer.zero_grad()
            pred     = model(bX)
            loss     = loss_fn(pred, by)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        if (epoch + 1) % 10 == 0:
            print(f"[LSTM] Zone {zone_id} | Epoch {epoch+1}/{EPOCHS} | Loss: {epoch_loss:.4f}")

    # 5. Save weights
    torch.save(model.state_dict(), str(_model_path(zone_id)))
    msg = f"Zone {zone_id} LSTM trained on {len(data)} samples ({n_samples} sequences). Model saved."
    print(f"[LSTM] {msg}")
    return msg


# ──────────────────────────────────────────
# PUBLIC API — PREDICT
# ──────────────────────────────────────────
def predict_next(zone_id: int) -> dict:
    """
    Predict the next risk score for a zone using the saved LSTM model.
    If no model exists yet, trains one first.
    Returns: { zone_id, predicted_risk_score, predicted_level }
    """
    mp = _model_path(zone_id)

    # Auto-train if no model file exists
    if not mp.exists():
        print(f"[LSTM] No model for zone {zone_id} — training now...")
        train_lstm(zone_id)

    # Load model
    model = LSTMPredictor()
    model.load_state_dict(torch.load(str(mp), weights_only=True))
    model.eval()

    # Fetch recent history
    data = fetch_history(zone_id, limit=SEQUENCE_LEN + 50)
    if len(data) < SEQUENCE_LEN:
        data = _generate_seed_data(zone_id)

    # Build input sequence (last SEQUENCE_LEN readings, normalised)
    recent     = np.array(data[-SEQUENCE_LEN:], dtype=np.float32) / MAX_SCORE
    X_input    = torch.tensor(recent, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)  # (1, seq, 1)

    # Predict
    with torch.no_grad():
        pred_norm = model(X_input).item()

    predicted_score = round(float(np.clip(pred_norm * MAX_SCORE, 0.0, MAX_SCORE)), 2)
    predicted_level = get_risk_label(predicted_score)

    return {
        "zone_id":              zone_id,
        "predicted_risk_score": predicted_score,
        "predicted_level":      predicted_level,
    }


# ──────────────────────────────────────────
# SAVE PREDICTIONS TO DATABASE (FOR PROOF)
# ──────────────────────────────────────────
def save_prediction(zone_id: int, predicted_score: float, predicted_level: str, actual_score: float = None, actual_level: str = None):
    """
    Save LSTM prediction to database for tracking & proof.
    Can be called with or without actual values.
    """
    try:
        conn = _get_db()
        cur = conn.cursor()
        
        accuracy = None
        if actual_score is not None:
            # Calculate accuracy as percentage (how close prediction was)
            diff = abs(predicted_score - actual_score)
            accuracy = max(0, 100 - (diff / 200 * 100))  # 200 is max score
        
        cur.execute(
            """
            INSERT INTO lstmpredictions 
            (zone_id, predicted_risk_score, predicted_risk_level, 
             actual_risk_score, actual_risk_level, prediction_accuracy)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (zone_id, predicted_score, predicted_level, actual_score, actual_level, accuracy)
        )
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[LSTM] Error saving prediction: {e}")
        return False


def get_prediction_accuracy(zone_id: int, days: int = 1) -> dict:
    """
    Get prediction accuracy stats for a zone.
    Returns average accuracy, count, etc.
    """
    try:
        conn = _get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute(
            """
            SELECT 
                COUNT(*) as total_predictions,
                AVG(prediction_accuracy) as avg_accuracy,
                MAX(prediction_accuracy) as best_accuracy,
                MIN(prediction_accuracy) as worst_accuracy,
                COUNT(CASE WHEN prediction_accuracy > 80 THEN 1 END) as high_accuracy_count
            FROM lstmpredictions
            WHERE zone_id = %s AND created_at > DATE_SUB(NOW(), INTERVAL %s DAY)
            """,
            (zone_id, days)
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        return result or {
            "total_predictions": 0,
            "avg_accuracy": None,
            "best_accuracy": None,
            "worst_accuracy": None,
            "high_accuracy_count": 0
        }
    except Exception as e:
        print(f"[LSTM] Error fetching accuracy: {e}")
        return {}


# ──────────────────────────────────────────
# QUICK TEST — run directly
# ──────────────────────────────────────────
if __name__ == "__main__":
    for zid in [1, 2, 3, 4]:
        print(f"\n{'='*40}")
        print(train_lstm(zid))
        result = predict_next(zid)
        print(f"Zone {zid} prediction -> score={result['predicted_risk_score']}  level={result['predicted_level']}")
