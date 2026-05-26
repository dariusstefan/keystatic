export interface Version {
  branch: string;
  label: string;
  isLatest?: boolean;
}

export const VERSIONS: Version[] = [
  { branch: 'master', label: 'master (dev)', isLatest: true },
  { branch: '4.0', label: '4.0' },
  { branch: '3.6', label: '3.6' },
  { branch: '3.5', label: '3.5' },
];

export const LATEST_VERSION = VERSIONS.find((v) => v.isLatest)!;

export function branchToSlug(branch: string): string {
  return branch.replace(/\./g, '-');
}

export function slugToBranch(slug: string): string {
  // Find the version whose slug matches (e.g. "4-0" → "4.0")
  return VERSIONS.find((v) => branchToSlug(v.branch) === slug)?.branch ?? slug;
}

export function getModuleUrl(module: string, branch: string): string {
  const v = VERSIONS.find((v) => v.branch === branch);
  return v?.isLatest ? `/modules/${module}` : `/modules/${module}/${branchToSlug(branch)}`;
}
