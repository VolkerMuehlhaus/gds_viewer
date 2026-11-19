#!/usr/bin/env python3
########################################################################
#
# Copyright 2025 Volker Muehlhaus and IHP PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
########################################################################

"""GDSII layout viewer (window and headless PNG), using gdstk and matplotlib, with IHP SG13G2 layer styling."""

import argparse
import sys


__version__ = "0.3.0"

# Hardcoded from sg13g2.lyp (IHP SG13G2 KLayout layer properties): (layer, datatype)
# -> (fill-color, dither-pattern name). Values are copied verbatim from the .lyp's
# <fill-color> and <dither-pattern>. See PATTERN_TILES below for what each pattern
# name actually looks like.
LAYER_STYLES = {
    (40, 0): ("#ffffff", "I1"),  # Substrate.drawing
    (40, 25): ("#39bfff", "C1"),  # Substrate.text
    (1, 0): ("#00ff00", "C2"),  # Activ.drawing
    (1, 1): ("#00ff00", "C3"),  # Activ.label
    (1, 2): ("#00ff00", "C2"),  # Activ.pin
    (1, 3): ("#00ff00", "C2"),  # Activ.net
    (1, 4): ("#00ff00", "C3"),  # Activ.boundary
    (1, 19): ("#ffff00", "I1"),  # Activ.lvs
    (1, 20): ("#00ff00", "C2"),  # Activ.mask
    (1, 22): ("#00ff00", "C4"),  # Activ.filler
    (1, 23): ("#00ff00", "I1"),  # Activ.nofill
    (1, 26): ("#00cc66", "C5"),  # Activ.OPC
    (1, 27): ("#00ff00", "C6"),  # Activ.iOPC
    (1, 28): ("#ff0000", "C3"),  # Activ.noqrc
    (5, 0): ("#bf4026", "C7"),  # GatPoly.drawing
    (5, 1): ("#bf4026", "C3"),  # GatPoly.label
    (5, 2): ("#bf4026", "C3"),  # GatPoly.pin
    (5, 3): ("#bf4026", "C7"),  # GatPoly.net
    (5, 4): ("#bf4026", "C7"),  # GatPoly.boundary
    (5, 22): ("#bf4026", "C7"),  # GatPoly.filler
    (5, 23): ("#bf4026", "I1"),  # GatPoly.nofill
    (5, 26): ("#9900e6", "I1"),  # GatPoly.OPC
    (5, 27): ("#ffff00", "C8"),  # GatPoly.iOPC
    (5, 28): ("#ff0000", "C3"),  # GatPoly.noqrc
    (128, 0): ("#bf4026", "C7"),  # PolyRes.drawing
    (128, 1): ("#bf4026", "C3"),  # PolyRes.label
    (128, 2): ("#bf4026", "C3"),  # PolyRes.pin
    (128, 3): ("#bf4026", "C7"),  # PolyRes.net
    (128, 4): ("#bf4026", "C7"),  # PolyRes.boundary
    (31, 0): ("#268c6b", "C9"),  # NWell.drawing
    (31, 1): ("#268c6b", "C3"),  # NWell.label
    (31, 2): ("#268c6b", "C3"),  # NWell.pin
    (31, 3): ("#268c6b", "C9"),  # NWell.net
    (31, 4): ("#268c6b", "C3"),  # NWell.boundary
    (32, 0): ("#8c8ca6", "C10"),  # nBuLay.drawing
    (32, 1): ("#8c8ca6", "C10"),  # nBuLay.label
    (32, 2): ("#8c8ca6", "C10"),  # nBuLay.pin
    (32, 3): ("#8c8ca6", "C10"),  # nBuLay.net
    (32, 4): ("#8c8ca6", "C10"),  # nBuLay.boundary
    (32, 21): ("#268c6b", "C3"),  # nBuLay.block
    (46, 21): ("#ff8000", "C11"),  # PWell.block
    (14, 0): ("#ccb899", "C12"),  # pSD.drawing
    (7, 0): ("#00cc66", "C13"),  # nSD.drawing
    (7, 21): ("#00cc66", "C14"),  # nSD.block
    (28, 0): ("#9900e6", "C15"),  # SalBlock.drawing
    (44, 0): ("#ffffcc", "C16"),  # ThickGateOx.drawing
    (6, 0): ("#00ffff", "C17"),  # Cont.drawing
    (6, 3): ("#00ffff", "C17"),  # Cont.net
    (6, 4): ("#00ffff", "C17"),  # Cont.boundary
    (6, 26): ("#ffff00", "I1"),  # Cont.OPC
    (8, 0): ("#39bfff", "C1"),  # Metal1.drawing
    (8, 1): ("#39bfff", "C1"),  # Metal1.label
    (8, 2): ("#39bfff", "C1"),  # Metal1.pin
    (8, 3): ("#39bfff", "C1"),  # Metal1.net
    (8, 4): ("#39bfff", "I1"),  # Metal1.boundary
    (8, 20): ("#39bfff", "C1"),  # Metal1.mask
    (8, 22): ("#39bfff", "C1"),  # Metal1.filler
    (8, 23): ("#39bfff", "I1"),  # Metal1.nofill
    (8, 24): ("#000000", "C18"),  # Metal1.slit
    (8, 25): ("#39bfff", "C1"),  # Metal1.text
    (8, 26): ("#ffff00", "I1"),  # Metal1.OPC
    (8, 28): ("#ff0000", "C3"),  # Metal1.noqrc
    (8, 29): ("#bf4026", "C19"),  # Metal1.res
    (8, 33): ("#39bfff", "I1"),  # Metal1.iprobe
    (8, 34): ("#39bfff", "I1"),  # Metal1.diffprb
    (19, 0): ("#ccccff", "C20"),  # Via1.drawing
    (19, 3): ("#ccccff", "C20"),  # Via1.net
    (19, 4): ("#ccccff", "C20"),  # Via1.boundary
    (10, 0): ("#ccccd9", "C21"),  # Metal2.drawing
    (10, 1): ("#ccccd9", "C21"),  # Metal2.label
    (10, 2): ("#ccccd9", "C21"),  # Metal2.pin
    (10, 3): ("#ccccd9", "C21"),  # Metal2.net
    (10, 4): ("#ccccd9", "C21"),  # Metal2.boundary
    (10, 20): ("#ccccd9", "C21"),  # Metal2.mask
    (10, 22): ("#ccccd9", "C21"),  # Metal2.filler
    (10, 23): ("#ccccd9", "I1"),  # Metal2.nofill
    (10, 24): ("#000000", "C18"),  # Metal2.slit
    (10, 25): ("#ccccd9", "C21"),  # Metal2.text
    (10, 26): ("#ffff00", "I1"),  # Metal2.OPC
    (10, 28): ("#ff0000", "C3"),  # Metal2.noqrc
    (10, 29): ("#bf4026", "C19"),  # Metal2.res
    (10, 33): ("#ccccd9", "I1"),  # Metal2.iprobe
    (10, 34): ("#ccccd9", "I1"),  # Metal2.diffprb
    (29, 0): ("#ff3736", "C22"),  # Via2.drawing
    (29, 3): ("#ff3736", "C22"),  # Via2.net
    (29, 4): ("#ff3736", "C22"),  # Via2.boundary
    (30, 0): ("#d80000", "C23"),  # Metal3.drawing
    (30, 1): ("#d80000", "C23"),  # Metal3.label
    (30, 2): ("#d80000", "C23"),  # Metal3.pin
    (30, 3): ("#d80000", "C23"),  # Metal3.net
    (30, 4): ("#d80000", "C23"),  # Metal3.boundary
    (30, 20): ("#d80000", "C23"),  # Metal3.mask
    (30, 22): ("#d80000", "C23"),  # Metal3.filler
    (30, 23): ("#d80000", "I1"),  # Metal3.nofill
    (30, 24): ("#000000", "C18"),  # Metal3.slit
    (30, 25): ("#d80000", "C23"),  # Metal3.text
    (30, 26): ("#ffff00", "I1"),  # Metal3.OPC
    (30, 28): ("#ff0000", "C3"),  # Metal3.noqrc
    (30, 29): ("#bf4026", "C19"),  # Metal3.res
    (30, 33): ("#d80000", "I1"),  # Metal3.iprobe
    (30, 34): ("#d80000", "I1"),  # Metal3.diffprb
    (36, 0): ("#268c6b", "C24"),  # MIM.drawing
    (36, 3): ("#268c6b", "C24"),  # MIM.net
    (36, 4): ("#268c6b", "C3"),  # MIM.boundary
    (129, 0): ("#ffe6bf", "C25"),  # Vmim.drawing
    (49, 0): ("#9ba940", "C26"),  # Via3.drawing
    (49, 3): ("#9ba940", "C26"),  # Via3.net
    (49, 4): ("#9ba940", "C26"),  # Via3.boundary
    (50, 0): ("#93e837", "C27"),  # Metal4.drawing
    (50, 1): ("#93e837", "C27"),  # Metal4.label
    (50, 2): ("#93e837", "C27"),  # Metal4.pin
    (50, 3): ("#93e837", "C27"),  # Metal4.net
    (50, 4): ("#93e837", "C27"),  # Metal4.boundary
    (50, 20): ("#93e837", "C27"),  # Metal4.mask
    (50, 22): ("#93e837", "C27"),  # Metal4.filler
    (50, 23): ("#93e837", "I1"),  # Metal4.nofill
    (50, 24): ("#000000", "C18"),  # Metal4.slit
    (50, 25): ("#93e837", "C27"),  # Metal4.text
    (50, 26): ("#ffff00", "I1"),  # Metal4.OPC
    (50, 28): ("#ff0000", "C3"),  # Metal4.noqrc
    (50, 29): ("#bf4026", "C19"),  # Metal4.res
    (50, 33): ("#d80000", "I1"),  # Metal4.iprobe
    (50, 34): ("#d80000", "I1"),  # Metal4.diffprb
    (66, 0): ("#deac5e", "C28"),  # Via4.drawing
    (66, 3): ("#deac5e", "C28"),  # Via4.net
    (66, 4): ("#deac5e", "C28"),  # Via4.boundary
    (67, 0): ("#dcd146", "C29"),  # Metal5.drawing
    (67, 1): ("#dcd146", "C29"),  # Metal5.label
    (67, 2): ("#dcd146", "C29"),  # Metal5.pin
    (67, 3): ("#dcd146", "C29"),  # Metal5.net
    (67, 4): ("#dcd146", "C29"),  # Metal5.boundary
    (67, 20): ("#dcd146", "C29"),  # Metal5.mask
    (67, 22): ("#dcd146", "C29"),  # Metal5.filler
    (67, 23): ("#dcd146", "I1"),  # Metal5.nofill
    (67, 24): ("#000000", "C18"),  # Metal5.slit
    (67, 25): ("#dcd146", "C29"),  # Metal5.text
    (67, 26): ("#ffff00", "I1"),  # Metal5.OPC
    (67, 28): ("#ff0000", "C3"),  # Metal5.noqrc
    (67, 29): ("#bf4026", "C19"),  # Metal5.res
    (67, 33): ("#dcd146", "I1"),  # Metal5.iprobe
    (67, 34): ("#dcd146", "I1"),  # Metal5.diffprb
    (125, 0): ("#ffe6bf", "C25"),  # TopVia1.drawing
    (125, 3): ("#ffe6bf", "C25"),  # TopVia1.net
    (125, 4): ("#ffe6bf", "I1"),  # TopVia1.boundary
    (126, 0): ("#ffe6bf", "C30"),  # TopMetal1.drawing
    (126, 1): ("#ffe6bf", "C30"),  # TopMetal1.label
    (126, 2): ("#ffe6bf", "C30"),  # TopMetal1.pin
    (126, 3): ("#ffe6bf", "C30"),  # TopMetal1.net
    (126, 4): ("#ffe6bf", "I1"),  # TopMetal1.boundary
    (126, 20): ("#ffe6bf", "C30"),  # TopMetal1.mask
    (126, 22): ("#ffe6bf", "C30"),  # TopMetal1.filler
    (126, 23): ("#ffe6bf", "I1"),  # TopMetal1.nofill
    (126, 24): ("#000000", "I1"),  # TopMetal1.slit
    (126, 25): ("#ffe6bf", "C0"),  # TopMetal1.text
    (126, 28): ("#ff0000", "C3"),  # TopMetal1.noqrc
    (126, 29): ("#bf4026", "C19"),  # TopMetal1.res
    (126, 33): ("#ffe6bf", "I1"),  # TopMetal1.iprobe
    (126, 34): ("#ffe6bf", "I1"),  # TopMetal1.diffprb
    (133, 0): ("#ff8000", "C31"),  # TopVia2.drawing
    (133, 3): ("#ff8000", "C31"),  # TopVia2.net
    (133, 4): ("#ff8000", "I1"),  # TopVia2.boundary
    (134, 0): ("#ff8000", "C32"),  # TopMetal2.drawing
    (134, 1): ("#ff8000", "C32"),  # TopMetal2.label
    (134, 2): ("#ff8000", "C32"),  # TopMetal2.pin
    (134, 3): ("#ff8000", "C32"),  # TopMetal2.net
    (134, 4): ("#ff8000", "I1"),  # TopMetal2.boundary
    (134, 20): ("#ff8000", "C32"),  # TopMetal2.mask
    (134, 22): ("#ff8000", "C1"),  # TopMetal2.filler
    (134, 23): ("#ff8000", "I1"),  # TopMetal2.nofill
    (134, 24): ("#000000", "I1"),  # TopMetal2.slit
    (134, 25): ("#ff8000", "C32"),  # TopMetal2.text
    (134, 28): ("#ff0000", "C3"),  # TopMetal2.noqrc
    (134, 29): ("#bf4026", "C19"),  # TopMetal2.res
    (134, 33): ("#ff8000", "I1"),  # TopMetal2.iprobe
    (134, 34): ("#ff8000", "I1"),  # TopMetal2.diffprb
    (9, 0): ("#e61f0d", "C3"),  # Passiv.drawing
    (9, 1): ("#e61f0d", "C3"),  # Passiv.label
    (9, 2): ("#e61f0d", "C3"),  # Passiv.pin
    (9, 3): ("#e61f0d", "C3"),  # Passiv.net
    (9, 4): ("#e61f0d", "C3"),  # Passiv.boundary
    (9, 35): ("#e61f0d", "C3"),  # Passiv.pillar
    (9, 36): ("#e61f0d", "C3"),  # Passiv.sbump
    (9, 40): ("#e61f0d", "C3"),  # Passiv.pdl
    (160, 0): ("#d9e6ff", "I1"),  # NoMetFiller.drawing
    (146, 0): ("#e61f0d", "C0"),  # ThinFilmRes.drawing
    (27, 0): ("#ffff00", "I1"),  # IND.drawing
    (27, 2): ("#ffff00", "C0"),  # IND.pin
    (27, 4): ("#ffff00", "I1"),  # IND.boundary
    (27, 25): ("#ffff00", "C0"),  # IND.text
    (39, 0): ("#5e00e6", "I1"),  # EdgeSeal.drawing
    (39, 4): ("#5e00e6", "I1"),  # EdgeSeal.boundary
    (41, 0): ("#5e00e6", "I1"),  # dfpad.drawing
    (41, 35): ("#5e00e6", "I1"),  # dfpad.pillar
    (41, 36): ("#5e00e6", "I1"),  # dfpad.sbump
    (63, 0): ("#ffffff", "I1"),  # TEXT.drawing
    (99, 0): ("#bdcccc", "C0"),  # Recog.drawing
    (99, 2): ("#bdcccc", "C0"),  # Recog.pin
    (99, 30): ("#ffff00", "I1"),  # Recog.esd
    (99, 31): ("#5e00e6", "I1"),  # Recog.diode
    (99, 32): ("#ffff00", "I1"),  # Recog.tsv
    (99, 33): ("#d9e6ff", "C0"),  # Recog.iprobe
    (99, 34): ("#d9e6ff", "C0"),  # Recog.diffprb
    (99, 35): ("#5e00e6", "I1"),  # Recog.pillar
    (99, 36): ("#5e00e6", "I1"),  # Recog.sbump
    (99, 37): ("#d9cc00", "I1"),  # Recog.otp
    (99, 38): ("#ffff00", "I1"),  # Recog.pdiode
    (99, 39): ("#268c6b", "C0"),  # Recog.mom
    (99, 100): ("#ffffcc", "I1"),  # Recog.pcm
    (16, 0): ("#ff0000", "C11"),  # DigiBnd.drawing
    (16, 10): ("#ff0000", "C11"),  # DigiBnd.drawing0
    (24, 0): ("#bf4026", "C19"),  # RES.drawing
    (24, 1): ("#bf4026", "C0"),  # RES.label
    (25, 0): ("#ffff00", "C2"),  # SRAM.drawing
    (25, 1): ("#ffff00", "C3"),  # SRAM.label
    (25, 4): ("#ffff00", "I1"),  # SRAM.boundary
    (26, 0): ("#00ffff", "C0"),  # TRANS.drawing
    (60, 0): ("#ffff00", "C11"),  # DigiSub.drawing
    (51, 0): ("#8c8ca6", "I1"),  # HeatTrans.drawing
    (52, 0): ("#8c8ca6", "I1"),  # HeatRes.drawing
    (148, 0): ("#ff0000", "C3"),  # NoRCX.drawing
    (148, 41): ("#ff0000", "C3"),  # NoRCX.m2m3
    (148, 42): ("#ff0000", "C3"),  # NoRCX.m2m4
    (148, 43): ("#ff0000", "C3"),  # NoRCX.m2m5
    (148, 44): ("#ff0000", "C3"),  # NoRCX.m2tm1
    (148, 45): ("#ff0000", "C3"),  # NoRCX.m2tm2
    (148, 46): ("#ff0000", "C3"),  # NoRCX.m3m4
    (148, 47): ("#ff0000", "C3"),  # NoRCX.m3m5
    (148, 48): ("#ff0000", "C3"),  # NoRCX.m3tm1
    (148, 49): ("#ff0000", "C3"),  # NoRCX.m3tm2
    (148, 50): ("#ff0000", "C3"),  # NoRCX.m4m5
    (148, 51): ("#ff0000", "C3"),  # NoRCX.m4tm1
    (148, 52): ("#ff0000", "C3"),  # NoRCX.m4tm2
    (148, 53): ("#ff0000", "C3"),  # NoRCX.m5tm1
    (148, 54): ("#ff0000", "C3"),  # NoRCX.m5tm2
    (148, 55): ("#ff0000", "C3"),  # NoRCX.tm1tm2
    (148, 123): ("#ff0000", "C3"),  # NoRCX.m1sub
    (148, 124): ("#ff0000", "C3"),  # NoRCX.m2sub
    (148, 125): ("#ff0000", "C3"),  # NoRCX.m3sub
    (148, 126): ("#ff0000", "C3"),  # NoRCX.m4sub
    (148, 127): ("#ff0000", "C3"),  # NoRCX.m5sub
    (148, 300): ("#ff0000", "C3"),  # NoRCX.tm1sub
    (148, 301): ("#ff0000", "C3"),  # NoRCX.tm2sub
    (3, 0): ("#268c6b", "C7"),  # BiWind.drawing
    (3, 26): ("#0000ff", "I1"),  # BiWind.OPC
    (13, 0): ("#bf4026", "C34"),  # BasPoly.drawing
    (13, 1): ("#bf4026", "C3"),  # BasPoly.label
    (13, 2): ("#bf4026", "C3"),  # BasPoly.pin
    (13, 3): ("#bf4026", "C35"),  # BasPoly.net
    (13, 4): ("#bf4026", "C3"),  # BasPoly.boundary
    (33, 0): ("#00cc66", "C3"),  # EmWind.drawing
    (33, 26): ("#ffff00", "I1"),  # EmWind.OPC
    (35, 0): ("#ff8000", "C3"),  # DeepCo.drawing
    (55, 0): ("#ffe6bf", "C3"),  # EmPoly.drawing
    (70, 0): ("#00cc66", "C3"),  # Varicap.drawing
    (90, 0): ("#00cc66", "C3"),  # EmWind3.drawing
    (91, 0): ("#00cc66", "C3"),  # EmWiHV3.drawing
    (101, 0): ("#d80000", "C36"),  # ColOpen.drawing
    (139, 0): ("#ff00ff", "C37"),  # ColWind.drawing
    (156, 0): ("#00cc66", "C3"),  # EmWiHV.drawing
    (152, 0): ("#ff8000", "I1"),  # DeepVia.drawing
    (157, 0): ("#ff00ff", "C8"),  # LBE.drawing
    (20, 0): ("#ffe6bf", "C30"),  # BackMetal1.drawing
    (20, 1): ("#ffe6bf", "C30"),  # BackMetal1.label
    (20, 2): ("#ffe6bf", "C30"),  # BackMetal1.pin
    (20, 3): ("#ffe6bf", "C30"),  # BackMetal1.net
    (20, 4): ("#ffe6bf", "I1"),  # BackMetal1.boundary
    (20, 20): ("#ffe6bf", "C30"),  # BackMetal1.mask
    (20, 22): ("#ffe6bf", "I1"),  # BackMetal1.filler
    (20, 23): ("#ffe6bf", "C30"),  # BackMetal1.nofill
    (20, 24): ("#ffe6bf", "C30"),  # BackMetal1.slit
    (20, 25): ("#39bfff", "C1"),  # BackMetal1.text
    (20, 26): ("#ffe6bf", "C30"),  # BackMetal1.OPC
    (20, 28): ("#ff0000", "C3"),  # BackMetal1.noqrc
    (20, 29): ("#bf4026", "C19"),  # BackMetal1.res
    (20, 33): ("#ffe6bf", "I1"),  # BackMetal1.iprobe
    (20, 34): ("#ffe6bf", "I1"),  # BackMetal1.diffprb
    (23, 0): ("#ffe6bf", "C30"),  # BackPassiv.drawing
    (72, 0): ("#268c6b", "C29"),  # IntBondVia.drawing
    (73, 0): ("#268c6b", "C29"),  # IntBondMet.drawing
    (74, 0): ("#5e00e6", "C30"),  # DevBondVia.drawing
    (75, 0): ("#5e00e6", "C30"),  # DevBondMet.drawing
    (76, 0): ("#ffffff", "C0"),  # DevTrench.drawing
    (77, 0): ("#ff00ff", "C0"),  # Redist.drawing
    (54, 0): ("#ffff00", "I1"),  # FBE.drawing
    (83, 0): ("#9900e6", "C38"),  # AntVia1.drawing
    (84, 0): ("#bf4026", "C39"),  # AntMetal2.drawing
    (132, 0): ("#9900e6", "C38"),  # AntMetal1.drawing
    (142, 0): ("#333399", "C0"),  # FLM.drawing
    (135, 0): ("#ff8000", "C7"),  # SNSRing.drawing
    (136, 0): ("#bdcccc", "C7"),  # Sensor.drawing
    (137, 0): ("#ff8000", "C7"),  # SNSArms.drawing
    (138, 0): ("#ff8000", "C7"),  # SNSCMOSVia.drawing
    (149, 0): ("#ccb899", "C40"),  # SNSBotVia.drawing
    (151, 0): ("#00ff00", "C40"),  # SNSTopVia.drawing
    (15, 0): ("#ffff00", "C0"),  # NLDB.drawing
    (45, 0): ("#ffff00", "C0"),  # PLDB.drawing
    (92, 0): ("#d9cc00", "C10"),  # RedBuLay.drawing
    (112, 0): ("#ffff00", "C41"),  # NLDD.drawing
    (113, 0): ("#ffff00", "C42"),  # PLDD.drawing
    (114, 0): ("#ffff00", "C43"),  # NExt.drawing
    (115, 0): ("#ffff00", "C44"),  # PExt.drawing
    (127, 0): ("#ffff00", "C41"),  # INLDPWL.drawing
    (131, 0): ("#ffff00", "C45"),  # nBuLayCut.drawing
    (78, 0): ("#9900e6", "C39"),  # GraphBot.drawing
    (79, 0): ("#ff00ff", "C46"),  # GraphTop.drawing
    (85, 0): ("#268c6b", "C29"),  # GraphCont.drawing
    (86, 0): ("#d80000", "C15"),  # SiWG.drawing
    (86, 22): ("#d80000", "C15"),  # SiWG.filler
    (86, 23): ("#d80000", "I1"),  # SiWG.nofill
    (87, 0): ("#8c8ca6", "C4"),  # SiGrating.drawing
    (88, 0): ("#008539", "C9"),  # SiNGrating.drawing
    (89, 0): ("#ff8000", "I1"),  # GraphPas.drawing
    (97, 0): ("#e61f0d", "C4"),  # GraphPad.drawing
    (109, 0): ("#00b300", "C29"),  # GraphMetal1.drawing
    (109, 22): ("#00b300", "C29"),  # GraphMetal1.filler
    (109, 23): ("#00b300", "I1"),  # GraphMetal1.nofill
    (109, 24): ("#00b300", "I1"),  # GraphMetal1.slit
    (109, 26): ("#00b300", "I1"),  # GraphMetal1.OPC
    (110, 0): ("#34b7ab", "C27"),  # GraphMet1L.drawing
    (110, 22): ("#34b7ab", "C27"),  # GraphMet1L.filler
    (110, 23): ("#34b7ab", "I1"),  # GraphMet1L.nofill
    (110, 24): ("#34b7ab", "I1"),  # GraphMet1L.slit
    (110, 26): ("#34b7ab", "I1"),  # GraphMet1L.OPC
    (118, 0): ("#ffff00", "C2"),  # GraphGate.drawing
    (119, 0): ("#ffffcc", "C15"),  # SiNWG.drawing
    (119, 22): ("#ffffcc", "C15"),  # SiNWG.filler
    (119, 23): ("#ffffcc", "I1"),  # SiNWG.nofill
    (46, 0): ("#ffff00", "C47"),  # PWell.drawing
    (46, 1): ("#ffff00", "C0"),  # PWell.label
    (46, 2): ("#ffff00", "C0"),  # PWell.pin
    (46, 3): ("#ffff00", "C47"),  # PWell.net
    (46, 4): ("#ffff00", "I1"),  # PWell.boundary
    (48, 0): ("#ffff00", "I1"),  # IC.drawing
    (62, 0): ("#ff0000", "C3"),  # NoDRC.drawing
    (68, 0): ("#ff76fb", "C0"),  # RadHard.drawing
    (69, 0): ("#ff00ff", "C48"),  # MemCap.drawing
    (93, 0): ("#ffff00", "C39"),  # SMOS.drawing
    (98, 0): ("#e61f0d", "C10"),  # Polimide.drawing
    (98, 1): ("#e61f0d", "C10"),  # Polimide.label
    (98, 2): ("#e61f0d", "C10"),  # Polimide.pin
    (98, 3): ("#e61f0d", "C10"),  # Polimide.net
    (111, 0): ("#5e00e6", "I1"),  # EXTBlock.drawing
    (116, 0): ("#ffff00", "C49"),  # NExtHV.drawing
    (117, 0): ("#ffff00", "C8"),  # PExtHV.drawing
    (124, 0): ("#ffff00", "C50"),  # MEMPAD.drawing
    (143, 0): ("#ff8000", "C7"),  # HafniumOx.drawing
    (145, 0): ("#d9cc00", "C0"),  # MEMVia.drawing
    (147, 0): ("#ff8000", "I1"),  # RFMEM.drawing
    (153, 0): ("#5e00e6", "C11"),  # FGEtch.drawing
    (154, 0): ("#ffffff", "C0"),  # CtrGat.drawing
    (155, 0): ("#d80000", "C0"),  # FGImp.drawing
    (159, 0): ("#ffffcc", "C0"),  # AlCuStop.drawing
    (189, 0): ("#9900e6", "I1"),  # prBoundary.drawing
    (189, 1): ("#9900e6", "I1"),  # prBoundary.label
    (189, 4): ("#9900e6", "I1"),  # prBoundary.boundary
    (190, 0): ("#00cc66", "C51"),  # Exchange0.drawing
    (190, 1): ("#00ff00", "C3"),  # Exchange0.label
    (190, 2): ("#00cc66", "C52"),  # Exchange0.pin
    (190, 25): ("#ccb899", "C3"),  # Exchange0.text
    (191, 0): ("#ffff00", "C42"),  # Exchange1.drawing
    (191, 1): ("#ffff00", "C3"),  # Exchange1.label
    (191, 2): ("#ffff00", "C52"),  # Exchange1.pin
    (191, 25): ("#00cc66", "C3"),  # Exchange1.text
    (192, 0): ("#ffbff2", "C43"),  # Exchange2.drawing
    (192, 1): ("#ffbff2", "C3"),  # Exchange2.label
    (192, 2): ("#ffbff2", "C52"),  # Exchange2.pin
    (192, 25): ("#ff76fb", "C3"),  # Exchange2.text
    (193, 0): ("#00ffff", "C44"),  # Exchange3.drawing
    (193, 1): ("#00ffff", "I1"),  # Exchange3.label
    (193, 2): ("#00ffff", "C53"),  # Exchange3.pin
    (193, 25): ("#ffba31", "C3"),  # Exchange3.text
    (194, 0): ("#ff8000", "C49"),  # Exchange4.drawing
    (194, 1): ("#ff8000", "I1"),  # Exchange4.label
    (194, 2): ("#ff8000", "C52"),  # Exchange4.pin
    (194, 25): ("#39bfff", "C3"),  # Exchange4.text
    (257, 0): ("#ff00ff", "I1"),  # isoNWell.drawing
}

