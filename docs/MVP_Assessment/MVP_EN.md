# Aiedio MVP Evaluation Report (English Version)

**Submission Deadline**：March 29, 2026

---

## 1. MVP Scope Determination

**Selected 2 core User Stories (US-4 decomposed into 4 Sub-Stories)**:

| US | Feature | Rationale |
| ---- | ------------------------------------------------- | ------------------------ |
| **US-1** | **Narrative Flow (Storyboard generation)** | **Core AI-driven creativity** |
| **US-4** | **One-Click Composition (Auto video pipeline)** | **Complete automation loop** |
| ↳ US-4.1 | Auto Data Acquisition (Crawler) | Scrapes trending topics as creative input |
| ↳ US-4.2 | Script Copywriting (Story Generation) | Distills trend data into video text structure |
| ↳ US-4.3 | AI Video Clip Generation (Video Gen API) | Calls model to produce visual footage |
| ↳ US-4.4 | Subtitle & Effects Compositing | Aligns audio/video timeline, delivers final MP4 |

**Excluded Rationale**: US-2 (Character continuity - future) / US-3 (Brand control - future) / US-5 (Latency optimization)

---

## 2. User Story Complexity

### US-1: Narrative Flow — 🔴 High

- **Sequential dependency**: 4-step LLM chain (Topic → Outline → Scenes → Shots)
  - Each step's output feeds the next — no parallelism
- **Quality control difficult**: Creative output is subjective
  - Hard to validate automatically, requires iterative Prompt tuning
- **Strict format constraint**: Output must be structured JSON
  - For downstream video generation
- **Video prompt alignment**: Scene descriptions must be precise enough
  - To produce coherent video clips via Video Gen API
  - Vague or inconsistent prompts lead to unusable output

### US-4: One-Click Composition (4 Sub-Stories) — 🟡 Medium (overall)

Modules are decoupled with clear interfaces and can be developed in parallel; complexity is in the orchestration layer.

#### US-4.1 Auto Data Acquisition — 🟢 Low
- Crawler logic is deterministic with well-defined interfaces
- No complex algorithms involved

#### US-4.2 Script Copywriting — 🟡 Medium
- Relies on LLM for stable information extraction
- Requires structured output to connect upstream and downstream

#### US-4.3 AI Video Clip Generation — 🔴 High
- Must handle network latency and Video Gen API rate limits
- Requires async request state management and retry logic

#### US-4.4 Subtitle & Effects Compositing — 🟡 Medium
- Relies on mature toolchain (MoviePy / FFmpeg)
- Requires precise multi-track timeline synchronization

---

## 3. User Story Importance

| US | Impact |
| --- | --- |
| US-1 | ⭐⭐⭐⭐⭐ |
| US-4.1 Auto Data Acquisition | ⭐⭐⭐⭐ |
| US-4.2 Script Copywriting | ⭐⭐⭐⭐⭐ |
| US-4.3 AI Video Clip Generation | ⭐⭐⭐⭐⭐ |
| US-4.4 Subtitle & Effects Compositing | ⭐⭐⭐⭐ |

---

## 4. MVP Completeness

Users can obtain a publish-ready short video through a complete automation loop: **Trend discovery (Crawler) → AI creativity (Storyboard) → Video generation → Automatic compositing**.

**Answer**: ✅ Complete

---

## 5. MVP Minimalism

| US   | Can Delete?                                         |
| ---- | --------------------------------------------------- |
| US-1 | ❌ No creativity = No AI value                      |
| US-4 | ❌ No crawler and compositing = No product delivery |

**Answer**: ✅ Minimal (Both 2 USs are essential)

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
