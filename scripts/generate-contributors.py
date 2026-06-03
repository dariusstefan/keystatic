#!/usr/bin/env python3
"""Generate contributor sections for module docs directly from git history.

Usage:
    python3 scripts/generate-contributors.py [module1 module2 ...]
    (no args = all modules in src/content/docs/modules/devel/)
"""

import math
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT         = Path(__file__).parent.parent
OPENSIPS_DIR = ROOT / 'opensips'
MODULES_ROOT = ROOT / 'src/content/docs/modules'
PLACEHOLDER  = '<!-- CONTRIBUTORS -->'

# Global project stats (last updated in build-contrib.sh)
PROJ_COMMITS   = 23226
PROJ_LINES_ADD = 2765168
PROJ_LINES_DEL = 1401082

TABLE_SIZE_COMMITS  = 10
TABLE_SIZE_ACTIVITY = 10

# ---------------------------------------------------------------------------
# Data ported from build-contrib.sh
# ---------------------------------------------------------------------------

SKIP_COMMITS = {
    'd88a1e2f6df5e591dd4162e2fa2e6e08d93e1c96',
    'a5b72648f928547d87c06c269b3118ae97b97aa4',
    '33b4d7c82f186e66311c9f215b76d55324f45adc',
    '251cc10f454050dba8f31653ee3e4c4cda87a74a',
    'b1ff52999c48688ae228e76ffa64e64f75d57b0d',
    'd41d30a8af8b79f00947dfc9600699f62b210d4d',
    'd55ce8ffc86dd433f4860d5867d03d484312d954',
    '442a83e55bb475637e75fc904f998e6d585bd437',
    '8fe24ec1990a1c468fcf8490228c2fcd42a15121',
}

