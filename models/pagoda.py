import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (242, 238, 228, 255),  # Warm Shikkui White Plaster
    2: (204, 52, 40, 255),    # Vermilion Lacquer Timber (Shu-iro)
    3: (132, 32, 28, 255),    # Deep Crimson Woodwork / Rafters
    4: (46, 58, 78, 255),     # Dark Blue-Grey Kawara Roof Tile
    5: (172, 184, 202, 255),  # Pale-Grey Ridge & Upturned Eaves
    6: (126, 128, 132, 255),  # Temple Stone Foundation (Ishigaki)
    7: (54, 58, 68, 255),     # Dark Slate Mortar / Iron Frame
    8: (246, 200, 64, 255),   # Gleaming Golden Sorin Finial
    9: (72, 230, 218, 255),   # Sacred Jade-Cyan Glow / Visor
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


def fill_square_ring(grid, r_in, r_out, z0, z1, col):
    """Fill a 4-way symmetric hollow square ring around (X/2, Y/2) center."""
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2
    for r in range(r_in, r_out + 1):
        fill_box(grid, cx_l - r, cx_r + r, cy_l - r, cy_l - r, z0, z1, col)
        fill_box(grid, cx_l - r, cx_r + r, cy_r + r, cy_r + r, z0, z1, col)
        fill_box(grid, cx_l - r, cx_l - r, cy_l - r, cy_r + r, z0, z1, col)
        fill_box(grid, cx_r + r, cx_r + r, cy_l - r, cy_r + r, z0, z1, col)


def fill_corners(grid, r, z0, z1, col):
    """Fill the 4 symmetric corner cells at radius r from center."""
    X, Y, _ = grid.shape
    cx_l, cx_r = X // 2 - 1, X // 2
    cy_l, cy_r = Y // 2 - 1, Y // 2
    for x in (cx_l - r, cx_r + r):
        for y in (cy_l - r, cy_r + r):
            fill_box(grid, x, x, y, y, z0, z1, col)


