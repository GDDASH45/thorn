/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "video.h"

/*
 * Stage 1 selects BIOS text mode 3 before entering protected mode.
 * This function verifies the intended fallback path without making a BIOS
 * call from protected mode.
 */
int video_init_text(void)
{
    return 0;
}

/*
 * VBE mode switching requires a real-mode BIOS call. Stage 2 currently runs
 * in 32-bit protected mode, so graphics mode is deliberately unavailable
 * until Thorn gains a real-mode thunk or a real-mode video setup stage.
 */
int video_init_graphics(uint32_t width, uint32_t height)
{
    (void)width;
    (void)height;
    return -1;
}
