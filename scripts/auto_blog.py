from datetime import datetime
import json
import os
import re
import sys
from oauth2client.service_account import ServiceAccountCredentials

# Pastikan folder scripts/ masuk ke sys.path agar bisa import image_generator.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
  sys.path.insert(0, SCRIPT_DIR)

import image_generator as img_gen

# ==========================================
# KONFIGURASI DIREKTORI & KREDENSIAL
# ==========================================
BLOG_CONTENT_DIR = os.path.join(PROJECT_ROOT, "src", "content", "blog")
ASTRO_IMG_DIR = os.path.join(PROJECT_ROOT, "src", "assets", "images", "blog")
PUBLIC_BLOG_DIR = os.path.join(PROJECT_ROOT, "public", "blog")
LLMS_TXT_PATH = os.path.join(PROJECT_ROOT, "public", "llms.txt")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")

# Pemetaan URL halaman layanan untuk Internal Linking otomatis
SERVICE_LINKS = {
    "jasa pembuatan website": "/services/jasa-pembuatan-website",
    "jasa seo": "/services/jasa-seo",
    "jasa iklan google ads": "/services/jasa-iklan-google-ads",
    "jasa iklan facebook": "/services/jasa-iklan-facebook",
    "jasa konten sosmed": "/services/jasa-konten-sosmed",
    "penulis artikel": "/services/penulis-artikel",
    "studi kasus": "/studi-kasus",
}


# ==========================================
# 1. KONEKSI GOOGLE SHEETS
# ==========================================
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



# ==========================================
# 2. AMBIL ARTIKEL LAMA UNTUK INTERNAL LINKING
# ==========================================
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
    links_text += "\n".join(related[-5:])  # Ambil maksimal 5 artikel terbaru
  return links_text


# ==========================================
# 3. GENERATE ARTIKEL VIA GEMINI API (SEO + AEO + GEO + E-E-A-T)
# ==========================================
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

  # Skema JSON terstruktur agar metadata Astro & isi Markdown terpisah rapi
  response_schema = {
      "type": "OBJECT",
      "properties": {
          "title": {
              "type": "STRING",
              "description": (
                  "Judul artikel SEO menarik, maksimal 65 karakter, mengandung"
                  " target keyword."
              ),
          },
          "slug": {
              "type": "STRING",
              "description": (
                  "URL slug huruf kecil dipisah tanda hubung, tanpa kata sambung"
                  " berlebihan."
              ),
          },
          "description": {
              "type": "STRING",
              "description": (
                  "Meta description maksimal 155 karakter yang merangkum"
                  " manfaat artikel."
              ),
          },
          "tags": {
              "type": "ARRAY",
              "items": {"type": "STRING"},
              "description": "3 sampai 5 tag relevan huruf kecil.",
          },
          "keywords": {
              "type": "ARRAY",
              "items": {"type": "STRING"},
              "description": (
                  "5 sampai 7 kata kunci turunan untuk frontmatter keywords."
              ),
          },
          "markdown_body": {
              "type": "STRING",
              "description": (
                  "Isi lengkap artikel dalam format Markdown (mulai langsung"
                  " dari paragraf pembuka, tanpa judul H1 dan tanpa"
                  " frontmatter). Wajib memuat {{hero}}, {{slot1}}, {{slot2}},"
                  " {{slot3}}, dan {{cta}}."
              ),
          },
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


# ==========================================
# 4. QUALITY GATE (VALIDASI ANTI-KLISE & STRUKTUR)
# ==========================================
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


# ==========================================
# 5. SIMPAN MARKDOWN ASTRO & RENDER GAMBAR OTOMATIS
# ==========================================
def build_astro_post_and_images(
    article_data: dict, category: str, pub_date: str
) -> tuple[str, str]:
  clean_slug = re.sub(
      r"[^a-z0-9]+", "-", article_data["slug"].lower()
  ).strip("-")
  md_filename = f"{clean_slug}.md"
  md_filepath = os.path.join(BLOG_CONTENT_DIR, md_filename)

  # Escape tanda kutip ganda pada title dan description agar YAML valid
  safe_title = article_data["title"].replace('"', '\\"')
  safe_desc = article_data["description"].replace('"', '\\"')
  tags_json = json.dumps(article_data["tags"], ensure_ascii=False)
  keywords_json = json.dumps(article_data["keywords"], ensure_ascii=False)

  # Gunakan placeholder {{fitur}} di frontmatter agar diganti otomatis oleh image_generator.py
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