# Layer and purpose names from sg13g2.lyp, for the layer list of the interactive window ("Metal1.drawing").
LAYER_NAMES = {
    1: "Activ", 3: "BiWind", 5: "GatPoly", 6: "Cont", 7: "nSD", 8: "Metal1", 9: "Passiv", 10: "Metal2",
    13: "BasPoly", 14: "pSD", 15: "NLDB", 16: "DigiBnd", 19: "Via1", 20: "BackMetal1", 23: "BackPassiv", 24: "RES",
    25: "SRAM", 26: "TRANS", 27: "IND", 28: "SalBlock", 29: "Via2", 30: "Metal3", 31: "NWell", 32: "nBuLay",
    33: "EmWind", 35: "DeepCo", 36: "MIM", 39: "EdgeSeal", 40: "Substrate", 41: "dfpad", 44: "ThickGateOx",
    45: "PLDB", 46: "PWell", 48: "IC", 49: "Via3", 50: "Metal4", 51: "HeatTrans", 52: "HeatRes", 54: "FBE",
    55: "EmPoly", 60: "DigiSub", 62: "NoDRC", 63: "TEXT", 66: "Via4", 67: "Metal5", 68: "RadHard", 69: "MemCap",
    70: "Varicap", 72: "IntBondVia", 73: "IntBondMet", 74: "DevBondVia", 75: "DevBondMet", 76: "DevTrench",
    77: "Redist", 78: "GraphBot", 79: "GraphTop", 83: "AntVia1", 84: "AntMetal2", 85: "GraphCont", 86: "SiWG",
    87: "SiGrating", 88: "SiNGrating", 89: "GraphPas", 90: "EmWind3", 91: "EmWiHV3", 92: "RedBuLay", 93: "SMOS",
    97: "GraphPad", 98: "Polimide", 99: "Recog", 101: "ColOpen", 109: "GraphMetal1", 110: "GraphMet1L",
    111: "EXTBlock", 112: "NLDD", 113: "PLDD", 114: "NExt", 115: "PExt", 116: "NExtHV", 117: "PExtHV",
    118: "GraphGate", 119: "SiNWG", 124: "MEMPAD", 125: "TopVia1", 126: "TopMetal1", 127: "INLDPWL", 128: "PolyRes",
    129: "Vmim", 131: "nBuLayCut", 132: "AntMetal1", 133: "TopVia2", 134: "TopMetal2", 135: "SNSRing",
    136: "Sensor", 137: "SNSArms", 138: "SNSCMOSVia", 139: "ColWind", 142: "FLM", 143: "HafniumOx", 145: "MEMVia",
    146: "ThinFilmRes", 147: "RFMEM", 148: "NoRCX", 149: "SNSBotVia", 151: "SNSTopVia", 152: "DeepVia",
    153: "FGEtch", 154: "CtrGat", 155: "FGImp", 156: "EmWiHV", 157: "LBE", 159: "AlCuStop", 160: "NoMetFiller",
    189: "prBoundary", 190: "Exchange0", 191: "Exchange1", 192: "Exchange2", 193: "Exchange3", 194: "Exchange4",
    257: "isoNWell",
}

