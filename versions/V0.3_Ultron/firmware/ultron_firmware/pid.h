#pragma once
#include <stdint.h>

// Wheel velocity PID (P0). Output is PWM in [-255, 255].
typedef struct {
    float kp, ki, kd;          // gains
    float integral;            // anti-windup clamped integrator
    float prev_measurement;    // for derivative-on-measurement
    float out_limit;           // PWM saturation
    float int_limit;           // integrator clamp
    float ff_gain;             // feed-forward = v/MAX_SPEED_MPS * 255 * ff_gain
    bool  first;               // first update (skip derivative)
} PidCtrl;

void pid_init(PidCtrl* c, float kp, float ki, float kd,
              float ff_gain, float out_limit, float int_limit);
void pid_reset(PidCtrl* c);
float pid_update(PidCtrl* c, float setpoint, float measurement, float dt,
                 float max_speed_mps);
