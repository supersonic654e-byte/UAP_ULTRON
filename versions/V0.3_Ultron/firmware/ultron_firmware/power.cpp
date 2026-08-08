#include <Arduino.h>
#include "power.h"
#include "config.h"
#include "tx_queue.h"
#include "protocol.h"

extern volatile uint8_t fault_flags;   // defined in the .ino

static float read_current(uint8_t pin){
    float v=analogRead(pin)*(5.0f/1023.0f);
    return (v-ACS712_ZERO_V)/ACS712_MV_PER_A;        // Amps
}

float read_battery_voltage(){
    return analogRead(BATTERY_VOLTAGE_PIN)*BATTERY_ADC_SCALE;
}

void background_tasks(){
    uint32_t now=millis();
    static uint32_t last_batt_ms=0, last_curr_ms=0;
    static uint8_t ci=0, filled=0;
    static float curr_l[OVERCURRENT_SAMPLES], curr_r[OVERCURRENT_SAMPLES];

    // Battery: publish ~1 Hz; latch critical fault at < 10.5 V.
    if(now-last_batt_ms>=1000){
        last_batt_ms=now;
        float v=read_battery_voltage();
        if(v<BATTERY_CRITICAL_V) SET_FAULT(FAULT_BIT_BATTERY);
        uint8_t tmp[TX_MAX_PKT_SIZE];
        tx_enqueue(tmp, build_battery_packet(tmp, v));
    }
    // Current: sample every 100 ms; 5-sample window = 500 ms sustained.
    if(now-last_curr_ms>=100){
        last_curr_ms=now;
        curr_l[ci]=read_current(CURRENT_SENSE_L_PIN);
        curr_r[ci]=read_current(CURRENT_SENSE_R_PIN);
        ci=(uint8_t)((ci+1)%OVERCURRENT_SAMPLES);
        if(filled<OVERCURRENT_SAMPLES) filled++;
        if(filled==OVERCURRENT_SAMPLES){
            float sl=0, sr=0;
            for(uint8_t i=0;i<OVERCURRENT_SAMPLES;i++){ sl+=curr_l[i]; sr+=curr_r[i]; }
            if((sl/OVERCURRENT_SAMPLES)>CURRENT_FAULT_AMPS ||
               (sr/OVERCURRENT_SAMPLES)>CURRENT_FAULT_AMPS)
                SET_FAULT(FAULT_BIT_OVERCURRENT);
        }
    }
}
