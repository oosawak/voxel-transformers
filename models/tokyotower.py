import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (234, 72, 34, 255),    # Iconic International Orange / Vermilion Red (Shu-iro)
    2: (176, 42, 22, 255),    # Deep Vermilion Steel Shading
    3: (244, 246, 250, 255),  # Crisp Aviation White Bands
    4: (184, 192, 206, 255),  # Light Grey Steel Truss Highlight
    5: (44, 48, 58, 255),     # Dark Charcoal Structural Shadow / Joints
    6: (36, 56, 82, 255),     # Deep Blue-Grey Observation Deck Glass
    7: (64, 230, 248, 255),   # Glowing Cyan Window Glint & Visor
    8: (255, 212, 86, 255),   # Warm Golden-Yellow Tower Illumination Lights
    9: (255, 42, 48, 255),    # Bright Red Aircraft Warning Beacon Tip
}


def fill_box(grid, x0, x1, y0, y1, z0, z1, col):
    """Fill a box inclusively in (x, y, z) coordinates."""
    X, Y, Z = grid.shape
    x0, x1 = max(0, min(x0, x1)), min(X - 1, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(Y - 1, max(y0, y1))
    z0, z1 = max(0, min(z0, z1)), min(Z - 1, max(z0, z1))
    grid[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1] = col


def fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, col):
    """Fill symmetrically around X center."""
    X = grid.shape[0]
    cx_l = X // 2 - 1
    cx_r = X // 2
    fill_box(grid, cx_l - x_off1, cx_l - x_off0, y0, y1, z0, z1, col)
    fill_box(grid, cx_r + x_off0, cx_r + x_off1, y0, y1, z0, z1, col)


def fill_4sym(grid, x_off0, x_off1, y_off0, y_off1, z0, z1, col):
    """Fill symmetrically in all 4 quadrants around (X//2, Y//2)."""
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2
    for x_rng in ((cx_l - x_off1, cx_l - x_off0), (cx_r + x_off0, cx_r + x_off1)):
        for y_rng in ((cy_l - y_off1, cy_l - y_off0), (cy_r + y_off0, cy_r + y_off1)):
            fill_box(grid, x_rng[0], x_rng[1], y_rng[0], y_rng[1], z0, z1, col)


def fill_ring(grid, r, z, col, thickness=1):
    """Fill a square hollow perimeter ring at radius r around (X//2, Y//2)."""
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2
    x0, x1 = cx_l - r, cx_r + r
    y0, y1 = cy_l - r, cy_r + r
    fill_box(grid, x0, x1, y0, y0 + thickness - 1, z, z, col)
    fill_box(grid, x0, x1, y1 - thickness + 1, y1, z, z, col)
    fill_box(grid, x0, x0 + thickness - 1, y0, y1, z, z, col)
    fill_box(grid, x1 - thickness + 1, x1, y0, y1, z, z, col)


