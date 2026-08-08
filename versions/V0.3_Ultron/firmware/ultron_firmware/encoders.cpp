#include <Arduino.h>
#include "encoders.h"
#include "config.h"

volatile int32_t left_encoder_count  = 0;
volatile int32_t right_encoder_count = 0;
volatile bool    right_enc_a_prev    = false;
volatile bool    right_enc_b_prev    = false;

// Left: D18=PD3=INT3 (Ch A) + D19=PD2=INT2 (Ch B)
ISR(INT3_vect) {                        // Ch A changed
    bool a=(PIND&(1<<PD3))!=0;
    bool b=(PIND&(1<<PD2))!=0;
    left_encoder_count+=(a^b)?1:-1;
}
ISR(INT2_vect) {                        // Ch B changed
    bool a=(PIND&(1<<PD3))!=0;
    bool b=(PIND&(1<<PD2))!=0;
    left_encoder_count+=(a^b)?-1:1;
}

// v4.2 B1: Right: D52=PB1=PCINT1 + D51=PB2=PCINT2 (Group PCIE0, PCMSK0)
// Port B — correct for ATmega2560. WAS D23/D24 (Port A) → no PCINT → never
// counted. ISR now reads PINB.
ISR(PCINT0_vect) {
    bool a=(PINB&(1<<PB1))!=0;          // D52
    bool b=(PINB&(1<<PB2))!=0;          // D51
    if(a!=right_enc_a_prev)
        right_encoder_count+=(a^b)?1:-1;
    else if(b!=right_enc_b_prev)
        right_encoder_count+=(a^b)?-1:1;
    right_enc_a_prev=a; right_enc_b_prev=b;
}

void init_encoders() {
    pinMode(LEFT_ENC_A, INPUT_PULLUP);
    pinMode(LEFT_ENC_B, INPUT_PULLUP);
    // INT3 (D18/PD3) CHANGE: EICRA ISC3[1:0]=01
    EICRA|=(1<<ISC30); EICRA&=~(1<<ISC31);
    // INT2 (D19/PD2) CHANGE: EICRA ISC2[1:0]=01
    EICRA|=(1<<ISC20); EICRA&=~(1<<ISC21);
    EIMSK|=(1<<INT3)|(1<<INT2);

    pinMode(RIGHT_ENC_A, INPUT_PULLUP);   // D52 = PB1
    pinMode(RIGHT_ENC_B, INPUT_PULLUP);   // D51 = PB2
    // PCIE0 = Port B (PB0-PB7). D52=PB1=PCINT1, D51=PB2=PCINT2.
    PCICR|=(1<<PCIE0);
    PCMSK0|=(1<<PCINT1)|(1<<PCINT2);
    right_enc_a_prev=(PINB&(1<<PB1))!=0;
    right_enc_b_prev=(PINB&(1<<PB2))!=0;
}
