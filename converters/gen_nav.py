#!/usr/bin/env python3
"""Generate a Starlight sidebar config from the converted MDX test-output directory.

Usage:
    python3 converters/gen_nav.py converters/test-output > src/sidebar.mjs
"""

import sys
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Version ordering
# ---------------------------------------------------------------------------

VERSIONS = [
    "4-1", "4-0",
    "3-6", "3-5", "3-4", "3-3", "3-2", "3-1", "3-0",
    "2-4", "2-3", "2-2", "2-1",
    "1-11", "1-10", "1-9", "1-8", "1-7", "1-6", "1-5", "1-4",
]

def version_label(v: str) -> str:
    return v.replace("-", ".")


# ---------------------------------------------------------------------------
# Topic patterns per version section
# ---------------------------------------------------------------------------

def slug(group: str, page: str) -> str:
    if page == "index":
        return group
    return f"{group}/{page}"


def make_item(label: str, s: str) -> dict:
    return {"label": label, "slug": s}


def make_group(label: str, items: list, collapsed: bool = True) -> dict:
    return {"label": label, "items": items, "collapsed": collapsed}


def versioned_page(group: str, base: str, v: str, existing: set) -> dict | None:
    page = f"{base}-{v}"
    if page in existing:
        label = base_label(base)
        return make_item(label, slug(group, page))
    return None


BASE_LABELS = {
    "install-download": "Download",
    "install-compileandinstall": "Compile & Install",
    "install-dbdeployment": "Database Deployment",
    "install-dbschema": "Database Schema",
    "configure-file": "Config File",
    "configure-rc": "RC Files",
    "generating-configs": "Generating Configs",
    "templating-config-files": "Templating Configs",
    "script-syntax": "Script Syntax",
    "script-coreparameters": "Core Parameters",
    "script-routes": "Routes",
    "script-operators": "Operators",
    "script-statements": "Statements",
    "script-corefunctions": "Core Functions",
    "script-corevar": "Core Variables",
    "script-flags": "Flags",
    "script-tran": "Transformations",
    "script-async": "Async Statements",
    "script-format": "Script Format",
    "modules": "Modules",
    "function-index": "Function Index",
    "interface-mi": "MI Interface",
    "interface-coremi": "Core MI Commands",
    "interface-events": "Event Interface",
    "interface-coreevents": "Core Events",
    "interface-statistics": "Statistics Interface",
    "interface-corestatistics": "Core Statistics",
    "interface-statusreport": "Status/Report Interface",
    "interface-binary": "Binary Interface",
    "development-manual": "Overview",
    "development-manual-arch": "Architecture",
    "development-manual-mm": "Memory Manager",
    "development-manual-module-dev": "Module Development",
    "development-manual-inline": "Inline Development",
    "development-manual-api-bin": "API: Binary",
    "development-manual-api-evi": "API: Event Interface",
    "development-manual-api-ipc": "API: IPC",
    "development-manual-api-locking": "API: Locking",
    "development-manual-api-lumps": "API: Lumps",
    "development-manual-api-mi": "API: MI",
    "development-manual-api-nosql": "API: NoSQL",
    "development-manual-api-script-func": "API: Script Functions",
    "development-manual-api-sip-parser": "API: SIP Parser",
    "development-manual-api-sql": "API: SQL",
    "development-manual-api-statistics": "API: Statistics",
    "development-manual-api-timer": "API: Timer",
    "development-manual-api-transformations": "API: Transformations",
    "development-manual-modapi-clusterer": "ModAPI: Clusterer",
    "development-manual-modapi-dialog": "ModAPI: Dialog",
    "development-manual-modapi-freeswitch": "ModAPI: FreeSWITCH",
    "development-manual-modapi-presence": "ModAPI: Presence",
    "development-manual-modapi-rr": "ModAPI: RR",
    "development-manual-modapi-tm": "ModAPI: TM",
    "development-manual-modapi-usrloc": "ModAPI: Usrloc",
    "conformance-tests": "Conformance Tests",
    "features": "Features",
    "tutorials-b2bua": "B2BUA",
    "tutorials-compression": "Compression",
    "tutorials-emergency": "Emergency Services",
    "tutorials-frauddetection": "Fraud Detection",
    "tutorials-siprec": "SIPREC Recording",
    "tutorials-tls": "TLS",
    "tutorials-websocket": "WebSocket",
}

def base_label(base: str) -> str:
    return BASE_LABELS.get(base, base.replace("-", " ").title())


