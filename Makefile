MAKEFILE_PATH                   := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT_DIR                        := $(patsubst %/,%,$(dir $(MAKEFILE_PATH)))

VENDOR_SRC                      := $(ROOT_DIR)/vendors
VENDOR_DIR                      := $(ROOT_DIR)/poetry/core/_vendor
POETRY_BIN                      ?= $(shell which poetry)


.PHONY: vendor/lock
vendor/lock:
    # regenerate lock file
	@pushd $(VENDOR_SRC) && $(POETRY_BIN) lock

	# regenerate vendor.txt file (exported from lockfile)
	@pushd $(VENDOR_SRC) && $(POETRY_BIN) export --without-hashes \
			| egrep -v "(importlib|zipp)" \
			| sort > $(VENDOR_DIR)/vendor.txt


.PHONY: vendor/sync
vendor/sync: | vendor/lock
	# vendor packages
	@vendoring sync

	# strip out *.pyi stubs
	@find "$(VENDOR_DIR)" -type f -name "*.pyi" -exec rm {} \;
