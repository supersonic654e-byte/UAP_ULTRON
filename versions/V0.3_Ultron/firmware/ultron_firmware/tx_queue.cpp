#include <Arduino.h>
#include <string.h>
#include "tx_queue.h"
#include "config.h"

struct Slot { uint8_t buf[TX_MAX_PKT_SIZE]; uint8_t len; };
static Slot q[TX_QUEUE_SLOTS];
static uint8_t head=0, count=0;

void init_tx_queue(){ head=0; count=0; }

bool tx_enqueue(const uint8_t* data, uint8_t len){
    if(len==0 || len>TX_MAX_PKT_SIZE) return false;
    if(count>=TX_QUEUE_SLOTS) return false;          // queue full: drop new
    uint8_t idx=(uint8_t)((head+count)%TX_QUEUE_SLOTS);
    memcpy(q[idx].buf, data, len);
    q[idx].len=len; count++;
    return true;
}

void tx_drain(){
    while(count>0 && Serial.availableForWrite()>=q[head].len){
        Serial.write(q[head].buf, q[head].len);
        head=(uint8_t)((head+1)%TX_QUEUE_SLOTS); count--;
    }
}
