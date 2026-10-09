# SPDX-FileCopyrightText: 2026 XXX
# SPDX-License-Identifier: Apache-2.0 WITH SHL-2.1

"""cocotb testbench for heichips26_FAIf (RTL and gate level).

The analog macro is replaced by the behavioral model in rtl/analogue_interface.sv
(compiled with SIM defined) in both modes. It has the real polarities of the macro:
the comparator gives adc_comp = 1 when V_dac > V_in, and the S&H tracks while
adc_hold (SH_EN) is 1. The ADC input voltage is the model's `vin`.
"""

import os
import logging
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles
from cocotb_tools.runner import get_runner

sim      = os.getenv("SIM", "icarus")
pdk_root = os.getenv("PDK_ROOT", Path("~/.ciel").expanduser())
pdk      = os.getenv("PDK", "ihp-sg13cmos5l")
scl      = os.getenv("SCL", "sg13cmos5l_stdcell")
# GL=1 selects the gate-level netlist; anything else (unset, "0", "") stays in RTL mode.
gl       = os.getenv("GL", "0").strip().lower() in ("1", "true", "yes", "on")

hdl_toplevel = "heichips26_FAIf"

CLK_FREQ_MHZ = 50
NBITS        = 8
VFS          = 3.3                 # full scale of the model's SAR DAC
LSB          = VFS / 2**NBITS

# uio_in bit positions
CLEAR, ENA, START, DAC_SEL, DAC_LOAD, LOAD_CONFIG = 0, 1, 2, 5, 6, 7
# uio_out bit positions
DONE, TICK = 3, 4

logger = logging.getLogger("heichips26_FAIf_tb")


class Tb:
    """Drives the pins at falling clock edges and keeps a shadow of uio_in."""

    def __init__(self, dut):
        self.dut = dut
        self.ana = dut.analogue_interface_instance
        self.uio = 0

    def set_uio(self, bit, value):
        if value:
            self.uio |= 1 << bit
        else:
            self.uio &= ~(1 << bit)
        self.dut.uio_in.value = self.uio

    def uio_out(self, bit):
        return (int(self.dut.uio_out.value) >> bit) & 1

    async def start_up(self):
        cocotb.start_soon(Clock(self.dut.clk, round(1000 / CLK_FREQ_MHZ, 4), "ns").start())
        self.dut.ena.value = 1
        self.dut.ui_in.value = 0
        self.dut.uio_in.value = 0
        self.dut.rst_n.value = 0
        await ClockCycles(self.dut.clk, 2)
        await FallingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await FallingEdge(self.dut.clk)

    async def pulse(self, bit, ui_in=None):
        """Set ui_in (optional) and pulse one uio_in bit for one clock cycle."""
        if ui_in is not None:
            self.dut.ui_in.value = ui_in
        self.set_uio(bit, 1)
        await FallingEdge(self.dut.clk)
        self.set_uio(bit, 0)

    async def convert(self, vin, vin_during=None):
        """One conversion of vin. vin_during is applied after start (S&H must hold)."""
        self.ana.vin.value = vin
        await ClockCycles(self.dut.clk, 2, rising=False)        # track
        assert int(self.ana.adc_hold.value) == 1, "S&H not tracking while idle"
        await self.pulse(START)
        if vin_during is not None:
            self.ana.vin.value = vin_during
        assert int(self.ana.adc_hold.value) == 0, "S&H not holding during the conversion"
        for _ in range(2 * NBITS + 4):
            if self.uio_out(TICK):
                break
            await FallingEdge(self.dut.clk)
        else:
            raise AssertionError(f"no tick for vin = {vin:.4f} V")
        assert self.uio_out(DONE) == 1, "done not 1 on tick"
        result = int(self.dut.uo_out.value)
        await FallingEdge(self.dut.clk)
        assert self.uio_out(TICK) == 0, "tick longer than one cycle"
        assert int(self.dut.uo_out.value) == result, "value not held after tick"
        return result


@cocotb.test()
async def test_reset(dut):
    """After reset: result 0, SAR idle (done 1, tick 0), S&H tracking, DAC and cfg 0."""
    tb = Tb(dut)
    await tb.start_up()
    assert int(dut.uo_out.value) == 0
    assert tb.uio_out(DONE) == 1 and tb.uio_out(TICK) == 0
    assert int(dut.uio_oe.value) == 0b00011000
    assert int(tb.ana.adc_hold.value) == 1
    assert int(tb.ana.dac_out.value) == 0
    assert int(tb.ana.sh_cap_en.value) == 0


