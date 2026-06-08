# Frontend Architecture

The ChargeHub frontend is a Single Page Application (SPA) built to provide a modern, sleek, and responsive interface for both standard residents and complex administrators.

## Core Technologies
- **React 18**: UI Library.
- **Vite**: Fast build tool and development server.
- **TypeScript**: For robust type safety across components and API responses.
- **React Router v6**: For client-side routing.
- **Lucide React**: For consistent, clean SVG iconography.
- **Recharts**: For rendering dynamic, real-time energy usage charts.

## Directory Structure
- `/src/api`: Contains Axios instances and API wrapper functions. Centralizes all backend communication (auth headers, error interceptors).
- `/src/components`: 
  - Shared UI components (Buttons, Modals, Cards, Inputs).
  - Designed following a dark-mode glassmorphic aesthetic.
- `/src/context`: React Context providers.
  - `AuthContext`: Manages the JWT token, user session, role (`admin` vs `resident`), and auto-logout logic.
- `/src/pages`: Top-level route components.
  - `Dashboard`: The main view for residents to see active sessions, start/stop charging, and view coin balance.
  - `AdminPanel`: Restricted view for admins to add/remove Plugs, view system-wide analytics, and credit user accounts.
  - `Login` / `Register`: Authentication flows.
- `index.css`: The global stylesheet. Contains CSS variables for theme colors, gradients, and utility classes. Tailwind is NOT used; custom CSS ensures exact control over the premium look.

## State Management
Global state is kept minimal. React Context (`AuthContext`) handles authentication state.
Data fetching (plugs, sessions, user balance) is largely done at the page level using `useEffect` hooks and local state (`useState`), passing data down to components via props. 
For real-time updates (like live wattage), the app may use periodic polling via `setInterval` or WebSockets/Server-Sent Events (SSE) if implemented in the backend.

## Design Philosophy
The UI prioritizes visual excellence.
- **Color Palette**: Curated dark modes with vibrant accent colors (e.g., neon blues/greens for "Active" states).
- **Glassmorphism**: Modals and cards often feature semi-transparent backgrounds with backdrop-blur to create a sense of depth.
- **Animations**: Subtle micro-animations on hover and active states encourage interaction.

## Building and Running
- `npm run dev`: Starts the Vite dev server with Hot Module Replacement (HMR).
- `npm run build`: Compiles TypeScript and builds the production-ready bundle into the `/dist` folder. The backend may be configured to serve these static files.
