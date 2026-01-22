# 🛠️ Technical Status & Context Map

**Last Updated:** Jan 22, 2026 (UI Refactored & Functional)
**Current Branch:** `fix_rating_distribution`
**Status:** **FUNCTIONAL BUT SLOW**

---

## 🗺️ Critical File Map

### 1. Core Logic (Backend)
- **Ingest Engine:** `scout_app/core/ingest.py` (Stable)
- **Stats Engine:** `scout_app/core/stats_engine.py` (Stable)

### 2. User Interface (Refactored)
- **Orchestrator:** `scout_app/Market_Intelligence.py` (Fixed Imports)
- **Tabs:** `scout_app/ui/tabs/*.py` (Fixed Imports)
- **Helpers:** `scout_app/ui/common.py` (Fixed Imports)

---

## ⚠️ Known Issues
- **UI Latency:** Dashboard takes ~3-4 seconds to interactive state even with Pre-calc data.
    - *Suspects:* Streamlit Data Transfer overhead, Plotly rendering on client-side, or unoptimized re-runs.

---

## 📝 Session Log (Recent Actions)

1.  **Fixed Import Errors:** Switched all relative imports (`..`) to absolute imports (`scout_app.ui...`) to fix Docker runtime crashes.
2.  **Restarted Service:** `scout_ui` container restarted.
3.  **UI Status:** Online, functional, debug indicator shows "Pre-calculated", but UX is sluggish.

---

## ⏭️ Next Steps

1.  **Merge Branch:** Save this state as a milestone.
2.  **Performance Profiling:** Use `st.profiler` or simple timers to find the 3s bottleneck.
3.  **Social Scout AI:** Proceed to next feature after merge.