# ==========================================
# FORM A: TOKYO TOWER (26 x 26 x 56)
# ==========================================
def build_a():
    grid = np.zeros((26, 26, 56), dtype=np.uint8)
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2

    # --- 1. FOUR SPLAYED ARCHED STEEL-LATTICE LEGS (Z: 0..20) ---
    # Concrete/steel corner footings at ground level (Z: 0..1)
    fill_4sym(grid, 8, 10, 8, 10, 0, 1, 5)
    fill_4sym(grid, 8, 10, 8, 10, 1, 1, 4)
    fill_4sym(grid, 8, 9, 8, 9, 1, 1, 1)

    # Graceful upward-sweeping parabolic curve for the 4 steel-lattice corner legs
    # (Band 1: Iconic International Orange Z=2..14, Band 2: Aviation White Z=15..19)
    leg_curve = [
        (0, 9), (1, 9),
        (2, 8), (3, 8), (4, 8),
        (5, 7), (6, 7), (7, 7),
        (8, 6), (9, 6), (10, 6), (11, 6),
        (12, 5), (13, 5), (14, 5),
        (15, 4), (16, 4), (17, 4), (18, 4), (19, 4),
    ]
    for z, r in leg_curve:
        main_col = 1 if z <= 14 else 3
        shade_col = 2 if z <= 14 else 4
        # 2x2 sturdy corner truss leg (overlapping r-1..r guarantees 6-connectivity across every step!)
        if z >= 2:
            fill_4sym(grid, r - 1, r, r - 1, r, z, z, main_col)
            # Inner shaded edge of each steel leg for truss depth
            fill_4sym(grid, r - 1, r - 1, r - 1, r - 1, z, z, shade_col)
            # Bridge step seamlessly when r shrinks from previous layer
            if z in (2, 5, 8, 12, 15):
                fill_4sym(grid, r, r + 1, r, r + 1, z - 1, z - 1, main_col)

    # Iconic Openwork Arch Bridge connecting the 4 legs (Z: 6..10)
    # High graceful arch opening underneath (Z=0..5 completely open!)
    arch_profile = [
        # (z, r_face, open_half_span)
        (6, 7, 5),
        (7, 7, 4),
        (8, 6, 2),
        (9, 6, 1),
        (10, 6, -1),  # Full horizontal tie-beam across arch crown!
    ]
    for z, r, open_span in arch_profile:
        col = 1
        for d in range(0, r):
            if d > open_span:
                # Front/Back arches
                fill_sym_box(grid, d, d, cy_r + r, cy_r + r, z, z, col)
                fill_sym_box(grid, d, d, cy_l - r, cy_l - r, z, z, col)
                # Left/Right arches
                fill_box(grid, cx_l - r, cx_l - r, cy_l - d, cy_l - d, z, z, col)
                fill_box(grid, cx_l - r, cx_l - r, cy_r + d, cy_r + d, z, z, col)
                fill_box(grid, cx_r + r, cx_r + r, cy_l - d, cy_l - d, z, z, col)
                fill_box(grid, cx_r + r, cx_r + r, cy_r + d, cy_r + d, z, z, col)
        # Warm golden illumination dots along the arch inner curve!
        if 0 <= open_span + 1 < r:
            gd = open_span + 1
            fill_sym_box(grid, gd, gd, cy_r + r, cy_r + r, z, z, 8)
            fill_sym_box(grid, gd, gd, cy_l - r, cy_l - r, z, z, 8)
            grid[cx_l - r, cy_l - gd, z] = 8
            grid[cx_l - r, cy_r + gd, z] = 8
            grid[cx_r + r, cy_l - gd, z] = 8
            grid[cx_r + r, cy_r + gd, z] = 8

    # Openwork X-brace steel truss panels between arch crown and Main Deck (Z: 11..19)
    # Horizontal tie-rings at Z=12, 15, 19 + crisp openwork diagonal lattice struts
    fill_ring(grid, 5, 12, 2, thickness=1)
    fill_ring(grid, 5, 14, 1, thickness=1)
    fill_ring(grid, 4, 15, 3, thickness=1)
    fill_ring(grid, 4, 19, 3, thickness=1)
    # Open lattice X-diagonal ribs on all 4 faces (6-connected with crisp airy truss openings!)
    for z, r, c_brace, offsets in [
        (11, 6, 2, [0, 2]),
        (13, 5, 2, [0, 2]),
        (16, 4, 4, [1, 2]),
        (17, 4, 3, [0, 1]),
        (18, 4, 4, [1, 2]),
    ]:
        for d in offsets:
            if d < r:
                fill_sym_box(grid, d, d, cy_r + r, cy_r + r, z, z, c_brace)
                fill_sym_box(grid, d, d, cy_l - r, cy_l - r, z, z, c_brace)
                grid[cx_l - r, cy_l - d, z] = c_brace
                grid[cx_l - r, cy_r + d, z] = c_brace
                grid[cx_r + r, cy_l - d, z] = c_brace
                grid[cx_r + r, cy_r + d, z] = c_brace
    # Slim central steel elevator shaft core (2x2, leaving airy truss space around it!)
    fill_4sym(grid, 0, 0, 0, 0, 10, 19, 5)
    # Connect slim elevator shaft to outer tie rings at Z=10, 15, 19
    for z, r, c in ((10, 6, 2), (15, 4, 4)):
        fill_sym_box(grid, 0, r, cy_l, cy_r, z, z, c)
        fill_box(grid, cx_l, cx_r, cy_l - r, cy_r + r, z, z, c)

    # --- 2. MAIN OBSERVATION DECK (DAI-TENBODAI) (Z: 20..24) ---
    # Prominent cantilevered square observatory (r=5, 12x12)
    fill_ring(grid, 5, 20, 4, thickness=2)       # Cantilevered steel underside deck
    fill_ring(grid, 5, 21, 3, thickness=1)       # Crisp aviation white lower deck fascia
    fill_ring(grid, 5, 22, 6, thickness=1)       # Panoramic deep blue-grey glass windows!
    fill_ring(grid, 5, 23, 6, thickness=1)       # Upper panoramic glass tier
    fill_ring(grid, 5, 24, 3, thickness=2)       # Crisp white upper observatory roof deck
    fill_ring(grid, 4, 24, 1, thickness=1)       # Inner vermilion collar transitioning to upper shaft
    # Vermilion structural corner piers framing the observation deck
    fill_4sym(grid, 5, 5, 5, 5, 20, 24, 1)
    # Glowing cyan glass window glints & warm golden landmark illumination lights!
    for d in (1, 3):
        fill_sym_box(grid, d, d, cy_r + 5, cy_r + 5, 22, 22, 7)
        fill_sym_box(grid, d, d, cy_l - 5, cy_l - 5, 22, 22, 7)
        grid[cx_l - 5, cy_l - d, 22] = 7
        grid[cx_l - 5, cy_r + d, 22] = 7
        grid[cx_r + 5, cy_l - d, 22] = 7
        grid[cx_r + 5, cy_r + d, 22] = 7
    for d in (0, 2, 4):
        fill_sym_box(grid, d, d, cy_r + 5, cy_r + 5, 21, 21, 8)
        fill_sym_box(grid, d, d, cy_l - 5, cy_l - 5, 21, 21, 8)
        grid[cx_l - 5, cy_l - d, 21] = 8
        grid[cx_l - 5, cy_r + d, 21] = 8
        grid[cx_r + 5, cy_l - d, 21] = 8
        grid[cx_r + 5, cy_r + d, 21] = 8
    # Floor bridge at Z=20 & roof bridge at Z=24 connecting outer deck solidly to central shaft
    fill_sym_box(grid, 0, 5, cy_l, cy_r, 20, 20, 5)
    fill_box(grid, cx_l, cx_r, cy_l - 5, cy_r + 5, 20, 20, 5)
    fill_sym_box(grid, 0, 4, cy_l, cy_r, 24, 24, 4)
    fill_box(grid, cx_l, cx_r, cy_l - 4, cy_r + 4, 24, 24, 4)

    # --- 3. UPPER STEEL-LATTICE SHAFT (Z: 25..36) ---
    # Band 3: Iconic International Orange (Z: 25..30, r=3 -> 8x8 openwork truss)
    for z in range(25, 31):
        fill_4sym(grid, 2, 3, 2, 3, z, z, 1)     # 4 corner steel truss columns
        fill_4sym(grid, 2, 2, 2, 2, z, z, 2)     # Shaded inner steel strut
    fill_ring(grid, 3, 25, 1, thickness=1)
    fill_ring(grid, 3, 28, 1, thickness=1)
    fill_ring(grid, 3, 30, 2, thickness=1)
    # Open X-brace crossbars on Band 3
    for z in (26, 27, 29):
        d = 1 if z % 2 == 0 else 0
        fill_sym_box(grid, d, d, cy_r + 3, cy_r + 3, z, z, 2)
        fill_sym_box(grid, d, d, cy_l - 3, cy_l - 3, z, z, 2)
        grid[cx_l - 3, cy_l - d, z] = 2
        grid[cx_l - 3, cy_r + d, z] = 2
        grid[cx_r + 3, cy_l - d, z] = 2
        grid[cx_r + 3, cy_r + d, z] = 2
    # Warm golden upward uplights on Band 3 corners
    fill_4sym(grid, 3, 3, 3, 3, 28, 28, 8)

    # Band 4: Crisp Aviation White (Z: 31..36, r=2 -> 6x6 openwork truss)
    for z in range(31, 37):
        fill_4sym(grid, 2, 2, 2, 2, z, z, 3)     # 4 crisp white corner struts
    fill_ring(grid, 2, 31, 3, thickness=1)
    fill_ring(grid, 2, 34, 3, thickness=1)
    fill_ring(grid, 2, 36, 4, thickness=1)
    for z in (32, 33, 35):
        d = 0 if z % 2 == 0 else 1
        fill_sym_box(grid, d, d, cy_r + 2, cy_r + 2, z, z, 4)
        fill_sym_box(grid, d, d, cy_l - 2, cy_l - 2, z, z, 4)
        grid[cx_l - 2, cy_l - d, z] = 4
        grid[cx_l - 2, cy_r + d, z] = 4
        grid[cx_r + 2, cy_l - d, z] = 4
        grid[cx_r + 2, cy_r + d, z] = 4

    # --- 4. TOP OBSERVATION DECK (TOKUBETSU-TENBODAI) (Z: 37..40) ---
    # Band 5: Vermilion-framed Upper Observatory (r=3 -> 8x8)
    fill_ring(grid, 3, 37, 1, thickness=2)       # Vermilion support deck
    fill_ring(grid, 3, 38, 6, thickness=1)       # Blue-grey observatory windows
    fill_ring(grid, 3, 39, 6, thickness=1)
    fill_ring(grid, 3, 40, 1, thickness=2)       # Vermilion top observatory roof
    fill_4sym(grid, 3, 3, 3, 3, 37, 40, 1)       # Vermilion corner pillars
    # Cyan window glints & golden top-deck beacon lights
    fill_sym_box(grid, 1, 1, cy_r + 3, cy_r + 3, 38, 38, 7)
    fill_sym_box(grid, 1, 1, cy_l - 3, cy_l - 3, 38, 38, 7)
    grid[cx_l - 3, cy_l - 1, 38] = 7
    grid[cx_l - 3, cy_r + 1, 38] = 7
    grid[cx_r + 3, cy_l - 1, 38] = 7
    grid[cx_r + 3, cy_r + 1, 38] = 7
    fill_4sym(grid, 3, 3, 3, 3, 40, 40, 8)
    # Solid deck cap connecting to antenna spire base
    fill_4sym(grid, 0, 2, 0, 2, 40, 40, 1)

    # --- 5. TALL STRIPED ANTENNA SPIRE (SENTO) (Z: 41..55) ---
    # Band 5 continued: Vermilion tapered spire collar (Z: 41..43, 4x4)
    fill_4sym(grid, 0, 1, 0, 1, 41, 43, 1)
    fill_4sym(grid, 0, 0, 0, 0, 41, 42, 2)
    # Band 6: Crisp Aviation White Antenna Spire (Z: 44..48)
    fill_4sym(grid, 0, 1, 0, 1, 44, 45, 3)
    fill_4sym(grid, 0, 0, 0, 0, 46, 48, 3)
    # White broadcast antenna cross-arrays at Z=46
    fill_sym_box(grid, 1, 1, cy_l, cy_r, 46, 46, 4)
    fill_box(grid, cx_l, cx_r, cy_l - 1, cy_r + 1, 46, 46, 4)
    # Band 7: Vivid International Orange Upper Antenna Spire (Z: 49..53)
    fill_4sym(grid, 0, 0, 0, 0, 49, 53, 1)
    # Compact upper transmitter array cross-fins at Z=50
    fill_sym_box(grid, 1, 1, cy_l, cy_r, 50, 50, 2)
    fill_box(grid, cx_l, cx_r, cy_l - 1, cy_r + 1, 50, 50, 2)
    # Bright Red Aircraft Warning Beacon Tip (Z: 54..55)
    fill_4sym(grid, 0, 0, 0, 0, 54, 55, 9)

    return grid