PURPOSE_NAMES = {
    0: "drawing", 1: "label", 2: "pin", 3: "net", 4: "boundary", 10: "drawing0", 19: "lvs", 20: "mask", 21: "block",
    22: "filler", 23: "nofill", 24: "slit", 25: "text", 26: "OPC", 27: "iOPC", 28: "noqrc", 29: "res", 30: "esd",
    31: "diode", 32: "tsv", 33: "iprobe", 34: "diffprb", 35: "pillar", 36: "sbump", 37: "otp", 38: "pdiode",
    39: "mom", 40: "pdl", 41: "m2m3", 42: "m2m4", 43: "m2m5", 44: "m2tm1", 45: "m2tm2", 46: "m3m4", 47: "m3m5",
    48: "m3tm1", 49: "m3tm2", 50: "m4m5", 51: "m4tm1", 52: "m4tm2", 53: "m5tm1", 54: "m5tm2", 55: "tm1tm2",
    100: "pcm", 123: "m1sub", 124: "m2sub", 125: "m3sub", 126: "m4sub", 127: "m5sub", 300: "tm1sub", 301: "tm2sub",
}

# Exact per-pattern bitmaps for every dither-pattern name used in sg13g2.lyp.
#
# KLayout ships this technology's dither-pattern definitions internally (not in
# the .lyp file itself), keyed by names like "I1" (built-in pattern) or "C23"
# (a further pattern beyond the built-in set). There's no public API to query
# them, so they were reverse-engineered empirically: a synthetic GDS with one
# swatch per pattern name was rendered through the real, installed KLayout
# (klayout_app.exe, batch mode) with sg13g2.lyp applied, then each swatch's
# minimal repeating tile was recovered from the rendered pixels (2D period
# detection, then majority-vote over all repeats to denoise anti-aliasing).
# Each value is a list of equal-length row strings; "*" = filled, "." = empty.
# A `None` value means the pattern renders with no fill at all (outline only) -
# used by several purpose layers (labels/pins/etc.) in this technology.
PATTERN_TILES = {
    "C0": None,
    "C1": ["........*.......", ".......*........", "......*.........", ".....*..........", "....*...........", "...*............", "..*.............", ".*..............", "*...............", "...............*", "..............*.", ".............*..", "............*...", "...........*....", "..........*.....", ".........*......"],
    "C2": ["................", "*....*.......*..", ".........*......", "...*............", ".......*........", "................", "..............*.", "......*....*....", "..**............", "..........*.....", "...*.........*..", "...............*", "......*.........", "................", "..*......*......", "................"],
    "C3": [".*.*", "..*.", ".*.*", "*..."],
    "C4": ["...*....*.....*.", "....*....*....*.", "....*.....*....*", "*....*....*.....", "*.....*....*....", ".*....*.....*...", "..*....*....*...", "..*.....*....*.."],
    "C5": ["...*", "....", ".*..", "...."],
    "C6": ["*...*...*..**...", "................", "................", "................"],
    "C7": ["......*.", "......*.", "........", ".*......", ".*......", ".*......", "****...*", ".*......", ".*......", ".*......", "........", "......*.", "......*.", "......*.", "*...****", "......*."],
    "C8": ["................", "................", "................", "....*....*.....*", "*..*.*..*.*...*.", "....*....*.....*", "................", "....*...........", "....*....*.....*", "*..*.*..*.*...*.", "....*....*.....*", "................", "................", "....*....*.....*", "*..*.*..*.*...*.", "....*....*.....*"],
    "C9": [".......*", "**......", "..*.....", "...**...", ".....*..", "......**", "*.......", ".**.....", "...*....", "....**..", "......*.", "*......*", ".*......", "..**....", "....*...", ".....**."],
    "C10": [".*****..........", "*.....*.........", ".......*.......*", "........*.....*.", ".........*...*..", ".........*...*..", ".........*...*..", ".........*...*..", ".........*...*..", "........*.....*.", ".......*.......*", "*.....*.........", ".*****..........", "................", "................", "................"],
    "C11": None,
    "C12": ["................", ".*...........*.*", ".....*.*.*......", "................", "......*.*.*.....", "................", "................", "*.*...........*.", "................", ".*.*...........*", "................", "................", "......*.*.*.....", "................", ".......*.*.*....", "*...........*.*."],
    "C13": ["..*.", "..*.", "..*.", "..*."],
    "C14": [".*.*", "..*.", ".*.*", "*..."],
    "C15": ["................", "........*.......", "................", "................", "....*..........*", "................", "..........*.....", "................", "................", ".........*......", "..............*.", "....*...........", "................", "................", "................", "*..............."],
    "C16": ["...*...*........", "................", "................", "................", "................", ".........*....*.", "................", ".*..............", "................", "................", ".......*........", "................", "...............*", "................", "................", "................"],
    "C17": ["......*.........", ".....*..........", "....*...........", "...*............", "..*.............", ".*..............", "*...............", "...............*", "..............*.", ".............*..", "............*...", "...........*....", "..........*.....", ".........*......", "........*.......", ".......*........"],
    "C18": None,
    "C19": ["..*..*..*..**..*", ".*..*..*..*...*.", "*..*..*..*...*..", "..*..*..*..**..*", ".*..*..*..*...*.", "*..*..*..*...*..", "..*..*..*..**..*", ".*..*..*..*...*.", "*..*..*..*...*..", "..*..*..*..**..*", "..*..*..*..**..*", ".*..*..*..*...*.", "*..*..*..*...*..", "..*..*..*..**..*", ".*..*..*..*...*.", "*..*..*..*...*.."],
    "C20": [".............*..", "............*...", "...........*....", "..........*.....", ".........*......", "........*.......", ".......*........", "......*.........", ".....*..........", "....*...........", "...*............", "..*.............", ".*..............", "*...............", "...............*", "..............*."],
    "C21": ["...............*", "..............*.", ".............*..", "............*...", "...........*....", "..........*.....", ".........*......", "........*.......", ".......*........", "......*.........", ".....*..........", "....*...........", "...*............", "..*.............", ".*..............", "*..............."],
    "C22": ["..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............", "....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*.....", "...........*....", "............*...", ".............*.."],
    "C23": ["..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............", "....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......"],
    "C24": ["*..***..*..***..", "...*.*...*.....*", ".***.***..*...*.", ".*.....*...*.*..", "**..*..***..*..*", "...*.*...*.....*", "..*...*..***.***", ".*.....*...*.*.."],
    "C25": ["...........*....", "............*...", ".............*..", "..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............", "....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*....."],
    "C26": ["....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............"],
    "C27": ["*...............", ".*..............", "..*.............", "...*............", "....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*"],
    "C28": [".........*......", "........*.......", ".......*........", "......*.........", ".....*..........", "....*...........", "...*............", "..*.............", ".*..............", "*...............", "...............*", "..............*.", ".............*..", "............*...", "...........*....", "..........*....."],
    "C29": [".............*..", "............*...", "...........*....", "..........*.....", ".........*......", "........*.......", ".......*........", "......*.........", ".....*..........", "....*...........", "...*............", "..*.............", ".*..............", "*...............", "...............*", "..............*."],
    "C30": ["....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............"],
    "C31": [".........*......", "..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............", "....*...........", ".....*..........", "......*.........", ".......*........", "........*......."],
    "C32": [".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*", "*...............", ".*..............", "..*.............", "...*............", "....*..........."],
    "C34": [".*.....*........", "*.....*.........", ".....*.....*...*", "....*.....*...*.", "...*.....*...*..", "..*.....*...*...", ".*.....*........", "*.....*.........", ".....*.....*...*", "....*.....*...*.", "...*.....*...*..", "..*.....*...*...", ".*.....*........", "*.....*.........", ".....*.....*...*", "....*.....*...*."],
    "C35": ["*...", "....", "..*.", "...."],
    "C36": ["*...", "....", "..*.", "...."],
    "C37": [".*....*...*.....", ".......*........", ".............*..", "................", ".*...*..........", ".......*..*.....", "..............*.", "....*........*..", "..*........*....", ".*..............", "........*.....*.", "*...............", "....*...........", "......*.........", "................", "..............*."],
    "C38": ["*...............", ".*..............", "..*.............", "...*............", "....*...........", ".....*..........", "......*.........", ".......*........", "........*.......", ".........*......", "..........*.....", "...........*....", "............*...", ".............*..", "..............*.", "...............*"],
    "C39": [".......*", "*.......", ".*......", "..*.....", "...*....", "....*...", ".....*..", "......*."],
    "C40": ["................", "................", ".......*.......*", ".......*.......*", ".......*.......*", ".......*.......*", ".......*.......*", ".......*.......*", "...*...*.......*", "...*...*.......*", "...*............", "...*............", "...*............", "...*............", "...*............", "...*............"],
    "C41": ["................", "................", ".........*.....*", "................", "..*...*.........", "..*...*.........", "................", "..............*.", ".........*......", "................", "................", "...........**...", "................", "...*............", "................", "...........**..."],
    "C42": ["....*..*........", "*...............", "................", "................", "*..*............", "................", "................", "................", "......*......*..", "................", "................", "*.....*..*...*..", "................", "....*...........", "................", "................"],
    "C43": [".............*..", "........*.......", "................", "*...............", "....*...........", "................", "...........**...", "................", ".........*......", "................", "...*..........*.", "................", "......*...*.....", "................", "..*.............", "................"],
    "C44": ["....*...........", ".........*......", "................", "................", "................", ".............*..", "................", "................", "................", "................", "..........*.....", "................", "................", "................", "..............*.", "................"],
    "C45": ["................", "................", "................", ".......*........", "......*.*.......", ".....*...*......", "....*.....*.....", "...*********....", "................", "................", "................", "*...............", ".*.............*", "..*...........*.", "...*.........*..", "*****.......****"],
    "C46": [".......*", "......*.", ".....*..", "....*...", "...*....", "..*.....", ".*......", "*......."],
    "C47": ["....", "...*", "....", ".*.."],
    "C48": ["..*.............", ".*..............", "*...............", "...............*", "..............*.", ".............*..", "............*...", "...........*....", "..........*.....", ".........*......", "........*.......", ".......*........", "......*.........", ".....*..........", "....*...........", "...*............"],
    "C49": ["*.........*.....", "..............*.", ".........*......", "...*..........*.", "................", "................", "..*.....*.......", "..............*.", "................", "....*...........", "............*...", "........*.......", "..............*.", "..*.............", "................", ".....*.........."],
    "C50": [".*", ".*", ".*", ".*", "*.", "*.", "*.", "*."],
    "C51": ["........*.......", "....*.........*.", ".*.......*......", "................", ".......*...*...*", "................", "......*..*...*..", "...*............", "...........*...*", ".............*..", ".*..*...........", ".........*....*.", "...*............", "....*...*......*", "................", "................"],
    "C52": ["*......*", "*......*", ".*....*.", "..*..*..", "...**...", "...**...", "..*..*..", ".*....*."],
    "C53": ["...**...", "...**...", "..*..*..", ".*....*.", "*......*", "*......*", ".*....*.", "..*..*.."],
    "I1": None,
}

