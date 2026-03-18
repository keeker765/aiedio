# Aiedio MVP Evaluation Report (English Version)

**Submission Deadline**：March 29, 2026

---

## 1. MVP Scope Determination (5 pts)

**Selected 2 User Stories**:

| US   | Feature                                           | Rationale                |
| ---- | ------------------------------------------------- | ------------------------ |
| US-1 | Narrative Flow (Story board generation)           | Core AI auto-creativity  |
| US-4 | One-Click Composition (Crawler+Video+Compositing) | Complete automation loop |

**Excluded Rationale**: US-2 (Character continuity - future) / US-3 (Brand control - future) / US-5 (Latency optimization)

---

## 2. User Story Complexity (3 pts)

| US   | Complexity | Analysis |
| ---- | ---------- | -------- |
| US-1 | High       | LLM multi-step reasoning, Prompt engineering, creative quality control |
| US-4 | Medium     | Distributed tasks (Crawler + API calls + Video encoding + Subtitle generation) but relatively independent stages |

---

## 3. User Story Importance (2 pts)

| US   | Impact     |
| ---- | ---------- |
| US-1 | ⭐⭐⭐⭐⭐ |
| US-4 | ⭐⭐⭐⭐⭐ |

---

## 4. MVP Completeness (2 pts)

Users can obtain a publish-ready short video through a complete automation loop: **Trend discovery (Crawler) → AI creativity (Storyboard) → Video generation → Automatic compositing**.

**Answer**: ✅ Complete

---

## 5. MVP Minimalism (2 pts)

| US   | Can Delete?                                         |
| ---- | --------------------------------------------------- |
| US-1 | ❌ No creativity = No AI value                      |
| US-4 | ❌ No crawler and compositing = No product delivery |

**Answer**: ✅ Minimal (Both 2 USs are essential)

---

## 6. MVP Realism (2 pts)

**Can 5-person team complete it?**

**Timeline**:

- Week 1: Backend routing + Frontend framework + Engine Stub
- Week 2: US-1 story generation + Crawler foundation
- Week 3: US-4 video generation, music, subtitles, compositing
- Week 4: Testing, bug fixes, integration

**Workload Distribution**:

- Wu Ke (Core Engine): US-1 = 50 hours
- Lu Yi (Backend): Data flow, queues, storage = 25 hours
- Hu Yuxuan (Crawler): US-4 crawler part = 15 hours
- Liu/Li (Frontend): UI interface = 10 hours

**Total**: ~100 hours / 800 available = Reasonable workload

**Main Risks**:

- LLM multi-step reasoning quality → Multiple Prompt templates mitigation
- Seedance API rate limiting → Early communication with quota + Plan B

**Answer**: ✅ Achievable

---

## 7. KPI Definition

**KPI**: Total video playback ≥ 10,000 views

- 10 users generate 50 videos, upload to platforms, total 7-day playback ≥ 10,000
- **Why correlates with revenue**: High playback → User continuous usage → Revenue conversion
- **Validation**: 50 videos × 200 views/video = 10,000 views

---

**Submission Date**: March 29, 2026