def hollow_26_interior(grid):
    """Safely hollow voxels whose entire 3x3x3 neighborhood is occupied (preserves 6-connectivity)."""
    X, Y, Z = grid.shape
    occ = grid > 0
    interior = np.ones((X - 2, Y - 2, Z - 2), dtype=bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                interior &= occ[1 + dx:X - 1 + dx, 1 + dy:Y - 1 + dy, 1 + dz:Z - 1 + dz]
    grid[1:X - 1, 1:Y - 1, 1:Z - 1][interior] = 0


# ==========================================
# FORM A: FIVE-STORY PAGODA (18 x 18 x 50)
# ==========================================
def build_a():
    grid = np.zeros((18, 18, 50), dtype=np.uint8)
    cx_l, cx_r = 8, 9
    cy_l, cy_r = 8, 9

    # --- STONE FOUNDATION BASE (Ishigaki, Z: 0..2) ---
    fill_square_ring(grid, 6, 6, 0, 1, 6)
    fill_square_ring(grid, 5, 6, 2, 2, 6)
    # Dark stone mortar masonry accents at corners & mid-walls
    fill_corners(grid, 6, 0, 2, 7)
    for off in (-3, 0, 3):
        fill_box(grid, cx_l + off, cx_l + off, cy_l - 6, cy_l - 6, 0, 0, 7)
        fill_box(grid, cx_l + off, cx_l + off, cy_r + 6, cy_r + 6, 0, 0, 7)
        fill_box(grid, cx_l - 6, cx_l - 6, cy_l + off, cy_l + off, 0, 0, 7)
        fill_box(grid, cx_r + 6, cx_r + 6, cy_l + off, cy_l + off, 0, 0, 7)
    # Front (+Y) grand stone entrance stairs
    fill_sym_box(grid, 0, 2, cy_r + 7, cy_r + 8, 0, 0, 6)
    fill_sym_box(grid, 0, 1, cy_r + 7, cy_r + 7, 1, 1, 6)
    fill_sym_box(grid, 0, 1, cy_r + 6, cy_r + 6, 2, 2, 6)
    fill_sym_box(grid, 2, 2, cy_r + 7, cy_r + 8, 0, 1, 7)
    fill_sym_box(grid, 2, 2, cy_r + 7, cy_r + 7, 2, 2, 2)  # Vermilion entrance posts

    # --- FIVE PROGRESSIVELY TAPERING STORIES (Z: 3..35) ---
    # Story definitions: (zw0, wall_h, rw, rr, next_rw)
    # Tightly engineered hollow shells with 100% 6-connected overlap at every tier!
    stories = [
        (3,  4, 5, 7, 4),  # Story 1: walls Z=3..6, roof Z=7..8, corners r=8 (18x18)
        (9,  4, 4, 6, 3),  # Story 2: walls Z=9..12, roof Z=13..14, corners r=7 (16x16)
        (15, 4, 3, 5, 2),  # Story 3: walls Z=15..18, roof Z=19..20, corners r=6 (14x14)
        (21, 4, 2, 4, 2),  # Story 4: walls Z=21..24, roof Z=25..26, corners r=5 (12x12)
        (27, 4, 2, 4, 0),  # Story 5: walls Z=27..30, pyramidal roof Z=31..35
    ]

    for idx, (zw0, wh, rw, rr, next_rw) in enumerate(stories):
        zw1 = zw0 + wh - 1
        zr = zw1 + 1

        # Vermilion balcony rim & corner posts on lower story
        if idx == 0:
            fill_square_ring(grid, rw + 1, rw + 1, zw0, zw0, 3)
            fill_corners(grid, rw + 1, zw0, zw0 + 1, 2)
            fill_sym_box(grid, 2, 2, cy_r + rw + 1, cy_r + rw + 1, zw0, zw0 + 1, 2)
            fill_sym_box(grid, 2, 2, cy_l - rw - 1, cy_l - rw - 1, zw0, zw0 + 1, 2)
        else:
            # Upper story vermilion corner balcony posts sitting cleanly on lower roof
            fill_corners(grid, rw + 1, zw0, zw0, 2)

        # Crisp white plaster hollow wall shell
        fill_square_ring(grid, rw, rw, zw0, zw1, 1)

        # Vermilion corner pillars & top/bottom timber beams
        fill_corners(grid, rw, zw0, zw1, 2)
        fill_square_ring(grid, rw, rw, zw1, zw1, 2)
        fill_square_ring(grid, rw, rw, zw0, zw0, 2)

        # Intermediate vermilion timber columns on lower stories
        if rw >= 4:
            for x in (cx_l - 2, cx_r + 2):
                fill_box(grid, x, x, cy_r + rw, cy_r + rw, zw0, zw1, 2)
                fill_box(grid, x, x, cy_l - rw, cy_l - rw, zw0, zw1, 2)
            for y in (cy_l - 2, cy_r + 2):
                fill_box(grid, cx_l - rw, cx_l - rw, y, y, zw0, zw1, 2)
                fill_box(grid, cx_r + rw, cx_r + rw, y, y, zw0, zw1, 2)

        # Shrine portals & temple windows
        if idx == 0:
            # Grand Story 1 front sanctuary doorway with gold lintel & sacred jade lantern
            fill_sym_box(grid, 0, 1, cy_r + rw, cy_r + rw, zw0, zw1 - 1, 3)
            fill_sym_box(grid, 0, 0, cy_r + rw, cy_r + rw, zw0 + 1, zw0 + 2, 9)
            fill_sym_box(grid, 0, 1, cy_r + rw, cy_r + rw, zw1, zw1, 8)
            fill_sym_box(grid, 0, 1, cy_l - rw, cy_l - rw, zw0, zw1 - 1, 3)
        else:
            fill_sym_box(grid, 0, 0, cy_r + rw, cy_r + rw, zw0 + 1, zw1 - 1, 3)
            fill_sym_box(grid, 0, 0, cy_l - rw, cy_l - rw, zw0 + 1, zw1 - 1, 3)
            fill_box(grid, cx_l - rw, cx_l - rw, cy_l, cy_r, zw0 + 1, zw1 - 1, 3)
            fill_box(grid, cx_r + rw, cx_r + rw, cy_l, cy_r, zw0 + 1, zw1 - 1, 3)
            if idx == 4:
                fill_sym_box(grid, 0, 0, cy_r + rw, cy_r + rw, zw0 + 1, zw0 + 2, 8)

        # Under-eave deep crimson rafters/brackets connecting wall to roof
        fill_square_ring(grid, rw + 1, rw + 1, zw1, zw1, 3)

        # Wide flaring dark blue-grey Kawara tiled roof (sleek 2-layer overhang + upturned corners)
        if idx < 4:
            # Layer 0 (zr): flaring outer roof rim (rw+1..rr)
            fill_square_ring(grid, rw + 1, rr, zr, zr, 4)
            # Layer 1 (zr+1): upper roof slope stepping cleanly to next story wall (next_rw..rw+1)
            fill_square_ring(grid, next_rw, rw + 1, zr + 1, zr + 1, 4)

            # Crisp pale-grey diagonal hip ridges & upturned corner eaves
            fill_corners(grid, rw + 1, zr + 1, zr + 1, 5)
            fill_corners(grid, rr, zr, zr + 1, 5)
            # Flaring upturned corner tip (6-connected via (rr, rr, zr+1))
            for sx, bx in ((-1, cx_l), (1, cx_r)):
                for sy, by in ((-1, cy_l), (1, cy_r)):
                    fill_box(grid, bx + sx * (rr + 1), bx + sx * (rr + 1), by + sy * rr, by + sy * rr, zr + 1, zr + 1, 5)
                    fill_box(grid, bx + sx * rr, bx + sx * rr, by + sy * (rr + 1), by + sy * (rr + 1), zr + 1, zr + 1, 5)
                    fill_box(grid, bx + sx * (rr + 1), bx + sx * (rr + 1), by + sy * (rr + 1), by + sy * (rr + 1), zr + 1, zr + 2, 5)
        else:
            # Story 5: steep pyramidal crowning roof (Z = 31..35)
            fill_square_ring(grid, 3, 4, zr, zr, 4)
            fill_square_ring(grid, 2, 3, zr + 1, zr + 1, 4)
            fill_square_ring(grid, 1, 2, zr + 2, zr + 2, 4)
            fill_square_ring(grid, 0, 1, zr + 3, zr + 3, 4)
            fill_box(grid, cx_l, cx_r, cy_l, cy_r, zr + 4, zr + 4, 4)
            # Pale-grey hip ridges converging to spire base + upturned corner eaves
            fill_corners(grid, 1, zr + 3, zr + 3, 5)
            fill_corners(grid, 2, zr + 2, zr + 2, 5)
            fill_corners(grid, 3, zr + 1, zr + 1, 5)
            fill_corners(grid, 4, zr, zr + 1, 5)
            for sx, bx in ((-1, cx_l), (1, cx_r)):
                for sy, by in ((-1, cy_l), (1, cy_r)):
                    fill_box(grid, bx + sx * 5, bx + sx * 5, by + sy * 4, by + sy * 4, zr + 1, zr + 1, 5)
                    fill_box(grid, bx + sx * 4, bx + sx * 4, by + sy * 5, by + sy * 5, zr + 1, zr + 1, 5)
                    fill_box(grid, bx + sx * 5, bx + sx * 5, by + sy * 5, by + sy * 5, zr + 1, zr + 2, 5)

    # --- TALL SLEEK GOLDEN SORIN SPIRE FINIAL (Z: 36..49) ---
    # Roban (dew basin) & fukubachi (inverted bowl)
    fill_square_ring(grid, 0, 1, 36, 36, 7)
    fill_box(grid, cx_l, cx_r, cy_l, cy_r, 37, 49, 8)
    fill_square_ring(grid, 1, 1, 37, 37, 8)
    # Stacked sacred rings (kurin) spaced cleanly for slender silhouette
    for rz in (39, 41, 43):
        fill_box(grid, cx_l - 1, cx_r + 1, cy_l, cy_r, rz, rz, 8)
        fill_box(grid, cx_l, cx_r, cy_l - 1, cy_r + 1, rz, rz, 8)
    # Water-flame filigree ornament (suien)
    fill_box(grid, cx_l - 2, cx_r + 2, cy_l, cy_r, 45, 45, 8)
    fill_box(grid, cx_l, cx_r, cy_l - 2, cy_r + 2, 45, 45, 8)
    fill_box(grid, cx_l - 2, cx_l - 2, cy_l, cy_r, 46, 46, 8)
    fill_box(grid, cx_r + 2, cx_r + 2, cy_l, cy_r, 46, 46, 8)
    fill_box(grid, cx_l, cx_r, cy_l - 2, cy_l - 2, 46, 46, 8)
    fill_box(grid, cx_l, cx_r, cy_r + 2, cy_r + 2, 46, 46, 8)
    # Sacred jewel (hoju) & golden pinnacle
    fill_box(grid, cx_l, cx_r, cy_l, cy_r, 47, 47, 9)
    fill_box(grid, cx_l, cx_r, cy_l, cy_r, 48, 49, 8)

    hollow_26_interior(grid)
    return grid


# ==========================================
# FORM B: FIVE-STORY PAGODA TITAN ROBOT (32 x 22 x 46)
# ==========================================
def build_b():
    grid = np.zeros((32, 22, 46), dtype=np.uint8)

    # --- HEAVY STONE FOUNDATION BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 2, 6, 6, 14, 0, 2, 6)
    fill_sym_box(grid, 2, 6, 6, 15, 0, 0, 7)      # Dark stone sole
    fill_sym_box(grid, 2, 5, 14, 16, 0, 1, 6)     # Stepped ishigaki stone toe
    fill_sym_box(grid, 3, 4, 15, 16, 2, 2, 6)
    fill_sym_box(grid, 2, 6, 6, 7, 1, 3, 7)       # Heavy stone heel block
    fill_sym_box(grid, 3, 5, 8, 13, 3, 3, 2)      # Tapered vermilion ankle collar
    fill_sym_box(grid, 4, 4, 15, 15, 2, 2, 8)     # Golden shrine toe stud

    # --- VERMILION & WHITE TIMBER LOWER LEGS (Z: 4..13) ---
    fill_sym_box(grid, 2, 5, 8, 13, 4, 13, 1)
    # Vermilion corner pillars framing crisp white plaster panels
    fill_sym_box(grid, 2, 2, 8, 8, 4, 13, 2)
    fill_sym_box(grid, 5, 5, 8, 8, 4, 13, 2)
    fill_sym_box(grid, 2, 2, 13, 13, 4, 13, 2)
    fill_sym_box(grid, 5, 5, 13, 13, 4, 13, 2)
    fill_sym_box(grid, 2, 5, 8, 13, 4, 4, 2)
    fill_sym_box(grid, 2, 5, 8, 13, 8, 8, 2)
    fill_sym_box(grid, 5, 5, 9, 12, 5, 7, 3)      # Crimson timber shutter accent
    fill_sym_box(grid, 5, 5, 9, 12, 9, 11, 3)
    # Flaring Kawara roof knee guards with upturned pale-grey eaves
    fill_sym_box(grid, 2, 5, 13, 15, 11, 13, 4)
    fill_sym_box(grid, 2, 2, 15, 15, 12, 13, 5)
    fill_sym_box(grid, 5, 5, 15, 15, 12, 13, 5)
    fill_sym_box(grid, 3, 4, 15, 15, 12, 12, 8)   # Golden knee crest

    # --- THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 2, 4, 8, 12, 14, 18, 7)
    fill_sym_box(grid, 2, 4, 12, 13, 14, 17, 1)
    fill_sym_box(grid, 4, 4, 9, 12, 14, 17, 2)

    # --- WAIST / PELVIS & DOUBLE-TIERED PAGODA ROOF KUSAZURI SKIRT (Z: 15..21) ---
    fill_sym_box(grid, 0, 4, 7, 13, 18, 21, 7)
    fill_sym_box(grid, 0, 1, 13, 15, 15, 20, 2)   # Center vermilion loincloth (maedare)
    fill_sym_box(grid, 0, 0, 14, 15, 16, 19, 1)
    fill_sym_box(grid, 0, 1, 14, 15, 20, 21, 8)   # Golden shrine belt buckle
    fill_sym_box(grid, 0, 0, 15, 15, 20, 20, 9)   # Jade waist jewel
    # Upper kusazuri pagoda roof tier (Z: 19..20)
    fill_sym_box(grid, 2, 5, 13, 15, 19, 20, 4)   # Front roof eaves
    fill_sym_box(grid, 5, 6, 7, 14, 19, 20, 4)    # Side roof eaves
    fill_sym_box(grid, 1, 5, 5, 7, 19, 20, 4)     # Rear roof eaves
    fill_sym_box(grid, 6, 7, 14, 15, 20, 20, 5)   # Upturned pale-grey front corners
    fill_sym_box(grid, 6, 7, 5, 6, 20, 20, 5)     # Upturned pale-grey rear corners
    # Lower kusazuri pagoda roof tier (Z: 15..18) flaring wider over thighs
    fill_sym_box(grid, 2, 5, 14, 15, 16, 18, 4)   # Front lower roof flaps
    fill_sym_box(grid, 5, 7, 7, 14, 16, 18, 4)    # Side lower roof flaps
    fill_sym_box(grid, 1, 5, 4, 6, 16, 18, 4)     # Rear lower roof flaps
    fill_sym_box(grid, 2, 5, 14, 14, 18, 18, 3)   # Crimson under-eave rafters
    fill_sym_box(grid, 6, 6, 7, 13, 18, 18, 3)
    fill_sym_box(grid, 7, 8, 14, 15, 17, 17, 5)   # Wide upturned pale-grey lower tips
    fill_sym_box(grid, 7, 8, 5, 6, 17, 17, 5)
    fill_sym_box(grid, 2, 5, 15, 15, 15, 15, 5)
    fill_sym_box(grid, 6, 7, 7, 13, 15, 15, 5)

    # --- TORSO / SANCTUARY CHEST & LAYERED CHEST EAVES (Z: 22..31) ---
    fill_sym_box(grid, 0, 5, 7, 14, 22, 31, 1)
    # Vermilion corner & horizontal beams framing white plaster sanctuary walls
    fill_sym_box(grid, 0, 4, 7, 13, 22, 22, 2)
    fill_sym_box(grid, 4, 5, 7, 14, 23, 30, 2)
    fill_sym_box(grid, 2, 2, 14, 14, 23, 30, 2)
    fill_sym_box(grid, 0, 5, 7, 13, 31, 31, 2)
    # Central shrine sanctuary doorway with glowing sacred jade core
    fill_sym_box(grid, 0, 1, 14, 15, 24, 28, 3)
    fill_sym_box(grid, 0, 1, 15, 15, 25, 27, 9)   # Glowing sacred jade core
    fill_sym_box(grid, 0, 1, 15, 15, 28, 28, 8)   # Golden lintel
    fill_sym_box(grid, 0, 1, 15, 15, 24, 24, 8)
    # Lower chest eave trim (Z: 23)
    fill_sym_box(grid, 2, 5, 14, 15, 23, 23, 4)
    fill_sym_box(grid, 5, 5, 15, 15, 23, 24, 5)
    # Grand Upper Chest Pagoda Roof Eave (Z: 29..31)
    fill_sym_box(grid, 0, 5, 14, 16, 29, 30, 4)
    fill_sym_box(grid, 0, 4, 14, 15, 31, 31, 4)
    fill_sym_box(grid, 0, 4, 14, 15, 28, 28, 3)   # Crimson under-eave rafters
    fill_sym_box(grid, 4, 5, 16, 16, 30, 31, 5)   # Upturned pale-grey chest eaves
    fill_sym_box(grid, 0, 1, 16, 16, 30, 31, 8)   # Golden onigawara gable crest
    # Samurai collar framing neck
    fill_sym_box(grid, 0, 2, 8, 12, 32, 32, 2)
    fill_sym_box(grid, 2, 2, 8, 12, 33, 33, 8)

    # --- BACKPACK: SHRINE HOUSING & SPLIT PAGODA ROOF WINGS (Y: 2..6, Z: 21..33) ---
    fill_sym_box(grid, 0, 3, 4, 6, 22, 31, 1)
    fill_sym_box(grid, 3, 3, 4, 6, 22, 31, 2)
    fill_sym_box(grid, 0, 1, 4, 4, 24, 29, 3)
    fill_sym_box(grid, 0, 2, 3, 4, 22, 24, 7)
    fill_sym_box(grid, 1, 2, 3, 4, 20, 21, 8)     # Golden temple bell thrusters
    # Sweeping split pagoda roof wing fins
    for i in range(5):
        fill_sym_box(grid, 3 + i, 4 + i, 2, 4, 25 + i, 27 + i, 4)
        fill_sym_box(grid, 4 + i, 4 + i, 2, 3, 27 + i, 28 + i, 5 if i >= 2 else 4)
    fill_sym_box(grid, 7, 8, 2, 3, 31, 32, 5)     # Wingtip upturned pale-grey eaves
    fill_sym_box(grid, 3, 4, 4, 6, 25, 28, 2)     # Solid wing mounts

    # --- DOUBLE-TIERED PAGODA ROOF SHOULDER PAULDRONS (Z: 27..36) ---
    # Shoulder joint connecting to torso
    fill_sym_box(grid, 5, 7, 8, 12, 27, 30, 7)
    # Lower shoulder pagoda story wall
    fill_sym_box(grid, 6, 9, 8, 12, 27, 28, 1)
    fill_sym_box(grid, 6, 9, 8, 8, 27, 28, 2)
    fill_sym_box(grid, 6, 9, 12, 12, 27, 28, 2)
    # LOWER SHOULDER PAGODA ROOF TIER (Z: 28..30)
    fill_sym_box(grid, 7, 13, 6, 14, 28, 29, 4)
    fill_sym_box(grid, 7, 11, 7, 13, 30, 30, 4)
    fill_sym_box(grid, 7, 12, 7, 13, 28, 28, 3)   # Crimson rafters underneath
    # Crisp dark kawara outer rim
    fill_sym_box(grid, 12, 13, 6, 14, 28, 29, 4)
    fill_sym_box(grid, 7, 13, 6, 7, 28, 29, 4)
    fill_sym_box(grid, 7, 13, 13, 14, 28, 29, 4)
    # Pale-grey upturned corners on Lower Shoulder Roof
    fill_sym_box(grid, 13, 14, 6, 7, 29, 30, 5)
    fill_sym_box(grid, 13, 14, 13, 14, 29, 30, 5)
    fill_sym_box(grid, 7, 8, 6, 6, 29, 30, 5)
    fill_sym_box(grid, 7, 8, 14, 14, 29, 30, 5)
    # Mid Pagoda Story Wall Spacer (clearly visible white plaster + vermilion pillars!)
    fill_sym_box(grid, 7, 10, 8, 12, 30, 32, 1)
    fill_sym_box(grid, 7, 7, 8, 12, 30, 32, 2)
    fill_sym_box(grid, 10, 10, 8, 12, 30, 32, 2)
    fill_sym_box(grid, 8, 9, 12, 12, 31, 31, 3)   # Mini shrine lattice window
    # UPPER SHOULDER PAGODA ROOF TIER (Z: 32..35)
    fill_sym_box(grid, 6, 12, 7, 13, 32, 33, 4)
    fill_sym_box(grid, 7, 10, 8, 12, 34, 34, 4)
    fill_sym_box(grid, 8, 9, 9, 11, 35, 35, 4)
    fill_sym_box(grid, 8, 9, 10, 10, 36, 36, 8)   # Golden miniature shoulder finial
    # Pale-grey ridge lines & soaring upturned eaves on Upper Shoulder Roof
    fill_sym_box(grid, 12, 13, 7, 8, 33, 34, 5)
    fill_sym_box(grid, 12, 13, 12, 13, 33, 34, 5)
    fill_sym_box(grid, 6, 7, 7, 7, 33, 34, 5)
    fill_sym_box(grid, 6, 7, 13, 13, 33, 34, 5)
    fill_sym_box(grid, 11, 11, 8, 8, 34, 34, 5)
    fill_sym_box(grid, 11, 11, 12, 12, 34, 34, 5)

    # --- ARMS & TIMBER GAUNTLETS (Z: 13..27) ---
    # Upper arm
    fill_sym_box(grid, 8, 9, 9, 11, 22, 27, 7)
    fill_sym_box(grid, 8, 9, 9, 11, 24, 25, 2)
    fill_sym_box(grid, 9, 9, 10, 10, 24, 25, 8)
    # Forearm gauntlets (white plaster & vermilion pillars)
    fill_sym_box(grid, 8, 10, 8, 13, 16, 21, 1)
    fill_sym_box(grid, 8, 8, 8, 13, 16, 21, 2)
    fill_sym_box(grid, 10, 10, 8, 13, 16, 21, 2)
    fill_sym_box(grid, 8, 10, 8, 13, 16, 16, 2)
    fill_sym_box(grid, 8, 10, 8, 13, 21, 21, 2)
    # Outer forearm kawara eave guards
    fill_sym_box(grid, 11, 11, 9, 13, 17, 21, 4)
    fill_sym_box(grid, 11, 12, 9, 9, 17, 18, 5)
    fill_sym_box(grid, 11, 12, 13, 13, 20, 21, 5)
    fill_sym_box(grid, 11, 11, 11, 11, 19, 19, 8)
    # Fists (Z: 13..15)
    fill_sym_box(grid, 8, 9, 9, 12, 13, 15, 7)
    fill_sym_box(grid, 9, 9, 12, 12, 14, 15, 2)

    # --- RIGHT-HAND SACRED TEMPLE KATANA (+X side, x=25) ---
    fill_box(grid, 25, 25, 8, 13, 14, 14, 3)      # Crimson wrapped hilt
    fill_box(grid, 25, 25, 8, 8, 14, 14, 8)       # Golden pommel
    fill_box(grid, 24, 26, 13, 13, 13, 15, 8)     # Golden tsuba crossguard
    # Sweeping forward silver & glowing sacred jade blade
    for step in range(8):
        by = 14 + step
        bz = 14 + (step // 2)
        fill_box(grid, 25, 25, by, by, bz, bz, 5)
        fill_box(grid, 25, 25, by, by, bz + 1, bz + 1, 9)

    # --- LEFT-ARM PAGODA EAVE BUCKLER SHIELD (-X side, x=3..4) ---
    fill_box(grid, 4, 4, 8, 14, 15, 22, 4)
    fill_box(grid, 3, 3, 9, 13, 16, 21, 4)
    fill_box(grid, 3, 3, 10, 12, 17, 20, 2)       # Vermilion shrine crest panel
    fill_box(grid, 3, 3, 11, 11, 18, 19, 8)       # Golden temple emblem
    fill_box(grid, 3, 4, 8, 8, 15, 16, 5)         # Upturned pale-grey shield eaves
    fill_box(grid, 3, 4, 14, 14, 15, 16, 5)
    fill_box(grid, 3, 4, 8, 8, 21, 22, 5)
    fill_box(grid, 3, 4, 14, 14, 21, 22, 5)

    # --- SAMURAI KABUTO HELMET & TOWERING GOLDEN SORIN SPIRE CREST (Z: 32..45) ---
    # Neck
    fill_sym_box(grid, 0, 1, 9, 11, 32, 33, 7)
    # Head core & white plaster samurai face mask
    fill_sym_box(grid, 0, 2, 8, 12, 33, 36, 1)
    fill_sym_box(grid, 0, 1, 12, 13, 33, 34, 1)   # White samurai face guard
    fill_sym_box(grid, 0, 0, 13, 13, 33, 33, 2)   # Vermilion chin plate
    fill_sym_box(grid, 0, 2, 12, 13, 35, 35, 9)   # Glowing sacred jade samurai visor
    fill_sym_box(grid, 0, 0, 13, 13, 35, 35, 7)   # Dark nose bridge
    # Kawara-roof Samurai Kabuto Helmet & Neck Flaps (Shikoro)
    fill_sym_box(grid, 0, 3, 7, 13, 36, 37, 4)    # Kabuto roof dome
    fill_sym_box(grid, 0, 2, 8, 12, 38, 38, 4)    # Crown tier
    fill_sym_box(grid, 2, 3, 7, 11, 33, 35, 4)    # Side & rear shikoro flaps
    fill_sym_box(grid, 0, 2, 7, 8, 33, 35, 4)
    fill_sym_box(grid, 3, 4, 9, 12, 36, 36, 5)    # Pale-grey upturned helmet eaves
    fill_sym_box(grid, 3, 4, 7, 8, 34, 35, 5)
    fill_sym_box(grid, 0, 2, 13, 13, 36, 36, 2)   # Vermilion brow band
    # Sweeping Golden Samurai Kuwagata Crescent Horns
    fill_sym_box(grid, 0, 1, 13, 14, 37, 38, 8)
    fill_sym_box(grid, 2, 2, 13, 14, 38, 39, 8)
    fill_sym_box(grid, 3, 3, 12, 13, 39, 40, 8)
    fill_sym_box(grid, 4, 4, 12, 13, 40, 41, 8)
    # TOWERING GOLDEN SORIN SPIRE CREST rising from helmet crown (Z: 38..45)
    fill_sym_box(grid, 0, 1, 9, 11, 38, 38, 8)    # Roban base
    fill_sym_box(grid, 0, 0, 10, 11, 39, 45, 8)   # Slender golden sorin spire shaft
    # Crisp stacked sacred rings (kurin) on head spire
    for rz in (40, 42):
        fill_sym_box(grid, 0, 1, 10, 11, rz, rz, 8)
        fill_sym_box(grid, 0, 0, 9, 12, rz, rz, 8)
    # Filigree suien crest wings & glowing sacred jewel tip
    fill_sym_box(grid, 1, 2, 10, 11, 43, 43, 8)
    fill_sym_box(grid, 2, 2, 10, 11, 44, 44, 8)
    fill_sym_box(grid, 0, 0, 10, 11, 44, 44, 9)   # Sacred jade jewel glint
    fill_sym_box(grid, 0, 0, 10, 11, 45, 45, 8)   # Golden pinnacle

    hollow_26_interior(grid)
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


def render_voxel_iso(grid, yaw_deg=35, pitch_deg=25, scale=None, img_size=(386, 266), margin=14):
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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=36, pitch_a=20, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "pagoda_a.vox")
    v_b = export_vox(model_b, "pagoda_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: FIVE-STORY PAGODA -> FIVE-STORY PAGODA TITAN ROBOT",
        "1. FIVE-STORY PAGODA",
        "2. FIVE-STORY PAGODA TITAN ROBOT",
        "preview_pagoda.png",
        yaw_a=36, pitch_a=20, yaw_b=32, pitch_b=20,
    )
    print(f"pagoda: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
