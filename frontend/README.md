# DevLens frontend

React + TypeScript + Vite SPA for DevLens. See the [project README](../README.md) for
what DevLens does, the architecture, and how to run the whole stack.

## Development

```bash
npm install
npm run dev      # dev server on http://localhost:5173, proxies /analyze and /health to :8000
npm run lint      # oxlint
npm run build     # tsc -b && vite build
```

`vite.config.ts` proxies API calls to `http://localhost:8000` by default; set
`VITE_PROXY_TARGET` to point elsewhere (used by the root `docker-compose.yml` to reach the
`backend` service).
