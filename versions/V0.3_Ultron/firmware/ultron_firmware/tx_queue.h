#pragma once
#include <stdint.h>
void init_tx_queue();
bool tx_enqueue(const uint8_t* data, uint8_t len);
void tx_drain();
