export interface Version {
  branch: string;
  slug: string;
  label: string;
  isLatest?: boolean;
}

export const VERSIONS: Version[] = [
  { branch: 'master', slug: 'devel', label: '4.1 / devel', isLatest: true },
  { branch: '4.0',    slug: '4-0',   label: '4.0' },
  { branch: '3.6',    slug: '3-6',   label: '3.6' },
  { branch: '3.5',    slug: '3-5',   label: '3.5' },
  { branch: '3.4',    slug: '3-4',   label: '3.4' },
  { branch: '3.3',    slug: '3-3',   label: '3.3' },
  { branch: '3.2',    slug: '3-2',   label: '3.2' },
  { branch: '3.1',    slug: '3-1',   label: '3.1' },
  { branch: '3.0',    slug: '3-0',   label: '3.0' },
  { branch: '2.4',    slug: '2-4',   label: '2.4' },
  { branch: '2.3',    slug: '2-3',   label: '2.3' },
  { branch: '2.2',    slug: '2-2',   label: '2.2' },
  { branch: '2.1',    slug: '2-1',   label: '2.1' },
  { branch: '1.11',   slug: '1-11',  label: '1.11' },
  { branch: '1.10',   slug: '1-10',  label: '1.10' },
  { branch: '1.9',    slug: '1-9',   label: '1.9' },
  { branch: '1.8',    slug: '1-8',   label: '1.8' },
  { branch: '1.7',    slug: '1-7',   label: '1.7' },
  { branch: '1.6',    slug: '1-6',   label: '1.6' },
  { branch: '1.5',    slug: '1-5',   label: '1.5' },
  { branch: '1.4',    slug: '1-4',   label: '1.4' },
];

export const LATEST_VERSION = VERSIONS.find((v) => v.isLatest)!;

export function getModuleUrl(module: string, slug: string): string {
  return `/docs/modules/${slug}/${module}`;
}

export function getManualUrl(page: string, slug: string): string {
  // page is the sub-path after the version slug ('' for the manual index)
  return page ? `/docs/manual/${slug}/${page}` : `/docs/manual/${slug}`;
}

export function slugToVersion(slug: string): Version | undefined {
  return VERSIONS.find((v) => v.slug === slug);
}
