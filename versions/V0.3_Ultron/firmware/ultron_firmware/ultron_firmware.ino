#include <Wire.h>
#include <avr/wdt.h>
#include "config.h"
#include "encoders.h"
#include "motors.h"
#include "imu.h"
#include "protocol.h"
#include "faults.h"
#include "tx_queue.h"
#include "power.h"
#include "pid.h"

volatile uint8_t fault_flags   = 0x00;
float  target_vel_left         = 0.0f;
float  target_vel_right        = 0.0f;
uint32_t last_cmd_vel_ms       = 0;
uint32_t last_heartbeat_ms     = 0;
bool     heartbeat_initialized = false;

uint8_t rx_buf[64]; uint8_t tx_tmp[TX_MAX_PKT_SIZE];
uint8_t rx_state=0, rx_type, rx_len, rx_idx;
uint8_t imu_fail_count=0, overcurrent_count=0, tx_decim=0;
uint32_t last_enc_ms=0, last_loop_us=0;
int32_t  last_total_ticks=0;

static PidCtrl pid_left, pid_right;   // P0: wheel velocity PID

int freeRam(){extern int __heap_start,*__brkval;int v;
  return (int)&v-(__brkval==0?(int)&__heap_start:(int)__brkval);}

// E-Stop: D2=PE4=INT4, uses EICRB (not EICRA)
ISR(INT4_vect){
    SET_FAULT(FAULT_BIT_ESTOP);
    OCR4A=0; OCR4B=0; OCR3A=0; OCR3C=0; // Zero ALL PWM channels (v4.2r2 D1)
    PORTG&=~(1<<PG5);                   // D4=LEFT_EN=PG5  → LOW
    PORTH&=~(1<<PH5);                   // D8=RIGHT_EN=PH5 → LOW
}

bool parse_byte(uint8_t b){
    switch(rx_state){
    case 0: if(b==HDR_IN){rx_state=1;}break;
    case 1: rx_type=b;rx_buf[0]=b;rx_state=2;break;
    case 2: rx_len=b;rx_buf[1]=b;rx_idx=2;
            rx_state=(rx_len==0)?4:3;break;
    case 3: rx_buf[rx_idx++]=b;
            if(rx_idx>=2+rx_len)rx_state=4;break;
    case 4:{uint8_t c=crc8(rx_buf,rx_idx);rx_state=0;return(c==b);}
    } return false;
}

void process_packet(){
    uint8_t *p=&rx_buf[2];
    switch(rx_type){
    case 0x01:
        if(rx_len!=8)break;
        {float vl=ntoh_float(&p[0]),vr=ntoh_float(&p[4]);
         if(isnan(vl)||isinf(vl)||isnan(vr)||isinf(vr))break;
         target_vel_left=constrain(vl,-MAX_SPEED_MPS,MAX_SPEED_MPS);
         target_vel_right=constrain(vr,-MAX_SPEED_MPS,MAX_SPEED_MPS);
         last_cmd_vel_ms=millis(); CLEAR_FAULT(FAULT_BIT_WATCHDOG);}break;
    case 0x02:
        SET_FAULT(FAULT_BIT_ESTOP);
        OCR4A=0;OCR4B=0;OCR3A=0;OCR3C=0;
        PORTG&=~(1<<PG5);PORTH&=~(1<<PH5);
        break;
    case 0x03:
        noInterrupts();
        left_encoder_count=right_encoder_count=0;
        interrupts();break;
    case 0x05:
        last_heartbeat_ms=millis();
        heartbeat_initialized=true;
        CLEAR_FAULT(FAULT_BIT_HEARTBEAT);break;
    // v4.2 B7: clear faults ONLY after the E-stop button is physically
    // released. Keeps latching for safety, adds a deliberate 2-step recovery.
    case 0x07:
        if(!ESTOP_LATCHED()){ fault_flags = 0; }
        break;
    }
}

void setup(){
    uint8_t m=MCUSR; MCUSR=0; wdt_disable();
    Serial.begin(SERIAL_BAUD);
    Wire.begin(); Wire.setClock(400000);
    init_encoders(); init_motor_pwm(); init_imu(); init_tx_queue();

    // P0: init wheel velocity PID (closed loop around measured wheel speed).
    pid_init(&pid_left,  PID_KP, PID_KI, PID_KD,
             PID_FEEDFORWARD, PID_OUTPUT_LIMIT, PID_INTEGRAL_LIMIT);
    pid_init(&pid_right, PID_KP, PID_KI, PID_KD,
             PID_FEEDFORWARD, PID_OUTPUT_LIMIT, PID_INTEGRAL_LIMIT);

    // E-Stop INT4: EICRB register, falling edge
    pinMode(ESTOP_PIN,INPUT_PULLUP);
    EICRB|=(1<<ISC41); EICRB&=~(1<<ISC40);
    EIMSK|=(1<<INT4);

    pinMode(HEARTBEAT_LED,OUTPUT); pinMode(FAULT_LED,OUTPUT);
    digitalWrite(HEARTBEAT_LED,LOW); digitalWrite(FAULT_LED,LOW);
    last_cmd_vel_ms=last_heartbeat_ms=millis();

    if(m&(1<<WDRF))
        Serial.println(F("WARN: Previous reset was HW WDT"));
    Serial.print(F("ultron ready. RAM:"));
    Serial.println(freeRam());

    wdt_enable(WDTO_8S);  // HW WDT: 8s
}

