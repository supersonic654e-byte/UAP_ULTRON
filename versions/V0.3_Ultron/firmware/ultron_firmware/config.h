#pragma once
#include <stdint.h>

// ── PINS (ATmega2560 R3 verified) ────────────────────────────────────────────
// v4.2r2 D1: native two-PWM BTS7960 control (one PWM per direction).
#define LEFT_MOTOR_PWM      6    // PH3 = Timer4 OC4A  (forward)
#define LEFT_MOTOR_LPWM     7    // PH4 = Timer4 OC4B  (reverse)
#define LEFT_MOTOR_EN       4    // PG5
#define RIGHT_MOTOR_PWM     5    // PE3 = Timer3 OC3A  (forward)
#define RIGHT_MOTOR_LPWM    3    // PE5 = Timer3 OC3C  (reverse)
#define RIGHT_MOTOR_EN      8    // PH5
// v4.2 B1: Right encoder moved from D23/D24 (Port A — NO PCINT on ATmega2560)
//          to D52/D51 (Port B). ISR reads PINB.
#define LEFT_ENC_A          18   // PD3 = INT3
#define LEFT_ENC_B          19   // PD2 = INT2
#define RIGHT_ENC_A         52   // PB1 = PCINT1 (PCIE0/PCMSK0)
#define RIGHT_ENC_B         51   // PB2 = PCINT2 (PCIE0/PCMSK0)
#define IMU_SDA             20   // PD1 = I2C SDA only
#define IMU_SCL             21   // PD0 = I2C SCL only
#define IMU_INT             22   // PA0
#define ESTOP_PIN           2    // PE4 = INT4 (EICRB register)
#define HEARTBEAT_LED       13   // PB7
#define FAULT_LED           12   // PB6
#define BATTERY_VOLTAGE_PIN A0   // PF0
#define CURRENT_SENSE_L_PIN A1   // PF1
#define CURRENT_SENSE_R_PIN A2   // PF2

// ── PWM ───────────────────────────────────────────────────────────────────────
#define MOTOR_PWM_TOP       99    // 16MHz/(8*(1+99)) = 20kHz, Timer3+4

// ── TIMING ────────────────────────────────────────────────────────────────────
#define LOOP_PERIOD_US          10000UL   // 10ms = 100Hz
#define CMD_VEL_TIMEOUT_MS      500UL
#define HEARTBEAT_TIMEOUT_MS    500UL
#define IMU_FAIL_THRESHOLD      10
#define OVERCURRENT_SAMPLES     5         // 5 × 100ms = 500ms
#define ENCODER_FAULT_MS        1000UL
#define TX_DECIMATION           3         // 100Hz/3 ≈ 33Hz publish
#define SERIAL_RX_WINDOW_US     1200UL    // v4.2r2 D4: full 12-byte vel pkt (1.04ms)

// ── KINEMATICS ────────────────────────────────────────────────────────────────
#define WHEEL_RADIUS_M      0.0381f       // TODO_CALIBRATE
#define WHEEL_SEP_M         0.3556f       // TODO_CALIBRATE
#define TICKS_PER_REV       825
#define METERS_PER_TICK     0.00029013f

// ── BATTERY ───────────────────────────────────────────────────────────────────
#define BATTERY_CRITICAL_V  10.5f
#define BATTERY_WARNING_V   11.1f
#define BATTERY_ADC_SCALE   0.017418f     // 5V/1023 / (3.9/13.9)

// ── CURRENT (v4.2 B8: per-motor 7.0A) ─────────────────────────────────────────
#define CURRENT_FAULT_AMPS  7.0f          // single stall (8A) triggers first
#define ACS712_ZERO_V       2.5f
#define ACS712_MV_PER_A     0.066f

// ── MOTOR ─────────────────────────────────────────────────────────────────────
#define MOTOR_LEFT          0
#define MOTOR_RIGHT         1
#define PWM_DEADZONE        25
#define MAX_SPEED_MPS       0.45f         // teleop clamp; Nav2 auto = 0.35

