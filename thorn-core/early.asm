; SPDX-License-Identifier: GPL-2.0-or-later
BITS 32

section .text.entry
global early_entry
extern thorn_main

early_entry:
    cli

    ; Stage 1 has already entered 32-bit protected mode.
    mov esp, stack_top
    cld

    call thorn_main

.halt:
    cli
    hlt
    jmp .halt

section .bss
align 16
stack_bottom:
    resb 16384
stack_top:

section .note.GNU-stack noalloc noexec nowrite progbits
