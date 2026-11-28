import csv
import hashlib
import io
import json
import os
import re
import shutil
import threading
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from PIL import Image, ImageDraw, ImageFont, ImageColor


# ==========================================
# KONFIGURASI DIREKTORI ASTRO (PORT 8090)
# ==========================================
HOST = "127.0.0.1"
PORT = 8090

ASTRO_BLOG_DIR = r"F:\astro-netmediatop\src\content\blog"
DEFAULT_MD_PATH = r"F:\astro-netmediatop\src\content\blog\jadikan-sosmedmu-sumber-trafik-tertarget.md"
DEFAULT_ASTRO_IMG_DIR = r"F:\astro-netmediatop\src\assets\images\blog"
DEFAULT_PUBLIC_BLOG_DIR = r"F:\astro-netmediatop\public\blog"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_DIR = os.path.join(BASE_DIR, "generated_images_v6")

BG_PALETTE = [
    {"label": "Mode Terang - Putih Bersih (#ffffff)", "hex": "#ffffff"},
    {"label": "Mode Terang - Biru Es Lembut (#eef4fb)", "hex": "#eef4fb"},
    {"label": "Biru Utama NetMediaTop (#0476d3)", "hex": "#0476d3"},
    {"label": "Mode Gelap - Slate Gelap (#0f172a)", "hex": "#0f172a"},
]

TEXT_PALETTE = [
    {"label": "Hitam Pekat HP-Friendly (#090d16)", "hex": "#090d16"},
    {"label": "Hitam Murni (#111827)", "hex": "#111827"},
    {"label": "Biru Gelap (#0b192c)", "hex": "#0b192c"},
    {"label": "Putih Terang (#f8fafd)", "hex": "#f8fafd"},
]

PLACEHOLDER_OPTIONS = [
    "{{fitur}}",
    "{{hero}}",
    "{{slot1}}",
    "{{slot2}}",
    "{{slot3}}",
    "{{slot4}}",
    "{{cta}}",
]

# Palet Dinamis untuk Panel Kanan {{fitur}} agar tiap artikel berbeda-beda
FEATURED_THEMES = [
    {
        "name": "Electric Blue",
        "panel_bg": (4, 118, 211),
        "panel_dark": (3, 84, 153),
        "accent": (125, 211, 252),
        "soft": (224, 242, 254),
        "badge_bg": (219, 234, 254),
        "badge_fg": (3, 105, 161),
    },
    {
        "name": "Midnight Navy",
        "panel_bg": (15, 23, 42),
        "panel_dark": (9, 13, 22),
        "accent": (56, 189, 248),
        "soft": (186, 230, 253),
        "badge_bg": (224, 242, 254),
        "badge_fg": (12, 74, 110),
    },
    {
        "name": "Ocean Teal",
        "panel_bg": (13, 148, 136),
        "panel_dark": (15, 118, 110),
        "accent": (153, 246, 228),
        "soft": (204, 251, 241),
        "badge_bg": (204, 251, 241),
        "badge_fg": (17, 94, 89),
    },
    {
        "name": "Royal Indigo",
        "panel_bg": (67, 56, 202),
        "panel_dark": (49, 46, 129),
        "accent": (165, 180, 252),
        "soft": (224, 231, 255),
        "badge_bg": (224, 231, 255),
        "badge_fg": (55, 48, 163),
    },
    {
        "name": "Deep Slate Cyan",
        "panel_bg": (3, 105, 161),
        "panel_dark": (7, 89, 133),
        "accent": (103, 232, 249),
        "soft": (207, 250, 254),
        "badge_bg": (207, 250, 254),
        "badge_fg": (14, 116, 144),
    },
    {
        "name": "Emerald Tech",
        "panel_bg": (5, 150, 105),
        "panel_dark": (6, 95, 70),
        "accent": (110, 231, 183),
        "soft": (209, 250, 229),
        "badge_bg": (209, 250, 229),
        "badge_fg": (6, 95, 70),
    },
]

DEFAULT_ROWS = [
    {
        "placeholder": "{{fitur}}",
        "badge": "01 / STRATEGI TRAFIK",
        "judul": "Jadikan Sosmedmu Sumber Trafik Tertarget",
        "deskripsi": "Saring audiens relevan | Arahkan ke halaman penawaran | Tingkatkan konversi website",
        "nama_file": "sosmed-trafik-tertarget-featured.webp",
        "alt_text": "Strategi menjadikan media sosial sebagai sumber trafik tertarget ke website bisnis.",
    },
    {
        "placeholder": "{{hero}}",
        "badge": "01 / PENTINGNYA ALUR",
        "judul": "Posting Rutin Tapi Website Masih Sepi?",
        "deskripsi": "Ubah penonton pasif menjadi pengunjung website yang siap bertransaksi",
        "nama_file": "sosmed-trafik-hero.webp",
        "alt_text": "Ilustrasi alur mengubah penonton media sosial menjadi pengunjung website tertarget.",
    },
    {
        "placeholder": "{{slot1}}",
        "badge": "02 / PENYEBAB UTAMA",
        "judul": "Kenapa Trafik Sosmed Gagal Jadi Penjualan?",
        "deskripsi": "Konten terlalu umum & tidak menyaring audiens | Tautan profil membingungkan & tanpa jembatan solusi",
        "nama_file": "sosmed-trafik-masalah.webp",
        "alt_text": "Tiga penyebab trafik dari media sosial gagal menghasilkan penjualan di website.",
    },
    {
        "placeholder": "{{slot2}}",
        "badge": "03 / TIGA PILAR UTAMA",
        "judul": "3 Pilar Mengubah Sosmed Jadi Mesin Trafik",
        "deskripsi": "Konten berbasis masalah spesifik & CTA satu arah | Landing page ringan dan cepat dibuka dari HP",
        "nama_file": "sosmed-trafik-3-pilar.webp",
        "alt_text": "Tiga pilar utama mengubah media sosial menjadi sumber trafik tertarget ke website.",
    },
    {
        "placeholder": "{{slot3}}",
        "badge": "04 / ALUR PRAKTIS",
        "judul": "4 Langkah Menghubungkan Sosmed ke Website",
        "deskripsi": "Pilih halaman tujuan & pecah jadi 3 sudut konten | Pasang tautan UTM & evaluasi perilaku pengunjung",
        "nama_file": "sosmed-trafik-4-langkah.webp",
        "alt_text": "Empat tahapan praktis menghubungkan konten media sosial ke halaman website.",
    },
    {
        "placeholder": "{{cta}}",
        "badge": "05 / MULAI SEKARANG",
        "judul": "Siap Mengubah Audiens Sosmed Jadi Pelanggan?",
        "deskripsi": "Strategi konten terarah & halaman tujuan siap konversi | Konsultasikan kebutuhan bisnis Anda via WhatsApp",
        "nama_file": "sosmed-trafik-cta.webp",
        "alt_text": "Ajakan konsultasi strategi konten media sosial dan website bersama NetMediaTop.",
    },
]