# "name <email>" or "name" → canonical "name <email>"
AUTHOR_ALIASES = {
    "AgalyaR <agalya.job@gmail.com>": "Agalya Ramachandran <agalya.job@gmail.com>",
    "Alessio Garzi <agarzi@clouditalia.com>": "Alessio Garzi <gun101@email.it>",
    "Anca Vamanu": "Anca Vamanu <anca@opensips.org>",
    "Andreas Granig <andreas.granig@inode.info>": "Andreas Granig <agranig@linguin.org>",
    "Andreas Heise": "Andreas Heise <aheise@gmx.de>",
    "Andrei Pelinescu-Onciul": "Andrei Pelinescu-Onciul <andrei@iptel.org>",
    "Bogdan Andrei IANCU <bogdan@opensips.org>": "Bogdan-Andrei Iancu <bogdan@opensips.org>",
    "Bogdan-Andrei Iancu <bogdan@voice-system.ro>": "Bogdan-Andrei Iancu <bogdan@opensips.org>",
    "Bogdan Iancu <bogdan@opensips.org>": "Bogdan-Andrei Iancu <bogdan@opensips.org>",
    "Carsten Bock": "Carsten Bock <lists@bock.info>",
    "Cerghit Ionel <ionel.cerghit@gmail.com>": "Ionel Cerghit <ionel.cerghit@gmail.com>",
    "Christian Schlatter <USERNAME@DOMAIN.COM>": "Christian Schlatter <cs@unc.edu>",
    "Christophe Sollet": "Christophe Sollet <csollet-git@keyyo.com>",
    "Daniel-Constantin Mierla <daniel@opensips.org>": "Daniel-Constantin Mierla <miconda@gmail.com>",
    "Daniel-Constantin Mierla <daniel@voice-system.ro>": "Daniel-Constantin Mierla <miconda@gmail.com>",
    "davesidwell <davesidwell@users.noreply.github.com>": "Dave Sidwell <davesidwell@users.noreply.github.com>",
    "Eric Tamme <eric@uphreak.com>": "Eric Tamme <eric.tamme@onsip.com>",
    "Fabian Gast <fgast+git@only640k.net>": "Fabian Gast <fabian.gast@nfon.com>",
    "Henning Westerholt": "Henning Westerholt <henning.westerholt@1und1.de>",
    "Ionut Ionita <ionutrazvan.ionita@gmail.com>": "Ionut Ionita <ionutionita@opensips.org>",
    "Ionut Ionita <ionut.ionita@cti.pub.ro>": "Ionut Ionita <ionutionita@opensips.org>",
    "Jan Janak": "Jan Janak <jan@iptel.org>",
    "Jarrod Baumann <jarrod@unixc.org>": "Jarrod Baumann <j@rrod.org>",
    "John Riordan": "John Riordan <john@junctionnetworks.com>",
    "Juha Heinanen": "Juha Heinanen <jh@tutpro.com>",
    "Kobi Eshun": "Kobi Eshun <kobi@sightspeed.com>",
    "Maxim Sobolev <sobomax@sippysoft.com>": "Maksym Sobolyev <sobomax@sippysoft.com>",
    "NAME <USERNAME@DOMAIN.COM>": "Anonymous",
    "Norm Brandinger <n.brandinger@gmail.com>": "Norman Brandinger <n.brandinger@gmail.com>",
    "Norman Brandinger": "Norman Brandinger <n.brandinger@gmail.com>",
    "Nick Altmann <nikbyte@users.noreply.github.com>": "Nick Altmann <nick.altmann@gmail.com>",
    "Nick Altmann <nick@altmann.pro>": "Nick Altmann <nick.altmann@gmail.com>",
    "Ovidiu Sas <osas@t40>": "Ovidiu Sas <osas@voipembedded.com>",
    "Oliver Mulelid-Tynes": "Oliver Severin Mulelid-Tynes <olivermt@users.noreply.github.com>",
    "Oliver Severin Mulelid-Tynes": "Oliver Severin Mulelid-Tynes <olivermt@users.noreply.github.com>",
    "Parantido De Rica <Parantido@users.noreply.github.com>": "Parantido Julius De Rica <parantido@techfusion.it>",
    "Peter Lemenkov": "Peter Lemenkov <lemenkov@gmail.com>",
    "pasandev <pasandev@ymail.com>": "Pasan Meemaduma <pasandev@ymail.com>",
    "Ryan Bullock": "Ryan Bullock <rrb3942@gmail.com>",
    "Răzvan Crainea <razvan@opensips.org>": "Razvan Crainea <razvan@opensips.org>",
    "Răzvan Crainea <razvan.crainea@gmail.com>": "Razvan Crainea <razvan@opensips.org>",
    "Răzvan Crainea <razvancrainea@users.noreply.github.com>": "Razvan Crainea <razvan@opensips.org>",
    "Rob Gagnon <rgagnon@vcentos7.telepointglobal.com>": "Rob Gagnon <rgagnon24@gmail.com>",
    "Sergey KHripchenko <shripchenko@intermedia.net>": "Sergey Khripchenko <shripchenko@intermedia.net>",
    "shripchenko <shripchenko@intermedia.net>": "Sergey Khripchenko <shripchenko@intermedia.net>",
    "rgagnon24 <rgagnon24@gmail.com>": "Rob Gagnon <rgagnon24@gmail.com>",
    "Saúl Ibarra Corretgé <saul@ag-projects.com>": "Saúl Ibarra Corretgé <saghul@gmail.com>",
    "Stéphane Alnet": "Stéphane Alnet <stephane@shimaore.net>",
    "Vladut Paiu <vladpaiu@opensips.org>": "Vlad Paiu <vladpaiu@opensips.org>",
    "Walter Doekes": "Walter Doekes <walter+github@wjd.nu>",
    "boris_t <boris@talovikov.ru>": "Boris Talovikov <boris@talovikov.ru>",
    "csollet <csollet-git@keyyo.com>": "Christophe Sollet <csollet-git@keyyo.com>",
    "ionutrazvanionita <ionutionita@opensips.org>": "Ionut Ionita <ionutionita@opensips.org>",
    "liviuchircu <liviu@opensips.org>": "Liviu Chircu <liviu@opensips.org>",
    "root <evillaron@gmail.com>": "Evandro Villaron <evillaron@gmail.com>",
    "root <root@localhost.localdomain>": "Robison Tesini <rtesini@gmail.com>",
    "root <root@vlad-pc.(none)>": "Vlad Paiu <vladpaiu@opensips.org>",
    "root <root@dell02.xipx.local>": "Chad Attermann <chad@broadmind.com>",
    "root <root@opensips.org>": "Bogdan-Andrei Iancu <bogdan@opensips.org>",
    "rvlad-patrascu <vladp@opensips.org>": "Vlad Patrascu <vladp@opensips.org>",
    "rvlad-patrascu <rvlad.patrascu@gmail.com>": "Vlad Patrascu <vladp@opensips.org>",
    "Vlad Pătrașcu <vladp@opensips.org>": "Vlad Patrascu <vladp@opensips.org>",
    "tallicamike <mtiganus@gmail.com>": "Mihai Tiganus <mtiganus@gmail.com>",
}

