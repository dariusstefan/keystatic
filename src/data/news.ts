export interface NewsItem {
  title: string;
  url: string;
  date: string;
  description?: string;
  source?: string;
}

export const news: NewsItem[] = [
  {
    title: 'Profiling your OpenSIPS 4.0',
    url: 'https://blog.opensips.org/2026/05/08/profiling-your-opensips-4-0/',
    date: '2026-05-08',
    description: 'Profiling with OpenSIPS 4.0 or the realtime X-ray of OpenSIPS, to answers to: what my OpenSIPS is doing, why is it slow or why not handling traffic.',
    source: 'Blog',
  },
  {
    title: 'OpenSIPS Summit 2026, 28 Apr – 1 May, Bucharest',
    url: 'https://www.opensips.org/events/Summit-2026Bucharest',
    date: '2026-05-07',
    description: 'The Summit is over, enriching us with presentations, recordings and photos, all gathered for you to review!',
    source: 'Summit',
  },
  {
    title: 'OpenSIPS SBC Community Edition',
    url: 'https://ce.opensips.org/opensips-sbc/',
    date: '2026-05-06',
    description: 'We are proud to announce the latest Community Edition project: the OpenSIPS Session Border Controller.',
    source: 'CE',
  },
  {
    title: 'Minor releases: OpenSIPS 3.6.5, 3.4.18',
    url: '/about/versions',
    date: '2026-05-06',
    description: 'A new round of minor versions for all stable releases.',
    source: 'Release',
  },
  {
    title: 'OpenSIPS 4.0 beta release is out',
    url: 'https://www.opensips.org/About/Version-Overview-4-0-0',
    date: '2026-04-22',
    description: 'The 4.0 version is a turning point in the OpenSIPS evolution, opening the way to radically change and improve legacy concepts and code.',
    source: 'Release',
  },
  {
    title: 'TCP/TLS rework in OpenSIPS 4.0',
    url: 'https://blog.opensips.org/2026/04/08/tcp-tls-rework-in-opensips-4-0/',
    date: '2026-04-08',
    description: 'OpenSIPS 4.0 brings a full TCP/TLS redesign, from multi-process connection handling to a centralized, multi-threaded I/O model.',
    source: 'Blog',
  },
  {
    title: 'PRACK/UPDATE Interworking in OpenSIPS 4.0',
    url: 'https://blog.opensips.org/2026/03/25/sip-prack-interworking-support-in-opensips-4-0/',
    date: '2026-03-25',
    description: 'Bridge IMS and legacy SIP networks using either simple built-in enablement or full scripting control.',
    source: 'Blog',
  },
  {
    title: 'Bond sockets in OpenSIPS 4.0',
    url: 'https://blog.opensips.org/2026/03/11/bond-sockets-in-opensips-4-0/',
    date: '2026-03-11',
    description: 'The bond sockets make possible the proper selection of the outbound socket based on the last-minute discovered (DNS based) properties of the destination.',
    source: 'Blog',
  },
  {
    title: 'Proxy Protocol support for OpenSIPS 4.0',
    url: 'https://blog.opensips.org/2026/02/24/proxy-protocol-support-in-opensips-4-0/',
    date: '2026-02-24',
    description: 'Check out the HAProxy Proxy Protocol implementation in OpenSIPS 4.0 in our latest blog post!',
    source: 'Blog',
  },
  {
    title: 'OpenSIPS Control Panel 9.3.6 has been released!',
    url: 'https://controlpanel.opensips.org/',
    date: '2026-02-18',
    description: 'OpenSIPS Control Panel 9.3.6, compatible with OpenSIPS 3.6.x versions has just been released!',
    source: 'CP',
  },
  {
    title: 'Minor releases: OpenSIPS 3.6.4 and 3.4.17',
    url: '/about/versions',
    date: '2026-02-18',
    description: 'Two new minor versions of our stable releases are out!',
    source: 'Release',
  },
  {
    title: 'Big scaling SIP forking',
    url: 'https://blog.opensips.org/2026/02/17/big-scale-sip-forking/',
    date: '2026-02-17',
    description: 'OpenSIPS 4.0 brings dynamic allocation of high number of branches per transaction, without any memory or processing penalties.',
    source: 'Blog',
  },
  {
    title: 'Minor releases: OpenSIPS 3.6.3, 3.5.9, 3.4.16',
    url: '/about/versions',
    date: '2025-12-18',
    description: 'A new round of minor versions for all stable releases.',
    source: 'Release',
  },
  {
    title: 'Minor releases: OpenSIPS 3.6.2, 3.5.8, 3.4.15',
    url: '/about/versions',
    date: '2025-10-22',
    description: 'Two new minor versions of our stable releases are out!',
    source: 'Release',
  },
  {
    title: 'Minor releases: OpenSIPS 3.6.1, 3.5.7, 3.4.14',
    url: '/about/versions',
    date: '2025-08-20',
    description: 'A new round of minor versions for all stable releases.',
    source: 'Release',
  },
  {
    title: 'Stable release: OpenSIPS 3.6.0',
    url: '/about/versions',
    date: '2025-07-23',
    description: 'OpenSIPS 3.6 is now stable, as beta testing phase is complete!',
    source: 'Release',
  },
  {
    title: 'Minor releases: OpenSIPS 3.5.6, 3.4.13',
    url: '/about/versions',
    date: '2025-06-25',
    description: 'We just released two new minor versions, one for each stable OpenSIPS release!',
    source: 'Release',
  },
];
