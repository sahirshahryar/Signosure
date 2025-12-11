# Signosure Web UI

The web frontend for Signosure, built with SvelteKit.

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Start dev server and open in browser
npm run dev -- --open
```

## Building

```bash
npm run build
npm run preview  # Preview the production build
```

## Configuration

Set the backend API URL via environment variable:

```bash
CORE_API_URL=http://localhost:8000
```

## Authentication

The web UI communicates with the FastAPI core service through SvelteKit server routes, which proxy requests to the backend. This architecture allows pages to be served even when the backend is unavailable.

### To-do

- [ ] `/auth`: User management
  - [ ] `/verify`: Email verification
  - [ ] `/forgot`: Password reset request
  - [ ] `/reset`: Password reset page
- [ ] `/datasets`: Dataset management
  - [ ] `/new`: Create new 
  - [ ] `/edit`: Edit existing
  - [ ] `/prompts`: Prompt management
    - [ ] `/new`
    - [ ] `/edit`
- [ ] `/collection`: Collection management
- [ ] `/annotation`: Data annotation
- [ ] `/visualization`: Data visualizations
- [ ] `/processing`: Data processing
- [ ] `/users`: User management