GITHUB_HANDLES = {
    "Agalya Ramachandran": "AgalyaR",
    "Alessio Garzi": "Ozzyboshi",
    "Alexandr Dubovikov": "adubovikov",
    "Alexey Vasilyev": "vasilevalex",
    "Andrei Datcu": "andrei-datcu",
    "Andrey Vorobiev": "andrey-vorobiev",
    "Andriy Pylypenko": "bambyster",
    "Aron Podrigal": "ar45",
    "Björn Esser": "besser82",
    "Bogdan-Andrei Iancu": "bogdan-iancu",
    "Callum Guy": "spacetourist",
    "Chad Attermann": "attermann",
    "Christophe Sollet": "csollet",
    "Damien Sandras": "dsandras",
    "Daniel-Constantin Mierla": "miconda",
    "Dan Pascu": "danpascu",
    "Dave Sidwell": "davesidwell",
    "Di-Shi Sun": "di-shi",
    "Dusan Klinec": "ph4r05",
    "Eric Tamme": "etamme",
    "Eseanu Marius Cristian": "eseanucristian",
    "Evandro Villaron": "evillaron",
    "Ezequiel Lovelle": "lovelle",
    "Fabian Gast": "fgast",
    "Federico Edorna": "fedorna",
    "Gohar Ahmed": "goharahmed",
    "Henning Westerholt": "henningw",
    "Ionel Cerghit": "ionel-cerghit",
    "Ionut Ionita": "ionutrazvanionita",
    "Italo Rossi": "italorossi",
    "jamesabravo": "jamesabravo",
    "Jan Janak": "janakj",
    "Jarrod Baumann": "jarrodb",
    "Jasper Hafkenscheid": "hafkensite",
    "Jeremy Martinez": "JeremyMartinez51",
    "Jiri Kuthan": "jiriatipteldotorg",
    "John Burke": "john08burke",
    "John Kiniston": "SB-JohnK",
    "Juha Heinanen": "juha-h",
    "Kobi Eshun": "ekobi",
    "Liviu Chircu": "liviuchircu",
    "Maksym Sobolyev": "sobomax",
    "Mihai Tiganus": "tallicamike",
    "Nick Altmann": "nikbyte",
    "Norman Brandinger": "NormB",
    "Oliver Mulelid-Tynes": "olivermt",
    "Oliver Severin Mulelid-Tynes": "olivermt",
    "Ovidiu Sas": "ovidiusas",
    "Parantido Julius De Rica": "Parantido",
    "Pasan Meemaduma": "pasanmdev",
    "Peter Lemenkov": "lemenkov",
    "Razvan Crainea": "razvancrainea",
    "Rob Gagnon": "rgagnon24",
    "Robison Tesini": "rtesini",
    "Ryan Bullock": "rrb3942",
    "Saúl Ibarra Corretgé": "saghul",
    "Sergey Khripchenko": "shripchenko",
    "Stefan Pologov": "sisoftrg",
    "Stéphane Alnet": "shimaore",
    "Victor Ciurel": "victor-ciurel",
    "Vlad Paiu": "vladpaiu",
    "Vlad Patrascu": "rvlad-patrascu",
    "Walter Doekes": "wdoekes",
    "Zero King": "l2dy",
}

