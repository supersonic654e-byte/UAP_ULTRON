#include "pid.h"

void pid_init(PidCtrl* c, float kp, float ki, float kd,
              float ff_gain, float out_limit, float int_limit) {
    if(!c) return;
    c->kp=kp; c->ki=ki; c->kd=kd;
    c->ff_gain=ff_gain; c->out_limit=out_limit; c->int_limit=int_limit;
    pid_reset(c);
}

void pid_reset(PidCtrl* c) {
    if(!c) return;
    c->integral=0.0f;
    c->prev_measurement=0.0f;
    c->first=true;
}

// Standard PID with:
//  - proportional on error
//  - integral (clamped, conditional integration when not saturated)
//  - derivative ON MEASUREMENT (avoids derivative kick on setpoint steps)
//  - velocity feed-forward so the controller only corrects residual error
float pid_update(PidCtrl* c, float setpoint, float measurement, float dt,
                 float max_speed_mps) {
    if(!c || dt<=0.0f) return 0.0f;
    float err = setpoint - measurement;

    float out = 0.0f;
    // Feed-forward term: nominal PWM for the requested speed.
    float ff = (setpoint/max_speed_mps) * c->out_limit * c->ff_gain;

    // Proportional.
    out += c->kp * err;

    // Derivative on measurement (damps noise, no kick).
    if(!c->first) {
        float dmeas = (measurement - c->prev_measurement)/dt;
        out -= c->kd * dmeas;
    }
    c->prev_measurement = measurement;

    // Integral with conditional integration (only when not saturated).
    float out_clamped = ff + out + c->integral;
    if(out_clamped < c->out_limit && out_clamped > -c->out_limit) {
        c->integral += c->ki * err * dt;
        if(c->integral >  c->int_limit) c->integral =  c->int_limit;
        if(c->integral < -c->int_limit) c->integral = -c->int_limit;
    }
    out = ff + out + c->integral;

    if(out >  c->out_limit) out =  c->out_limit;
    if(out < -c->out_limit) out = -c->out_limit;
    c->first=false;
    return out;
}