// ── WHEEL VELOCITY PID (P0 — closes the open-loop gap before Nav2 reliance) ──
// Closes loop on measured wheel speed (m/s) computed from encoder deltas at
// the 100 Hz loop. Output is PWM in [-255, 255] (feed-forward + feedback).
#define WHEEL_PID_ENABLED   1             // 1 = closed-loop, 0 = open-loop PWM
#define PID_PERIOD_S        0.01f         // must match LOOP_PERIOD_US
#define PID_FEEDFORWARD     1.0f          // full FF: v/MAX_SPEED_MPS*255
#define PID_KP              14.0f         // proportional gain (PWM per m/s err)
#define PID_KI              40.0f         // integral gain (windup-limited)
#define PID_KD              0.08f         // derivative on measurement (damping)
#define PID_INTEGRAL_LIMIT  90.0f         // anti-windup cap
#define PID_OUTPUT_LIMIT    255.0f        // PWM saturation
#define PID_SPEED_LPF_ALPHA 0.35f         // measured-speed low-pass (0..1)

// ── PROTOCOL ──────────────────────────────────────────────────────────────────
#define SERIAL_BAUD         115200
#define HDR_OUT             0xAA
#define HDR_IN              0xBB
#define PKT_ENCODER         0x01
#define PKT_IMU             0x02
#define PKT_BATTERY         0x03
#define PKT_FAULT           0x04
#define PKT_HEARTBEAT       0x05
#define PKT_CLEAR_FAULTS    0x07    // v4.2 B7

// ── FAULT BITS ────────────────────────────────────────────────────────────────
#define FAULT_BIT_ESTOP       (1 << 0)
#define FAULT_BIT_OVERCURRENT (1 << 1)
#define FAULT_BIT_WATCHDOG    (1 << 2)
#define FAULT_BIT_IMU         (1 << 3)
#define FAULT_BIT_ENCODER     (1 << 4)
#define FAULT_BIT_BATTERY     (1 << 5)
#define FAULT_BIT_HEARTBEAT   (1 << 6)

#define SET_FAULT(b)    (fault_flags |=  (b))
#define CLEAR_FAULT(b)  (fault_flags &= ~(b))
#define IS_FAULT(b)     (fault_flags &   (b))
#define ANY_MOTOR_FAULT() \
    (fault_flags & (FAULT_BIT_ESTOP|FAULT_BIT_OVERCURRENT| \
                    FAULT_BIT_ENCODER|FAULT_BIT_BATTERY|FAULT_BIT_HEARTBEAT))

// E-stop button state (D2 = PE4). Active-low: LATCHED when pressed.
#define ESTOP_LATCHED()     (!(PINE & (1 << PE4)))

// ── TX QUEUE ──────────────────────────────────────────────────────────────────
#define TX_QUEUE_SLOTS    4
#define TX_MAX_PKT_SIZE   30

// ── FIXED POINT (Q16.16) ──────────────────────────────────────────────────────
typedef int32_t fixed16_t;
#define FLOAT_TO_FIXED(f) ((fixed16_t)((f)*65536.0f))
#define FIXED_TO_FLOAT(x) ((float)(x)/65536.0f)
#define FIXED_MUL(a,b)    ((fixed16_t)(((int64_t)(a)*(b))>>16))
// Well-defined int32 -> Q16.16 (safe on negative values too).
#define INT_TO_FIXED(v)   ((fixed16_t)(((int64_t)(v))<<16))

// ── IMU ───────────────────────────────────────────────────────────────────────
#define IMU_I2C_ADDR    0x68
#define IMU_DLPF_CFG    0x02          // 42 Hz low-pass (P1: DLPF now active)
#define IMU_BIAS_SAMPLES 100         // stationary samples for gyro zero-offset