# SHA → canonical author string
FIX_AUTHORS = {
    "0de42c5b2b9f35a983f59c925a10ccf08a544ca6": "Edson Gellert Schubert <4lists@gmail.com>",
    "7ef17c650772b635ede8bbb7ac061c49abce584a": "Edson Gellert Schubert <4lists@gmail.com>",
    "9394da66657f23d11bc35396bec4ae8e108a92ad": "UnixDev",
    "c8c8263bbce3449c6ed140e832eb4b971dc7be77": "Andreas Granig",
    "cd6142cb65c0104e49f27812ef14c1c89cf8cca7": "John Riordan",
    "7740840eec2be4c786537c905374f5568561b878": "Walter Doekes",
    "14a626b000d1788c5cb1649b12f708712d11d8d9": "Ancuta Onofrei <ancuta@voice-system.ro>",
    "c4c6ac5947eab0d9e5dec05529aefce3c61c3ff6": "Norman Brandinger",
    "e65227a9c8f3c8fac0564ae8d0bba71617e034e0": "Vallimamod Abdullah",
    "6097c7bba18be247cdf9c72327e6bb89c7751f59": "Walter Doekes",
    "4db2b711486eef5a330806095d11bb4f191ab9be": "Walter Doekes",
    "40f53d8f4043427258e5c2eb338739e3b43f139b": "Angel Marin",
    "fe1e5ce3e4113da6f6645419236dfef958edaeaa": "Stanislaw Pitucha",
    "401d799e64ec71f6774e3a70dde8d86aef667915": "Stanislaw Pitucha",
    "13637069128558a04d3bf70bfb28f045ce3a97c3": "Iouri Kharon <yjh@styx.cabel.net>",
    "42f9066ebf4b1c459be35b2597eda4a5937a8866": "Andreas Heise",
    "2b1f7934628e99db96be759dc81eb3b8204b2174": "Jeffrey Magder <jmagder@somanetworks.com>",
    "e0fe570fe75c78d0573aa5185ae8986dba0c91da": "Shlomi Gutman <shlomi@voicenter.com>",
    "5346d6f2118818f51512c777fb5ee7b089c8e2fb": "Phil D'Amore",
    "ee0221187d8f3d57b63e3cbd615c448a5a508667": "Marcus Hunger <hunger@sipgate.de>",
    "45e4b0bc8b1d4198f72859d02c3ccb5f9c2cadd2": "Marcus Hunger <hunger@sipgate.de>",
    "0ddde446698a62566fa94d9da74549f3acd5a9ae": "Juha Heinanen",
    "baa5e19b90931b3d84813e4c585c4361e9fd69ca": "Klaus Darilion",
    # aaa_radius
    "2296c4953ce85b9cffab3a74e2c98ce3186c96db": "Boris Ratner",
    "77cc5af653240f7b5b2355e100082434a5dcb2ed": "Boris Ratner",
    "46124d967074e981afa46a200c278529cdf731cb": "Matt Lehner",
    "5e138604958a7b8d5c0ccb01ed8a24010e338a39": "Авдиенко Михаил",
    "9870f06530ba72145733bace69f15f2e802c9a3c": "Alex Massover",
    # acc
    "77d77188b35de71c06e5cf3c4787166888e5ff80": "Ryan Bullock",
    "95dc05f3ba606f80ffc1b767b8e4d47ad667584b": "Ryan Bullock",
    "829eaa2e409a2398842f72fe40829ef8ba3f6939": "Alex Massover",
    "ce4ba967cbc5c186e63993ae51181b85517a1157": "Ovidiu Sas",
    "eb2854457a428b3de08142a8e7c8bf0825785c3b": "Ovidiu Sas",
    "bdb07d33492551a2893fc1d49d453c1658b2e04b": "Peter Nixon",
    # alias_db
    "7c308080e1c0f9edb07a19afde45534abd681b37": "Vladimir Romanov",
    # auth
    "26599d25cbc140373a5c24759dce688235e57589": "Anatoly Pidruchny",
    # auth_db
    "dbf3497f4d09a6b1158a536d6843f8402704fd6b": "Richard Revels",
    "13e9a5cbe14050e622a3ef65cd34b72260a74f01": "Kennard White",
    # sqlops / b2b / etc. (abbreviated for brevity — full list in build-contrib.sh)
    "37eba4b6d38f379a227040397c569f0d0fe99c9c": "Kennard White",
    "d129377f64f13e85ea0baf6d215092b4b4776f6e": "Norman Brandinger",
    "b9247c08af07662c6e712179dc57bcc5f16794aa": "Kobi Eshun",
    "bbbaaeca433fc5d03eca587d0a33f53d7720bec5": "Olle E. Johansson",
    "80eee1a046ea1da637a2c8b55d3aa22cb6f16d82": "Andrei Pelinescu-Onciul",
    "ec7b4e54bf7f09fb6ff56e8f8497563cf13719e8": "@DMOsipov",
    "cdd3c519fcbdadf351ab76bf2efbc75d35ba2803": "Ryan Bullock",
    "4135804ae488d8c574611298488540b5e868dd4d": "Nick Altmann",
    "65df3af5781c21ba8a41f23983e060badf7d9b48": "Stéphane Alnet",
    "ee8ca9e979e87506d6eb9260a26a7a2fee45e026": "Henk Hesselink",
    "5a3b6ac30c4b9dd68e3ebc5cbe83e31eb1175b77": "Nick Altmann",
    "1a45f19c7911bae211a83883874e6408842afceb": "Nick Altmann",
    "4822b9c83a7da4191eb9c67ae5e739598f2fbee8": "Nick Altmann",
    "28135f150c6d5268bf1d99ff6be68e9eb8f78e00": "Nick Altmann",
    "099adbe9f944afcd3cfc16ea1a470ea25e76860e": "Nick Altmann",
    "2c35387a83353a6d3e7a1cdc1ee1853c167e44b4": "Ovidiu Sas",
    "2e15877aab36ce18d71d06700dd7578c7831fa69": "Ovidiu Sas",
}

