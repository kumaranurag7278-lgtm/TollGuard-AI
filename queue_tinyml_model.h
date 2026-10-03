/*
 * ==============================================================================
 * TinyML Edge AI Model for ESP32 (Auto-Generated)
 * Project #190: AI Queue & Toll Enforcement Node
 *
 * Runs on-chip inference directly on the ESP32 Xtensa Dual-Core CPU!
 * Features:
 *   - distance_cm: Current HC-SR04 reading
 *   - rolling_avg_cm: Exponential / rolling moving average
 *   - rate_of_change: Delta distance per measurement interval
 *
 * Classes:
 *   0 = SHORT_WAIT  (Low congestion / Fast clearance)
 *   1 = MEDIUM_WAIT (Moderate queue)
 *   2 = LONG_WAIT   (Congested / Bottleneck)
 * ==============================================================================
 */

#ifndef QUEUE_TINYML_MODEL_H
#define QUEUE_TINYML_MODEL_H

enum QueueState {
    SHORT_WAIT = 0,
    MEDIUM_WAIT = 1,
    LONG_WAIT = 2
};

inline const char* getQueueStateName(QueueState state) {
    switch (state) {
        case SHORT_WAIT:  return "SHORT_WAIT";
        case MEDIUM_WAIT: return "MEDIUM_WAIT";
        case LONG_WAIT:   return "LONG_WAIT";
        default:          return "UNKNOWN";
    }
}

// Embedded Edge AI Inference Function
inline QueueState predictQueueStateOnChip(float distance_cm, float rolling_avg_cm, float rate_of_change) {
    // Decision Tree logic compiled into branch instructions
    if (rolling_avg_cm <= 99.5f) {
        return LONG_WAIT;
    } else {
        if (rolling_avg_cm <= 230.5f) {
            return MEDIUM_WAIT;
        } else {
            return SHORT_WAIT;
        }
    }
}

#endif // QUEUE_TINYML_MODEL_H
