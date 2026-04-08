# Aiedio MVP Evaluation Report (English Version)

**Submission Deadline**：March 29, 2026

---

## 1. MVP Scope Determination

### Full User Story Priority Ranking

All five user stories from the UX research document are evaluated below across **impact** and **4-week time constraint** before selecting the MVP scope.

| US       | Story Name                | User Role            | Description                                              | Impact | Priority                                             |
| -------- | ------------------------- | -------------------- | -------------------------------------------------------- | ------ | ---------------------------------------------------- |
| **US-1** | **Narrative Flow**        | Content Creator      | Generate a 4-scene storyboard from a one-sentence prompt | ⭐⭐⭐⭐⭐  | <span style="color:#d32f2f">**P0 — MVP Core**</span> |
| **US-4** | **One-Click Composition** | Small Business Owner | Auto-pipeline: trending data → script → video → MP4      | ⭐⭐⭐⭐⭐  | <span style="color:#d32f2f">**P0 — MVP Core**</span> |
| US-2     | Character Continuity      | Content Creator      | Maintain consistent character appearance across scenes   | ⭐⭐⭐⭐   | <span style="color:#e57c00">P1 — Post-MVP</span>     |
| US-5     | Efficiency                | Small Business Owner | Generate a 15-second video in under 5 minutes            | ⭐⭐⭐    | <span style="color:#e57c00">P1 — Post-MVP</span>     |
| US-3     | Style Lock-in             | Marketing Expert     | Lock brand color palettes and lighting style templates   | ⭐⭐⭐    | <span style="color:#2e7d32">P2 — Future</span>       |

> **Selection rationale for P0 stories is expanded in Chapter 3.**

---

**Selected 2 core User Stories (US-4 decomposed into 4 Sub-Stories)**:

| US       | Feature                                         | Rationale                                       |
| -------- | ----------------------------------------------- | ----------------------------------------------- |
| **US-1** | **Narrative Flow (Storyboard generation)**      | **Core AI-driven creativity**                   |
| **US-4** | **One-Click Composition (Auto video pipeline)** | **Complete automation loop**                    |
| ↳ US-4.1 | Auto Data Acquisition (Crawler)                 | Scrapes trending topics as creative input       |
| ↳ US-4.2 | Script Copywriting (Story Generation)           | Distills trend data into video text structure   |
| ↳ US-4.3 | AI Video Clip Generation (Video Gen API)        | Calls model to produce visual footage           |
| ↳ US-4.4 | Subtitle & Effects Compositing                  | Aligns audio/video timeline, delivers final MP4 |

**Excluded Rationale**: US-2 (Character continuity - future) / US-3 (Brand control - future) / US-5 (Latency optimization)

---

## 2. User Story Complexity

### US-1: Narrative Flow — <span style="color:#d32f2f">Complexity: High</span> | <span style="color:#d32f2f">Priority: P0</span>

- **Sequential dependency**: 4-step LLM chain (Topic → Outline → Scenes → Shots)
  - Each step's output feeds the next — no parallelism
- **Quality control difficult**: Creative output is subjective
  - Hard to validate automatically, requires iterative Prompt tuning
- **Strict format constraint**: Output must be structured JSON
  - For downstream video generation
- **Video prompt alignment**: Scene descriptions must be precise enough
  - To produce coherent video clips via Video Gen API
  - Vague or inconsistent prompts lead to unusable output

### US-4: One-Click Composition (4 Sub-Stories) — <span style="color:#e57c00">Complexity: Medium (overall)</span> | <span style="color:#d32f2f">Priority: P0</span>

Modules are decoupled with clear interfaces and can be developed in parallel; complexity is in the orchestration layer.

#### US-4.1 Auto Data Acquisition — <span style="color:#2e7d32">Complexity: Low</span> | Priority: P0

- Crawler logic is deterministic with well-defined interfaces
- No complex algorithms involved