# ==========================================
# FORM B: TOKYO TOWER ROBOT (36 x 22 x 52)
# ==========================================
def build_b():
    grid = np.zeros((36, 22, 52), dtype=np.uint8)
    X = grid.shape[0]
    cx_l, cx_r = X // 2 - 1, X // 2

    # --- 1. FEET / SPLAYED STEEL-FOOTING BOOTS (Z: 0..3) ---
    # Heavy dark-steel tower footings (x_off: 3..7)
    fill_sym_box(grid, 3, 7, 7, 16, 0, 1, 5)
    fill_sym_box(grid, 4, 6, 16, 17, 0, 1, 4)    # Steel toe pads
    fill_sym_box(grid, 4, 6, 7, 8, 0, 2, 4)      # Heel stabilizers
    # Vivid Vermilion splayed arched boot armor (Z: 2..3)
    fill_sym_box(grid, 3, 7, 8, 15, 2, 3, 1)
    fill_sym_box(grid, 4, 6, 15, 16, 2, 2, 1)
    fill_sym_box(grid, 5, 5, 15, 16, 2, 2, 8)    # Golden illumination toe light
    fill_sym_box(grid, 3, 7, 9, 14, 3, 3, 2)

    # --- 2. LOWER LEGS / SHINS (Z: 4..15) - ICONIC VERMILION STEEL-TRUSS LEGS! ---
    # Directly preserves Tokyo Tower's splayed vermilion openwork steel-lattice legs!
    # Inner dark-charcoal mechanical hydraulic leg core (recessed so outer steel truss reads as openwork!)
    fill_sym_box(grid, 4, 5, 10, 12, 4, 14, 5)
    # 4 Vivid Vermilion corner steel-truss columns wrapping each leg (x_off: 3..7 -> 3..6)
    for z in range(4, 15):
        ox = 7 if z <= 8 else 6
        # Four vertical corner struts of each leg's steel lattice
        for dx in (3, ox):
            for y in (9, 13):
                grid[cx_l - dx, y, z] = 1
                grid[cx_r + dx, y, z] = 1
        # Horizontal truss tie-rings at Z=4, 7, 10, 13
        if z in (4, 7, 10, 13):
            col_ring = 1 if z <= 10 else 3       # Aviation white band right below knee!
            fill_sym_box(grid, 3, ox, 9, 9, z, z, col_ring)
            fill_sym_box(grid, 3, ox, 13, 13, z, z, col_ring)
            fill_sym_box(grid, 3, 3, 9, 13, z, z, col_ring)
            fill_sym_box(grid, ox, ox, 9, 13, z, z, col_ring)
        else:
            # Openwork X-brace diagonal truss struts on front, back, and outer calf!
            c_br = 2 if z <= 11 else 4
            bx = 4 + (z % 2) if ox == 6 else 4 + (z % 3)
            bx = min(bx, ox - 1)
            fill_sym_box(grid, bx, bx, 13, 13, z, z, c_br)
            fill_sym_box(grid, bx, bx, 9, 9, z, z, c_br)
            by = 10 + (z % 3)
            grid[cx_l - ox, by, z] = c_br
            grid[cx_r + ox, by, z] = c_br
            grid[cx_l - 3, by, z] = c_br
            grid[cx_r + 3, by, z] = c_br
    # Flared outer vermilion arch-skirt fin on lower calf (echoing tower base arch!)
    fill_sym_box(grid, 7, 8, 10, 12, 4, 7, 1)
    fill_sym_box(grid, 8, 8, 11, 11, 4, 6, 2)
    fill_sym_box(grid, 7, 7, 13, 13, 6, 6, 8)    # Golden tower uplight dot on calf
    # Aviation White & Vermilion Armored Knee Guards (Z: 13..16)
    fill_sym_box(grid, 3, 6, 13, 15, 13, 15, 3)  # Crisp white aviation band knee!
    fill_sym_box(grid, 4, 5, 15, 15, 14, 16, 1)  # Vermilion knee crest
    fill_sym_box(grid, 4, 5, 15, 15, 13, 13, 8)  # Warm golden knee light
    fill_sym_box(grid, 3, 6, 9, 13, 14, 14, 3)

    # --- 3. THIGHS (Z: 16..20) - White & Vermilion Banded Truss ---
    fill_sym_box(grid, 3, 5, 9, 13, 16, 20, 5)   # Dark charcoal frame
    fill_sym_box(grid, 3, 5, 12, 13, 16, 19, 3)  # Crisp aviation white thigh plates
    fill_sym_box(grid, 5, 5, 10, 12, 16, 19, 1)  # Vermilion outer thigh rib
    fill_sym_box(grid, 4, 4, 13, 13, 17, 18, 1)  # Vermilion front stripe
    fill_sym_box(grid, 3, 5, 9, 10, 16, 19, 4)   # Rear steel thigh plates

    # --- 4. WAIST / PELVIS (Z: 20..24) ---
    fill_sym_box(grid, 0, 4, 9, 13, 20, 24, 5)   # Dark steel waist core
    fill_sym_box(grid, 0, 4, 13, 14, 21, 23, 3)  # Crisp white aviation waist belt
    fill_sym_box(grid, 0, 4, 8, 9, 21, 23, 3)
    fill_sym_box(grid, 0, 1, 14, 15, 19, 23, 1)  # Vivid vermilion front codpiece
    fill_sym_box(grid, 0, 0, 15, 15, 20, 22, 4)  # Steel ridge
    fill_sym_box(grid, 0, 0, 15, 15, 22, 22, 8)  # Golden waist beacon
    # Vermilion steel-truss side hip skirts
    fill_sym_box(grid, 5, 6, 9, 13, 19, 22, 1)
    fill_sym_box(grid, 6, 6, 10, 12, 20, 21, 2)
    fill_sym_box(grid, 5, 6, 10, 12, 22, 22, 3)  # White hip rim

    # --- 5. TORSO / CHEST (Z: 24..33) - MAIN OBSERVATION DECK (DAI-TENBODAI) CHEST! ---
    # Solid lower abdomen truss bridge connecting waist to Observation Deck chest
    fill_sym_box(grid, 0, 4, 9, 13, 24, 25, 1)
    fill_sym_box(grid, 0, 3, 13, 14, 24, 25, 4)  # Steel cantilevered support brackets!
    fill_sym_box(grid, 2, 2, 14, 14, 24, 25, 1)  # Vermilion truss ribs supporting deck

    # PROMINENT SQUARE MAIN OBSERVATION DECK FORMING THE ENTIRE CHEST (Z: 26..32)!
    fill_sym_box(grid, 0, 5, 9, 15, 26, 32, 1)
    # Hollow unseen torso interior to keep voxel count balanced
    fill_sym_box(grid, 0, 3, 10, 13, 27, 30, 0)
    # Lower cantilevered white observation deck fascia (Z: 26)
    fill_sym_box(grid, 0, 5, 14, 16, 26, 26, 3)
    fill_sym_box(grid, 5, 5, 9, 16, 26, 32, 1)   # Vivid vermilion deck corner columns!
    # Warm golden landmark illumination lights lining the lower deck rim!
    for dx in (0, 2, 4):
        fill_sym_box(grid, dx, dx, 16, 16, 26, 26, 8)
    # Wrap-around Panoramic Deep Blue-Grey Observation Deck Glass Chest (Z: 27..30)!
    fill_sym_box(grid, 0, 4, 15, 16, 27, 30, 6)
    fill_sym_box(grid, 5, 5, 11, 14, 27, 30, 6)  # Side observation windows!
    # Crisp Glowing Cyan Window Glints & Central Observatory Core
    fill_sym_box(grid, 0, 1, 16, 16, 28, 29, 7)  # Glowing cyan main observatory window!
    fill_sym_box(grid, 3, 3, 16, 16, 28, 29, 7)  # Flanking cyan window reflection!
    fill_sym_box(grid, 2, 2, 16, 16, 27, 30, 1)  # Vermilion window mullions
    # Upper aviation white observation deck roof fascia & vermilion collar (Z: 31..32)
    fill_sym_box(grid, 0, 5, 14, 16, 31, 31, 3)
    fill_sym_box(grid, 1, 1, 16, 16, 31, 31, 8)  # Upper golden deck lights
    fill_sym_box(grid, 3, 3, 16, 16, 31, 31, 8)
    fill_sym_box(grid, 0, 4, 9, 14, 32, 32, 1)   # Vivid vermilion upper deck roof
    fill_sym_box(grid, 0, 3, 10, 13, 33, 33, 4)  # Steel neck collar base

    # --- 6. BACKPACK (Y: 5..8, Z: 24..37) - FOLDED TOP DECK & LATTICE WING-STAYS ---
    # Rear folded Top Observation Deck housing
    fill_sym_box(grid, 0, 3, 6, 8, 25, 31, 1)
    fill_sym_box(grid, 0, 2, 5, 6, 26, 30, 3)    # Aviation white band on pack
    fill_sym_box(grid, 0, 2, 5, 5, 27, 29, 6)    # Rear observatory glass module
    fill_sym_box(grid, 0, 1, 5, 5, 28, 28, 7)    # Cyan core glint
    fill_sym_box(grid, 0, 2, 5, 5, 26, 26, 8)    # Golden rear tower lights
    # Twin dark-charcoal vernier thrusters
    fill_sym_box(grid, 2, 3, 5, 7, 23, 25, 5)
    fill_sym_box(grid, 2, 2, 5, 5, 23, 23, 7)
    # Angled Vermilion & White Steel-Truss Wing Stabilizers jutting upward from upper back!
    for i in range(5):
        wcol = 1 if i < 3 else 3
        fill_sym_box(grid, 3 + i, 4 + i, 6, 7, 31 + i, 32 + i, wcol)
    fill_sym_box(grid, 7, 8, 6, 7, 36, 37, 1)
    fill_sym_box(grid, 8, 8, 6, 7, 37, 37, 8)    # Wingtip golden beacon light

    # --- 7. SHOULDERS & ARMS (Z: 15..35) - VERMILION & WHITE BANDED TRUSS ARMOR ---
    # Solid steel shoulder joints connecting into torso
    fill_sym_box(grid, 5, 7, 10, 12, 29, 31, 5)
    # Bold angular Tokyo-Tower Vermilion & White Banded Shoulder Pauldrons!
    fill_sym_box(grid, 6, 10, 9, 14, 29, 32, 1)  # Vivid vermilion lower pauldron!
    fill_sym_box(grid, 10, 10, 9, 14, 29, 31, 2)
    fill_sym_box(grid, 6, 10, 9, 14, 33, 33, 3)  # Crisp aviation white stripe!
    fill_sym_box(grid, 7, 9, 10, 13, 34, 35, 1)  # Vermilion upper truss cap!
    fill_sym_box(grid, 8, 8, 11, 12, 35, 35, 8)  # Golden shoulder warning beacon
    # Open truss vent detail on front/rear of pauldrons
    fill_sym_box(grid, 7, 9, 14, 14, 30, 31, 2)
    fill_sym_box(grid, 8, 8, 14, 14, 30, 31, 4)  # Steel cross-strut

    # Upper arms (x_off: 7..9, Z: 24..28)
    fill_sym_box(grid, 7, 9, 10, 12, 24, 28, 5)
    fill_sym_box(grid, 7, 9, 10, 12, 25, 26, 3)  # White upper arm band
    fill_sym_box(grid, 7, 9, 10, 12, 27, 28, 1)  # Vermilion upper arm band
    fill_sym_box(grid, 7, 9, 10, 12, 24, 24, 4)  # Steel elbow ring

    # LEFT ARM (-X side, x = 8..10) + Steel-Truss Observation Shield
    fill_box(grid, 8, 10, 10, 13, 17, 23, 1)     # Vivid vermilion forearm
    fill_box(grid, 8, 10, 10, 13, 19, 20, 3)     # Crisp white aviation band
    fill_box(grid, 8, 8, 10, 13, 17, 23, 2)
    fill_box(grid, 8, 10, 10, 13, 17, 17, 5)     # Dark steel wrist cuff
    fill_box(grid, 8, 10, 10, 12, 15, 16, 5)     # Left steel fist
    # Tokyo Tower Lattice Buckler Shield on outer left forearm (x = 5..7)
    fill_box(grid, 7, 7, 9, 14, 16, 24, 1)       # Vermilion lattice shield frame
    fill_box(grid, 6, 7, 10, 13, 17, 23, 3)      # White aviation band inner border
    fill_box(grid, 6, 6, 10, 13, 18, 22, 6)      # Blue-grey glass shield core
    fill_box(grid, 5, 5, 11, 12, 19, 21, 7)      # Glowing cyan energy reflector
    fill_box(grid, 6, 6, 11, 12, 16, 16, 8)      # Golden bottom light
    fill_box(grid, 6, 6, 11, 12, 24, 24, 9)      # Red top beacon dot

    # RIGHT ARM (+X side, x = 25..33) - Extended outward holding Broadcast Truss Lance
    fill_box(grid, 25, 27, 10, 13, 19, 23, 1)
    fill_box(grid, 25, 27, 10, 13, 21, 21, 3)    # White band
    fill_box(grid, 26, 30, 10, 13, 18, 20, 1)    # Forearm angled outward
    fill_box(grid, 29, 31, 10, 13, 18, 20, 3)    # White wrist cuff
    fill_box(grid, 31, 33, 11, 13, 17, 19, 5)    # Right fist gripping lance cleanly outside shoulder
    fill_box(grid, 32, 33, 13, 13, 17, 18, 1)

    # --- BROADCAST TRUSS LANCE (+X side at x=33, y=12, clear of shoulder & below Head Spire!) ---
    fill_box(grid, 33, 33, 12, 12, 5, 33, 5)     # Dark steel shaft
    fill_box(grid, 33, 33, 12, 12, 4, 5, 1)      # Vermilion pommel
    fill_box(grid, 33, 33, 12, 12, 15, 16, 3)    # White grip collar
    fill_box(grid, 33, 33, 12, 12, 20, 21, 1)    # Vermilion collar
    # Broadcast Truss Guard & Glowing Cyan Signal Emitter Tip (Z: 31..39)
    fill_box(grid, 32, 34, 11, 13, 31, 32, 1)    # Vermilion truss guard
    fill_box(grid, 31, 35, 12, 12, 32, 32, 3)    # White broadcast crossbar
    fill_box(grid, 32, 34, 12, 12, 33, 34, 4)    # Steel emitter collar
    fill_box(grid, 33, 33, 12, 12, 33, 38, 7)    # Glowing cyan broadcast beam tip
    fill_box(grid, 33, 33, 12, 12, 39, 39, 9)    # Bright red warning beacon tip

    # --- 8. HEAD & DRAMATIC ANTENNA SPIRE CREST (SENTO) (Z: 33..51) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 33, 34, 5)
    # Heroic Mecha Helmet (Z: 34..39) - Crisp Aviation White & Vivid Vermilion!
    fill_sym_box(grid, 0, 2, 9, 13, 34, 38, 3)   # Aviation white helmet shell
    fill_sym_box(grid, 2, 2, 9, 13, 35, 38, 1)   # Vivid vermilion side cheeks/ears!
    fill_sym_box(grid, 2, 2, 10, 11, 36, 37, 8)  # Golden ear beacon lights
    # Faceplate & Glowing Cyan Heroic Visor
    fill_sym_box(grid, 0, 1, 14, 14, 34, 35, 3)  # Crisp white faceplate
    fill_sym_box(grid, 0, 0, 14, 14, 34, 34, 1)  # Vermilion chin guard
    fill_sym_box(grid, 0, 1, 14, 14, 36, 36, 7)  # Glowing cyan heroic visor!
    fill_sym_box(grid, 0, 1, 14, 14, 37, 38, 1)  # Vermilion helmet brow!
    # Swept Side Radar Ear Fins flanking the helmet (kept cleanly to the sides so Spire shines!)
    fill_sym_box(grid, 3, 3, 10, 12, 37, 39, 1)
    fill_sym_box(grid, 4, 4, 10, 11, 39, 40, 3)
    fill_sym_box(grid, 4, 4, 11, 11, 40, 40, 8)

    # THE ICONIC TOKYO TOWER ANTENNA SPIRE CREST (Z: 39..51)!
    # Mini Top-Deck Observatory Crown Base (Z: 39..41)
    fill_sym_box(grid, 0, 2, 10, 13, 39, 39, 1)
    fill_sym_box(grid, 0, 1, 10, 13, 40, 40, 6)  # Blue-grey Top Deck glass crown
    fill_sym_box(grid, 0, 0, 13, 13, 40, 40, 7)  # Cyan forehead beacon
    fill_sym_box(grid, 0, 1, 10, 13, 41, 41, 1)  # Vermilion crown cap
    fill_sym_box(grid, 1, 1, 13, 13, 41, 41, 8)  # Golden crown lights
    # Striped White & Vermilion Tall Antenna Spire Ornament (Z: 42..51)!
    fill_sym_box(grid, 0, 1, 11, 12, 42, 43, 3)  # Aviation white spire base
    fill_sym_box(grid, 0, 0, 11, 12, 44, 45, 3)  # Slender white spire shaft
    fill_sym_box(grid, 1, 2, 11, 12, 44, 44, 4)  # Steel broadcast crossbar fin 1
    fill_sym_box(grid, 0, 0, 11, 12, 46, 49, 1)  # Vivid vermilion upper spire!
    fill_sym_box(grid, 1, 1, 11, 12, 47, 47, 3)  # Crisp white upper crossbar fin 2
    fill_sym_box(grid, 0, 0, 11, 12, 50, 51, 9)  # Bright Red Aircraft Warning Beacon Tip!

    return grid