# version slug → git branch name
SLUG_TO_BRANCH = {
    'devel': 'master',
    '4-0':   '4.0',
    '3-6':   '3.6',
    '3-5':   '3.5',
    '3-4':   '3.4',
    '3-3':   '3.3',
}

# module → old_name (simplified; timestamp-based renames use tuple (old, since, until))
MOD_RENAMES = {
    "db_mysql":        "mysql",
    "db_postgres":     "postgres",
    "db_text":         "dbtext",
    "db_flatstore":    "flatstore",
    "db_unixodbc":     "unixodbc",
    "db_perlvdb":      "perlvdb",
    "cpl_c":           "cpl-c",
    "auth_aaa":        "auth_radius",
    "cachedb_local":   "localcache",
    "uac_registrant":  "registrant",
    "tracer":          "siptrace",
    "stir_shaken":     "stir",
    "event_stream":    "event_jsonrpc",
    "sqlops":          "dbops",
    "dbops":           "avpops",
    "event_rabbitmq":  "rabbitmq",
}


# ---------------------------------------------------------------------------
# Author normalisation
# ---------------------------------------------------------------------------

def _name_only(author: str) -> str:
    return re.sub(r'\s*<[^>]*>', '', author).strip()


def normalize_author(raw: str) -> str:
    """Apply aliases to a raw 'Name <email>' string."""
    raw = raw.strip()
    if raw in AUTHOR_ALIASES:
        return AUTHOR_ALIASES[raw]
    name = _name_only(raw)
    if name in AUTHOR_ALIASES:
        return AUTHOR_ALIASES[name]
    return raw


def format_author(author: str) -> str:
    """Return display name with optional GitHub link in Markdown."""
    name = _name_only(author)
    if name.startswith('@'):
        handle = name.lstrip('@')
        return f"[@{handle}](https://github.com/{handle})"
    handle = GITHUB_HANDLES.get(name)
    if handle:
        return f"{name} ([@{handle}](https://github.com/{handle}))"
    return name


# ---------------------------------------------------------------------------
# Git log parsing
# ---------------------------------------------------------------------------

_COMMIT_RE = re.compile(r'^COMMIT:([0-9a-f]{40}):([^:]+):(.*)$')
_NUMSTAT_RE = re.compile(r'^(\d+|-)\t(\d+|-)\t(.+)$')