void loop(){
    uint32_t now_us=micros();
    if((now_us-last_loop_us)<LOOP_PERIOD_US){
        background_tasks(); return;
    }
    last_loop_us=now_us; wdt_reset();

    // STEP 1: Atomic encoder read
    noInterrupts();
    int32_t lc=left_encoder_count;
    int32_t rc=right_encoder_count;
    interrupts();

    // STEP 2: Per-loop wheel deltas + measured speed (host does final pose;
    // on-MCU odom is harmless and feeds the P0 PID).
    static int32_t plc=0,prc=0;
    int32_t dl=lc-plc, dr=rc-prc; plc=lc; prc=rc;
    float vmeas_l = (float)dl*METERS_PER_TICK/PID_PERIOD_S;
    float vmeas_r = (float)dr*METERS_PER_TICK/PID_PERIOD_S;
    static float flt_l=0.0f, flt_r=0.0f;      // low-pass measured speed
    flt_l += PID_SPEED_LPF_ALPHA*(vmeas_l-flt_l);
    flt_r += PID_SPEED_LPF_ALPHA*(vmeas_r-flt_r);

    // STEP 3: IMU
    ImuData imu; bool imu_ok=read_imu(&imu);
    if(!imu_ok){if(++imu_fail_count>=IMU_FAIL_THRESHOLD)SET_FAULT(FAULT_BIT_IMU);}
    else{imu_fail_count=0; CLEAR_FAULT(FAULT_BIT_IMU);}

    // STEP 4: Serial RX (v4.2r2 D4: 1200µs window → full 12-byte velocity pkt)
    while(Serial.available()&&(micros()-now_us)<SERIAL_RX_WINDOW_US){
        if(parse_byte((uint8_t)Serial.read()))process_packet();
    }

    // STEP 5: Software watchdogs
    uint32_t now_ms=millis();
    if((now_ms-last_cmd_vel_ms)>CMD_VEL_TIMEOUT_MS){
        SET_FAULT(FAULT_BIT_WATCHDOG);
        target_vel_left=target_vel_right=0.0f;
    }
    if(heartbeat_initialized){
        if((now_ms-last_heartbeat_ms)>HEARTBEAT_TIMEOUT_MS){
            SET_FAULT(FAULT_BIT_HEARTBEAT);
            target_vel_left=target_vel_right=0.0f;
        }
    } else if((now_ms-last_heartbeat_ms)>5000UL){
        heartbeat_initialized=true; // 5s boot grace
    }

    // STEP 6: Motor output (v4.2r2 D3: re-enable EN pins after fault clear).
    // P0: closed-loop PID on measured wheel speed; open-loop fallback when
    // WHEEL_PID_ENABLED=0.
    if(ANY_MOTOR_FAULT()){
        OCR4A=0;OCR4B=0;OCR3A=0;OCR3C=0;
        PORTG&=~(1<<PG5);PORTH&=~(1<<PH5);   // keep EN low while faulted
        pid_reset(&pid_left); pid_reset(&pid_right);
    } else {
        PORTG|=(1<<PG5);PORTH|=(1<<PH5);     // re-enable drivers
        if(WHEEL_PID_ENABLED){
            int16_t pl=(int16_t)pid_update(&pid_left,target_vel_left,flt_l,
                                           PID_PERIOD_S,MAX_SPEED_MPS);
            int16_t pr=(int16_t)pid_update(&pid_right,target_vel_right,flt_r,
                                           PID_PERIOD_S,MAX_SPEED_MPS);
            set_motor_pwm(MOTOR_LEFT, pl);
            set_motor_pwm(MOTOR_RIGHT,pr);
        } else {
            set_motor_pwm(MOTOR_LEFT, velocity_to_pwm(target_vel_left));
            set_motor_pwm(MOTOR_RIGHT,velocity_to_pwm(target_vel_right));
        }
    }

    // STEP 7: Encoder fault check (both wheels now count — v4.2 B1)
    // NOTE: use labs() — abs() is 16-bit int on AVR and overflows >32767.
    int32_t tot=labs(lc)+labs(rc);
    if(tot!=last_total_ticks){last_total_ticks=tot;last_enc_ms=now_ms;}
    if((fabs(target_vel_left)>0.05f||fabs(target_vel_right)>0.05f)&&
       (now_ms-last_enc_ms)>ENCODER_FAULT_MS)
        SET_FAULT(FAULT_BIT_ENCODER);

    // STEP 8: Enqueue TX
    if(++tx_decim>=TX_DECIMATION){
        tx_decim=0;
        uint8_t n=build_encoder_packet(tx_tmp,lc,rc,now_ms);
        tx_enqueue(tx_tmp,n);
        if(imu_ok){n=build_imu_packet(tx_tmp,&imu);tx_enqueue(tx_tmp,n);}
        // Publish motor current every 3rd cycle (~10 Hz)
        static uint8_t curr_div=0;
        if(++curr_div>=3){
            curr_div=0;
            float cl=read_current(CURRENT_SENSE_L_PIN);
            float cr=read_current(CURRENT_SENSE_R_PIN);
            n=build_current_packet(tx_tmp,cl,cr);
            tx_enqueue(tx_tmp,n);
        }
    }
    if(fault_flags){
        uint8_t n=build_fault_packet(tx_tmp,fault_flags);
        tx_enqueue(tx_tmp,n);
    }

    // STEP 9: Drain TX
    tx_drain();
    digitalWrite(FAULT_LED,fault_flags?HIGH:LOW);
}
