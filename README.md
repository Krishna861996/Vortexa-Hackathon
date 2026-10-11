# CodeQuest AI

## Gemini coding mentor

Add `GEMINI_API_KEY=your-key` and `GEMINI_MODEL=gemini-flash-latest` to `backend/.env`, then restart FastAPI. The mentor unlocks after all hints are revealed and answers only when the learner asks. The backend sends the challenge description, concept tags, question, and current code to Gemini; hidden tests are excluded. Responses are labeled Gemini mentor only when Gemini returns an answer. Missing keys, service errors, and quota limits use the local mentor fallback. Keep the key in the ignored backend environment file.

Beginner Python practice with a Next.js frontend, FastAPI backend, and Supabase
database. Learners browse challenges, run Python solutions, view per-test
feedback, and track their progress.

## Structure

```text
frontend/
  src/app/         Challenge library, practice page, and progress page
  src/components/  Shared navigation, states, and result cards
  src/lib/api.ts   Typed FastAPI client
backend/
  app/             API, Supabase repository, Docker runner client
  runner/          Locked-down Python runner image
  tests/           API, runner, and real-container tests
  .env.example     Environment variable template
  requirements.txt Pinned Python dependencies
supabase/
  schema.sql       Tables, access controls, demo learner, six challenges
```

## Setup

1. The schema and seed data have been applied to the existing **CodeQuest AI**
   Supabase project (`pdekyufwolupdqxlqibp`). For another project, run
   `supabase/schema.sql` in its **SQL Editor**. Rerunning it refreshes challenge
   content without deleting attempts.
2. For the local demo, copy `backend/.env.demo.example` to `backend/.env`
   (this workspace already has that local setting).
   The API serves the same six challenges from server-side seed data and saves
   hints and attempts in an ignored `backend/demo.sqlite3` file. To use Supabase
   instead, copy `backend/.env.example` to `backend/.env` and set `SUPABASE_URL`
   and `SUPABASE_SECRET_KEY` from the project's API settings. Use a server-side
   secret key or legacy service-role key. Never put this key in frontend code.
3. In a terminal, start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

   On macOS/Linux, activate with `source .venv/bin/activate` instead.
