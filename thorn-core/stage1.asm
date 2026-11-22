BITS 16
ORG 0x7C00

start:
    cli

    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    sti
    cld

    mov [boot_drive], dl

    ; Load Stage 2 from LBA sector 1
    mov si, disk_packet
    mov dl, [boot_drive]
    mov ah, 0x42
    int 0x13
    jc disk_error

    ; Enable A20 through the fast A20 gate
    in al, 0x92
    or al, 2
    and al, 0xFE
    out 0x92, al

    ; Load the GDT
    cli
    lgdt [gdt_descriptor]

    ; Enter protected mode
    mov eax, cr0
    or eax, 1
    mov cr0, eax

    jmp dword 0x08:protected_mode

disk_error:
    mov si, error_message

.print:
    lodsb
    test al, al
    jz .halt

    mov ah, 0x0E
    int 0x10
    jmp .print

.halt:
    cli
    hlt
    jmp .halt

boot_drive db 0

disk_packet:
    db 0x10
    db 0
    dw 32
    dw 0x8000
    dw 0
    dq 1

error_message db 'Thorn: Stage 2 loading failed!', 0

align 8

gdt_start:
    dq 0x0000000000000000
    dq 0x00CF9A000000FFFF
    dq 0x00CF92000000FFFF
gdt_end:

gdt_descriptor:
    dw gdt_end - gdt_start - 1
    dd gdt_start

BITS 32

protected_mode:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax

    jmp 0x08:0x8000

BITS 16

times 510 - ($ - $$) db 0
dw 0xAA55
