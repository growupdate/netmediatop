// src/utils/wikidataFetcher.ts

export interface WikidataEntity {
  name: string;
  id: string;
  sameAs: string;
}

// Memory cache untuk mencegah penembakan API berulang untuk entitas yang sama
const entityCache: Record<string, WikidataEntity> = {};

export async function fetchWikidataEntity(
  keyword: string,
): Promise<WikidataEntity | null> {
  const cleanKeyword = keyword.trim();

  if (!cleanKeyword) return null;

  // 1. Cek Cache (O(1) Access)
  if (entityCache[cleanKeyword]) {
    return entityCache[cleanKeyword];
  }

  // 2. Endpoint API Resmi Wikidata (Format JSON, Bahasa Indonesia)
  const searchUrl = `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=${encodeURIComponent(cleanKeyword)}&language=id&format=json&limit=1`;

  try {
    // 3. Gunakan native fetch() bawaan Astro (lebih cepat & bersih daripada modul 'https' Node.js)
    const response = await fetch(searchUrl, {
      headers: {
        "User-Agent": "NetmediatopBot/1.0 (https://netmediatop.com)",
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      console.warn(
        `[Knowledge Graph] Gagal fetch API Wikidata untuk: ${cleanKeyword}`,
      );
      return null;
    }

    const json = await response.json();

    // 4. Validasi dan Format Data
    if (json.search && json.search.length > 0) {
      const result = json.search[0];

      const conceptUrl = new URL(result.concepturi);
      conceptUrl.protocol = "https:";

      const entityData: WikidataEntity = {
        name: result.label,
        id: result.id,
        sameAs: conceptUrl.href,
      };

      // 5. Simpan ke Cache dan Kembalikan Hasil
      entityCache[cleanKeyword] = entityData;
      return entityData;
    }

    return null; // Jika entitas tidak ditemukan di Wikidata
  } catch (error) {
    console.error(`[Knowledge Graph] Error memproses ${cleanKeyword}:`, error);
    return null;
  }
}
