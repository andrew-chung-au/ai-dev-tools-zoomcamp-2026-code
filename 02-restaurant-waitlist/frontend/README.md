# Welcome to your Lovable project

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Open your project in the [Lovable editor](https://lovable.dev) and keep building.

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: connect the project to GitHub and every change made in Lovable is committed straight to your repository.
- **Full ownership**: this code is yours. Push to your repository and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

## Built with

- TanStack Start
- TypeScript
- React
- Tailwind CSS

## Frontend prototype notes (Step 2)

- This is a **frontend-only prototype**. There is no backend, database, or authentication.
- All backend-shaped behaviour is mocked in `src/services/mockWaitlistService.ts` (in-memory, seeded, simulated async delays). React components only talk to the `WaitlistService` interface exported from `src/services/index.ts`.
- The service layer will later be replaced with a FastAPI client; the request/response types in `src/services/waitlistService.ts` are the basis for the future OpenAPI contract.
- Staff login is mocked: any non-empty credentials succeed and the session is held in memory only.
- **No real messages are sent.** Notifications are recorded as mock in-app events with a delivery status.
- **Real logo upload is deferred to the backend phase**; a neutral logo placeholder is used everywhere.

### Assumptions

- One venue, one service date; the ticket sequence is shared across party classes and resets per mock service date.
- Data lives in memory and resets on page reload.
- Seating is not strictly FIFO: staff pick any compatible available table.
- Guest status pages are reached with an opaque mock access token returned by the service.

## Configuration

Copy `.env.example` to `.env` if you need to override defaults:

```bash
cp .env.example .env
```

Key variables:

- `VITE_API_BASE_URL` — Backend API URL.  
  Default: `http://localhost:8091/api`

- `VITE_USE_MOCK_SERVICE` — If set to `true`, the frontend uses the in‑browser mock service instead of calling the backend.  
  Useful for frontend‑only development.  
  Tests always use the mock regardless of this setting.

### Tests

Run `bunx vitest run` — the suite covers guest submission and validation, large-party enquiries, ticket stability, cancellation, notification and return-by behaviour, table compatibility rules, and completion releasing a table.
