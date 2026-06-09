import { visit } from 'unist-util-visit';

// Map GitHub alert types → Starlight aside types. GitHub alerts (> [!NOTE] …)
// render natively on github.com (the fork manual) but Starlight ignores them;
// this turns them into Starlight asides so the website shows proper callouts.
const ALERT_TO_ASIDE = {
  NOTE: 'note',
  TIP: 'tip',
  IMPORTANT: 'caution',
  WARNING: 'danger',
  CAUTION: 'danger',
};

const ALERT_RE = /^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*\r?\n?/;

export default function remarkGithubAlerts() {
  return (tree) => {
    visit(tree, 'blockquote', (node) => {
      const firstPara = node.children?.[0];
      if (!firstPara || firstPara.type !== 'paragraph') return;
      const firstText = firstPara.children?.[0];
      if (!firstText || firstText.type !== 'text') return;

      const match = firstText.value.match(ALERT_RE);
      if (!match) return;

      const asideType = ALERT_TO_ASIDE[match[1]];

      // Strip the "[!TYPE]" marker (and trailing newline) from the leading text.
      firstText.value = firstText.value.slice(match[0].length);
      // Drop a now-empty leading text node so the paragraph doesn't start blank.
      if (firstText.value === '') firstPara.children.shift();
      // If the first paragraph is now empty, drop it entirely.
      if (firstPara.children.length === 0) node.children.shift();

      // Re-type the blockquote as a Starlight aside container directive; Starlight's
      // own remark plugin renders containerDirective nodes named note/tip/caution/danger.
      node.type = 'containerDirective';
      node.name = asideType;
      node.attributes = {};
      node.data = {};
    });
  };
}
