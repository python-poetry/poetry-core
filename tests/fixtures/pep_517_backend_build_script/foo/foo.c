#include <Python.h>


static PyObject *hello(PyObject *self) {
    return PyUnicode_FromString("Hello");
}


static PyMethodDef module_methods[] = {
    {
        "hello",
        (PyCFunction) hello,
        NULL,
        PyDoc_STR("Say hello.")
    },
    {NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "foo",
    NULL,
    -1,
    module_methods,
    NULL,
    NULL,
    NULL,
    NULL,
};
#endif

PyMODINIT_FUNC
#if PY_MAJOR_VERSION >= 3
PyInit_foo(void)
#else
init_foo(void)
#endif
{
    PyObject *module;

#if PY_MAJOR_VERSION >= 3
    module = PyModule_Create(&moduledef);
#else
    module = Py_InitModule3("foo", module_methods, NULL);
#endif

    if (module == NULL)
#if PY_MAJOR_VERSION >= 3
        return NULL;
#else
        return;
#endif

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
