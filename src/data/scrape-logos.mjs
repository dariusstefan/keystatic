import { mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join, extname } from 'path';
import * as cheerio from 'cheerio';

const companies = JSON.parse(readFileSync('./whoisusing.json', 'utf-8'));

const OUT_DIR = './logos';
const TIMEOUT_MS = 8000;
const CONCURRENCY = 5;

mkdirSync(OUT_DIR, { recursive: true });

const results = [];

// Score candidate logos — higher = better
function scoreLogo(url, attr) {
  let score = 0;
  const u = url.toLowerCase();

  // Strongly prefer SVG
  if (u.endsWith('.svg')) score += 50;

  // Prefer PNG over JPG
  if (u.endsWith('.png')) score += 20;

  // Keywords that suggest it's a logo
  const logoKeywords = ['logo', 'brand', 'mark', 'symbol', 'identity'];
  for (const kw of logoKeywords) {
    if (u.includes(kw)) score += 15;
  }

  // Penalise icons/favicons (too small)
  const badKeywords = ['favicon', 'icon-', 'sprite', 'badge', 'thumb', 'avatar', 'placeholder'];
  for (const kw of badKeywords) {
    if (u.includes(kw)) score -= 30;
  }

  // Prefer apple-touch-icon over basic favicon
  if (attr === 'apple-touch-icon') score += 10;
  if (attr === 'og:image') score += 5;
  if (attr === 'img-src') score += 5;

  return score;
}

function resolveUrl(base, href) {
  try {
    return new URL(href, base).href;
  } catch {
    return null;
  }
}

function slugify(name) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function getExtension(url, contentType) {
  // Try URL first
  const urlExt = extname(new URL(url).pathname).toLowerCase();
  if (['.svg', '.png', '.jpg', '.jpeg', '.webp'].includes(urlExt)) return urlExt;

  // Fall back to content-type
  if (contentType?.includes('svg')) return '.svg';
  if (contentType?.includes('png')) return '.png';
  if (contentType?.includes('webp')) return '.webp';
  if (contentType?.includes('jpeg') || contentType?.includes('jpg')) return '.jpg';

  return '.png'; // default
}

const BROWSER_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.9',
  'Cache-Control': 'no-cache',
  'Upgrade-Insecure-Requests': '1',
};

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: { ...BROWSER_HEADERS, ...(options.headers || {}) },
    });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

async function downloadImage(url, destPath) {
  const res = await fetchWithTimeout(url, {
    headers: { 'Accept': 'image/svg+xml,image/png,image/webp,image/*,*/*' }
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const buffer = await res.arrayBuffer();
  writeFileSync(destPath, Buffer.from(buffer));
  return res.headers.get('content-type');
}

async function scrapeLogos(company) {
  const { name, website } = company;
  const slug = slugify(name);

  let html, baseUrl;

  try {
    const res = await fetchWithTimeout(website, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; LogoScraper/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
      },
      redirect: 'follow',
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    baseUrl = res.url; // follow redirects
    html = await res.text();
  } catch (err) {
    return { ...company, slug, logo: null, error: `Fetch failed: ${err.message}` };
  }

  const $ = cheerio.load(html);
  const candidates = [];

  // 1. <link rel="apple-touch-icon">
  $('link[rel*="apple-touch-icon"]').each((_, el) => {
    const href = $(el).attr('href');
    const url = resolveUrl(baseUrl, href);
    if (url) candidates.push({ url, attr: 'apple-touch-icon', score: scoreLogo(url, 'apple-touch-icon') });
  });

  // 2. <link rel="icon"> with SVG or large size
  $('link[rel="icon"], link[rel="shortcut icon"]').each((_, el) => {
    const href = $(el).attr('href');
    const sizes = $(el).attr('sizes') || '';
    const url = resolveUrl(baseUrl, href);
    if (!url) return;
    let score = scoreLogo(url, 'icon');
    // Boost larger declared sizes
    const sizeMatch = sizes.match(/(\d+)x(\d+)/);
    if (sizeMatch) score += Math.min(parseInt(sizeMatch[1]) / 10, 20);
    candidates.push({ url, attr: 'icon', score });
  });

  // 3. og:image
  $('meta[property="og:image"]').each((_, el) => {
    const content = $(el).attr('content');
    const url = resolveUrl(baseUrl, content);
    if (url) candidates.push({ url, attr: 'og:image', score: scoreLogo(url, 'og:image') });
  });

  // 4. twitter:image
  $('meta[name="twitter:image"]').each((_, el) => {
    const content = $(el).attr('content');
    const url = resolveUrl(baseUrl, content);
    if (url) candidates.push({ url, attr: 'twitter:image', score: scoreLogo(url, 'twitter:image') });
  });

  // 5. <img> tags with logo-like src/alt/class
  $('img').each((_, el) => {
    const src = $(el).attr('src');
    const alt = ($(el).attr('alt') || '').toLowerCase();
    const cls = ($(el).attr('class') || '').toLowerCase();
    const id = ($(el).attr('id') || '').toLowerCase();

    if (!src) return;

    const isLogoLike =
      alt.includes('logo') ||
      cls.includes('logo') ||
      id.includes('logo') ||
      src.toLowerCase().includes('logo');

    if (!isLogoLike) return;

    const url = resolveUrl(baseUrl, src);
    if (url) candidates.push({ url, attr: 'img-src', score: scoreLogo(url, 'img-src') + 10 });
  });

  if (candidates.length === 0) {
    return { ...company, slug, logo: null, error: 'No logo candidates found' };
  }

  // Sort by score descending, try to download the best one
  candidates.sort((a, b) => b.score - a.score);

  for (const candidate of candidates.slice(0, 3)) {
    try {
      const ext = getExtension(candidate.url, null);
      const filename = `${slug}${ext}`;
      const destPath = join(OUT_DIR, filename);
      await downloadImage(candidate.url, destPath);

      return {
        name,
        website,
        slug,
        logo: `/logos/whoisusing/${filename}`,
        logoUrl: candidate.url,
        attr: candidate.attr,
        score: candidate.score,
        error: null,
      };
    } catch (err) {
      // try next candidate
    }
  }

  return { ...company, slug, logo: null, error: 'All candidates failed to download' };
}

// Process in batches to avoid hammering servers
async function processBatch(batch) {
  return Promise.all(batch.map(c => scrapeLogos(c)));
}

console.log(`\nScraping logos for ${companies.length} companies...\n`);

let success = 0, failed = 0;

for (let i = 0; i < companies.length; i += CONCURRENCY) {
  const batch = companies.slice(i, i + CONCURRENCY);
  const batchResults = await processBatch(batch);

  for (const result of batchResults) {
    if (result.logo) {
      console.log(`✓  ${result.name.padEnd(35)} ${result.attr} (score: ${result.score})`);
      success++;
    } else {
      console.log(`✗  ${result.name.padEnd(35)} ${result.error}`);
      failed++;
    }
    results.push(result);
  }
}

// Write manifest
writeFileSync('./whoisusing-resolved.json', JSON.stringify(results, null, 2));

console.log(`\n─────────────────────────────────`);
console.log(`✓ Success: ${success}`);
console.log(`✗ Failed:  ${failed}`);
console.log(`Manifest saved to whoisusing-resolved.json`);
console.log(`Logos saved to ./logos/`);
