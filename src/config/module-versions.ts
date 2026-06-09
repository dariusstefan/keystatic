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
