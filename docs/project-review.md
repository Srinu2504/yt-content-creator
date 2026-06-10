# YT Content Creator — Project Review

**Generated:** 2026-06-09  
**Scope:** config, database, downloader, transcriber, content_engine, exporter, 02_history, main, requirements.txt, railway.toml, nixpacks.toml

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | 2 |
| High | 4 |
| Medium | 8 |
| Low | 6 |

**Syntax errors:** None (all Python files pass `py_compile`)  
**Import errors:** None when `PYTHONPATH` points to project root  
**Missing package in requirements.txt:** `pydub`  
**ffmpeg in nixpacks.toml:** Yes  
**PYTHONPATH in start commands:** Correct for Railway (`/app`)

---

## 1. app/core/config.py

| Line | Type | Issue |
|------|------|-------|
| 8 | Logic | `int(os.getenv("MAX_VIDEO_DURATION_MINUTES", "60"))` raises `ValueError` if env var is non-numeric |
| 8–10 | Hardcoded | Defaults (`60`, `whisper-large-v3-turbo`, `llama-3.3-70b-versatile`) are fine as fallbacks; already overridable via env |
| — | Missing env | `YOUTUBE_COOKIES` used in `downloader.py` but not documented/loaded here (read directly from `os.environ` in downloader) |

**Imports:** OK (`os`, `dotenv`)  
**Syntax:** OK

---

## 2. app/core/database.py

| Line | Type | Issue |
|------|------|-------|
| 37–45 | Logic | `save_video()` always generates a **new UUID** with `INSERT OR REPLACE`. Re-saving the same `youtube_url` replaces the video row with a new `id`, orphaning `generated_content` rows tied to the old id (no `ON DELETE CASCADE`) |
| 75–82 | Logic | `get_content_for_video()` builds `{row["format"]: dict(row) for row in rows}`. With `ORDER BY created_at DESC`, duplicate formats mean the **oldest** entry wins (last row in iteration overwrites newer ones) |
| 28 | Logic | `REFERENCES videos(id)` has no `ON DELETE CASCADE`; `delete_video()` manually cleans up — OK, but orphans possible via `save_video` replace |

**Imports:** OK  
**Syntax:** OK  
**Missing calls:** None

---

## 3. app/core/downloader.py

| Line | Type | Issue |
|------|------|-------|
| 46–48, 86 | Hardcoded | `socket_timeout=30`, `retries=3`, `extractor_retries=3` could be env vars |
| 50–55 | Hardcoded | Chrome User-Agent string hardcoded |
| 74, 86 | Logic | `info.get("duration", 0)` — if YouTube returns `duration: null`, `.get("duration", 0)` returns `None`, causing `TypeError` on division at line 86 |
| 84 | Logic | `get_video_info()` called inside `download_audio()` — cookies temp file created/destroyed twice per full download |
| 137–141 | Logic | Error message says *"upload fresh cookies.txt in the sidebar"* but **no sidebar cookie upload exists** in `app/main.py` — only `YOUTUBE_COOKIES` env var |
| 117–120 | Runtime | `FFmpegExtractAudio` postprocessor requires **ffmpeg** on PATH — satisfied by `nixpacks.toml` on Railway, must be installed locally for dev |
| 132–133 | Logic | If download succeeds but ffmpeg fails to produce `.mp3`, loop continues silently until all formats exhausted |

**Imports:** OK (`yt_dlp`, `tempfile`, config)  
**Syntax:** OK

---

## 4. app/core/transcriber.py

| Line | Type | Issue |
|------|------|-------|
| 3, 11 | Logic | `GROQ_API_KEY` imported at module load from `config.py`. If key is only set via Railway at runtime (not in `.env`), works. If key were set in Streamlit session only, transcriber would not see it (sidebar no longer sets `os.environ`) |
| 19–20 | Hardcoded | 24 MB chunk threshold hardcoded |
| 44 | Hardcoded | 10-minute chunk size hardcoded |
| 39–41 | Missing dep | `pydub` imported optionally — **not listed in `requirements.txt`** |
| 43 | Runtime | `AudioSegment.from_mp3()` requires **ffmpeg** for many inputs |
| 54 | Logic | Recursive `transcribe_audio(chunk_path)` on chunks under 24 MB — OK; chunk export at 64k keeps chunks small |

**Imports:** OK (groq, config; pydub lazy)  
**Syntax:** OK

---

## 5. app/core/content_engine.py

| Line | Type | Issue |
|------|------|-------|
| 3, 19 | Logic | Same import-time `GROQ_API_KEY` binding as transcriber |
| 31 | Hardcoded | `temperature=0.7` not configurable via env |
| 38–43 | Hardcoded | Truncation limits (`12000`, `14000` chars) and `max_tokens` per function hardcoded |
| 10–15 | Runtime | Prompt files must exist in `prompts/` — all four present ✓ |

**Imports:** OK  
**Syntax:** OK  
**Missing references:** None

---

## 6. app/exporters/exporter.py

| Line | Type | Issue |
|------|------|-------|
| 14 | Unused import | `TA_JUSTIFY` imported but never used |
| 52 | Unused import | `Pt` imported but never used |
| 37–44 | Logic | PDF heading/body text not fully XML-escaped (only plain lines escaped at line 43); `&` in headings could break ReportLab |
| 73–74 | Logic | `doc.save(buf)` — need `buf.seek(0)` before `getvalue()` in some python-docx versions; current pattern usually works |

**Imports:** OK (reportlab, docx lazy)  
**Syntax:** OK

---

## 7. app/pages/02_history.py

