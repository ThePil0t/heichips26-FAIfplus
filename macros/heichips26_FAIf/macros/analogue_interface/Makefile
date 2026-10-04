# SPDX-FileCopyrightText: 2026 The HeiChips Contributors
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# Variables
TOP = analogue_interface

.DEFAULT_GOAL := help

# The sak-* verification scripts (vendored from IIC-OSIC-TOOLS, see scripts/) expect PDKPATH and STD_CELL_LIBRARY
export PDKPATH ?= $(PDK_ROOT)/$(PDK)
export STD_CELL_LIBRARY ?= sg13cmos5l_stdcell

# Cell name for verification targets (default: top-level cell)
# Override with: make <target> CELL=<cellname>
CELL ?= $(TOP)

# KLayout DRC level: precheck, macro, or regular (sak-drc.sh -l, only used by klayout-drc; default: macro)
# Override with: make <target> DRC_LEVEL=<precheck|macro|regular>
DRC_LEVEL ?= macro

# Folder structure
LAY_DIR         := layout
SCRIPTS_DIR     := scripts
GDS_DIR         := final/gds
LEF_DIR         := final/lef
LIB_DIR         := final/lib
VH_DIR          := final/vh
RENDER_DIR      := final/render
DRC_RPT_DIR     := verification/drc


# Help Target
help: ## Show this help message
	@echo 'Usage: make <target> [CELL=<cellname>] [DRC_LEVEL=<precheck|macro|regular>]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z0-9_.-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'
.PHONY: help
# ================================================================================================


# Layout Target
layout: ## Place the analog blocks and dummies, write the layout GDS and the LEF, Verilog header and Liberty views
	rm -rf $(LEF_DIR) $(LIB_DIR) $(VH_DIR)
	python3 $(SCRIPTS_DIR)/build_analogue_interface.py
.PHONY: layout
# ================================================================================================


# Copy Target
copy-gds: ## Copy the TOP cell GDS from layout/ to final/gds/
	rm -rf $(GDS_DIR)
	mkdir -p $(GDS_DIR)
	cp $(LAY_DIR)/$(TOP).gds $(GDS_DIR)/$(TOP).gds
.PHONY: copy-gds
# ================================================================================================


# Render Target
render-gds: ## Render an image from the final GDS using lay2img.py
	rm -rf $(RENDER_DIR)/
	mkdir -p $(RENDER_DIR)/
	python3 $(SCRIPTS_DIR)/lay2img.py $(LAY_DIR)/$(TOP).gds $(RENDER_DIR)/$(TOP).png --width 2048 --oversampling 4
.PHONY: render-gds
# ================================================================================================


# DRC Targets
# The sak-* scripts are vendored from IIC-OSIC-TOOLS (see scripts/.sak-scripts-version)
klayout-drc: ## Run KLayout DRC of the CELL cell (usage: make klayout-drc [CELL=<cellname>] [DRC_LEVEL=<precheck|macro|regular>])
	mkdir -p $(DRC_RPT_DIR)
	sh $(SCRIPTS_DIR)/sak-drc.sh -d -k -l $(DRC_LEVEL) -w $(DRC_RPT_DIR) $(LAY_DIR)/$(CELL).gds
.PHONY: klayout-drc
# ================================================================================================


# Build Target
build-top: ## Build TOP cell (layout GDS, LEF, LIB, Verilog header, copy GDS, and render image)
	$(MAKE) layout
	$(MAKE) copy-gds
	$(MAKE) render-gds
.PHONY: build-top

all: ## Build the macro
	$(MAKE) build-top
.PHONY: all
# ================================================================================================


# Clean Targets
clean: ## Delete all generated files and folders (final views, DRC reports)
	rm -rf final
	rm -rf $(DRC_RPT_DIR)
.PHONY: clean
# ================================================================================================
