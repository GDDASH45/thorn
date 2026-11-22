#include "boot.h"
#include "video.h"
#include "terminal.h"

static struct thorn_boot_info boot_info;

static uint32_t boot_flags;

void thorn_main(void)
{
    boot_flags = 0;

    terminal_clear();
    terminal_write("THORN\n");
    terminal_write("Initializing bootloader...\n");

    /* Initialize memory map. */
    /* Set THORN_FLAG_MEMORY_MAP after successful initialization. */

    /* Retrieve saved BIOS boot drive. */
    /* Set THORN_FLAG_BOOT_DRIVE after successful initialization. */

    /* Try graphical mode first. */
    if (video_init_graphics(1024, 768) == 0)
    {
        boot_flags |= THORN_FLAG_FRAMEBUFFER;
        terminal_write("Graphics mode initialized.\n");
    }
    else
    {
        video_init_text();
        terminal_write("Using text mode.\n");
    }

    /* Kernel loading and TBP handoff will follow. */

    for (;;)
        __asm__ volatile ("cli; hlt");
}
