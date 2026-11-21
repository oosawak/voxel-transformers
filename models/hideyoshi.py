import struct
import numpy as np
from PIL import Image, ImageDraw

# Color Palette (Index 1..9, 0 is empty)
# Shared across Toyotomi Hideyoshi Robot (Form A) and Armored Monkey (Form B)
PALETTE = {
    1: (244, 196, 46, 255),   # Gleaming Imperial Gold (Sunburst Kabuto, Gourds, Armor)
    2: (186, 128, 34, 255),   # Warm Antique Gold / Bronze Shading & Trim
    3: (208, 44, 42, 255),    # Crimson-Vermilion Lacquer / Macaque Red Face & Collar
    4: (136, 24, 28, 255),    # Deep Crimson Shadow / Armor Backing & Face Depth
    5: (156, 100, 56, 255),   # Warm Ochre-Brown Fur / Bronze-Brown Under-Armor
    6: (96, 58, 34, 255),     # Rich Dark Umber Fur Shading / Dark Bronze Limbs
    7: (244, 236, 216, 255),  # Cream-White Silk Cords / Macaque Cheek Ruff & Belly Fur
    8: (46, 48, 56, 255),     # Charcoal Iron Kabuto Bowl / Joints / Pupils & Claws
    9: (255, 236, 118, 255),  # Radiant Sun-Yellow Highlights / Glowing Eyes & Crests
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
    """Hollow strictly interior voxels (all 26 neighbors occupied) to preserve 6-connectivity."""
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


def fill_sphere_local(grid, cx, cy, cz, rx, ry, rz, col):
    """Fill an ellipsoid centered at (cx, cy, cz)."""
    X, Y, Z = grid.shape
    x0 = max(0, int(np.floor(cx - rx)))
    x1 = min(X - 1, int(np.ceil(cx + rx)))
    y0 = max(0, int(np.floor(cy - ry)))
    y1 = min(Y - 1, int(np.ceil(cy + ry)))
    z0 = max(0, int(np.floor(cz - rz)))
    z1 = min(Z - 1, int(np.ceil(cz + rz)))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                d2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2
                if d2 <= 1.0:
                    grid[x, y, z] = col


def fill_tube(grid, p0, p1, r0, r1, col, steps=16):
    """Fill a 6-connected tapered cylindrical limb/tail segment from p0 to p1."""
    for i in range(steps + 1):
        t = i / float(steps)
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        z = p0[2] + (p1[2] - p0[2]) * t
        r = r0 + (r1 - r0) * t
        fill_sphere_local(grid, x, y, z, r, r, r, col)


def fill_gourd(grid, cx, cy, cz_bot, scale=1.0, main_col=1, shade_col=2, cord_col=3, hi_col=9):
    """
    Sculpt an unmistakable 3D golden figure-8 gourd (Hyotan / 瓢箪) centered at (cx, cy)
    with bottom at cz_bot. Includes large lower bulb, cinched crimson cord waist,
    smaller upper bulb, and bright golden stem cap.
    """
    r_lo = 1.90 * scale
    r_hi = 1.32 * scale
    z_lo = cz_bot + r_lo * 0.85
    z_waist = cz_bot + r_lo * 1.90
    z_hi = cz_bot + r_lo * 2.65

    # Lower bulbous belly
    fill_sphere_local(grid, cx, cy, z_lo, r_lo, r_lo, r_lo * 0.96, main_col)
    # Antique-gold underside shading
    fill_sphere_local(grid, cx, cy, cz_bot + 0.55 * scale, r_lo * 0.72, r_lo * 0.72, 0.78 * scale, shade_col)
    # Cinched crimson silk ribbon around gourd waist
    fill_sphere_local(grid, cx, cy, z_waist, r_hi * 0.82, r_hi * 0.82, 0.68 * scale, cord_col)
    # Upper smaller bulb
    fill_sphere_local(grid, cx, cy, z_hi, r_hi, r_hi, r_hi * 0.96, main_col)
    # Bright sun-yellow highlight on front/top of bulbs
    ix = int(round(cx))
    iy_f = int(round(cy + r_lo * 0.65))
    iz_lo = int(round(z_lo + 0.3 * scale))
    iz_hi = int(round(z_hi + r_hi * 0.70))
    X, Y, Z = grid.shape
    if 0 <= ix < X and 0 <= iy_f < Y and 0 <= iz_lo < Z:
        grid[ix, iy_f, iz_lo] = hi_col
    if 0 <= ix < X and 0 <= int(round(cy)) < Y and 0 <= iz_hi < Z:
        grid[ix, int(round(cy)), iz_hi] = hi_col


# ==========================================
# FORM A: TOYOTOMI HIDEYOSHI ROBOT (42 x 28 x 48)
# ==========================================
def build_a():
    grid = np.zeros((42, 28, 48), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx_l = X // 2 - 1  # 20 (-X robot left)
    cx_r = X // 2      # 21 (+X robot right)

    # --- AGILE SAMURAI FEET / ARMORED TABI BOOTS (Z: 0..3) ---
    fill_sym_box(grid, 2, 5, 10, 17, 0, 1, 8)    # Charcoal iron waraji sole
    fill_sym_box(grid, 2, 5, 11, 16, 1, 2, 6)    # Dark bronze boot body
    fill_sym_box(grid, 2, 5, 16, 18, 1, 2, 1)    # Gleaming gold toe guard
    fill_sym_box(grid, 3, 4, 18, 18, 1, 1, 9)    # Bright gold toe tip
    fill_sym_box(grid, 3, 4, 15, 16, 2, 2, 7)    # Cream-white tabi strap
    fill_sym_box(grid, 2, 5, 11, 15, 3, 3, 3)    # Crimson ankle cord cuff

    # --- AGILE LOWER LEGS / GOLDEN SUNEATE SHINGUARDS (Z: 4..13) ---
    fill_sym_box(grid, 2, 4, 11, 15, 4, 12, 5)   # Warm brown-ochre inner leg
    fill_sym_box(grid, 2, 4, 11, 12, 4, 12, 6)   # Dark umber calf backing
    # Gleaming gold vertical splint shin guards
    fill_sym_box(grid, 2, 4, 15, 15, 4, 11, 1)
    fill_sym_box(grid, 3, 3, 15, 16, 5, 10, 2)
    fill_sym_box(grid, 4, 4, 12, 14, 5, 10, 1)   # Outer gold shin plate
    # Crimson shin bindings & cream lacing
    fill_sym_box(grid, 2, 4, 11, 15, 6, 6, 3)
    fill_sym_box(grid, 2, 4, 11, 15, 10, 10, 3)
    fill_sym_box(grid, 3, 3, 16, 16, 6, 6, 7)
    # Ornate Golden Knee Armor (Tateage)
    fill_sym_box(grid, 2, 4, 14, 16, 11, 14, 1)
    fill_sym_box(grid, 3, 3, 16, 17, 12, 14, 9)
    fill_sym_box(grid, 2, 4, 14, 15, 11, 11, 4)

    # --- ATHLETIC THIGHS / HAIDATE ARMOR (Z: 14..18) ---
    fill_sym_box(grid, 2, 4, 11, 15, 14, 18, 6)  # Dark bronze-brown thigh core
    fill_sym_box(grid, 2, 4, 13, 15, 15, 18, 5)  # Warm ochre-brown thigh muscles
    fill_sym_box(grid, 3, 4, 15, 15, 15, 17, 3)  # Crimson thigh lamellar
    fill_sym_box(grid, 4, 4, 12, 14, 15, 17, 2)  # Bronze outer thigh plate

    # --- WAIST, KUSAZURI TASSETS & HIP GOLDEN GOURDS (Z: 18..23) ---
    fill_sym_box(grid, 0, 4, 10, 15, 19, 22, 8)  # Inner iron pelvis frame
    # Flared Crimson & Gold Kusazuri War Skirt
    fill_sym_box(grid, 0, 4, 14, 16, 18, 21, 3)  # Front crimson tassets
    fill_sym_box(grid, 0, 4, 9, 11, 18, 21, 3)   # Rear crimson tassets
    fill_sym_box(grid, 0, 4, 16, 16, 18, 18, 1)  # Gold lower front trim
    fill_sym_box(grid, 0, 4, 9, 9, 18, 18, 1)    # Gold lower rear trim
    fill_sym_box(grid, 1, 3, 16, 16, 20, 20, 1)  # Gold lamellar stripe
    # Cream-white silk obi sash & golden Taiko center buckle
    fill_sym_box(grid, 0, 4, 10, 16, 21, 22, 7)
    fill_sym_box(grid, 0, 1, 15, 17, 20, 22, 1)
    fill_sym_box(grid, 0, 0, 17, 17, 21, 21, 9)
    fill_sym_box(grid, 0, 1, 15, 16, 18, 19, 4)

    # HIP GOLDEN GOURDS (腰の瓢箪) mounted prominently at front-outer hips!
    fill_sym_box(grid, 4, 5, 13, 15, 20, 21, 3)  # Crimson hip mount strap
    for xc in (cx_l - 6.0, cx_r + 6.0):
        fill_gourd(grid, xc, 14.8, 16.5, scale=0.90, main_col=1, shade_col=2, cord_col=3, hi_col=9)

    # --- FLAMBOYANT GOLDEN & CRIMSON TAIKO TORSO (Z: 23..32) ---
    # Tapered agile abdomen
    fill_sym_box(grid, 0, 3, 11, 15, 22, 24, 4)
    fill_sym_box(grid, 0, 3, 14, 15, 22, 24, 3)
    fill_sym_box(grid, 1, 2, 15, 16, 23, 24, 1)
    fill_sym_box(grid, 0, 0, 15, 16, 23, 24, 7)

    # Broad heroic golden Dō cuirass with crimson odoshi lacing
    fill_sym_box(grid, 0, 5, 10, 15, 25, 31, 1)  # Gleaming gold main chest armor
    fill_sym_box(grid, 0, 4, 15, 16, 25, 30, 1)  # Sculpted front chest bevel
    # Crimson lamellar ribs & central breastplate across chest
    fill_sym_box(grid, 1, 4, 16, 16, 26, 26, 3)
    fill_sym_box(grid, 2, 4, 16, 16, 28, 28, 3)
    fill_sym_box(grid, 0, 2, 15, 17, 27, 30, 3)  # Crimson chest breastplate core
    fill_sym_box(grid, 0, 1, 17, 17, 28, 29, 1)  # Golden Paulownia / Sun chest crest
    fill_sym_box(grid, 0, 0, 17, 17, 29, 29, 9)  # Sun-yellow chest jewel
    # Cream-white silk haori chest cords (agemaki)
    fill_sym_box(grid, 2, 2, 16, 17, 29, 30, 7)
    fill_sym_box(grid, 1, 1, 16, 17, 26, 26, 7)
    # Bronze shoulder-collar armor plates
    fill_sym_box(grid, 3, 5, 11, 15, 31, 31, 2)

    # HIGH FLARED CRIMSON JINBAORI COLLAR (reused directly as Monkey's crimson collar!)
    fill_sym_box(grid, 0, 4, 9, 15, 31, 32, 3)
    fill_sym_box(grid, 2, 4, 9, 14, 32, 33, 3)
    fill_sym_box(grid, 3, 4, 10, 14, 33, 33, 1)  # Gold collar rim
    fill_sym_box(grid, 1, 2, 15, 16, 31, 32, 7)  # Cream collar lapels
    fill_sym_box(grid, 0, 2, 9, 10, 32, 33, 4)   # Deep crimson rear neck guard

    # --- SHOULDER ARMOR: GOLDEN GOURD PAULDRONS (肩の瓢箪装甲, Z: 25..34) ---
    fill_sym_box(grid, 5, 7, 11, 14, 28, 31, 8)  # Iron shoulder joint axle
    # Deep crimson samurai sode backing plates so the outer golden gourds POP in contrast!
    fill_sym_box(grid, 6, 9, 10, 15, 27, 31, 4)
    fill_sym_box(grid, 6, 8, 10, 15, 28, 30, 3)
    fill_sym_box(grid, 6, 9, 10, 15, 31, 32, 1)  # Flared gold shoulder cap
    fill_sym_box(grid, 7, 10, 11, 14, 32, 32, 9) # Sun-yellow shoulder edge
    fill_sym_box(grid, 7, 9, 10, 15, 27, 27, 2)
    # Sculpted Golden Gourd mounted boldly on the outer face of BOTH shoulders!
    for xc in (cx_l - 9.8, cx_r + 9.8):
        fill_gourd(grid, xc, 12.8, 26.2, scale=1.02, main_col=1, shade_col=2, cord_col=3, hi_col=9)

    # --- NOTICEABLY LONG, POWERFUL ARTICULATED ARMS (長い腕, Z: 8..28) ---
    # Reaches noticeably low (down to knee/shin Z: 8..11!) with agile outward-swept forearms!
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        # Upper arm (Z: 21..28): warm brown-ochre & dark umber armored sleeve with gold elbow
        p_sh = (xc_base + sign * 8.0, 12.5, 27.5)
        # Right arm (+1) angles slightly more outward so its Gunbai fan clears the right leg cleanly!
        out_el = 10.6 if sign > 0 else 9.8
        out_wr = 12.2 if sign > 0 else 10.4
        p_el = (xc_base + sign * out_el, 12.0, 20.5)
        fill_tube(grid, p_sh, p_el, 1.55, 1.45, 5, steps=12)
        # Crimson upper-arm armor band
        ex0 = int(round(xc_base + sign * 8.0))
        ex1 = int(round(xc_base + sign * out_el))
        fill_box(grid, min(ex0, ex1) - 1, max(ex0, ex1) + 1, 11, 14, 24, 25, 3)
        # Golden articulated elbow joint
        fill_sphere_local(grid, p_el[0], p_el[1], p_el[2], 1.65, 1.65, 1.5, 2)
        fill_sphere_local(grid, p_el[0] + sign * 0.5, p_el[1] + 0.6, p_el[2], 1.15, 1.15, 1.15, 1)

        # Very long powerful forearm sweeping downward & forward (Z: 11..20)
        p_wr = (xc_base + sign * out_wr, 15.8, 11.6)
        fill_tube(grid, p_el, p_wr, 1.65, 1.55, 5, steps=14)
        # Dark umber inner muscle tone & gleaming gold outer kote gauntlet plate
        fill_tube(grid, (p_el[0] - sign * 0.4, p_el[1] - 0.5, p_el[2] - 1.0),
                  (p_wr[0] - sign * 0.4, p_wr[1] - 0.4, p_wr[2] + 0.5), 1.25, 1.2, 6, steps=10)
        fill_tube(grid, (p_el[0] + sign * 0.85, p_el[1] + 0.35, p_el[2] - 1.5),
                  (p_wr[0] + sign * 0.85, p_wr[1] + 0.35, p_wr[2] + 1.2), 1.1, 1.05, 1, steps=10)
        # Crimson & cream wrist cuff
        fill_sphere_local(grid, p_wr[0], p_wr[1], p_wr[2] + 0.7, 1.75, 1.75, 0.95, 3)
        fill_sphere_local(grid, p_wr[0] + sign * 0.6, p_wr[1] + 0.8, p_wr[2] + 0.7, 0.9, 0.9, 0.7, 7)

        # Large articulated agile fists/hands reaching down to Z: 8..11!
        hx = int(round(p_wr[0]))
        hy = int(round(p_wr[1]))
        fill_box(grid, hx - 1, hx + 1, hy - 1, hy + 2, 9, 11, 6)    # Dark bronze hand palm
        fill_box(grid, hx - 1, hx + 1, hy + 1, hy + 2, 8, 10, 8)    # Articulated curled fingers
        fill_box(grid, hx + (1 if sign > 0 else -1), hx + (1 if sign > 0 else -1),
                 hy, hy + 1, 9, 11, 1)                               # Gold knuckle plate
        fill_box(grid, hx - (1 if sign > 0 else -1), hx - (1 if sign > 0 else -1),
                 hy + 2, hy + 2, 9, 10, 5)                           # Thumb

    # --- RIGHT HAND (+X): GOLDEN TAIKO GUNBAI WAR FAN (swept cleanly outward clear of leg!) ---
    gx_h = cx_r + 13
    fill_box(grid, gx_h - 1, gx_h + 1, 15, 20, 10, 11, 2)       # Bronze fan handle through fist
    fill_box(grid, gx_h, gx_h + 1, 14, 15, 10, 11, 3)           # Crimson pommel tassel
    # Flared gourd-shaped crimson & gold Gunbai paddle angled boldly forward-outward (+Y: 20..26, Z: 9..17)
    fill_box(grid, gx_h, gx_h + 2, 20, 25, 10, 16, 1)           # Gleaming gold rim
    fill_box(grid, gx_h, gx_h + 2, 21, 24, 11, 15, 3)           # Rich crimson fan face
    fill_box(grid, gx_h + 2, gx_h + 2, 22, 23, 12, 14, 9)       # Radiant sun emblem on outer face
    fill_box(grid, gx_h, gx_h, 22, 23, 12, 14, 9)               # Sun emblem on inner face
    fill_box(grid, gx_h + 1, gx_h + 2, 26, 26, 11, 15, 1)       # Rounded fan tip
    fill_box(grid, gx_h + 1, gx_h + 2, 21, 24, 17, 17, 9)       # Top golden tip crest

    # --- BACKPACK & GRAND THOUSAND-GOURDS WAR STANDARD (千成瓢箪馬印, Y: 3..9, Z: 22..45) ---
    fill_sym_box(grid, 0, 4, 7, 9, 23, 30, 6)
    fill_sym_box(grid, 0, 3, 6, 7, 24, 29, 3)
    fill_sym_box(grid, 0, 3, 6, 6, 29, 30, 1)
    fill_sym_box(grid, 2, 3, 6, 7, 22, 24, 8)    # Compact iron lower thrusters
    fill_sym_box(grid, 2, 3, 6, 6, 22, 22, 9)

    # Central large golden gourd mounted on the back of the backpack (clearly seen in REAR VIEW!)
    fill_gourd(grid, (cx_l + cx_r) / 2.0, 5.0, 23.0, scale=1.18, main_col=1, shade_col=2, cord_col=3, hi_col=9)

    # TWIN FLANKING THOUSAND-GOURDS STANDARDS (千成瓢箪) rising high behind shoulders!
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        p_b0 = (xc_base + sign * 3.5, 7.5, 28.0)
        p_b1 = (xc_base + sign * 8.6, 5.5, 32.0)
        p_b2 = (xc_base + sign * 12.2, 5.0, 38.0)
        p_b3 = (xc_base + sign * 13.4, 5.0, 43.2)
        fill_tube(grid, p_b0, p_b1, 0.95, 0.85, 6, steps=8)
        fill_tube(grid, p_b1, p_b2, 0.85, 0.75, 2, steps=8)
        fill_tube(grid, p_b2, p_b3, 0.75, 0.65, 1, steps=6)

        # Tiered golden gourds clustered along each flanking standard!
        fill_gourd(grid, xc_base + sign * 11.4, 5.2, 31.2, scale=0.95, main_col=1, shade_col=2, cord_col=3, hi_col=9)
        fill_gourd(grid, xc_base + sign * 13.6, 5.0, 38.0, scale=1.08, main_col=1, shade_col=2, cord_col=3, hi_col=9)
        fill_gourd(grid, xc_base + sign * 9.0, 5.2, 34.2, scale=0.75, main_col=1, shade_col=2, cord_col=3, hi_col=9)

    # --- HEAD & ICONIC RADIANT GOLDEN SUNBURST KABUTO (後光/馬藺後立付兜, Z: 32..47) ---
    fill_sym_box(grid, 0, 1, 11, 13, 31, 33, 8)
    # Samurai Helmet Bowl (Kabuto) & Shikoro neck plates
    fill_sym_box(grid, 0, 2, 10, 15, 33, 37, 8)  # Charcoal iron kabuto bowl
    fill_sym_box(grid, 0, 3, 10, 13, 33, 35, 3)  # Crimson shikoro flared side/back guards
    fill_sym_box(grid, 3, 3, 11, 13, 33, 33, 1)  # Gold shikoro edge trim
    fill_sym_box(grid, 0, 2, 11, 14, 37, 38, 1)  # Golden kabuto crown ribs
    fill_sym_box(grid, 0, 1, 10, 15, 38, 38, 2)
    # Expressive Taiko Warlord Face & Fierce Glowing Eyes
    fill_sym_box(grid, 0, 1, 15, 16, 33, 34, 4)  # Deep crimson warlord menpo jaw
    fill_sym_box(grid, 0, 0, 16, 16, 33, 33, 1)  # Gold chin guard accent
    fill_sym_box(grid, 1, 1, 16, 16, 34, 34, 7)  # Cream-white cheek/mustache highlight
    fill_sym_box(grid, 0, 2, 15, 16, 35, 35, 8)  # Dark iron eye slit shadow
    fill_sym_box(grid, 1, 2, 16, 16, 35, 35, 9)  # Fierce glowing sun-yellow samurai eyes!
    # Golden Kabuto Visor Brim & Front Mini-Gourd Maedate Crest
    fill_sym_box(grid, 0, 2, 15, 16, 36, 36, 1)
    fill_sym_box(grid, 0, 0, 16, 17, 36, 38, 1)  # Forehead gourd crest
    fill_sym_box(grid, 0, 0, 17, 17, 37, 37, 3)  # Crimson waist on forehead crest
    fill_sym_box(grid, 0, 0, 16, 17, 39, 39, 9)  # Sun crest tip

    # ICONIC RADIANT GOLDEN SUNBURST / BAREN FAN (後光・一の谷馬藺後立)!
    fill_sym_box(grid, 0, 2, 9, 11, 35, 38, 2)   # Antique bronze sunburst hub
    sun_cx = (cx_l + cx_r) / 2.0
    sun_cz = 37.0
    # 9 crisp, majestic radiating golden rays fanning out in a grand Taiko halo!
    ray_angles_deg = [-80, -60, -40, -20, 0, 20, 40, 60, 80]
    for r_idx, ang_deg in enumerate(ray_angles_deg):
        ang = np.radians(ang_deg)
        ray_len = 9.5 if (r_idx % 2 == 0) else 7.8
        for step in range(1, 20):
            dist = (step / 19.0) * ray_len
            rx = sun_cx + np.sin(ang) * dist
            rz = sun_cz + np.cos(ang) * dist
            ix, iz = int(round(rx)), int(round(rz))
            if 0 <= ix < X and 0 <= iz < Z:
                if dist < 2.6:
                    col = 2
                elif dist > ray_len - 1.8:
                    col = 9  # Bright sun-yellow radiant tips!
                else:
                    col = 1  # Gleaming imperial gold ray!
                grid[ix, 10, iz] = col
                if dist < 5.5:
                    grid[ix, 9, iz] = col
                if step > 1:
                    prev_dist = ((step - 1) / 19.0) * ray_len
                    px = int(round(sun_cx + np.sin(ang) * prev_dist))
                    pz = int(round(sun_cz + np.cos(ang) * prev_dist))
                    if px != ix and pz != iz:
                        grid[px, 10, iz] = col

    # Hollow strictly interior voxels to keep count crisp inside ~2,600-3,500
    hollow_interior_26(grid, 1, Z - 2)

    return grid


# ==========================================
# FORM B: ARMORED MONKEY / 猿 (32 x 38 x 30)
# ==========================================
def build_b():
    grid = np.zeros((32, 38, 30), dtype=np.uint8)
    X, Y, Z = grid.shape
    cx = (X - 1) / 2.0   # 15.5
    cx_l = X // 2 - 1    # 15 (-X monkey left)
    cx_r = X // 2        # 16 (+X monkey right)

    # --- ATHLETIC HIND LEGS & GRASPING MONKEY FEET (Y: 8..16, Z: 0..13) ---
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        # Flat grasping monkey hind feet on ground (Z: 0..1), tucked slightly back for clean arm gap!
        fx = xc_base + sign * 4.4
        fill_box(grid, int(round(fx - 1.2)), int(round(fx + 1.2)), 9, 14, 0, 1, 6)
        # Distinct monkey toes + opposable inner big toe!
        fill_box(grid, int(round(fx - 1.0)), int(round(fx + 1.0)), 15, 16, 0, 0, 8)
        fill_box(grid, int(round(fx - sign * 2.0)), int(round(fx - sign * 1.2)), 13, 15, 0, 0, 8)
        # Golden ankle cuff reused from robot greaves
        fill_sphere_local(grid, fx, 11.0, 2.2, 1.55, 1.55, 0.9, 1)
        fill_sphere_local(grid, fx, 11.0, 3.0, 1.45, 1.45, 0.65, 3)

        # Bent athletic lower hind leg -> forward knee -> muscular thigh into hip
        p_ank = (fx, 11.0, 2.2)
        p_kne = (xc_base + sign * 5.0, 14.5, 7.2)
        p_hip = (xc_base + sign * 3.8, 11.2, 11.2)
        fill_tube(grid, p_ank, p_kne, 1.45, 1.65, 5, steps=12)
        fill_tube(grid, p_kne, p_hip, 1.85, 2.15, 5, steps=12)
        # Dark umber fur shading on back of thighs/calves
        fill_tube(grid, (fx, 10.2, 3.0), (xc_base + sign * 4.0, 10.0, 10.5), 1.3, 1.5, 6, steps=10)
        # Small bronze knee accent
        fill_sphere_local(grid, p_kne[0], p_kne[1] + 0.8, p_kne[2], 1.15, 1.0, 1.15, 2)

    # --- LEAN, ATHLETIC ARCHED MONKEY TORSO (Y: 9..23, Z: 8..19) ---
    torso_spine = [
        # (y, z, rx, rz)
        (9.5,  11.0, 3.4, 2.4),  # Rump
        (11.0, 11.5, 3.8, 2.7),
        (12.5, 12.0, 3.9, 2.8),
        (14.0, 12.5, 3.7, 2.8),  # Lean tucked monkey waist!
        (15.5, 13.2, 4.0, 3.0),
        (17.0, 14.0, 4.5, 3.3),  # Broad chest
        (18.5, 14.8, 4.9, 3.5),  # High muscular shoulders
        (20.0, 15.6, 4.8, 3.5),
        (21.5, 16.2, 4.1, 3.0),  # Upper chest tapering into crimson collar
    ]
    for ty, tz, rx, rz in torso_spine:
        fill_sphere_local(grid, cx, ty, tz, rx, 1.55, rz, 5)
        # Cream-white soft belly & chest fur on underside/front
        if ty >= 13.0:
            fill_sphere_local(grid, cx, ty + 0.5, tz - rz * 0.52, rx * 0.65, 1.3, rz * 0.48, 7)
        # Darker umber fur shading along flanks
        if 11.5 <= ty <= 17.5:
            fill_sphere_local(grid, cx, ty, tz + rz * 0.55, rx * 0.72, 1.2, rz * 0.45, 6)

    # Subtle crimson Japanese macaque rump patch (classic Nihonzaru touch!)
    fill_sphere_local(grid, cx, 8.7, 10.4, 2.1, 1.1, 1.5, 3)
    fill_sphere_local(grid, cx, 9.0, 9.8, 1.6, 0.9, 1.0, 4)

    # --- REUSED ROBOT ARMOR ON MONKEY: BACK GOURD CARAPACE & CRIMSON COLLAR ---
    # 1. Crimson Jinbaori Armored Collar wrapping monkey's neck (Z: 16..20, Y: 19..25)
    fill_sphere_local(grid, cx, 21.5, 17.5, 4.2, 2.7, 1.8, 3)
    fill_sphere_local(grid, cx, 22.0, 18.5, 3.8, 2.3, 1.1, 4)
    # Gold & cream collar edge trim (matching Hideyoshi robot!)
    fill_sym_box(grid, 0, 3, 23, 24, 16, 17, 1)
    fill_sym_box(grid, 0, 1, 24, 24, 16, 17, 9)
    fill_sym_box(grid, 2, 3, 21, 23, 18, 18, 7)

    # 2. Sculpted Golden Gourd-Shaped Back Armor & Folded Sunburst Fins (Y: 12..20, Z: 16..22)
    # Raised golden gourd carapace plate with crisp crimson cord cinch!
    fill_sphere_local(grid, cx, 14.5, 17.8, 2.8, 2.6, 1.9, 1)  # Larger rear golden gourd bulb
    fill_sphere_local(grid, cx, 16.9, 18.4, 1.9, 1.3, 1.5, 3)  # Crisp crimson ribbon cinch!
    fill_sphere_local(grid, cx, 19.0, 19.1, 2.2, 2.0, 1.6, 1)  # Front upper golden gourd bulb
    fill_sphere_local(grid, cx, 14.5, 19.5, 1.4, 1.3, 0.7, 9)  # Sun-yellow gourd gleam
    fill_sphere_local(grid, cx, 19.0, 20.4, 1.0, 1.0, 0.6, 9)
    # Folded golden kabuto sunburst side-fins flanking the back gourd armor
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        fill_box(grid, int(round(xc_base + sign * 3)), int(round(xc_base + sign * 4)), 13, 18, 17, 18, 2)
        fill_box(grid, int(round(xc_base + sign * 3)), int(round(xc_base + sign * 5)), 13, 14, 18, 20, 1)
        fill_box(grid, int(round(xc_base + sign * 4)), int(round(xc_base + sign * 5)), 13, 13, 20, 21, 9)

    # 3. Prominent Golden Gourd-Shaped Shoulder Armor Plates on BOTH shoulders!
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        # Deep crimson sode backing
        fill_sphere_local(grid, xc_base + sign * 5.2, 19.5, 16.4, 1.9, 2.4, 2.3, 4)
        fill_sphere_local(grid, xc_base + sign * 5.6, 19.8, 16.6, 1.6, 2.1, 2.0, 3)
        # Unmistakable sculpted golden gourd shoulder armor!
        fill_gourd(grid, xc_base + sign * 6.7, 20.0, 14.2, scale=1.02, main_col=1, shade_col=2, cord_col=3, hi_col=9)

    # --- VERY LONG MUSCULAR MONKEY ARMS (長い腕) POISED DYNAMICALLY FORWARD/DOWNWARD! ---
    # Left Arm (-X, viewer's right): Long muscular arm sweeping outward & far down to ground (Z: 0..16)
    p_l_sh = (cx_l - 5.4, 19.8, 15.4)
    p_l_el = (cx_l - 8.2, 22.4, 9.4)
    p_l_wr = (cx_l - 6.8, 27.2, 2.2)
    fill_tube(grid, p_l_sh, p_l_el, 1.85, 1.70, 5, steps=14)
    fill_tube(grid, p_l_el, p_l_wr, 1.65, 1.45, 5, steps=16)
    # Dark umber muscular shading
    fill_tube(grid, (p_l_sh[0] - 0.5, p_l_sh[1] - 0.6, p_l_sh[2] - 0.5),
              (p_l_el[0] - 0.5, p_l_el[1] - 0.6, p_l_el[2]), 1.3, 1.2, 6, steps=10)
    fill_tube(grid, (p_l_el[0] - 0.4, p_l_el[1] - 0.6, p_l_el[2]),
              (p_l_wr[0] - 0.4, p_l_wr[1] - 0.5, p_l_wr[2] + 0.5), 1.2, 1.1, 6, steps=12)
    # Golden & crimson wrist bracer reused from robot gauntlet
    fill_sphere_local(grid, p_l_wr[0], p_l_wr[1], p_l_wr[2] + 1.0, 1.65, 1.65, 0.9, 1)
    fill_sphere_local(grid, p_l_wr[0], p_l_wr[1], p_l_wr[2] + 1.9, 1.55, 1.55, 0.65, 3)
    # Grounded agile monkey hand & long grasping fingers (Z: 0..2, Y: 26..31)
    lhx, lhy = int(round(p_l_wr[0])), int(round(p_l_wr[1]))
    fill_box(grid, lhx - 1, lhx + 1, lhy - 1, lhy + 2, 0, 2, 6)
    fill_box(grid, lhx - 1, lhx + 1, lhy + 2, lhy + 4, 0, 1, 8)   # Long dark fingers
    fill_box(grid, lhx + 2, lhx + 2, lhy + 1, lhy + 3, 0, 1, 8)   # Inner thumb

    # Right Arm (+X, viewer's left): VERY LONG muscular arm poised boldly FORWARD & DOWNWARD!
    # Sweeps far forward (+Y -> 32..36) creating a clean silhouette gap from the hind leg!
    p_r_sh = (cx_r + 5.4, 19.8, 15.4)
    p_r_el = (cx_r + 9.2, 24.0, 10.6)
    p_r_wr = (cx_r + 8.0, 31.8, 5.2)
    fill_tube(grid, p_r_sh, p_r_el, 1.85, 1.70, 5, steps=14)
    fill_tube(grid, p_r_el, p_r_wr, 1.65, 1.45, 5, steps=16)
    # Muscular dark umber shading
    fill_tube(grid, (p_r_sh[0] + 0.5, p_r_sh[1] - 0.6, p_r_sh[2] - 0.5),
              (p_r_el[0] + 0.5, p_r_el[1] - 0.6, p_r_el[2]), 1.3, 1.2, 6, steps=10)
    fill_tube(grid, (p_r_el[0] + 0.4, p_r_el[1] - 0.5, p_r_el[2]),
              (p_r_wr[0] + 0.4, p_r_wr[1] - 0.5, p_r_wr[2]), 1.2, 1.1, 6, steps=12)
    # Golden & crimson wrist bracer
    fill_sphere_local(grid, p_r_wr[0], p_r_wr[1] - 0.9, p_r_wr[2] + 0.6, 1.65, 1.65, 0.95, 1)
    fill_sphere_local(grid, p_r_wr[0], p_r_wr[1] - 1.6, p_r_wr[2] + 1.1, 1.55, 1.55, 0.65, 3)
    # Dynamic open monkey hand with curled grasping fingers reaching forward-downward!
    rhx, rhy, rhz = int(round(p_r_wr[0])), int(round(p_r_wr[1])), int(round(p_r_wr[2]))
    fill_box(grid, rhx - 1, rhx + 1, rhy, rhy + 2, rhz - 1, rhz + 1, 6)
    # Three articulated spread monkey fingers + opposable thumb
    fill_box(grid, rhx - 1, rhx - 1, rhy + 2, rhy + 4, rhz - 2, rhz, 8)
    fill_box(grid, rhx + 1, rhx + 1, rhy + 2, rhy + 4, rhz - 2, rhz, 8)
    fill_box(grid, rhx, rhx, rhy + 3, rhy + 4, rhz - 3, rhz - 1, 8)
    fill_box(grid, rhx - 2, rhx - 2, rhy + 1, rhy + 2, rhz - 1, rhz, 8)

    # --- EXPRESSIVE JAPANESE MACAQUE HEAD & CRIMSON FACE (猿の顔立ち, Y: 21..33, Z: 18..28) ---
    # Neck solidly anchoring head into crimson collar
    fill_sphere_local(grid, cx, 22.6, 19.2, 2.7, 2.2, 2.2, 5)

    # Warm brown-ochre monkey cranium (Y: 21..28, Z: 19..27)
    fill_sphere_local(grid, cx, 24.6, 23.0, 3.8, 3.6, 3.8, 5)
    # Shaggy crown tuft on top of head (Z: 26..28)
    fill_sphere_local(grid, cx, 24.3, 26.5, 2.5, 2.4, 1.4, 5)
    fill_sphere_local(grid, cx, 24.0, 27.2, 1.5, 1.6, 0.9, 2)  # Warm golden-ochre crown highlight
    # Dark umber shading on back of head
    fill_sphere_local(grid, cx, 22.0, 22.6, 3.0, 1.6, 2.8, 6)

    # Fluffy Cream-White Cheek Ruffs / Sideburns framing the crimson face cleanly!
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        fill_sphere_local(grid, xc_base + sign * 3.3, 26.2, 21.3, 1.35, 1.7, 2.0, 7)
        fill_sphere_local(grid, xc_base + sign * 2.4, 26.8, 19.7, 1.2, 1.4, 1.1, 7)

    # PROMINENT ROUND MONKEY EARS sticking cleanly out BOTH sides! (x_off: 4..7, Y: 24..26, Z: 22..26)
    for sign, xc_base in ((-1, cx_l), (1, cx_r)):
        ex = xc_base + sign * 5.6
        # Solid ear attachment into side of cranium
        fill_box(grid, int(round(xc_base + sign * 3.5)), int(round(ex)), 24, 25, 23, 24, 5)
        # Round monkey ear disc (warm brown outer rim + dark umber edge + crimson inner ear!)
        fill_sphere_local(grid, ex, 24.8, 23.6, 1.65, 1.15, 2.05, 5)
        fill_sphere_local(grid, ex + sign * 0.4, 24.4, 23.6, 1.15, 0.9, 1.5, 6)
        fill_box(grid, int(round(ex - 0.6)), int(round(ex + 0.6)), 25, 26, 23, 24, 3)

    # UNMISTAKABLE RED/CRIMSON MONKEY FACE WITH BROW RIDGE, BRIGHT EYES & PROTRUDING SNOUT!
    # Crimson upper face mask (cheeks & eye surrounds)
    fill_sym_box(grid, 0, 2, 27, 29, 21, 24, 3)
    # Prominent overhanging brow ridge (Z: 24..25, Y: 28..30)
    fill_sym_box(grid, 0, 2, 28, 30, 24, 24, 3)
    fill_sym_box(grid, 0, 2, 28, 29, 25, 25, 5)  # Brown fur brow crown
    fill_sym_box(grid, 0, 1, 29, 30, 25, 25, 6)  # Brow ridge shadow
    # Bright expressive eyes set clearly beneath the overhanging brow! (Z: 23, Y: 29..30)
    fill_sym_box(grid, 1, 2, 29, 29, 23, 23, 4)  # Deep crimson eye socket
    fill_sym_box(grid, 1, 1, 29, 30, 23, 23, 9)  # Gleaming bright amber-gold eye!
    fill_sym_box(grid, 2, 2, 29, 30, 23, 23, 8)  # Crisp dark pupil right beside bright iris!
    # Protruding sculpted crimson monkey snout / muzzle (Y: 29..33, Z: 19..22)!
    fill_sym_box(grid, 0, 2, 28, 30, 20, 22, 3)
    fill_sym_box(grid, 0, 1, 30, 32, 20, 22, 3)
    fill_sym_box(grid, 0, 1, 32, 33, 21, 21, 3)  # Rounded tip of snout
    fill_sym_box(grid, 0, 1, 30, 31, 19, 19, 4)  # Lower jaw / chin
    # Nostrils & expressive monkey grin!
    fill_sym_box(grid, 0, 0, 33, 33, 22, 22, 4)  # Nostrils
    fill_sym_box(grid, 0, 1, 32, 32, 20, 20, 4)  # Expressive mouth line
    fill_sym_box(grid, 1, 1, 31, 32, 20, 20, 7)  # Cheeky flash of tooth/muzzle highlight
    # Small golden forehead crest (callback to Hideyoshi's kabuto maedate!)
    fill_sym_box(grid, 0, 0, 28, 29, 26, 26, 1)
    fill_sym_box(grid, 0, 0, 29, 29, 26, 26, 9)

    # --- GRACEFUL CURVED MONKEY TAIL (Y: 1..10, Z: 11..27) ---
    tail_pts = [
        (cx, 9.5,  11.8, 1.45),
        (cx, 7.6,  12.4, 1.35),
        (cx, 5.6,  13.8, 1.30),
        (cx, 3.8,  15.8, 1.25),
        (cx, 2.4,  18.2, 1.20),
        (cx, 1.8,  20.8, 1.15),
        (cx, 2.2,  23.4, 1.10),
        (cx, 3.6,  25.4, 1.05),
        (cx, 5.8,  26.4, 1.00),
        (cx, 7.6,  25.6, 0.95),
        (cx, 8.0,  23.8, 0.90),
    ]
    for idx in range(len(tail_pts) - 1):
        p0 = tail_pts[idx][:3]
        p1 = tail_pts[idx + 1][:3]
        r0 = tail_pts[idx][3]
        r1 = tail_pts[idx + 1][3]
        col = 5 if idx % 2 == 0 else 6
        fill_tube(grid, p0, p1, r0, r1, col, steps=8)
    # Golden & crimson tail ring near base
    fill_sphere_local(grid, cx, 7.4, 12.7, 1.45, 1.1, 1.45, 1)
    fill_sphere_local(grid, cx, 8.2, 12.3, 1.35, 0.85, 1.35, 3)

    # Hollow unseen interior voxels to keep count crisp in ~1,800-3,000 budget
    hollow_interior_26(grid, 1, Z - 2)

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


def render_preview(grid_a, v_a, grid_b, v_b, title_banner, label_a, label_b, out_path, yaw_a=30, pitch_a=20, yaw_b=44, pitch_b=19):
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


def count_components_6(grid):
    """Count 6-connected components to verify zero floating/detached voxels."""
    X, Y, Z = grid.shape
    visited = np.zeros_like(grid, dtype=bool)
    xs, ys, zs = np.nonzero(grid)
    comps = 0
    for sx, sy, sz in zip(xs, ys, zs):
        if visited[sx, sy, sz]:
            continue
        comps += 1
        stack = [(int(sx), int(sy), int(sz))]
        visited[sx, sy, sz] = True
        while stack:
            x, y, z = stack.pop()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = x + dx, y + dy, z + dz
                if 0 <= nx < X and 0 <= ny < Y and 0 <= nz < Z and not visited[nx, ny, nz] and grid[nx, ny, nz] > 0:
                    visited[nx, ny, nz] = True
                    stack.append((nx, ny, nz))
    return comps


if __name__ == "__main__":
    model_a = build_a()
    model_b = build_b()
    v_a = export_vox(model_a, "hideyoshi_a.vox")
    v_b = export_vox(model_b, "hideyoshi_b.vox")
    c_a = count_components_6(model_a)
    c_b = count_components_6(model_b)
    render_preview(
        model_a, v_a, model_b, v_b,
        "TRANSFORMING VOXEL MODEL: TOYOTOMI HIDEYOSHI ROBOT -> ARMORED MONKEY",
        "1. TOYOTOMI HIDEYOSHI ROBOT",
        "2. ARMORED MONKEY (SARU)",
        "preview_hideyoshi.png",
        yaw_a=30, pitch_a=20, yaw_b=44, pitch_b=19,
    )
    print(f"hideyoshi: A={v_a} voxels {model_a.shape} (comp6={c_a}), B={v_b} voxels {model_b.shape} (comp6={c_b})")
