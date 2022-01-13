libraries = [
    (
        "mylib",
        {
            "sources": ["lib/mylib/mylib.c"],
            "include_dirs": ["include"],
        },
    )
]


def build(setup_kwargs):
    setup_kwargs.update({"libraries": libraries})
