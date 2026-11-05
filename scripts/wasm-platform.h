// Claude: Slang 2026.20 cpp prelude has no wasm platform branch; declare a POSIX-like
// platform (no OS calls are used by the kernel) and disable _Float16, which wasm32 lacks.
#pragma once
#define SLANG_PLATFORM
#define SLANG_WINRT 0
#define SLANG_XBOXONE 0
#define SLANG_WIN64 0
#define SLANG_X360 0
#define SLANG_WIN32 0
#define SLANG_ANDROID 0
#define SLANG_LINUX 1
#define SLANG_IOS 0
#define SLANG_OSX 0
#define SLANG_PS3 0
#define SLANG_PS4 0
#define SLANG_PSP2 0
#define SLANG_WIIU 0
#include <float.h>
#undef FLT16_MIN
