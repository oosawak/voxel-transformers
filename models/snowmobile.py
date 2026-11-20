import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
PALETTE = {
    1: (238, 246, 255, 255),  # Crisp Arctic White
    2: (24, 118, 224, 255),   # Bright Arctic Blue
    3: (16, 68, 148, 255),    # Deep Alpine Navy
    4: (255, 92, 32, 255),    # Vibrant Neon-Orange Racing Stripe
    5: (44, 50, 62, 255),     # Matte Track Rubber / Seat Charcoal
    6: (152, 168, 188, 255),  # Brushed Steel Struts / Handlebars / Shaft
    7: (26, 54, 96, 255),     # Dark Tinted Windscreen Glass
    8: (96, 230, 255, 255),   # Frost Cyan Highlight / Visor / Ice-Axe Edge
    9: (255, 228, 96, 255),   # Warm Bright Headlight Gold
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


def clear_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1):
    """Hollow out an interior box symmetrically."""
    fill_sym_box(grid, x_off0, x_off1, y0, y1, z0, z1, 0)


# ==========================================
# FORM A: SPORTY ALPINE SNOWMOBILE (20 x 40 x 16)
# ==========================================
def build_a():
    grid = np.zeros((20, 40, 16), dtype=np.uint8)

    # --- 1. REAR CATERPILLAR TRACK & SUSPENSION (Y: 2..21, Z: 0..4) ---
    fill_sym_box(grid, 0, 3, 4, 20, 0, 4, 5)
    fill_sym_box(grid, 0, 3, 3, 3, 1, 4, 5)
    fill_sym_box(grid, 0, 3, 21, 21, 1, 4, 5)
    # Hollow interior of track loop for realistic open suspension & lean voxel count
    clear_sym_box(grid, 0, 2, 5, 19, 1, 3)
    # Rubber tread ribs along bottom edges
    for ty in range(4, 21, 2):
        clear_sym_box(grid, 3, 3, ty, ty, 0, 0)
    # Steel suspension slide rail & bogie wheels visible on outer track flanks
    fill_sym_box(grid, 3, 3, 5, 19, 1, 1, 6)
    for wy in (4, 8, 12, 16, 20):
        fill_sym_box(grid, 3, 3, wy, wy, 2, 3, 6)
    fill_sym_box(grid, 0, 2, 4, 4, 2, 3, 6)    # Rear idler axle
    fill_sym_box(grid, 0, 2, 20, 20, 2, 3, 6)  # Front drive axle
    fill_sym_box(grid, 2, 2, 13, 14, 2, 3, 4)  # Rear coilover shock

    # --- 2. REAR TUNNEL, SNOW FLAP & RUNNING BOARDS (Y: 1..22, Z: 2..7) ---
    fill_sym_box(grid, 0, 3, 1, 1, 2, 5, 5)    # Rear snow flap
    fill_sym_box(grid, 0, 3, 2, 2, 5, 6, 3)
    # Sleek aluminum/white tunnel deck
    fill_sym_box(grid, 0, 3, 2, 21, 5, 6, 1)
    clear_sym_box(grid, 0, 2, 4, 20, 5, 5)     # Hollow under-deck
    fill_sym_box(grid, 3, 3, 3, 20, 5, 5, 6)   # Brushed steel tunnel side
    fill_sym_box(grid, 3, 3, 4, 19, 6, 6, 2)   # Arctic blue tunnel stripe
    # Slim running boards (footrests) leaving rubber track clearly visible underneath
    fill_sym_box(grid, 4, 4, 7, 20, 4, 5, 5)
    fill_sym_box(grid, 4, 4, 8, 19, 5, 5, 4)   # Neon-orange running board rail
    # Rear bumper grab handle & brake light
    fill_sym_box(grid, 0, 3, 1, 2, 6, 7, 6)
    fill_sym_box(grid, 0, 2, 2, 2, 7, 7, 4)    # Neon-orange taillight strip

    # --- 3. CUSHIONED SEAT & FUEL TANK (Y: 5..21, Z: 7..10) ---
    fill_sym_box(grid, 0, 2, 5, 16, 7, 9, 5)
    fill_sym_box(grid, 0, 1, 5, 14, 10, 10, 5)
    clear_sym_box(grid, 0, 1, 7, 15, 7, 8)     # Hollow seat core
    fill_sym_box(grid, 2, 2, 6, 14, 7, 8, 3)   # Navy seat bolster
    fill_sym_box(grid, 2, 2, 8, 13, 8, 8, 4)   # Orange side accent
    # Sculpted fuel tank ahead of seat
    fill_sym_box(grid, 0, 3, 16, 20, 7, 9, 2)
    fill_sym_box(grid, 0, 2, 16, 20, 10, 10, 1)
    clear_sym_box(grid, 0, 2, 17, 20, 7, 8)
    fill_sym_box(grid, 3, 3, 17, 20, 7, 8, 1)
    fill_sym_box(grid, 3, 3, 17, 20, 9, 9, 4)

    # --- 4. SLEEK AERODYNAMIC FRONT COWL / HOOD (Y: 20..34, Z: 4..11) ---
    # Lower belly pan & front bulkhead
    fill_sym_box(grid, 0, 3, 21, 31, 4, 5, 5)
    clear_sym_box(grid, 0, 2, 22, 30, 5, 5)
    # Sculpted forward-sloping alpine hood (Arctic Blue primary + White chevrons)
    fill_sym_box(grid, 0, 4, 21, 26, 6, 8, 2)
    fill_sym_box(grid, 0, 3, 21, 25, 9, 10, 2)
    fill_sym_box(grid, 0, 2, 21, 23, 11, 11, 2)
    # Smoothly sloping nose tiers
    fill_sym_box(grid, 0, 4, 27, 28, 6, 7, 2)
    fill_sym_box(grid, 0, 3, 26, 28, 8, 9, 2)
    fill_sym_box(grid, 0, 3, 29, 31, 6, 7, 2)
    fill_sym_box(grid, 0, 2, 29, 30, 8, 8, 2)
    fill_sym_box(grid, 0, 2, 32, 33, 5, 6, 2)
    fill_sym_box(grid, 0, 1, 31, 32, 7, 7, 1)
    # Hollow cowl interior cleanly
    clear_sym_box(grid, 0, 2, 22, 28, 6, 8)
    clear_sym_box(grid, 0, 1, 29, 30, 6, 7)

    # Crisp Arctic White hood racing panels & smooth sloped center spline
    fill_sym_box(grid, 0, 0, 22, 25, 10, 10, 1)
    fill_sym_box(grid, 0, 0, 26, 28, 9, 9, 1)
    fill_sym_box(grid, 0, 0, 29, 30, 8, 8, 1)
    fill_sym_box(grid, 0, 0, 31, 32, 7, 7, 1)
    fill_sym_box(grid, 4, 4, 22, 27, 7, 8, 1)   # White upper side fairings
    fill_sym_box(grid, 3, 3, 28, 30, 7, 7, 1)
    # Deep Navy lower intake louvers
    fill_sym_box(grid, 4, 4, 22, 27, 6, 6, 3)
    fill_sym_box(grid, 3, 3, 28, 30, 6, 6, 3)
    # Vibrant Neon-Orange diagonal racing stripes sweeping forward down the cowl!
    fill_sym_box(grid, 3, 3, 21, 24, 9, 9, 4)
    fill_sym_box(grid, 4, 4, 24, 27, 8, 8, 4)
    fill_sym_box(grid, 3, 3, 28, 30, 7, 7, 4)
    fill_sym_box(grid, 2, 2, 31, 32, 6, 6, 4)

    # Bright Headlight integrated cleanly into nose (+Y)
    fill_sym_box(grid, 0, 1, 32, 33, 6, 6, 9)
    fill_sym_box(grid, 0, 0, 33, 33, 6, 7, 9)
    fill_sym_box(grid, 1, 1, 32, 32, 7, 7, 9)
    # Sleek front bullbar bumper
    fill_sym_box(grid, 0, 2, 33, 34, 4, 5, 5)
    fill_sym_box(grid, 0, 1, 34, 34, 5, 5, 6)

    # --- 5. TINTED WINDSCREEN WITH CLEAN CYAN HIGHLIGHT (Y: 21..26, Z: 10..15) ---
    fill_sym_box(grid, 0, 3, 25, 25, 10, 11, 7)
    fill_sym_box(grid, 0, 2, 24, 24, 11, 12, 7)
    fill_sym_box(grid, 0, 2, 23, 23, 12, 13, 7)
    fill_sym_box(grid, 0, 1, 22, 22, 13, 14, 7)
    fill_sym_box(grid, 0, 1, 21, 21, 14, 14, 7)
    # Crisp diagonal frost-cyan specular highlight on windscreen (asymmetric glint looks real!)
    fill_box(grid, 10, 11, 25, 25, 11, 11, 8)
    fill_box(grid, 9, 10, 24, 24, 12, 12, 8)
    fill_box(grid, 8, 9, 23, 23, 13, 13, 8)
    fill_sym_box(grid, 3, 3, 25, 25, 10, 10, 4)  # Orange windscreen base clip

    # --- 6. STEERING COLUMN & HANDLEBARS (Y: 19..21, Z: 10..14) ---
    fill_sym_box(grid, 0, 0, 20, 21, 10, 13, 6)  # Steering riser post
    fill_sym_box(grid, 0, 4, 20, 20, 13, 13, 6)  # Steel handlebar tube
    fill_sym_box(grid, 4, 6, 19, 20, 13, 13, 5)  # Dark rubber grips
    fill_sym_box(grid, 5, 6, 21, 21, 13, 14, 4)  # Compact neon-orange handguards

    # --- 7. ARTICULATED FRONT A-ARM STRUTS & COILOVERS (Y: 25..29, Z: 1..6) ---
    fill_sym_box(grid, 4, 7, 26, 26, 3, 3, 6)    # Rear lower A-arm
    fill_sym_box(grid, 4, 7, 29, 29, 3, 3, 6)    # Front lower A-arm
    fill_sym_box(grid, 4, 7, 27, 28, 5, 5, 6)    # Upper A-arm
    # Diagonal neon-orange coilover shock absorbers
    fill_sym_box(grid, 5, 5, 27, 28, 5, 6, 4)
    fill_sym_box(grid, 6, 6, 27, 28, 3, 5, 4)
    # Vertical steel ski spindles
    fill_sym_box(grid, 7, 7, 27, 28, 1, 5, 6)
    fill_sym_box(grid, 7, 7, 27, 28, 2, 2, 5)

    # --- 8. TWIN LONG CURVED FRONT SKIS (x_off: 6..8, Y: 22..39, Z: 0..5) ---
    # Grounded charcoal carbide keel & wide ski runner deck
    fill_sym_box(grid, 6, 8, 23, 34, 0, 0, 5)
    fill_sym_box(grid, 6, 8, 23, 34, 1, 1, 2)
    fill_sym_box(grid, 7, 7, 23, 35, 1, 1, 1)    # White center ski ridge
    # Rear ski tail
    fill_sym_box(grid, 6, 8, 22, 22, 1, 1, 2)
    # Sleek curved upturned alpine ski tips!
    fill_sym_box(grid, 6, 8, 35, 35, 1, 2, 2)
    fill_sym_box(grid, 7, 7, 35, 35, 2, 2, 1)
    fill_sym_box(grid, 6, 8, 36, 36, 2, 2, 2)
    fill_sym_box(grid, 7, 7, 36, 37, 3, 3, 1)
    fill_sym_box(grid, 6, 8, 37, 37, 3, 3, 4)
    fill_sym_box(grid, 7, 7, 37, 38, 3, 4, 4)    # Solidly connected curved orange ski tip
    fill_sym_box(grid, 7, 7, 38, 39, 4, 5, 4)    # Tapered neon-orange upturned ski tip
    fill_sym_box(grid, 7, 7, 37, 38, 5, 5, 5)    # Dark ski tip loop

    return grid


