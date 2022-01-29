#include <Python.h>
#if defined _WIN32 || defined __CYGWIN__
extern "C" {
#endif
    #include <../lib/mylib/include/mylib.h>
#if defined _WIN32 || defined __CYGWIN__
}
#endif

static PyObject *hello(PyObject *self);
