export type VersionStatus = 'development' | 'beta' | 'stable' | 'lts' | 'eol';

export interface Version {
  /** Version series, e.g. "3.6", "4.0", "4.1" */
  series: string;
  status: VersionStatus;
  /** Marketing label, e.g. "Current LTS", "Beta", "Master" */
  label?: string;
  releaseDate?: string;
  betaReleaseDate?: string;
  lastReleaseDate?: string;
  minorReleases?: number;
  supportedUntil?: string;
  /** Slug for the per-version docs page (Starlight). null = no docs yet. */
  docsSlug?: string | null;
}

/**
 * OpenSIPS release history.
 * Source of truth — the /about/versions page and any version pickers should read from here.
 * Update this file when a new version is released or status changes.
 */
export const versions: Version[] = [
  {
    series: '4.1',
    status: 'development',
    label: 'Master',
    betaReleaseDate: 'May 2027',
    minorReleases: 0,
    docsSlug: null,
  },
  {
    series: '4.0',
    status: 'beta',
    label: 'Beta',
    betaReleaseDate: 'April 2026',
    supportedUntil: 'December 2027',
    minorReleases: 0,
    docsSlug: null,
  },
  {
    series: '3.6',
    status: 'lts',
    label: 'Current LTS',
    releaseDate: '23 July 2025',
    betaReleaseDate: '21 May 2025',
    lastReleaseDate: '6 May 2026',
    minorReleases: 5,
    supportedUntil: '21 May 2028',
    docsSlug: null,
  },
  {
    series: '3.5',
    status: 'eol',
    releaseDate: '25 July 2024',
    betaReleaseDate: '9 May 2024',
    lastReleaseDate: '18 December 2025',
    minorReleases: 9,
    supportedUntil: 'December 2025',
    docsSlug: null,
  },
  {
    series: '3.4',
    status: 'eol',
    releaseDate: '19 July 2023',
    betaReleaseDate: '17 May 2023',
    lastReleaseDate: '6 May 2026',
    minorReleases: 18,
    supportedUntil: 'May 2026',
    docsSlug: null,
  },
  {
    series: '3.3',
    status: 'eol',
    releaseDate: '14 July 2022',
    betaReleaseDate: '18 May 2022',
    lastReleaseDate: '20 December 2023',
    minorReleases: 9,
    supportedUntil: 'December 2023',
    docsSlug: null,
  },
  {
    series: '3.2',
    status: 'eol',
    label: 'LTS',
    releaseDate: '21 July 2021',
    betaReleaseDate: '27 May 2021',
    lastReleaseDate: '19 June 2024',
    minorReleases: 19,
    supportedUntil: 'May 2024',
    docsSlug: null,
  },
  {
    series: '3.1',
    status: 'eol',
    label: 'LTS',
    releaseDate: '22 July 2020',
    betaReleaseDate: '27 May 2020',
    lastReleaseDate: '31 August 2023',
    minorReleases: 17,
    supportedUntil: '31 August 2023',
    docsSlug: null,
  },
  {
    series: '3.0',
    status: 'eol',
    releaseDate: '29 May 2019',
    betaReleaseDate: '16 April 2019',
    lastReleaseDate: '22 December 2020',
    minorReleases: 5,
    supportedUntil: '22 December 2020',
    docsSlug: null,
  },
  {
    series: '2.4',
    status: 'eol',
    label: 'LTS',
    releaseDate: '30 April 2018',
    betaReleaseDate: '28 March 2018',
    lastReleaseDate: '22 June 2021',
    minorReleases: 11,
    supportedUntil: '22 June 2021',
    docsSlug: null,
  },
  {
    series: '2.3',
    status: 'eol',
    releaseDate: '26 April 2017',
    betaReleaseDate: '16 March 2017',
    lastReleaseDate: '14 August 2018',
    minorReleases: 6,
    supportedUntil: '26 October 2018',
    docsSlug: null,
  },
  {
    series: '2.2',
    status: 'eol',
    label: 'LTS',
    releaseDate: '27 May 2016',
    betaReleaseDate: '31 March 2016',
    lastReleaseDate: '11 June 2018',
    minorReleases: 8,
    supportedUntil: '11 June 2019',
    docsSlug: null,
  },
  {
    series: '2.1',
    status: 'eol',
    releaseDate: '7 May 2015',
    betaReleaseDate: '18 March 2015',
    lastReleaseDate: '19 October 2016',
    minorReleases: 5,
    supportedUntil: '7 November 2016',
    docsSlug: null,
  },
  {
    series: '1.11',
    status: 'eol',
    label: 'LTS',
    releaseDate: '7 May 2014',
    betaReleaseDate: '20 March 2014',
    lastReleaseDate: '18 May 2017',
    minorReleases: 11,
    supportedUntil: '18 May 2017',
    docsSlug: null,
  },
  {
    series: '1.10',
    status: 'eol',
    releaseDate: '10 September 2013',
    betaReleaseDate: '5 August 2013',
    lastReleaseDate: '7 May 2015',
    minorReleases: 5,
    docsSlug: null,
  },
  {
    series: '1.9',
    status: 'eol',
    releaseDate: '27 February 2013',
    betaReleaseDate: '29 January 2013',
    lastReleaseDate: '12 March 2014',
    minorReleases: 2,
    docsSlug: null,
  },
  {
    series: '1.8',
    status: 'eol',
    releaseDate: '17 May 2012',
    betaReleaseDate: '22 March 2012',
    lastReleaseDate: '7 May 2015',
    minorReleases: 8,
    docsSlug: null,
  },
  {
    series: '1.7',
    status: 'eol',
    releaseDate: '26 August 2011',
    betaReleaseDate: '12 June 2011',
    lastReleaseDate: '22 February 2012',
    minorReleases: 2,
    docsSlug: null,
  },
  {
    series: '1.6',
    status: 'eol',
    releaseDate: '16 October 2009',
    lastReleaseDate: '20 December 2010',
    minorReleases: 4,
    docsSlug: null,
  },
  {
    series: '1.5',
    status: 'eol',
    releaseDate: '23 March 2009',
    lastReleaseDate: '27 August 2009',
    minorReleases: 3,
    docsSlug: null,
  },
  {
    series: '1.4',
    status: 'eol',
    releaseDate: '4 August 2008',
    lastReleaseDate: '23 March 2009',
    minorReleases: 4,
    docsSlug: null,
  },
];

export function getActive(): Version[] {
  return versions.filter((v) => v.status === 'development' || v.status === 'beta' || v.status === 'lts' || v.status === 'stable');
}

export function getHistorical(): Version[] {
  return versions.filter((v) => v.status === 'eol');
}

export function versionHref(v: Version): string {
  return v.docsSlug ? `/documentation/versions/${v.docsSlug}` : `/documentation/versions/${v.series.replace(/\./g, '-')}`;
}

export const STATUS_LABELS: Record<VersionStatus, string> = {
  development: 'Under development',
  beta: 'Beta',
  stable: 'Stable',
  lts: 'Long-Term Supported',
  eol: 'End of life',
};

export const STATUS_BADGE: Record<VersionStatus, string> = {
  development: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
  beta: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
  stable: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
  lts: 'bg-primary/15 text-primary',
  eol: 'bg-gray-200 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
};
