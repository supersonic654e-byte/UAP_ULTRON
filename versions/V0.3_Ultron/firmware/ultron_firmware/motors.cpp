#include <Arduino.h>
#include <math.h>
#include "motors.h"
#include "config.h"

void init_motor_pwm() {
    pinMode(LEFT_MOTOR_PWM,OUTPUT); pinMode(LEFT_MOTOR_LPWM,OUTPUT);
    pinMode(LEFT_MOTOR_EN,OUTPUT);  pinMode(RIGHT_MOTOR_PWM,OUTPUT);
    pinMode(RIGHT_MOTOR_LPWM,OUTPUT);pinMode(RIGHT_MOTOR_EN,OUTPUT);
    digitalWrite(LEFT_MOTOR_EN,LOW); digitalWrite(RIGHT_MOTOR_EN,LOW);

    // Timer4: LEFT motor, OC4A=D6 (fwd) + OC4B=D7 (rev), Fast PWM, prescaler=8
    TCCR4A=(1<<COM4A1)|(1<<COM4B1)|(1<<WGM41);
    TCCR4B=(1<<WGM43)|(1<<WGM42)|(1<<CS41);
    ICR4=MOTOR_PWM_TOP; OCR4A=0; OCR4B=0;

    // Timer3: RIGHT motor, OC3A=D5 (fwd) + OC3C=D3 (rev), Fast PWM, prescaler=8
    TCCR3A=(1<<COM3A1)|(1<<COM3C1)|(1<<WGM31);
    TCCR3B=(1<<WGM33)|(1<<WGM32)|(1<<CS31);
    ICR3=MOTOR_PWM_TOP; OCR3A=0; OCR3C=0;

    digitalWrite(LEFT_MOTOR_EN,HIGH); digitalWrite(RIGHT_MOTOR_EN,HIGH);
}

void set_motor_pwm(uint8_t motor, int16_t pwm) {
    // v4.2r2 D1: drive the forward or reverse channel, zero the other.
    if(motor==MOTOR_LEFT){
        if(pwm>=0){ OCR4A=map(pwm,0,255,0,MOTOR_PWM_TOP); OCR4B=0; }
        else      { OCR4A=0; OCR4B=map(-pwm,0,255,0,MOTOR_PWM_TOP); }
    } else {
        if(pwm>=0){ OCR3A=map(pwm,0,255,0,MOTOR_PWM_TOP); OCR3C=0; }
        else      { OCR3A=0; OCR3C=map(-pwm,0,255,0,MOTOR_PWM_TOP); }
    }
}

int16_t velocity_to_pwm(float v) {
    // teleop clamp 0.45 m/s; autonomous is limited earlier by Nav2 (0.35)
    float p=(v/MAX_SPEED_MPS)*255.0f;
    if(fabs(p)<PWM_DEADZONE&&fabs(p)>0.0f)
        p=(p>0)?PWM_DEADZONE:-PWM_DEADZONE;
    return (int16_t)constrain(p,-255,255);
}
