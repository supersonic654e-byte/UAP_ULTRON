#include "faults.h"

// Debug helper only. FAULT bits are authoritative in config.h.
const char* fault_name(uint8_t bit){
    switch(bit){
        case 0: return "ESTOP";
        case 1: return "OVERCURRENT";
        case 2: return "WATCHDOG";
        case 3: return "IMU";
        case 4: return "ENCODER";
        case 5: return "BATTERY";
        case 6: return "HEARTBEAT";
        case 7: return "RESERVED";
    }
    return "?";
}
