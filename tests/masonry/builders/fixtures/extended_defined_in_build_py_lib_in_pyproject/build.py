from distutils.core import Extension


extensions = [
    Extension(
        "extended.extended",
        sources=["src/extended/extended.cpp"],
        include_dirs=["include"],
        libraries=["mylib"],
        extra_compile_args=["-std=c++11"],
        swig_opts="-Iinclude",
        language="c++",
        optional=False,
    )
]


def build(setup_kwargs):
    setup_kwargs.update({"ext_modules": extensions})
