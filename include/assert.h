/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef THORN_ASSERT_H
#define THORN_ASSERT_H

#ifdef NDEBUG

#define assert(expression) ((void)0)

#else

void thorn_assert_fail(
    const char *expression,
    const char *file,
    unsigned int line
);

#define assert(expression)                                      \
    do {                                                        \
        if (!(expression))                                      \
            thorn_assert_fail(#expression, __FILE__, __LINE__); \
    } while (0)

#endif

#endif /* THORN_ASSERT_H */
