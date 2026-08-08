#pragma once
#include <stdint.h>
typedef struct { float ax, ay, az, gx, gy, gz; } ImuData;
// Stationary gyro zero-offsets (rad/s), captured at init (P1).
typedef struct { float gx, gy, gz; } ImuOffsets;
void init_imu();
bool read_imu(ImuData* out);