| Line | Type | Issue |
|------|------|-------|
| 7 | Logic | `st.set_page_config()` after `init_db()` — Streamlit requires `set_page_config` as first `st.*` call; `init_db()` is fine before it, but if `init_db` ever calls Streamlit it would break |
| 22 | Logic | `vid['duration_sec']//60` — `TypeError` if `duration_sec` is `None` |
| 22–27 | UX | Nested `st.expander` inside `st.expander` — Streamlit may warn or behave inconsistently |
| 57–71 | Runtime | No try/except around `export_pdf`/`export_docx` (unlike `main.py`) — export failures crash the page |

**Imports:** OK — all referenced symbols exist  
**Syntax:** OK

---

## 8. app/main.py

| Line | Type | Issue |
|------|------|-------|
| 3–11 | Imports | All core module imports resolve correctly ✓ |
| 38–44 | Logic | `api-badge` CSS class used but custom CSS was removed — badge renders unstyled |
| 51–55 | Logic | `hero-badge` / `transcript-box` classes have no CSS — cosmetic only |
| 88–89 | Logic | Checks `os.environ.get("GROQ_API_KEY", GROQ_API_KEY)` but `transcriber`/`content_engine` use config module constant loaded at import — consistent if key is in `.env` or Railway vars at startup |
| 135–142 | Logic | `status` referenced in `except` blocks inside `else` branch only — OK structurally |
| 147–149 | Security | Transcript injected into HTML via `unsafe_allow_html=True` without escaping — XSS risk if transcript contains `<script>` etc. |
| 198–235 | Logic | On `GenerationError`, `continue` skips rest of loop — OK. If generation fails, no partial UI for that format |
| 234–235 | Logic | **Copy button does not copy to clipboard** — only displays `st.code()`; misleading label |
| 100 | Logic | Cached `transcript` could be `None` — `len(transcript.split())` at line 151 would fail |

**Imports:** OK  
**Syntax:** OK  
**Missing references:** None

---

## 9. requirements.txt

| Line | Type | Issue |
|------|------|-------|
| — | Missing | **`pydub`** — used in `transcriber.py` for files > 24 MB |
| — | Note | File appears to be full `pip freeze` output (58 packages), not minimal pinned deps — works but harder to maintain |
| — | OK | Contains: `streamlit`, `yt-dlp`, `groq`, `python-dotenv`, `reportlab`, `python-docx`, `requests` |

**Packages used in code vs requirements:**

| Package | In code | In requirements |
|---------|---------|-----------------|
| streamlit | ✓ | ✓ |
| yt-dlp | ✓ | ✓ |
| groq | ✓ | ✓ |
| python-dotenv | ✓ | ✓ |
| reportlab | ✓ | ✓ |
| python-docx | ✓ | ✓ |
| requests | — (not directly imported) | ✓ |
| pydub | ✓ (optional) | **✗ MISSING** |

---

## 10. railway.toml

| Line | Type | Issue |
|------|------|-------|
| 5 | OK | `PYTHONPATH=/app` — correct for Railway container layout |
| 5 | OK | `streamlit run app/main.py` — correct entry point |
| 6 | Deploy | `healthcheckPath = "/"` — Streamlit may return non-200 on `/` during startup or use websockets; healthcheck timeouts/failures possible |
| — | Note | Duplicate start config with `nixpacks.toml` — Railway may use either; keep both in sync ✓ |

**ffmpeg:** Not in `railway.toml` — provided via `nixpacks.toml` ✓

---

## 11. nixpacks.toml

| Line | Type | Issue |
|------|------|-------|
| 2 | OK | `ffmpeg` included ✓ |
| 2 | Note | `python312` in `nixPkgs` may duplicate Nixpacks auto-detected Python — usually harmless |
| 5 | OK | `PYTHONPATH=/app` correct |
| 5 | OK | Start command matches `railway.toml` |

---

## Cross-Cutting Checks

### Does app/main.py correctly import from all core modules?

**Yes.** All imports resolve:

- `app.core.config` → `APP_TITLE`, `GROQ_API_KEY`
- `app.core.database` → `init_db`, `save_video`, `get_video_by_url`, `save_content`, `get_content_for_video`
- `app.core.downloader` → `download_audio`, `extract_youtube_id`, `DownloadError`
- `app.core.transcriber` → `transcribe_audio`, `TranscriptionError`
- `app.core.content_engine` → all four generators + `GenerationError`
- `app.exporters.exporter` → `export_txt`, `export_pdf`, `export_docx`

### Local development note

Imports use `from app.core...` which requires **project root** on `PYTHONPATH`.  
Run locally as:

```
PYTHONPATH=. streamlit run app/main.py
```

(or set `PYTHONPATH` to project root on Windows)

---

## Priority Fix List

1. **Add `pydub` to `requirements.txt`** — transcriber large-file path fails without it
2. **Fix `get_content_for_video()` dict logic** (database.py:82) — keep newest per format, not oldest
3. **Fix `save_video()` replace behavior** (database.py:37-45) — reuse existing id or cascade-delete old content
4. **Escape transcript HTML** (main.py:147-149) — use `st.text_area` or `html.escape(transcript)`
5. **Align bot-error message** (downloader.py:140) — mention `YOUTUBE_COOKIES` env var, not sidebar upload
6. **Guard `duration_sec` None** (downloader.py:86, 02_history.py:22)
7. **Fix Copy button** (main.py:234) — use `st.clipboard` (Streamlit 1.31+) or remove misleading label
8. **Add try/except for exports** in `02_history.py` (match main.py pattern)

---

*End of review*
