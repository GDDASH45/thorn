BITS 32

section .text
global thorn_enter_kernel

thorn_enter_kernel:
    cli
    cld

    ; Get function arguments (cdecl)
    mov edx, [esp + 4]      ; Kernel entry
    mov ecx, [esp + 8]      ; Boot info pointer
    mov ebx, [esp + 12]     ; Boot flags

    ; Set TBP magic
    mov eax, 0x5448524E

    ; Transfer control to kernel
    jmp edx