# ==========================================
# AUTO-SCAN ARTIKEL MARKDOWN UNTUK AUTO-FILL
# ==========================================
def scan_markdown_for_rows(md_path: str) -> list[dict]:
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"File Markdown tidak ditemukan: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        raw = f.read()

    base_slug = os.path.splitext(os.path.basename(md_path))[0]
    slug_clean = re.sub(r"[^a-z0-9]+", "-", base_slug.lower()).strip("-")[:42] or "artikel"

    title = slug_clean.replace("-", " ").title()
    category = "PANDUAN WEBSITE"
    description = ""

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, flags=re.DOTALL)
    body = raw
    if fm_match:
        fm_text, body = fm_match.group(1), fm_match.group(2)
        m_title = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm_text, flags=re.MULTILINE)
        if m_title and m_title.group(1).strip():
            title = m_title.group(1).strip()
        m_cat = re.search(r'^category:\s*["\']?(.*?)["\']?\s*$', fm_text, flags=re.MULTILINE)
        if m_cat and m_cat.group(1).strip():
            category = m_cat.group(1).strip().upper()
        m_desc = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', fm_text, flags=re.MULTILINE)
        if m_desc and m_desc.group(1).strip():
            description = m_desc.group(1).strip()

    found_phs = []
    if "{{fitur}}" in raw:
        found_phs.append("{{fitur}}")
    for m in re.finditer(r"\{\{(hero|slot\d+|cta)\}\}", body):
        ph = m.group(0)
        if ph not in found_phs:
            found_phs.append(ph)

    h2_sections = []
    lines = body.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("## "):
            heading_txt = re.sub(r"^##\s+", "", s).strip()
            bullets = []
            for j in range(i + 1, min(len(lines), i + 16)):
                nxt = lines[j].strip()
                if nxt.startswith("## "):
                    break
                if not nxt or "{{" in nxt or nxt.startswith(("#", "---", "```", "![")):
                    continue
                clean_line = re.sub(r"^[\-\*\d\.]+\s*", "", nxt)
                clean_line = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_line)
                clean_line = re.sub(r"`([^`]+)`", r"\1", clean_line)
                if 16 <= len(clean_line) <= 125 and clean_line not in bullets:
                    bullets.append(clean_line)
                if len(bullets) >= 2:
                    break
            h2_sections.append({"heading": heading_txt, "bullets": bullets})

    if not found_phs:
        found_phs = ["{{fitur}}", "{{hero}}", "{{slot1}}", "{{slot2}}", "{{slot3}}", "{{cta}}"]

    rows = []
    h2_cursor = 0

    for idx, ph in enumerate(found_phs):
        ph_key = ph.replace("{", "").replace("}", "")
        suffix_file = "featured" if ph_key == "fitur" else ph_key
        fname = f"{slug_clean}-{suffix_file}.webp"

        if ph == "{{fitur}}":
            rows.append({
                "placeholder": "{{fitur}}",
                "badge": f"01 / {category[:22]}",
                "judul": title,
                "deskripsi": description or f"Panduan praktis {title}",
                "nama_file": fname,
                "alt_text": f"Ilustrasi utama artikel {title}",
            })
            continue

        ph_line_idx = -1
        for li, ln in enumerate(lines):
            if ph in ln:
                ph_line_idx = li
                break

        sec_heading = ""
        sec_bullets = []

        if ph_line_idx != -1:
            for back in range(ph_line_idx, -1, -1):
                s_ln = lines[back].strip()
                if s_ln.startswith(("## ", "### ")):
                    sec_heading = re.sub(r"^#{2,3}\s+", "", s_ln).strip()
                    break
            for w_idx in range(max(0, ph_line_idx - 10), min(len(lines), ph_line_idx + 12)):
                w_ln = lines[w_idx].strip()
                if not w_ln or "{{" in w_ln or w_ln.startswith(("#", "---", "```", "![")):
                    continue
                clean_w = re.sub(r"^[\-\*\d\.]+\s*", "", w_ln)
                clean_w = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_w)
                if 16 <= len(clean_w) <= 125 and clean_w not in sec_bullets:
                    sec_bullets.append(clean_w)
                if len(sec_bullets) >= 2:
                    break

        if not sec_heading:
            if ph == "{{hero}}":
                sec_heading = h2_sections[0]["heading"] if h2_sections else title
                sec_bullets = h2_sections[0]["bullets"] if h2_sections else ([description] if description else [])
                if h2_sections:
                    h2_cursor = 1
            elif ph == "{{cta}}":
                last_sec = h2_sections[-1] if len(h2_sections) > 1 else None
                sec_heading = last_sec["heading"] if last_sec else f"Siap Menerapkan {title[:45]}?"
                sec_bullets = last_sec["bullets"] if last_sec else ["Konsultasikan kebutuhan strategi digital bisnis Anda bersama NetMediaTop"]
            else:
                if h2_cursor < len(h2_sections):
                    sec_heading = h2_sections[h2_cursor]["heading"]
                    sec_bullets = h2_sections[h2_cursor]["bullets"]
                    h2_cursor += 1
                else:
                    sec_heading = title
                    sec_bullets = [description] if description else []

        badge_num = f"0{idx}" if idx < 10 else str(idx)
        badge_tag = "PENTINGNYA ALUR" if ph == "{{hero}}" else ("MULAI SEKARANG" if ph == "{{cta}}" else "POIN UTAMA")

        rows.append({
            "placeholder": ph,
            "badge": f"{badge_num} / {badge_tag}",
            "judul": sec_heading,
            "deskripsi": " | ".join(sec_bullets) if sec_bullets else f"Ringkasan poin penting {sec_heading}",
            "nama_file": fname,
            "alt_text": f"{sec_heading} - {title}",
        })

    return rows


# ==========================================
# PARSER CSV / GOOGLE SHEETS
# ==========================================
def slugify_webp(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "gambar-artikel.webp"
    base, _ = os.path.splitext(name)
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).strip("-").lower()
    return f"{base or 'gambar-artikel'}.webp"


def normalize_placeholder(ph: str) -> str:
    raw = (ph or "").strip().lower().replace("{", "").replace("}", "")
    if not raw:
        return "{{slot1}}"
    return f"{{{{{raw}}}}}"


def convert_gsheet_url_to_csv(url: str) -> str:
    u = (url or "").strip()
    m = re.search(r"docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)", u)
    if m and "output=csv" not in u and "toco/pub" not in u:
        sheet_id = m.group(1)
        gid_match = re.search(r"[?&]gid=([0-9]+)", u)
        gid = gid_match.group(1) if gid_match else "0"
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return u


def parse_csv_rows(csv_text: str) -> list[dict]:
    if not csv_text or not csv_text.strip():
        raise ValueError("Data CSV kosong.")

    sample = csv_text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(csv_text), dialect=dialect)
    if not reader.fieldnames:
        raise ValueError("Header kolom CSV tidak terbaca.")

    field_map = {h.strip().lower(): h for h in reader.fieldnames if h}

    def pick(row_dict, keys, fallback=""):
        for k in keys:
            real_k = field_map.get(k)
            if real_k is not None and row_dict.get(real_k) is not None:
                val = str(row_dict[real_k]).strip()
                if val != "":
                    return val
        return fallback

    parsed = []
    default_order = ["{{fitur}}", "{{hero}}", "{{slot1}}", "{{slot2}}", "{{slot3}}", "{{slot4}}", "{{cta}}"]

    for idx, r in enumerate(reader):
        judul = pick(r, ["judul", "title", "pain_point", "pain point", "topik"])
        deskripsi = pick(r, ["deskripsi", "description", "poin", "solusi"])
        if not judul and not deskripsi:
            continue

        ph_raw = pick(r, ["placeholder", "slot", "jenis"], default_order[min(idx, len(default_order) - 1)])
        badge = pick(r, ["badge", "label"], f"0{idx + 1} / POIN UTAMA")
        slug = re.sub(r"[^a-z0-9]+", "-", judul.lower()).strip("-")[:38] or f"gambar-{idx + 1}"
        nama_file = slugify_webp(pick(r, ["nama_file", "nama file", "filename", "file"], f"{slug}.webp"))
        alt_text = pick(r, ["alt_text", "alt text", "alt"], f"{judul} - {deskripsi}".strip(" -"))

        parsed.append({
            "placeholder": normalize_placeholder(ph_raw),
            "badge": badge,
            "judul": judul,
            "deskripsi": deskripsi,
            "nama_file": nama_file,
            "alt_text": alt_text,
        })

    if not parsed:
        raise ValueError("Tidak ada baris data valid yang ditemukan di CSV.")
    return parsed