@cocotb.test()
async def test_dac_byte_order(dut):
    """dac_sel = 0 loads the LSB register; dac_sel = 1 loads {ui_in, LSB} into dac_out."""
    tb = Tb(dut)
    await tb.start_up()
    tb.set_uio(DAC_SEL, 0)
    await tb.pulse(DAC_LOAD, ui_in=0x0F)
    assert int(tb.ana.dac_out.value) == 0, "dac_out changed by an LSB load"
    tb.set_uio(DAC_SEL, 1)
    await tb.pulse(DAC_LOAD, ui_in=0xF0)
    tb.set_uio(DAC_SEL, 0)
    await FallingEdge(dut.clk)
    assert int(tb.ana.dac_out.value) == 0xF00F


@cocotb.test()
async def test_config_register(dut):
    """load_config latches ui_in into cfg; cfg[3:0] drives sh_cap_en."""
    tb = Tb(dut)
    await tb.start_up()
    await tb.pulse(LOAD_CONFIG, ui_in=0xA5)
    dut.ui_in.value = 0x3C                       # no load: must not change cfg
    await ClockCycles(dut.clk, 2, rising=False)
    assert int(tb.ana.sh_cap_en.value) == 0x5
    assert int(tb.ana.dac_out.value) == 0, "dac_out changed by a config load"


@cocotb.test()
async def test_adc_sweep(dut):
    """Closed loop: every code converts exactly; the input changes during each conversion."""
    tb = Tb(dut)
    await tb.start_up()
    tb.set_uio(ENA, 1)
    for code in range(2**NBITS):
        result = await tb.convert((code + 0.5) * LSB, vin_during=(255 - code + 0.5) * LSB)
        assert result == code, f"code {code} converted to {result}"
    logger.info("all %d codes converted exactly", 2**NBITS)


@cocotb.test()
async def test_adc_clear(dut):
    """clear during a conversion stops it and clears the result."""
    tb = Tb(dut)
    await tb.start_up()
    tb.set_uio(ENA, 1)
    assert await tb.convert(200.5 * LSB) == 200
    await tb.pulse(START)
    await ClockCycles(dut.clk, 3, rising=False)
    assert tb.uio_out(DONE) == 0
    await tb.pulse(CLEAR)
    assert tb.uio_out(DONE) == 1 and tb.uio_out(TICK) == 0
    assert int(dut.uo_out.value) == 0
    assert int(tb.ana.adc_hold.value) == 1


def heichips26_FAIf_runner():

    proj_path = Path(__file__).resolve().parent

    sources  = []
    defines  = {"SIM": 1}      # enables the analog model in rtl/analogue_interface.sv
    includes = [proj_path / "../../rtl/"]

    if gl:
        # SCL models
        sources.append(Path(pdk_root) / pdk / "libs.ref" / scl / "verilog" / f"{scl}.v")
        sources.append(Path(pdk_root) / pdk / "libs.ref" / scl / "verilog" / "sg13cmos5l_udp.v")

        # Unpowered gate-level netlist of the macro
        sources.append(proj_path / f"../../final/nl/{hdl_toplevel}.nl.v")

        # Unpowered netlist: USE_POWER_PINS must NOT be defined at all
        # (passing USE_POWER_PINS=False would still define the macro).
    else:
        sources.append(proj_path / "../../rtl/heichips26_FAIf.sv")
        sources.append(proj_path / "../../rtl/gen/dac_reg.v")
        sources.append(proj_path / "../../rtl/gen/sar.v")

    # Behavioral model of the analog macro (RTL and gate level)
    sources.append(proj_path / "../../rtl/analogue_interface.sv")

    build_args = []

    if sim == "icarus":
        # -gno-specify: skip specify blocks; sg13cmos5l_stdcell.v uses
        # `ifnone with edge-sensitive paths`, which iverilog can't parse.
        build_args = ["-gno-specify"]

    if sim == "verilator":
        build_args = ["--timing", "--trace", "--trace-fst", "--trace-structs"]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        defines=defines,
        always=True,
        includes=includes,
        build_args=build_args,
        waves=True,
        timescale=("1ns", "1fs")
    )

    plusargs = []

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module="heichips26_FAIf_tb",
        plusargs=plusargs,
        waves=True,
    )


if __name__ == "__main__":
    heichips26_FAIf_runner()
