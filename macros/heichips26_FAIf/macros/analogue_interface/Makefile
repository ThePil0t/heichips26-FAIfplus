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
LVS_RPT_DIR     := verification/lvs
XSCHEM_SCH_DIR  := schematic/xschem
NET_SCH_DIR     := netlist/schematic
NET_LAY_DIR     := netlist/layout


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


# LVS Targets
# The reference schematic is generated from the analog part of the top schematic (needs PDK_ROOT/PDK)
reference-schematic: ## Regenerate schematic/xschem/analogue_interface.sch/.sym from the top schematic
	python3 $(SCRIPTS_DIR)/gen_reference_schematic.py
.PHONY: reference-schematic

klayout-lvs-netlist: ## Export the CDL netlist of the reference schematic for KLayout LVS
	mkdir -p $(NET_SCH_DIR)
	xschem -s -r -x -q --rcfile $(XSCHEM_SCH_DIR)/xschemrc --command ' \
		set spiceprefix 1; \
		set lvs_netlist 1; \
		set top_is_subckt 1; \
		set lvs_ignore 1; \
		set netlist_dir $(NET_SCH_DIR); \
		xschem set netlist_name $(TOP)_klayout.cdl; \
		xschem netlist \
	' $(XSCHEM_SCH_DIR)/$(TOP).sch
.PHONY: klayout-lvs-netlist

klayout-lvs: ## Run KLayout LVS of the macro against the reference schematic
	$(MAKE) klayout-lvs-netlist
	mkdir -p $(LVS_RPT_DIR) $(NET_LAY_DIR)
	sh $(SCRIPTS_DIR)/sak-lvs.sh -d -k -w $(LVS_RPT_DIR) -s $(NET_SCH_DIR)/$(TOP)_klayout.cdl -l $(LAY_DIR)/$(TOP).gds -c $(TOP)
	mv $(LVS_RPT_DIR)/$(TOP).klayout.lvs/$(TOP)_extracted.cir $(NET_LAY_DIR)/$(TOP)_klayout.cir
.PHONY: klayout-lvs
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
	rm -rf $(DRC_RPT_DIR) $(LVS_RPT_DIR)
.PHONY: clean
# ================================================================================================
