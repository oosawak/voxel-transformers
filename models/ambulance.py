import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (244, 248, 254, 255),  # Crisp Rescue White (Van Body, Chest, Armor, Helmet)
    2: (192, 202, 216, 255),  # Light Cool Grey Shading (Panel Lines, Lower Trim)
    3: (228, 34, 42, 255),    # Vivid Rescue Red (Red Cross Emblem, Side Stripe, Siren)
    4: (36, 40, 48, 255),     # Dark Rubber Tire Charcoal (Tires, Undercarriage, Pillars)
    5: (82, 92, 108, 255),    # Gunmetal Steel (Bumpers, Joints, Chassis)
    6: (164, 178, 196, 255),  # Brushed Silver / Chrome (Stretcher Frame, Grille, Rims)
    7: (72, 206, 248, 255),   # Bright Cyan Windshield / Robot Visor
    8: (42, 118, 246, 255),   # Vivid Emergency Blue (Roof Lightbar Blue, Rescue Accent)
    9: (255, 224, 96, 255),   # Warm Amber / Headlight Glow & Turn Signals
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


def fill_sym_wheel_x(
    grid, x_off0, x_off1, cy, cz, r_outer, r_rim, r_hub,
    tire_col=4, rim_col=6, hub_col=1,
):
    """Draw a pair of symmetrical rescue van wheels along the X axis."""
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1
    cx_r = X // 2
    y_min = max(0, int(np.floor(cy - r_outer - 1)))
    y_max = min(Y - 1, int(np.ceil(cy + r_outer + 1)))
    z_min = max(0, int(np.floor(cz - r_outer - 1)))
    z_max = min(Z - 1, int(np.ceil(cz + r_outer + 1)))

    for y in range(y_min, y_max + 1):
        for z in range(z_min, z_max + 1):
            dist = np.hypot(y - cy, z - cz)
            if dist > r_outer:
                continue
            for x_off in range(x_off0, x_off1 + 1):
                is_outer = (x_off == x_off1)
                if dist <= r_hub:
                    col = hub_col if is_outer else 5
                elif dist <= r_rim:
                    col = rim_col if is_outer else 5
                else:
                    col = tire_col
                xl = cx_l - x_off
                xr = cx_r + x_off
                if 0 <= xl < X:
                    grid[xl, y, z] = col
                if 0 <= xr < X:
                    grid[xr, y, z] = col