DEFAULT_COLOR = "#a0a0a0"
DEFAULT_PATTERN = None  # for layer_colors: solid fill
FULL_DEPTH = 32  # expand all reference levels instead of drawing name-labeled boxes
OUTLINE_LINEWIDTH = 0.5  # --screenshot: polygon outline width, in points

# Purpose (datatype) numbers hidden in --screenshot and switched off at first in the window, across
# every layer. Verified against LAYER_STYLES above (derived straight from
# sg13g2.lyp) rather than trusted by name alone: sibling repo gds_prepare_for_EM
# lists these same 4 purposes as [20, 22, 23, 32], but per the real .lyp, 20 is
# "mask" and 32 is a layer number (nBuLay), not a purpose - noqrc is actually 28
# and block is actually 21. The set below uses the .lyp-verified numbers.
HIDDEN_DATATYPES = {21, 22, 23, 28}  # block, filler, nofill, noqrc


def pick_cell(lib, cellname):
    """The cell to show of a gdstk library: the cell called cellname, else the top-level cell with the largest
    bounding box, never KLayout's $$$CONTEXT_INFO$$$ (or another $$$ cell). The same rule as gds2palace's
    select_design_cell() and gds_prepare_for_EM, so the viewer shows the cell that the EM tools read: keep in sync."""
    import gdstk

    cells = {c.name: c for c in lib.cells if not isinstance(c, gdstk.RawCell)}
    if cellname is not None:
        if cellname not in cells:
            sys.exit(f"Cell '{cellname}' not found. Available cells: {', '.join(sorted(cells))}")
        return cells[cellname]
    top_cells = [c for c in lib.top_level() if not isinstance(c, gdstk.RawCell) and not c.name.startswith("$$$")]
    if not top_cells:
        sys.exit("No top-level cell found in this GDS file.")

    def area(cell):
        box = cell.bounding_box()
        return 0 if box is None else (box[1][0] - box[0][0]) * (box[1][1] - box[0][1])
    return max(top_cells, key=area)


