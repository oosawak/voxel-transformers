import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 246, 250, 255),  # Crisp Vending Machine White (Cabinet, Torso, Armor)
    2: (220, 36, 46, 255),    # Vivid Soda-Can Crimson Red (Side/Top Branding, Cola Cans)
    3: (92, 206, 246, 255),   # Cool Ice-Blue (Glass Glint, Cold Sports Drinks, Visor)
    4: (42, 46, 56, 255),     # Dark Charcoal (Dispenser Recess, Joints, Vent Louvers)
    5: (176, 186, 200, 255),  # Silver Chrome (Coin Slot, Shelves, Metal Trim, Cannon)
    6: (252, 168, 32, 255),   # Vibrant Citrus Orange/Yellow (Juice Cans, LED Price Display)
    7: (46, 182, 88, 255),    # Refreshing Emerald Green (Green Tea Cans, Indicators)
    8: (34, 54, 96, 255),     # Deep Navy (Display Backing, Button Strip, Shading)
    9: (255, 248, 214, 255),  # Glowing Warm-White (Showcase Backlight, Top Marquee)
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


# ==========================================
# FORM A: JAPANESE BEVERAGE VENDING MACHINE (18 x 12 x 28)
# ==========================================
def build_a():
    grid = np.zeros((18, 12, 28), dtype=np.uint8)

    # --- BASE PLINTH & LEVELING FEET (Z: 0..1) ---
    fill_sym_box(grid, 6, 7, 2, 3, 0, 1, 4)    # Rear corner leveling feet
    fill_sym_box(grid, 6, 7, 8, 9, 0, 1, 4)    # Front corner leveling feet
    fill_sym_box(grid, 0, 7, 2, 9, 1, 1, 4)    # Dark charcoal recessed base skirt
    fill_sym_box(grid, 0, 6, 3, 8, 1, 1, 0)    # Hollow base underside
    fill_sym_box(grid, 0, 7, 9, 9, 1, 1, 5)    # Front chrome base kickplate

    # --- MAIN HOLLOW CABINET SHELL (X: 1..16, Y: 1..10, Z: 2..26) ---
    fill_box(grid, 1, 16, 1, 10, 2, 26, 1)
    # Hollow interior cleanly so voxel budget stays crisp!
    fill_box(grid, 2, 15, 2, 9, 3, 25, 0)

    # Vivid Crimson Red Side Panels (left & right cabinet walls)
    fill_box(grid, 1, 1, 2, 9, 2, 26, 2)
    fill_box(grid, 16, 16, 2, 9, 2, 26, 2)
    # Crisp white horizontal brand stripes along both red side walls
    fill_box(grid, 1, 1, 3, 8, 13, 14, 1)
    fill_box(grid, 16, 16, 3, 8, 13, 14, 1)
    fill_box(grid, 1, 1, 4, 7, 23, 23, 9)
    fill_box(grid, 16, 16, 4, 7, 23, 23, 9)
    # Lower side service vent louvers
    for vz in (4, 6):
        fill_box(grid, 1, 1, 3, 7, vz, vz, 4)
        fill_box(grid, 16, 16, 3, 7, vz, vz, 4)

    # Rear Service Panel Details (Y: 1, visible in Rear View)
    fill_box(grid, 2, 15, 1, 1, 2, 26, 1)
    fill_box(grid, 2, 2, 1, 1, 2, 26, 2)
    fill_box(grid, 15, 15, 1, 1, 2, 26, 2)
    # Rear compressor ventilation louvers & power junction box
    fill_box(grid, 4, 13, 1, 1, 3, 8, 4)
    for vz in (4, 6, 7):
        fill_box(grid, 5, 12, 1, 1, vz, vz, 5)
    fill_box(grid, 5, 12, 1, 1, 12, 22, 5)
    fill_box(grid, 6, 11, 1, 1, 13, 21, 1)
    fill_box(grid, 13, 14, 1, 1, 10, 11, 4)  # Power cord box

    # --- TOP ILLUMINATED HEADER CANOPY & ROOF UNIT (Z: 25..27) ---
    fill_box(grid, 1, 16, 1, 10, 25, 26, 2)     # Vivid red top fascia
    fill_box(grid, 2, 15, 2, 9, 25, 25, 0)      # Keep interior hollow
    fill_box(grid, 1, 16, 10, 11, 25, 26, 2)    # Overhanging front marquee brow
    fill_box(grid, 3, 14, 11, 11, 25, 25, 9)    # Glowing warm-white marquee light
    fill_box(grid, 5, 6, 11, 11, 25, 25, 2)     # Red brand logo accent on marquee
    fill_box(grid, 11, 12, 11, 11, 25, 25, 3)   # Cool ice-blue "COLD" logo accent
    # Top roof condenser housing
    fill_box(grid, 4, 13, 3, 8, 27, 27, 5)
    fill_box(grid, 5, 12, 4, 7, 27, 27, 4)

    # --- RECESSED ILLUMINATED GLASS DISPLAY SHOWCASE (X: 2..15, Y: 7..10, Z: 13..24) ---
    # Open the front face (Y: 10) for the showcase window
    fill_box(grid, 3, 14, 10, 10, 13, 23, 0)
    # Recessed bright warm-white backlight wall at Y: 7
    fill_box(grid, 2, 15, 7, 7, 13, 24, 9)
    # Inner showcase side & ceiling/floor walls (Y: 8..9) so no gaps into hollow interior
    fill_box(grid, 2, 2, 8, 9, 13, 24, 5)
    fill_box(grid, 15, 15, 8, 9, 13, 24, 5)
    fill_box(grid, 2, 15, 8, 9, 24, 24, 9)
    fill_box(grid, 2, 15, 8, 9, 12, 12, 8)

    # Silver Chrome Showcase Frame & Cool Ice-Blue Glass Corner Glints (Y: 10)
    fill_box(grid, 2, 15, 10, 10, 24, 24, 5)
    fill_box(grid, 2, 2, 10, 10, 13, 23, 5)
    fill_box(grid, 15, 15, 10, 10, 13, 23, 5)
    # Diagonal cool ice-blue glass glint bars at top corners (keeps drinks clearly visible!)
    fill_box(grid, 13, 14, 10, 10, 23, 23, 3)
    fill_box(grid, 14, 14, 10, 10, 22, 22, 3)
    fill_box(grid, 3, 4, 10, 10, 23, 23, 3)

    # 3 HORIZONTAL DISPLAY SHELVES + COLORFUL ROWS OF DRINKS!
    # 6 crisp vibrant drinks per row across X = 3, 5, 7, 10, 12, 14
    shelf_configs = [
        (21, [(3, 2), (5, 2), (7, 3), (10, 3), (12, 7), (14, 6)]),  # Top: Cola, Sports, Tea, Juice
        (17, [(3, 3), (5, 7), (7, 7), (10, 6), (12, 2), (14, 2)]),  # Mid: Sports, Tea, Juice, Cola
        (13, [(3, 6), (5, 6), (7, 2), (10, 7), (12, 3), (14, 2)]),  # Bot: Hot/Cold mix
    ]
    for sz, drinks in shelf_configs:
        fill_box(grid, 3, 14, 8, 9, sz, sz, 5)   # Silver shelf deck
        fill_box(grid, 3, 14, 10, 10, sz, sz, 8) # Deep navy selection button strip
        for dx, dcol in drinks:
            # 2-voxel-tall drink can/bottle standing on shelf (Y: 8..9, Z: sz+1..sz+2)
            fill_box(grid, dx, dx, 8, 9, sz + 1, sz + 2, dcol)
            fill_box(grid, dx, dx, 9, 9, sz + 2, sz + 2, 5 if sz == 17 else dcol)
            # Glowing selection push-button directly below each drink!
            btn_col = 3 if dcol in (3, 7) else (2 if dcol == 2 else 6)
            fill_box(grid, dx, dx, 10, 10, sz, sz, btn_col)

    # --- MIDDLE CONTROL PANEL: COIN SLOT, BILL ACCEPTOR, LED PRICE & BRAND PANEL (Z: 8..12, Y: 10) ---
    fill_box(grid, 2, 15, 10, 10, 8, 12, 1)  # Crisp white front panel
    # Left/Viewer's-Left (+X: X=9..14): Iconic Vivid Red Soda-Can Brand Graphic
    fill_box(grid, 9, 14, 10, 10, 9, 11, 2)
    fill_box(grid, 10, 13, 10, 10, 10, 10, 1)  # White wave stripe
    fill_box(grid, 11, 12, 10, 10, 10, 10, 9)  # Highlight gleam
    # Right/Viewer's-Right (-X: X=3..7): Dark Control Bezel, Orange LED Display, Silver Coin/Bill Slots
    fill_box(grid, 3, 7, 10, 10, 8, 12, 4)
    fill_box(grid, 4, 6, 10, 10, 11, 11, 6)  # Glowing Citrus Orange LED Price Display ("130")
    fill_box(grid, 6, 6, 10, 10, 9, 10, 5)   # Silver Chrome Coin Slot
    fill_box(grid, 4, 5, 10, 10, 10, 10, 5)  # Silver Bill Acceptor Trim
    fill_box(grid, 4, 5, 10, 10, 9, 9, 8)    # Bill Slot Slit
    fill_box(grid, 3, 3, 10, 10, 8, 9, 5)    # Coin Return Lever & Pocket

    # --- WIDE RECESSED DARK PICKUP DISPENSER SLOT (取り出し口) (X: 3..14, Y: 7..10, Z: 3..7) ---
    fill_box(grid, 3, 14, 10, 10, 4, 6, 0)    # Open dispenser bay on front face
    fill_box(grid, 3, 14, 7, 7, 4, 6, 4)      # Back wall of dispenser slot
    fill_box(grid, 3, 14, 7, 9, 3, 3, 4)      # Bottom pickup tray
    fill_box(grid, 3, 14, 7, 9, 7, 7, 4)      # Ceiling of dispenser bay
    fill_box(grid, 2, 2, 7, 9, 3, 7, 4)       # Right inner sidewall
    fill_box(grid, 15, 15, 7, 9, 3, 7, 4)     # Left inner sidewall
    # Deep navy hinged push-flap inside upper dispenser opening
    fill_box(grid, 4, 13, 8, 9, 6, 6, 8)
    fill_box(grid, 5, 12, 9, 9, 6, 6, 5)      # Chrome flap handle bar
    # A freshly dispensed red cola can resting inside the pickup tray!
    fill_box(grid, 8, 10, 8, 9, 4, 4, 2)
    fill_box(grid, 10, 10, 8, 9, 4, 4, 5)     # Can lid
    # Crisp silver chrome outer bezel framing the Pickup Dispenser Slot
    fill_box(grid, 2, 15, 10, 10, 3, 3, 5)
    fill_box(grid, 2, 15, 10, 10, 7, 7, 5)
    fill_box(grid, 2, 2, 10, 10, 4, 6, 5)
    fill_box(grid, 15, 15, 10, 10, 4, 6, 5)
    # Red lower front skirt stripe beneath dispenser
    fill_box(grid, 2, 15, 10, 10, 2, 2, 2)

    return grid


