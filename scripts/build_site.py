"""Build site/index.html: a standalone copy of the dashboard that runs on any static host.

dashboard/index.html is the source of a Claude Dashboard artifact. It expects the host to
supply a `dash` runtime, a d3 global and the design tokens it styles against, so on an
ordinary static host (Netlify, Pages, S3) it renders as unstyled text with no data. This
script wraps that same page, copied verbatim, in everything it is missing:

  * a document skeleton (doctype, charset, viewport, title)
  * the design tokens it references, in light and dark
  * d3 v7 from a CDN
  * the three datasets, inlined from data/*.csv
  * a small `dash` shim implementing data(), calc() and draw()

The artifact page stays the single source of truth: nothing in it is edited, so a change
there flows into the site on the next build.

Usage: python3 scripts/build_site.py
"""

import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'dashboard', 'index.html')
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(ROOT, 'site', 'index.html')

DATASETS = ['indicators', 'trend', 'targets']

# d3 v7, pinned. The page uses d3.format, d3.group, d3.create, d3.extent,
# d3.scaleLinear, d3.line and d3.axisBottom.
D3 = 'https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js'

TOKENS = """<style>
  /* The design tokens the artifact host normally supplies. The page references these
     but does not define them; only its own --cmh-* status colours are its own. */
  :root {
    --font-anthropic-sans: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    --font-anthropic-serif: ui-serif, Georgia, "Times New Roman", Times, serif;

    --cds-radius: 8px;
    --cds-pad-xs: 6px;
    --cds-pad-sm: 10px;
    --cds-pad-lg: 20px;
    --cds-gap-xs: 4px;
    --cds-gap-sm: 8px;
    --cds-gap-md: 12px;
    --cds-gap-xl: 24px;
    --cds-font-size-caption: 0.75rem;
    --cds-font-size-body: 0.9375rem;
    --cds-font-size-heading: 1.0625rem;
    --cds-font-size-title: 1.5rem;
    --cds-font-weight-medium: 500;
    --cds-dur-slow: 0.4s;

    --cmh-page: #faf9f7;
    --color-fg: #1f1e1c;
    --color-fg-muted: #6e6b64;
    --color-panel: #ffffff;
    --color-border-line: #e6e3dc;
    --color-bad: #c0392b;
    --cds-border: #e6e3dc;
    --cds-text-secondary: #6e6b64;
    --cds-surface-popover: #ffffff;
    --cds-shadow-popover: 0 2px 8px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.04);
    --cds-chart-axis: #8d8a83;
    --cds-chart-grid: #ece9e2;
    --cds-chart-muted: #b4b0a8;
    --cds-chart-reference: #8d8a83;
  }

  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --cmh-page: #1c1b17;
      --color-fg: #edeae3;
      --color-fg-muted: #a5a19a;
      --color-panel: #26251f;
      --color-border-line: #3a3832;
      --color-bad: #e06c5c;
      --cds-border: #3a3832;
      --cds-text-secondary: #a5a19a;
      --cds-surface-popover: #2f2e27;
      --cds-shadow-popover: 0 2px 10px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06);
      --cds-chart-axis: #8f8b83;
      --cds-chart-grid: #3a3832;
      --cds-chart-muted: #6d6a63;
      --cds-chart-reference: #9a968e;
    }
  }

  :root[data-theme="dark"] {
    --cmh-page: #1c1b17;
    --color-fg: #edeae3;
    --color-fg-muted: #a5a19a;
    --color-panel: #26251f;
    --color-border-line: #3a3832;
    --color-bad: #e06c5c;
    --cds-border: #3a3832;
    --cds-text-secondary: #a5a19a;
    --cds-surface-popover: #2f2e27;
    --cds-shadow-popover: 0 2px 10px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06);
    --cds-chart-axis: #8f8b83;
    --cds-chart-grid: #3a3832;
    --cds-chart-muted: #6d6a63;
    --cds-chart-reference: #9a968e;
  }

  html { -webkit-text-size-adjust: 100%; }
  body {
    margin: 0;
    padding: 24px 16px 48px;
    background: var(--cmh-page);
    color: var(--color-fg);
    font-family: var(--font-anthropic-sans);
    font-size: var(--cds-font-size-body);
    line-height: 1.5;
  }
  .cmh-page { max-width: 1040px; margin: 0 auto; }
</style>"""

