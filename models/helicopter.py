import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 246, 250, 255),  # Pure Rescue White
    2: (235, 92, 32, 255),    # Vibrant Rescue Orange-Red
    3: (255, 206, 48, 255),   # High-Vis Rescue Yellow
    4: (56, 66, 82, 255),     # Dark Slate Charcoal (Blades / Skids / Joints)
    5: (26, 62, 108, 255),    # Deep Tinted Cockpit Glass Navy
    6: (102, 226, 255, 255),  # Cyan Glass Glint / Robot Visor / Blade Edge
    7: (122, 134, 154, 255),  # Brushed Metallic Steel (Mast / Struts / Hilt)
    8: (216, 38, 48, 255),    # Signal Crimson Red (Beacons / Warning Bands)
    9: (188, 198, 214, 255),  # Light Silver-Grey (Underside / Intakes / Thighs)
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
# FORM A: RESCUE HELICOPTER (36 x 48 x 20)
# ==========================================
def build_a():
    grid = np.zeros((36, 48, 20), dtype=np.uint8)
    cx_r = grid.shape[0] // 2  # 18

    # --- LANDING SKIDS (Z: 0..3) ---
    fill_sym_box(grid, 5, 5, 20, 41, 0, 0, 4)  # Main skid tubes
    fill_sym_box(grid, 5, 5, 19, 19, 0, 0, 7)  # Rear skid caps
    # Curved front skid tips (6-connected upward curve)
    fill_sym_box(grid, 5, 5, 41, 42, 1, 1, 4)
    fill_sym_box(grid, 5, 5, 42, 43, 2, 2, 7)
    # Twin angled struts connecting skids to fuselage belly
    for sy in (25, 36):
        fill_sym_box(grid, 5, 5, sy, sy + 1, 1, 1, 7)
        fill_sym_box(grid, 4, 5, sy, sy + 1, 2, 2, 7)
        fill_sym_box(grid, 3, 4, sy, sy + 1, 3, 3, 7)

    # --- MAIN FUSELAGE CABIN (Y: 22..41, Z: 3..11) ---
    fill_sym_box(grid, 0, 3, 23, 41, 3, 3, 9)   # Silver belly underside
    fill_sym_box(grid, 3, 3, 23, 40, 3, 3, 2)   # Orange belly trim
    fill_sym_box(grid, 0, 4, 22, 40, 4, 6, 2)   # Lower rescue-orange fuselage
    fill_sym_box(grid, 0, 4, 22, 39, 7, 9, 1)   # Upper pure-white cabin
    fill_sym_box(grid, 0, 3, 23, 38, 10, 10, 1) # Curved upper shoulder
    fill_sym_box(grid, 0, 2, 23, 36, 11, 11, 1) # Cabin roof

    # Hollow unseen cabin interior to keep voxel count lean
    fill_sym_box(grid, 0, 2, 24, 36, 4, 9, 0)

    # High-vis yellow rescue stripe along fuselage flanks
    fill_sym_box(grid, 4, 4, 22, 40, 6, 6, 3)

    # Side cabin windows & sliding rescue door detail
    fill_sym_box(grid, 4, 4, 35, 38, 7, 9, 5)   # Pilot side window
    fill_sym_box(grid, 4, 4, 36, 37, 9, 9, 6)   # Cyan glint
    fill_sym_box(grid, 4, 4, 29, 32, 7, 8, 5)   # Sliding door window
    fill_sym_box(grid, 4, 4, 31, 32, 8, 8, 6)   # Cyan glint
    fill_sym_box(grid, 4, 4, 25, 27, 7, 8, 5)   # Rear cabin window
    # Rescue red cross badge on lower door
    fill_sym_box(grid, 4, 4, 29, 31, 4, 5, 1)
    fill_sym_box(grid, 4, 4, 30, 30, 4, 5, 8)
    # Navigation beacons on lower fuselage sides
    fill_sym_box(grid, 4, 4, 23, 23, 4, 4, 8)
    # Rescue hoist / winch pod mounted on +X side above door
    fill_box(grid, cx_r + 5, cx_r + 5, 29, 33, 9, 10, 7)
    fill_box(grid, cx_r + 5, cx_r + 5, 30, 32, 10, 10, 3)
    fill_box(grid, cx_r + 5, cx_r + 5, 31, 31, 8, 8, 8)

    # --- PANORAMIC COCKPIT & AERODYNAMIC NOSE (Y: 38..45, Z: 4..10) ---
    # Lower rounded orange nose
    fill_sym_box(grid, 0, 3, 40, 42, 4, 6, 2)
    fill_sym_box(grid, 3, 3, 41, 42, 6, 6, 3)
    fill_sym_box(grid, 0, 2, 43, 44, 4, 5, 2)
    fill_sym_box(grid, 2, 2, 43, 44, 5, 5, 3)
    fill_sym_box(grid, 0, 1, 45, 45, 4, 5, 2)
    fill_sym_box(grid, 0, 0, 45, 45, 4, 5, 4)   # Weather radar nose cap
    # Nose searchlight underneath chin
    fill_sym_box(grid, 0, 0, 42, 43, 3, 3, 4)
    fill_sym_box(grid, 0, 0, 44, 44, 3, 3, 6)
    # Wrap-around panoramic dark navy cockpit canopy
    fill_sym_box(grid, 0, 3, 38, 40, 7, 9, 5)
    fill_sym_box(grid, 0, 2, 41, 41, 7, 8, 5)
    fill_sym_box(grid, 0, 1, 42, 42, 7, 7, 5)
    # Canopy upper white brow & roof fairing
    fill_sym_box(grid, 0, 2, 37, 39, 10, 10, 1)
    fill_sym_box(grid, 0, 1, 40, 40, 9, 9, 1)
    # Crisp cyan windshield reflections
    fill_sym_box(grid, 1, 2, 40, 40, 8, 9, 6)
    fill_sym_box(grid, 0, 1, 41, 41, 8, 8, 6)
    fill_sym_box(grid, 0, 0, 42, 42, 7, 7, 6)
    # Cockpit frame pillars
    fill_sym_box(grid, 3, 3, 39, 39, 7, 9, 4)

    # --- REAR TRANSITION & TAPERED TAIL BOOM (Y: 4..22, Z: 5..10) ---
    # Rear cabin taper
    fill_sym_box(grid, 0, 3, 21, 22, 5, 9, 1)
    fill_sym_box(grid, 0, 3, 21, 22, 5, 6, 2)
    fill_sym_box(grid, 3, 3, 21, 22, 6, 6, 3)
    fill_sym_box(grid, 0, 2, 21, 22, 10, 10, 1)
    fill_sym_box(grid, 0, 2, 19, 20, 6, 9, 1)
    fill_sym_box(grid, 0, 2, 19, 20, 6, 7, 2)
    fill_sym_box(grid, 2, 2, 19, 20, 7, 7, 3)
    # Mid tail boom
    fill_sym_box(grid, 0, 1, 12, 18, 7, 9, 1)
    fill_sym_box(grid, 0, 1, 12, 18, 7, 7, 2)
    fill_sym_box(grid, 1, 1, 12, 18, 8, 8, 3)
    fill_sym_box(grid, 0, 0, 12, 19, 10, 10, 7)  # Steel drive shaft cover
    # Rear slender tail boom
    fill_sym_box(grid, 0, 0, 5, 11, 7, 9, 1)
    fill_sym_box(grid, 0, 0, 5, 11, 7, 7, 2)
    fill_sym_box(grid, 0, 0, 5, 11, 8, 8, 3)
    fill_sym_box(grid, 0, 0, 6, 11, 10, 10, 7)
    # Horizontal tail stabilizers & endplates
    fill_sym_box(grid, 1, 4, 9, 11, 8, 8, 2)
    fill_sym_box(grid, 1, 4, 11, 11, 8, 8, 1)
    fill_sym_box(grid, 4, 4, 9, 11, 7, 9, 2)
    fill_sym_box(grid, 4, 4, 9, 11, 9, 9, 3)

    # --- SWEPT VERTICAL TAIL FIN & TAIL ROTOR (Y: 1..7, Z: 5..16) ---
    fill_sym_box(grid, 0, 0, 4, 7, 7, 10, 2)
    fill_sym_box(grid, 0, 0, 4, 6, 9, 10, 1)
    fill_sym_box(grid, 0, 0, 3, 6, 10, 12, 1)
    fill_sym_box(grid, 0, 0, 3, 5, 11, 11, 3)   # Yellow tail stripe
    fill_sym_box(grid, 0, 0, 2, 5, 12, 14, 2)
    fill_sym_box(grid, 0, 0, 1, 4, 14, 15, 2)
    fill_sym_box(grid, 0, 0, 1, 4, 15, 15, 3)   # Yellow fin top
    fill_sym_box(grid, 0, 0, 2, 3, 16, 16, 8)   # Red anti-collision beacon
    # Ventral tail skid fin
    fill_sym_box(grid, 0, 0, 4, 6, 5, 6, 4)
    fill_sym_box(grid, 0, 0, 4, 4, 5, 5, 3)
    # Tail rotor mounted on +X side of vertical fin
    fill_box(grid, cx_r + 1, cx_r + 2, 4, 4, 12, 12, 7)  # Steel tail rotor axle
    fill_box(grid, cx_r + 2, cx_r + 2, 4, 4, 10, 14, 4)  # Vertical tail blades
    fill_box(grid, cx_r + 2, cx_r + 2, 2, 6, 12, 12, 4)  # Horizontal tail blades
    fill_box(grid, cx_r + 2, cx_r + 2, 4, 4, 10, 10, 3)  # Yellow blade tips
    fill_box(grid, cx_r + 2, cx_r + 2, 4, 4, 14, 14, 3)
    fill_box(grid, cx_r + 2, cx_r + 2, 2, 2, 12, 12, 3)
    fill_box(grid, cx_r + 2, cx_r + 2, 6, 6, 12, 12, 3)
    fill_box(grid, cx_r + 2, cx_r + 2, 4, 4, 12, 12, 7)  # Center hub

    # --- TWIN TURBINE ENGINE COWLING & MAST (Y: 22..35, Z: 12..16) ---
    fill_sym_box(grid, 0, 2, 24, 34, 12, 13, 1)
    fill_sym_box(grid, 2, 2, 24, 34, 12, 12, 2)  # Orange cowling trim
    fill_sym_box(grid, 0, 1, 25, 33, 14, 14, 2)  # Upper turbine spine
    # Front twin turbine intakes
    fill_sym_box(grid, 1, 2, 35, 35, 12, 13, 9)
    fill_sym_box(grid, 1, 1, 35, 35, 12, 13, 4)
    # Rear twin exhaust nozzles
    fill_sym_box(grid, 1, 2, 22, 23, 12, 13, 7)
    fill_sym_box(grid, 1, 1, 22, 22, 12, 13, 4)
    # Rotor mast & swashplate
    fill_sym_box(grid, 0, 1, 28, 31, 15, 15, 4)
    fill_sym_box(grid, 0, 0, 29, 30, 15, 16, 7)

    # --- 4-BLADE MAIN ROTOR (Z: 17..18, Center X: 17..18, Y: 29..30) ---
    fill_sym_box(grid, 0, 1, 28, 31, 17, 17, 4)  # Rotor head hub
    fill_sym_box(grid, 0, 0, 29, 30, 18, 18, 8)  # Red rotor spinner dome
    # Left & Right blades (+X / -X)
    fill_sym_box(grid, 2, 3, 29, 30, 17, 17, 7)   # Steel roots
    fill_sym_box(grid, 4, 13, 29, 30, 17, 17, 4)  # Charcoal blades
    fill_sym_box(grid, 14, 14, 29, 30, 17, 17, 8) # Red warning band
    fill_sym_box(grid, 15, 16, 29, 30, 17, 17, 3) # High-vis yellow tips
    # Front blade (+Y)
    fill_sym_box(grid, 0, 0, 32, 33, 17, 17, 7)
    fill_sym_box(grid, 0, 0, 34, 43, 17, 17, 4)
    fill_sym_box(grid, 0, 0, 44, 44, 17, 17, 8)
    fill_sym_box(grid, 0, 0, 45, 46, 17, 17, 3)
    # Rear blade (-Y)
    fill_sym_box(grid, 0, 0, 26, 27, 17, 17, 7)
    fill_sym_box(grid, 0, 0, 16, 25, 17, 17, 4)
    fill_sym_box(grid, 0, 0, 15, 15, 17, 17, 8)
    fill_sym_box(grid, 0, 0, 13, 14, 17, 17, 3)

    return grid


