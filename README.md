# Provenance Guard

Backend system that classifies submitted creative content as AI-generated or human-written, scores confidence, surfaces transparency labels, and handles creator appeals.

This README is updated as each milestone is completed. Sections marked "To be completed" will be filled in during later milestones.

## Project Structure

```
ai201-project4-provenance-guard/
├── app.py                # Flask app: routes and app setup (Milestone 3+)
├── signals/
│   ├── llm_signal.py     # Signal 1: Groq LLM classification (Milestone 3)
│   └── stylometry.py     # Signal 2: stylometric heuristics (Milestone 4)
├── scoring.py             # Confidence scoring logic (Milestone 4)
├── labels.py              # Transparency label generation (Milestone 5)
├── audit_log.py           # Structured audit logging (Milestone 3+)
├── analytics.py            # Stretch feature: analytics dashboard (post-Milestone 5)
├── planning.md             # Architecture, spec, and AI tool plan
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── .env                    # GROQ_API_KEY (not committed)
├── .gitignore
└── .venv/                  # Virtual environment (not committed)
```

Note: file names above reflect the planned structure from `planning.md` and may be adjusted slightly during implementation.

## Setup

1. Clone the repo and create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the repo root:
   ```
   GROQ_API_KEY=your_key_here
   ```
4. Run the app (once available):
   ```
   python app.py
   ```

## API Endpoints

| Endpoint     | Method | Purpose                                                  |
| ------------ | ------ | -------------------------------------------------------- |
| `/submit`    | POST   | Submit text for attribution analysis                     |
| `/appeal`    | POST   | Contest a classification                                 |
| `/log`       | GET    | View structured audit log entries                        |
| `/analytics` | GET    | View aggregated detection/appeal stats (stretch feature) |

## Detection Signals

**Signal 1: LLM-based classification (Groq)** — implemented and working.

- Sends submitted text to `llama-3.3-70b-versatile` with a structured prompt asking for an `ai_probability` score between 0 and 1.
- Tested independently on clearly-AI and clearly-human sample text before integration: clearly-AI text scored 0.8, clearly-human text scored 0.2, confirming meaningful separation.
- Falls back to a neutral 0.5 score if the model output cannot be parsed as JSON, rather than crashing the endpoint.
- Known blind spot, confirmed in testing: can be fooled by lightly-edited AI text. A lightly-edited AI sample scored 0.2 (read as human), pulling the overall confidence down to "likely_human" for that case. See Known Limitations.

**Signal 2: Stylometric heuristics (pure Python)** — implemented and working.

- Combines three metrics into a single 0-1 score: sentence length variance, type-token ratio (vocabulary diversity), and punctuation density.
- Normalization constants were calibrated against real measured values from test samples (not guessed), since initial constants compressed all scores into a narrow, low range.
- Known blind spot: type-token ratio is a weak signal on short text (under ~30 words), since vocabulary diversity naturally stays high regardless of authorship at that length. It only becomes a reliable signal on longer passages.

## Confidence Scoring

Combined confidence = (0.6 × Signal 1 score) + (0.4 × Signal 2 score), mapped to three bands: 0.75-1.0 (likely_ai), 0.35-0.74 (uncertain), 0.0-0.34 (likely_human). Thresholds are intentionally asymmetric, it takes more evidence to reach "likely_ai" than "likely_human", to avoid false accusations against human creators.

Tested against 4 inputs spanning the confidence range:

| Input                                | Signal 1 | Signal 2 | Confidence | Attribution  |
| ------------------------------------ | -------- | -------- | ---------- | ------------ |
| Clearly AI-generated                 | 0.8      | 0.343    | 0.617      | uncertain    |
| Clearly human-written                | 0.2      | 0.131    | 0.172      | likely_human |
| Borderline: formal human writing     | 0.8      | 0.281    | 0.592      | uncertain    |
| Borderline: lightly edited AI output | 0.2      | 0.489    | 0.316      | likely_human |

Notably, even the clearest AI-generated sample lands in "uncertain" rather than "likely_ai," a deliberate consequence of the asymmetric thresholds: the system would rather flag genuine uncertainty than confidently accuse. The formal human writing case correctly avoided a false "likely_ai" label, showing the asymmetric design working as intended.

## Transparency Labels

Three label variants, implemented and confirmed reachable via the `/submit` endpoint:

**High-confidence AI (confidence 0.75 - 1.0):**

> "This content shows strong indicators of AI generation based on our analysis. If you believe this is a mistake, you can appeal this classification."

**Uncertain (confidence 0.35 - 0.74):**

> "Our system could not confidently determine whether this content was AI-generated or human-written. This result reflects genuine uncertainty in the analysis."

**High-confidence human (confidence 0.0 - 0.34):**

> "This content shows strong indicators of human authorship based on our analysis."

## Appeals Workflow

`POST /appeal` accepts `content_id` and `creator_reasoning`. On a valid appeal:

1. The original submission is looked up by `content_id`.
2. Its status is updated to `"under_review"`.
3. The appeal reasoning and an appeal timestamp are added to that same audit log entry, alongside the original classification data.
4. A confirmation response is returned to the creator.

Example, tested end-to-end:

```json
{
  "content_id": "39ef7897-5d6c-4b6f-93e8-c3165d7e66d4",
  "creator_id": "test-edited-ai",
  "timestamp": "2026-07-04T21:09:56.655Z",
  "attribution": "likely_human",
  "confidence": 0.316,
  "signal_1_score": 0.2,
  "signal_2_score": 0.489,
  "status": "under_review",
  "appeal_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical.",
  "appeal_timestamp": "2026-07-04T21:14:27.106Z"
}
```

Automated re-classification is not implemented; a human reviewer would use this log entry (original decision + appeal reasoning) to make a manual call.

## Rate Limiting

`POST /submit` is limited to **10 requests per minute** and **100 requests per day** per client, using Flask-Limiter with in-memory storage.

Reasoning: a legitimate writer submitting drafts or revisions is very unlikely to exceed 10 submissions in a single minute, and 100 per day comfortably covers even a very active user across a full day. The per-minute limit is the main defense against automated flooding (rapid repeated requests), while the per-day limit is a backstop against sustained abuse.

Tested by firing 12 rapid requests in a row:

```
200
200
200
200
200
200
200
200
200
200
429
429
```

The first 10 succeeded, the 11th and 12th were correctly rejected with `429 Too Many Requests`.

## Audit Log

Every submission and appeal writes a structured JSON entry to `audit_log.json`, containing: `content_id`, `creator_id`, `timestamp`, `attribution`, `confidence`, `signal_1_score`, `signal_2_score`, `status`, and (when applicable) `appeal_reasoning` and `appeal_timestamp`.

Sample entries from testing:

```json
{
  "attribution": "uncertain",
  "confidence": 0.617,
  "content_id": "ad453bcd-6209-4bf9-ad83-51e70a7cff02",
  "creator_id": "test-ai",
  "signal_1_score": 0.8,
  "signal_2_score": 0.343,
  "status": "classified",
  "timestamp": "2026-07-04T21:09:13.772Z"
}
```

```json
{
  "attribution": "uncertain",
  "confidence": 0.592,
  "content_id": "2a695f20-75b5-424f-bc31-f8cb5a05611e",
  "creator_id": "test-formal-human",
  "signal_1_score": 0.8,
  "signal_2_score": 0.281,
  "status": "classified",
  "timestamp": "2026-07-04T20:52:59.863Z"
}
```

```json
{
  "attribution": "likely_human",
  "confidence": 0.316,
  "content_id": "39ef7897-5d6c-4b6f-93e8-c3165d7e66d4",
  "creator_id": "test-edited-ai",
  "signal_1_score": 0.2,
  "signal_2_score": 0.489,
  "status": "under_review",
  "appeal_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical.",
  "appeal_timestamp": "2026-07-04T21:14:27.106Z",
  "timestamp": "2026-07-04T21:09:56.655Z"
}
```

## Known Limitations

**Signal 1 can be fooled by lightly-edited AI text.** During Milestone 4 testing, a lightly-edited AI-generated sample (natural-sounding sentence starters, informal tone) was scored 0.2 by the Groq signal, holistically reading it as human-written. This pulled the combined confidence down to "likely_human" even though the text was AI-generated. This is a structural limitation of asking an LLM to holistically judge tone and phrasing: it can be misled by surface-level informality regardless of underlying origin.

**Signal 2's type-token ratio metric is unreliable on short text.** On passages under roughly 30 words, vocabulary diversity naturally stays high (0.86-0.90 in our testing) regardless of who wrote it, since there's little opportunity for repetition either way. This metric only becomes a meaningful discriminator on longer text samples.

## Spec Reflection

_To be completed in Milestone 6._

## AI Usage

_To be completed in Milestone 6._

## Stretch Features

**Analytics dashboard** (planned): aggregated view of detection patterns, appeal rate, and average confidence score. See `planning.md` for design.

## Progress Log

- ✅ Getting Started: repo created, environment set up, dependencies installed
- ✅ Milestone 1: architecture defined, detection signals chosen, API surface sketched, diagram drawn
- ✅ Milestone 2: planning.md written with all five spec questions, architecture section, and AI tool plan
- ✅ Milestone 3: Flask app built, POST /submit endpoint working with real Signal 1 (Groq), structured audit log writing on every submission, GET /log endpoint returning entries
- ✅ Milestone 4: Signal 2 (stylometric heuristics) implemented and calibrated, combined confidence scoring wired in, tested against 4 inputs spanning the confidence range
- ✅ Milestone 5: transparency labels wired in and all 3 variants confirmed reachable, appeals workflow built and tested end-to-end, rate limiting implemented and verified (10/minute, 100/day), audit log confirmed complete with sample entries
- ⬜ Milestone 6: documentation and walkthrough