def build_version_section(group: str, v: str, existing: set) -> dict | None:
    def vp(base: str) -> dict | None:
        return versioned_page(group, base, v, existing)

    def collect(*bases) -> list:
        return [x for b in bases if (x := vp(b))]

    install = collect(
        "install-download", "install-compileandinstall",
        "install-dbdeployment", "install-dbschema",
    )
    configure = collect(
        "configure-file", "configure-rc",
        "generating-configs", "templating-config-files",
    )
    scripting = collect(
        "script-syntax", "script-format",
        "script-coreparameters", "script-routes",
        "script-operators", "script-statements",
        "script-corefunctions", "script-corevar",
        "script-flags", "script-tran", "script-async",
    )
    modules = collect("modules", "function-index")
    interfaces = collect(
        "interface-mi", "interface-coremi",
        "interface-events", "interface-coreevents",
        "interface-statistics", "interface-corestatistics",
        "interface-statusreport", "interface-binary",
    )

    dev_core = collect(
        "development-manual", "development-manual-arch",
        "development-manual-mm", "development-manual-module-dev",
        "development-manual-inline",
    )
    dev_apis = collect(
        "development-manual-api-bin", "development-manual-api-evi",
        "development-manual-api-ipc", "development-manual-api-locking",
        "development-manual-api-lumps", "development-manual-api-mi",
        "development-manual-api-nosql", "development-manual-api-script-func",
        "development-manual-api-sip-parser", "development-manual-api-sql",
        "development-manual-api-statistics", "development-manual-api-timer",
        "development-manual-api-transformations",
    )
    dev_modapis = collect(
        "development-manual-modapi-clusterer", "development-manual-modapi-dialog",
        "development-manual-modapi-freeswitch", "development-manual-modapi-presence",
        "development-manual-modapi-rr", "development-manual-modapi-tm",
        "development-manual-modapi-usrloc",
    )
    dev_items = dev_core
    if dev_apis:
        dev_items = dev_items + [make_group("Core APIs", dev_apis)]
    if dev_modapis:
        dev_items = dev_items + [make_group("Module APIs", dev_modapis)]

    tutorials_versioned = collect(
        "tutorials-tls", "tutorials-websocket", "tutorials-b2bua",
        "tutorials-emergency", "tutorials-frauddetection",
        "tutorials-siprec", "tutorials-compression",
    )
    misc = collect("conformance-tests", "features")

    # Migration page: pattern is migration-X-to-Y-Z-W-V (one page per version)
    migration = [
        make_item("Migration Guide", slug(group, p))
        for p in existing
        if re.match(rf'migration-.*-to-{re.escape(v)}-0$', p)
        or re.match(rf'migration-.*-{re.escape(v)}-0$', p)
    ]

    # Main manual index page
    manual_page = vp("manual")

    # Build sub-items
    sub_items: list = []
    if manual_page:
        sub_items.append(manual_page)
    if install:
        sub_items.append(make_group("Installation", install, collapsed=True))
    if configure:
        sub_items.append(make_group("Configuration", configure, collapsed=True))
    if scripting:
        sub_items.append(make_group("Scripting", scripting, collapsed=True))
    if modules:
        sub_items.append(make_group("Modules", modules, collapsed=True))
    if interfaces:
        sub_items.append(make_group("Interfaces", interfaces, collapsed=True))
    if dev_items:
        sub_items.append(make_group("Development Manual", dev_items, collapsed=True))
    if tutorials_versioned:
        sub_items.append(make_group("Tutorials", tutorials_versioned, collapsed=True))
    if misc:
        sub_items += misc
    if migration:
        sub_items += migration

    if not sub_items:
        return None

    return make_group(f"OpenSIPS {version_label(v)}", sub_items, collapsed=True)


# ---------------------------------------------------------------------------
# Non-versioned tutorial pages
# ---------------------------------------------------------------------------