# ==========================================
# FORM B: VENDING MACHINE ROBOT (32 x 22 x 42)
# ==========================================
def build_b():
    grid = np.zeros((32, 22, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 15 (-X robot left)
    cx_r = grid.shape[0] // 2      # 16 (+X robot right)

    # --- FEET & STURDY BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 7, 15, 0, 1, 4)   # Dark charcoal rubber base soles
    fill_sym_box(grid, 3, 6, 7, 9, 0, 2, 5)    # Chrome heel stabilizer
    fill_sym_box(grid, 3, 6, 10, 16, 1, 2, 1)  # Crisp white armored boot body
    fill_sym_box(grid, 4, 5, 13, 17, 1, 2, 2)  # Vivid crimson toe caps
    fill_sym_box(grid, 4, 5, 14, 16, 3, 3, 5)  # Silver ankle bridge

    # --- BLOCKY CABINET-PANEL LOWER LEGS / SHINS (Z: 4..14) ---
    fill_sym_box(grid, 3, 6, 8, 14, 4, 14, 1)
    fill_sym_box(grid, 4, 5, 9, 13, 5, 13, 0)  # Hollow interior
    # Vivid Red Cabinet Side Panels along outer shins with white stripe
    fill_sym_box(grid, 6, 6, 8, 13, 4, 13, 2)
    fill_sym_box(grid, 6, 6, 9, 12, 8, 9, 1)
    fill_sym_box(grid, 3, 3, 9, 13, 5, 13, 5)  # Inner leg silver hydraulic frame
    # Front shin panel details & glowing ice-blue knee guards
    fill_sym_box(grid, 4, 5, 14, 14, 5, 10, 2)
    fill_sym_box(grid, 4, 5, 14, 14, 7, 8, 1)
    fill_sym_box(grid, 3, 6, 14, 15, 12, 15, 1)  # White armored kneecap
    fill_sym_box(grid, 4, 5, 15, 16, 13, 14, 3)  # Cool ice-blue knee lens
    fill_sym_box(grid, 4, 5, 15, 15, 12, 12, 5)  # Chrome knee trim

    # --- MECHANICAL THIGHS (Z: 15..18) ---
    fill_sym_box(grid, 3, 5, 9, 13, 15, 18, 4)
    fill_sym_box(grid, 4, 4, 10, 12, 16, 17, 0)  # Hollow core
    fill_sym_box(grid, 3, 5, 13, 14, 16, 18, 1)  # White front thigh guard
    fill_sym_box(grid, 4, 4, 14, 14, 16, 17, 5)  # Silver piston rod
    fill_sym_box(grid, 5, 5, 10, 12, 16, 18, 8)  # Deep navy side trim

    # --- WAIST / PELVIS: PICKUP DISPENSER SLOT MOTIF (取り出し口が腰!) (Z: 18..22) ---
    fill_sym_box(grid, 0, 5, 8, 14, 19, 22, 1)
    fill_sym_box(grid, 0, 4, 9, 12, 20, 21, 0)  # Hollow interior
    # Recessed Dark Charcoal Pickup Dispenser Slot right across front waist! (Y: 13..15, Z: 19..21)
    fill_sym_box(grid, 0, 4, 13, 15, 19, 21, 0)  # Deep open dispenser cavity
    fill_sym_box(grid, 0, 4, 12, 12, 19, 21, 4)  # Deep dark charcoal dispenser back wall
    fill_sym_box(grid, 0, 4, 13, 14, 18, 18, 4)  # Dark pickup tray bottom
    fill_sym_box(grid, 0, 3, 13, 14, 21, 21, 8)  # Deep navy angled dispenser push-flap
    fill_sym_box(grid, 0, 2, 14, 14, 21, 21, 5)  # Chrome flap bar
    # Silver Chrome Dispenser Frame enclosing the Waist Belt!
    fill_sym_box(grid, 0, 5, 15, 15, 18, 18, 5)  # Lower pickup lip
    fill_sym_box(grid, 0, 5, 14, 15, 22, 22, 5)  # Upper dispenser frame
    fill_sym_box(grid, 5, 5, 13, 15, 19, 21, 5)  # Left/Right chrome side frames
    # Vivid Red & White Hip Armor Skirts (side panels)
    fill_sym_box(grid, 6, 7, 9, 13, 19, 22, 2)
    fill_sym_box(grid, 7, 7, 10, 12, 20, 21, 1)
    fill_sym_box(grid, 7, 7, 11, 11, 20, 20, 6)  # Citrus orange coin-return detail

    # --- BOXY CABINET TORSO WITH ILLUMINATED DRINK-ROW CHEST (箱の本体が胴体・飲み物の列が胸の意匠!) (Z: 23..33) ---
    # Core Sturdy Boxy Vending-Machine Torso
    fill_sym_box(grid, 0, 6, 7, 15, 23, 32, 1)
    fill_sym_box(grid, 0, 5, 8, 13, 24, 31, 0)  # Hollow torso core
    # Vivid Red Cabinet Side Walls on outer torso flanks
    fill_sym_box(grid, 6, 6, 8, 14, 23, 32, 2)
    fill_sym_box(grid, 6, 6, 9, 13, 27, 28, 1)  # White brand stripe

    # Front Chest Illuminated Showcase Frame (Y: 14..16, Z: 24..33)
    fill_sym_box(grid, 0, 5, 15, 16, 24, 32, 1)  # Crisp white cabinet bezel
    fill_sym_box(grid, 0, 4, 15, 16, 25, 31, 0)  # Cut out recessed showcase window!
    fill_sym_box(grid, 0, 4, 14, 14, 25, 31, 9)  # Glowing warm-white showcase backlight!
    # Silver chrome inner trim & cool ice-blue corner glass glints
    fill_sym_box(grid, 5, 5, 15, 16, 25, 31, 5)
    fill_sym_box(grid, 0, 5, 15, 16, 32, 32, 2)  # Vivid red top marquee header
    fill_sym_box(grid, 0, 3, 16, 16, 32, 32, 9)  # Glowing warm-white chest marquee light
    fill_sym_box(grid, 4, 4, 16, 16, 31, 31, 3)  # Ice-blue glass glint corner

    # TWO VIBRANT ROWS OF COLORFUL DRINKS SHINING ACROSS THE CHEST PLATE!
    # Upper shelf (Z: 28) + Drinks (Z: 29..30, Y: 15)
    fill_sym_box(grid, 0, 4, 14, 15, 28, 28, 5)  # Silver shelf ledge
    fill_sym_box(grid, 0, 4, 16, 16, 28, 28, 8)  # Deep navy selection button bar
    # Upper row drinks across X = 11..20 (symmetric around cx_l=15, cx_r=16)
    upper_drinks = [
        (11, 2), (13, 3), (15, 7), (16, 6), (18, 3), (20, 2),
    ]
    for dx, dcol in upper_drinks:
        fill_box(grid, dx, dx, 15, 15, 29, 30, dcol)  # Vibrant drink can
        fill_box(grid, dx, dx, 15, 15, 31, 31, 5)     # Silver can cap
        fill_box(grid, dx, dx, 16, 16, 28, 28, 3 if dcol in (3, 7) else 6)  # Glowing button

    # Lower shelf (Z: 24) + Drinks (Z: 25..26, Y: 15)
    fill_sym_box(grid, 0, 4, 14, 15, 24, 24, 5)  # Silver lower shelf
    fill_sym_box(grid, 0, 4, 16, 16, 24, 24, 8)  # Lower navy button bar
    lower_drinks = [
        (11, 6), (13, 7), (15, 2), (16, 2), (18, 7), (20, 6),
    ]
    for dx, dcol in lower_drinks:
        fill_box(grid, dx, dx, 15, 15, 25, 26, dcol)  # Vibrant drink can
        fill_box(grid, dx, dx, 15, 15, 27, 27, 1)     # Crisp white bottle cap
        fill_box(grid, dx, dx, 16, 16, 24, 24, 2 if dcol == 2 else 3)  # Glowing button

    # Control / Coin-Slot Strip at bottom chest bezel (Z: 23, Y: 15..16)
    fill_sym_box(grid, 0, 5, 14, 15, 23, 23, 4)
    fill_sym_box(grid, 0, 2, 15, 15, 23, 23, 6)  # Orange LED price bar
    fill_sym_box(grid, 4, 4, 15, 15, 23, 23, 5)  # Coin slot chrome

    # Collar armor framing neck
    fill_sym_box(grid, 2, 5, 10, 14, 33, 33, 2)
    fill_sym_box(grid, 3, 5, 13, 14, 33, 33, 1)

    # --- BACKPACK: REAR SERVICE PANEL & COOLING COMPRESSOR THRUSTERS (Y: 4..7, Z: 22..33) ---
    fill_sym_box(grid, 0, 5, 5, 7, 23, 32, 1)
    fill_sym_box(grid, 0, 4, 6, 6, 24, 31, 0)  # Hollow backpack interior
    fill_sym_box(grid, 5, 5, 5, 7, 23, 32, 2)  # Red cabinet side wrap
    # Rear dark compressor vent louvers
    fill_sym_box(grid, 0, 3, 4, 5, 25, 30, 4)
    for vz in (26, 28, 30):
        fill_sym_box(grid, 0, 3, 4, 4, vz, vz, 5)
    # Top red roof cooling cap
    fill_sym_box(grid, 0, 4, 4, 7, 32, 33, 2)
    fill_sym_box(grid, 0, 2, 5, 6, 33, 33, 9)
    # Twin Refrigeration Thruster Nozzles at backpack bottom (Z: 22..24)
    fill_sym_box(grid, 2, 4, 4, 6, 22, 24, 4)
    fill_sym_box(grid, 3, 3, 4, 4, 22, 23, 3)  # Cool ice-blue frost jet core

    # --- BLOCKY RED & WHITE CABINET SHOULDERS (Z: 28..35, x_off: 7..12) ---
    fill_sym_box(grid, 6, 8, 10, 12, 29, 32, 4)  # Heavy shoulder joint axle
    fill_sym_box(grid, 7, 8, 10, 12, 30, 31, 5)
    # Massive blocky shoulder armor pauldrons
    fill_sym_box(grid, 8, 12, 8, 14, 28, 34, 2)  # Vivid crimson red cabinet shells
    fill_sym_box(grid, 9, 11, 9, 13, 29, 33, 0)  # Hollow interior
    # Re-anchor inner shoulder mount so arm connects cleanly
    fill_sym_box(grid, 8, 10, 10, 12, 29, 32, 4)
    # Crisp white top & front stripe detailing + silver hinges
    fill_sym_box(grid, 8, 12, 9, 13, 34, 35, 1)  # White shoulder roof cap
    fill_sym_box(grid, 9, 11, 14, 14, 30, 32, 1)  # White front door panel
    fill_sym_box(grid, 10, 10, 14, 14, 31, 31, 6)  # Citrus orange indicator
    fill_sym_box(grid, 12, 12, 9, 13, 31, 32, 1)  # Outer white brand stripe
    fill_sym_box(grid, 12, 12, 13, 13, 29, 33, 5)  # Silver cabinet hinge

    # --- ARMS, FOREARMS & CAN-LAUNCHER BLASTER (Z: 15..28) ---
    # Upper arms
    fill_sym_box(grid, 9, 11, 10, 12, 23, 28, 4)
    fill_sym_box(grid, 9, 11, 10, 12, 25, 26, 5)  # Silver bicep piston
    # Blocky armored forearms
    fill_sym_box(grid, 9, 12, 9, 14, 17, 22, 1)
    fill_sym_box(grid, 10, 11, 10, 13, 18, 21, 0)  # Hollow forearm interior
    fill_sym_box(grid, 12, 12, 9, 13, 17, 22, 2)   # Outer vivid red cuff
    fill_sym_box(grid, 9, 11, 14, 14, 18, 21, 8)   # Front navy guard
    fill_sym_box(grid, 10, 10, 14, 14, 19, 20, 3)  # Ice-blue forearm LED
    # Mechanical fists
    fill_sym_box(grid, 9, 11, 10, 13, 15, 16, 4)
    fill_sym_box(grid, 9, 11, 13, 13, 15, 16, 5)

    # RIGHT FOREARM (+X, viewer's left): SODA CAN-LAUNCHER FOREARM BLASTER!
    # Mounted firmly to right fist & outer forearm (X = cx_r + 10..13 = 26..29)
    fill_box(grid, cx_r + 10, cx_r + 13, 12, 17, 16, 19, 2)  # Red launcher housing
    fill_box(grid, cx_r + 11, cx_r + 12, 13, 16, 17, 18, 0)  # Hollow breech
    fill_box(grid, cx_r + 11, cx_r + 12, 17, 21, 17, 18, 5)  # Heavy silver chrome barrel
    fill_box(grid, cx_r + 11, cx_r + 12, 21, 21, 17, 18, 3)  # Glowing ice-blue chilled muzzle
    fill_box(grid, cx_r + 10, cx_r + 13, 13, 16, 19, 19, 1)  # White upper rail
    # Visible colorful Soda-Can Ammo Magazine loaded on top of launcher!
    fill_box(grid, cx_r + 11, cx_r + 12, 13, 13, 20, 21, 6)  # Citrus orange can
    fill_box(grid, cx_r + 11, cx_r + 12, 14, 14, 20, 21, 7)  # Green tea can
    fill_box(grid, cx_r + 11, cx_r + 12, 15, 15, 20, 21, 2)  # Red cola can

    # LEFT FOREARM (-X, viewer's right): COIN-PANEL COOLER SHIELD
    fill_box(grid, cx_l - 13, cx_l - 12, 10, 15, 17, 22, 1)
    fill_box(grid, cx_l - 13, cx_l - 13, 11, 14, 18, 21, 2)  # Red inner shield face
    fill_box(grid, cx_l - 13, cx_l - 13, 12, 13, 20, 20, 6)  # Orange LED display strip
    fill_box(grid, cx_l - 13, cx_l - 12, 15, 15, 17, 22, 5)  # Silver shield edge

    # --- HEROIC HEAD WITH COIN-SLOT & LED VISOR CROWN (Z: 34..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 10, 12, 33, 34, 4)
    # Main crisp white helmet block
    fill_sym_box(grid, 0, 2, 9, 13, 35, 39, 1)
    # Vivid crimson red top helmet cap & side ear pods
    fill_sym_box(grid, 0, 2, 9, 13, 39, 39, 2)
    fill_sym_box(grid, 3, 3, 10, 12, 36, 38, 2)
    fill_sym_box(grid, 3, 3, 11, 11, 37, 37, 5)  # Silver ear coin-dial
    # Cool Ice-Blue Panoramic Visor & Silver Faceplate
    fill_sym_box(grid, 0, 2, 14, 14, 37, 37, 3)  # Glowing ice-blue visor
    fill_sym_box(grid, 1, 1, 14, 14, 37, 37, 9)  # Bright warm-white eye glints
    fill_sym_box(grid, 0, 1, 14, 14, 35, 36, 5)  # Silver chrome faceplate
    fill_sym_box(grid, 0, 0, 14, 14, 35, 35, 8)  # Chin vent
    # Forehead LED Price-Display & Coin-Slot Crown + Swept V-Crest!
    fill_sym_box(grid, 0, 2, 14, 14, 38, 39, 8)  # Dark navy forehead bezel
    fill_sym_box(grid, 0, 1, 14, 15, 39, 39, 6)  # Glowing Citrus Orange LED crown bar
    fill_sym_box(grid, 0, 0, 15, 15, 39, 40, 5)  # Silver coin-slot centerpiece
    fill_sym_box(grid, 1, 2, 13, 14, 40, 40, 2)  # Red V-crest inner wings
    fill_sym_box(grid, 2, 3, 12, 13, 41, 41, 1)  # Crisp white V-crest tips

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=38, pitch_a=24, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "vending_a.vox")
    v_b = export_vox(model_b, "vending_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: VENDING MACHINE -> DRINK DISPENSER ROBOT",
        "1. VENDING MACHINE",
        "2. DRINK DISPENSER ROBOT",
        "preview_vending.png",
        yaw_a=34, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"vending: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
