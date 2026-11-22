/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef THORN_TERMINAL_H
#define THORN_TERMINAL_H

#include <stdint.h>

#define TERMINAL_WIDTH  80u
#define TERMINAL_HEIGHT 25u
#define TERMINAL_COLOR  0x0Fu

static uint16_t *const terminal_buffer = (uint16_t *)0xB8000;
static uint32_t terminal_row = 0;
static uint32_t terminal_column = 0;

static inline uint16_t terminal_entry(char c, uint8_t color)
{
    return (uint16_t)(uint8_t)c | ((uint16_t)color << 8);
}

static inline void terminal_outb(uint16_t port, uint8_t value)
{
    __asm__ volatile (
        "outb %0, %w1"
        :
        : "a"(value), "Nd"(port)
    );
}

static inline void terminal_set_cursor(uint16_t x, uint16_t y)
{
    uint16_t position = (uint16_t)(y * TERMINAL_WIDTH + x);

    terminal_outb(0x3D4, 0x0F);
    terminal_outb(0x3D5, (uint8_t)(position & 0xFF));
    terminal_outb(0x3D4, 0x0E);
    terminal_outb(0x3D5, (uint8_t)(position >> 8));
}

static inline void terminal_scroll(void)
{
    for (uint32_t y = 1; y < TERMINAL_HEIGHT; y++)
    {
        for (uint32_t x = 0; x < TERMINAL_WIDTH; x++)
            terminal_buffer[(y - 1) * TERMINAL_WIDTH + x] =
                terminal_buffer[y * TERMINAL_WIDTH + x];
    }

    for (uint32_t x = 0; x < TERMINAL_WIDTH; x++)
        terminal_buffer[(TERMINAL_HEIGHT - 1) * TERMINAL_WIDTH + x] =
            terminal_entry(' ', TERMINAL_COLOR);

    terminal_row = TERMINAL_HEIGHT - 1;
}

static inline void terminal_clear(void)
{
    for (uint32_t i = 0; i < TERMINAL_WIDTH * TERMINAL_HEIGHT; i++)
        terminal_buffer[i] = terminal_entry(' ', TERMINAL_COLOR);

    terminal_row = 0;
    terminal_column = 0;
    terminal_set_cursor(0, 0);
}

static inline void terminal_putchar(char c)
{
    if (c == '\n')
    {
        terminal_column = 0;
        terminal_row++;
    }
    else if (c == '\r')
    {
        terminal_column = 0;
    }
    else if (c == '\b')
    {
        if (terminal_column > 0)
        {
            terminal_column--;
            terminal_buffer[terminal_row * TERMINAL_WIDTH + terminal_column] =
                terminal_entry(' ', TERMINAL_COLOR);
        }
    }
    else if (c == '\t')
    {
        uint32_t next = (terminal_column + 8u) & ~7u;
        do
        {
            terminal_putchar(' ');
        } while (terminal_column != 0 && terminal_column < next);
    }
    else
    {
        if (terminal_row >= TERMINAL_HEIGHT)
            terminal_scroll();

        terminal_buffer[terminal_row * TERMINAL_WIDTH + terminal_column] =
            terminal_entry(c, TERMINAL_COLOR);

        terminal_column++;
        if (terminal_column >= TERMINAL_WIDTH)
        {
            terminal_column = 0;
            terminal_row++;
        }
    }

    if (terminal_row >= TERMINAL_HEIGHT)
        terminal_scroll();

    terminal_set_cursor((uint16_t)terminal_column, (uint16_t)terminal_row);
}

static inline void terminal_write(const char *str)
{
    while (*str)
        terminal_putchar(*str++);
}

#endif
