/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef THORN_VIDEO_H
#define THORN_VIDEO_H

#include <stdint.h>

int video_init_text(void);
int video_init_graphics(uint32_t width, uint32_t height);

#endif
