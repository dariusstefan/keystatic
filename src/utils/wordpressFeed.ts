export type FeedItem = {
  title: string;
  link: string;
  pubDate: Date;
  description: string;
  author?: string;
};

const decodeEntities = (s: string): string =>
  s
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));

const stripCdata = (s: string): string => s.replace(/^<!\[CDATA\[([\s\S]*?)\]\]>$/, '$1').trim();

const stripHtml = (s: string): string => s.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

const pick = (block: string, tag: string): string => {
  const re = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i');
  const m = block.match(re);
  return m ? stripCdata(m[1]) : '';
};

export async function fetchWordPressFeed(feedUrl: string, limit = 5): Promise<FeedItem[]> {
  try {
    const res = await fetch(feedUrl, {
      headers: { 'User-Agent': 'opensips.org-build/1.0' },
    });
    if (!res.ok) {
      console.warn(`[wordpressFeed] ${feedUrl} returned ${res.status}`);
      return [];
    }
    const xml = await res.text();
    const items = [...xml.matchAll(/<item>([\s\S]*?)<\/item>/g)].slice(0, limit);
    return items.map((m) => {
      const block = m[1];
      const rawDescription = pick(block, 'description');
      return {
        title: decodeEntities(pick(block, 'title')),
        link: pick(block, 'link'),
        pubDate: new Date(pick(block, 'pubDate')),
        description: decodeEntities(stripHtml(rawDescription)).slice(0, 200) + '…',
        author: decodeEntities(pick(block, 'dc:creator') || pick(block, 'author')),
      };
    });
  } catch (err) {
    console.warn(`[wordpressFeed] failed to fetch ${feedUrl}:`, err);
    return [];
  }
}
