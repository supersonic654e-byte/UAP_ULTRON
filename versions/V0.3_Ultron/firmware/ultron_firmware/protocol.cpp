#include <Arduino.h>
#include <string.h>
#include "protocol.h"
#include "config.h"

// CRC-8-CCITT poly 0x07 init 0x00, over TYPE+LEN+PAYLOAD.
// Must stay byte-for-byte identical to serial_node.py `crc8()`.
uint8_t crc8(const uint8_t* data, uint8_t len){
    uint8_t crc=0;
    for(uint8_t i=0;i<len;i++){
        crc^=data[i];
        for(uint8_t b=0;b<8;b++)
            crc=(crc&0x80)?(uint8_t)((crc<<1)^0x07):(uint8_t)(crc<<1);
    }
    return crc;
}

float ntoh_float(const uint8_t* p){
    union { uint32_t u; float f; } x;
    x.u=((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];
    return x.f;
}

// finalize: HDR, TYPE, LEN, payload[0..len-1], CRC over TYPE+LEN+payload
static uint8_t pkt_finish(uint8_t* out, uint8_t type, uint8_t len){
    out[0]=HDR_OUT; out[1]=type; out[2]=len;
    out[3+len]=crc8(&out[1], (uint8_t)(len+2));
    return (uint8_t)(len+4);
}

uint8_t build_encoder_packet(uint8_t* out, int32_t l, int32_t r, uint32_t ts){
    out[3]=(uint8_t)(l>>24); out[4]=(uint8_t)(l>>16); out[5]=(uint8_t)(l>>8); out[6]=(uint8_t)l;
    out[7]=(uint8_t)(r>>24); out[8]=(uint8_t)(r>>16); out[9]=(uint8_t)(r>>8); out[10]=(uint8_t)r;
    out[11]=(uint8_t)(ts>>24);out[12]=(uint8_t)(ts>>16);out[13]=(uint8_t)(ts>>8);out[14]=(uint8_t)ts;
    return pkt_finish(out, PKT_ENCODER, 12);
}

uint8_t build_imu_packet(uint8_t* out, const ImuData* imu){
    const float v[6]={imu->ax,imu->ay,imu->az,imu->gx,imu->gy,imu->gz};
    for(uint8_t i=0;i<6;i++){
        union { uint32_t u; float f; } x; x.f=v[i];
        out[3+i*4]=(uint8_t)(x.u>>24); out[4+i*4]=(uint8_t)(x.u>>16);
        out[5+i*4]=(uint8_t)(x.u>>8);  out[6+i*4]=(uint8_t)x.u;
    }
    return pkt_finish(out, PKT_IMU, 24);
}

uint8_t build_battery_packet(uint8_t* out, float v){
    union { uint32_t u; float f; } x; x.f=v;
    out[3]=(uint8_t)(x.u>>24); out[4]=(uint8_t)(x.u>>16);
    out[5]=(uint8_t)(x.u>>8);  out[6]=(uint8_t)x.u;
    return pkt_finish(out, PKT_BATTERY, 4);
}

uint8_t build_fault_packet(uint8_t* out, uint8_t flags){
    out[3]=flags;
    return pkt_finish(out, PKT_FAULT, 1);
}
