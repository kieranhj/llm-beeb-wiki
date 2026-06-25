---
title: 6502.org — 65C02 Opcode Reference (with NMOS / W65C02S deltas)
type: source
tags: [6502, 65c02, 65c12, opcodes, undocumented]
url: http://www.6502.org/tutorials/65c02opcodes.html
ingested: 2026-06-17
---

# 6502.org — 65C02 Opcodes

## Bibliographic

- **URL:** http://www.6502.org/tutorials/65c02opcodes.html
- **Author:** maintained on 6502.org by the 6502.org community.
- **Date:** undated; references span 1980s datasheets through W65C02S errata of the 2000s.
- **Format:** HTML tutorial. Web-fetched, not archived locally.

## Summary

The community-canonical opcode-by-opcode reference for the 65C02 family. Covers the standard CMOS opcodes added over NMOS, then enumerates every unused opcode and what each variant of the chip does with it: 1-byte 1-cycle NOPs in columns 3/7/B/F on G65SC/R65SC parts; 2-byte/2- or 3- or 4-cycle reads in the column-2 and special slots; the Rockwell extensions (BBR/BBS/RMB/SMB) occupying columns 7/F on R65C02; and the WDC W65C02S reservations (some of which trap or run as longer multi-byte NOPs).

This page was consulted to verify the behaviour of opcode `$93` and the surrounding undefined-opcode space on the Master's R65SC12. Result: `$93` is a 1-byte, 1-cycle NOP — there is no BRK trap on Acorn's CPU variants.

## Key technical claims (relevant to BBC)

- All `$x3` and `$xB` opcodes are 1-byte, 1-cycle NOPs on every 65C02 family member that's not the WDC W65C02S — including Acorn's R65SC12 in the Master 128 and Compact.
- All `$x7` and `$xF` opcodes are 1-byte, 1-cycle NOPs on the G65SC/R65SC parts. On Rockwell R65C02 they become RMB/SMB and BBR/BBS respectively.
- The column-2 holes (`$02 $22 $42 $62 $82 $C2 $E2`) are 2-byte, 2-cycle NOPs that read and discard the operand byte.
- `$44` is a 2-byte, 3-cycle NOP that reads from the zp address named by the operand.
- `$54 $D4 $F4` are 2-byte, 4-cycle NOPs reading from `(operand + X) & $FF`.
- `$5C` is a 3-byte, 8-cycle NOP described as reading "from somewhere in the 64K range, using no known address mode" — empirically reads from `(addr & $FF00) | $FF` and `$FFFF`.
- `$DC $FC` are 3-byte, 4-cycle NOPs reading the absolute address named by the operand.
- I/O hazard explicitly called out: "all variations of this skip-two-bytes trick … cause a read according to ADL and ADH, and trouble can result if that read touches an I/O device."
- WDC W65C02S deviates: reserved-for-future-expansion opcodes either trap or take additional cycles. **Not relevant for any Acorn machine** — Acorn never shipped a WDC part.

## Filed into

- [[hardware/6502-undefined-opcodes]] — primary destination for all of the above.
- [[hardware/6502]] — corrected the "BRK on undocumented" claim in the variant-detection section.

## Cross-refs

- [[sources/naug-ch05-6502-isa]] — NAUG's instruction set chapter does not enumerate the unused opcodes; this 6502.org reference fills that gap.
- [[sources/master-arm]] — Master ARM mentions the 65C12 by name but does not document its undefined-opcode behaviour either.

## Open follow-ups

- An NMOS undocumented-opcode page (LAX / SAX / DCP / ISC / etc.) would round out the picture for Model B and Electron. Canonical reference is the Oxyron table at http://www.oxyron.de/html/opcodes02.html — not yet fetched.
- Real-hardware verification on a Master: does `$5C` actually read `$FFFF` on the second cycle? The 6502.org page's wording is hedged. Would benefit from a jsbeeb trace.

---

<!-- llm-wiki-footer -->
*This wiki is curated by **Claude** following the [LLM-Wiki methodology](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
