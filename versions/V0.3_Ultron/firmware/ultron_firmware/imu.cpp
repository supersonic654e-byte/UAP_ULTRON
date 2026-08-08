#include <Arduino.h>
#include <Wire.h>
#include "imu.h"
#include "config.h"

#define MPU_WHOAMI   0x75
#define MPU_PWR      0x6B
#define MPU_CONFIG   0x1A
#define MPU_ACCEL_XH 0x3B
#define MPU_GYRO_XH  0x43
#define ACCEL_SCALE  16384.0f      // +-2g full scale (LSB/g)
#define GYRO_SCALE   131.0f        // +-250 deg/s full scale (LSB/(deg/s))

static ImuOffsets g_bias = {0.0f, 0.0f, 0.0f};

static bool reg_write(uint8_t reg, uint8_t val) {
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(reg); Wire.write(val);
    return (Wire.endTransmission() == 0);
}

static bool read_gyro_raw(int16_t* x, int16_t* y, int16_t* z) {
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(MPU_GYRO_XH);
    if(Wire.endTransmission()!=0) return false;
    Wire.requestFrom((uint8_t)IMU_I2C_ADDR, (uint8_t)6);
    if(Wire.available()<6) return false;
    uint8_t b[6];
    for(uint8_t i=0;i<6;i++) b[i]=Wire.read();
    *x=(int16_t)(((uint16_t)b[0]<<8)|b[1]);
    *y=(int16_t)(((uint16_t)b[2]<<8)|b[3]);
    *z=(int16_t)(((uint16_t)b[4]<<8)|b[5]);
    return true;
}

void init_imu(){
    // Wake from sleep.
    reg_write(MPU_PWR, 0x00);
    delay(5);
    // DLPF 42 Hz (config register bits 2:0 = 0x02). Attenuates high-freq
    // vibration noise before the gyro bias capture below.
    reg_write(MPU_CONFIG, IMU_DLPF_CFG);

    // P1: capture stationary gyro zero-offset (rad/s) so IMU_DATA is
    // unbiased. Must be still on the bench / floor at boot.
    int16_t gx=0, gy=0, gz=0;
    long sx=0, sy=0, sz=0;
    int n=0;
    for(int i=0;i<IMU_BIAS_SAMPLES;i++){
        if(read_gyro_raw(&gx,&gy,&gz)){ sx+=gx; sy+=gy; sz+=gz; n++; }
        delay(2);
    }
    if(n>0){
        float s=1.0f/(GYRO_SCALE*n)*0.0174533f;   // deg/s->rad/s per sample
        g_bias.gx=(float)sx*s;
        g_bias.gy=(float)sy*s;
        g_bias.gz=(float)sz*s;
    }
}

bool read_imu(ImuData* out){
    if(!out) return false;
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(MPU_ACCEL_XH);
    if(Wire.endTransmission()!=0) return false; // NACK = IMU absent/fault
    Wire.requestFrom((uint8_t)IMU_I2C_ADDR, (uint8_t)14);
    if(Wire.available()<14) return false;
    uint8_t b[14]; for(uint8_t i=0;i<14;i++) b[i]=Wire.read();
    int16_t ax=((int16_t)((uint16_t)b[0]<<8)|b[1]);
    int16_t ay=((int16_t)((uint16_t)b[2]<<8)|b[3]);
    int16_t az=((int16_t)((uint16_t)b[4]<<8)|b[5]);
    int16_t gx=((int16_t)((uint16_t)b[8]<<8)|b[9]);
    int16_t gy=((int16_t)((uint16_t)b[10]<<8)|b[11]);
    int16_t gz=((int16_t)((uint16_t)b[12]<<8)|b[13]);
    out->ax=ax/ACCEL_SCALE;   out->ay=ay/ACCEL_SCALE;   out->az=az/ACCEL_SCALE;
    // deg/s -> rad/s, then subtract stationary bias (P1).
    out->gx=gx/GYRO_SCALE*0.0174533f - g_bias.gx;
    out->gy=gy/GYRO_SCALE*0.0174533f - g_bias.gy;
    out->gz=gz/GYRO_SCALE*0.0174533f - g_bias.gz;
    return true;
}
