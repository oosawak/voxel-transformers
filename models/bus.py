import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (206, 32, 42, 255),    # Iconic London Crimson Red
    2: (142, 20, 30, 255),    # Deep Burgundy / Armor Shadow Red
    3: (245, 236, 214, 255),  # Classic Cream / Ivory Stripe
    4: (36, 40, 48, 255),     # Charcoal Tire Rubber / Undercarriage
    5: (28, 48, 76, 255),     # Dark Tinted Window Glass
    6: (115, 218, 250, 255),  # Cyan Glass Highlight / Robot Visor
    7: (255, 212, 74, 255),   # Warm Amber Destination Sign / Headlights
    8: (192, 202, 216, 255),  # Chrome Silver Grille / Rims / Handrails
    9: (102, 112, 128, 255),  # Gunmetal Steel Chassis / Joints
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


def fill_sym_wheel(grid, x_off0, x_off1, yc, zc, radius, tire_col=4, rim_col=8, hub_col=9):
    """Build a crisp symmetrical rubber tire with chrome/gunmetal rim on the YZ plane."""
    r2 = radius * radius + 0.35
    y0, y1 = int(np.floor(yc - radius)), int(np.ceil(yc + radius))
    z0, z1 = int(np.floor(zc - radius)), int(np.ceil(zc + radius))
    for y in range(y0, y1 + 1):
        for z in range(z0, z1 + 1):
            d2 = (y - yc) ** 2 + (z - zc) ** 2
            if d2 <= r2:
                fill_sym_box(grid, x_off0, x_off1, y, y, z, z, tire_col)
                if d2 <= (radius * 0.56) ** 2:
                    fill_sym_box(grid, x_off1, x_off1, y, y, z, z, hub_col)
                if d2 <= (radius * 0.32) ** 2:
                    fill_sym_box(grid, x_off1, x_off1, y, y, z, z, rim_col)


