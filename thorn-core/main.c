#include "boot.h"
#include "video.h"
#include "terminal.h"

static uint32_t boot_flags;

void thorn_main(void)
{
    boot_flags = 0;

    terminal_clear();
    terminal_write("THORN\n");
    terminal_write("Initializing bootloader...\n");

    /*
     * Memory-map discovery and boot-drive handoff are not implemented yet.
     * Do not advertise either capability in TBP flags until the data exists.
     */

    /* Thorn owns video mode selection; the kernel will inherit the result. */
    if (video_init_graphics(1024, 768) == 0)
    {
        boot_flags |= THORN_FLAG_FRAMEBUFFER;
        terminal_write("Graphics mode initialized.\n");
    }
    else
    {
        video_init_text();
        terminal_write("Graphics unavailable; using BIOS text mode.\n");
    }

    /*
     * Kernel loading and the final TBP handoff are the next boot stages.
     * The current image intentionally stops here.
     */
    (void)boot_flags;

    for (;;)
        __asm__ volatile ("cli; hlt");
}
