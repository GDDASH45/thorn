BITS 32

section .text
global early_entry

early_entry:
    cli

    ; Set up the stack
    mov esp, stack_top

    ; Clear direction flag
    cld

    ; Continue into the C initialization
    call thorn_main

.halt:
    hlt
    jmp .halt

section .bss
align 16

stack_bottom:
    resb 16384
stack_top:
