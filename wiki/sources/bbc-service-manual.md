---
title: BBC Microcomputer Service Manual
type: source
tags: [service-manual, source, hardware, model-b, repair]
publisher: Acorn Computers
year: 1982-1985
format: PDF
location: raw/manuals/BBCServiceManual.pdf
pages: 90
updated: 2026-05-16
---

# BBC Microcomputer Service Manual

Acorn's official service / repair manual for the BBC Model A/B (Issues 1-7 of the PCB). Covers electrical-level circuit operation, fault-finding, link options, and upgrade procedures.

Out of scope for **most** performance/demo work — this is a hardware-repair document, not a software reference. Useful contributions to the wiki are:

- **Reset distinction** (§3.1): cold start (power-up via "Reset A" signal) vs warm start (BREAK key) — distinguishable by polling System VIA IFR on entry.
- **Specific IC numbers** on the Model B PCB for cross-reference with the [[hardware/address-translation]] page (IC32, IC39, IC9).
- **DRAM CAS arrangement**: Model A = single bank (CAS1 only); Model B = two banks (CAS0 lower 16K, CAS1 upper 16K).
- **Link options** (§5): factory configurations and selectable options.
- **Hardware hints** (§7.3): potentially demoscene-relevant electrical tricks.

For chip-level documentation, prefer the per-chip pages ([[hardware/6502]], [[hardware/crtc-6845]], [[hardware/video-ula]], etc.) which have been built from primary manufacturer datasheets.

## Bibliographic

- **Title**: BBC Microcomputer Service Manual
- **Publisher**: Acorn Computers Ltd.
- **Year**: 1982 first edition; updated through ~1985 to cover PCB issues 1 through 7.
- **PDF source**: bitshifters/bbc-documents archive ([[reference_bbc_documents_repo]])
- **Format**: 90 pages including schematics and parts lists.

## Section index

| § | Title | Pages | Filed into |
|---|---|---|---|
| 1 | Introduction + specs | 5-8 | *out of scope (specs)* |
| 2 | General Description of Hardware | 9-12 | *out of scope (overview)* |
| 3 | Detailed Circuit Description | 13-27 | Cross-checks against per-chip pages; Reset-A note filed in [[os/break-intercept]] |
| 4 | Upgrading the PCB | 28-40 | *out of scope (repair procedures)* |
| 5 | Selection links and circuit changes | 41-50 | *out of scope (historical PCB link config, factory-set)* |
| 6 | Servicing and Fault-finding | 51-60 | *out of scope (also contains the canonical "test ROM" routine for finding dead machines — historical interest only)* |
| 7 | Interfacing Survey | 54-60 | §7.3 reviewed — hints are end-user PCB mods (110 baud trick, BREAK-key disable). No demoscene-relevant tricks. |
| 8 | Component location tables | 68-75 | *out of scope (parts list)* |
| 9 | Appendices (schematics, parts list) | 76-90 | *out of scope* |

## Filed into

- **§3 (Detailed Circuit Description)** → cross-checked against existing per-chip pages. Added cold-start vs warm-start "Reset A" mechanism note to [[os/break-intercept]]. Confirmed IC numbers for [[hardware/address-translation]] (IC32 addressable latch, IC39 74LS283 adder).