def _git_log_for_path(path_glob: str, branch: str = 'master', extra_args: list[str] | None = None) -> list[dict]:
    """Return a list of commit dicts {sha, author, date, added, deleted} for path_glob."""
    cmd = [
        'git', 'log',
        branch,
        '--format=COMMIT:%H:%aI:%an <%ae>',
        '--numstat',
        *(extra_args or []),
        '--',
        path_glob,
    ]
    result = subprocess.run(cmd, cwd=OPENSIPS_DIR, capture_output=True, text=True, errors='replace')
    if result.returncode != 0:
        return []

    commits = []
    current: dict | None = None

    for line in result.stdout.splitlines():
        m = _COMMIT_RE.match(line)
        if m:
            if current:
                commits.append(current)
            sha, iso_date, raw_author = m.group(1), m.group(2), m.group(3)
            if sha in SKIP_COMMITS:
                current = None
                continue
            if sha in FIX_AUTHORS:
                raw_author = FIX_AUTHORS[sha]
            author = normalize_author(raw_author)
            try:
                date = datetime.fromisoformat(iso_date)
            except Exception:
                date = None
            current = {'sha': sha, 'author': author, 'added': 0, 'deleted': 0, 'date': date}
            continue

        if current is None:
            continue

        nm = _NUMSTAT_RE.match(line)
        if nm:
            a = int(nm.group(1)) if nm.group(1) != '-' else 0
            d = int(nm.group(2)) if nm.group(2) != '-' else 0
            filename = nm.group(3)
            # only count files in modules/ (ignore doc/ subpath for module stats)
            if not filename.startswith('modules/'):
                continue
            current['added']   += a
            current['deleted'] += d

    if current:
        commits.append(current)

    return [c for c in commits if c['added'] or c['deleted']]


def get_module_commits(module: str, branch: str = 'master') -> list[dict]:
    commits = _git_log_for_path(f'modules/{module}/', branch)
    old = MOD_RENAMES.get(module)
    if old:
        commits += _git_log_for_path(f'modules/{old}/', branch)
    return commits


def get_doc_commits(module: str, branch: str = 'master') -> list[dict]:
    commits = _git_log_for_path(f'modules/{module}/doc/', branch)
    old = MOD_RENAMES.get(module)
    if old:
        commits += _git_log_for_path(f'modules/{old}/doc/', branch)
    return commits


# ---------------------------------------------------------------------------
# Stats computation
# ---------------------------------------------------------------------------

def compute_stats(commits: list[dict]) -> dict:
    """Aggregate per-author stats."""
    stats: dict[str, dict] = {}
    for c in commits:
        a = c['author']
        if a not in stats:
            stats[a] = {'commits': 0, 'add': 0, 'del': 0, 'first': None, 'last': None}
        s = stats[a]
        s['commits'] += 1
        s['add']     += c['added']
        s['del']     += c['deleted']
        dt = c.get('date')
        if dt:
            if s['first'] is None or dt < s['first']:
                s['first'] = dt
            if s['last'] is None or dt > s['last']:
                s['last'] = dt
    return stats


def devscore(s: dict) -> float:
    add_rate = PROJ_LINES_ADD / PROJ_COMMITS
    del_rate = PROJ_LINES_DEL / PROJ_COMMITS
    return s['commits'] + math.ceil(s['add'] / add_rate) + math.ceil(s['del'] / del_rate)


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _fmt_date(dt: datetime | None) -> str:
    return dt.strftime('%b %Y') if dt else '?'


