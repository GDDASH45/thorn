/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef THORN_BOOT_H
#define THORN_BOOT_H

#include <stdint.h>

#define THORN_BOOT_MAGIC 0x5448524Eu

/*
 * TBP flags are capabilities: a bit is set only when the corresponding
 * information is valid and available to the kernel.
 */
#define THORN_FLAG_MEMORY_MAP  (1u << 0)
#define THORN_FLAG_BOOT_DRIVE  (1u << 1)
#define THORN_FLAG_FRAMEBUFFER (1u << 2)
#define THORN_FLAG_KERNEL      (1u << 3)
#define THORN_FLAG_COMMAND_LINE (1u << 4)

/*
 * These are the expected combined flag values once the memory map and boot
 * drive fields are populated: text = 0x3, graphics = 0x7.
 */
#define THORN_MODE_TEXT     0x00000003u
#define THORN_MODE_GRAPHICS 0x00000007u

#define THORN_FRAMEBUFFER_NONE 0u

struct thorn_boot_info
{
    uint32_t boot_drive;

    uint32_t memory_map_address;
    uint32_t memory_map_entries;

    uint32_t kernel_address;
    uint32_t kernel_size;

    uint32_t framebuffer_address;
    uint32_t framebuffer_width;
    uint32_t framebuffer_height;
    uint32_t framebuffer_pitch;
    uint32_t framebuffer_bpp;

    /* Optional NUL-terminated kernel command line. */
    uint32_t command_line_address;
    uint32_t command_line_size;
};

/* Transfer control to the kernel using the Thorn Boot Protocol. */
__attribute__((noreturn))
void thorn_enter_kernel(
    uint32_t entry,
    struct thorn_boot_info *info,
    uint32_t flags
);

#endif
