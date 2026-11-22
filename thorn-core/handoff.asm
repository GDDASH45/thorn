BITS 32

section .text
global thorn_enter_kernel

; cdecl:
;   [esp + 4]  = kernel entry address
;   [esp + 8]  = struct thorn_boot_info pointer
;   [esp + 12] = TBP flags
;
; Kernel entry contract:
;   EAX = THORN_BOOT_MAGIC
;   EBX = flags
;   ECX = boot info pointer
thorn_enter_kernel:
    cli
    cld

    mov edx, [esp + 4]
    mov ecx, [esp + 8]
    mov ebx, [esp + 12]
    mov eax, 0x5448524E

    jmp edx

section .note.GNU-stack noalloc noexec nowrite progbits
