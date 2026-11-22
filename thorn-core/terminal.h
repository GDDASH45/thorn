#ifndef THORN_TERMINAL_H
#define THORN_TERMINAL_H

#include <stdint.h>

#define TERMINAL_WIDTH  80
#define TERMINAL_HEIGHT 25
#define TERMINAL_COLOR  0x0F

static uint16_t *const terminal_buffer = (uint16_t *)0xB8000;

static uint32_t terminal_row = 0;
static uint32_t terminal_column = 0;

static inline uint16_t terminal_entry(char c, uint8_t color)
{
    return (uint16_t)c | ((uint16_t)color << 8);
}

static inline void terminal_set_cursor(uint16_t x, uint16_t y)
{
    uint16_t position = y * TERMINAL_WIDTH + x;

    __asm__ volatile (
        "outb %0, $0x3D4"
        :
        : "a"((uint8_t)0x0F)
    );

    __asm__ volatile (
        "outb %0, $0x3D5"
        :
        : "a"((uint8_t)(position & 0xFF))
    );

    __asm__ volatile (
        "outb %0, $0x3D4"
        :
        : "a"((uint8_t)0x0E)
    );

    __asm__ volatile (
        "outb %0, $0x3D5"
        :
        : "a"((uint8_t)(position >> 8))
    );
}

static inline void terminal_clear(void)
{
    for (uint32_t y = 0; y < TERMINAL_HEIGHT; y++)
    {
        for (uint32_t x = 0; x < TERMINAL_WIDTH; x++)
        {
            terminal_buffer[y * TERMINAL_WIDTH + x] =
                terminal_entry(' ', TERMINAL_COLOR);
        }
    }

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
        return;
    }

    if (terminal_row >= TERMINAL_HEIGHT)
        return;

    terminal_buffer[terminal_row * TERMINAL_WIDTH + terminal_column] =
        terminal_entry(c, TERMINAL_COLOR);

    terminal_column++;

    if (terminal_column >= TERMINAL_WIDTH)
    {
        terminal_column = 0;
        terminal_row++;
    }
}

static inline void terminal_write(const char *str)
{
    while (*str)
        terminal_putchar(*str++);
}

#endif
