import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

const siteUrl = new URL("https://netmediatop.com/");
const sitemapUrl = new URL("sitemap-index.xml", siteUrl);
const indexNowEndpoint = "https://api.indexnow.org/indexnow";
const publicDirectory = resolve(process.cwd(), "public");

function findIndexNowKey() {
  const configuredKey = process.env.INDEXNOW_KEY?.trim();
  const candidateFiles = readdirSync(publicDirectory).filter((fileName) =>
    /^[a-f0-9]{32}\.txt$/i.test(fileName),
  );

  const matchingFiles = candidateFiles
    .map((fileName) => {
      const key = fileName.slice(0, -4);
      const fileContents = readFileSync(
        resolve(publicDirectory, fileName),
        "utf8",
      ).trim();
      return fileContents === key ? key : null;
    })
    .filter(Boolean);

  const key = configuredKey || matchingFiles[0];
  if (!key) {
    throw new Error(
      "IndexNow key tidak ditemukan. Tambahkan public/{key}.txt dengan isi yang sama.",
    );
  }

  if (!candidateFiles.includes(`${key}.txt`) || !matchingFiles.includes(key)) {
    throw new Error(
      `File verifikasi public/${key}.txt tidak cocok dengan key.`,
    );
  }

  return key;
}

function getLocValues(xml) {
  return [...xml.matchAll(/<loc>([\s\S]*?)<\/loc>/gi)].map((match) =>
    match[1]
      .trim()
      .replaceAll("&amp;", "&")
      .replaceAll("&lt;", "<")
      .replaceAll("&gt;", ">")
      .replaceAll("&quot;", '"')
      .replaceAll("&apos;", "'"),
  );
}

async function getSitemapUrls() {
  const indexResponse = await fetch(sitemapUrl);
  if (!indexResponse.ok) {
    throw new Error(
      `Gagal mengambil sitemap index (${indexResponse.status}): ${sitemapUrl}`,
    );
  }

  const indexXml = await indexResponse.text();
  const sitemapLocations = getLocValues(indexXml);
  const sitemapFiles = indexXml.includes("<sitemapindex")
    ? sitemapLocations
    : [sitemapUrl.href];
  const urls = new Set();

  for (const sitemapLocation of sitemapFiles) {
    const sitemapResponse = await fetch(sitemapLocation);
    if (!sitemapResponse.ok) {
      throw new Error(
        `Gagal mengambil sitemap (${sitemapResponse.status}): ${sitemapLocation}`,
      );
    }

    for (const value of getLocValues(await sitemapResponse.text())) {
      const url = new URL(value);
      if (
        url.origin === siteUrl.origin &&
        url.protocol === "https:" &&
        !url.search &&
        !url.hash
      ) {
        urls.add(url.href);
      }
    }
  }

  return [...urls];
}

async function main() {
  const key = findIndexNowKey();
  const urls = await getSitemapUrls();
  if (urls.length === 0) {
    throw new Error("Tidak ada URL situs yang dapat dikirim dari sitemap.");
  }

  const response = await fetch(indexNowEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=utf-8" },
    body: JSON.stringify({
      host: siteUrl.hostname,
      key,
      keyLocation: new URL(`${key}.txt`, siteUrl).href,
      urlList: urls,
    }),
  });

  if (![200, 202].includes(response.status)) {
    const responseBody = await response.text();
    throw new Error(
      `IndexNow menolak permintaan (${response.status}): ${responseBody}`,
    );
  }

  console.log(
    `IndexNow menerima ${urls.length} URL (HTTP ${response.status}). Ini notifikasi crawl, bukan jaminan URL masuk indeks.`,
  );
}

main().catch((error) => {
  console.error(`[IndexNow] ${error.message}`);
  process.exitCode = 1;
});
