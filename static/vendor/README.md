# Pinned chart dependency

- Chart.js version: 4.4.1
- Upstream: https://github.com/chartjs/Chart.js/tree/v4.4.1
- Download source: https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js
- License: MIT; full upstream text is in `Chart.js-LICENSE.md`.
- Local filename: `chart.umd.min.js` (upstream UMD distribution).

The library is served by Flask's static route. Users' uploaded CSVs are sent
only to this application's analysis endpoint, not to the CDN. The browser
does not need a CDN connection to draw charts after the application's assets
have loaded. This is an upstream dependency, not project-authored code.