TUTORIAL_STATICS = [
    ("Getting Started", "tutorials-gettingstarted"),
    ("Getting Started (2)", "tutorials-gettingstarted2"),
    ("Getting Started (centos)", "tutorials-installoncentos"),
    ("Getting Started (Red Hat)", "tutorials-opensipsonredhat"),
    ("TLS", "tutorials-tls"),
    ("WebSocket", "tutorials-websocket"),
    ("B2BUA", "tutorials-b2bua"),
    ("B2BUA Config Example", "tutorials-b2buaconfigexample"),
    ("B2BUA Provisional Media", "tutorials-b2buaprovisionalmedia"),
    ("Load Balancing", "tutorials-loadbalancing"),
    ("SIPREC Recording", "tutorials-siprec"),
    ("Emergency Services", "tutorials-emergency"),
    ("Fraud Detection", "tutorials-frauddetection"),
    ("Fail2Ban", "tutorials-fail2ban"),
    ("Radius Auth", "tutorials-radius"),
    ("Redirect", "tutorials-redirect"),
    ("Topology Hiding", "tutorials-topology-hiding"),
    ("Tracing", "tutorials-tracing"),
    ("Memory Caching", "tutorials-memorycaching"),
    ("Mid Registrar", "tutorials-midregistrar"),
    ("Key-Value Interface", "tutorials-keyvalueinterface"),
    ("Concurrent Calls Limit", "tutorials-concurrentcallslimitation"),
    ("Accounting", "tutorials-accounting"),
    ("Advanced Accounting", "tutorials-advanced-accounting"),
    ("Asterisk Integration", "tutorials-opensipsasteriskintegration"),
    ("FreeSWITCH Integration", "tutorials-opensipsfreeswitchintegration"),
    ("Distributed User Location (Federation)", "tutorials-distributed-user-location-federation"),
    ("Distributed User Location (Full Sharing)", "tutorials-distributed-user-location-full-sharing"),
    ("RCS Capabilities", "tutorials-rcs-managing-capabilities"),
    ("RLS", "tutorials-rls"),
    ("RLS Config", "tutorials-rlsconfig"),
    ("Diameter AAA", "tutorials-diameter-aaa"),
    ("Diameter Client/Server", "tutorials-diameter-client-server"),
    ("Cross-Compile", "tutorials-crosscompile"),
    ("Compression", "tutorials-compression"),
    ("PUA Extensions", "tutorials-puaextensions"),
    ("MSRP Chat", "msrp-chat"),
    ("MSRP Relay", "msrp-relay"),
    ("Presence Server", "tutorials-presence"),
    ("Presence: Simple Config", "tutorials-presence-simplepresconfig"),
    ("Presence: Server Setup", "tutorials-presence-presenceserver"),
    ("Presence: Module", "tutorials-presence-presencemodule"),
    ("Presence: Aux Modules", "tutorials-presence-presenceauxmodules"),
    ("Presence: PUA BLA Config", "tutorials-presence-puablaconfig"),
    ("Presence: PUA Dialoginfo", "tutorials-presence-puadialoinfoconfig"),
    ("Presence: PUA XMPP", "tutorials-presence-puaxmppconfig"),
    ("Presence: PUA Usrloc", "tutorials-presence-puausrlocconfig"),
    ("Presence: XCAP Client", "tutorials-presence-xcapclient"),
    ("Presence: OpenXCAP", "tutorials-presence-openxcappresconfig"),
    ("Sangoma Voice Transcoding", "tutorials-sangomavoicetranscoding"),
    ("Script Helper", "tutorials-scripthelper"),
    ("Event Interface", "tutorials-eventinterface"),
    ("WebSocket", "tutorials-websocket"),
]

DEV_SESSION_LABELS = [
    "Devel Session 01: Intro",
    "Devel Session 02: SIP Routing",
    "Devel Session 03: Dialog",
    "Devel Session 04: Registrar",
    "Devel Session 05: B2BUA",
    "Devel Session 06: IVR/Media",
    "Devel Session 07: Scripting",
]


# ---------------------------------------------------------------------------
# JS serialiser
# ---------------------------------------------------------------------------

