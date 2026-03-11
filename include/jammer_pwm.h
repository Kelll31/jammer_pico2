#ifndef JAMMER_PWM_H
#define JAMMER_PWM_H

#include <stdint.h>
#include <stdbool.h>

void jammer_pwm_init(void);
void jammer_pwm_set_freq(uint32_t freq);
void jammer_pwm_enable(bool enable);

#endif // JAMMER_PWM_H
