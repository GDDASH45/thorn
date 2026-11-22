/* SPDX-License-Identifier: GPL-2.0-or-later */
OUTPUT_FORMAT(elf32-i386)
OUTPUT_ARCH(i386)
ENTRY(early_entry)

PHDRS
{
    text   PT_LOAD FLAGS(5);
    rodata PT_LOAD FLAGS(4);
    data   PT_LOAD FLAGS(6);
}

SECTIONS
{
    . = 0x8000;

    .text :
    {
        *(.text.entry)
        *(.text)
        *(.text.*)
    } :text

    .rodata :
    {
        *(.rodata)
        *(.rodata.*)
    } :rodata

    .data :
    {
        *(.data)
        *(.data.*)
    } :data

    .bss :
    {
        *(COMMON)
        *(.bss)
        *(.bss.*)
    } :data

    /DISCARD/ :
    {
        *(.comment)
        *(.note*)
        *(.eh_frame*)
    }
}
