import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (124, 78, 44, 255),    # Warm Woodland Brown Plumage
    2: (176, 124, 74, 255),   # Soft Tawny / Tan Feathers
    3: (234, 218, 188, 255),  # Cream Speckled Breast & Facial Disc
    4: (72, 46, 28, 255),     # Dark Umber Wingtip Feathers & Shading
    5: (44, 48, 56, 255),     # Deep Charcoal Mecha Joints & Talons
    6: (255, 196, 36, 255),   # Huge Bright Golden-Amber Owl Eyes & Core
    7: (18, 20, 26, 255),     # Pitch-Black Pupils & Deep Crevices
    8: (238, 128, 32, 255),   # Warm Orange Beak & Talon Feet
    9: (250, 244, 228, 255),  # Pale Feather Highlight & Eye Glint
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


def hollow_interior_26(grid, z_min, z_max):
    """Hollow only strictly interior voxels (all 26 neighbors occupied) so 6-connectivity is preserved."""
    X, Y, Z = grid.shape
    to_clear = []
    for x in range(1, X - 1):
        for y in range(1, Y - 1):
            for z in range(max(1, z_min), min(Z - 1, z_max + 1)):
                if grid[x, y, z] == 0:
                    continue
                if np.all(grid[x - 1:x + 2, y - 1:y + 2, z - 1:z + 2] > 0):
                    to_clear.append((x, y, z))
    for x, y, z in to_clear:
        grid[x, y, z] = 0


