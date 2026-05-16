---
title: OSBYTE Calls
type: os
tags: [osbyte, mos, reference]
sources: [naug-appendix-ab, bbc-user-guide]
updated: 2026-05-13
---

# OSBYTE Calls

Complete OSBYTE directory. **Call: `JSR &FFF4`** (indirected through `&20A`) with `A` = call number, `X`/`Y` per call. Most are documented in [[sources/naug-appendix-ab]] Appendix A (NAUG p443-447).

Many OSBYTEs follow the **read/modify/write byte protocol**: `NEW = (OLD AND Y) EOR X`, with the old value returned in X. Read: `X=0, Y=&FF`. Write: `X=val, Y=0`.

NAUG page numbers are *book pages* — they are 8 less than the PDF page numbers in `raw/manuals/New_Advanced_User_Guide.pdf` (book p171 = PDF p179, etc.). Where a wiki source page is available (chapter ingested), it's linked.

## Calls `&00`-`&1F` — actions

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&00` | 0 | Print / identify OS version | 427 | (Ch24, pending) |
| `&01` | 1 | Set user flag | 429 | (Ch24, pending) |
| `&02` | 2 | Select input stream | 105, 241 | (Ch6, pending) |
| `&03` | 3 | Select output stream | 108, 241 | (Ch6, pending) |
| `&04` | 4 | Enable/disable cursor editing | 225 | (Ch14, pending) |
| `&05` | 5 | Select printer destination | 422 | (Ch24, pending) |
| `&06` | 6 | Set printer ignore character | 423 | (Ch24, pending) |
| `&07` | 7 | Set RS423 receive baud rate | 242 | (Ch15, pending) |
| `&08` | 8 | Set RS423 transmit baud rate | 242 | (Ch15, pending) |
| `&09` | 9 | Set flashing-colour mark duration | 178 | [[sources/naug-ch13-video]] |
| `&0A` | 10 | Set flashing-colour space duration | 179 | [[sources/naug-ch13-video]] |
| `&0B` | 11 | Set keyboard auto-repeat delay | 224 | (Ch14, pending) |
| `&0C` | 12 | Set keyboard auto-repeat rate | 224 | (Ch14, pending) |
| `&0D` | 13 | Disable events | 121 | (Ch7, pending) |
| `&0E` | 14 | Enable events | 121 | (Ch7, pending) |
| `&0F` | 15 | Flush selected buffer class | 143 | (Ch9, pending) |
| `&10` | 16 | Select ADC channel | 366 | (Ch20, pending) |
| `&11` | 17 | Force ADC conversion | 367 | (Ch20, pending) |
| `&12` | 18 | Reset soft function keys | 227 | (Ch14, pending) |
| `&13` | 19 | **Wait for vertical sync** | 182 | [[sources/naug-ch13-video]] |
| `&14` | 20 | Explode character definition RAM | 172 | [[sources/naug-ch13-video]] |
| `&15` | 21 | Flush specific buffer | 143 | (Ch9, pending) |
| `&16` | 22 | Increment polling semaphore | 325 | (Ch17, pending) |
| `&17` | 23 | Decrement polling semaphore | 325 | (Ch17, pending) |
| `&18` | 24 | Select external sound (Electron) | 375 | (Ch21, pending) |
| `&19` | 25 | Restore default font definitions (Master) | 173 | [[sources/naug-ch13-video]] |

OSBYTEs `&1A`-`&43` (26-67) are **unused by the OS**.

## Calls `&44`-`&6F` — actions (sparse)

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&44` | 68 | Test for sideways RAM | 159 | [[sources/naug-ch12-memory]] |
| `&45` | 69 | Sideways RAM allocation | 160 | [[sources/naug-ch12-memory]] |
| `&6B` | 107 | Select 1MHz bus / cartridge | 413 | (Ch23, pending) |
| `&6C` | 108 | Select screen memory for direct access (Master) | 157 | [[sources/naug-ch12-memory]] |
| `&6D` | 109 | Make temporary filing system permanent | 260 | (Ch16, pending) |