# ==========================================
# ENGINE RENDER FONT & HELPER (100% IDENTIK V5)
# ==========================================
def load_best_font(size: int, bold: bool = False):
    candidates = []
    if os.name == "nt":
        if bold:
            candidates = [
                r"C:\Windows\Fonts\arialbd.ttf",
                r"C:\Windows\Fonts\segoeuib.ttf",
                r"C:\Windows\Fonts\calibrib.ttf",
            ]
        else:
            candidates = [
                r"C:\Windows\Fonts\seguisb.ttf",
                r"C:\Windows\Fonts\arial.ttf",
                r"C:\Windows\Fonts\segoeui.ttf",
            ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int):
    words = (text or "").split()
    if not words:
        return []
    lines = []
    cur = words[0]
    for w in words[1:]:
        test = f"{cur} {w}"
        bbox = draw.textbbox((0, 0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


# ==========================================
# ENGINE RENDER KHUSUS {{fitur}} (SPLIT EDITORIAL DINAMIS)
# ==========================================
def draw_split_right_visual(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, theme: dict, pattern_idx: int):
    p_bg = theme["panel_bg"]
    p_dark = theme["panel_dark"]
    accent = theme["accent"]
    soft = theme["soft"]
    white = (255, 255, 255)

    draw.rectangle([x0, y0, x1, y1], fill=p_bg)

    w = x1 - x0
    h = y1 - y0
    draw.ellipse([x1 - 240, y0 - 110, x1 + 120, y0 + 250], fill=p_dark)
    draw.ellipse([x0 - 90, y1 - 210, x0 + 210, y1 + 90], fill=p_dark)

    if pattern_idx == 0:
        bx, by = x0 + 42, y0 + 175
        bw, bh = 185, 240
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=white)
        draw.rounded_rectangle([bx, by, bx + bw, by + 34], radius=16, fill=soft)
        draw.rectangle([bx, by + 18, bx + bw, by + 34], fill=soft)
        for idx_dot in range(3):
            cx = bx + 20 + idx_dot * 16
            draw.ellipse([cx, by + 12, cx + 9, by + 21], fill=p_bg)
        draw.rounded_rectangle([bx + 18, by + 52, bx + bw - 18, by + 125], radius=10, fill=soft)
        draw.rounded_rectangle([bx + 18, by + 142, bx + bw - 35, by + 158], radius=6, fill=accent)
        draw.rounded_rectangle([bx + 18, by + 170, bx + bw - 55, by + 184], radius=6, fill=soft)
        draw.rounded_rectangle([bx + 18, by + 200, bx + 115, by + 222], radius=8, fill=p_bg)

        node_x = x1 - 108
        node_ys = [y0 + 135, y0 + 295, y0 + 455]
        target_ys = [by + 75, by + 125, by + 175]
        for ny, ty in zip(node_ys, target_ys):
            mid_x = bx + bw + 55
            draw.line([(node_x, ny), (mid_x, ny), (mid_x, ty), (bx + bw + 12, ty)], fill=white, width=6)
            draw.polygon(
                [(bx + bw + 8, ty), (bx + bw + 24, ty - 10), (bx + bw + 24, ty + 10)],
                fill=white,
            )
            draw.rounded_rectangle([node_x - 32, ny - 32, node_x + 32, ny + 32], radius=16, fill=white)
            draw.ellipse([node_x - 12, ny - 12, node_x + 12, ny + 12], fill=p_bg)

    elif pattern_idx == 1:
        draw.rounded_rectangle([x0 + 88, y0 + 110, x1 - 44, y1 - 150], radius=20, fill=p_dark)
        cx0, cy0, cx1, cy1 = x0 + 56, y0 + 145, x1 - 74, y1 - 115
        draw.rounded_rectangle([cx0, cy0, cx1, cy1], radius=20, fill=white)
        draw.rounded_rectangle([cx0 + 24, cy0 + 26, cx0 + 140, cy0 + 46], radius=10, fill=accent)
        for row_i in range(3):
            ry = cy0 + 78 + row_i * 74
            draw.rounded_rectangle([cx0 + 24, ry, cx0 + 66, ry + 42], radius=10, fill=p_bg)
            draw.line([(cx0 + 35, ry + 22), (cx0 + 43, ry + 30), (cx0 + 56, ry + 14)], fill=white, width=4)
            draw.rounded_rectangle([cx0 + 84, ry + 6, cx1 - 28, ry + 20], radius=6, fill=p_dark)
            draw.rounded_rectangle([cx0 + 84, ry + 28, cx1 - 76, ry + 39], radius=5, fill=soft)

    elif pattern_idx == 2:
        cx = x0 + w // 2
        cy = y0 + h // 2 - 15
        for rad, col, wid in [(175, p_dark, 18), (125, accent, 8), (75, white, 10)]:
            draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=col, width=wid)
        draw.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=white)
        draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=p_bg)
        satellites = [(cx - 125, cy - 125), (cx + 125, cy - 125), (cx - 125, cy + 125), (cx + 125, cy + 125)]
        for sx, sy in satellites:
            draw.ellipse([sx - 22, sy - 22, sx + 22, sy + 22], fill=white)
            draw.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], fill=p_bg)

    else:
        bx0, by0, bx1, by1 = x0 + 54, y0 + 135, x1 - 54, y1 - 125
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=22, fill=white)
        bar_heights = [95, 145, 200, 260]
        bar_w = 46
        gap = 24
        start_x = bx0 + 36
        base_y = by1 - 36
        pts = []
        for i, bh in enumerate(bar_heights):
            x_left = start_x + i * (bar_w + gap)
            y_top = base_y - bh
            col = p_bg if i == len(bar_heights) - 1 else soft
            draw.rounded_rectangle([x_left, y_top, x_left + bar_w, base_y], radius=10, fill=col)
            pts.append((x_left + bar_w // 2, y_top - 16))
        draw.line(pts, fill=p_bg, width=6)
        for px, py in pts:
            draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=p_bg)


def generate_featured_split_card(
    out_path: str,
    badge: str,
    judul: str,
    nama_file: str,
    style_seed_offset: int = 0,
    footer_left: str = "Bantu Bisnis Online",
    footer_right: str = "NetMediaTop.com",
):
    width, height = 1200, 720

    seed_str = f"{nama_file}|{judul}".encode("utf-8")
    digest = int(hashlib.md5(seed_str).hexdigest(), 16) + int(style_seed_offset)
    theme = FEATURED_THEMES[digest % len(FEATURED_THEMES)]
    pattern_idx = (digest // len(FEATURED_THEMES)) % 4

    left_bg = (248, 250, 252)
    split_x = 770
    footer_h = 68

    img = Image.new("RGB", (width, height), left_bg)
    draw = ImageDraw.Draw(img)

    draw_split_right_visual(draw, split_x, 0, width, height - footer_h, theme, pattern_idx)

    pad_left = 56
    max_left_w = split_x - pad_left - 44

    font_badge = load_best_font(23, bold=True)
    font_title = load_best_font(56, bold=True)
    font_footer = load_best_font(24, bold=False)

    badge_txt = (badge or "ARTIKEL PILIHAN").upper()
    b_box = draw.textbbox((0, 0), badge_txt, font=font_badge)
    b_w = (b_box[2] - b_box[0]) + 36
    b_h = (b_box[3] - b_box[1]) + 18

    title_lines = wrap_lines(draw, judul, font_title, max_left_w)[:3]
    line_h = 66
    total_block_h = b_h + 30 + (len(title_lines) * line_h)

    start_y = max(68, ((height - footer_h) - total_block_h) // 2)

    draw.rounded_rectangle([pad_left, start_y, pad_left + b_w, start_y + b_h], radius=12, fill=theme["badge_bg"])
    draw.text((pad_left + 18, start_y + 7), badge_txt, fill=theme["badge_fg"], font=font_badge)

    cur_y = start_y + b_h + 30
    for line in title_lines:
        draw.text((pad_left, cur_y), line, fill=(9, 13, 22), font=font_title)
        cur_y += line_h

    # 3. Footer Bar Bawah Penuh (Identik v5)
    fy = height - footer_h
    draw.rectangle([0, fy, width, height], fill=(255, 255, 255))
    draw.line([(0, fy), (width, fy)], fill=(226, 232, 240), width=2)

    draw.rounded_rectangle([pad_left, fy + 22, pad_left + 38, fy + 44], radius=6, fill=theme["panel_bg"])
    draw.text((pad_left + 52, fy + 20), footer_left, fill=(71, 85, 105), font=font_footer)

    r_box = draw.textbbox((0, 0), footer_right, font=font_footer)
    r_w = r_box[2] - r_box[0]
    draw.text((width - pad_left - r_w, fy + 20), footer_right, fill=(9, 13, 22), font=font_footer)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, format="WEBP", quality=90)
    return width, height


# ==========================================
# ENGINE RENDER KARTU ISI ARTIKEL ({{hero}}, {{slot1..4}}, {{cta}})
# ==========================================
def generate_card(
    out_path: str,
    placeholder: str,
    badge: str,
    judul: str,
    deskripsi: str,
    bg_hex: str,
    text_hex: str,
    nama_file: str = "",
    style_seed_offset: int = 0,
    footer_left: str = "Bantu Bisnis Online 24/7",
    footer_right: str = "NetMediaTop.com",
):
    ph_clean = normalize_placeholder(placeholder)
    if ph_clean == "{{fitur}}":
        return generate_featured_split_card(
            out_path=out_path,
            badge=badge,
            judul=judul,
            nama_file=nama_file,
            style_seed_offset=style_seed_offset,
            footer_left=footer_left,
            footer_right=footer_right,
        )

    width = 1200
    outer_rgb = ImageColor.getrgb(bg_hex)
    text_rgb = ImageColor.getrgb(text_hex)

    is_dark_card = (0.299 * text_rgb[0] + 0.587 * text_rgb[1] + 0.114 * text_rgb[2]) > 180

    if is_dark_card:
        card_fill = (17, 24, 39)
        border_color = (59, 130, 246)
        badge_bg = (30, 58, 138)
        badge_fg = (191, 219, 254)
        sub_color = (241, 245, 249)
        divider_color = (51, 65, 85)
    else:
        card_fill = (255, 255, 255)
        border_color = (4, 118, 211)
        badge_bg = (219, 234, 254)
        badge_fg = (3, 105, 161)
        sub_color = (9, 13, 22)
        divider_color = (148, 163, 184)

    if outer_rgb == (255, 255, 255) and not is_dark_card:
        outer_rgb = (241, 245, 249)

    tmp_img = Image.new("RGB", (width, 1200), outer_rgb)
    tmp_draw = ImageDraw.Draw(tmp_img)

    margin_x = 36
    margin_y = 28
    pad_x = margin_x + 50
    content_w = (width - margin_x - 50) - pad_x

    font_badge = load_best_font(24, bold=True)
    font_title = load_best_font(58, bold=True)
    font_item = load_best_font(37, bold=False)
    font_footer = load_best_font(24, bold=False)

    badge_txt = (badge or "PANDUAN WEBSITE").upper()
    b_box = tmp_draw.textbbox((0, 0), badge_txt, font=font_badge)
    b_w = (b_box[2] - b_box[0]) + 36
    b_h = (b_box[3] - b_box[1]) + 18

    title_lines = wrap_lines(tmp_draw, judul, font_title, content_w)[:3]
    line_h_title = 68
    title_block_h = len(title_lines) * line_h_title

    raw_points = [p.strip() for p in re.split(r"\||\n", deskripsi or "") if p.strip()]
    line_h_item = 48

    wrapped_points = []
    if len(raw_points) > 1:
        for pt in raw_points[:3]:
            wrapped_points.append(wrap_lines(tmp_draw, pt, font_item, content_w - 48)[:2])
        desc_block_h = sum(len(lines) * line_h_item + 10 for lines in wrapped_points)
    else:
        single_lines = wrap_lines(tmp_draw, deskripsi, font_item, content_w)[:4]
        wrapped_points = [single_lines]
        desc_block_h = len(single_lines) * line_h_item

    top_pad_inner = 40
    gap_badge_title = 22
    gap_title_desc = 18
    gap_desc_footer = 28
    footer_area_h = 56

    content_needed_h = (
        (margin_y * 2)
        + top_pad_inner
        + b_h
        + gap_badge_title
        + title_block_h
        + gap_title_desc
        + desc_block_h
        + gap_desc_footer
        + footer_area_h
    )

    height = max(340, content_needed_h)

    img = Image.new("RGB", (width, height), outer_rgb)
    draw = ImageDraw.Draw(img)

    card_rect = [margin_x, margin_y, width - margin_x, height - margin_y]
    draw.rounded_rectangle(card_rect, radius=24, fill=card_fill, outline=border_color, width=4)

    y = margin_y + top_pad_inner

    draw.rounded_rectangle([pad_x, y, pad_x + b_w, y + b_h], radius=12, fill=badge_bg)
    draw.text((pad_x + 17, y + 7), badge_txt, fill=badge_fg, font=font_badge)
    y += b_h + gap_badge_title

    for line in title_lines:
        draw.text((pad_x, y), line, fill=text_rgb, font=font_title)
        y += line_h_title

    y += gap_title_desc

    if len(raw_points) > 1:
        for pt_lines in wrapped_points:
            box_size = 34
            draw.rounded_rectangle(
                [pad_x, y + 6, pad_x + box_size, y + 6 + box_size],
                radius=8,
                fill=(4, 118, 211),
            )
            draw.line(
                [(pad_x + 8, y + 23), (pad_x + 15, y + 29), (pad_x + 26, y + 14)],
                fill=(255, 255, 255),
                width=3,
            )
            for pl in pt_lines:
                draw.text((pad_x + 50, y), pl, fill=sub_color, font=font_item)
                y += line_h_item
            y += 10
    else:
        for pl in wrapped_points[0]:
            draw.text((pad_x, y), pl, fill=sub_color, font=font_item)
            y += line_h_item

    footer_y = height - margin_y - 48
    draw.line(
        [(pad_x, footer_y - 16), (width - margin_x - 50, footer_y - 16)],
        fill=divider_color,
        width=2,
    )
    draw.text((pad_x, footer_y), footer_left, fill=sub_color, font=font_footer)

    r_box = draw.textbbox((0, 0), footer_right, font=font_footer)
    r_w = r_box[2] - r_box[0]
    draw.text((width - margin_x - 50 - r_w, footer_y), footer_right, fill=text_rgb, font=font_footer)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, format="WEBP", quality=90)
    return width, height


# ==========================================
# ENGINE UPLOAD KE ASTRO & GANTI PLACEHOLDER (SMART AUTO-INJECT)
# ==========================================
def upload_and_replace_placeholders(
    md_path: str,
    astro_img_dir: str,
    public_blog_dir: str,
    rows: list[dict],
    rel_prefix: str = "../../assets/images/blog",
):
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"File artikel tidak ditemukan: {md_path}")

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    replaced_log = []
    fallback_body_tags = []

    for row in rows:
        ph = normalize_placeholder(row.get("placeholder", ""))
        fname = slugify_webp(row.get("nama_file", ""))
        alt = (row.get("alt_text") or "").strip() or (row.get("judul") or "").strip()
        src_local = os.path.join(GENERATED_DIR, fname)

        if not os.path.exists(src_local):
            raise FileNotFoundError(f"Gambar '{fname}' belum di-generate. Klik tombol Langkah 1 dulu.")

        if ph == "{{fitur}}":
            os.makedirs(public_blog_dir, exist_ok=True)
            shutil.copy2(src_local, os.path.join(public_blog_dir, fname))
            public_url = f"/blog/{fname}"

            if ph in content:
                content = content.replace(ph, public_url)
                replaced_log.append(f"{ph} -> {public_url}")
            elif re.search(r"^(heroImage|image)\s*:", content, flags=re.MULTILINE):
                content = re.sub(
                    r"^((?:heroImage|image)\s*:\s*).*$",
                    rf'\g<1>"{public_url}"',
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )
                replaced_log.append(f"frontmatter -> {public_url}")
            elif content.startswith("---"):
                content = re.sub(r"^---\s*\n", f'---\nimage: "{public_url}"\n', content, count=1)
                replaced_log.append(f"frontmatter (baru) -> {public_url}")
        else:
            os.makedirs(astro_img_dir, exist_ok=True)
            shutil.copy2(src_local, os.path.join(astro_img_dir, fname))
            md_tag = f"![{alt}]({rel_prefix}/{fname})"

            if ph in content:
                content = content.replace(ph, md_tag)
                replaced_log.append(f"{ph} -> {fname}")
            else:
                fallback_body_tags.append((ph, md_tag, fname))

    if fallback_body_tags:
        fm_match = re.match(r"^(---\s*\n.*?\n---\s*\n)(.*)$", content, flags=re.DOTALL)
        fm_part = fm_match.group(1) if fm_match else ""
        body_part = fm_match.group(2) if fm_match else content

        h2_matches = list(re.finditer(r"^##\s+.*$", body_part, flags=re.MULTILINE))
        slot_idx = 0

        for ph, md_tag, fname in fallback_body_tags:
            if f"{rel_prefix}/{fname}" in body_part:
                continue

            if ph == "{{hero}}":
                if h2_matches:
                    pos = h2_matches[0].start()
                    body_part = body_part[:pos] + f"\n{md_tag}\n\n" + body_part[pos:]
                else:
                    body_part = f"\n{md_tag}\n\n" + body_part
                replaced_log.append(f"{ph} (auto-sisip atas) -> {fname}")
                h2_matches = list(re.finditer(r"^##\s+.*$", body_part, flags=re.MULTILINE))
            elif ph == "{{cta}}":
                body_part = body_part.rstrip() + f"\n\n{md_tag}\n"
                replaced_log.append(f"{ph} (auto-sisip bawah) -> {fname}")
            else:
                if slot_idx < len(h2_matches):
                    h2_end = h2_matches[slot_idx].end()
                    next_blank = body_part.find("\n\n", h2_end + 1)
                    insert_pos = next_blank + 2 if next_blank != -1 else len(body_part)
                    body_part = body_part[:insert_pos] + f"{md_tag}\n\n" + body_part[insert_pos:]
                    replaced_log.append(f"{ph} (auto-sisip H2 #{slot_idx + 1}) -> {fname}")
                    slot_idx += 1
                    h2_matches = list(re.finditer(r"^##\s+.*$", body_part, flags=re.MULTILINE))
                else:
                    body_part = body_part.rstrip() + f"\n\n{md_tag}\n"
                    replaced_log.append(f"{ph} (auto-sisip) -> {fname}")

        content = fm_part + body_part

    for unused_ph in ["{{hero}}", "{{slot1}}", "{{slot2}}", "{{slot3}}", "{{slot4}}", "{{cta}}"]:
        if unused_ph in content:
            content = re.sub(rf"\n*{re.escape(unused_ph)}\n*", "\n\n", content)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    return replaced_log


