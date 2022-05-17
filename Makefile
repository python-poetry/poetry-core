SHELL                           := $(shell which bash) -e
MAKEFILE_PATH                   := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT_DIR                        := $(patsubst %/,%,$(dir $(MAKEFILE_PATH)))

VENDOR_SRC                      := $(ROOT_DIR)/vendors
VENDOR_DIR                      := $(ROOT_DIR)/src/poetry/core/_vendor
VENDOR_TXT                      := $(VENDOR_DIR)/vendor.txt
POETRY_BIN                      ?= $(shell which poetry)

.PHONY: vendor/lock
vendor/lock: $(VENDOR_LOCK)
	# regenerate lock file
	@pushd $(VENDOR_SRC) && $(POETRY_BIN) lock --no-update

.PHONY: vendor/sync
vendor/sync:
	# regenerate vendor.txt file (exported from lockfile)
	@pushd $(VENDOR_SRC) && $(POETRY_BIN) export --without-hashes 2> /dev/null \
			| egrep -v "(importlib|zipp)" \
			| sort > $(VENDOR_TXT)

	# vendor packages
	@vendoring sync

	# strip out *.pyi stubs
	@find "$(VENDOR_DIR)" -type f -name "*.pyi" -exec rm {} \;

.PHONY: vendor/update
vendor/update: | vendor/lock vendor/sync
	@:
