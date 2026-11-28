from datetime import datetime
import json
import os
import re
import sys
from google import genai
from google.genai import types
import gspread

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
  sys.path.insert(0, SCRIPT_DIR)

import image_generator as img_gen

BLOG_CONTENT_DIR = os.path.join(PROJECT_ROOT, "src", "content", "blog")
ASTRO_IMG_DIR = os.path.join(PROJECT_ROOT, "src", "assets", "images", "blog")
PUBLIC_BLOG_DIR = os.path.join(PROJECT_ROOT, "public", "blog")
LLMS_TXT_PATH = os.path.join(PROJECT_ROOT, "public", "llms.txt")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")

SERVICE_LINKS = {
    "jasa pembuatan website": "/services/jasa-pembuatan-website",
    "jasa seo": "/services/jasa-seo",
    "jasa iklan google ads": "/services/jasa-iklan-google-ads",
    "jasa iklan facebook": "/services/jasa-iklan-facebook",
    "jasa konten sosmed": "/services/jasa-konten-sosmed",
    "penulis artikel": "/services/penulis-artikel",
    "studi kasus": "/studi-kasus",
}


def connect_sheets():
  if not GOOGLE_CREDS_JSON or not SHEET_ID:
    raise ValueError(
        "Environment variable GOOGLE_SHEETS_CREDENTIALS atau SHEET_ID belum"
        " diatur."
    )
  creds_dict = json.loads(GOOGLE_CREDS_JSON)
  client = gspread.service_account_from_dict(creds_dict)
  sheet = client.open_by_key(SHEET_ID)
  return sheet.worksheet("Master_Topik"), sheet.worksheet("Published_Index")


def get_cluster_internal_links(published_sheet, category: str) -> str:
  records = published_sheet.get_all_records()
  cat_clean = category.strip().lower()
  related = [
      f"- [{r.get('judul')}](/blog/{r.get('slug_url')})"
      for r in records
      if str(r.get("cluster_kategori", "")).strip().lower() == cat_clean
      and r.get("slug_url")
  ]
  service_url = SERVICE_LINKS.get(cat_clean, "/services")
  links_text = f"- Halaman Layanan Utama: [{category.title()}]({service_url})\n"
  if related:
    links_text += "\n".join(related[-5:])
  return links_text


def generate_article_with_gemini(row_data: dict, internal_links: str) -> dict:
  if not GEMINI_API_KEY:
    raise ValueError("Environment variable GEMINI_API_KEY belum diatur.")

  client = genai.Client(api_key=GEMINI_API_KEY)
  keyword = row_data.get("target_keyword", "").strip()
  category = row_data.get("cluster_kategori", "jasa seo").strip().lower()
  lsi = row_data.get("lsi_keywords", "")
  paa = row_data.get("paa_questions", "")
  angle = row_data.get("unique_angle", "")
  experience = row_data.get("catatan_pengalaman", "")
  geo_data = row_data.get("data_fakta_geo", "")

  system_instruction = """
Kamu adalah Senior SEO Content Strategist dan Praktisi Digital Marketing di NetMediaTop.
Tugasmu menulis artikel blog bahasa Indonesia yang memenuhi standar SEO, AEO (Answer Engine Optimization), GEO (Generative Engine Optimization), dan E-E-A-T.

ATURAN WAJIB STRUKTUR & KUALITAS:
1. AEO (Paragraf Pembuka): Paragraf pertama maksimal 50 kata dan langsung menjawab inti kata kunci secara lugas (cetak tebal inti jawabannya).
2. PLACEHOLDER GAMBAR (WAJIB PERSIS): Sisipkan tag placeholder berikut di dalam badan artikel agar dapat diproses oleh generator gambar otomatis:
   - Letakkan `{{hero}}` tepat setelah paragraf pembuka pertama.
   - Letakkan `{{slot1}}`, `{{slot2}}`, dan `{{slot3}}` masing-masing di bawah 3 sub-heading H2 utama.
   - Letakkan `{{cta}}` di bagian penutup sebelum kesimpulan akhir.
3. GEO (Generative Engine): Wajib sertakan minimal 1 tabel perbandingan Markdown dan daftar poin (bullet points) berisi fakta/angka dari data referensi. Dilarang menggunakan kalimat klise pembuka seperti "Di era digital saat ini..." atau "Tidak dapat dipungkiri...".
4. E-E-A-T (Experience): Buat satu bagian H2 khusus studi kasus/pengalaman lapangan, dan olah 'Catatan Pengalaman Penulis' menggunakan sudut pandang orang pertama ("Saya" atau "Tim NetMediaTop").
5. FAQ (AEO): Buat bagian H2 "Pertanyaan yang Sering Diajukan (FAQ)" yang menjawab seluruh daftar pertanyaan PAA secara ringkas.
6. INTERNAL LINKING: Sisipkan 2-3 tautan internal dari daftar yang diberikan secara natural di dalam kalimat.
7. Output HARUS berupa JSON valid sesuai skema yang diminta.
"""

  user_prompt = f"""
Buat artikel lengkap berdasarkan data riset berikut:
- Target Keyword: {keyword}
- Kategori Cluster: {category}
- LSI Keywords: {lsi}
- Pertanyaan Pengguna (PAA): {paa}
- Sudut Pandang Unik (Unique Angle): {angle}
- Catatan Pengalaman Nyata Penulis (WAJIB MASUK): {experience}
- Data Fakta & Angka Valid (GEO): {geo_data}
- Daftar Internal Link Tersedia:
{internal_links}
"""

  response_schema = {
      "type": "OBJECT",
      "properties": {
          "title": {"type": "STRING"},
          "slug": {"type": "STRING"},
          "description": {"type": "STRING"},
          "tags": {"type": "ARRAY", "items": {"type": "STRING"}},
          "keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
          "markdown_body": {"type": "STRING"},
      },
      "required": [
          "title",
          "slug",
          "description",
          "tags",
          "keywords",
          "markdown_body",
      ],
  }

  response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=user_prompt,
      config=types.GenerateContentConfig(
          system_instruction=system_instruction,
          response_mime_type="application/json",
          response_schema=response_schema,
          temperature=0.4,
      ),
  )
  return json.loads(response.text)


def validate_article(article_data: dict):
  body = article_data.get("markdown_body", "")
  word_count = len(body.split())
  if word_count < 550:
    raise ValueError(
        f"Artikel terlalu pendek ({word_count} kata). Minimal 550 kata."
    )
  if "| ---" not in body and "|---" not in body and "|:---" not in body:
    raise ValueError("Validasi GEO gagal: Tidak ditemukan tabel Markdown.")
  forbidden_phrases = [
      "di era digital saat ini",
      "dalam dunia yang terus berkembang",
      "tidak dapat dipungkiri bahwa",
  ]
  body_lower = body.lower()
  for phrase in forbidden_phrases:
    if phrase in body_lower:
      raise ValueError(
          f"Validasi Kualitas gagal: Ditemukan frasa klise AI '{phrase}'."
      )


def build_astro_post_and_images(
    article_data: dict, category: str, pub_date: str
) -> tuple[str, str]:
  clean_slug = re.sub(
      r"[^a-z0-9]+", "-", article_data["slug"].lower()
  ).strip("-")
  md_filename = f"{clean_slug}.md"
  md_filepath = os.path.join(BLOG_CONTENT_DIR, md_filename)

  safe_title = article_data["title"].replace('"', '\\"')
  safe_desc = article_data["description"].replace('"', '\\"')
  tags_json = json.dumps(article_data["tags"], ensure_ascii=False)
  keywords_json = json.dumps(article_data["keywords"], ensure_ascii=False)

  frontmatter = f"""---
title: "{safe_title}"
pubDate: "{pub_date}"
description: "{safe_desc}"
author: "Tri Pudjo-NetMediaTop"
image: "{{{{fitur}}}}"
category: "{category}"
tags: {tags_json}
keywords: {keywords_json}
---

"""
  os.makedirs(BLOG_CONTENT_DIR, exist_ok=True)
  with open(md_filepath, "w", encoding="utf-8", newline="\n") as f:
    f.write(frontmatter + article_data["markdown_body"].strip() + "\n")

  print(f"[ImageGen] Memindai placeholder gambar pada {md_filename}...")
  rows = img_gen.scan_markdown_for_rows(md_filepath)

  os.makedirs(img_gen.GENERATED_DIR, exist_ok=True)
  for r in rows:
    ph = img_gen.normalize_placeholder(r.get("placeholder", ""))
    fname = img_gen.slugify_webp(r.get("nama_file", ""))
    out_local = os.path.join(img_gen.GENERATED_DIR, fname)
    img_gen.generate_card(
        out_path=out_local,
        placeholder=ph,
        badge=r.get("badge", ""),
        judul=r.get("judul", ""),
        deskripsi=r.get("deskripsi", ""),
        bg_hex="#ffffff",
        text_hex="#090d16",
        nama_file=fname,
        style_seed_offset=0,
    )

  logs = img_gen.upload_and_replace_placeholders(
      md_path=md_filepath,
      astro_img_dir=ASTRO_IMG_DIR,
      public_blog_dir=PUBLIC_BLOG_DIR,
      rows=rows,
  )
  print(f"[ImageGen] Berhasil memasang {len(logs)} gambar WebP ke Astro.")
  return clean_slug, md_filepath


def update_llms_txt(title: str, slug: str, description: str):
  if not os.path.exists(LLMS_TXT_PATH):
    return
  with open(LLMS_TXT_PATH, "r", encoding="utf-8") as f:
    content = f.read()

  entry = f"- [{title}](https://netmediatop.com{slug}): {description}\n"
  if slug not in content:
    with open(LLMS_TXT_PATH, "w", encoding="utf-8", newline="\n") as f:
      f.write(content.rstrip() + "\n" + entry)
    print("[GEO] public/llms.txt diperbarui.")


def main():
  print("=== Memulai Pipeline Auto-Blog NetMediaTop ===")
  master_sheet, published_sheet = connect_sheets()
  all_rows = master_sheet.get_all_records()

  target_row_idx = None
  target_data = None
  today_str = datetime.now().strftime("%Y-%m-%d")

  for idx, row in enumerate(all_rows, start=2):
    status = str(row.get("status", "")).strip().lower()
    exp = str(row.get("catatan_pengalaman", "")).strip()
    sched_date = str(row.get("publish_date", "")).strip()

    if status == "ready" and exp:
      if not sched_date or sched_date <= today_str:
        target_row_idx = idx
        target_data = row
        break

  if not target_data:
    print(
        "Tidak ada topik berstatus 'ready' yang memenuhi syarat hari ini."
        " Selesai."
    )
    return

  keyword = target_data.get("target_keyword")
  category = str(target_data.get("cluster_kategori", "jasa seo")).strip().lower()
  pub_date = str(target_data.get("publish_date") or today_str).strip()

  print(f"[1/4] Memproses topik: '{keyword}' (Kategori: {category})")
  internal_links = get_cluster_internal_links(published_sheet, category)

  print("[2/4] Menghasilkan artikel via Gemini API...")
