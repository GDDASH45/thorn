/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <assert.h>
#include "terminal.h"

static void err_write_uint(unsigned int value)
{
    char buffer[10];
    unsigned int i = 0;

    if (value == 0)
    {
        terminal_putchar('0');
        return;
    }

    while (value > 0)
    {
        buffer[i++] = (char)('0' + (value % 10));
        value /= 10;
    }

    while (i > 0)
        terminal_putchar(buffer[--i]);
}

void thorn_assert_fail(
    const char *expression,
    const char *file,
    unsigned int line
)
{
    terminal_write("\n\nTHORN ASSERTION FAILED\n");
    terminal_write("Expression: ");
    terminal_write(expression);
    terminal_write("\nFile: ");
    terminal_write(file);
    terminal_write("\nLine: ");
    err_write_uint(line);
    terminal_write("\n");

    __asm__ volatile ("cli");

    for (;;)
        __asm__ volatile ("hlt");
}