def _polygons_and_box(cell):
    """({(layer, datatype): [point arrays]}, ((x0, y0), (x1, y1))) of a cell with its whole hierarchy, paths as
    polygons. cell: a gdstk cell, or a gdspy cell (render_screenshot still takes those). Told apart by their
    methods, so neither package is imported here."""
    if hasattr(cell, "get_bounding_box"):          # gdspy
        return cell.get_polygons(by_spec=True, depth=FULL_DEPTH), cell.get_bounding_box()
    polygons_by_spec = {}
    for p in cell.get_polygons(include_paths=True):     # gdstk: flattened, all levels
        polygons_by_spec.setdefault((p.layer, p.datatype), []).append(p.points)
    return polygons_by_spec, cell.bounding_box()


def _draw_order(keys, layer_colors=None):
    """(layer, datatype) keys bottom first. SG13G2: the order of sg13g2.lyp, so layers stack as in KLayout (not in
    the GDS stream's order), unknown layers on top. With layer_colors (other technologies): unlisted layers first,
    then the listed ones in the order of the dict."""
    if layer_colors is None:
        return [k for k in LAYER_STYLES if k in keys] + [k for k in keys if k not in LAYER_STYLES]
    rank = {int(layer): i for i, layer in enumerate(layer_colors)}
    return sorted(keys, key=lambda k: (rank.get(int(k[0]), -1), k))