def generate_contributors_md(module: str, branch: str = 'master') -> str:
    commits     = get_module_commits(module, branch)
    doc_commits = get_doc_commits(module, branch)

    if not commits and not doc_commits:
        return ''

    stats = compute_stats(commits)

    # Sort by DevScore
    by_score = sorted(stats.items(), key=lambda x: (-devscore(x[1]), -x[1]['commits'], -x[1]['add']))
    # Sort by most recent activity
    by_activity = sorted(stats.items(), key=lambda x: (
        -(x[1]['last'].timestamp() if x[1]['last'] else 0)
    ))

    lines = [f'\n## Contributors {{#contributors}}\n']

    # --- Table 1: By Commit Statistics ---
    lines.append('\n### By Commit Statistics {#contrib_commit_statistics}\n')
    lines.append(
        '**Top contributors by DevScore^(1)^, authored commits^(2)^ '
        'and lines added/removed^(3)^**\n'
    )
    lines.append('| # | Name | DevScore | Commits | Lines++ | Lines-- |')
    lines.append('|---|---|---|---|---|---|')

    side = []
    for i, (author, s) in enumerate(by_score, 1):
        if i > TABLE_SIZE_COMMITS:
            side.append(format_author(author))
            continue
        lines.append(
            f'| {i}. | {format_author(author)} '
            f'| {devscore(s):.0f} | {s["commits"]} | {s["add"]} | {s["del"]} |'
        )

    if side:
        lines.append(f'\n**All remaining contributors**: {", ".join(side)}.\n')

    lines.append(
        '\n*(1) DevScore = author\\_commits + author\\_lines\\_added / '
        '(project\\_lines\\_added / project\\_commits) + author\\_lines\\_deleted / '
        '(project\\_lines\\_deleted / project\\_commits)*\n'
    )
    lines.append(
        '*(2) including any documentation-related commits, excluding merge commits*\n'
    )
    lines.append('*(3) ignoring whitespace edits, renamed files and auto-generated files*\n')

    # --- Table 2: By Commit Activity ---
    lines.append('\n### By Commit Activity {#contrib_commit_activity}\n')
    lines.append('| # | Name | Commit Activity |')
    lines.append('|---|---|---|')

    side = []
    for i, (author, s) in enumerate(by_activity, 1):
        if i > TABLE_SIZE_ACTIVITY:
            side.append(format_author(author))
            continue
        activity = f'{_fmt_date(s["first"])} - {_fmt_date(s["last"])}'
        lines.append(f'| {i}. | {format_author(author)} | {activity} |')

    if side:
        lines.append(f'\n**All remaining contributors**: {", ".join(side)}.\n')

    lines.append('\n*(1) including any documentation-related commits, excluding merge commits*\n')

    # --- Documentation section ---
    lines.append('\n## Documentation {#documentation}\n')
    lines.append('\n### Contributors {#documentation_contributors}\n')

    if doc_commits:
        doc_stats = compute_stats(doc_commits)
        doc_by_activity = sorted(
            doc_stats.items(),
            key=lambda x: -(x[1]['last'].timestamp() if x[1]['last'] else 0)
        )
        doc_authors = ', '.join(format_author(a) for a, _ in doc_by_activity)
        lines.append(f'**Last edited by:** {doc_authors}.\n')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------

def process_file(md_path: Path, module: str) -> bool:
    if not md_path.exists():
        return False

    content = md_path.read_text('utf-8')
    if PLACEHOLDER not in content:
        return True

    contrib = generate_contributors_md(module)
    if not contrib.strip():
        return True

    md_path.write_text(content.replace(PLACEHOLDER, contrib.strip()), 'utf-8')
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not OPENSIPS_DIR.is_dir():
        print(f'ERROR: {OPENSIPS_DIR} not found. Clone opensips repo first.', file=sys.stderr)
        sys.exit(1)

    if not MODULES_ROOT.exists():
        print('Run npm run generate:modules first.', file=sys.stderr)
        sys.exit(1)

    # Collect all (md_path, module_name, slug) pairs across all version dirs
    if sys.argv[1:]:
        pairs = [
            (version_dir / f'{module}.md', module, version_dir.name)
            for version_dir in sorted(MODULES_ROOT.iterdir()) if version_dir.is_dir()
            for module in sys.argv[1:]
        ]
    else:
        pairs = [
            (md_path, md_path.stem, version_dir.name)
            for version_dir in sorted(MODULES_ROOT.iterdir()) if version_dir.is_dir()
            for md_path in sorted(version_dir.glob('*.md'))
            if PLACEHOLDER in md_path.read_text('utf-8')
        ]

    total = len(pairs)
    print(f'Generating contributors for {total} files...')

    contrib_cache: dict[tuple, str] = {}
    ok = 0
    for i, (md_path, module, slug) in enumerate(pairs, 1):
        branch = SLUG_TO_BRANCH.get(slug, 'master')
        cached = (module, branch) in contrib_cache
        print(f'  [{i}/{total}] {slug}/{module}{"" if cached else " (git log...)"}', end='', flush=True)
        key = (module, branch)
        if key not in contrib_cache:
            contrib_cache[key] = generate_contributors_md(module, branch)
        contrib = contrib_cache[key]
        content = md_path.read_text('utf-8')
        if PLACEHOLDER in content and contrib.strip():
            md_path.write_text(content.replace(PLACEHOLDER, contrib.strip()), 'utf-8')
        ok += 1
        print(' ✓')

    print(f'Done ({ok}/{total}).')


if __name__ == '__main__':
    main()