4. In a second terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000). The FastAPI reference
   is at [http://localhost:8000/docs](http://localhost:8000/docs). The frontend
   defaults to `http://localhost:8000` for API calls. For another backend URL,
   copy `frontend/.env.local.example` to `frontend/.env.local`, edit
   `NEXT_PUBLIC_API_BASE_URL`, and restart Next.js. The backend's `CORS_ORIGINS`
   must include the frontend origin.

   The challenge and progress pages show a connection error when FastAPI is
   stopped. The local demo mode lets you browse all six challenges without
   Supabase credentials.
5. The website's **Run code** button uses free Pyodide in the browser to run visible tests. No Docker or execution API key is needed. The first run downloads Pyodide, so an internet connection is required. Results and code are saved through `/practice-attempts` for progress and level unlocks. These are browser-reported practice results, not server-verified hidden-test results.

   The separate `/attempts` API uses Piston by default. To use it, set `PISTON_URL` to your hosted or self-hosted Piston instance. The public instance may require `PISTON_TOKEN`; leave it blank only if your instance permits anonymous requests.
   For the optional Docker runner, set `CODEQUEST_RUNNER=docker`, then install Docker and start a **Linux container** daemon.
   From the repository root, build the runner image:

   ```powershell
   docker build -t codequest-python-runner:local backend/runner
   docker info --format '{{.OSType}}'
   ```

   The second command must print `linux`. Keep this image on the host running
   the API. Until Docker and the image are available, the Docker submission API returns a setup
   error and saves no attempt; the API never executes submissions on the host.

Run tests from `backend/` with `python -m unittest discover -s tests -v`.
   The Docker integration test runs four real submissions after Docker and the
image are available; it is skipped when they are not. Unit tests still check
the API's fail-safe setup response and the four result categories.
Check the frontend from `frontend/` with `npm run typecheck` and `npm run build`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/challenges` | List challenge summaries |
| GET | `/api/challenges/{id}` | Get prompt, starter code, visible tests, and hint count |
| POST | `/api/challenges/{id}/hints/next` | Get the next hint for a learner |
| POST | `/api/challenges/{id}/attempts` | Grade code and save its result |
| POST | `/api/challenges/{id}/practice-attempts` | Save browser-reported visible-test practice results |
| GET | `/api/learners/{id}/progress` | Get attempts, solved count, and concepts |

The seeded learner ID is `demo-learner`. POST bodies:

```json
{"learner_id":"demo-learner"}
```

for the hint route, and:

```json
{"learner_id":"demo-learner","code":"def add_numbers(a, b):\n    return a + b"}
```

for the attempt route.

The browser practice route also requires `categories`, with one category per visible test. Stored results have `execution: "browser"`; server runner results have `execution: "server"`. Hidden test contents are never sent to the browser runner.

## Levels and celebrations

The path is **Beginner → Easy → Medium → Hard → Advanced**. Complete every challenge in earlier levels to unlock the next level. A completion requires all visible practice tests to pass in one saved attempt. Failed attempts do not unlock levels; previously saved passing attempts still count. Empty levels are skipped. The API enforces the same gate for practice submissions, server submissions, hints, and mentor requests.

The library shows lock icons and the requirement for each locked challenge. Successful practice displays a short blue-and-yellow confetti celebration and a link to the next available challenge. The Python logo gently floats inside a rotating orbit. Animations respect the device's reduced-motion setting.

Progress uses the shared `demo-learner` account and survives page reloads. Browser practice results are self-reported and suitable for this learning demo, not tamper-proof grading or certification.

Hidden tests reside in a separate database table, are queried only by the
backend, and are never returned in challenge details. Submission responses
report a category for each hidden test without its input, expected value, or
actual value. Categories are `passed`, `wrong output`, `runtime error`, and
`timeout`. Tables have RLS enabled and no `anon` or `authenticated` grants;
the backend alone uses the server key.

Each challenge has three server-side hints, revealed in order, one per request.
They become more specific without supplying finished code. After a failed
submission, the API returns `failure_explanation` and `feedback_source: "local"`.
This deterministic fallback uses only result categories and public concept
tags, so its advice is a likely next check rather than an AI diagnosis. No AI
feedback service is used for this automatic explanation; the optional Gemini mentor is requested separately. The challenge page offers a button back to the
editor after a hint or failed result, preserving the learner's code.

Progress is calculated from saved attempts, once per tagged concept per
submission. The progress page shows attempts, full passes, different passing
solutions, completed challenges, and the latest three result categories for
each concept. Its labels follow these rules:

- **Not started:** no attempts.
- **Practicing:** at least one attempt, before a sustained passing pattern.
- **Improving:** at least two attempts and a full pass on the latest attempt.
- **Demonstrated:** at least three attempts, two different passing solutions,
  and two passes among the latest three attempts.

Submitting the same code again does not add a different passing solution. When
the two latest attempts for a concept use different code and fail in the same
category, the API recommends the easiest unsolved challenge tagged with that
concept (or a solved one if needed) and states the evidence. The added **Sum a
list** challenge gives lists and loops a smaller practice option. Recommendations
do not reveal hidden test data.

When the Docker runner is selected, each server test launches a fresh Docker container. The API passes the submitted code,
function name, and one test input through stdin; the expected value remains in
the API process. The container uses no network, a read-only root filesystem, a
non-root user, dropped capabilities, Docker's built-in seccomp profile, no new
privileges, a small temporary filesystem, 128 MiB memory, half a CPU, 32 PIDs,
and a four-second wall-clock limit. User output and errors are discarded. The
API returns only sanitized result categories; Docker setup or start errors return HTTP 503 and
do not save an attempt. Do not expose the Docker daemon or its socket to users.

This is a demo learner with no sign-in or per-user access control; use it for
local learning and prototypes only.