#### US-4.2 Script Copywriting — <span style="color:#e57c00">Complexity: Medium</span> | Priority: P0

- Relies on LLM for stable information extraction
- Requires structured output to connect upstream and downstream

#### US-4.3 AI Video Clip Generation — <span style="color:#d32f2f">Complexity: High</span> | Priority: P0

- Must handle network latency and Video Gen API rate limits
- Requires async request state management and retry logic

#### US-4.4 Subtitle & Effects Compositing — <span style="color:#e57c00">Complexity: Medium</span> | Priority: P0

- Relies on mature toolchain (MoviePy / FFmpeg)
- Requires precise multi-track timeline synchronization

---

## 3. Selection Rationale & Sub-Story Decomposition

### Why US-1: Narrative Flow?

US-1 is the core AI differentiator of the entire product. All three user interviews identified "narrative incoherence" as the primary deal-breaker with existing tools. The gap between competitor platforms (random clip generators) and our product is precisely the LLM-driven storyboard pipeline: one sentence in → structured 4-scene JSON out.

Without US-1, the system has no creative intelligence. It would be reduced to a dumb video template tool. US-1 is therefore **non-negotiable for MVP**.

| Dimension        | Assessment                                                             |
| ---------------- | ---------------------------------------------------------------------- |
| User pain solved | "Lottery effect" (incoherent clips) — reported by all 3 interviewees   |
| Competitive edge | No existing tool provides an end-to-end LLM storyboard pipeline        |
| Dependency       | US-4.2 and US-4.3 cannot operate without US-1's structured JSON output |
| Impact           | ⭐⭐⭐⭐⭐                                                                  |

---

### Why US-4: One-Click Composition?

US-4 is the delivery mechanism that converts AI creativity (US-1) into a tangible, shareable artifact. Even the best storyboard is worthless if users still need Premiere Pro to assemble the final video. US-4 closes the automation loop from **trending topic to finished MP4** without manual editing.

Without US-4, the product cannot be demo'd or validated against the KPI (10,000 playback views). US-4 is therefore **essential for a complete MVP**.

| Dimension         | Assessment                                                                  |
| ----------------- | --------------------------------------------------------------------------- |
| User pain solved  | Manual assembly time (3–5 days for Li Jie, Mr. Wang)                        |
| Competitive edge  | No competitor provides a fully automated Story → Clip → Edit pipeline       |
| Dependency        | Wraps US-4.1 through US-4.4 into a single orchestrated flow                 |
| Impact            | ⭐⭐⭐⭐⭐                                                                    |

---

### US-4 Sub-Story Decomposition

US-4 is decomposed into 4 independently developable sub-stories, each owning one stage of the pipeline:

#### US-4.1 — Auto Data Acquisition (Crawler)

> *"As a user, I want the system to automatically fetch today's trending topics, so that I don't need to manually look up what's popular."*

- **Input**: Platform list (Zhihu, GitHub)
- **Output**: `hot_trends.json` — list of `{platform, title, hot_value}` objects
- **Complexity**: <span style="color:#2e7d32">Low</span> — deterministic scraping logic, no ML required
- **Dependency**: Provides the raw input for US-4.2

#### US-4.2 — Script Copywriting (Story Generation)

> *"As a user, I want the system to turn a trending topic into a structured video script, so that the narrative is ready for clip generation."*

- **Input**: Single trend object from US-4.1
- **Output**: 4-scene storyboard JSON `{scene_id, visual, narration, style}`
- **Complexity**: <span style="color:#e57c00">Medium</span> — LLM prompt engineering, structured output validation
- **Dependency**: Requires US-4.1 output; feeds directly into US-4.3

#### US-4.3 — AI Video Clip Generation (Video Gen API)

> *"As a user, I want each storyboard scene to be rendered as a short AI video clip, so that I have raw footage for the final assembly."*

