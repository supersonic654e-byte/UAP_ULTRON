#pragma once
#include <stdint.h>
#include "imu.h"
uint8_t crc8(const uint8_t* data, uint8_t len);
uint8_t build_encoder_packet(uint8_t* out, int32_t l, int32_t r, uint32_t ts);
uint8_t build_imu_packet(uint8_t* out, const ImuData* imu);
uint8_t build_battery_packet(uint8_t* out, float v);
uint8_t build_fault_packet(uint8_t* out, uint8_t flags);
uint8_t build_current_packet(uint8_t* out, float left, float right);
float ntoh_float(const uint8_t* p);