# ==========================================
# FORM B: HELICOPTER SKY ROBOT (36 x 26 x 42)
# ==========================================
def build_b():
    grid = np.zeros((36, 26, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 17
    cx_r = grid.shape[0] // 2      # 18

    # --- FEET (Z: 0..3) - Stabilizer Heels + Rescue Armored Toes ---
    fill_sym_box(grid, 2, 5, 8, 16, 0, 1, 4)     # Grounded charcoal soles
    fill_sym_box(grid, 2, 5, 13, 17, 1, 2, 2)    # Orange armored toes
    fill_sym_box(grid, 3, 4, 15, 18, 1, 2, 1)    # White central toe cap
    fill_sym_box(grid, 3, 4, 17, 18, 2, 2, 3)    # Yellow toe bumper
    fill_sym_box(grid, 2, 5, 7, 9, 0, 2, 7)      # Steel stabilizer heel spurs
    fill_sym_box(grid, 3, 4, 10, 13, 2, 4, 4)    # Ankle hydraulic joints

    # --- LOWER LEGS (Z: 4..15) - Split Tail Boom + Swept Tail-Fin Stabilizers ---
    fill_sym_box(grid, 2, 5, 10, 14, 4, 14, 1)   # White tail-boom greaves
    fill_sym_box(grid, 2, 5, 10, 14, 4, 8, 2)    # Orange lower shin wrap
    fill_sym_box(grid, 3, 4, 14, 15, 5, 12, 2)   # Orange front shin ridge
    fill_sym_box(grid, 5, 5, 11, 13, 5, 13, 3)   # Yellow rescue stripe
    # Hollow unseen lower leg interior
    fill_sym_box(grid, 3, 4, 11, 13, 5, 13, 0)
    # Angular knee guards
    fill_sym_box(grid, 2, 4, 14, 15, 13, 15, 1)
    fill_sym_box(grid, 3, 4, 15, 16, 13, 15, 2)
    fill_sym_box(grid, 3, 3, 16, 16, 14, 15, 3)
    # Swept vertical tail-fin stabilizers mounted on outer/rear calves!
    fill_sym_box(grid, 6, 6, 9, 11, 6, 13, 1)
    fill_sym_box(grid, 6, 6, 9, 11, 6, 9, 2)
    fill_sym_box(grid, 6, 6, 10, 11, 10, 11, 3)  # Yellow fin stripe
    fill_sym_box(grid, 7, 7, 8, 10, 5, 11, 2)
    fill_sym_box(grid, 7, 7, 9, 10, 10, 11, 3)
    fill_sym_box(grid, 8, 8, 7, 9, 5, 9, 2)
    fill_sym_box(grid, 8, 8, 7, 8, 5, 6, 8)      # Red tail-fin beacon tip
    # Mini tail-rotor circular hub detail on outer calf
    fill_sym_box(grid, 6, 6, 12, 13, 9, 11, 4)
    fill_sym_box(grid, 6, 6, 12, 13, 10, 10, 7)

    # --- THIGHS (Z: 15..21) ---
    fill_sym_box(grid, 2, 4, 10, 13, 15, 21, 9)  # Light silver thighs
    fill_sym_box(grid, 2, 4, 13, 14, 16, 20, 1)  # White front armor plates
    fill_sym_box(grid, 4, 4, 11, 13, 17, 19, 2)  # Orange outer accent
    fill_sym_box(grid, 2, 3, 11, 12, 15, 15, 4)  # Knee joint pin

    # --- WAIST / PELVIS (Z: 21..25) ---
    fill_sym_box(grid, 0, 4, 10, 14, 21, 23, 4)  # Charcoal waist frame
    fill_sym_box(grid, 0, 1, 14, 16, 20, 24, 2)  # Orange central codpiece
    fill_sym_box(grid, 0, 0, 16, 16, 21, 23, 3)  # Yellow rescue buckle
    fill_sym_box(grid, 0, 0, 16, 16, 23, 23, 8)  # Red waist emblem
    fill_sym_box(grid, 2, 4, 14, 15, 21, 23, 1)  # White front skirts
    fill_sym_box(grid, 2, 4, 15, 15, 21, 21, 3)  # Yellow skirt trim
    fill_sym_box(grid, 5, 5, 10, 13, 21, 23, 2)  # Orange hip armor
    fill_sym_box(grid, 5, 5, 11, 12, 23, 23, 1)
    # Athletic V-taper waist abs core
    fill_sym_box(grid, 0, 2, 10, 14, 24, 25, 4)
    fill_sym_box(grid, 0, 1, 14, 15, 24, 25, 9)

    # --- TORSO / CHEST (Z: 26..33) - Helicopter Panoramic Cockpit & Nose ---
    fill_sym_box(grid, 0, 5, 9, 15, 26, 33, 1)   # White upper chest cabin
    fill_sym_box(grid, 0, 5, 9, 15, 26, 28, 2)   # Orange lower chest fuselage
    fill_sym_box(grid, 0, 5, 9, 15, 28, 28, 3)   # Yellow wrap-around rescue stripe
    # Hollow unseen torso core
    fill_sym_box(grid, 0, 3, 10, 14, 27, 32, 0)

    # Prominent jutting Helicopter Nose & Panoramic Canopy on chest!
    fill_sym_box(grid, 0, 3, 16, 18, 26, 28, 2)  # Orange lower nose cone
    fill_sym_box(grid, 0, 2, 19, 19, 26, 28, 2)
    fill_sym_box(grid, 0, 1, 20, 20, 27, 28, 2)
    fill_sym_box(grid, 0, 0, 20, 20, 27, 27, 3)  # Bright nose searchlight core
    fill_sym_box(grid, 2, 3, 18, 18, 27, 27, 9)  # Nose intake vents
    # Panoramic dark navy cockpit glass windshield
    fill_sym_box(grid, 0, 3, 16, 17, 29, 32, 5)
    fill_sym_box(grid, 0, 2, 18, 18, 29, 31, 5)
    fill_sym_box(grid, 0, 1, 19, 19, 29, 30, 5)
    # Crisp cyan glass glints across chest canopy
    fill_sym_box(grid, 1, 2, 17, 17, 31, 32, 6)
    fill_sym_box(grid, 0, 1, 18, 18, 30, 31, 6)
    fill_sym_box(grid, 0, 0, 19, 19, 30, 30, 6)
    # Upper white brow & red chest beacons
    fill_sym_box(grid, 0, 3, 15, 16, 33, 33, 1)
    fill_sym_box(grid, 4, 4, 15, 15, 31, 32, 8)
    fill_sym_box(grid, 3, 4, 15, 15, 29, 30, 4)  # Canopy side pillars

    # --- TURBINE BACKPACK & ICONIC 4-BLADE X-ROTOR WINGS (Y: 4..8, Z: 19..41) ---
    # Twin turbine doghouse backpack
    fill_sym_box(grid, 0, 4, 6, 8, 26, 33, 1)
    fill_sym_box(grid, 3, 4, 6, 8, 26, 32, 2)
    fill_sym_box(grid, 0, 2, 7, 8, 27, 32, 0)    # Hollow unseen backpack core
    fill_sym_box(grid, 2, 3, 6, 8, 33, 34, 9)    # Top silver turbine intakes
    fill_sym_box(grid, 2, 2, 6, 7, 34, 34, 4)
    # Twin lower exhaust thrusters with cyan glow
    fill_sym_box(grid, 2, 3, 5, 7, 23, 25, 7)
    fill_sym_box(grid, 2, 3, 5, 6, 23, 23, 6)
    # Central rotor mast & spinner hub
    fill_sym_box(grid, 0, 1, 4, 5, 29, 32, 4)
    fill_sym_box(grid, 0, 1, 5, 5, 30, 31, 7)
    fill_sym_box(grid, 0, 0, 4, 4, 30, 31, 8)    # Red rotor hub spinner

    # 4 massive X-shaped rotor blades radiating from hub (Y: 5, 6-connected!)
    # Upper-left & upper-right blades (sweeping up & out past shoulders)
    for i in range(13):
        xo = 2 + i
        zb = 32 + int(round(i * 0.72))
        if i <= 1:
            col = 7
        elif i <= 9:
            col = 4
        elif i == 10:
            col = 8
        else:
            col = 3
        fill_sym_box(grid, xo, xo, 5, 5, zb, zb + 1, col)
    # Lower-left & lower-right blades (sweeping down & out past flanks)
    for i in range(12):
        xo = 2 + i
        zb = 29 - int(round(i * 0.78))
        if i <= 1:
            col = 7
        elif i <= 8:
            col = 4
        elif i == 9:
            col = 8
        else:
            col = 3
        fill_sym_box(grid, xo, xo, 5, 5, zb - 1, zb, col)

    # --- SHOULDERS & ARMS (Z: 15..35) ---
    # Shoulder connector joints
    fill_sym_box(grid, 5, 6, 11, 13, 30, 32, 4)
    # Broad rescue-armored pauldrons
    fill_sym_box(grid, 6, 10, 9, 14, 29, 34, 1)
    fill_sym_box(grid, 9, 10, 9, 14, 29, 33, 2)  # Orange outer wing
    fill_sym_box(grid, 6, 10, 10, 13, 31, 31, 3) # Yellow stripe
    fill_sym_box(grid, 7, 9, 14, 14, 32, 33, 5)  # Cabin-window armor slit
    fill_sym_box(grid, 8, 9, 11, 12, 35, 35, 8)  # Red shoulder beacon
    fill_sym_box(grid, 7, 9, 10, 13, 30, 33, 0)  # Hollow unseen pauldron interior
    # Upper arms
    fill_sym_box(grid, 7, 8, 10, 13, 24, 28, 4)
    fill_sym_box(grid, 7, 8, 11, 12, 25, 27, 7)
    # Forearm gauntlets
    fill_sym_box(grid, 7, 9, 10, 14, 17, 23, 1)
    fill_sym_box(grid, 9, 9, 10, 14, 18, 22, 2)
    fill_sym_box(grid, 7, 9, 13, 14, 17, 18, 3)  # Yellow wrist cuff
    # Folded Landing Skid Rails mounted along outer forearms!
    fill_sym_box(grid, 10, 10, 11, 12, 16, 24, 4)  # Charcoal skid rail
    fill_sym_box(grid, 10, 10, 12, 12, 24, 25, 7)  # Curved steel skid tip
    fill_sym_box(grid, 9, 10, 11, 12, 18, 18, 7)   # Lower strut mount
    fill_sym_box(grid, 9, 10, 11, 12, 22, 22, 7)   # Upper strut mount
    # Fists
    fill_sym_box(grid, 7, 8, 11, 13, 15, 16, 4)

    # --- RIGHT HAND (+X): HELI-ROTOR BLADE SWORD ---
    rx0, rx1 = cx_r + 7, cx_r + 8  # 25..26
    fill_box(grid, rx0, rx1, 10, 15, 15, 16, 7)  # Steel hilt through fist
    fill_box(grid, rx0, rx1, 14, 15, 14, 17, 2)  # Orange rotor handguard
    fill_box(grid, rx1, rx1, 16, 23, 15, 15, 4)  # Sleek charcoal rotor-blade spine
    fill_box(grid, rx1, rx1, 16, 22, 16, 16, 6)  # Glowing cyan energy edge
    fill_box(grid, rx1, rx1, 23, 23, 15, 16, 8)  # Red warning band
    fill_box(grid, rx1, rx1, 24, 25, 15, 16, 3)  # High-vis yellow razor tip
    fill_box(grid, rx1, rx1, 25, 25, 16, 16, 0)  # Tapered sword point

    # --- LEFT FOREARM (-X): RESCUE WINCH / GRAPPLE POD ---
    lx0, lx1 = cx_l - 9, cx_l - 8  # 8..9
    fill_box(grid, lx0, lx1, 14, 15, 19, 21, 7)  # Steel winch housing
    fill_box(grid, lx0, lx1, 15, 15, 20, 21, 3)  # Yellow hoist stripe
    fill_box(grid, lx0, lx0, 16, 16, 19, 20, 8)  # Red rescue grapple hook

    # --- HEAD (Z: 34..41) - Aviator-Mecha Helmet & V-Fin Crest ---
    fill_sym_box(grid, 0, 1, 11, 13, 34, 34, 4)  # Neck
    fill_sym_box(grid, 0, 2, 10, 15, 35, 38, 1)  # White helmet shell
    fill_sym_box(grid, 0, 2, 10, 14, 38, 39, 2)  # Orange aviator helmet crown
    fill_sym_box(grid, 0, 1, 15, 15, 35, 35, 9)  # Silver chin/faceplate
    # Glowing cyan pilot visor
    fill_sym_box(grid, 0, 2, 15, 16, 36, 37, 6)
    fill_sym_box(grid, 0, 1, 15, 16, 38, 38, 5)  # Visor upper brow shadow
    # Swept Yellow V-Fin aerial crest + red central sensor
    fill_sym_box(grid, 0, 0, 15, 16, 38, 39, 8)  # Red forehead gem
    fill_sym_box(grid, 1, 1, 15, 16, 39, 39, 3)  # V-fin inner
    fill_sym_box(grid, 1, 2, 14, 15, 40, 40, 3)  # V-fin mid (6-connected)
    fill_sym_box(grid, 2, 3, 13, 14, 41, 41, 3)  # V-fin tips
    # Steel ear-comms antennae
    fill_sym_box(grid, 3, 3, 11, 13, 36, 38, 7)
    fill_sym_box(grid, 3, 3, 12, 12, 39, 39, 8)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=42, pitch_a=26, yaw_b=32, pitch_b=20):
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
    v_a = export_vox(model_a, "helicopter_a.vox")
    v_b = export_vox(model_b, "helicopter_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: HELICOPTER -> HELICOPTER SKY ROBOT",
        "1. HELICOPTER",
        "2. HELICOPTER SKY ROBOT",
        "preview_helicopter.png",
        yaw_a=42, pitch_a=26, yaw_b=32, pitch_b=20,
    )
    print(f"helicopter: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
