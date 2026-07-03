# Provenance Guard: Planning

## 1. Detection Signals

This system uses two distinct signals to classify submitted text as AI-generated or human-written.

**Signal 1: LLM-based classification (Groq, llama-3.3-70b-versatile)**

- Measures: holistic semantic and stylistic coherence. The model is prompted to assess whether the text reads as human or AI-generated based on overall reasoning style, tone, and phrasing patterns.
- Output format: a score between 0 and 1 representing the probability the text is AI-generated.
- Blind spot: can be fooled by lightly-edited AI output, or by very polished human writing that superficially resembles AI patterns.

**Signal 2: Stylometric heuristics (pure Python)**

- Measures: structural/statistical properties of the text, specifically sentence length variance, type-token ratio (vocabulary diversity), and punctuation density.
- Output format: the three metrics are combined into a single 0 to 1 "AI-likelihood" score for this signal.
- Blind spot: naturally uniform formal/technical human writing can score similarly to AI text. Short text samples do not give the metrics enough data to be reliable.

**Combining the signals:**
A weighted average is used to compute the final confidence score:

confidence = (0.6 _ signal_1_score) + (0.4 _ signal_2_score)

Signal 1 (LLM) is weighted more heavily since it captures holistic meaning, while Signal 2 (stylometrics) acts as a supporting, structural check.

## 2. Uncertainty Representation

The combined confidence score (0 to 1) is mapped to three categories. Thresholds are deliberately asymmetric: it takes stronger, more consistent evidence to reach "Likely AI-generated" than to reach "Likely human-written." This reflects the principle that a false positive (accusing a human of using AI) is worse than a false negative on a creative writing platform.

| Confidence score range | Category             |
| ---------------------- | -------------------- |
| 0.75 - 1.0             | Likely AI-generated  |
| 0.35 - 0.74            | Uncertain            |
| 0.0 - 0.34             | Likely human-written |

A score of 0.6, for example, means the signals show some indicators of AI-generated text, but not strongly or consistently enough to state that confidently. This lands in "Uncertain" rather than an accusation.

## 3. Transparency Label Design

**High-confidence AI (0.75 - 1.0):**
"This content shows strong indicators of AI generation based on our analysis. If you believe this is a mistake, you can appeal this classification."

**Uncertain (0.35 - 0.74):**
"Our system could not confidently determine whether this content was AI-generated or human-written. This result reflects genuine uncertainty in the analysis."

**High-confidence human (0.0 - 0.34):**
"This content shows strong indicators of human authorship based on our analysis."

## 4. Appeals Workflow

- Who can appeal: the original creator_id associated with the submission.
- What they provide: content_id and creator_reasoning (free-text explanation).
- What happens on appeal:
  1. System looks up the content by content_id.
  2. Updates that content's status to "under_review".
  3. Writes a new audit log entry capturing the appeal, including the original classification, the creator's reasoning, and a timestamp.
  4. Returns a confirmation response to the creator including the updated status.
- What a human reviewer would see: querying GET /log surfaces the original submission entry (signals, confidence, label) alongside the linked appeal entry (creator reasoning, under_review status), giving full context for a manual decision. No automated re-classification is implemented.

## 5. Anticipated Edge Cases

**Edge case 1: Formal academic or technical writing by a human.**
A human writer with a formal, technical style may naturally produce low sentence length variance and consistent vocabulary. The stylometric signal could score this as AI-like even though it is genuinely human, since it cannot distinguish "naturally uniform formal writing" from "AI-generated uniformity." The asymmetric thresholds are designed to route this into "Uncertain" rather than "Likely AI-generated."

**Edge case 2: Short, simple, repetitive creative writing (e.g., a children's poem or minimalist piece).**
Heavy repetition and simple vocabulary lower the type-token ratio, one of the stylometric AI-likelihood indicators, even though repetition is a deliberate literary device. Short samples also give the stylometric signal too little data to be reliable, making Signal 1 (Groq) the dominant factor by weight, which may or may not correct the result. This is a known limitation.

## Architecture

### Diagram

```
SUBMISSION FLOW:

  POST /submit
  { text, creator_id }
        |
        v
  +-------------------+
  | Signal 1: Groq LLM|  --> raw score (0-1)
  +-------------------+
        |
        v
  +-------------------------+
  | Signal 2: Stylometrics  |  --> raw score (0-1)
  +-------------------------+
        |
        v
  +---------------------------+
  | Confidence Scoring        |
  | (combines signal 1 + 2,   |
  |  asymmetric thresholds:   |
  |  harder to reach "AI")    |
  +---------------------------+
        |
        v
  +---------------------------+
  | Transparency Label        |
  | (maps confidence score to |
  |  label text)              |
  +---------------------------+
        |
        v
  +---------------------------+
  | Audit Log                 |
  | (writes content_id,       |
  |  signals, confidence,     |
  |  label, timestamp)        |
  +---------------------------+
        |
        v
  Response:
  { content_id, attribution,
    confidence, label }


APPEAL FLOW:

  POST /appeal
  { content_id, creator_reasoning }
        |
        v
  +---------------------------+
  | Status Update              |
  | (content status ->         |
  |  "under_review")           |
  +---------------------------+
        |
        v
  +---------------------------+
  | Audit Log                 |
  | (logs appeal alongside     |
  |  original decision)        |
  +---------------------------+
        |
        v
  Response:
  { confirmation, status }
```

### Narrative

A submitted text passes through the Groq LLM signal and the stylometric heuristics signal independently, each producing a 0 to 1 score. These are combined into a single weighted confidence score, which determines both the transparency label shown to the user and the attribution category. Every submission is written to the audit log. Appeals reference an existing content_id, update that content's status to "under_review," and are logged alongside the original decision so a reviewer has full context.

## AI Tool Plan

**M3 (submission endpoint + first signal):**

- Provide: Detection signals section (Signal 1) + architecture diagram
- Ask for: Flask app skeleton with POST /submit route stub, and the Groq signal function
- Verify: test the Groq function directly with a few sample texts and confirm it returns a 0-1 score before wiring it into the endpoint

**M4 (second signal + confidence scoring):**

- Provide: Detection signals section (Signal 2) + uncertainty representation section + diagram
- Ask for: stylometric heuristics function, and confidence scoring logic applying the 0.6/0.4 weighted average and threshold bands
- Verify: run the 4 test inputs from the spec (clearly AI, clearly human, 2 borderline) and confirm scores land in the expected ranges and match the threshold table

**M5 (production layer):**

- Provide: Transparency label section + appeals workflow section + diagram
- Ask for: label generation function mapping confidence to exact label text, and the POST /appeal endpoint
- Verify: test all three label variants are reachable by feeding different confidence scores, and confirm an appeal updates status to "under_review" and appears correctly in the audit log

## Stretch Feature Plan

**Analytics dashboard**: a GET /analytics endpoint that reads from the audit log and returns aggregated stats: counts by attribution category, appeal rate (appeals / total submissions), and average confidence score. Will be implemented after the core pipeline (Milestones 3-5) is complete and stable.