# ==========================================
# FORM A: GREAT HORNED OWL (24 x 22 x 34)
# ==========================================
def build_a():
    grid = np.zeros((24, 22, 34), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0  # 11.5

    # --- CLAWED ORANGE TALONS GRIPPING BASE (Z: 0..3) ---
    # Three spreading forward toes + rear gripping talon per foot
    fill_sym_box(grid, 2, 4, 10, 14, 0, 1, 8)   # Foot pad
    fill_sym_box(grid, 1, 1, 13, 15, 0, 0, 8)   # Inner toe
    fill_sym_box(grid, 3, 3, 14, 16, 0, 0, 8)   # Middle toe
    fill_sym_box(grid, 5, 5, 13, 15, 0, 0, 8)   # Outer toe
    fill_sym_box(grid, 3, 3, 8, 9, 0, 0, 8)     # Rear hallux toe
    # Sharp dark charcoal talon tips
    fill_sym_box(grid, 1, 1, 16, 16, 0, 0, 5)
    fill_sym_box(grid, 3, 3, 17, 17, 0, 0, 5)
    fill_sym_box(grid, 5, 5, 16, 16, 0, 0, 5)
    fill_sym_box(grid, 3, 3, 7, 7, 0, 0, 5)
    # Feathered owl ankle puffs (Z: 2..3)
    fill_sym_box(grid, 2, 4, 10, 13, 2, 3, 2)
    fill_sym_box(grid, 2, 3, 12, 13, 2, 3, 3)

    # --- PLUMP SPECKLED OWL BODY (Z: 3..21) ---
    # (z, rx, yc, ry_back, ry_front)
    body_profile = [
        (3,  4.4, 10.6, 3.3, 3.6),
        (4,  5.3, 10.6, 4.1, 4.5),
        (5,  6.0, 10.6, 4.6, 5.1),
        (6,  6.5, 10.6, 5.0, 5.5),
        (7,  6.8, 10.6, 5.2, 5.8),
        (8,  7.0, 10.6, 5.3, 5.9),
        (9,  7.1, 10.6, 5.3, 6.0),
        (10, 7.1, 10.6, 5.3, 6.0),
        (11, 7.0, 10.6, 5.2, 5.9),
        (12, 6.9, 10.6, 5.1, 5.8),
        (13, 6.7, 10.6, 5.0, 5.7),
        (14, 6.5, 10.6, 4.9, 5.5),
        (15, 6.3, 10.6, 4.8, 5.3),
        (16, 6.1, 10.6, 4.7, 5.1),
        (17, 5.8, 10.6, 4.5, 4.9),
        (18, 5.5, 10.6, 4.3, 4.7),
        (19, 5.3, 10.6, 4.2, 4.6),
        (20, 5.1, 10.6, 4.1, 4.5),
        (21, 5.1, 10.7, 4.0, 4.5),
    ]

    for z, rx, yc, ry_b, ry_f in body_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    # Front breast is cream with crisp horizontal owl-feather speckles
                    breast_cut = 10.6 + 0.16 * (dx ** 1.35)
                    if y >= breast_cut:
                        # Crisp speckled chevron flecks across cream owl breast (organic owl mottling)
                        if z <= 4:
                            col = 2
                        elif z >= 19 and dx <= 2.5 and y >= 14:
                            col = 9  # Pale white-cream throat bib!
                        elif (z % 3 == 0) and (int(round(dx * 1.1)) + (z // 3)) % 3 == 0 and dx <= rx - 1.0:
                            col = 1  # Woodland brown breast fleck
                        elif (z % 3 == 2) and (int(round(dx * 1.2)) + (z // 3)) % 3 == 1 and dx <= rx - 1.1:
                            col = 2  # Soft tawny feather speckle
                        else:
                            col = 3  # Cream breast plumage
                    else:
                        # Layered woodland brown back with tawny feather scaling & dark umber bars
                        if (z % 3 == 0) and (int(round(dx)) % 2 == 0):
                            col = 2
                        elif (z % 4 == 1) and dy < -ry_b * 0.55:
                            col = 4
                        else:
                            col = 1
                    grid[x, y, z] = col

    # --- LAYERED OWL TAIL FEATHERS AT -Y (Z: 1..8, Y: 2..7) ---
    fill_sym_box(grid, 0, 3, 5, 7, 5, 8, 1)
    fill_sym_box(grid, 0, 3, 4, 6, 3, 6, 1)
    fill_sym_box(grid, 0, 2, 3, 5, 2, 4, 4)     # Dark umber tail feather bars
    fill_sym_box(grid, 0, 2, 2, 4, 1, 2, 1)
    fill_sym_box(grid, 1, 1, 2, 5, 2, 6, 2)     # Tawny feather rib streaks
    fill_sym_box(grid, 0, 1, 2, 2, 1, 1, 4)     # Tapered dark tail tips

    # --- FOLDED LAYERED BROWN WINGS ON SIDES (Z: 5..19, x_off: 5..8) ---
    # Hugging the flanks and sweeping slightly back toward the dark umber wingtips
    wing_layers = [
        # (z, x0, x1, y0, y1, main_col, edge_col)
        (19, 5, 6, 8, 12, 2, 1),
        (18, 5, 7, 7, 13, 2, 1),
        (17, 6, 7, 7, 13, 2, 9),
        (16, 6, 8, 7, 13, 1, 2),
        (15, 6, 8, 6, 13, 1, 2),
        (14, 7, 8, 6, 13, 1, 4),
        (13, 7, 8, 6, 12, 1, 2),
        (12, 7, 8, 6, 12, 1, 4),
        (11, 7, 8, 5, 12, 4, 1),
        (10, 6, 8, 5, 11, 1, 4),
        (9,  6, 8, 5, 11, 4, 2),
        (8,  6, 7, 4, 10, 4, 1),
        (7,  5, 7, 4, 9,  4, 4),
        (6,  5, 6, 4, 8,  4, 4),
        (5,  4, 5, 4, 7,  4, 4),
    ]
    for z, x0, x1, y0, y1, mcol, ecol in wing_layers:
        fill_sym_box(grid, x0, x1, y0, y1, z, z, mcol)
        # Layered feather scallop highlight along outer/front covert edge
        fill_sym_box(grid, x1, x1, y1 - 1, y1, z, z, ecol)
        if z in (16, 13, 10):
            fill_sym_box(grid, x1, x1, y0 + 1, y1 - 2, z, z, 9)  # Crisp pale feather tips

    # --- BROAD REGAL OWL HEAD & HEART-SHAPED FACIAL DISC (Z: 21..30) ---
    head_profile = [
        (22, 5.4, 11.0, 4.1, 4.6),
        (23, 5.7, 11.1, 4.3, 4.9),
        (24, 5.9, 11.2, 4.4, 5.0),
        (25, 6.0, 11.2, 4.4, 5.0),
        (26, 6.0, 11.2, 4.4, 5.0),
        (27, 5.9, 11.2, 4.3, 4.9),
        (28, 5.6, 11.1, 4.1, 4.7),
        (29, 4.9, 11.0, 3.6, 4.1),
        (30, 3.8, 10.9, 2.8, 3.2),
    ]
    for z, rx, yc, ry_b, ry_f in head_profile:
        for x in range(X):
            dx = abs(x - cx)
            if dx > rx + 0.2:
                continue
            for y in range(Y):
                dy = y - yc
                ry = ry_f if dy >= 0 else ry_b
                if (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0:
                    if dy > 0.45 * ry_f and z <= 28:
                        col = 3  # Broad cream facial disc interior
                    elif z >= 29 and (int(round(dx)) % 2 == 0):
                        col = 2  # Tawny crown feather texture
                    elif dy < -0.5 * ry_b and z % 2 == 0:
                        col = 4  # Dark umber nape shading
                    else:
                        col = 1
                    grid[x, y, z] = col

    # Sculpted Heart-Shaped Cream Facial Disc Rim (Y: 15..16, Z: 22..29)
    fill_sym_box(grid, 0, 4, 15, 16, 23, 28, 3)   # Broad flat cream facial disc
    fill_sym_box(grid, 1, 4, 16, 16, 24, 28, 9)   # Bright pale cream spectacle face
    fill_sym_box(grid, 0, 2, 16, 16, 23, 24, 3)   # Lower facial disc curve
    # Dark umber outer facial disc border (heart/owl rim!)
    fill_sym_box(grid, 5, 5, 14, 15, 24, 28, 4)   # Side dark umber rim
    fill_sym_box(grid, 3, 4, 15, 16, 29, 29, 4)   # Upper brow arch
    fill_sym_box(grid, 0, 1, 16, 16, 28, 29, 4)   # Iconic V-dip brow between eyes!
    fill_sym_box(grid, 1, 2, 16, 16, 22, 22, 4)   # Lower chin disc rim

    # --- HUGE BRIGHT GOLDEN-AMBER OWL EYES (Z: 25..27, x_off: 1..3, Y: 16..17) ---
    # Large 3x3 golden-amber owl eyes popping proudly out of the pale facial disc!
    fill_sym_box(grid, 1, 3, 16, 17, 25, 27, 6)   # Huge 3x3 bright golden-amber iris
    fill_sym_box(grid, 2, 2, 17, 17, 26, 26, 7)   # Bold pitch-black pupil
    fill_sym_box(grid, 1, 1, 17, 17, 27, 27, 9)   # Crisp upper-inner eye glint!

    # --- CURVED WARM ORANGE OWL BEAK (x_off: 0, Y: 16..19, Z: 23..25) ---
    fill_sym_box(grid, 0, 0, 16, 18, 24, 25, 8)   # Upper beak bridge between eyes
    fill_sym_box(grid, 0, 0, 18, 19, 23, 24, 8)   # Hooked downward orange beak tip!
    fill_sym_box(grid, 0, 0, 17, 17, 23, 23, 4)   # Subtle under-beak shadow

    # --- REGAL TUFTED EAR-PLUMES (x_off: 3..6, Y: 12..15, Z: 29..33) ---
    fill_sym_box(grid, 3, 4, 12, 15, 29, 30, 1)
    fill_sym_box(grid, 4, 5, 12, 14, 30, 31, 1)
    fill_sym_box(grid, 4, 5, 13, 14, 31, 32, 2)   # Tawny inner tuft feathers
    fill_sym_box(grid, 5, 6, 12, 13, 32, 33, 4)   # Dark umber pointed ear-plume tips!

    # Hollow unseen body & head core to stay squarely in target range
    hollow_interior_26(grid, 4, 28)

    return grid


# ==========================================
# FORM B: WISE WINGED OWL ROBOT (44 x 24 x 43)
# ==========================================
def build_b():
    grid = np.zeros((44, 24, 43), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 21 (-X robot left)
    cx_r = X // 2      # 22 (+X robot right)

    # --- CLAWED ORANGE TALON MECHA FEET (Z: 0..3) ---
    # Heavy charcoal foot base + 3 bold orange clawed front talons + rear gripping talon!
    fill_sym_box(grid, 3, 5, 9, 14, 0, 1, 5)    # Charcoal foot chassis
    fill_sym_box(grid, 3, 5, 11, 15, 1, 2, 8)   # Orange armored foot instep
    # 3 distinct clawed forward talons
    fill_sym_box(grid, 2, 3, 14, 17, 0, 1, 8)   # Inner orange talon
    fill_sym_box(grid, 2, 2, 18, 18, 0, 0, 5)   # Inner sharp dark claw tip
    fill_sym_box(grid, 4, 4, 15, 18, 0, 1, 8)   # Center orange talon
    fill_sym_box(grid, 4, 4, 19, 19, 0, 0, 5)   # Center sharp dark claw tip
    fill_sym_box(grid, 5, 6, 14, 17, 0, 1, 8)   # Outer orange talon
    fill_sym_box(grid, 6, 6, 18, 18, 0, 0, 5)   # Outer sharp dark claw tip
    # Rear stabilizing orange talon heel spur
    fill_sym_box(grid, 4, 4, 7, 9, 0, 1, 8)
    fill_sym_box(grid, 4, 4, 6, 6, 0, 0, 5)
    # Feathered ankle collar & charcoal joint
    fill_sym_box(grid, 4, 5, 10, 13, 2, 3, 5)
    fill_sym_box(grid, 3, 5, 11, 13, 3, 3, 2)

    # --- STURDY FEATHER-ARMORED LEGS (Z: 4..20) ---
    # Shins (Z: 4..14)
    fill_sym_box(grid, 3, 5, 9, 13, 4, 13, 1)   # Woodland brown shin shell
    fill_sym_box(grid, 3, 5, 12, 14, 4, 12, 2)  # Soft tawny front greave plates
    fill_sym_box(grid, 4, 4, 14, 14, 5, 11, 3)  # Cream feathered front shin strip
    fill_sym_box(grid, 5, 5, 9, 12, 5, 11, 4)   # Dark umber outer feather ridge
    fill_sym_box(grid, 3, 3, 10, 12, 5, 12, 5)  # Inner charcoal hydraulics
    # Layered owl-feather knee guards with golden-amber knee gems
    fill_sym_box(grid, 3, 5, 13, 15, 12, 14, 1)
    fill_sym_box(grid, 4, 4, 15, 15, 12, 14, 4)
    fill_sym_box(grid, 4, 4, 15, 15, 13, 13, 6)  # Golden-amber knee crest

    # Thighs (Z: 14..19)
    fill_sym_box(grid, 3, 5, 10, 13, 14, 19, 3)  # Cream feathered thigh plates
    fill_sym_box(grid, 4, 5, 10, 11, 15, 18, 5)  # Charcoal rear thigh frame
    fill_sym_box(grid, 5, 5, 11, 13, 15, 18, 2)  # Tawny outer thigh armor
    fill_sym_box(grid, 4, 4, 13, 13, 16, 17, 1)  # Brown feather speckle accent

    # --- WAIST / PELVIS & REAR LAYERED TAIL-FEATHERS (Z: 19..23) ---
    fill_sym_box(grid, 0, 5, 9, 13, 20, 22, 5)   # Charcoal pelvic frame
    fill_sym_box(grid, 2, 5, 13, 14, 19, 22, 1)  # Front layered feather skirt plates
    fill_sym_box(grid, 2, 4, 14, 14, 20, 21, 2)  # Tawny skirt feather row
    fill_sym_box(grid, 5, 6, 10, 13, 19, 21, 4)  # Dark umber hip guards
    # Center pelvic crest
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 3)
    fill_sym_box(grid, 0, 1, 15, 15, 20, 21, 6)  # Golden-amber belt core
    fill_sym_box(grid, 0, 0, 15, 15, 19, 19, 8)  # Orange talon-chevron accent
    # Rear Layered Owl Tail-Coat Feathers (from Form A tail!)
    fill_sym_box(grid, 0, 3, 6, 9, 19, 21, 1)
    fill_sym_box(grid, 0, 3, 5, 7, 17, 19, 4)
    fill_sym_box(grid, 0, 2, 4, 6, 15, 17, 1)
    fill_sym_box(grid, 1, 2, 4, 5, 15, 19, 2)    # Tawny tail feather ribs

    # --- STURDY PLUMP SPECKLED OWL-BODY TORSO (Z: 22..33) - DIRECTLY FORM A'S BODY! ---
    # Lower chest / abdomen
    fill_sym_box(grid, 0, 4, 9, 14, 22, 24, 5)
    fill_sym_box(grid, 0, 3, 13, 15, 22, 24, 3)  # Cream owl belly continuation
    fill_sym_box(grid, 1, 2, 15, 15, 23, 23, 1)  # Brown belly speckle

    # Broad Sculpted Owl Chest Block (Z: 25..33)
    fill_sym_box(grid, 0, 6, 8, 15, 25, 32, 1)   # Woodland brown main torso shell
    fill_sym_box(grid, 0, 5, 9, 14, 26, 31, 0)   # Hollow unseen torso core
    # Prominent Plump Speckled Cream Owl Breastplate! (Y: 13..17, Z: 25..32)
    fill_sym_box(grid, 0, 5, 13, 16, 25, 31, 3)  # Cream breastplate
    fill_sym_box(grid, 0, 4, 15, 17, 26, 30, 3)  # Rounded plump owl chest curve
    fill_sym_box(grid, 0, 3, 16, 17, 31, 32, 9)  # Bright pale owl throat bib!
    # Unmistakable Owl Breast Feather Speckles & Chevron Markings!
    fill_sym_box(grid, 2, 3, 17, 17, 26, 26, 1)  # Woodland brown chest flecks
    fill_sym_box(grid, 1, 2, 17, 17, 28, 28, 2)  # Tawny chevron bar
    fill_sym_box(grid, 3, 4, 16, 17, 29, 29, 1)  # Outer brown breast fleck
    fill_sym_box(grid, 2, 3, 16, 17, 30, 30, 2)  # Upper tawny bar
    fill_sym_box(grid, 4, 5, 14, 16, 26, 27, 4)  # Dark umber side rib feathering
    # Wise Golden-Amber Owl Chest Reactor Core
    fill_sym_box(grid, 0, 1, 17, 17, 28, 29, 6)  # Glowing golden-amber core
    fill_sym_box(grid, 0, 1, 17, 17, 27, 27, 4)  # Dark umber collar frame
    # Layered Tawny Mantle Collar around shoulders/neck
    fill_sym_box(grid, 2, 6, 10, 14, 32, 33, 2)
    fill_sym_box(grid, 3, 5, 12, 15, 33, 33, 4)

    # --- DORSAL WING-PACK & SWEEPING FEATHERED BACK WINGS (Y: 4..9, Z: 19..40, x_off: 4..20) ---
    # Sturdy dorsal backpack housing the wing hinges
    fill_sym_box(grid, 0, 4, 6, 9, 25, 32, 4)
    fill_sym_box(grid, 0, 3, 5, 7, 26, 31, 1)
    fill_sym_box(grid, 0, 1, 5, 6, 27, 30, 2)    # Center back feather crest
    fill_sym_box(grid, 2, 3, 5, 6, 25, 26, 5)    # Twin stealth thrusters
    fill_sym_box(grid, 2, 3, 5, 5, 25, 25, 6)    # Amber thruster glow

    # Sweeping Feathered Back Wings unfolding dramatically outward & upward!
    # Sleek 2-voxel-thick aerodynamic wing blades tapering to 1-voxel sculpted feather tips!
    wing_columns = [
        # (x_off, y0, y1, z_bot, z_top, has_notch)
        (4,  6, 7, 27, 32, False),
        (5,  6, 7, 26, 33, False),
        (6,  6, 7, 25, 34, False),
        (7,  5, 6, 24, 35, False),
        (8,  5, 6, 23, 36, False),
        (9,  5, 6, 23, 36, False),
        (10, 5, 6, 22, 37, False),
        (11, 5, 6, 22, 38, False),
        (12, 5, 6, 24, 38, True),   # Stepped feathered silhouette along lower trailing edge
        (13, 5, 6, 23, 39, False),
        (14, 5, 6, 26, 39, True),
        (15, 5, 6, 25, 40, False),
        (16, 6, 6, 28, 40, True),
        (17, 6, 6, 27, 40, False),
        (18, 6, 6, 31, 40, True),
        (19, 6, 6, 32, 39, False),
        (20, 6, 6, 36, 38, False),  # Swept outermost primary feather tip!
    ]
    for xo, y0, y1, zb, zt, notch in wing_columns:
        # Fill full column in rich woodland brown
        fill_sym_box(grid, xo, xo, y0, y1, zb, zt, 1)
        # Upper leading edge: soft tawny coverts + pale feather highlight ridge
        fill_sym_box(grid, xo, xo, y0, y1, max(zb, zt - 3), zt, 2)
        if xo >= 7:
            fill_sym_box(grid, xo, xo, y1, y1, zt, zt, 9)  # Crisp pale upper wing ridge
        # Lower trailing primary feathers: dark umber tips with subtle feather striping
        tip_h = min(zt - 2, zb + 4)
        fill_sym_box(grid, xo, xo, y0, y1, zb, tip_h, 4)
        if not notch and xo >= 9:
            # Cream/tawny secondary feather band across mid-wing
            mid_z = (zb + zt) // 2 + 1
            fill_sym_box(grid, xo, xo, y0, y1, mid_z, mid_z, 3 if xo % 2 == 0 else 2)
            # Extending individual dark umber primary feather finger down 1-2 voxels
            fill_sym_box(grid, xo, xo, y0, y0, zb - 2, zb - 1, 4)

    # --- FEATHERED SHOULDER PAULDRONS & WING-BLADED FOREARMS (Z: 14..34) ---
    # Shoulder joint connectors
    fill_sym_box(grid, 6, 7, 10, 12, 29, 31, 5)
    # Layered Owl-Feather Shoulder Pauldrons (x_off: 7..11, Z: 28..34)
    fill_sym_box(grid, 7, 10, 9, 14, 28, 33, 1)   # Woodland brown pauldron
    fill_sym_box(grid, 8, 11, 10, 13, 32, 34, 2)  # Soft tawny upper feather tier
    fill_sym_box(grid, 10, 11, 10, 13, 28, 31, 4) # Dark umber outer feather edge
    fill_sym_box(grid, 8, 10, 14, 14, 29, 31, 3)  # Cream front pauldron trim
    fill_sym_box(grid, 11, 11, 11, 12, 33, 34, 9) # Pale feather tip accent

    # Articulated Dark Charcoal Upper Arms (Z: 23..27)
    fill_sym_box(grid, 8, 9, 10, 12, 23, 27, 5)
    fill_sym_box(grid, 8, 9, 12, 13, 24, 26, 2)   # Tawny bicep guard

    # ARMORED FEATHER-BLADED FOREARMS / ARM-WINGS (Z: 15..23, x_off: 8..13)
    # Main sturdy cream & brown bracer forearm
    fill_sym_box(grid, 8, 10, 10, 14, 17, 22, 1)
    fill_sym_box(grid, 8, 9, 13, 14, 18, 21, 3)   # Cream inner forearm cuff
    fill_sym_box(grid, 9, 10, 14, 14, 19, 20, 6)  # Golden-amber bracer gem
    # Sweeping Layered Feather-Wing Blades mounted on BOTH outer forearms!
    fill_sym_box(grid, 11, 11, 9, 14, 16, 23, 2)  # Upper tawny wing-blade tier
    fill_sym_box(grid, 12, 12, 9, 13, 15, 22, 1)  # Mid woodland brown feather-blade
    fill_sym_box(grid, 13, 13, 10, 13, 14, 20, 4) # Outer dark umber razor pinion blade!
    fill_sym_box(grid, 13, 13, 13, 14, 15, 19, 9) # Pale razor leading edge
    fill_sym_box(grid, 12, 12, 10, 11, 13, 14, 4) # Stepped lower feather blade tips
    fill_sym_box(grid, 11, 11, 11, 12, 14, 15, 4)

    # Articulated Charcoal Mecha Fists with Orange Knuckle Claws (Z: 15..16)
    fill_sym_box(grid, 8, 10, 11, 13, 15, 16, 5)
    fill_sym_box(grid, 8, 10, 13, 13, 15, 15, 8)  # Orange talon-knuckles

    # Right Forearm (+X, viewer's left): Extended Swept Pinion Feather-Sword Blade!
    # Attached cleanly to right fist/bracer (X = cx_r + 9..11 = 31..33, Y: 14..21)
    fill_box(grid, cx_r + 9, cx_r + 10, 14, 16, 15, 16, 5)   # Grip & guard
    fill_box(grid, cx_r + 10, cx_r + 11, 15, 16, 15, 17, 6)  # Golden-amber hilt crest
    fill_box(grid, cx_r + 10, cx_r + 11, 16, 20, 15, 17, 4)  # Dark umber feather-sword spine
    fill_box(grid, cx_r + 11, cx_r + 11, 16, 21, 15, 16, 9)  # Pale razor feather-edge
    fill_box(grid, cx_r + 10, cx_r + 10, 20, 22, 15, 16, 9)  # Pointed pinion tip
    fill_box(grid, cx_r + 10, cx_r + 11, 17, 19, 17, 17, 2)  # Tawny feather ridge

    # --- ICONIC HUGE-EYED OWL MECHA HEAD WITH FACIAL DISC & EAR TUFTS (Z: 33..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 13, 32, 33, 5)
    # Broad Wise Owl Helmet Cranium (x_off: 0..4 — generous width so HUGE owl eyes shine!)
    fill_sym_box(grid, 0, 4, 9, 14, 34, 39, 1)   # Woodland brown armored owl head
    fill_sym_box(grid, 0, 3, 10, 14, 39, 40, 2)  # Tawny crown dome
    fill_sym_box(grid, 0, 4, 9, 10, 35, 38, 4)   # Dark umber rear helmet plates

    # Broad Heart-Shaped Cream Facial Disc Faceplate (Y: 14..15, Z: 34..39)
    fill_sym_box(grid, 0, 3, 14, 15, 34, 38, 3)  # Cream facial disc
    fill_sym_box(grid, 1, 3, 15, 15, 35, 38, 9)  # Crisp bright pale spectacle faceplate
    # Dark umber spectacle rim & V-brow framing the huge owl eyes!
    fill_sym_box(grid, 4, 4, 13, 15, 35, 38, 4)  # Outer dark umber facial disc frame
    fill_sym_box(grid, 0, 0, 15, 15, 38, 39, 4)  # Wise central V-brow dip!
    fill_sym_box(grid, 1, 3, 14, 15, 39, 39, 4)  # Upper dark umber brow ridge
    fill_sym_box(grid, 1, 2, 15, 15, 34, 34, 4)  # Lower chin disc rim

    # ICONIC HUGE BRIGHT GOLDEN-AMBER OWL EYES! (3x3 per eye, Z: 36..38, x_off: 1..3, Y: 15..16)
    fill_sym_box(grid, 1, 3, 15, 16, 36, 38, 6)  # Huge luminous 3x3 golden-amber owl eyes!
    fill_sym_box(grid, 2, 2, 16, 16, 37, 37, 7)  # Piercing pitch-black pupils
    fill_sym_box(grid, 1, 1, 16, 16, 38, 38, 9)  # Crisp eye-glint highlight

    # Sculpted Curved Orange Owl Beak Crest between the lower inner eyes (Y: 16..17, Z: 34..36)
    fill_sym_box(grid, 0, 0, 15, 17, 35, 36, 8)  # Prominent warm orange owl beak!
    fill_sym_box(grid, 0, 0, 17, 17, 34, 35, 8)  # Hooked beak tip

    # Dramatic Sweeping Horned Owl Ear-Plume V-Fins (x_off: 3..6, Z: 39..42)
    fill_sym_box(grid, 3, 4, 12, 14, 39, 40, 1)
    fill_sym_box(grid, 4, 5, 12, 14, 40, 41, 2)  # Tawny ear-tuft sweep
    fill_sym_box(grid, 5, 6, 11, 13, 41, 42, 4)  # Dark umber pointed tuft tips!

    # Hollow strictly interior voxels across the whole model (preserves 6-connectivity!)
    hollow_interior_26(grid, 1, 40)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=34, pitch_a=20, yaw_b=30, pitch_b=20):
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
    v_a = export_vox(model_a, "owl_a.vox")
    v_b = export_vox(model_b, "owl_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: GREAT HORNED OWL -> WISE WINGED OWL ROBOT",
        "1. GREAT HORNED OWL",
        "2. WISE WINGED OWL ROBOT",
        "preview_owl.png",
        yaw_a=34, pitch_a=20, yaw_b=30, pitch_b=20,
    )
    print(f"owl: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
