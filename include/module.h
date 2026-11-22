/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef THORN_MODULE_H
#define THORN_MODULE_H

#include <stdint.h>

#define THORN_MOD_MAGIC "THRNMOD"
#define THORN_MOD_VERSION 1u
#define THORN_MOD_HEADER_SIZE 32u

#define THORN_MOD_ARCH_I386 3u

/*
 * Thorn .mod files contain position-independent raw i386 machine code.
 * The loader chooses the payload's load address; entry_offset is relative
 * to the first byte of the payload.
 */
#define THORN_MOD_FLAG_POSITION_INDEPENDENT (1u << 0)
#define THORN_MOD_KNOWN_FLAGS THORN_MOD_FLAG_POSITION_INDEPENDENT

struct thorn_mod_header
{
    uint8_t magic[8];
    uint16_t version;
    uint16_t header_size;
    uint16_t architecture;
    uint16_t flags;
    uint32_t payload_size;
    uint32_t entry_offset;
    uint32_t payload_crc32;
    uint32_t reserved;
} __attribute__((packed));

_Static_assert(sizeof(struct thorn_mod_header) == THORN_MOD_HEADER_SIZE,
               "Thorn module header must be exactly 32 bytes");

#endif /* THORN_MODULE_H */
