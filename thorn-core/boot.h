#ifndef THORN_BOOT_H
#define THORN_BOOT_H

#include <stdint.h>

#define THORN_BOOT_MAGIC 0x5448524E

/* Boot flags */
#define THORN_FLAG_MEMORY_MAP  (1u << 0)
#define THORN_FLAG_FRAMEBUFFER (1u << 1)
#define THORN_FLAG_BOOT_DRIVE  (1u << 2)
#define THORN_FLAG_KERNEL      (1u << 3)

/* Thorn Boot Protocol information */
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
};

/* Transfer control to the kernel */
__attribute__((noreturn))
void thorn_enter_kernel(
    uint32_t entry,
    struct thorn_boot_info *info,
    uint32_t flags
);

#endif
