## Question

I used a Prompt-to-app AI builder (e.g., Lovable, v0, Bolt, Replit AI, Claude Design) to create my front end, but when trying to containerize using vite with a backend I built separately, the build doesn't produce a static `index.html` for FastAPI to serve. How do I fix it?

## Answer

### The Issue
AI builders like Lovable, Bolt, and v0 generate a React app for you quickly based on a single prompt. However, to provide modern features, they frequently scaffold these projects using frameworks (like TanStack Start, Next.js, or Remix) with **Server-Side Rendering (SSR)** enabled by default. 

To simplify deployment, the course recommends building the frontend once into a set of static HTML, CSS, and JavaScript files so the FastAPI backend can serve them directly, eliminating the need for a separate frontend container. Because SSR relies on a live Node.js server, the build process skips creating a static `index.html` shell, which breaks this single-container deployment strategy.

### The Fix
There are two ways to handle this, depending on whether you are writing a new prompt or following up on one you already sent. Once the Dockerfile is correctly generated, you will need to lock in the decision using your project's context file.

**Option A: The Preemptive Prompt (Recommended)**
If you haven't generated the container yet, use this prompt to ensure your agent handles the SSR-to-SPA conversion automatically:

> "Inspect our frontend framework configuration (e.g., `vite.config.ts` or `next.config.js`). If it is currently configured for Server-Side Rendering (SSR), update it to export a static Single Page Application (SPA) instead. Once configured, create a multi-stage Dockerfile where Stage 1 builds the static frontend assets and Stage 2 builds a Python image where FastAPI serves those static files from the root path."

**Option B: The Conversational Route**
If you already used a general prompt that didn't explicitly mention SSR, your AI tool will handle the ambiguity based on its underlying design:
*   **Interactive behavior:** Some agents will analyze your codebase, realize the framework requires a live server, and pause to ask you how to proceed. If prompted with a choice, look for an option to **enable static/SPA export** (or similar).
*   **Direct-execution behavior:** Other agents will simply follow your general instructions to the letter and build the Dockerfile right away. If the container builds but the frontend doesn't load, you just need to guide the agent with a conversational follow-up: *"It looks like the frontend was scaffolded with SSR. Please update its configuration to export a static SPA, and adjust the Dockerfile so FastAPI serves those static files."*

**Final Step: Update your Context (`AGENTS.md`)**
Regardless of which option you used, you should stop the agent from accidentally reverting this setup in future sessions. Add this single rule to your `AGENTS.md` file:
* The frontend is a static SPA. Production builds must output static files to be served by FastAPI; do not introduce a Node.js server runtime.