# A flat tile in the "above average" green, so the page does not request a favicon
# that no static host would have.
# A flat tile in the "above average" green, so the page does not request a favicon
# that no static host would have. Percent-encoded: a raw '<' in a data URI inside an
# attribute is not reliably accepted.
FAVICON = (
    '<link rel="icon" href="data:image/svg+xml,'
    '%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E'
    '%3Crect width=%2716%27 height=%2716%27 rx=%273%27 fill=%27%231C7A58%27/%3E'
    '%3C/svg%3E">'
)

SHIM = """<script>
// A stand-in for the artifact host's `dash` runtime, covering the three calls the page
// makes. Datasets come from the inlined CSV above; derived datasets are evaluated lazily
// and memoised, so a calc that depends on another resolves without ordering rules.
window.dash = (() => {
  const loaded = new Map();
  const calcs = new Map();
  const derived = new Map();
  const draws = [];

  document.querySelectorAll('script[type="text/csv"][data-dataset]').forEach((node) => {
    const id = node.dataset.dataset;
    try {
      loaded.set(id, {status: 'ok', data: d3.csvParse(node.textContent.trim())});
    } catch (err) {
      console.error('dataset failed to parse:', id, err);
      loaded.set(id, {status: 'error', data: []});
    }
  });

  const data = (id) => {
    if (loaded.has(id)) return loaded.get(id);
    if (derived.has(id)) return derived.get(id);
    const spec = calcs.get(id);
    if (!spec) return {status: 'error', data: []};
    let result;
    try {
      const args = (spec.inputs || []).map((name) => {
        const got = data(name);
        if (got.status !== 'ok') throw new Error('input not available: ' + name);
        return got.data;
      });
      result = {status: 'ok', data: spec.fn.apply(null, args)};
    } catch (err) {
      console.error('calc failed:', id, err);
      result = {status: 'error', data: []};
    }
    derived.set(id, result);
    return result;
  };

  // The page registers every calc before any draw, then expects the host to paint. Draws
  // are queued and flushed once the page's own script has finished running.
  const flush = () => draws.forEach(([name, fn]) => {
    document.querySelectorAll('[data-draw="' + name + '"]').forEach((el) => {
      try { fn(el); } catch (err) { console.error('draw failed:', name, err); }
    });
  });
  // Draws size their charts from el.clientWidth, so they must run after the first
  // layout, not merely after parsing: on DOMContentLoaded the width still reads 0 and
  // the charts fall back to a guessed width.
  // 'load' fires after the first layout, so widths are real by then. It is used in
  // preference to requestAnimationFrame, which never fires in a background tab and
  // would leave the page blank until it was looked at.
  if (document.readyState === 'complete') flush();
  else window.addEventListener('load', flush);

  return {
    data: data,
    calc: (id, spec) => calcs.set(id, spec),
    draw: (name, fn) => draws.push([name, fn])
  };
})();
</script>"""


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def main():
    page = read(PAGE)

    # The page's inline script is the only <script> in it; everything the script needs
    # has to be in place before it runs.
    anchor = '<script>'
    if page.count(anchor) != 1:
        raise SystemExit('expected exactly one <script> in the page, found %d' % page.count(anchor))

    blocks = []
    for name in DATASETS:
        csv = read(os.path.join(DATA, name + '.csv')).strip()
        if '</script' in csv.lower():
            raise SystemExit('refusing to inline %s: it contains a closing script tag' % name)
        blocks.append(
            '<script type="text/csv" data-dataset="%s">\n%s\n</script>' % (name, csv)
        )

    prelude = '\n'.join([
        '<script src="%s" crossorigin="anonymous" referrerpolicy="no-referrer"></script>' % D3,
        '\n'.join(blocks),
        SHIM,
        '',
    ])

    body = page.replace(anchor, prelude + anchor, 1)

    out = '\n'.join([
        '<!doctype html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>CIHI Quality Dashboard</title>',
        FAVICON,
        '<meta name="description" content="CIHI quality indicators for Cambridge Memorial Hospital, with the hospital\'s QIP targets alongside them.">',
        TOKENS,
        '</head>',
        '<body>',
        body,
        '</body>',
        '</html>',
        '',
    ])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(out)
    print('wrote', OUT, len(out), 'bytes')


if __name__ == '__main__':
    main()
