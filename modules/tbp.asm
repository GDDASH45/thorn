; SPDX-License-Identifier: GPL-2.0-or-later
BITS 32

%define MODULE_ABI_MAGIC       0x54484D31

%define MODULE_E_ABI           1
%define MODULE_E_CONTEXT       2
%define MODULE_E_ARGUMENT      3
%define MODULE_E_SERVICES      4
%define MODULE_E_LOAD          5
%define MODULE_E_HANDOFF       6

%define CTX_SIZE               0
%define CTX_ARGC               4
%define CTX_ARGV               8
%define CTX_SERVICES           12
%define CTX_BYTES              20

%define SERVICES_SIZE          0
%define SERVICES_LOAD_KERNEL   4
%define SERVICES_HANDOFF       8
%define SERVICES_BYTES         12

%define IMAGE_BYTES            12

; cdecl service signatures:
;   uint32_t load_kernel(const char *path, struct thorn_module_image *image);
;   void handoff(struct thorn_module_image *image,
;                uint32_t argc, const char *const *argv);
;
; Entry:
;   EAX = MODULE_ABI_MAGIC
;   EBX = thorn_module_exec_context *

module_entry:
    push esi
    push edi
    push ebp

    cmp eax, MODULE_ABI_MAGIC
    jne .bad_abi

    test ebx, ebx
    jz .bad_context

    mov edi, ebx
    cmp dword [edi + CTX_SIZE], CTX_BYTES
    jb .bad_context

    ; argv[0] is "tbp"; argv[1] is the kernel path.
    cmp dword [edi + CTX_ARGC], 2
    jb .bad_argument

    mov ebp, [edi + CTX_ARGV]
    test ebp, ebp
    jz .bad_argument

    mov eax, [ebp + 4]
    test eax, eax
    jz .bad_argument

    ; Validate the service table.
    mov esi, [edi + CTX_SERVICES]
    test esi, esi
    jz .bad_services

    cmp dword [esi + SERVICES_SIZE], SERVICES_BYTES
    jb .bad_services

    cmp dword [esi + SERVICES_LOAD_KERNEL], 0
    je .bad_services

    cmp dword [esi + SERVICES_HANDOFF], 0
    je .bad_services

    ; Reserve the 12-byte kernel image descriptor.
    sub esp, IMAGE_BYTES

    ; load_kernel(argv[1], &image)
    push esp
    push eax
    call dword [esi + SERVICES_LOAD_KERNEL]
    add esp, 8

    test eax, eax
    jnz .load_failed

    ; handoff(&image, argc - 2, argv + 2)
    ; The handoff service serializes these arguments into TBP.

    mov eax, [edi + CTX_ARGV]
    lea eax, [eax + 8]
    push eax

    mov eax, [edi + CTX_ARGC]
    sub eax, 2
    push eax

    lea eax, [esp + 8]
    push eax

    call dword [esi + SERVICES_HANDOFF]

    ; A successful handoff must never return.
    add esp, 12
    add esp, IMAGE_BYTES
    mov eax, MODULE_E_HANDOFF
    jmp .return

.load_failed:
    add esp, IMAGE_BYTES
    ; Preserve the loader's error code in EAX.
    jmp .return

.bad_abi:
    mov eax, MODULE_E_ABI
    jmp .return

.bad_context:
    mov eax, MODULE_E_CONTEXT
    jmp .return

.bad_argument:
    mov eax, MODULE_E_ARGUMENT
    jmp .return

.bad_services:
    mov eax, MODULE_E_SERVICES
    jmp .return

.return:
    pop ebp
    pop edi
    pop esi
    ret
