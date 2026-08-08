#pragma once
#include <stdint.h>
#include "config.h"
void init_motor_pwm();
void set_motor_pwm(uint8_t motor, int16_t pwm);
int16_t velocity_to_pwm(float v);