`&46`-`&6A` and `&6E`-`&6F` unused.

## Calls `&70`-`&7F` — actions

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&70` | 112 | Select memory for VDU (Master) | 158 | [[sources/naug-ch12-memory]] |
| `&71` | 113 | Select memory for display (Master) | 158 | [[sources/naug-ch12-memory]] |
| `&72` | 114 | Write shadow memory use | 159 | [[sources/naug-ch12-memory]] |
| `&73` | 115 | Blank or restore palette (Electron) | 181 | [[sources/naug-ch13-video]] |
| `&74` | 116 | Reset sound system (Electron) | 375 | (Ch21, pending) |
| `&75` | 117 | Read VDU status | 176 | [[sources/naug-ch13-video]] |
| `&76` | 118 | Make LEDs reflect keyboard status | 228 | (Ch14, pending) |
| `&77` | 119 | Close *SPOOL/*EXEC files | 257 | (Ch16, pending) |
| `&78` | 120 | Write current keys pressed | 222 | (Ch14, pending) |
| `&79` | 121 | Perform keyboard scan | 221 | (Ch14, pending) |
| `&7A` | 122 | Perform keyboard scan from `&10` | 222 | (Ch14, pending) |
| `&7B` | 123 | Printer driver going dormant | 425 | (Ch24, pending) |
| `&7C` | 124 | Clear ESCAPE condition | 147 | (Ch10, pending) |
| `&7D` | 125 | Set ESCAPE condition | 147 | (Ch10, pending) |
| `&7E` | 126 | Acknowledge ESCAPE + effects | 147 | (Ch10, pending) |
| `&7F` | 127 | Check for EOF | 258 | (Ch16, pending) |

## Calls `&80`-`&9F` — reads / mixed

(Some numbers have two meanings depending on machine — both listed.)

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&80` | 128 | Read ADC channel | 365 | (Ch20, pending) |
| `&80` | 128 | Read buffer status | 143 | (Ch9, pending) |
| `&81` | 129 | Read key with time limit / read machine type | 221, 428 | (Ch14/24, pending) |
| `&82` | 130 | Read machine high-order address | 257 | (Ch16, pending) |
| `&83` | 131 | Read OSHWM (top of OS RAM) | 117 | (Ch6, pending) |
| `&84` | 132 | Read HIMEM (top of user RAM) | 157 | [[sources/naug-ch12-memory]] |
| `&85` | 133 | Read HIMEM for given mode | 157 | [[sources/naug-ch12-memory]] |
| `&86` | 134 | Read input cursor position (POS, VPOS) | 175 | [[sources/naug-ch13-video]] |
| `&87` | 135 | Read character at text cursor + screen mode | 174 | [[sources/naug-ch13-video]] |
| `&88` | 136 | Perform *CODE | 425 | (Ch24, pending) |
| `&89` | 137 | Perform *MOTOR | 262 | (Ch16, pending) |
| `&8A` | 138 | Insert value into buffer | 144 | (Ch9, pending) |
| `&8B` | 139 | Perform *OPT | 258 | (Ch16, pending) |
| `&8C` | 140 | Perform *TAPE | 262 | (Ch16, pending) |
| `&8D` | 141 | Perform *ROM | 264 | (Ch17, pending) |
| `&8E` | 142 | Enter language ROM | 322 | (Ch17, pending) |
| `&8F` | 143 | Issue paged ROM service request | 322 | (Ch17, pending) |
| `&90` | 144 | Perform *TV | 184 | [[sources/naug-ch13-video]] |
| `&91` | 145 | Get character from buffer | 145 | (Ch9, pending) |
| `&92` | 146 | Read from FRED (1MHz bus) | 403 | (Ch23, pending) |
| `&93` | 147 | Write to FRED | 403 | (Ch23, pending) |
| `&94` | 148 | Read from JIM | 403 | (Ch23, pending) |
| `&95` | 149 | Write to JIM | 403 | (Ch23, pending) |
| `&96` | 150 | Read from SHEILA | 403 | (Ch23, pending) |
| `&97` | 151 | Write to SHEILA | 403 | (Ch23, pending) |
| `&98` | 152 | Examine buffer status | 145 | (Ch9, pending) |
| `&99` | 153 | Put character into input buffer | 146 | (Ch9, pending) |
| `&9A` | 154 | **Write Video ULA control register + OS copy** (BBC) / Reset flash cycle (Electron) | 180 | [[sources/naug-ch13-video]] |
| `&9B` | 155 | **Write Video ULA palette register + OS copy** (XOR 7) | 181 | [[sources/naug-ch13-video]] |
| `&9C` | 156 | R/W 6850 control register + OS copy | 244 | (Ch15, pending) |
| `&9D` | 157 | Fast Tube BPUT | 254 | (Ch18, pending) |
| `&9E` | 158 | Read from speech processor | 374 | (Ch21, pending) |
| `&9F` | 159 | Write to speech processor | 374 | (Ch21, pending) |