- **Input**: Scene description JSON from US-4.2
- **Output**: Per-scene `.mp4` clips downloaded to `core_engine/output/`
- **Complexity**: <span style="color:#d32f2f">High</span> — async API calls, polling, rate-limit retry, error handling
- **Dependency**: Requires US-4.2 output; feeds into US-4.4

#### US-4.4 — Subtitle & Effects Compositing

> *"As a user, I want all clips assembled with subtitles and background music into a single output file, so that I can download a publish-ready video."*

- **Input**: Per-scene clips from US-4.3 + narration text
- **Output**: Final `output.mp4` with multi-track timeline (video + subtitle + BGM)
- **Complexity**: <span style="color:#e57c00">Medium</span> — MoviePy/FFmpeg timeline sync, subtitle rendering
- **Dependency**: Final stage; delivers the KPI-measurable artifact

---

## 4. MVP Completeness

Users can obtain a publish-ready short video through a complete automation loop: **Trend discovery (Crawler) → AI creativity (Storyboard) → Video generation → Automatic compositing**.

**Answer**: ✅ Complete

---

## 5. MVP Minimalism

| US                                    | Can Delete?                                  |
| ------------------------------------- | -------------------------------------------- |
| US-1                                  | ❌ No creativity = No AI value               |
| US-4.1 Auto Data Acquisition          | ❌ No data source = No content input         |
| US-4.2 Script Copywriting             | ❌ No script = Cannot drive video generation |
| US-4.3 AI Video Clip Generation       | ❌ No video = No product core                |
| US-4.4 Subtitle & Effects Compositing | ❌ No compositing = No deliverable output    |

**Answer**: ✅ Minimal (US-1 and every US-4 sub-story are all essential)

---

## 6. MVP Realism

**Can 5-person team complete it?**

**Timeline**:

- Week 1: Backend routing + Frontend framework + Engine Stub
- Week 2: US-1 story generation + Crawler foundation
- Week 3: US-4 video generation, music, subtitles, compositing
- Week 4: Testing, bug fixes, integration

**Workload Distribution**:

- Wu Ke (Core Engine): US-1 story generation = 25 hours
- Lu Yi (Backend): Data flow, queues, API routes = 20 hours
- Hu Yuxuan (Crawler): US-4 crawler + data pipeline = 20 hours
- Liu Shuaizhen (Frontend Interaction): State management, API integration, business logic = 20 hours
- Li Xinying (Frontend UI/UX): Component styling, responsive layout, motion effects = 15 hours

**Total**: ~100 hours / 800 available = Reasonable workload

**Main Risks**:

- LLM multi-step reasoning quality → Multiple Prompt templates mitigation
- Video Gen API rate limiting → Early communication with quota + Plan B

**Answer**: ✅ Achievable

---

## 7. KPI Definition

**KPI**: Total video playback ≥ 10,000 views

- 10 users generate 50 videos, upload to platforms, total 7-day playback ≥ 10,000
- **Why correlates with revenue**: High playback → User continuous usage → Revenue conversion
- **Validation**: 50 videos × 200 views/video = 10,000 views

---

## 8. Implementation Tools (Technology Stack)

| Layer             | Tool                     | Purpose                                           |
| ----------------- | ------------------------ | ------------------------------------------------- |
| Backend           | FastAPI (Python 3.10+)   | REST API, task queue, data flow                   |
| Frontend          | React / Vue              | User interface, video preview, dashboard          |
| AI/LLM            | LangChain + LLM API      | Multi-step reasoning chain, storyboard generation |
| Video Generation  | Video Gen API            | AI video clip generation                          |
| Video Compositing | MoviePy + FFmpeg         | Editing, transitions, subtitles, BGM, MP4 export  |
| Crawler           | Requests + BeautifulSoup | Hot topic collection (Zhihu/GitHub etc.)          |
| Version Control   | Git + GitHub             | Team collaboration, code management               |

---

**Submission Date**: March 29, 2026
