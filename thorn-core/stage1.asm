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

    ; Save BIOS boot drive
    mov [boot_drive], dl

    ; Initialize video mode
    mov ax, 0x0003
    int 0x10

    ; Print startup message
    mov si, msg
    call print_string

.halt:
    cli
    hlt
    jmp .halt

print_string:
    lodsb
    test al, al
    jz .done

    mov ah, 0x0E
    mov bh, 0x00
    int 0x10

    jmp print_string

.done:
    ret

boot_drive db 0

msg db 'Thorn Bootloader - Stage 1', 13, 10, 0

times 510 - ($ - $$) db 0
dw 0xAA55