# ==========================================
# FORM A: HIGH-ROOF AMBULANCE VAN (16 x 34 x 18)
# ==========================================
def build_a():
    grid = np.zeros((16, 34, 18), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 7 (-X left)
    cx_r = grid.shape[0] // 2      # 8 (+X right)

    # --- FOUR HEAVY VAN WHEELS (Z: 0..4) ---
    # Rear axle (Y: 7..11, x_off: 5..6) & Front axle (Y: 25..29, x_off: 4..5)
    fill_sym_wheel_x(
        grid, 5, 6, cy=9.0, cz=2.0,
        r_outer=2.45, r_rim=1.35, r_hub=0.65,
        tire_col=4, rim_col=6, hub_col=1,
    )
    fill_sym_wheel_x(
        grid, 4, 5, cy=26.5, cz=2.0,
        r_outer=2.35, r_rim=1.25, r_hub=0.65,
        tire_col=4, rim_col=6, hub_col=1,
    )

    # --- UNDERCARRIAGE CHASSIS & BUMPERS (Y: 1..33, Z: 2..3) ---
    fill_sym_box(grid, 0, 4, 2, 32, 2, 3, 5)
    fill_sym_box(grid, 0, 3, 4, 30, 2, 2, 0)  # Hollow underbelly center
    # Rear chrome step bumper & front gunmetal/chrome bumper
    fill_sym_box(grid, 0, 6, 1, 2, 2, 3, 6)
    fill_sym_box(grid, 0, 5, 1, 1, 3, 3, 5)
    fill_sym_box(grid, 0, 5, 32, 33, 2, 3, 5)
    fill_sym_box(grid, 0, 3, 33, 33, 3, 3, 6)

    # --- BOXY HIGH-ROOF MEDICAL COMPARTMENT (Y: 2..22, Z: 3..14, x_off: 0..6) ---
    fill_sym_box(grid, 0, 6, 2, 22, 3, 13, 1)
    # Hollow unseen van interior completely for sleek voxel count
    fill_sym_box(grid, 0, 5, 3, 21, 4, 12, 0)
    # Chamfered high-roof top deck (Z: 14)
    fill_sym_box(grid, 0, 5, 3, 21, 14, 14, 1)
    # Light grey lower rocker trim along sides
    fill_sym_box(grid, 6, 6, 2, 22, 3, 4, 2)
    # Carve wheel-well arches neatly above rear tires
    fill_sym_box(grid, 5, 6, 7, 11, 3, 4, 4)
    # Re-draw outer rear wheel so it pops cleanly inside arch
    fill_sym_wheel_x(
        grid, 5, 6, cy=9.0, cz=2.0,
        r_outer=2.45, r_rim=1.35, r_hub=0.65,
        tire_col=4, rim_col=6, hub_col=1,
    )

    # Vivid Rescue Red continuous side stripe along medical box (Z: 5..6)
    fill_sym_box(grid, 6, 6, 2, 22, 5, 5, 3)
    fill_sym_box(grid, 6, 6, 2, 22, 13, 13, 2)  # Subtle upper roof gutter shading
    # Upper side emergency strobe lights on medical box corners
    fill_sym_box(grid, 6, 6, 3, 4, 12, 12, 3)
    fill_sym_box(grid, 6, 6, 20, 21, 12, 12, 8)
    # Small side compartment hatch seam near front of box
    fill_sym_box(grid, 6, 6, 18, 20, 6, 10, 2)
    fill_sym_box(grid, 6, 6, 19, 19, 7, 9, 1)

    # --- ICONIC RED CROSS EMBLEMS (SIDES, ROOF & FRONT BROW) ---
    # Side Red Crosses on both medical box walls (Y: 11..16, Z: 7..12 -> bold 6x6 with 2-voxel bars!)
    fill_sym_box(grid, 6, 6, 13, 14, 7, 12, 3)  # Vertical bar
    fill_sym_box(grid, 6, 6, 11, 16, 9, 10, 3)  # Horizontal bar
    # Roof Red Cross (x_off: 0..2, Y: 10..15, Z: 14 -> bold 6x6!)
    fill_sym_box(grid, 0, 0, 10, 15, 14, 14, 3)
    fill_sym_box(grid, 0, 2, 12, 13, 14, 14, 3)
    # Front High-Roof Brow Red Cross facing forward cleanly above cab roof (Y: 22, Z: 12..14)
    fill_sym_box(grid, 0, 5, 22, 22, 14, 14, 1)  # Crisp white upper brow fascia
    fill_sym_box(grid, 0, 0, 22, 22, 12, 14, 3)  # Vertical bar
    fill_sym_box(grid, 0, 1, 22, 22, 13, 13, 3)  # Horizontal bar
    # Front brow flank emergency flashers (Red +X, Blue -X)
    fill_box(grid, cx_r + 3, cx_r + 4, 22, 22, 13, 13, 3)
    fill_box(grid, cx_l - 4, cx_l - 3, 22, 22, 13, 13, 8)

    # --- REAR DOUBLE DOORS (Y: 2, Z: 4..13) ---
    fill_sym_box(grid, 0, 0, 2, 2, 4, 12, 2)    # Center door split seam
    fill_sym_box(grid, 1, 3, 2, 2, 9, 11, 7)    # Twin cyan rear door windows
    fill_sym_box(grid, 1, 5, 2, 2, 5, 5, 3)     # Red rear safety stripe
    fill_sym_box(grid, 5, 5, 2, 2, 6, 8, 3)     # Vertical red tail light bars
    fill_sym_box(grid, 5, 5, 2, 2, 6, 6, 9)     # Amber turn signal
    # Rear roof emergency beacons (Red +X, Blue -X)
    fill_box(grid, cx_r + 2, cx_r + 4, 3, 4, 15, 15, 3)
    fill_box(grid, cx_l - 4, cx_l - 2, 3, 4, 15, 15, 8)
    fill_sym_box(grid, 0, 1, 3, 4, 15, 15, 2)

    # --- FRONT VAN CAB & HOOD (Y: 23..32, Z: 3..11, x_off: 0..5) ---
    # Lower cab doors & engine hood
    fill_sym_box(grid, 0, 5, 23, 31, 3, 7, 1)
    fill_sym_box(grid, 0, 4, 23, 30, 4, 6, 0)  # Hollow cab lower interior
    fill_sym_box(grid, 0, 5, 32, 32, 4, 6, 1)  # Front nose fascia
    fill_sym_box(grid, 5, 5, 23, 31, 5, 5, 3)  # Continuous red stripe across cab doors!
    fill_sym_box(grid, 5, 5, 23, 31, 3, 4, 2)  # Light grey lower door trim
    # Front wheel-well cutouts & crisp redraw of front wheels
    fill_sym_box(grid, 4, 5, 25, 28, 3, 4, 4)
    fill_sym_wheel_x(
        grid, 4, 5, cy=26.5, cz=2.0,
        r_outer=2.35, r_rim=1.25, r_hub=0.65,
        tire_col=4, rim_col=6, hub_col=1,
    )
    # Upper cab greenhouse & sloped windshield (Y: 23..29, Z: 8..11)
    fill_sym_box(grid, 0, 5, 23, 28, 8, 10, 1)
    fill_sym_box(grid, 0, 4, 23, 27, 8, 9, 0)  # Hollow cab interior
    fill_sym_box(grid, 0, 4, 23, 27, 11, 11, 1)  # Cab roof blending into medical box
    # Sloped cyan windshield & side door windows
    fill_sym_box(grid, 0, 4, 28, 29, 8, 9, 7)
    fill_sym_box(grid, 0, 4, 27, 28, 10, 10, 7)
    fill_sym_box(grid, 4, 4, 28, 28, 8, 10, 4)  # A-pillars
    fill_sym_box(grid, 5, 5, 24, 27, 8, 10, 7)  # Side cab windows
    fill_sym_box(grid, 5, 5, 23, 23, 8, 10, 4)  # B-pillar
    # Side view mirrors
    fill_sym_box(grid, 6, 6, 27, 27, 8, 9, 4)
    fill_sym_box(grid, 5, 6, 27, 27, 8, 8, 5)
    # Front Chrome Radiator Grille & Glowing Amber Headlights (Y: 32, Z: 4..6)
    fill_sym_box(grid, 0, 2, 32, 32, 4, 6, 4)
    fill_sym_box(grid, 0, 2, 32, 32, 5, 5, 6)  # Chrome grille slat
    fill_sym_box(grid, 0, 0, 32, 32, 6, 6, 3)  # Red front emblem badge
    fill_sym_box(grid, 3, 4, 32, 32, 5, 6, 9)  # Glowing warm headlights
    fill_sym_box(grid, 5, 5, 31, 32, 5, 5, 9)  # Amber side turn signals

    # --- ICONIC ROOF EMERGENCY LIGHTBAR (Y: 20..22, Z: 15..16) ---
    fill_sym_box(grid, 0, 4, 20, 21, 15, 15, 5)  # Gunmetal mounting rack
    fill_box(grid, cx_r + 1, cx_r + 4, 20, 21, 15, 16, 3)  # Vivid Red right lightbar
    fill_box(grid, cx_l - 4, cx_l - 1, 20, 21, 15, 16, 8)  # Vivid Blue left lightbar
    fill_sym_box(grid, 0, 0, 20, 21, 15, 16, 1)            # Crisp white center strobe

    return grid


# ==========================================
# FORM B: HEROIC RESCUE AMBULANCE ROBOT (34 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((34, 24, 42), dtype=np.uint8)
    cx_l = grid.shape[0] // 2 - 1  # 16 (-X robot left, viewer's right)
    cx_r = grid.shape[0] // 2      # 17 (+X robot right, viewer's left)

    # --- STURDY RESCUE BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 3, 6, 7, 15, 0, 1, 5)    # Gunmetal bumper soles
    fill_sym_box(grid, 3, 6, 6, 8, 0, 2, 6)     # Chrome step-bumper heels
    fill_sym_box(grid, 3, 6, 10, 16, 1, 2, 1)   # White armored boot shell
    fill_sym_box(grid, 3, 6, 13, 16, 2, 2, 3)   # Vivid red toe guard stripe
    fill_sym_box(grid, 4, 5, 16, 16, 1, 2, 2)   # Light grey toe cap

    # --- BOXY AMBULANCE-BODY LOWER LEGS / SHINS (Z: 3..15) ---
    fill_sym_box(grid, 3, 6, 8, 13, 3, 14, 1)
    fill_sym_box(grid, 4, 5, 9, 12, 4, 13, 0)   # Hollow leg core
    fill_sym_box(grid, 3, 6, 13, 14, 4, 12, 1)  # Front white van-panel shins
    fill_sym_box(grid, 4, 5, 14, 14, 4, 11, 3)  # Iconic vertical red rescue stripe on shins!
    fill_sym_box(grid, 3, 3, 9, 12, 4, 13, 2)   # Inner light-grey panel
    # Heavy rescue knee guards
    fill_sym_box(grid, 3, 6, 13, 15, 12, 15, 3)
    fill_sym_box(grid, 4, 5, 15, 15, 13, 15, 1)
    fill_sym_box(grid, 4, 5, 15, 15, 14, 14, 6)
    # Rear van wheels mounted cleanly on outer calves (x_off: 6..7, Z: 5..9)
    fill_sym_wheel_x(
        grid, 6, 7, cy=10.5, cz=7.0,
        r_outer=2.45, r_rim=1.35, r_hub=0.65,
        tire_col=4, rim_col=6, hub_col=1,
    )
    # Rear door windows & tail lights on calf backs
    fill_sym_box(grid, 4, 5, 8, 8, 6, 9, 7)     # Cyan rear door window
    fill_sym_box(grid, 5, 6, 8, 8, 4, 5, 3)     # Red tail lights
    fill_sym_box(grid, 6, 6, 8, 8, 4, 4, 9)     # Amber turn marker

    # --- MECHANICAL THIGHS (Z: 15..20) ---
    fill_sym_box(grid, 3, 5, 8, 12, 15, 20, 2)
    fill_sym_box(grid, 4, 4, 9, 11, 16, 19, 0)  # Hollow thigh interior
    fill_sym_box(grid, 3, 5, 12, 13, 16, 19, 1)  # Crisp white front thigh armor
    fill_sym_box(grid, 4, 4, 13, 13, 17, 18, 5)  # Gunmetal hydraulic accent

    # --- WAIST / PELVIS (Z: 19..23) ---
    fill_sym_box(grid, 0, 5, 8, 12, 20, 22, 5)
    fill_sym_box(grid, 0, 4, 9, 11, 20, 22, 0)  # Hollow waist core
    # White waist armor skirts with vivid red rescue belt
    fill_sym_box(grid, 2, 5, 12, 13, 19, 22, 1)
    fill_sym_box(grid, 2, 5, 13, 13, 21, 21, 3)
    # Center heroic codpiece
    fill_sym_box(grid, 0, 1, 12, 14, 19, 22, 1)
    fill_sym_box(grid, 0, 1, 14, 14, 20, 21, 3)
    fill_sym_box(grid, 0, 0, 14, 14, 21, 21, 9)  # Warm amber belt buckle core
    # Side hip skirts
    fill_sym_box(grid, 5, 6, 9, 12, 20, 22, 1)
    fill_sym_box(grid, 6, 6, 10, 11, 20, 21, 3)

    # --- BOXY AMBULANCE TORSO & PROMINENT RED CROSS CHEST PLATE (Z: 23..33) ---
    # Main sturdy white ambulance-van torso block
    fill_sym_box(grid, 0, 5, 7, 13, 23, 32, 1)
    fill_sym_box(grid, 0, 4, 8, 12, 24, 31, 0)  # Hollow torso core
    # Recessed gunmetal & chrome abdomen ribs
    fill_sym_box(grid, 0, 4, 12, 13, 23, 24, 5)
    fill_sym_box(grid, 1, 3, 13, 13, 23, 24, 6)
    # PROMINENT WHITE CHEST PLATE WITH BOLD RED CROSS EMBLEM! (Y: 14..16, Z: 24..31)
    fill_sym_box(grid, 0, 4, 14, 16, 24, 31, 1)
    fill_sym_box(grid, 0, 3, 14, 15, 25, 30, 0)  # Hollow chest plate core
    # Light grey chamfered upper/lower chest bevels
    fill_sym_box(grid, 0, 4, 14, 15, 32, 32, 2)
    fill_sym_box(grid, 0, 4, 15, 16, 24, 24, 2)
    # BOLD 6x6 VIVID RED CROSS EMBLEM RIGHT ON CENTER CHEST (Y: 16, x_off: 0..2, Z: 25..30)!
    fill_sym_box(grid, 0, 0, 16, 16, 25, 30, 3)  # 2-wide x 6-tall vertical bar
    fill_sym_box(grid, 0, 2, 16, 16, 27, 28, 3)  # 6-wide x 2-tall horizontal bar
    # Outer chest ribs with glowing headlights & cyan medical status vents
    fill_sym_box(grid, 4, 4, 15, 16, 27, 28, 3)  # Red stripe wrapping chest flanks
    fill_sym_box(grid, 4, 4, 16, 16, 25, 26, 9)  # Glowing warm ambulance headlights!
    fill_sym_box(grid, 4, 4, 16, 16, 29, 30, 7)  # Cyan chest sensor vents
    # Collar armor framing neck
    fill_sym_box(grid, 2, 4, 9, 12, 32, 33, 2)

    # --- BACKPACK & CROWNING RED/BLUE EMERGENCY LIGHTBAR ARCH (Y: 3..7, Z: 22..36) ---
    # Folded ambulance front cab hood & grille on back
    fill_sym_box(grid, 0, 4, 4, 7, 23, 32, 1)
    fill_sym_box(grid, 0, 3, 5, 6, 24, 31, 0)   # Hollow backpack core
    fill_sym_box(grid, 0, 3, 3, 4, 25, 30, 2)   # Rear medical pack fairing
    fill_sym_box(grid, 0, 2, 3, 3, 26, 28, 6)   # Chrome van grille folded on back
    fill_sym_box(grid, 0, 2, 3, 3, 27, 27, 4)   # Grille slot
    fill_sym_box(grid, 3, 3, 3, 3, 26, 27, 9)   # Rear pack amber lights
    fill_sym_box(grid, 1, 3, 4, 5, 22, 23, 5)   # Lower rescue thruster nozzles
    # CROWNING ROOF EMERGENCY LIGHTBAR ARCH ABOVE SHOULDERS/BACKPACK! (Y: 6..8, Z: 33..37)
    fill_sym_box(grid, 2, 5, 6, 8, 33, 34, 5)   # Gunmetal lightbar pylon supports
    fill_sym_box(grid, 0, 7, 6, 8, 34, 34, 2)   # Wide lightbar crossbeam
    fill_box(grid, cx_r + 2, cx_r + 7, 6, 8, 35, 36, 3)   # Vivid Red right emergency bar!
    fill_box(grid, cx_l - 7, cx_l - 2, 6, 8, 35, 36, 8)   # Vivid Blue left emergency bar!
    fill_sym_box(grid, 0, 1, 6, 8, 35, 36, 1)             # Crisp white center siren strobe

    # --- FRONT-CAB SHOULDER PAULDRONS WITH VAN WHEELS (Z: 27..34, x_off: 6..10) ---
    fill_sym_box(grid, 6, 7, 9, 11, 29, 31, 5)  # Shoulder joint bridge
    fill_sym_box(grid, 7, 10, 8, 13, 28, 33, 1)
    fill_sym_box(grid, 8, 9, 9, 12, 29, 32, 0)  # Hollow shoulder core
    fill_sym_box(grid, 7, 9, 9, 12, 34, 34, 3)  # Vivid red upper shoulder trim
    # Angled cyan cab windshield glass panel on front of each shoulder!
    fill_sym_box(grid, 7, 9, 13, 13, 30, 32, 7)
    fill_sym_box(grid, 7, 9, 13, 13, 29, 29, 3)  # Red rescue shoulder stripe
    # Front ambulance wheels nestled cleanly on outer shoulders (x_off: 10..11)
    fill_sym_wheel_x(
        grid, 10, 11, cy=10.5, cz=30.5,
        r_outer=2.25, r_rim=1.25, r_hub=0.60,
        tire_col=4, rim_col=6, hub_col=1,
    )

    # --- UPPER ARMS, FOREARMS & FISTS (Z: 15..27) ---
    fill_sym_box(grid, 7, 9, 9, 11, 23, 27, 5)   # Gunmetal upper arms
    fill_sym_box(grid, 8, 9, 9, 11, 24, 26, 2)   # Light grey bicep armor
    # Crisp white rescue forearms
    fill_sym_box(grid, 7, 10, 8, 13, 17, 22, 1)
    fill_sym_box(grid, 8, 9, 9, 12, 18, 21, 0)   # Hollow forearm interior
    fill_sym_box(grid, 7, 10, 13, 13, 18, 21, 2)  # Front forearm guard
    fill_sym_box(grid, 8, 9, 13, 13, 19, 20, 3)   # Red forearm stripe
    # Mechanical fists
    fill_sym_box(grid, 7, 9, 9, 12, 15, 16, 5)
    fill_sym_box(grid, 7, 9, 12, 12, 15, 16, 6)   # Chrome knuckles

    # --- LEFT FOREARM (-X, viewer's right): WHEELED STRETCHER RESCUE SHIELD! ---
    # Mounted facing forward (+Y) on the front of the left forearm so its full face & Red Cross pop in 3/4 view!
    # Chrome mounting bracket connecting left forearm (Y=13) to shield back (Y=15)
    fill_box(grid, cx_l - 9, cx_l - 8, 13, 15, 18, 20, 6)
    # Main elongated Rescue Stretcher Shield plate (X: cx_l - 13..-7 [7 wide], Z: 13..25 [13 tall], Y: 15..16)
    fill_box(grid, cx_l - 12, cx_l - 8, 15, 16, 14, 24, 1)  # Crisp white stretcher shield bed
    fill_box(grid, cx_l - 11, cx_l - 9, 15, 15, 15, 23, 2)  # Light grey backplate contour
    # Tubular brushed chrome stretcher side safety rails & end push-bars!
    fill_box(grid, cx_l - 13, cx_l - 13, 15, 16, 13, 25, 6)  # Outer chrome rail
    fill_box(grid, cx_l - 7, cx_l - 7, 15, 16, 13, 25, 6)    # Inner chrome rail
    fill_box(grid, cx_l - 13, cx_l - 7, 15, 16, 25, 25, 6)   # Top chrome push-handle
    fill_box(grid, cx_l - 13, cx_l - 7, 15, 16, 13, 13, 6)   # Bottom chrome bumper rail
    # Red stretcher safety straps across upper and lower shield bed
    fill_box(grid, cx_l - 12, cx_l - 8, 16, 16, 23, 23, 3)
    fill_box(grid, cx_l - 12, cx_l - 8, 16, 16, 15, 15, 3)
    # Crisp centered 5x5 Vivid Red Cross Emblem on Stretcher Shield front face (Y=16, center X=cx_l-10, Z=19)!
    fill_box(grid, cx_l - 10, cx_l - 10, 16, 16, 17, 21, 3)  # Vertical bar
    fill_box(grid, cx_l - 12, cx_l - 8, 16, 16, 19, 19, 3)   # Horizontal bar
    # 4 Folded Stretcher Caster Wheels & Chrome Scissor Undercarriage on back corners of shield (Y: 14)
    for sz in (14, 24):
        fill_box(grid, cx_l - 12, cx_l - 12, 14, 14, sz, sz, 4)  # Dark rubber caster wheel
        fill_box(grid, cx_l - 8, cx_l - 8, 14, 14, sz, sz, 4)
    # Crossed chrome scissor-legs visible on rear of shield (Y=14)
    fill_box(grid, cx_l - 11, cx_l - 9, 14, 14, 16, 16, 6)
    fill_box(grid, cx_l - 11, cx_l - 9, 14, 14, 22, 22, 6)

    # --- RIGHT HAND (+X, viewer's left): RESCUE MED-BEAM / DEFIBRILLATOR MULTI-TOOL ---
    fill_box(grid, cx_r + 8, cx_r + 10, 13, 18, 16, 18, 5)   # Gunmetal tool housing
    fill_box(grid, cx_r + 8, cx_r + 10, 15, 18, 18, 18, 1)   # White upper shroud
    fill_box(grid, cx_r + 9, cx_r + 10, 14, 17, 17, 17, 3)   # Red rescue accent stripe
    fill_box(grid, cx_r + 8, cx_r + 10, 19, 21, 16, 17, 6)   # Twin chrome emitter prongs
    fill_box(grid, cx_r + 9, cx_r + 9, 19, 21, 17, 17, 7)    # Glowing cyan med-beam emitter
    fill_box(grid, cx_r + 10, cx_r + 10, 15, 17, 16, 16, 8)  # Emergency blue power cell

    # --- HEROIC RESCUE MEDIC HEAD & VISOR (Z: 33..41) ---
    # Neck
    fill_sym_box(grid, 0, 1, 9, 11, 32, 33, 5)
    # Main crisp white helmet block
    fill_sym_box(grid, 0, 2, 8, 12, 34, 38, 1)
    # Helmet crown & rescue medic ridge
    fill_sym_box(grid, 0, 2, 9, 13, 38, 39, 1)
    fill_sym_box(grid, 0, 0, 9, 13, 39, 40, 3)   # Vivid red medic helmet center crest
    # Bright cyan wrap-around visor
    fill_sym_box(grid, 0, 2, 13, 13, 36, 37, 7)
    # Chrome faceplate mouthguard
    fill_sym_box(grid, 0, 1, 13, 13, 34, 35, 6)
    fill_sym_box(grid, 0, 0, 13, 13, 34, 34, 5)
    # Helmet ear-comms pods with red (+X) & blue (-X) mini siren accents!
    fill_sym_box(grid, 3, 3, 9, 11, 35, 37, 2)
    fill_box(grid, cx_r + 3, cx_r + 3, 10, 10, 36, 38, 3)  # Red right ear beacon
    fill_box(grid, cx_l - 3, cx_l - 3, 10, 10, 36, 38, 8)  # Blue left ear beacon
    # Heroic swept white & red V-crest antennae
    fill_sym_box(grid, 1, 1, 13, 14, 39, 40, 1)
    fill_sym_box(grid, 2, 3, 12, 13, 40, 41, 3)

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
    v_a = export_vox(model_a, "ambulance_a.vox")
    v_b = export_vox(model_b, "ambulance_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: AMBULANCE VAN -> RESCUE MEDIC ROBOT",
        "1. HIGH-ROOF AMBULANCE VAN",
        "2. RESCUE MEDIC ROBOT",
        "preview_ambulance.png",
        yaw_a=40, pitch_a=22, yaw_b=32, pitch_b=20,
    )
    print(f"ambulance: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