## Calls `&A0`-`&BF` — reads / R/W

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&A0` | 160 | Read VDU variable value | 183 | [[sources/naug-ch13-video]] |
| `&A1` | 161 | Read CMOS RAM/EEPROM (Master) | 356 | (Ch19, pending) |
| `&A2` | 162 | Write CMOS RAM/EEPROM (Master) | 358 | (Ch19, pending) |
| `&A3` | 163 | (Reserved for app software) | — | — |
| `&A4` | 164 | Check for 6502 code | 326 | (Ch17, pending) |
| `&A5` | 165 | Read output cursor position (POS, VPOS) (Master) | 174 | [[sources/naug-ch13-video]] |
| `&A6` | 166 | Read start address of OS variables (LSB) | 118 | (Ch6, pending) |
| `&A7` | 167 | Read start address of OS variables (MSB) | 118 | (Ch6, pending) |
| `&A8` | 168 | ROM pointer table address (LSB) | 323 | (Ch17, pending) |
| `&A9` | 169 | ROM pointer table address (MSB) | 323 | (Ch17, pending) |
| `&AA` | 170 | ROM info table address (LSB) | 323 | (Ch17, pending) |
| `&AB` | 171 | ROM info table address (MSB) | 323 | (Ch17, pending) |
| `&AC` | 172 | Key translation table address (LSB) | 223 | (Ch14, pending) |
| `&AD` | 173 | Key translation table address (MSB) | 223 | (Ch14, pending) |
| `&AE` | 174 | VDU variables address (LSB) | 183 | [[sources/naug-ch13-video]] |
| `&AF` | 175 | VDU variables address (MSB) | 183 | [[sources/naug-ch13-video]] |
| `&B0` | 176 | R/W CFS timeout counter | 249 | (Ch15, pending) |
| `&B1` | 177 | R/W input source | 105 | (Ch6, pending) |
| `&B2` | 178 | R/W keyboard semaphore | 230 | (Ch14, pending) |
| `&B3` | 179 | R/W primary OSHWM | 117 | (Ch6, pending) |
| `&B4` | 180 | R/W current OSHWM | 117 | (Ch6, pending) |
| `&B5` | 181 | R/W RS423 mode | 243 | (Ch15, pending) |
| `&B6` | 182 | R character def explosion (B / Electron) **OR** R/W use printer ignore char (Master) | 173, 423 | [[sources/naug-ch13-video]] |
| `&B7` | 183 | R/W cassette/ROM filing system switch | 263 | (Ch16, pending) |
| `&B8` | 184 | Read OS copy of Video ULA control | 182 | [[sources/naug-ch13-video]] |
| `&B9` | 185 | Read OS copy of Video ULA palette **OR** R/W polling semaphore | 182, 326 | [[sources/naug-ch13-video]] |
| `&BA` | 186 | **R/W active ROM number at last BRK** | 135 | [[sources/naug-ch08-interrupts]] |
| `&BB` | 187 | R/W BASIC ROM number | 324 | (Ch17, pending) |
| `&BC` | 188 | Read current ADC channel | 367 | (Ch20, pending) |
| `&BD` | 189 | Read max ADC channel | 367 | (Ch20, pending) |
| `&BE` | 190 | R/W ADC conversion type | 368 | (Ch20, pending) |
| `&BF` | 191 | R/W RS423 use flag | 244 | (Ch15, pending) |

## Calls `&C0`-`&DF` — R/W state

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&C0` | 192 | R/W RS423 control flag | 245 | (Ch15, pending) |
| `&C1` | 193 | R/W flash counter | 180 | [[sources/naug-ch13-video]] |
| `&C2` | 194 | R/W flash mark duration | 179 | [[sources/naug-ch13-video]] |
| `&C3` | 195 | R/W flash space duration | 179 | [[sources/naug-ch13-video]] |
| `&C4` | 196 | R/W keyboard auto-repeat delay | 224 | (Ch14, pending) |
| `&C5` | 197 | R/W keyboard auto-repeat rate | 225 | (Ch14, pending) |
| `&C6` | 198 | R/W *EXEC file handle | 258 | (Ch16, pending) |
| `&C7` | 199 | R/W *SPOOL file handle | 258 | (Ch16, pending) |
| `&C8` | 200 | R/W ESCAPE and BREAK effects | 148, 419 | (Ch10/Ch24, pending) |
| `&C9` | 201 | R/W keyboard disable | 228 | (Ch14, pending) |
| `&CA` | 202 | R/W keyboard status | 229 | (Ch14, pending) |
| `&CB` | 203 | R/W RS423 handshake **OR** R/W Electron ULA IRQ bit mask | 246, 132 | [[sources/naug-ch08-interrupts]] |
| `&CC` | 204 | R/W RS423 input suppression **OR** R/W firm key pointer (Electron) | 246, 231 | (Ch15/Ch14, pending) |
| `&CD` | 205 | R/W cassette/RS423 selection **OR** R/W firm key string length (Electron) | 246, 231 | (Ch15/Ch14, pending) |
| `&CE` | 206 | R/W Econet OS call interception | 118 | (Ch6, pending) |
| `&CF` | 207 | R/W Econet OSRDCH interception | 118 | (Ch6, pending) |
| `&D0` | 208 | R/W Econet OSWRCH interception | 118 | (Ch6, pending) |
| `&D1` | 209 | R/W speech suppression status | 373 | (Ch21, pending) |
| `&D2` | 210 | R/W sound suppression status | 373 | (Ch21, pending) |
| `&D3` | 211 | R/W BELL channel | 374 | (Ch21, pending) |
| `&D4` | 212 | R/W BELL amplitude/envelope | 374 | (Ch21, pending) |
| `&D5` | 213 | R/W BELL frequency | 374 | (Ch21, pending) |
| `&D6` | 214 | R/W BELL duration | 374 | (Ch21, pending) |
| `&D7` | 215 | R/W OS startup message + !BOOT options | 419 | (Ch24, pending) |
| `&D8` | 216 | R/W soft key string length | 227 | (Ch14, pending) |
| `&D9` | 217 | R/W lines printed since last page | 176 | [[sources/naug-ch13-video]] |
| `&DA` | 218 | R/W number of characters in VDU queue | 168 | [[sources/naug-ch13-video]] |
| `&DB` | 219 | R/W TAB character | 231 | (Ch14, pending) |
| `&DC` | 220 | R/W ESCAPE character | 148, 232 | (Ch10/Ch14, pending) |
| `&DD` | 221 | R/W character `&C0-&CF` status | 226 | (Ch14, pending) |
| `&DE` | 222 | R/W character `&D0-&DF` status | 226 | (Ch14, pending) |
| `&DF` | 223 | R/W character `&E0-&EF` status | 226 | (Ch14, pending) |

