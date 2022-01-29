
#ifndef MYLIB
    #define MYLIB
    #if defined _WIN32 || defined __CYGWIN__
        #ifdef __GNUC__
            #define MYLIB_EXPORT __attribute__ ((dllexport))
        #else
            #define MYLIB_EXPORT __declspec(dllexport)
        #endif
    #else
        #define MYLIB_EXPORT __attribute__ ((visibility("default")))
    #endif
#endif

MYLIB_EXPORT char* mylib_say_hello();
