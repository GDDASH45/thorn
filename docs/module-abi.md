# Thorn module execution ABI

This document defines the version 1 execution ABI used by executable .mod
modules. The .mod file container is specified separately in
[module-format.md](module-format.md).

## Entry point

Modules execute in 32-bit protected mode and use the i386 cdecl calling
convention.

At the module entry address:

| Register | Value |
| --- | --- |
| EAX | THORN_MODULE_ABI_MAGIC (0x54484D31) |
| EBX | Pointer to struct thorn_module_exec_context |

The module returns a status code in EAX if it returns. A module that transfers
control to a kernel must not return after a successful handoff.

The context and service structures are declared in include/module_abi.h.
All pointers are 32-bit linear addresses valid in the current flat protected
mode address space. The module manager must validate the complete context,
argument vector, service table, and pointed-to strings before entering a
module.

## Execution context

The version 1 context contains:

- size: size of the context structure in bytes.
- argc: number of command-line arguments.
- argv: pointer to an array of argc NUL-terminated string pointers.
- services: pointer to the Thorn service table.
- reserved: must be zero.

The boot-script interpreter invokes a command module with argv[0] set to the
command name. For example:

~~~sh
tbp /boot/kernel.bin --verbose
~~~

produces an argument vector equivalent to:

- argv[0]: tbp
- argv[1]: /boot/kernel.bin
- argv[2]: --verbose

## Services

The version 1 service table contains two cdecl callbacks:

~~~c
uint32_t load_kernel(
    const char *path,
    struct thorn_module_image *image
);

void handoff(
    struct thorn_module_image *image,
    uint32_t argc,
    const char *const *argv
);
~~~

load_kernel loads and validates the requested kernel image. On success it
fills in the entry address, TBP boot-information pointer, and TBP flags in
the image descriptor, then returns THORN_MODULE_OK.

The handoff callback receives only the arguments after the kernel path.
It is responsible for constructing the TBP command-line field and invoking
the TBP register handoff. It must not return after a successful transfer.

The current Thorn boot path does not yet implement the module manager,
boot-script interpreter, filesystem access, or kernel-loading service. This
ABI defines their contract; it does not claim those runtime features already
work.

## Status codes

| Code | Name | Meaning |
| ---: | --- | --- |
| 0 | THORN_MODULE_OK | Success |
| 1 | THORN_MODULE_E_ABI | Entry ABI magic mismatch |
| 2 | THORN_MODULE_E_CONTEXT | Invalid execution context |
| 3 | THORN_MODULE_E_ARGUMENT | Missing or invalid command arguments |
| 4 | THORN_MODULE_E_SERVICES | Required Thorn service unavailable |
| 5 | THORN_MODULE_E_LOAD | Reserved for a module-side load failure |
| 6 | THORN_MODULE_E_HANDOFF | Handoff unexpectedly returned |

A nonzero value returned directly by load_kernel is propagated unchanged.
