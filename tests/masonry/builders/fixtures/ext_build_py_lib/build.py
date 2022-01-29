libraries = [
    (
        "mylib",
        {
            "sources": ["lib/mylib/src/mylib.c"],
            "include_dirs": [
                "include",
                "lib/mylib/include",
            ],
        },
    )
]


def build(setup_kwargs):
    setup_kwargs.update({"libraries": libraries})