def list_astro_md_files():
    files = []
    if os.path.isdir(ASTRO_BLOG_DIR):
        for fn in sorted(os.listdir(ASTRO_BLOG_DIR)):
            if fn.endswith(".md") or fn.endswith(".mdx"):
                files.append(os.path.join(ASTRO_BLOG_DIR, fn))
    if DEFAULT_MD_PATH not in files and os.path.exists(DEFAULT_MD_PATH):
        files.insert(0, DEFAULT_MD_PATH)
    return files


# ==========================================
# HTML ANTARMUKA WEB LOKAL (127.0.0.1:8090)
# ==========================================
HTML_PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Astro SEO Image Generator v6 — Auto-Fill MD + Split Editorial Dinamis</title>
  <style>
    :root {
      --bg: #f1f5f9;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #cbd5e1;
      --primary: #0476d3;
      --primary-hover: #0360ad;
      --success: #16a34a;
      --success-hover: #15803d;
    }
    * { box-sizing: border-box; font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
    body { margin: 0; background: var(--bg); color: var(--text); }
    header {
      background: #0f172a; color: #f8fafd; padding: 14px 24px;
      display: flex; justify-content: space-between; align-items: center;
    }
    header h1 { margin: 0; font-size: 18px; }
    header span { font-size: 12px; color: #93c5fd; }
    .container { max-width: 1340px; margin: 18px auto; padding: 0 16px; }
    .panel {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 12px; padding: 16px; margin-bottom: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .panel h2 { margin: 0 0 12px 0; font-size: 15px; color: var(--primary); }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .import-bar {
      display: grid; grid-template-columns: 1fr auto auto; gap: 8px;
      background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px;
      padding: 10px 12px; margin-bottom: 12px; align-items: center;
    }
    label { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; color: var(--muted); }
    input[type="text"], select, textarea {
      width: 100%; padding: 8px 10px; border: 1px solid var(--border);
      border-radius: 8px; font-size: 13px; background: #fff; color: var(--text);
    }
    .toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; align-items: center; }
    .action-group { display: flex; gap: 10px; margin-left: auto; align-items: center; }
    button {
      border: none; border-radius: 8px; padding: 9px 15px; font-size: 13px;
      font-weight: 700; cursor: pointer; transition: 0.2s;
    }
    button:disabled {
      opacity: 0.55; cursor: not-allowed; pointer-events: none;
    }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover:not(:disabled) { background: var(--primary-hover); }
    .btn-upload { background: var(--success); color: #fff; }
    .btn-upload:hover:not(:disabled) { background: var(--success-hover); }
    .btn-done { background: #1e293b !important; color: #4ade80 !important; border: 1px solid #16a34a; }
    .btn-secondary { background: #e2e8f0; color: #0f172a; font-weight: 600; }
    .btn-secondary:hover:not(:disabled) { background: #cbd5e1; }
    .btn-accent { background: #dbeafe; color: #1e40af; font-weight: 700; }
    .btn-accent:hover:not(:disabled) { background: #bfdbfe; }
    .btn-danger { background: #fee2e2; color: #b91c1c; padding: 5px 9px; font-size: 12px; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { border: 1px solid var(--border); padding: 6px; text-align: left; vertical-align: top; }
    th { background: #f8fafc; font-weight: 700; }
    td input, td select { padding: 6px 8px; font-size: 12px; border-radius: 6px; }
    .ph-select { font-family: monospace; font-weight: 700; color: #0369a1; background: #f0f9ff; }
    .preview-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .preview-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px; padding: 16px; border-radius: 10px; transition: 0.2s;
      align-items: start;
    }
    .preview-light { background: #ffffff; border: 1px solid #e2e8f0; }
    .preview-dark { background: #090d16; border: 1px solid #1e293b; color: #f8fafd; }
    .preview-card {
      border-radius: 10px; overflow: hidden; border: 1px solid rgba(148,163,184,0.3);
      padding: 10px; background: rgba(148,163,184,0.06);
    }
    .preview-card img { width: 100%; height: auto; border: 1px solid #e2e8f0; border-radius: 8px; display: block; }
    .preview-meta { font-size: 11px; margin-top: 8px; line-height: 1.55; }
    .badge-dim {
      display: inline-block; background: #dbeafe; color: #1e40af;
      padding: 2px 7px; border-radius: 4px; font-weight: 700; font-size: 11px; font-family: monospace;
    }
    .status-box {
      padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 600;
      margin-top: 12px; display: none;
    }
    .status-ok { background: #dcfce7; color: #166534; display: block; }
    .status-info { background: #e0f2fe; color: #075985; display: block; }
    .status-err { background: #fee2e2; color: #991b1b; display: block; }
    dialog {
      border: 1px solid var(--border); border-radius: 12px; padding: 18px;
      width: 680px; max-width: 95vw;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Astro SEO Image Generator (v6 — Auto-Fill MD + Split Editorial Dinamis)</h1>
      <span>Cover {{fitur}} Split Editorial Auto-Variasi • Isi Artikel Kartu Tegas • Auto-Scan MD & GSheet/CSV Import</span>
    </div>
    <div><strong>NetMediaTop.com</strong></div>
  </header>

  <div class="container">
    <div class="panel">
      <h2>1. Target Artikel Astro & Pengaturan Warna Kartu Isi</h2>
      <div class="grid-2">
        <div>
          <label>Pilih Artikel dari Folder Blog Astro (Otomatis Mengisi Tabel di Bawah):</label>
          <select id="mdSelect" onchange="onTargetChange(this.value)"></select>
        </div>
        <div>
          <label>Path File Markdown (.md) Tujuan:</label>
          <input type="text" id="mdPath" oninput="resetActionStates()" />
        </div>
      </div>

      <div class="grid-3" style="margin-top:10px;">
        <div>
          <label>Folder Aset Artikel (<code>{{hero}}</code>, <code>{{slot1..4}}</code>, <code>{{cta}}</code>):</label>
          <input type="text" id="astroImgDir" oninput="resetActionStates()" />
        </div>
        <div>
          <label>Folder Public Featured (<code>{{fitur}}</code>):</label>
          <input type="text" id="publicBlogDir" oninput="resetActionStates()" />
        </div>
        <div class="grid-2">
          <div>
            <label>Background Kartu Isi:</label>
            <select id="bgHex" onchange="resetActionStates()"></select>
          </div>
          <div>
            <label>Teks Kartu Isi:</label>
            <select id="textHex" onchange="resetActionStates()"></select>
          </div>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>2. Import Tabel dari Google Sheets / File CSV (Atau Edit Hasil Auto-Fill MD)</h2>

      <div class="import-bar">
        <div>
          <label style="margin-bottom:2px;">Link Google Sheets (Link Edit / Publish CSV) atau Pilih File CSV Lokal:</label>
          <input type="text" id="gsheetUrl" placeholder="Tempel link Google Sheets di sini (pastikan akses publik / Publish to web CSV)..." />
        </div>
        <div style="padding-top:16px;">
          <button class="btn-primary" onclick="importFromGSheet()">Ambil dari GSheet</button>
        </div>
        <div style="padding-top:16px;">
          <input type="file" id="csvFileInput" accept=".csv,.txt" style="display:none;" onchange="handleCsvFile(event)" />
          <button class="btn-secondary" onclick="document.getElementById('csvFileInput').click()">Upload File (.csv)</button>
        </div>
      </div>

      <div class="toolbar">
        <button class="btn-secondary" onclick="rescanCurrentMd()">🔄 Scan Ulang dari MD</button>
        <button class="btn-secondary" onclick="addRow()">+ Tambah Baris</button>
        <button class="btn-secondary" onclick="document.getElementById('pasteModal').showModal()">Paste Blok Tabel / CSV</button>
        <button class="btn-secondary" onclick="exportCSV()">Download Template CSV</button>
        <button class="btn-accent" onclick="shuffleFeaturedStyle()" title="Ganti kombinasi warna & motif panel kanan untuk {{fitur}}">🎲 Acak Gaya {{fitur}}</button>

        <div class="action-group">
          <button id="btnGenerate" class="btn-primary" onclick="stepGenerate()">1. Generate & Preview Gambar</button>
          <button id="btnUpload" class="btn-upload" onclick="stepUpload()" disabled>2. Upload & Pasang ke Astro</button>
        </div>
      </div>

      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th style="width:125px;">Placeholder</th>
              <th style="width:165px;">Badge</th>
              <th style="width:240px;">Judul (Pain Point)</th>
              <th style="width:290px;">Deskripsi / Poin (untuk <code>{{hero}}</code>..<code>{{cta}}</code>)</th>
              <th style="width:210px;">Nama File (.webp)</th>
              <th style="width:210px;">Alt Text SEO</th>
              <th style="width:55px;">Aksi</th>
            </tr>
          </thead>
          <tbody id="tableBody"></tbody>
        </table>
      </div>
      <div id="statusBox" class="status-box"></div>
    </div>

    <div class="panel">
      <div class="preview-bar">
        <h2 style="margin:0;">3. Preview Hasil Gambar (Cek Sebelum Upload ke Astro)</h2>
        <div>
          <button class="btn-secondary" onclick="setPreviewTheme('light')">☀️ Simulasi Mode Terang</button>
          <button class="btn-secondary" onclick="setPreviewTheme('dark')">🌙 Simulasi Mode Gelap</button>
        </div>
      </div>
      <div id="previewGrid" class="preview-grid preview-light"></div>
    </div>
  </div>

  <dialog id="pasteModal">
    <h3 style="margin-top:0;">Paste Blok Tabel dari Google Sheets / CSV</h3>
    <p style="font-size:12px; color:#475569;">Bisa menempel langsung blok baris dari Google Sheets (dengan header <code>placeholder,badge,judul,deskripsi,nama_file,alt_text</code>) atau format cepat <code>Judul = Deskripsi</code>.</p>
    <textarea id="pasteInput" rows="9">placeholder,badge,judul,deskripsi,nama_file,alt_text
{{fitur}},01 / STRATEGI TRAFIK,Jadikan Sosmedmu Sumber Trafik Tertarget,Saring audiens relevan | Arahkan ke halaman penawaran,sosmed-trafik-tertarget-featured.webp,Strategi menjadikan media sosial sebagai sumber trafik tertarget ke website bisnis.
{{hero}},01 / PENTINGNYA ALUR,Posting Rutin Tapi Website Masih Sepi?,Ubah penonton pasif menjadi pengunjung website yang siap bertransaksi,sosmed-trafik-hero.webp,Ilustrasi alur mengubah penonton media sosial menjadi pengunjung website tertarget.
{{cta}},05 / MULAI SEKARANG,Siap Mengubah Audiens Sosmed Jadi Pelanggan?,Strategi konten terarah & halaman tujuan siap konversi,sosmed-trafik-cta.webp,Ajakan konsultasi strategi konten media sosial dan website bersama NetMediaTop.</textarea>
    <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:12px;">
      <button class="btn-secondary" onclick="document.getElementById('pasteModal').close()">Batal</button>
      <button class="btn-primary" onclick="applyPaste()">Masukkan ke Tabel</button>
    </div>
  </dialog>

  <script>
    let state = { rows: [], placeholders: [], bgPalette: [], textPalette: [], mdFiles: [] };
    let isGenerated = false;
    let isUploaded = false;
    let styleSeedOffset = 0;

    function showStatus(msg, type = 'info') {
      const box = document.getElementById('statusBox');
      box.textContent = msg;
      box.className = 'status-box status-' + type;
      box.style.display = 'block';
    }

    function resetActionStates() {
      isGenerated = false;
      isUploaded = false;

      const btnGen = document.getElementById('btnGenerate');
      const btnUp = document.getElementById('btnUpload');

      btnGen.disabled = false;
      btnGen.className = 'btn-primary';
      btnGen.textContent = '1. Generate & Preview Gambar';

      btnUp.disabled = true;
      btnUp.className = 'btn-upload';
      btnUp.textContent = '2. Upload & Pasang ke Astro';
    }

    function shuffleFeaturedStyle() {
      styleSeedOffset += 1;
      resetActionStates();
      stepGenerate();
    }

    async function autoFillFromMd(mdPath) {
      if (!mdPath) return;
      showStatus('⏳ Memindai artikel Markdown untuk mengisi tabel otomatis...', 'info');
      try {
        const res = await fetch('/api/scan-md', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mdPath })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Gagal memindai file .md');
        state.rows = data.rows;
        styleSeedOffset = 0;
        renderTable();
        resetActionStates();
        document.getElementById('previewGrid').innerHTML = '';
        showStatus(`✅ Tabel otomatis terisi ${data.rows.length} baris dari artikel "${mdPath.split(/[\\\\/]/).pop()}". Klik '1. Generate & Preview Gambar' atau timpa via GSheet/CSV.`, 'ok');
      } catch (err) {
        showStatus('Info Auto-Fill MD: ' + err.message, 'err');
      }
    }

    async function onTargetChange(val) {
      document.getElementById('mdPath').value = val;
      resetActionStates();
      await autoFillFromMd(val);
    }

    async function rescanCurrentMd() {
      const mdPath = document.getElementById('mdPath').value.trim();
      await autoFillFromMd(mdPath);
    }

    async function init() {
      const res = await fetch('/api/init');
      state = await res.json();

      const mdSel = document.getElementById('mdSelect');
      state.mdFiles.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.textContent = p.split(/[\\\\/]/).pop();
        mdSel.appendChild(opt);
      });
      document.getElementById('mdPath').value = state.defaultMd;
      document.getElementById('astroImgDir').value = state.defaultAstroImgDir;
      document.getElementById('publicBlogDir').value = state.defaultPublicBlogDir;

      const bgSel = document.getElementById('bgHex');
      state.bgPalette.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.hex; opt.textContent = c.label;
        bgSel.appendChild(opt);
      });

      const txtSel = document.getElementById('textHex');
      state.textPalette.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.hex; opt.textContent = c.label;
        txtSel.appendChild(opt);
      });

      renderTable();
      resetActionStates();
      if (state.defaultMd) {
        await autoFillFromMd(state.defaultMd);
      }
    }

    function renderTable() {
      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = '';
      state.rows.forEach((r, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>
            <select class="ph-select" onchange="state.rows[${idx}].placeholder = this.value; resetActionStates();">
              ${state.placeholders.map(ph =>
                `<option value="${ph}" ${r.placeholder === ph ? 'selected' : ''}>${ph}</option>`
              ).join('')}
            </select>
          </td>
          <td><input type="text" value="${escapeHtml(r.badge)}" oninput="state.rows[${idx}].badge = this.value; resetActionStates();" /></td>
          <td><input type="text" value="${escapeHtml(r.judul)}" oninput="state.rows[${idx}].judul = this.value; resetActionStates();" /></td>
          <td><input type="text" value="${escapeHtml(r.deskripsi)}" oninput="state.rows[${idx}].deskripsi = this.value; resetActionStates();" /></td>
          <td><input type="text" value="${escapeHtml(r.nama_file)}" oninput="state.rows[${idx}].nama_file = this.value; resetActionStates();" /></td>
          <td><input type="text" value="${escapeHtml(r.alt_text)}" oninput="state.rows[${idx}].alt_text = this.value; resetActionStates();" /></td>
          <td><button class="btn-danger" onclick="removeRow(${idx})">Hapus</button></td>
        `;
        tbody.appendChild(tr);
      });
    }

    function escapeHtml(s) {
      return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    function addRow() {
      const used = new Set(state.rows.map(r => r.placeholder));
      const nextPh = state.placeholders.find(p => !used.has(p)) || '{{slot1}}';
      const n = state.rows.length + 1;
      state.rows.push({
        placeholder: nextPh,
        badge: `0${n} / POIN PENTING`,
        judul: 'Judul Pain Point Baru',
        deskripsi: 'Solusi singkat pertama | Solusi singkat kedua',
        nama_file: `0${n}-gambar-artikel.webp`,
        alt_text: 'Deskripsi alt text SEO gambar artikel',
      });
      renderTable();
      resetActionStates();
    }

    function removeRow(idx) {
      if (state.rows.length <= 1) return alert('Minimal sisakan 1 baris.');
      state.rows.splice(idx, 1);
      renderTable();
      resetActionStates();
    }

    async function importFromGSheet() {
      const url = document.getElementById('gsheetUrl').value.trim();
      if (!url) return alert('Tempelkan link Google Sheets terlebih dahulu.');
      showStatus('⏳ Mengambil data tabel dari Google Sheets...', 'info');
      try {
        const res = await fetch('/api/import-gsheet', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Gagal mengambil data GSheet');
        state.rows = data.rows;
        styleSeedOffset = 0;
        renderTable();
        resetActionStates();
        showStatus(`✅ Berhasil mengimpor ${data.rows.length} baris dari Google Sheets! Silakan klik '1. Generate & Preview Gambar'.`, 'ok');
      } catch (err) {
        showStatus('Error GSheet: ' + err.message, 'err');
      }
    }

    async function handleCsvFile(event) {
      const file = event.target.files[0];
      if (!file) return;
      const csvText = await file.text();
      await parseCsvOnServer(csvText, `file "${file.name}"`);
      event.target.value = '';
    }

    async function parseCsvOnServer(csvText, sourceLabel = 'teks') {
      showStatus(`⏳ Memproses data dari ${sourceLabel}...`, 'info');
      try {
        const res = await fetch('/api/parse-csv', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ csvText })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Gagal memproses CSV');
        state.rows = data.rows;
        styleSeedOffset = 0;
        renderTable();
        resetActionStates();
        showStatus(`✅ Berhasil memuat ${data.rows.length} baris dari ${sourceLabel}! Silakan klik '1. Generate & Preview Gambar'.`, 'ok');
      } catch (err) {
        showStatus('Error Import: ' + err.message, 'err');
      }
    }

    async function applyPaste() {
      const raw = document.getElementById('pasteInput').value.trim();
      if (!raw) return;

      if (/placeholder/i.test(raw) || /judul/i.test(raw)) {
        document.getElementById('pasteModal').close();
        await parseCsvOnServer(raw, 'blok tabel paste');
        return;
      }

      const lines = raw.split('\\n');
      const parsed = [];
      const orderPh = ['{{fitur}}', '{{hero}}', '{{slot1}}', '{{slot2}}', '{{slot3}}', '{{slot4}}'];
      lines.forEach((line, i) => {
        if (!line.includes('=')) return;
        const parts = line.split('=');
        const j = parts[0].trim();
        const d = parts.slice(1).join('=').trim();
        if (!j) return;
        const num = i + 1;
        const isLast = i === lines.length - 1 && lines.length > 2;
        const ph = isLast ? '{{cta}}' : (orderPh[i] || '{{slot4}}');
        const slug = j.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 36);
        parsed.push({
          placeholder: ph,
          badge: `0${num} / POIN UTAMA`,
          judul: j,
          deskripsi: d,
          nama_file: `0${num}-${slug}.webp`,
          alt_text: `${j} - ${d}`,
        });
      });
      if (parsed.length) {
        state.rows = parsed;
        styleSeedOffset = 0;
        renderTable();
        resetActionStates();
        showStatus(`✅ Berhasil memuat ${parsed.length} baris ke tabel.`, 'ok');
      }
      document.getElementById('pasteModal').close();
    }

    function setPreviewTheme(mode) {
      const grid = document.getElementById('previewGrid');
      grid.className = 'preview-grid ' + (mode === 'dark' ? 'preview-dark' : 'preview-light');
    }

    function exportCSV() {
      const headers = ['placeholder','badge','judul','deskripsi','nama_file','alt_text'];
      const csvRows = [headers.join(',')];
      state.rows.forEach(r => {
        csvRows.push(headers.map(h => `"${(r[h] || '').replace(/"/g, '""')}"`).join(','));
      });
      const blob = new Blob([csvRows.join('\\n')], { type: 'text/csv;charset=utf-8;' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'template-mapping-astro.csv';
      a.click();
    }

    async function stepGenerate() {
      const btnGen = document.getElementById('btnGenerate');
      const btnUp = document.getElementById('btnUpload');

      btnGen.disabled = true;
      btnGen.textContent = '⏳ Sedang Generate Gambar...';
      btnUp.disabled = true;

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            bgHex: document.getElementById('bgHex').value,
            textHex: document.getElementById('textHex').value,
            styleSeedOffset: styleSeedOffset,
            rows: state.rows
          })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Gagal generate');

        isGenerated = true;
        isUploaded = false;

        btnGen.disabled = false;
        btnGen.className = 'btn-done';
        btnGen.textContent = '✓ Sudah Di-Generate (Generate Ulang)';

        btnUp.disabled = false;
        btnUp.className = 'btn-upload';
        btnUp.textContent = '2. Upload & Pasang ke Astro';

        showStatus(data.message, 'info');

        const grid = document.getElementById('previewGrid');
        grid.innerHTML = '';
        const ts = Date.now();
        data.items.forEach(it => {
          const targetDesc = it.placeholder === '{{fitur}}'
            ? `/blog/${it.nama_file} (public/blog)`
            : `![${escapeHtml(it.alt_text)}](../../assets/images/blog/${it.nama_file})`;
          const card = document.createElement('div');
          card.className = 'preview-card';
          card.innerHTML = `
            <img src="/generated/${encodeURIComponent(it.nama_file)}?t=${ts}" alt="${escapeHtml(it.alt_text)}" />
            <div class="preview-meta">
              <span class="badge-dim">${it.placeholder} • ${it.width}×${it.height}px</span><br/>
              <strong>File:</strong> <code>${it.nama_file}</code><br/>
              <strong>Target Pengganti:</strong> <code>${targetDesc}</code>
            </div>
          `;
          grid.appendChild(card);
        });
      } catch (err) {
        btnGen.disabled = false;
        btnGen.textContent = '1. Generate & Preview Gambar';
        showStatus('Error: ' + err.message, 'err');
      }
    }

    async function stepUpload() {
      if (!isGenerated || isUploaded) return;

      const btnUp = document.getElementById('btnUpload');
      btnUp.disabled = true;
      btnUp.textContent = '⏳ Mengupload & Mengganti Placeholder...';

      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mdPath: document.getElementById('mdPath').value,
            astroImgDir: document.getElementById('astroImgDir').value,
            publicBlogDir: document.getElementById('publicBlogDir').value,
            rows: state.rows
          })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Gagal upload');

        isUploaded = true;
        btnUp.disabled = true;
        btnUp.className = 'btn-done';
        btnUp.textContent = '✅ Sudah Terupload & Terpasang';

        showStatus(data.message, 'ok');
      } catch (err) {
        btnUp.disabled = false;
        btnUp.textContent = '2. Upload & Pasang ke Astro';
        showStatus('Error: ' + err.message, 'err');
      }
    }

    init();
  </script>
</body>
</html>
"""


class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            body = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/init":
            md_files = list_astro_md_files()
            initial_md = md_files[0] if md_files else DEFAULT_MD_PATH
            self._send_json({
                "defaultMd": initial_md,
                "defaultAstroImgDir": DEFAULT_ASTRO_IMG_DIR,
                "defaultPublicBlogDir": DEFAULT_PUBLIC_BLOG_DIR,
                "mdFiles": md_files,
                "placeholders": PLACEHOLDER_OPTIONS,
                "bgPalette": BG_PALETTE,
                "textPalette": TEXT_PALETTE,
                "rows": DEFAULT_ROWS,
            })
        elif parsed.path.startswith("/generated/"):
            fname = os.path.basename(urllib.parse.unquote(parsed.path[len("/generated/"):]))
            fpath = os.path.join(GENERATED_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/webp")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404, "File tidak ditemukan")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw)

        if parsed.path == "/api/scan-md":
            try:
                md_path = (payload.get("mdPath") or "").strip()
                rows = scan_markdown_for_rows(md_path)
                self._send_json({"rows": rows})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif parsed.path == "/api/import-gsheet":
            try:
                csv_url = convert_gsheet_url_to_csv(payload.get("url") or "")
                req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    csv_text = resp.read().decode("utf-8-sig", errors="replace")
                rows = parse_csv_rows(csv_text)
                self._send_json({"rows": rows})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif parsed.path == "/api/parse-csv":
            try:
                rows = parse_csv_rows(payload.get("csvText") or "")
                self._send_json({"rows": rows})
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif parsed.path == "/api/generate":
            try:
                bg_hex = payload.get("bgHex") or "#ffffff"
                text_hex = payload.get("textHex") or "#090d16"
                seed_offset = int(payload.get("styleSeedOffset") or 0)
                rows = payload.get("rows") or []

                results = []
                for r in rows:
                    ph = normalize_placeholder(r.get("placeholder", ""))
                    fname = slugify_webp(r.get("nama_file", ""))
                    out_local = os.path.join(GENERATED_DIR, fname)
                    w, h = generate_card(
                        out_path=out_local,
                        placeholder=ph,
                        badge=r.get("badge", ""),
                        judul=r.get("judul", ""),
                        deskripsi=r.get("deskripsi", ""),
                        bg_hex=bg_hex,
                        text_hex=text_hex,
                        nama_file=fname,
                        style_seed_offset=seed_offset,
                    )
                    results.append({
                        "placeholder": ph,
                        "nama_file": fname,
                        "alt_text": r.get("alt_text", ""),
                        "width": w,
                        "height": h,
                    })

                self._send_json({
                    "message": f"Langkah 1 Selesai: {len(results)} gambar siap dicek di Preview. Klik '2. Upload & Pasang ke Astro' jika sudah sesuai.",
                    "items": results,
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)

        elif parsed.path == "/api/upload":
            try:
                md_path = (payload.get("mdPath") or "").strip()
                astro_dir = (payload.get("astroImgDir") or "").strip()
                public_dir = (payload.get("publicBlogDir") or "").strip()
                rows = payload.get("rows") or []

                logs = upload_and_replace_placeholders(
                    md_path=md_path,
                    astro_img_dir=astro_dir,
                    public_blog_dir=public_dir,
                    rows=rows,
                )

                ringkasan = ", ".join(logs) if logs else "File disalin"
                self._send_json({
                    "message": f"Langkah 2 Selesai (Terkunci Anti-Double): {ringkasan}.",
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        pass


def main():
    os.makedirs(GENERATED_DIR, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    url = f"http://{HOST}:{PORT}/"
    print(f"Server Astro Image Generator v6 aktif di: {url}")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()


if __name__ == "__main__":
    main()