# ==========================================
# FORM B: ARCTIC SNOWMOBILE ROBOT (36 x 24 x 42)
# ==========================================
def build_b():
    grid = np.zeros((36, 24, 42), dtype=np.uint8)
    cx_l = 17  # -X side (robot left)
    cx_r = 18  # +X side (robot right)

    # --- 1. SKI-BLADE SNOW-BOOT FEET (Z: 0..4, x_off: 3..6) ---
    # Twin front skis become unmistakable long armored ski-blade feet!
    fill_sym_box(grid, 3, 6, 5, 17, 0, 0, 5)     # Grounded carbide ski keel
    fill_sym_box(grid, 3, 6, 6, 17, 1, 1, 2)     # Bright arctic blue ski blade
    fill_sym_box(grid, 4, 5, 7, 17, 2, 2, 1)     # Crisp white center ski ridge
    # Rear stabilizer heel ski tail
    fill_sym_box(grid, 4, 5, 3, 5, 1, 1, 2)
    fill_sym_box(grid, 4, 5, 3, 4, 2, 2, 4)      # Orange rear heel tail
    # Long dramatic curved upturned ski-blade toe tips!
    fill_sym_box(grid, 3, 6, 18, 18, 1, 2, 2)
    fill_sym_box(grid, 4, 5, 18, 18, 2, 2, 1)
    fill_sym_box(grid, 3, 6, 19, 19, 2, 2, 2)
    fill_sym_box(grid, 4, 5, 19, 20, 3, 3, 4)
    fill_sym_box(grid, 4, 5, 20, 21, 4, 4, 4)    # Sharp upturned neon-orange ski tip
    fill_sym_box(grid, 4, 5, 19, 20, 4, 4, 5)    # Ski loop accent
    # Steel ski-spindle ankle clamp & orange shock
    fill_sym_box(grid, 4, 5, 10, 13, 2, 4, 6)
    fill_sym_box(grid, 6, 6, 10, 12, 2, 3, 4)

    # --- 2. LOWER LEGS / SHIN RUNNERS + SPLIT CATERPILLAR TRACK CALVES (Z: 4..14) ---
    # Inner leg structural core (hollowed internally for lean voxel budget)
    fill_sym_box(grid, 3, 5, 9, 13, 4, 13, 3)
    clear_sym_box(grid, 4, 4, 10, 12, 5, 12)
    # Front shin ski-runner armor plates
    fill_sym_box(grid, 3, 5, 13, 14, 4, 13, 1)
    fill_sym_box(grid, 4, 4, 14, 15, 5, 12, 2)
    fill_sym_box(grid, 5, 5, 13, 14, 6, 11, 4)   # Neon-orange racing stripe down shin
    # Outer steel A-arm strut guard & exposed orange coilover spring
    fill_sym_box(grid, 6, 6, 10, 12, 5, 12, 6)
    fill_sym_box(grid, 6, 6, 11, 11, 7, 10, 4)
    # SPLIT CATERPILLAR TRACK PODS on backs of calves (Y: 6..9, Z: 4..13)!
    fill_sym_box(grid, 3, 6, 6, 9, 4, 13, 5)
    clear_sym_box(grid, 4, 5, 7, 8, 5, 12)       # Hollow unseen inner track pod
    for tz in range(4, 14, 2):
        clear_sym_box(grid, 4, 5, 6, 6, tz, tz)  # Ribbed rubber tread notches
    for tz in (5, 8, 11):
        fill_sym_box(grid, 6, 6, 7, 8, tz, tz, 6)  # Steel bogie rollers
    # Sharp alpine knee guards (Z: 12..15)
    fill_sym_box(grid, 3, 5, 14, 15, 12, 14, 2)
    fill_sym_box(grid, 4, 4, 15, 16, 13, 15, 1)
    fill_sym_box(grid, 4, 4, 16, 16, 14, 14, 4)

    # --- 3. THIGHS (Z: 14..19, x_off: 3..5) ---
    fill_sym_box(grid, 3, 5, 9, 13, 14, 19, 6)
    clear_sym_box(grid, 4, 4, 10, 12, 15, 18)    # Hollow thigh core
    fill_sym_box(grid, 3, 5, 12, 14, 15, 18, 1)  # Crisp white front thigh armor
    fill_sym_box(grid, 5, 5, 10, 13, 15, 18, 2)  # Arctic blue outer thigh plate
    fill_sym_box(grid, 3, 4, 9, 10, 15, 18, 5)   # Dark rear hydraulic backing
    # Hip bridge inward to pelvis
    fill_sym_box(grid, 2, 3, 10, 12, 18, 20, 5)

    # --- 4. WAIST / PELVIS (Z: 19..23, x_off: 0..5) ---
    fill_sym_box(grid, 0, 5, 9, 13, 19, 21, 5)
    clear_sym_box(grid, 0, 3, 10, 12, 20, 20)
    fill_sym_box(grid, 1, 4, 13, 14, 19, 21, 1)  # White front waist skirts
    fill_sym_box(grid, 2, 3, 14, 14, 19, 20, 2)
    fill_sym_box(grid, 0, 1, 13, 15, 19, 22, 3)  # Deep navy center codpiece
    fill_sym_box(grid, 0, 0, 15, 15, 20, 22, 4)  # Neon-orange belt buckle
    fill_sym_box(grid, 5, 5, 10, 13, 19, 21, 2)  # Side hip skirts
    fill_sym_box(grid, 5, 5, 11, 12, 19, 20, 4)
    fill_sym_box(grid, 0, 4, 8, 9, 19, 21, 3)    # Rear pelvis armor
    # Nimble tapered waist core
    fill_sym_box(grid, 0, 2, 9, 13, 21, 23, 5)
    fill_sym_box(grid, 0, 2, 12, 13, 22, 23, 6)

    # --- 5. TORSO / CHEST (Z: 23..33) — AERODYNAMIC SNOWMOBILE COWL! ---
    fill_sym_box(grid, 0, 5, 8, 14, 24, 32, 2)
    fill_sym_box(grid, 0, 4, 9, 13, 23, 24, 3)
    clear_sym_box(grid, 0, 4, 9, 13, 25, 31)     # Hollow torso cavity
    fill_sym_box(grid, 0, 5, 9, 13, 31, 32, 1)   # White upper shoulder yoke
    fill_sym_box(grid, 4, 5, 11, 14, 25, 30, 1)
    # PROMINENT FORWARD-ANGLED SNOWMOBILE COWL CHEST ARMOR (Y: 14..18)
    fill_sym_box(grid, 0, 4, 14, 15, 24, 29, 2)
    fill_sym_box(grid, 0, 3, 16, 16, 25, 29, 2)
    fill_sym_box(grid, 0, 2, 17, 17, 25, 28, 2)
    fill_sym_box(grid, 0, 1, 18, 18, 26, 27, 1)
    clear_sym_box(grid, 0, 2, 14, 15, 26, 28)    # Hollow cowl chest cavity
    # Crisp White cowl ridge & flank accents
    fill_sym_box(grid, 0, 0, 15, 17, 28, 29, 1)
    fill_sym_box(grid, 3, 4, 14, 15, 26, 28, 1)
    # Deep Navy lower intake louvers
    fill_sym_box(grid, 3, 4, 14, 15, 24, 25, 3)
    # Vibrant Neon-Orange diagonal racing stripes sweeping across chest cowl!
    fill_sym_box(grid, 4, 4, 14, 15, 28, 29, 4)
    fill_sym_box(grid, 3, 3, 15, 16, 27, 27, 4)
    fill_sym_box(grid, 2, 2, 16, 17, 26, 26, 4)
    # BRIGHT HEADLIGHT embedded in center of chest cowl nose!
    fill_sym_box(grid, 0, 1, 18, 18, 26, 27, 9)
    fill_sym_box(grid, 1, 1, 17, 17, 27, 27, 9)
    # TINTED WINDSCREEN COLLAR WITH CRISP CYAN GLINT across upper chest!
    fill_sym_box(grid, 0, 3, 14, 15, 30, 31, 7)
    fill_sym_box(grid, 0, 2, 13, 14, 32, 32, 7)
    # Asymmetric diagonal frost-cyan glass reflection
    fill_box(grid, cx_r + 1, cx_r + 2, 15, 15, 30, 30, 8)
    fill_box(grid, cx_r, cx_r + 1, 15, 15, 31, 31, 8)
    fill_box(grid, cx_l, cx_r, 14, 14, 32, 32, 8)
    fill_sym_box(grid, 3, 3, 14, 14, 30, 30, 4)

    # --- 6. BACKPACK (Y: 4..8, Z: 23..33) — SEAT, REAR TUNNEL & THRUSTERS ---
    fill_sym_box(grid, 0, 3, 5, 7, 24, 32, 1)
    clear_sym_box(grid, 0, 2, 6, 7, 25, 31)      # Hollow backpack interior
    fill_sym_box(grid, 0, 2, 4, 5, 25, 31, 5)    # Folded dark cushioned seat pad
    fill_sym_box(grid, 3, 3, 5, 7, 25, 31, 2)    # Arctic blue tunnel trim
    fill_sym_box(grid, 0, 2, 4, 4, 31, 31, 4)    # Rear brake light bar
    # Twin winter-recon thruster nozzles
    fill_sym_box(grid, 2, 3, 4, 6, 22, 24, 6)
    fill_sym_box(grid, 2, 3, 4, 5, 22, 22, 8)    # Frost-cyan thruster glow

    # --- 7. SHOULDERS & HANDLEBAR ANTENNAS (Z: 27..38) ---
    fill_sym_box(grid, 5, 6, 10, 12, 28, 30, 5)  # Shoulder joint bridges
    # Sleek sloped alpine pauldrons
    fill_sym_box(grid, 6, 9, 9, 13, 28, 32, 1)
    clear_sym_box(grid, 7, 8, 10, 12, 29, 31)    # Hollow shoulder interiors
    fill_sym_box(grid, 7, 9, 9, 13, 31, 33, 2)
    fill_sym_box(grid, 9, 10, 10, 12, 28, 31, 2)
    fill_sym_box(grid, 7, 9, 13, 13, 29, 30, 4)  # Front shoulder racing stripe
    fill_sym_box(grid, 7, 9, 9, 9, 29, 30, 4)    # Rear shoulder racing stripe
    fill_sym_box(grid, 6, 8, 10, 12, 33, 33, 3)  # Deep navy shoulder crest
    # HANDLEBAR / STRUT SHOULDER ANTENNAS rising cleanly up & outward!
    fill_sym_box(grid, 8, 8, 10, 11, 34, 35, 6)  # Steel handlebar stalk
    fill_sym_box(grid, 9, 9, 10, 11, 35, 37, 6)
    fill_sym_box(grid, 9, 10, 10, 10, 37, 38, 5) # Handlebar grip tip
    fill_sym_box(grid, 9, 10, 11, 11, 36, 37, 4) # Neon-orange handguard fin

    # --- 8. ARMS, LEFT SNOW-SHIELD & RIGHT FROST-PIKE (Z: 7..36) ---
    # Upper arms (angled slightly outward for athletic silhouette)
    fill_sym_box(grid, 7, 8, 10, 12, 23, 27, 5)
    fill_sym_box(grid, 8, 8, 10, 12, 24, 26, 6)
    # Forearms (sculpted winter-recon gauntlets)
    fill_sym_box(grid, 8, 10, 9, 14, 17, 22, 1)
    clear_sym_box(grid, 9, 9, 10, 13, 18, 21)    # Hollow forearm core
    fill_sym_box(grid, 9, 10, 10, 13, 18, 21, 2)
    fill_sym_box(grid, 10, 10, 11, 12, 18, 21, 4)
    fill_sym_box(grid, 8, 10, 14, 14, 18, 21, 3)
    # Articulated charcoal fists
    fill_sym_box(grid, 8, 10, 10, 13, 15, 16, 5)

    # LEFT ARM (-X, x = cx_l - 12 .. cx_l - 11): Compact Alpine Snow-Shield
    fill_box(grid, cx_l - 11, cx_l - 11, 10, 15, 16, 23, 1)
    fill_box(grid, cx_l - 12, cx_l - 12, 11, 14, 17, 22, 2)
    fill_box(grid, cx_l - 12, cx_l - 12, 12, 13, 16, 17, 4)  # Orange chevron
    fill_box(grid, cx_l - 12, cx_l - 12, 12, 13, 21, 22, 8)  # Frost sensor strip
    fill_box(grid, cx_l - 11, cx_l - 10, 11, 13, 18, 20, 6)  # Shield mount

    # RIGHT HAND (+X, x = cx_r + 10 .. cx_r + 16): FROST-PIKE / ICE-AXE!
    # Held cleanly OUTBOARD of the right arm/leg so its silhouette pops sharply!
    # Horizontal wrist grip bridge from right fist (cx_r+10) out to pike shaft (cx_r+11..12)
    fill_box(grid, cx_r + 10, cx_r + 11, 11, 12, 15, 16, 5)  # Fist gripping shaft
    # Brushed steel Frost-Pike shaft standing cleanly clear to +X (cx_r + 11..12)
    fill_box(grid, cx_r + 11, cx_r + 11, 11, 12, 5, 31, 6)
    fill_box(grid, cx_r + 11, cx_r + 11, 11, 12, 14, 17, 5)  # Wrapped handle grip
    fill_box(grid, cx_r + 11, cx_r + 11, 11, 12, 3, 4, 8)    # Spiked frost butt-cap
    # Neon-orange & deep-navy axe collar
    fill_box(grid, cx_r + 11, cx_r + 12, 11, 13, 27, 29, 3)
    fill_box(grid, cx_r + 11, cx_r + 12, 11, 12, 26, 26, 4)
    # Top frost-spear crystal point
    fill_box(grid, cx_r + 11, cx_r + 11, 11, 12, 32, 33, 6)
    fill_box(grid, cx_r + 11, cx_r + 11, 11, 12, 34, 36, 8)
    # Outward-sweeping Frost Ice-Axe Blade (+X, cleanly silhouetted against dark sky!)
    fill_box(grid, cx_r + 12, cx_r + 14, 11, 12, 26, 30, 2)  # Arctic blue axe body
    fill_box(grid, cx_r + 14, cx_r + 15, 11, 12, 25, 31, 8)  # Glowing frost-cyan blade edge
    fill_box(grid, cx_r + 16, cx_r + 16, 11, 12, 26, 30, 8)  # Curved razor frost edge
    fill_box(grid, cx_r + 13, cx_r + 14, 11, 12, 24, 25, 8)  # Lower axe beard hook
    # Inner counter-pick hook facing slightly forward (+Y)
    fill_box(grid, cx_r + 11, cx_r + 11, 13, 14, 28, 29, 6)
    fill_box(grid, cx_r + 11, cx_r + 11, 15, 16, 27, 28, 8)

    # --- 9. SCULPTED HEAD WITH SNOW-GOGGLE VISOR & ALPINE CREST (Z: 32..40) ---
    fill_sym_box(grid, 0, 1, 10, 12, 32, 33, 5)  # Neck
    # Sleek winter-recon helmet
    fill_sym_box(grid, 0, 2, 9, 13, 34, 37, 1)
    fill_sym_box(grid, 0, 1, 9, 13, 38, 38, 2)   # Tapered arctic blue crown
    fill_sym_box(grid, 0, 0, 10, 13, 39, 39, 3)  # Deep navy central crown ridge
    # Glowing Frost-Cyan Snow-Goggle Visor
    fill_sym_box(grid, 0, 2, 13, 14, 35, 36, 8)
    fill_sym_box(grid, 0, 1, 14, 14, 34, 34, 6)  # Steel chin vent
    # Neon-orange forehead gem & sharp swept V-fin alpine crest
    fill_sym_box(grid, 0, 0, 13, 14, 37, 38, 4)
    fill_sym_box(grid, 1, 1, 13, 14, 38, 38, 1)
    fill_sym_box(grid, 2, 2, 12, 13, 38, 39, 2)
    fill_sym_box(grid, 3, 3, 11, 12, 39, 40, 4)  # Sharp orange crest tips
    # Compact ear comm-pods
    fill_sym_box(grid, 3, 3, 10, 11, 35, 36, 6)

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
    v_a = export_vox(model_a, "snowmobile_a.vox")
    v_b = export_vox(model_b, "snowmobile_b.vox")
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: SNOWMOBILE -> ARCTIC SNOWMOBILE ROBOT",
        "1. SNOWMOBILE",
        "2. ARCTIC SNOWMOBILE ROBOT",
        "preview_snowmobile.png",
        yaw_a=42, pitch_a=24, yaw_b=32, pitch_b=20,
    )
    print(f"snowmobile: A={v_a} voxels {model_a.shape}, B={v_b} voxels {model_b.shape}")
