-------------------------------------------------------------------------------
-- Title      : Test bench for the Successive Approximation Register
-- Project    : FABulous Analogue Interface (FAIf) for HeiChips 2026
-------------------------------------------------------------------------------
-- File       : sar_tb.vhdl
-- Author     : Torsten Maehne  <torsten.maehne@bfh.ch>
-- Company    : BFH-EIT
-- Created    : 2026-08-06
-- Last update: 2026-10-09
-- Platform   : GHDL
-- Standard   : VHDL-1993
-------------------------------------------------------------------------------
-- Description:
--
-- Self-checking test bench for `sar`. An ideal comparator model closes the
-- loop: the analogue input lies half an LSB above `code_in`, so comp = '1'
-- (keep the bit) when code_in >= ref_out.
--
-- `sar_ref` (sar_ref.vhdl, the SAR before the 2026-10-09 fixes) runs side by
-- side on the same clock and stimuli with its own comparator model. Every
-- cycle, after the outputs have settled, the bench checks:
-- - sh_en = not hold_ref, done = done_ref, ref_out = ref_out_ref
--   (same conversion sequence and S&H timing, cycle by cycle);
-- - tick = tick_ref one cycle later, and value then equals value_ref
--   (the final result);
-- - value only changes on tick or after clear.
--
-- Phase 1 converts every code once and checks value = code_in on tick.
-- Phase 2 runs random start/clear/ena/input sequences.
-- Any mismatch stops the simulation with severity failure.
-------------------------------------------------------------------------------
-- Copyright (c) 2026 HeiChips 2026 FAIf team
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-- 2026-08-06  1.0      maehne  Created
-- 2026-10-09  1.1      FAIf    comparator model, all codes, asserts,
--                              equivalence checks against sar_ref
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

-------------------------------------------------------------------------------

entity sar_tb is

end entity sar_tb;

-------------------------------------------------------------------------------

architecture bench of sar_tb is

  -- stimuli parameters
  constant CLK_PERIOD      : delay_length := 10 ns;  -- clock period
  constant N_RANDOM_CYCLES : natural      := 20000;  -- length of phase 2

  -- component generics
  constant NBITS : positive := 8;

  -- common stimuli
  signal clk     : std_logic := '1';
  signal rst_n   : std_logic := '0';
  signal clear   : std_logic := '0';
  signal ena     : std_logic := '0';
  signal start   : std_logic := '0';
  signal code_in : natural range 0 to 2**NBITS-1 := 0;  -- analogue input as code

  -- sar (device under verification)
  signal done    : std_logic;
  signal tick    : std_logic;
  signal value   : std_logic_vector(NBITS-1 downto 0);
  signal sh_en   : std_logic;
  signal ref_out : std_logic_vector(NBITS-1 downto 0);
  signal comp    : std_logic;

  -- sar_ref (golden model)
  signal done_ref    : std_logic;
  signal tick_ref    : std_logic;
  signal value_ref   : std_logic_vector(NBITS-1 downto 0);
  signal hold_ref    : std_logic;
  signal ref_out_ref : std_logic_vector(NBITS-1 downto 0);
  signal comp_ref    : std_logic;

  -- test bench signals
  signal tb_finished : boolean := false;  -- flag end of tests

begin  -- architecture bench

  duv : entity work.sar(rtl)
    generic map (
      NBITS => NBITS)
    port map (
      clk     => clk,
      rst_n   => rst_n,
      clear   => clear,
      ena     => ena,
      start   => start,
      done    => done,
      tick    => tick,
      value   => value,
      sh_en   => sh_en,
      ref_out => ref_out,
      comp    => comp);

  golden : entity work.sar_ref(rtl)
    generic map (
      NBITS => NBITS)
    port map (
      clk     => clk,
      rst_n   => rst_n,
      clear   => clear,
      ena     => ena,
      start   => start,
      done    => done_ref,
      tick    => tick_ref,
      value   => value_ref,
      hold    => hold_ref,
      ref_out => ref_out_ref,
      comp    => comp_ref);

  -- Ideal comparators: V_in = (code_in + 0.5) LSB, V_dac = ref_out LSB
  comp     <= '1' when code_in >= to_integer(unsigned(ref_out))     else '0';
  comp_ref <= '1' when code_in >= to_integer(unsigned(ref_out_ref)) else '0';

  -- Clock and reset generation
  clk   <= not clk after CLK_PERIOD / 2 when not tb_finished;
  rst_n <= '0', '1' after 2.25 * CLK_PERIOD;

  -- Stimuli generation
  STIM : process
    variable seed1, seed2 : positive := 42;
    variable r            : real;
    variable n_cycles     : natural;
    variable n_old_wrong  : natural := 0;  -- old SAR: value wrong at its tick
  begin
    wait until rst_n = '1';
    wait until rising_edge(clk);
    ena <= '1';

    -- Phase 1: convert every code once
    for code in 0 to 2**NBITS-1 loop
      code_in <= code;
      start   <= '1';
      wait until rising_edge(clk);
      start   <= '0';
      n_cycles := 0;
      loop
        wait until falling_edge(clk);
        if tick_ref = '1' and to_integer(unsigned(value_ref)) /= code then
          n_old_wrong := n_old_wrong + 1;
        end if;
        exit when tick = '1';
        n_cycles := n_cycles + 1;
        assert n_cycles < 2 * NBITS + 4
          report "no tick for code " & integer'image(code)
          severity failure;
      end loop;
      assert to_integer(unsigned(value)) = code
        report "code " & integer'image(code) & " converted to " &
        integer'image(to_integer(unsigned(value)))
        severity failure;
      assert sh_en = '1' and done = '1'
        report "SAR not idle on tick (code " & integer'image(code) & ")"
        severity failure;
      wait until rising_edge(clk);
    end loop;
    report "phase 1: all " & integer'image(2**NBITS) & " codes converted exactly; " &
      "old SAR: value at its tick wrong in " & integer'image(n_old_wrong) &
      " of " & integer'image(2**NBITS) & " conversions";

    -- Phase 2: random start/clear/ena/input sequences
    for i in 1 to N_RANDOM_CYCLES loop
      uniform(seed1, seed2, r);
      if r < 0.9 then ena <= '1'; else ena <= '0'; end if;
      uniform(seed1, seed2, r);
      if r < 0.2 then start <= '1'; else start <= '0'; end if;
      uniform(seed1, seed2, r);
      if r < 0.02 then clear <= '1'; else clear <= '0'; end if;
      uniform(seed1, seed2, r);
      if r < 0.05 then
        uniform(seed1, seed2, r);
        code_in <= integer(trunc(r * real(2**NBITS)));  -- r < 1.0: 0 .. 2**NBITS-1
      end if;
      wait until rising_edge(clk);
    end loop;
    report "phase 2: " & integer'image(N_RANDOM_CYCLES) &
      " random cycles equivalent to sar_ref";

    report "sar_tb: PASS";
    tb_finished <= true;
    wait;
  end process STIM;

  -- Cycle-by-cycle comparison with the golden model
  CHECK : process
    variable tick_ref_d : std_logic := '0';  -- tick_ref just before the last edge
    variable clear_d    : std_logic := '0';  -- clear just before the last edge
    variable value_exp  : std_logic_vector(NBITS-1 downto 0) := (others => '0');
  begin
    wait until rising_edge(clk);
    tick_ref_d := tick_ref;
    clear_d    := clear;
    wait until falling_edge(clk);
    if rst_n = '0' then
      assert sh_en = '1' and done = '1' and tick = '0' and unsigned(value) = 0
        report "wrong reset values" severity failure;
      value_exp := (others => '0');
    else
      assert sh_en = not hold_ref
        report "sh_en /= not hold_ref" severity failure;
      assert done = done_ref
        report "done /= done_ref" severity failure;
      assert ref_out = ref_out_ref
        report "ref_out /= ref_out_ref" severity failure;
      assert tick = tick_ref_d
        report "tick is not tick_ref delayed by one cycle" severity failure;
      if tick = '1' then
        value_exp := value_ref;
      elsif clear_d = '1' then
        value_exp := (others => '0');
      end if;
      assert value = value_exp
        report "value /= expected result" severity failure;
    end if;
  end process CHECK;

end architecture bench;
