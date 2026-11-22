/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef THORN_MODULE_ABI_H
#define THORN_MODULE_ABI_H

#include <stdint.h>

#define THORN_MODULE_ABI_MAGIC   0x54484D31u
#define THORN_MODULE_ABI_VERSION 1u

#define THORN_MODULE_OK          0u
#define THORN_MODULE_E_ABI       1u
#define THORN_MODULE_E_CONTEXT   2u
#define THORN_MODULE_E_ARGUMENT  3u
#define THORN_MODULE_E_SERVICES  4u
#define THORN_MODULE_E_LOAD      5u
#define THORN_MODULE_E_HANDOFF   6u

/*
 * Entry contract:
 *   EAX = THORN_MODULE_ABI_MAGIC
 *   EBX = pointer to thorn_module_exec_context
 *
 * Module entry points use 32-bit cdecl and return a status in EAX.
 */

struct thorn_module_image {
    uint32_t entry_address;
    uint32_t boot_info;
    uint32_t flags;
};

/*
 * load_kernel(path, image):
 *   Load and validate the kernel named by path. Fill image on success.
 *   Return THORN_MODULE_OK on success.
 *
 * handoff(image, argc, argv):
 *   Build the TBP boot information, including the optional command line,
 *   then transfer control to image->entry_address. This callback must not
 *   return after a successful handoff.
 *
 * Both callbacks are 32-bit cdecl function pointers.
 */
struct thorn_module_services {
    uint32_t size;
    uint32_t load_kernel;
    uint32_t handoff;
};

struct thorn_module_exec_context {
    uint32_t size;
    uint32_t argc;
    uint32_t argv;
    uint32_t services;
    uint32_t reserved;
};

_Static_assert(sizeof(struct thorn_module_image) == 12,
               "module image descriptor must be 12 bytes");
_Static_assert(sizeof(struct thorn_module_services) == 12,
               "module service table must be 12 bytes");
_Static_assert(sizeof(struct thorn_module_exec_context) == 20,
               "module execution context must be 20 bytes");

#endif