def _layer_style(key, layer_colors=None):
    """(color, kind, tile rows) of a layer: kind "outline" (a pattern without fill, e.g. pin and label purposes),
    "helper" (a layer without SG13G2 style, e.g. port, region or marker layers: a wider outline in DEFAULT_COLOR,
    so it doesn't hide the layers below), "solid" (all of layer_colors) or "pattern" (tile rows of PATTERN_TILES)."""
    if layer_colors is None:
        if key not in LAYER_STYLES:
            return DEFAULT_COLOR, "helper", None
        color, pattern_name = LAYER_STYLES[key]
    else:
        color, pattern_name = layer_colors.get(int(key[0]), DEFAULT_COLOR), None
    tile_rows = PATTERN_TILES.get(pattern_name) if pattern_name else None
    if pattern_name is not None and tile_rows is None and pattern_name in PATTERN_TILES:
        return color, "outline", None
    if tile_rows is None:
        return color, "solid", None
    return color, "pattern", tile_rows


def _pattern_tile(color, tile_rows, pattern_scale=1):
    """RGBA uint8 array of one pattern tile: the layer color where the pattern is set, transparent elsewhere."""
    import numpy as np

    tile = np.array([[c == "*" for c in row] for row in tile_rows], dtype=bool)
    if pattern_scale > 1:
        tile = np.kron(tile, np.ones((pattern_scale, pattern_scale), dtype=bool))
    rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
    rgba_tile = np.zeros((*tile.shape, 4), dtype=np.uint8)
    rgba_tile[tile] = (*rgb, 255)
    return rgba_tile