# ==========================================
# FORM A: DOUBLE-DECKER BUS (14 x 34 x 18)
# ==========================================
def build_a():
    grid = np.zeros((14, 34, 18), dtype=np.uint8)

    # --- UNDERCARRIAGE & CHASSIS (Z: 1..2) ---
    fill_sym_box(grid, 0, 4, 2, 31, 2, 2, 4)
    fill_sym_box(grid, 0, 3, 4, 29, 1, 1, 9)
    # Axle beams connecting left/right wheel hubs
    for wy in (7, 25):
        fill_sym_box(grid, 0, 4, wy, wy, 1, 2, 9)

    # --- MAIN DOUBLE-DECKER BODY SHELL (Y: 2..31, Z: 2..15) ---
    fill_sym_box(grid, 0, 5, 2, 31, 2, 15, 1)
    # Hollow interior to keep voxel count clean & efficient
    fill_sym_box(grid, 0, 4, 3, 30, 3, 14, 0)

    # --- CURVED ROOF (Z: 15..17) ---
    fill_sym_box(grid, 0, 4, 3, 30, 16, 16, 1)
    fill_sym_box(grid, 0, 2, 5, 28, 16, 16, 0)  # Hollow interior while keeping roof crown 6-connected
    fill_sym_box(grid, 0, 3, 4, 29, 17, 17, 2)  # Deep red roof crown
    # Roof bevel trim & twin silver vents
    fill_sym_box(grid, 4, 4, 3, 30, 16, 16, 2)
    fill_sym_box(grid, 0, 1, 9, 11, 17, 17, 8)
    fill_sym_box(grid, 0, 1, 21, 23, 17, 17, 8)

    # --- ICONIC CREAM/WHITE MID-DECK STRIPE (Z: 9) ---
    fill_sym_box(grid, 5, 5, 2, 31, 9, 9, 3)
    fill_sym_box(grid, 0, 5, 31, 31, 9, 9, 3)
    fill_sym_box(grid, 0, 5, 2, 2, 9, 9, 3)
    # Subtle cream roof-edge pinstripe
    fill_sym_box(grid, 5, 5, 3, 30, 15, 15, 3)

    # --- LOWER DECK SIDE WINDOWS (Z: 5..7) ---
    for wy in (10, 14, 18, 22, 26):
        fill_sym_box(grid, 5, 5, wy, wy + 2, 5, 7, 5)
        fill_sym_box(grid, 5, 5, wy + 1, wy + 2, 7, 7, 6)
        fill_sym_box(grid, 5, 5, wy + 2, wy + 2, 6, 6, 6)
    # Driver cab side window
    fill_sym_box(grid, 5, 5, 29, 30, 5, 7, 5)
    fill_sym_box(grid, 5, 5, 30, 30, 7, 7, 6)

    # --- UPPER DECK SIDE WINDOWS (Z: 11..13) ---
    for wy in (4, 8, 12, 16, 20, 24, 28):
        fill_sym_box(grid, 5, 5, wy, wy + 2, 11, 13, 5)
        fill_sym_box(grid, 5, 5, wy + 1, wy + 2, 13, 13, 6)
        fill_sym_box(grid, 5, 5, wy + 2, wy + 2, 12, 12, 6)

    # --- FRONT FACE (+Y, Y: 31..32) ---
    # Chrome front bumper & lower apron
    fill_sym_box(grid, 0, 5, 32, 32, 2, 2, 8)
    fill_sym_box(grid, 4, 5, 32, 32, 2, 2, 4)
    # Classic front radiator grille (centered, silver/charcoal slats)
    fill_sym_box(grid, 0, 2, 32, 32, 3, 5, 8)
    fill_sym_box(grid, 0, 1, 32, 32, 4, 4, 4)
    fill_sym_box(grid, 0, 2, 31, 31, 3, 5, 4)
    # Round glowing headlights with chrome bezel
    fill_sym_box(grid, 4, 4, 32, 32, 4, 4, 7)
    fill_sym_box(grid, 3, 3, 31, 31, 4, 4, 8)
    # Wide lower deck front windshield (Z: 6..8)
    fill_sym_box(grid, 0, 4, 31, 31, 6, 8, 5)
    fill_sym_box(grid, 1, 3, 31, 31, 8, 8, 6)
    fill_sym_box(grid, 2, 3, 31, 31, 7, 7, 6)
    fill_sym_box(grid, 0, 0, 31, 31, 6, 8, 4)  # Center windshield divider
    # Glowing amber destination display above lower windshield (Z: 9..10)
    fill_sym_box(grid, 0, 3, 31, 31, 9, 10, 4)
    fill_sym_box(grid, 0, 2, 31, 31, 9, 10, 7)
    fill_sym_box(grid, 0, 2, 32, 32, 9, 10, 7)
    fill_sym_box(grid, 3, 3, 32, 32, 9, 10, 4)
    # Wide upper deck panoramic windshield (Z: 12..14)
    fill_sym_box(grid, 0, 4, 31, 31, 12, 14, 5)
    fill_sym_box(grid, 1, 3, 31, 31, 14, 14, 6)
    fill_sym_box(grid, 2, 3, 31, 31, 13, 13, 6)
    fill_sym_box(grid, 0, 0, 31, 31, 12, 14, 1)  # Upper divider pillar
    # Side wing mirrors
    fill_sym_box(grid, 6, 6, 30, 30, 6, 8, 4)
    fill_sym_box(grid, 6, 6, 30, 30, 7, 7, 8)

    # --- REAR DECK, OPEN BOARDING PLATFORM & STAIR DETAIL (-Y, Y: 1..6) ---
    # Rear chrome bumper & tail lights
    fill_sym_box(grid, 0, 5, 1, 1, 2, 2, 8)
    fill_sym_box(grid, 4, 4, 2, 2, 4, 5, 7)  # Amber indicator
    fill_sym_box(grid, 4, 4, 2, 2, 3, 3, 2)  # Deep red tail light
    # Upper rear panoramic window
    fill_sym_box(grid, 0, 4, 2, 2, 11, 13, 5)
    fill_sym_box(grid, 1, 3, 2, 2, 13, 13, 6)
    # Open Routemaster rear boarding platform on -X side (x: 1..6, y: 2..6, z: 3..8)
    fill_box(grid, 1, 6, 2, 6, 3, 8, 0)
    fill_box(grid, 1, 6, 2, 6, 2, 2, 4)  # Boarding deck floor
    fill_box(grid, 1, 6, 2, 6, 9, 9, 2)  # Deck ceiling / upper floor support
    fill_box(grid, 1, 6, 7, 7, 3, 8, 2)  # Interior cabin bulkhead wall
    fill_box(grid, 7, 7, 2, 7, 3, 8, 2)  # Center partition wall
    # Chrome boarding handrail pole
    fill_box(grid, 2, 2, 3, 3, 3, 8, 8)
    # Interior ascending staircase steps inside the open rear deck
    for step in range(4):
        fill_box(grid, 4 + (step // 2), 6, 3 + step, 3 + step, 3 + step, 4 + step, 9)
        fill_box(grid, 4 + (step // 2), 6, 3 + step, 3 + step, 4 + step, 4 + step, 3)
    # Rear-right enclosed stairwell small window
    fill_box(grid, 8, 11, 2, 2, 5, 7, 5)
    fill_box(grid, 9, 10, 2, 2, 7, 7, 6)

    # --- 4 RUBBER TIRES WITH SILVER RIMS (front Y=25, rear Y=7) ---
    for wy in (7, 25):
        # Sculpt neat wheel wells into lower skirt
        fill_sym_box(grid, 4, 5, wy - 2, wy + 2, 2, 4, 0)
        fill_sym_box(grid, 5, 5, wy - 2, wy + 2, 5, 5, 2)  # Wheel arch brow
        fill_sym_wheel(grid, 4, 5, yc=wy, zc=2, radius=2.1, tire_col=4, rim_col=8, hub_col=9)

    return grid


# ==========================================
# FORM B: DOUBLE-DECKER GUARDIAN ROBOT (32 x 22 x 40)
# ==========================================
def build_b():
    grid = np.zeros((32, 22, 40), dtype=np.uint8)

    # --- FEET (Z: 0..2) - Grounded Bus Chassis & Bumper Toes ---
    fill_sym_box(grid, 3, 6, 6, 15, 0, 1, 4)       # Charcoal rubber sole
    fill_sym_box(grid, 3, 6, 12, 16, 1, 2, 1)      # Crimson toe armor
    fill_sym_box(grid, 4, 5, 16, 16, 1, 1, 8)      # Chrome bumper toe tip
    fill_sym_box(grid, 3, 5, 5, 7, 0, 2, 9)        # Gunmetal heel brace
    fill_sym_box(grid, 3, 6, 8, 12, 2, 2, 9)       # Ankle joint collar

    # --- LOWER LEGS / SHINS (Z: 3..13) + REAR TIRE ANKLE PODS ---
    fill_sym_box(grid, 3, 6, 8, 13, 3, 13, 1)      # Solid crimson lower leg armor
    fill_sym_box(grid, 4, 5, 9, 12, 4, 12, 0)      # Hollow shin core
    fill_sym_box(grid, 3, 3, 8, 13, 3, 13, 2)      # Inner burgundy bevel
    fill_sym_box(grid, 3, 6, 8, 8, 4, 12, 4)       # Rear chassis backing
    fill_sym_box(grid, 4, 5, 7, 7, 5, 11, 9)       # Rear calf damper struts
    # Cream bus stripe along outer shin
    fill_sym_box(grid, 6, 6, 11, 11, 6, 12, 3)
    # Chrome Radiator Grille Knee-Guards (Z: 10..14, Y: 14..15)
    fill_sym_box(grid, 3, 6, 13, 14, 10, 14, 1)    # Crimson knee guard housing
    fill_sym_box(grid, 4, 5, 14, 15, 11, 13, 8)    # Chrome radiator grille face
    fill_sym_box(grid, 4, 5, 15, 15, 12, 12, 4)    # Grille horizontal louver slot
    fill_sym_box(grid, 6, 6, 14, 14, 12, 12, 7)    # Amber corner marker light
    # Rear 2 bus tires mounted as bold outer ankle wheel pods!
    fill_sym_box(grid, 6, 7, 10, 11, 4, 5, 9)      # Wheel pod axle mount
    fill_sym_wheel(grid, 7, 8, yc=10.5, zc=4.5, radius=2.3, tire_col=4, rim_col=8, hub_col=9)

    # --- THIGHS (Z: 14..18) ---
    fill_sym_box(grid, 3, 5, 9, 12, 14, 18, 9)     # Gunmetal inner thigh frame
    fill_sym_box(grid, 3, 5, 12, 13, 15, 17, 3)    # Cream front thigh armor plate
    fill_sym_box(grid, 3, 5, 9, 9, 15, 17, 4)      # Rear charcoal thigh guard
    fill_sym_box(grid, 5, 5, 10, 11, 15, 17, 2)    # Outer burgundy trim

    # --- WAIST / PELVIS (Z: 18..21) ---
    fill_sym_box(grid, 0, 5, 8, 13, 18, 20, 4)     # Charcoal pelvis block
    fill_sym_box(grid, 0, 5, 8, 13, 21, 21, 9)     # Gunmetal waist joint
    # Front waist skirts & belt
    fill_sym_box(grid, 2, 5, 13, 14, 18, 20, 1)    # Crimson front skirt plates
    fill_sym_box(grid, 1, 5, 14, 14, 20, 20, 3)    # Cream waist belt trim
    fill_sym_box(grid, 0, 1, 13, 15, 18, 21, 2)    # Central burgundy groin armor
    fill_sym_box(grid, 0, 0, 15, 15, 19, 20, 8)    # Chrome belt buckle
    fill_sym_box(grid, 0, 0, 15, 15, 20, 20, 7)    # Amber buckle emblem
    # Side hip skirts
    fill_sym_box(grid, 6, 6, 9, 12, 18, 20, 1)
    fill_sym_box(grid, 6, 6, 10, 11, 19, 19, 3)

    # --- TORSO / CHEST (Z: 22..32) - THE DOUBLE-DECKER BUS BODY! ---
    fill_sym_box(grid, 0, 5, 7, 14, 22, 32, 1)     # Broad boxy crimson bus torso (12 wide)
    fill_sym_box(grid, 0, 4, 8, 13, 23, 31, 0)     # Hollow unseen torso core
    # Burgundy roof brow & lower chest base
    fill_sym_box(grid, 0, 5, 7, 14, 32, 32, 2)
    fill_sym_box(grid, 0, 4, 14, 15, 22, 31, 1)    # Projecting chest facade

    # Lower chest bumper, chrome radiator grille & glowing headlights (Z: 22)
    fill_sym_box(grid, 0, 5, 15, 15, 22, 22, 8)    # Chrome bumper bar
    fill_sym_box(grid, 0, 2, 15, 15, 22, 22, 4)    # Mini grille recess
    fill_sym_box(grid, 0, 1, 15, 15, 22, 22, 8)    # Chrome grille bars
    fill_sym_box(grid, 4, 4, 15, 15, 22, 22, 7)    # Glowing round headlights!

    # Lower row of iconic bus windows across chest (Z: 23..24)
    for x0, x1 in ((0, 1), (3, 4)):
        fill_sym_box(grid, x0, x1, 15, 15, 23, 24, 5)
        fill_sym_box(grid, x1, x1, 15, 15, 24, 24, 6)
    fill_sym_box(grid, 0, 0, 15, 15, 24, 24, 6)

    # Crisp uninterrupted Cream horizontal band wrapping chest & sides (Z: 25)
    fill_sym_box(grid, 0, 5, 7, 15, 25, 25, 3)
    # Glowing Amber Destination Sign prominently above the cream band (Z: 26..27)
    fill_sym_box(grid, 0, 3, 15, 15, 26, 27, 4)    # Dark sign housing
    fill_sym_box(grid, 0, 2, 15, 16, 26, 27, 7)    # Glowing amber destination box!

    # Upper row of iconic bus windows across chest (Z: 29..30)
    for x0, x1 in ((0, 1), (3, 4)):
        fill_sym_box(grid, x0, x1, 15, 15, 29, 30, 5)
        fill_sym_box(grid, x1, x1, 15, 15, 30, 30, 6)
    fill_sym_box(grid, 0, 0, 15, 15, 30, 30, 6)

    # Side torso bus windows for 360-degree transformation authenticity
    fill_sym_box(grid, 5, 5, 9, 12, 23, 24, 5)
    fill_sym_box(grid, 5, 5, 11, 12, 24, 24, 6)
    fill_sym_box(grid, 5, 5, 9, 12, 29, 30, 5)
    fill_sym_box(grid, 5, 5, 11, 12, 30, 30, 6)

    # --- BACKPACK (Y: 4..6, Z: 22..33) - Rear Deck & Stairwell Pack ---
    fill_sym_box(grid, 0, 4, 4, 6, 22, 31, 2)      # Burgundy rear deck pack
    fill_sym_box(grid, 0, 3, 5, 5, 23, 30, 0)      # Hollow backpack interior
    fill_sym_box(grid, 0, 4, 4, 4, 25, 25, 3)      # Cream wraparound stripe
    fill_sym_box(grid, 0, 3, 4, 4, 28, 30, 5)      # Rear upper bus window
    fill_sym_box(grid, 1, 2, 4, 4, 30, 30, 6)
    # Chrome rear-deck handrail bars & twin roof-vent exhaust stacks
    fill_sym_box(grid, 2, 2, 3, 4, 23, 29, 8)
    fill_sym_box(grid, 0, 1, 3, 4, 23, 25, 9)
    fill_sym_box(grid, 4, 4, 4, 4, 23, 24, 7)      # Rear amber tail markers
    fill_sym_box(grid, 3, 4, 5, 6, 31, 34, 9)      # Twin gunmetal stacks
    fill_sym_box(grid, 3, 4, 5, 6, 34, 35, 8)      # Chrome stack tips

    # --- BOLD TIRE SHOULDER-PAULDRONS (Z: 27..34) ---
    # Heavy shoulder joint bridge connecting torso to tire shoulders
    fill_sym_box(grid, 6, 7, 9, 12, 28, 31, 4)
    fill_sym_box(grid, 6, 7, 10, 11, 29, 30, 9)
    # Iconic large round bus tires as bold shoulder-pauldrons!
    fill_sym_wheel(grid, 8, 10, yc=10.5, zc=30.5, radius=2.9, tire_col=4, rim_col=8, hub_col=9)
    # Sleek crimson bus-fender epaulette on inner-top shoulder, leaving outer tire arc bold & round
    fill_sym_box(grid, 6, 8, 9, 12, 33, 34, 1)
    fill_sym_box(grid, 6, 8, 12, 12, 34, 34, 3)    # Cream epaulette piping

    # --- ARMS & FOREARMS (Z: 15..27) ---
    # Upper arms (gunmetal/charcoal piston limbs descending from tire shoulders)
    fill_sym_box(grid, 8, 9, 9, 12, 23, 27, 9)
    fill_sym_box(grid, 8, 9, 10, 11, 24, 26, 4)
    # Sturdy crimson double-decker forearm gauntlets
    fill_sym_box(grid, 7, 10, 9, 13, 17, 22, 1)
    fill_sym_box(grid, 8, 9, 10, 12, 18, 21, 0)    # Hollow forearm core
    fill_sym_box(grid, 7, 10, 9, 13, 18, 18, 3)    # Cream wrist cuff band
    fill_sym_box(grid, 10, 10, 10, 12, 20, 21, 5)  # Outer mini bus-window armor
    fill_sym_box(grid, 10, 10, 11, 12, 21, 21, 6)
    fill_sym_box(grid, 7, 10, 13, 13, 19, 21, 2)   # Burgundy front gauntlet plate
    # Articulated charcoal fists
    fill_sym_box(grid, 8, 9, 10, 12, 15, 16, 4)
    fill_sym_box(grid, 8, 9, 12, 12, 15, 16, 9)

    # --- GENTLEMAN-GUARDIAN EQUIPMENT ---
    # Left Forearm (-X, x=4..6): Bus-Panel Tower Shield with cream stripe & window slot
    fill_box(grid, 4, 5, 10, 15, 15, 24, 1)
    fill_box(grid, 6, 6, 11, 12, 19, 21, 9)        # Solid mount to left forearm
    fill_box(grid, 4, 4, 10, 15, 19, 19, 3)        # Cream horizontal bus stripe
    fill_box(grid, 4, 4, 11, 14, 21, 22, 5)        # Shield viewport window
    fill_box(grid, 4, 4, 13, 14, 22, 22, 6)
    fill_box(grid, 4, 5, 10, 15, 24, 24, 2)        # Burgundy top edge
    fill_box(grid, 4, 5, 10, 15, 15, 15, 8)        # Chrome lower rim

    # Right Hand (+X, x=24..25): High-contrast Chrome & Amber Guardian Baton
    fill_box(grid, 24, 25, 13, 20, 15, 16, 8)      # Chrome baton shaft
    fill_box(grid, 24, 25, 13, 14, 15, 16, 4)      # Charcoal grip guard
    fill_box(grid, 24, 25, 19, 21, 15, 16, 7)      # Glowing amber beacon head
    fill_box(grid, 24, 25, 18, 18, 15, 16, 9)      # Gunmetal collar ring

    # --- HEAD (Z: 33..39) - Bus-Roof Crest Gentleman-Guardian Head ---
    fill_sym_box(grid, 0, 1, 9, 12, 32, 33, 4)     # Sturdy neck
    fill_sym_box(grid, 0, 2, 8, 13, 34, 37, 1)     # Crimson helmet
    fill_sym_box(grid, 3, 3, 10, 11, 35, 36, 3)    # Cream ear/side-visor pods
    # Chrome faceplate & glowing cyan guardian visor
    fill_sym_box(grid, 0, 1, 13, 14, 34, 34, 8)    # Silver chin / faceplate
    fill_sym_box(grid, 0, 1, 13, 14, 35, 36, 6)    # Glowing cyan visor eyes
    fill_sym_box(grid, 2, 2, 13, 13, 35, 36, 2)    # Cheek guards
    # Classic Bus-Roof Crest (layered roof dome + cream brow band + amber crest beacon)
    fill_sym_box(grid, 0, 2, 9, 14, 37, 37, 3)     # Crisp cream roof-brim band
    fill_sym_box(grid, 0, 2, 9, 13, 38, 38, 2)     # Burgundy bus-roof dome
    fill_sym_box(grid, 0, 0, 10, 14, 38, 39, 1)    # Central crimson crest fin
    fill_sym_box(grid, 0, 0, 14, 14, 38, 39, 7)    # Amber roof-crest emblem

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=40, pitch_a=22, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "bus_a.vox")
    v_b = export_vox(model_b, "bus_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: DOUBLE-DECKER BUS -> DOUBLE-DECKER GUARDIAN ROBOT",
        "1. DOUBLE-DECKER BUS",
        "2. DOUBLE-DECKER GUARDIAN ROBOT",
        "preview_bus.png",
        yaw_a=40, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"bus: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