# ==========================================
# MAGICA-VOXEL (.vox) EXPORTER
# ==========================================
def export_vox(grid, filename):
    X, Y, Z = grid.shape
    xs, ys, zs = np.nonzero(grid)
    voxels = [(int(x), int(y), int(z), int(grid[x, y, z])) for x, y, z in zip(xs, ys, zs)]

    size_content = struct.pack('<III', X, Y, Z)
    size_chunk = b'SIZE' + struct.pack('<II', len(size_content), 0) + size_content

    xyzi_content = bytearray(struct.pack('<I', len(voxels)))
    for vx, vy, vz, vc in voxels:
        xyzi_content += struct.pack('<BBBB', vx, vy, vz, vc)
    xyzi_chunk = b'XYZI' + struct.pack('<II', len(xyzi_content), 0) + bytes(xyzi_content)

    rgba_content = bytearray(256 * 4)
    for idx, (r, g, b, a) in PALETTE.items():
        offset = (idx - 1) * 4
        rgba_content[offset:offset + 4] = struct.pack('<BBBB', r, g, b, a)
    rgba_chunk = b'RGBA' + struct.pack('<II', len(rgba_content), 0) + bytes(rgba_content)

    children = size_chunk + xyzi_chunk + rgba_chunk
    main_chunk = b'MAIN' + struct.pack('<II', 0, len(children)) + children
    header = b'VOX ' + struct.pack('<I', 150)

    with open(filename, 'wb') as f:
        f.write(header + main_chunk)
    return len(voxels)