def js_value(v, indent=0) -> str:
    pad = "  " * indent
    inner = "  " * (indent + 1)
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, dict):
        lines = ["{"]
        for k, val in v.items():
            lines.append(f"{inner}{k}: {js_value(val, indent + 1)},")
        lines.append(pad + "}")
        return "\n".join(lines)
    if isinstance(v, list):
        if not v:
            return "[]"
        lines = ["["]
        for item in v:
            lines.append(f"{inner}{js_value(item, indent + 1)},")
        lines.append(pad + "]")
        return "\n".join(lines)
    return repr(v)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("converters/test-output")

    doc_dir = root / "documentation"
    existing_doc = {p.stem for p in doc_dir.glob("*.mdx")} if doc_dir.exists() else set()

    sidebar: list = []

    # --- Documentation by version ---
    doc_sections = []
    for v in VERSIONS:
        section = build_version_section("documentation", v, existing_doc)
        if section:
            doc_sections.append(section)

    # --- Non-versioned reference pages ---
    reference_statics = []
    for label, page in [
        ("Troubleshooting", "troubleshooting"),
        ("Crash Analysis", "troubleshooting-crash"),
        ("Startup Issues", "troubleshooting-doesnotstart"),
        ("Performance", "troubleshooting-findperfpb"),
        ("Increase Memory", "troubleshooting-increasemem"),
        ("Out of Memory", "troubleshooting-outofmem"),
        ("Tips & FAQ", "tipsfaq"),
        ("Tools", "tools"),
        ("Non-SIP Trace Samples", "trace-nonsip-samples"),
        ("Webinars", "webinars"),
    ]:
        if page in existing_doc:
            reference_statics.append(make_item(label, slug("documentation", page)))

    # --- Non-versioned tutorials ---
    tutorial_statics = []
    for label, page in TUTORIAL_STATICS:
        group_prefix = "documentation" if page not in {"msrp-chat", "msrp-relay"} else "documentation"
        if page in existing_doc:
            tutorial_statics.append(make_item(label, slug("documentation", page)))

    # --- Dev sessions ---
    dev_sessions = []
    for i, label in enumerate(DEV_SESSION_LABELS, 1):
        page = f"tutorials-develsession{i:02d}"
        if page in existing_doc:
            dev_sessions.append(make_item(label, slug("documentation", page)))

    sidebar.append({
        "label": "Documentation",
        "items": doc_sections,
    })

    if tutorial_statics or dev_sessions:
        tut_items = tutorial_statics
        if dev_sessions:
            tut_items = tut_items + [make_group("Developer Sessions", dev_sessions, collapsed=True)]
        sidebar.append(make_group("Tutorials", tut_items, collapsed=True))

    if reference_statics:
        sidebar.append(make_group("Reference", reference_statics, collapsed=True))

    # --- Other groups ---
    about_dir = root / "about"
    about_pages = sorted(p.stem for p in about_dir.glob("*.mdx")) if about_dir.exists() else []
    about_items = []
    for page in about_pages:
        if re.match(r'^news\d+$', page):
            continue  # too many news items, skip
        about_items.append(make_item(page.replace("-", " ").title(), slug("about", page)))
    if about_items:
        sidebar.append(make_group("About", about_items, collapsed=True))

    community_dir = root / "community"
    if community_dir.exists():
        community_items = []
        summit_items = []
        irc_items = []
        event_items = []
        for p in sorted(community_dir.glob("*.mdx")):
            name = p.stem
            label = name.replace("-", " ").title()
            if "summit" in name.lower():
                summit_items.append(make_item(label, slug("community", name)))
            elif "ircmeeting" in name.lower():
                irc_items.append(make_item(label, slug("community", name)))
            elif name.startswith("event-"):
                event_items.append(make_item(label, slug("community", name)))
            elif name == "recentchanges":
                continue
            else:
                community_items.append(make_item(label, slug("community", name)))
        full = community_items
        if event_items:
            full = full + [make_group("Events", event_items, collapsed=True)]
        if summit_items:
            full = full + [make_group("Summits", summit_items, collapsed=True)]
        if irc_items:
            full = full + [make_group("IRC Meetings", irc_items, collapsed=True)]
        if full:
            sidebar.append(make_group("Community", full, collapsed=True))

    dev_dir = root / "development"
    if dev_dir.exists():
        dev_items = []
        plan_items = []
        for p in sorted(dev_dir.glob("*.mdx")):
            name = p.stem
            if "planning" in name or "development-plan" in name:
                plan_items.append(make_item(name.replace("-", " ").title(), slug("development", name)))
            elif name == "recentchanges":
                continue
            else:
                dev_items.append(make_item(name.replace("-", " ").title(), slug("development", name)))
        full = dev_items
        if plan_items:
            full = full + [make_group("Version Planning", plan_items, collapsed=True)]
        if full:
            sidebar.append(make_group("Development", full, collapsed=True))

    support_dir = root / "support"
    if support_dir.exists():
        sup_items = [
            make_item(p.stem.replace("-", " ").title(), slug("support", p.stem))
            for p in sorted(support_dir.glob("*.mdx"))
            if p.stem != "recentchanges"
        ]
        if sup_items:
            sidebar.append(make_group("Support", sup_items, collapsed=True))

    training_dir = root / "training"
    if training_dir.exists():
        tr_items = [
            make_item(p.stem.replace("-", " ").title(), slug("training", p.stem))
            for p in sorted(training_dir.glob("*.mdx"))
            if p.stem != "recentchanges"
        ]
        if tr_items:
            sidebar.append(make_group("Training", tr_items, collapsed=True))

    print("// AUTO-GENERATED by converters/gen_nav.py — do not edit by hand")
    print("// Run: python3 converters/gen_nav.py converters/test-output > src/sidebar.mjs")
    print()
    print(f"export const sidebar = {js_value(sidebar, 0)};")


if __name__ == "__main__":
    main()
