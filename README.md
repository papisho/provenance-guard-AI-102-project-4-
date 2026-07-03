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

_To be completed in Milestone 3 and 4 with implementation details, sample outputs, and reasoning._

Planned signals (see `planning.md` for full reasoning):

- Signal 1: LLM-based classification (Groq)
- Signal 2: Stylometric heuristics (sentence length variance, type-token ratio, punctuation density)

## Confidence Scoring

_To be completed in Milestone 4 with example submissions showing score variation._

## Transparency Labels

_To be completed in Milestone 5._

Planned label variants (see `planning.md`):

- High-confidence AI
- Uncertain
- High-confidence human

## Appeals Workflow

_To be completed in Milestone 5._

## Rate Limiting

_To be completed in Milestone 5 with chosen limits and reasoning._

## Audit Log

_To be completed in Milestone 5 with sample entries._

## Known Limitations

_To be completed in Milestone 6._

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
- ⬜ Milestone 3: submission endpoint + first signal
- ⬜ Milestone 4: second signal + confidence scoring
- ⬜ Milestone 5: production layer (labels, appeals, rate limiting, audit log)
- ⬜ Milestone 6: documentation and walkthrough