## Calls `&E0`-`&FF` — R/W state

| Hex | # | Function | NAUG p | Source |
|---|---|---|---|---|
| `&E0` | 224 | R/W character `&F0-&FF` status | 226 | (Ch14, pending) |
| `&E1` | 225 | R/W function key status | 226 | (Ch14, pending) |
| `&E2` | 226 | R/W SHIFT+fn key status | 226 | (Ch14, pending) |
| `&E3` | 227 | R/W CTRL+fn key status | 226 | (Ch14, pending) |
| `&E4` | 228 | R/W CTRL+SHIFT+fn key status | 226 | (Ch14, pending) |
| `&E5` | 229 | R/W ESCAPE key status | 149 | (Ch10, pending) |
| `&E6` | 230 | R/W ESCAPE effects | 149 | (Ch10, pending) |
| `&E7` | 231 | **R/W user 6522 VIA IRQ bit mask** | 130 | [[sources/naug-ch08-interrupts]] |
| `&E8` | 232 | **R/W 6850 IRQ bit mask** / R/W ext sound semaphore (Electron) | 131, 247, 375 | [[sources/naug-ch08-interrupts]] |
| `&E9` | 233 | **R/W system 6522 VIA IRQ bit mask** | 131 | [[sources/naug-ch08-interrupts]] |
| `&EA` | 234 | R/W Tube presence flag | 347 | (Ch18, pending) |
| `&EB` | 235 | R/W speech processor presence flag | 373 | (Ch21, pending) |
| `&EC` | 236 | R/W output stream destination | 109 | (Ch6, pending) |
| `&ED` | 237 | R/W cursor editing status | 225 | (Ch14, pending) |
| `&EE` | 238 | R/W base for numeric keypad | 230 | (Ch14, pending) |
| `&EF` | 239 | R/W shadow state | 159 | [[sources/naug-ch12-memory]] |
| `&F0` | 240 | R/W country code | 428 | (Ch24, pending) |
| `&F1` | 241 | R/W user flag | 429 | (Ch24, pending) |
| `&F2` | 242 | R/W OS copy of serial ULA | 247 | (Ch15, pending) |
| `&F3` | 243 | R/W timer switch state | 353 | (Ch19, pending) |
| `&F4` | 244 | R/W soft key consistency flag | 227 | (Ch14, pending) |
| `&F5` | 245 | R/W printer destination | 422 | (Ch24, pending) |
| `&F6` | 246 | R/W printer ignore character | 423 | (Ch24, pending) |
| `&F7` | 247 | R/W BREAK intercept code (JMP) | 420 | (Ch24, pending) |
| `&F8` | 248 | R/W BREAK intercept code (LSB) | 420 | (Ch24, pending) |
| `&F9` | 249 | R/W BREAK intercept code (MSB) | 420 | (Ch24, pending) |
| `&FA` | 250 | R/W VDU shadow memory flag | 158 | [[sources/naug-ch12-memory]] |
| `&FB` | 251 | R/W display shadow memory flag | 159 | [[sources/naug-ch12-memory]] |
| `&FC` | 252 | R/W current language ROM number | 324 | (Ch17, pending) |
| `&FD` | 253 | R/W last BREAK type | 420 | (Ch24, pending) |
| `&FE` | 254 | R/W shift key effect / R/W available RAM | 230, 160 | [[sources/naug-ch12-memory]] |
| `&FF` | 255 | R/W start-up options | 421 | (Ch24, pending) |

## Performance note

OSBYTE round-trip is **expensive** — JSR + indirect through `&20A` + dispatch + work + RTS. A single `OSBYTE &13` (wait vsync) costs hundreds of cycles overhead before any waiting happens.

For tight raster code: read state via the OSBYTE once, cache the result, then do direct hardware writes inside your loop. E.g. for palette updates, query the OS palette copy once via OSBYTE `&B9`, then `STA &FE21` directly inside the hot loop — the OS shadow goes stale, but you'll restore it before exiting your routine (or accept the desync if MOS won't be called again).

See [[hardware/video-ula]] for the OSBYTE-vs-direct trade-off discussion.

---

<!-- llm-wiki-footer -->
*This wiki is curated by an LLM following the **LLM-Wiki methodology** — a human curates source documents, the LLM compiles structured cross-linked markdown. Content may contain errors, omissions, or stale claims. For authoritative information refer to the original source documents in the [bbc-documents](https://github.com/bitshifters/bbc-documents) GitHub archive.*