# ==========================================
# TRUE ISOMETRIC / 3D VOXEL RENDERER
# ==========================================
def shade_color(rgba, factor):
    r, g, b, a = rgba
    return (int(min(255, r * factor)), int(min(255, g * factor)), int(min(255, b * factor)), a)


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=12):
    img = Image.new("RGBA", img_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    X, Y, Z = grid.shape
    xs, ys, zs = np.nonzero(grid)
    if len(xs) == 0:
        return img

    cx = (xs.min() + xs.max() + 1) / 2.0
    cy = (ys.min() + ys.max() + 1) / 2.0
    cz = (zs.min() + zs.max() + 1) / 2.0

    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)
    cos_y, sin_y = np.cos(yaw), np.sin(yaw)
    cos_p, sin_p = np.cos(pitch), np.sin(pitch)

    def project_unit(x, y, z):
        dx, dy, dz = x - cx, y - cy, z - cz
        rx = -dx * cos_y + dy * sin_y
        ry = dx * sin_y + dy * cos_y
        sy = ry * sin_p - dz * cos_p
        depth = ry * cos_p + dz * sin_p
        return rx, sy, depth

    corners = [
        (x, y, z)
        for x in (xs.min(), xs.max() + 1)
        for y in (ys.min(), ys.max() + 1)
        for z in (zs.min(), zs.max() + 1)
    ]
    proj_c = [project_unit(x, y, z) for x, y, z in corners]
    min_rx = min(p[0] for p in proj_c)
    max_rx = max(p[0] for p in proj_c)
    min_sy = min(p[1] for p in proj_c)
    max_sy = max(p[1] for p in proj_c)

    if scale is None:
        sx_fit = (img_size[0] - 2 * margin) / max(1e-5, max_rx - min_rx)
        sy_fit = (img_size[1] - 2 * margin) / max(1e-5, max_sy - min_sy)
        scale = min(sx_fit, sy_fit, 9.5)

    ox = img_size[0] / 2.0 - ((min_rx + max_rx) / 2.0) * scale
    oy = img_size[1] / 2.0 - ((min_sy + max_sy) / 2.0) * scale

    def project(x, y, z):
        rx, sy, depth = project_unit(x, y, z)
        return (rx * scale + ox, sy * scale + oy), depth

    visible = []
    for x, y, z in zip(xs, ys, zs):
        x, y, z = int(x), int(y), int(z)
        if (0 < x < X - 1 and 0 < y < Y - 1 and 0 < z < Z - 1 and
                grid[x - 1, y, z] and grid[x + 1, y, z] and
                grid[x, y - 1, z] and grid[x, y + 1, z] and
                grid[x, y, z - 1] and grid[x, y, z + 1]):
            continue
        _, d = project(x + 0.5, y + 0.5, z + 0.5)
        visible.append((d, x, y, z, int(grid[x, y, z])))

    visible.sort(key=lambda item: item[0])

    faces = [
        ([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)], (0, 0, 1), 1.08),
        ([(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], (0, 0, -1), 0.55),
        ([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (0, -1, 0), 0.76),
        ([(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)], (0, 1, 0), 0.94),
        ([(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)], (-1, 0, 0), 0.80),
        ([(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)], (1, 0, 0), 0.88),
    ]

    vx_dir = sin_y * cos_p
    vy_dir = cos_y * cos_p
    vz_dir = sin_p

    for _, x, y, z, c in visible:
        base_col = PALETTE[c]
        for verts, normal, light in faces:
            nx, ny, nz = normal
            nnx, nny, nnz = x + nx, y + ny, z + nz
            if 0 <= nnx < X and 0 <= nny < Y and 0 <= nnz < Z and grid[nnx, nny, nnz] > 0:
                continue
            dot = nx * vx_dir + ny * vy_dir + nz * vz_dir
            if dot <= 1e-6:
                continue
            poly = [project(x + vx, y + vy, z + vz)[0] for vx, vy, vz in verts]
            fcol = shade_color(base_col, light)
            draw.polygon(poly, fill=fcol, outline=shade_color(fcol, 0.85))
    return img


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=20, yaw_b=32, pitch_b=18):
    canvas = Image.new("RGBA", (860, 540), (20, 24, 34, 255))
    draw = ImageDraw.Draw(canvas)
    for gx in range(0, 860, 20):
        draw.line([(gx, 0), (gx, 540)], fill=(28, 34, 48, 255), width=1)
    for gy in range(0, 540, 20):
        draw.line([(0, gy), (860, gy)], fill=(28, 34, 48, 255), width=1)

    draw.text((24, 16), title_banner, fill=(210, 225, 250, 255))

    models = [
        (label_a, grid_a, v_a, yaw_a, pitch_a),
        (label_b, grid_b, v_b, yaw_b, pitch_b),
    ]
    for idx, (label, m_grid, v_cnt, yaw, pitch) in enumerate(models):
        bx = 24 + idx * 414
        by = 48
        w, h = 398, 468
        draw.rectangle([bx, by, bx + w, by + h], fill=(14, 17, 24, 255), outline=(65, 80, 110, 255), width=2)
        draw.text((bx + 14, by + 12), label, fill=(235, 240, 255, 255))
        gx, gy, gz = m_grid.shape
        draw.text((bx + 14, by + 30), f"Grid: {gx}x{gy}x{gz} | Voxels: {v_cnt}", fill=(130, 155, 195, 255))

        r_front = render_voxel_iso(m_grid, yaw_deg=yaw, pitch_deg=pitch, img_size=(386, 266), margin=12)
        canvas.paste(r_front, (bx + 6, by + 48), r_front)

        rx0, ry0 = bx + 242, by + 318
        draw.rectangle([rx0, ry0, rx0 + 146, ry0 + 140], fill=(20, 24, 34, 255), outline=(50, 62, 85, 255))
        r_rear = render_voxel_iso(m_grid, yaw_deg=yaw + 170, pitch_deg=pitch, img_size=(140, 120), margin=8)
        canvas.paste(r_rear, (rx0 + 3, ry0 + 16), r_rear)
        draw.text((rx0 + 8, ry0 + 5), "REAR VIEW", fill=(120, 140, 175, 255))

        draw.text((bx + 14, by + 406), f"Z-Slices: {gz} layers", fill=(160, 180, 210, 255))
        for pi in range(1, 10):
            px0 = bx + 14 + (pi - 1) * 20
            py0 = by + 430
            draw.rectangle([px0, py0, px0 + 15, py0 + 15], fill=PALETTE[pi], outline=(70, 82, 105, 255))

    canvas.save(out_path)


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "tokyotower_a.vox")
    v_b = export_vox(model_b, "tokyotower_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TOKYO TOWER -> TOKYO TOWER ROBOT",
        "1. TOKYO TOWER",
        "2. TOKYO TOWER ROBOT",
        "preview_tokyotower.png",
        yaw_a=38, pitch_a=18, yaw_b=32, pitch_b=18,
    )
    print(f"tokyotower: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
