// 直接測我們建出的 ICU 能不能開 Big5 轉換器（隔離問題：與取名字表無關）。
#include <unicode/ucnv.h>
#include <unicode/uclean.h>
#include <stdio.h>

static void probe(const char* name) {
    UErrorCode e = U_ZERO_ERROR;
    UConverter* c = ucnv_open(name, &e);
    printf("%-10s : %s (err=%d %s)\n", name,
           U_SUCCESS(e) ? "OK" : "FAIL", e, u_errorName(e));
    if (c) ucnv_close(c);
}

int main() {
    UErrorCode e = U_ZERO_ERROR;
    u_init(&e);
    printf("u_init err=%d %s\n", e, u_errorName(e));
    probe("UTF-8");
    probe("Big5");
    probe("Shift_JIS");
    probe("windows-950");
    printf("available converters: %d\n", ucnv_countAvailable());
    return 0;
}