def _pattern_image(ax, rgba_tile, compound_path, x0, y0, out_w, out_h, px_per_um):
    """The pattern, one tile pixel per output pixel, as an image of out_w x out_h pixels from (x0, y0) up,
    clipped to the layer's shapes."""
    import numpy as np
    from matplotlib.patches import PathPatch

    th, tw = rgba_tile.shape[:2]
    big = np.tile(rgba_tile, (out_h // th + 2, out_w // tw + 2, 1))[:out_h, :out_w]
    im = ax.imshow(
        big,
        extent=(x0, x0 + out_w / px_per_um, y0, y0 + out_h / px_per_um),
        origin="upper",
        interpolation="nearest",
    )
    im.set_clip_path(PathPatch(compound_path, transform=ax.transData))
    return im


def render_screenshot(cell, output_path, background="#000000", width_px=None, labels=None,
                      outline_layers=None, layer_colors=None, pattern_scale=1, fill_alpha=None):
    """Render the cell's full geometry (no GUI window needed) and save it as PNG.
    cell: a gdstk cell (or a gdspy cell).

    Uses the exact PATTERN_TILES bitmaps, so this is a pixel-accurate
    reproduction of sg13g2.lyp's fill patterns.

    output_path: file name or binary file object.
    width_px: image width in pixels (default 2400).
    labels: optional list of (x, y, text) in layout coordinates, drawn on top
    with a marker, e.g. to show port locations.
    outline_layers: optional set of layer numbers drawn as outlines only, e.g.
    helper layers without SG13G2 style that would otherwise hide other layers.
    Layers without SG13G2 style are drawn as outlines in DEFAULT_COLOR, like
    outline_layers.
    layer_colors: optional {layer number: color} for other technologies than
    SG13G2. The SG13G2 styles are then not used: each listed layer is a solid
    fill in its color ("#rrggbb", or "#rrggbbaa" with transparency), drawn in
    the order of the dict (first = bottom); other layers are solid
    DEFAULT_COLOR, drawn first.
    pattern_scale: integer >= 1. Each pixel of the fill patterns becomes a
    pattern_scale x pattern_scale block, and outlines get pattern_scale times
    wider, so the 1-pixel pattern lines stay visible when the image is shown
    smaller than it was rendered. 1 (default) is the exact KLayout look.
    fill_alpha: optional 0..1. Adds a solid fill in the layer color with this
    opacity under each fill pattern, so that metal areas stay visible when the
    image is shown small. None (default) is the exact KLayout look.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    polygons_by_spec, ((x0, y0), (x1, y1)) = _polygons_and_box(cell)
    width, height = x1 - x0, y1 - y0
    # figure with the layout's own aspect ratio, so there are no empty bands
    # around it; very tall layouts get a narrower figure instead of a taller one
    fig_width = 12.0
    fig_height = fig_width * height / width
    if fig_height > 20.0:
        fig_width, fig_height = fig_width * 20.0 / fig_height, 20.0
    fig_height = max(fig_height, 0.5)
    dpi = 200 * 12.0 / fig_width if width_px is None else width_px / fig_width

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=background)
    ax.set_facecolor(background)

    # Texture resolution matched to the final output resolution (not a fixed
    # px/um): a fixed density blows up to a huge array for PCB-scale designs
    # (millimeters, not microns) and wastes memory on chip-scale ones.
    px_per_um = (fig_width * dpi) / width

    for key in _draw_order(polygons_by_spec, layer_colors):
        if layer_colors is None and key[1] in HIDDEN_DATATYPES:
            continue
        color, kind, tile_rows = _layer_style(key, layer_colors)
        compound_path = Path.make_compound_path(*(Path(p) for p in polygons_by_spec[key]))
        linewidth = OUTLINE_LINEWIDTH * pattern_scale

        if kind == "outline":
            ax.add_patch(PathPatch(compound_path, facecolor="none", edgecolor=color, linewidth=linewidth))
            continue
        if kind == "helper" or key[0] in (outline_layers or ()):
            ax.add_patch(PathPatch(compound_path, facecolor="none", edgecolor=color, linewidth=2 * linewidth))
            continue
        if kind == "solid":
            ax.add_patch(PathPatch(compound_path, facecolor=color, edgecolor=color, linewidth=linewidth))
            continue

        if fill_alpha:
            # zorder 0 like the pattern image (patches default to 1): drawn just below its own pattern
            ax.add_patch(PathPatch(compound_path, facecolor=color, edgecolor="none", alpha=fill_alpha, zorder=0))
        verts = compound_path.vertices
        bx0, by0 = verts.min(axis=0)
        bx1, by1 = verts.max(axis=0)
        _pattern_image(ax, _pattern_tile(color, tile_rows, pattern_scale), compound_path, bx0, by0,
                       max(1, int((bx1 - bx0) * px_per_um)), max(1, int((by1 - by0) * px_per_um)), px_per_um)
        ax.add_patch(PathPatch(compound_path, facecolor="none", edgecolor=color, linewidth=linewidth))

    import matplotlib.patheffects as patheffects

    # label size follows the image size (text about 3 % of the image width, at least
    # 14 px), so labels stay readable when the PNG is shown smaller than it is
    text_px = max(14.0, 0.03 * fig_width * dpi)
    pt = 72.0 / dpi   # points per pixel
    outline = [patheffects.withStroke(linewidth=0.25 * text_px * pt, foreground="black")]
    cx = (x0 + x1) / 2
    edge = text_px / px_per_um   # text height in layout units
    for x, y, text in labels or []:
        ax.plot(x, y, marker="o", markersize=0.5 * text_px * pt, markerfacecolor="none",
                markeredgecolor="white", markeredgewidth=0.12 * text_px * pt, path_effects=outline)
        # text beside the marker, on the side toward the layout center, so labels of ports at
        # the edge stay inside the image; vertically centered (labels of ports above each other
        # don't collide), except within one text height of the top/bottom edge
        dx = 0.5 * text_px * pt * (1 if x <= cx else -1)
        va = "top" if y > y1 - edge else "bottom" if y < y0 + edge else "center"
        ax.annotate(text, (x, y), xytext=(dx, 0), textcoords="offset points", color="white",
                    fontsize=text_px * pt, fontweight="bold", path_effects=outline,
                    ha="left" if x <= cx else "right", va=va)

    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0)
    fig.savefig(output_path, facecolor=background, dpi=dpi)
    plt.close(fig)


def layer_label(key):
    """Name of a (layer, datatype) in the layer list, e.g. "Metal1.drawing 8/0"; numbers only for unknown ones."""
    layer, datatype = key
    name = LAYER_NAMES.get(layer)
    if name is None:
        return f"{layer}/{datatype}"
    return f"{name}.{PURPOSE_NAMES.get(datatype, datatype)} {layer}/{datatype}"


def _quiet_aspect_warning():
    """matplotlib logs "Ignoring fixed x limits to fulfill fixed data aspect ..." whenever a zoom range is widened to
    the window's shape: intended in LayoutWindow, so not shown."""
    import logging

    logger = logging.getLogger("matplotlib.axes._base")
    if not any(getattr(f, "_gds_viewer", False) for f in logger.filters):
        def keep(record):
            return "to fulfill fixed data aspect" not in record.getMessage()
        keep._gds_viewer = True
        logger.addFilter(keep)


class LayoutWindow:
    """Interactive matplotlib window of a gdstk cell with its whole hierarchy, in the sg13g2.lyp colors and the
    exact fill patterns of render_screenshot().

    Pan and zoom with matplotlib's toolbar (or keys p and o, h for the whole layout, scroll wheel zooms at the
    cursor), the cursor position in um at the bottom. The layer list on the right switches layers on and off;
    purposes in HIDDEN_DATATYPES (block, filler, nofill, noqrc) start off. GDS texts are shown with their layer.

    The fill patterns are redrawn after each pan or zoom, at the screen's resolution, so they keep their
    KLayout look at every zoom level.
    """

    LIST_WIDTH = 0.22          # part of the window width taken by the layer list
    REDRAW_DELAY_MS = 150      # patterns are redrawn this long after the last pan/zoom step

    def __init__(self, cell, background="#000000", title=None):
        import matplotlib.pyplot as plt
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch
        from matplotlib.widgets import CheckButtons

        polygons_by_spec, box = _polygons_and_box(cell)
        texts = {}
        for label in cell.get_labels():
            texts.setdefault((label.layer, label.texttype), []).append(label)
        if box is None:
            raise ValueError(f"cell {cell.name} has no shapes")
        (x0, y0), (x1, y1) = box

        self.fig = fig = plt.figure(figsize=(13, 8), facecolor=background)
        if fig.canvas.manager is not None:
            fig.canvas.manager.set_window_title(title or f"gds_viewer: {cell.name}")
        self.ax = ax = fig.add_axes((0.0, 0.0, 1.0 - self.LIST_WIDTH, 1.0))
        ax.set_facecolor(background)
        # equal scales by widening the shown range, not by shrinking the drawing area: a zoom box of another shape
        # than the window would otherwise leave black bands beside a narrow drawing
        ax.set_aspect("equal", adjustable="datalim")
        _quiet_aspect_warning()
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.format_coord = lambda x, y: f"x = {x:.3f} um   y = {y:.3f} um"

        self.layers = {}       # (layer, datatype) -> dict of its style and artists
        text_size = 8
        for key in _draw_order(set(polygons_by_spec) | set(texts)):
            color, kind, tile_rows = _layer_style(key)
            entry = {"color": color, "artists": [], "path": None, "tile": None, "image": None,
                     "visible": key[1] not in HIDDEN_DATATYPES}
            if key in polygons_by_spec:
                path = Path.make_compound_path(*(Path(p) for p in polygons_by_spec[key]))
                width = OUTLINE_LINEWIDTH * (2 if kind == "helper" else 1)
                entry["artists"].append(ax.add_patch(PathPatch(path, facecolor="none", edgecolor=color,
                                                               linewidth=width)))
                if kind == "pattern":
                    entry["path"], entry["tile"] = path, _pattern_tile(color, tile_rows)
                    verts = path.vertices
                    entry["bounds"] = (*verts.min(axis=0), *verts.max(axis=0))
            for label in texts.get(key, ()):
                entry["artists"].append(ax.text(*label.origin, label.text, color=color, fontsize=text_size,
                                                ha="center", va="center", clip_on=True))
            for artist in entry["artists"]:
                artist.set_visible(entry["visible"])
            self.layers[key] = entry

        pad = 0.02 * max(x1 - x0, y1 - y0)
        ax.set_xlim(x0 - pad, x1 + pad)
        ax.set_ylim(y0 - pad, y1 + pad)

        # the layer list: one check box per layer, in the layer's color, top = drawn last (as in KLayout's list)
        keys = list(reversed(list(self.layers)))
        self.list_ax = fig.add_axes((1.0 - self.LIST_WIDTH, 0.0, self.LIST_WIDTH, 1.0))
        self.list_ax.set_facecolor("#1e1e1e")
        colors = [self.layers[k]["color"] for k in keys]
        size = max(5.0, min(9.0, 520.0 / max(1, len(keys))))
        self.checks = CheckButtons(
            self.list_ax, [layer_label(k) for k in keys], [self.layers[k]["visible"] for k in keys],
            label_props={"color": colors, "fontsize": [size] * len(keys)},
            frame_props={"edgecolor": colors, "facecolor": "none"},
            check_props={"facecolor": colors},
        )
        self._keys_in_list = keys
        self.checks.on_clicked(self._on_check)

        self._drawn_view = None    # (x limits, y limits, axes size in pixels) the patterns were last drawn for
        self._timer = fig.canvas.new_timer(interval=self.REDRAW_DELAY_MS)
        self._timer.single_shot = True
        self._timer.add_callback(self._redraw_patterns)
        ax.callbacks.connect("xlim_changed", self._schedule)
        ax.callbacks.connect("ylim_changed", self._schedule)
        fig.canvas.mpl_connect("resize_event", self._schedule)
        fig.canvas.mpl_connect("scroll_event", self._on_scroll)
        self._redraw_patterns()

    def set_visible(self, key, visible):
        """Show or hide one (layer, datatype)."""
        entry = self.layers[key]
        entry["visible"] = visible
        for artist in entry["artists"]:
            artist.set_visible(visible)
        self._redraw_patterns()

    def _on_check(self, label):
        index = [t.get_text() for t in self.checks.labels].index(label)
        key = self._keys_in_list[index]
        self.set_visible(key, not self.layers[key]["visible"])

    def _on_scroll(self, event):
        """Zoom by 1.25 per wheel step around the cursor."""
        if event.inaxes is not self.ax or event.xdata is None:
            return
        factor = 1 / 1.25 if event.button == "up" else 1.25
        (vx0, vx1), (vy0, vy1) = self.ax.get_xlim(), self.ax.get_ylim()
        x, y = event.xdata, event.ydata
        self.ax.set_xlim(x - (x - vx0) * factor, x + (vx1 - x) * factor)
        self.ax.set_ylim(y - (y - vy0) * factor, y + (vy1 - y) * factor)
        self.fig.canvas.draw_idle()

    def _view(self):
        extent = self.ax.get_window_extent()
        return self.ax.get_xlim(), self.ax.get_ylim(), (round(extent.width), round(extent.height))

    def _schedule(self, *_):
        # drawing applies the equal aspect, which sets the limits again (unchanged once the patterns match them):
        # no redraw then, or each redraw would start the next one
        if self._view() == self._drawn_view:
            return
        self._timer.stop()
        self._timer.start()

    def _redraw_patterns(self):
        """Pattern images of the visible pattern layers for the current view: one tile pixel per screen pixel,
        only over the part of the layer in view, tiles anchored to the layout grid so they don't move when
        panning."""
        import math

        self.ax.apply_aspect()     # the range that will be shown: widened to the window's shape
        (vx0, vx1), (vy0, vy1) = self.ax.get_xlim(), self.ax.get_ylim()
        extent = self.ax.get_window_extent()
        if vx1 <= vx0 or vy1 <= vy0 or extent.width <= 0 or extent.height <= 0:
            return
        px_per_um = min(extent.width / (vx1 - vx0), extent.height / (vy1 - vy0))
        for entry in self.layers.values():
            if entry["image"] is not None:
                entry["image"].remove()
                entry["image"] = None
            if entry["tile"] is None or not entry["visible"]:
                continue
            bx0, by0, bx1, by1 = entry["bounds"]
            ix0, iy0, ix1, iy1 = max(bx0, vx0), max(by0, vy0), min(bx1, vx1), min(by1, vy1)
            if ix1 <= ix0 or iy1 <= iy0:
                continue
            th, tw = entry["tile"].shape[:2]
            # start on a tile boundary of the layout grid, and whole tiles, so the pattern stays in place
            ix0 = math.floor(ix0 * px_per_um / tw) * tw / px_per_um
            iy0 = math.floor(iy0 * px_per_um / th) * th / px_per_um
            out_w = math.ceil((ix1 - ix0) * px_per_um / tw) * tw
            out_h = math.ceil((iy1 - iy0) * px_per_um / th) * th
            entry["image"] = _pattern_image(self.ax, entry["tile"], entry["path"], ix0, iy0, out_w, out_h,
                                            px_per_um)
        # images were added after the patches; keep the view the user chose (imshow would autoscale)
        self.ax.set_xlim(vx0, vx1, emit=False)
        self.ax.set_ylim(vy0, vy1, emit=False)
        self._drawn_view = self._view()
        self.fig.canvas.draw_idle()


def show_window(cell, background="#000000"):
    """Open the interactive window of a gdstk cell and wait until it is closed."""
    import matplotlib.pyplot as plt

    window = LayoutWindow(cell, background=background)
    plt.show()
    return window


def main():
    parser = argparse.ArgumentParser(
        description="View a GDSII layout with IHP SG13G2 (sg13g2.lyp) layer colors."
    )
    parser.add_argument("gds_file", help="input GDSII file")
    parser.add_argument(
        "--cellname",
        help="cell to display (default: the largest top-level cell, as gds2palace and gds_prepare_for_EM take)",
    )
    parser.add_argument(
        "--screenshot",
        metavar="FILE.png",
        help="save the layout as a PNG to FILE.png instead of opening the window",
    )
    parser.add_argument(
        "--width", type=int, default=None, metavar="PIXELS",
        help="width of the --screenshot PNG in pixels (default 2400)",
    )
    parser.add_argument(
        "--pattern-scale", type=int, default=1, metavar="N",
        help="draw fill pattern pixels as NxN blocks and outlines N times wider in the --screenshot "
             "PNG, so patterns stay visible when the image is shown small (default 1: exact KLayout look)",
    )
    parser.add_argument(
        "--fill-alpha", type=float, default=None, metavar="0..1",
        help="add a solid fill with this opacity under the fill patterns of the --screenshot PNG, "
             "so metal stays visible when the image is shown small (default: exact KLayout look)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    import gdstk

    lib = gdstk.read_gds(args.gds_file)
    cell = pick_cell(lib, args.cellname)
    print(f"Displaying cell '{cell.name}' from {args.gds_file}")

    if args.screenshot:
        render_screenshot(cell, args.screenshot, width_px=args.width, pattern_scale=max(1, args.pattern_scale),
                          fill_alpha=args.fill_alpha)
        print(f"Saved screenshot to {args.screenshot}")
        return

    show_window(cell)


if __name__ == "__main__":
    main()
