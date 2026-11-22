#include "terminal.h"

void thorn_main(void)
{
    terminal_clear();

    terminal_write("Thorn Bootloader\n");
    terminal_write("Stage 2 initialized.");

    for (;;)
        __asm__ volatile ("cli; hlt");
}