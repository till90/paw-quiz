#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PAW Patrol Quiz (Level-Run wie beim HP-Quiz)

Was neu ist (gegenüber dem alten "Random Question" Paw-Quiz):
- 15 Fragen pro Level
- Level-Anzahl wird dynamisch aus dem Datenset berechnet:
    Nur Charaktere mit < 5 "Unbekannt"-Einträgen in profile_flat kommen ins Spiel.
- Kein Schwierigkeitsgrad mehr
- Run-Token (itsdangerous) -> Level kann fortgesetzt werden (LocalStorage im Frontend)
- Vor/Zurück-Navigation: beantwortete Fragen sind durchscrollbar
"""

import hashlib
import json
import mimetypes
import os
import random
import re
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from flask import Flask, Response, jsonify, make_response, render_template_string, request, send_file
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


# ------------------------------------------------------------
# 0) META / LINKS
# ------------------------------------------------------------

LANDING_URL = "https://data-tales.dev/"

SERVICES = [
    ("Worm Attack 3000", "https://worm-attack-3000.data-tales.dev/"),
    ("PAW Wiki", "https://paw-wiki.data-tales.dev/"),
    ("WizardQuiz", "https://wizard-quiz.data-tales.dev/"),
]

SERVICE_META = {
    "service_name_slug": "paw-quiz",
    "page_title": "PAW  Quiz",
    "page_h1": "PAW Quiz",
    "page_subtitle": "Errate den Charakter anhand des Bildes. 15 Fragen pro Level.",
}

# ------------------------------------------------------------
# 1) SETTINGS / VALIDATION
# ------------------------------------------------------------

QUESTIONS_PER_LEVEL = 15
UNKNOWN_LIMIT = 5  # nur Charaktere mit < 5 *Unbekannt* (profile_flat) kommen ins Spiel

ID_RE = re.compile(r"^[a-z0-9-]{1,80}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9._-]{20,8000}$")
MEDIA_PATH_RE = re.compile(r"^[A-Za-z0-9_\-./]{1,220}$")

# Run-Token lange gültig (Fortsetzen)
RUN_TOKEN_MAX_AGE_S = int(os.getenv("RUN_TOKEN_MAX_AGE_S", str(30 * 24 * 60 * 60)))

EXCLUDE_PROFILE_KEYS = {"Stimme (US/Kanada)", "Stimme (UK)"}

APP_DIR = Path(__file__).resolve().parent


def _resolve_path(p: str) -> Path:
    if not p:
        return APP_DIR
    pp = Path(p)
    return pp if pp.is_absolute() else (APP_DIR / pp)


DATA_JSON_PATH = _resolve_path(os.getenv("DATA_JSON_PATH", "out_pawpatrol_characters/characters_de.json"))
DATA_BASE_DIR = _resolve_path(os.getenv("DATA_BASE_DIR", "out_pawpatrol_characters"))


class QuizDataError(Exception):
    pass


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _derive_secret_from_dataset_bytes(all_bytes: bytes) -> str:
    env_secret = (os.getenv("APP_SECRET") or "").strip()
    if env_secret:
        return env_secret
    h = _sha256_hex(all_bytes)
    return h or "paw-quiz-fallback-secret"


def _make_serializer(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret, salt="paw-quiz-v2")


def _token_dumps(s: URLSafeTimedSerializer, kind: str, payload: Dict[str, Any]) -> str:
    obj = {"k": kind, "p": payload}
    return s.dumps(obj)


def _token_loads(s: URLSafeTimedSerializer, token: str, kind: str, max_age_s: int) -> Dict[str, Any]:
    if not isinstance(token, str) or not TOKEN_RE.match(token):
        raise QuizDataError("Ungültiges Token-Format.")
    obj = s.loads(token, max_age=max_age_s)
    if not isinstance(obj, dict) or obj.get("k") != kind or not isinstance(obj.get("p"), dict):
        raise QuizDataError("Ungültiges Token.")
    return obj["p"]


# ------------------------------------------------------------
# 2) DATASET LOADING
# ------------------------------------------------------------

def _nonempty_profile_flat(pf: Any) -> bool:
    return isinstance(pf, dict) and any(str(k).strip() and str(v).strip() for k, v in pf.items())


def _safe_media_path(rel_path: str) -> Path:
    """Resolve rel_path under DATA_BASE_DIR and prevent path traversal."""
    if not rel_path or not MEDIA_PATH_RE.fullmatch(rel_path) or rel_path.startswith("/") or ".." in rel_path:
        raise ValueError("invalid media path")

    base = DATA_BASE_DIR.resolve()
    target = (DATA_BASE_DIR / rel_path).resolve()
    if base not in target.parents and target != base:
        raise ValueError("media path traversal blocked")
    return target


@lru_cache(maxsize=1)
def load_dataset() -> Dict[str, Any]:
    if not DATA_JSON_PATH.exists():
        raise FileNotFoundError(f"Dataset JSON not found: {DATA_JSON_PATH}")
    obj = json.loads(DATA_JSON_PATH.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Dataset root must be an object")
    chars = obj.get("characters")
    if not isinstance(chars, list):
        raise ValueError("Dataset must contain characters[] list")
    return obj


@lru_cache(maxsize=1)
def get_valid_characters() -> List[Dict[str, Any]]:
    ds = load_dataset()
    out: List[Dict[str, Any]] = []
    for ch in ds.get("characters", []):
        if not isinstance(ch, dict):
            continue
        cid = str(ch.get("id", "")).strip()
        name = str(ch.get("name", "")).strip()
        pf = ch.get("profile_flat", {})
        img = ch.get("image", {}) if isinstance(ch.get("image"), dict) else {}
        src = ch.get("source", {}) if isinstance(ch.get("source"), dict) else {}

        if not cid or not ID_RE.fullmatch(cid):
            continue
        if not name:
            continue
        if not _nonempty_profile_flat(pf):
            continue

        rel_img = ""
        if isinstance(img, dict):
            rel_img = str(img.get("local_path", "")).strip()
        if not rel_img:
            continue

        try:
            img_path = _safe_media_path(rel_img)
        except Exception:
            continue
        if not img_path.exists() or not img_path.is_file():
            continue

        out.append(
            {
                "id": cid,
                "name": name,
                "image_rel": rel_img,
                "profile_flat": pf if isinstance(pf, dict) else {},
                "source": {
                    "page_url": str(src.get("page_url", "")).strip(),
                    "attribution": str(src.get("attribution", "")).strip(),
                },
            }
        )

    if len(out) < 3:
        raise ValueError("Not enough valid characters with profile_flat + existing images (need >= 3).")
    return out


def _filter_profile_flat(pf: Dict[str, Any]) -> Dict[str, str]:
    clean: Dict[str, str] = {}
    for k, v in pf.items():
        kk = str(k).strip()
        if not kk or kk in EXCLUDE_PROFILE_KEYS:
            continue
        vv = str(v).strip()
        if not vv:
            continue
        clean[kk] = vv
    return clean


def _unknown_count(pf: Dict[str, Any]) -> int:
    pf_clean = _filter_profile_flat(pf)
    n = 0
    for v in pf_clean.values():
        if str(v).strip().lower() == "unbekannt":
            n += 1
    return n


@lru_cache(maxsize=1)
def get_eligible_characters() -> List[Dict[str, Any]]:
    """Nur Charaktere mit < UNKNOWN_LIMIT 'Unbekannt' in profile_flat."""
    chars = get_valid_characters()
    eligible = [c for c in chars if _unknown_count(c.get("profile_flat", {})) < UNKNOWN_LIMIT]
    if len(eligible) < 3:
        raise QuizDataError(
            f"Zu wenig geeignete Charaktere (>=3 benötigt). "
            f"Aktuell: {len(eligible)} (Filter: < {UNKNOWN_LIMIT}× 'Unbekannt')."
        )
    return eligible


@lru_cache(maxsize=1)
def _dataset_secret() -> str:
    try:
        raw = DATA_JSON_PATH.read_bytes()
    except Exception:
        raw = b"paw-quiz-fallback"
    return _derive_secret_from_dataset_bytes(raw)


SERIALIZER = _make_serializer(_dataset_secret())


def _stable_rng(seed_parts: List[str]) -> random.Random:
    s = "|".join(seed_parts).encode("utf-8", errors="ignore")
    h = hashlib.sha256((_dataset_secret() + "::").encode("utf-8") + s).digest()
    seed_int = int.from_bytes(h[:8], "big", signed=False)
    return random.Random(seed_int)


@lru_cache(maxsize=1)
def get_levels() -> List[Dict[str, Any]]:
    """Compute dynamic levels from eligible characters."""
    eligible = get_eligible_characters()
    n = len(eligible)
    # mindestens ein Level
    level_count = max(1, (n + QUESTIONS_PER_LEVEL - 1) // QUESTIONS_PER_LEVEL)

    # stabile globale Reihenfolge (damit Levels reproduzierbar sind)
    rng = _stable_rng(["global-order"])
    ids = [c["id"] for c in eligible]
    rng.shuffle(ids)
    by_id = {c["id"]: c for c in eligible}
    ordered = [by_id[i] for i in ids if i in by_id]

    levels: List[Dict[str, Any]] = []
    for lv in range(1, level_count + 1):
        start = (lv - 1) * QUESTIONS_PER_LEVEL
        end = start + QUESTIONS_PER_LEVEL
        chunk = ordered[start:end]

        # Sicherstellen: genau 15 Fragen (falls Restmenge kleiner ist -> auffüllen)
        if len(chunk) < QUESTIONS_PER_LEVEL:
            pool = [c for c in ordered if c["id"] not in {x["id"] for x in chunk}]
            rng2 = _stable_rng(["fill", str(lv)])
            while len(chunk) < QUESTIONS_PER_LEVEL:
                if pool:
                    chunk.append(pool.pop(rng2.randrange(0, len(pool))))
                else:
                    # Notfall: Duplikate zulassen (immer noch "eligible")
                    chunk.append(ordered[rng2.randrange(0, len(ordered))])

        levels.append(
            {
                "level": lv,
                "title": f"Level {lv}",
                "questions": QUESTIONS_PER_LEVEL,
                "character_ids": [c["id"] for c in chunk],
            }
        )

    return levels


def _validate_level(level: Any) -> int:
    lv = _safe_int(level, 0)
    levels = get_levels()
    if lv < 1 or lv > len(levels):
        raise QuizDataError(f"Level muss zwischen 1 und {len(levels)} liegen.")
    return lv


def _find_character(cid: str) -> Optional[Dict[str, Any]]:
    if not ID_RE.fullmatch(cid):
        return None
    for c in get_valid_characters():
        if c["id"] == cid:
            return c
    return None


def _build_run(level: int) -> Dict[str, Any]:
    levels = get_levels()
    lv_def = levels[level - 1]
    eligible = get_eligible_characters()
    eligible_ids = [c["id"] for c in eligible]
    by_id = {c["id"]: c for c in eligible}

    rng = random.SystemRandom()

    qspecs: List[Dict[str, Any]] = []
    for cid in lv_def["character_ids"]:
        if cid not in by_id:
            continue
        # 2 Distraktoren aus eligible (nicht korrekt)
        distractors = [x for x in eligible_ids if x != cid]
        if len(distractors) < 2:
            raise QuizDataError("Zu wenig Distraktoren im Datenset (>=2 benötigt).")
        d1, d2 = rng.sample(distractors, 2)

        opt_ids = [cid, d1, d2]
        rng.shuffle(opt_ids)
        qspecs.append({"cid": cid, "opt": opt_ids})

    # garantiert 15 (Chunk-Fill + Validierung oben)
    if len(qspecs) != QUESTIONS_PER_LEVEL:
        raise QuizDataError("Interner Fehler: Level enthält nicht 15 Fragen.")

    runp = {
        "v": 1,
        "rid": uuid.uuid4().hex,
        "lvl": level,
        "t0": int(time.time()),
        "score": 0,
        "next": 0,  # index der nächsten unbeantworteten Frage
        "qs": qspecs,  # [{cid, opt:[...]}]
        "ans": [None] * QUESTIONS_PER_LEVEL,  # selected option-id
        "ok": [None] * QUESTIONS_PER_LEVEL,   # bool
    }
    return runp


def _state_from_run(runp: Dict[str, Any], view_pos: int) -> Dict[str, Any]:
    return {
        "level": runp.get("lvl"),
        "pos": view_pos,
        "next": runp.get("next"),
        "total": QUESTIONS_PER_LEVEL,
        "score": runp.get("score"),
        "done": int(runp.get("next", 0)) >= QUESTIONS_PER_LEVEL,
    }


def _question_payload(runp: Dict[str, Any], pos: int) -> Dict[str, Any]:
    qs = runp["qs"]
    if pos < 0 or pos >= len(qs):
        raise QuizDataError("Ungültige Frage-Position.")

    q = qs[pos]
    cid = q["cid"]
    opt_ids = q["opt"]

    ch = _find_character(cid)
    if not ch:
        raise QuizDataError("Charakter nicht gefunden.")

    # options -> names
    name_map = {c["id"]: c["name"] for c in get_valid_characters()}
    options = [{"id": oid, "text": name_map.get(oid, oid)} for oid in opt_ids]

    answered = runp["ans"][pos] is not None
    selected_id = runp["ans"][pos] if answered else None
    correct_id = cid if answered else None
    correct = (selected_id == correct_id) if answered else None

    payload: Dict[str, Any] = {
        "idx": pos + 1,
        "pos": pos,
        "total": QUESTIONS_PER_LEVEL,
        "image_url": f"/media/{quote(ch['image_rel'])}",
        "options": options,
        "answered": answered,
        "selected_id": selected_id,
        "correct_id": correct_id,
        "correct": correct,
    }

    # Quelle IMMER mitsenden (auch vor Beantwortung)
    src = ch.get("source", {}) if isinstance(ch.get("source"), dict) else {}
    src_attrib = str(src.get("attribution", "")).strip()
    src_page_url = str(src.get("page_url", "")).strip()

    payload["source"] = {
        "attribution": src_attrib,
        "page_url": src_page_url,
        "page_title": str(src.get("page_title", "")).strip(),
        "text_license_default": str(src.get("text_license_default", "")).strip(),
        "text_license_url": str(src.get("text_license_url", "")).strip(),
        "retrieved_at": str(src.get("retrieved_at", "")).strip(),
        "revision_id": src.get("revision_id"),
        "revision_timestamp": str(src.get("revision_timestamp", "")).strip(),
    }
    # Fallback-Felder für ältere JS-Versionen
    payload["attribution"] = src_attrib
    payload["page_url"] = src_page_url

    return payload


def _summary_from_run(runp: Dict[str, Any]) -> Dict[str, Any]:
    duration_s = max(0, int(time.time()) - int(runp.get("t0", int(time.time()))))
    correct_n = sum(1 for x in runp.get("ok", []) if x is True)
    accuracy = float(correct_n) / float(QUESTIONS_PER_LEVEL)
    return {
        "level": runp.get("lvl"),
        "score": int(runp.get("score", 0)),
        "correct_n": int(correct_n),
        "accuracy": accuracy,
        "duration_s": duration_s,
    }


def _validate_run_token(run_token: str) -> Dict[str, Any]:
    try:
        runp = _token_loads(SERIALIZER, run_token, "run", max_age_s=RUN_TOKEN_MAX_AGE_S)
    except SignatureExpired as e:
        raise QuizDataError("Run-Token ist abgelaufen. Bitte starte das Level neu.") from e
    except BadSignature as e:
        raise QuizDataError("Run-Token ist ungültig. Bitte starte das Level neu.") from e

    needed = ("rid", "lvl", "score", "next", "qs", "ans", "ok", "t0")
    for k in needed:
        if k not in runp:
            raise QuizDataError("Run-Token ist unvollständig. Bitte starte das Level neu.")

    if not isinstance(runp["qs"], list) or len(runp["qs"]) != QUESTIONS_PER_LEVEL:
        raise QuizDataError("Run-Token ist ungültig (qs).")
    if not isinstance(runp["ans"], list) or len(runp["ans"]) != QUESTIONS_PER_LEVEL:
        raise QuizDataError("Run-Token ist ungültig (ans).")
    if not isinstance(runp["ok"], list) or len(runp["ok"]) != QUESTIONS_PER_LEVEL:
        raise QuizDataError("Run-Token ist ungültig (ok).")

    nxt = _safe_int(runp.get("next"), 0)
    if nxt < 0 or nxt > QUESTIONS_PER_LEVEL:
        raise QuizDataError("Run-Token ist ungültig (next).")

    # normalize ints
    runp["lvl"] = _safe_int(runp.get("lvl"), 1)
    runp["score"] = _safe_int(runp.get("score"), 0)
    runp["next"] = nxt
    runp["t0"] = _safe_int(runp.get("t0"), int(time.time()))
    return runp


def _update_run_token(runp: Dict[str, Any]) -> str:
    # ensure JSON-serializable / normalized
    runp["lvl"] = int(runp["lvl"])
    runp["score"] = int(runp["score"])
    runp["next"] = int(runp["next"])
    runp["t0"] = int(runp["t0"])
    return _token_dumps(SERIALIZER, "run", runp)


# ------------------------------------------------------------
# 3) APP
# ------------------------------------------------------------

app = Flask(__name__)


# ------------------------------------------------------------
# 4) ROUTES (API)
# ------------------------------------------------------------

@app.get("/api/health")
def api_health() -> Response:
    try:
        _ = get_levels()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)[:240]}), 500


@app.get("/api/levels")
def api_levels() -> Response:
    try:
        levels = get_levels()
        out = [{"level": lv["level"], "title": lv["title"], "questions": lv["questions"]} for lv in levels]
        eligible_total = len(get_eligible_characters())
        return jsonify({"ok": True, "levels": out, "eligible_total": eligible_total})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/run/start")
def api_run_start() -> Response:
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception:
        return _json_error("invalid_json", 400)

    try:
        level = _validate_level(body.get("level"))
        runp = _build_run(level)
        run_token = _update_run_token(runp)
        q = _question_payload(runp, 0)
        st = _state_from_run(runp, view_pos=0)
        return jsonify({"ok": True, "run": run_token, "state": st, "question": q})
    except QuizDataError as e:
        return _json_error(str(e), 400)
    except Exception as e:
        return _json_error(str(e), 500)


@app.post("/api/run/resume")
def api_run_resume() -> Response:
    """Client sends saved run-token, server re-validates and returns current question (view at min(next, last answered))."""
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception:
        return _json_error("invalid_json", 400)

    run_token = str(body.get("run", "")).strip()
    if not run_token:
        return _json_error("run fehlt", 400)

    try:
        runp = _validate_run_token(run_token)
        # View pos: last answered (next-1) or 0
        view_pos = max(0, int(runp["next"]) - 1) if int(runp["next"]) > 0 else 0
        q = _question_payload(runp, view_pos)
        st = _state_from_run(runp, view_pos=view_pos)
        done = bool(st["done"])
        summary = _summary_from_run(runp) if done else None
        return jsonify({"ok": True, "updated_run": _update_run_token(runp), "state": st, "question": q, "done": done, "summary": summary})
    except QuizDataError as e:
        return _json_error(str(e), 400)


@app.post("/api/run/question")
def api_run_question() -> Response:
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception:
        return _json_error("invalid_json", 400)

    run_token = str(body.get("run", "")).strip()
    pos = _safe_int(body.get("pos"), 0)

    if not run_token:
        return _json_error("run fehlt", 400)

    try:
        runp = _validate_run_token(run_token)

        # darf maximal bis "next" (erste unbeantwortete) navigieren
        if pos < 0 or pos > int(runp["next"]):
            return _json_error("Diese Frage ist noch nicht freigeschaltet.", 400)
        if pos >= QUESTIONS_PER_LEVEL:
            return _json_error("Ungültige Frage-Position.", 400)

        q = _question_payload(runp, pos)
        st = _state_from_run(runp, view_pos=pos)
        return jsonify({"ok": True, "updated_run": _update_run_token(runp), "state": st, "question": q})
    except QuizDataError as e:
        return _json_error(str(e), 400)


@app.post("/api/run/answer")
def api_run_answer() -> Response:
    try:
        body = request.get_json(force=True, silent=False) or {}
    except Exception:
        return _json_error("invalid_json", 400)

    run_token = str(body.get("run", "")).strip()
    pos = _safe_int(body.get("pos"), -1)
    choice_id = str(body.get("choice_id", "")).strip()

    if not run_token:
        return _json_error("run fehlt", 400)
    if not ID_RE.fullmatch(choice_id):
        return _json_error("Ungültige Auswahl.", 400)

    try:
        runp = _validate_run_token(run_token)

        if pos != int(runp["next"]):
            # Nur die nächste offene Frage darf beantwortet werden (kein Überspringen / keine Änderungen)
            return _json_error("Nur die nächste offene Frage kann beantwortet werden.", 400)

        if pos < 0 or pos >= QUESTIONS_PER_LEVEL:
            return _json_error("Ungültige Frage-Position.", 400)

        qspec = runp["qs"][pos]
        opt_ids = qspec.get("opt", [])
        if choice_id not in opt_ids:
            return _json_error("Auswahl passt nicht zur Frage.", 400)

        correct_id = qspec.get("cid")
        is_correct = (choice_id == correct_id)

        # speichern
        runp["ans"][pos] = choice_id
        runp["ok"][pos] = bool(is_correct)
        if is_correct:
            runp["score"] = int(runp.get("score", 0)) + 1

        runp["next"] = int(runp["next"]) + 1

        updated = _update_run_token(runp)

        # Antwort-Question Payload (inkl. Steckbrief)
        q = _question_payload(runp, pos)
        st = _state_from_run(runp, view_pos=pos)
        done = bool(st["done"])
        summary = _summary_from_run(runp) if done else None

        return jsonify({"ok": True, "updated_run": updated, "state": st, "question": q, "done": done, "summary": summary})

    except QuizDataError as e:
        return _json_error(str(e), 400)


# ------------------------------------------------------------
# 5) ROUTES (MEDIA)
# ------------------------------------------------------------

@app.get("/media/<path:rel_path>")
def media(rel_path: str):
    try:
        fp = _safe_media_path(rel_path)
        if not fp.exists() or not fp.is_file():
            return jsonify({"ok": False, "error": "not_found"}), 404

        mime, _ = mimetypes.guess_type(str(fp))
        resp = make_response(send_file(fp, mimetype=mime or "application/octet-stream"))
        resp.headers["Cache-Control"] = "public, max-age=2592000, immutable"
        return resp
    except Exception:
        return jsonify({"ok": False, "error": "invalid_path"}), 400


# ------------------------------------------------------------
# 6) UI
# ------------------------------------------------------------

HTML = r"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <meta name="theme-color" content="#0b0f19"/>
  <meta name="robots" content="noindex,nofollow"/>
  <title>{{ page_title }}</title>

  <style>
  :root{
    --bg: #0b0f19;
    --bg2:#0f172a;
    --card:#111a2e;
    --text:#e6eaf2;
    --muted:#a8b3cf;
    --border: rgba(255,255,255,.10);
    --shadow: 0 18px 60px rgba(0,0,0,.35);
    --primary:#6ea8fe;
    --primary2:#8bd4ff;
    --focus: rgba(110,168,254,.45);
    --radius: 18px;
    --container: 1100px;
    --gap: 18px;
    --font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji","Segoe UI Emoji";
  }
  [data-theme="light"]{
    --bg:#f6f7fb;
    --bg2:#ffffff;
    --card:#ffffff;
    --text:#111827;
    --muted:#4b5563;
    --border: rgba(17,24,39,.12);
    --shadow: 0 18px 60px rgba(17,24,39,.10);
    --primary:#2563eb;
    --primary2:#0ea5e9;
    --focus: rgba(37,99,235,.25);
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{
    margin:0;
    font-family:var(--font);
    background: radial-gradient(1200px 800px at 20% -10%, rgba(110,168,254,.25), transparent 55%),
                radial-gradient(1000px 700px at 110% 10%, rgba(139,212,255,.20), transparent 55%),
                linear-gradient(180deg, var(--bg), var(--bg2));
    color:var(--text);
  }


  /* Layout: Quiz im Desktop-Viewport ohne Scrollen (so gut wie möglich) */
  body{ display:flex; flex-direction:column; min-height:100vh; }
  .site-header{ flex:0 0 auto; }
  main{ flex:1 1 auto; }

  @media (min-width: 900px){
    body.in-quiz{ height:100vh; overflow:hidden; }
    body.in-quiz main{ overflow:hidden; padding: 12px 0 14px; }
    body.in-quiz .hero{ height:100%; padding: 6px 0 10px; }
    body.in-quiz .quiz-wrap{ height:100%; }
    body.in-quiz .quiz-grid{ height:100%; }
    body.in-quiz .quiz-card{ max-height:100%; overflow:auto; }

    /* Footer im Quiz ausblenden, spart Platz */
    body.in-quiz .site-footer{ display:none; }

    /* Platz sparen */
    .quiz-media{ aspect-ratio: 4 / 3; max-height: 38vh; margin-top: 10px; }
    .options{ grid-template-columns: 1fr 1fr; gap: 10px; }
    .option-btn{ min-height: 46px; padding: 10px 12px; }
  }

  /* 3-2-1 + Richtig/Falsch Overlay (Wizard-Quiz Stil) */
  .answer-overlay{
    position: fixed;
    inset: 0;
    z-index: 120;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    backdrop-filter: blur(8px);
  }
  .answer-overlay.verdict{
    background: rgba(0,0,0,.72);
    backdrop-filter: blur(8px);
  }
  .answer-overlay[hidden]{ display:none; }

  .overlay-label{
    min-width: min(520px, 86vw);
    padding: 26px 30px;
    border-radius: 22px;
    border: 1px solid var(--border);
    background: rgba(17, 26, 46, .92);
    box-shadow: var(--shadow);
    text-align: center;
    font-weight: 950;
    letter-spacing: .06em;
    text-transform: uppercase;
    font-size: clamp(34px, 6vw, 70px);
  }
  [data-theme="light"] .overlay-label{ background: rgba(255,255,255,.92); }

  .overlay-label.count{
    letter-spacing: 0;
    text-transform: none;
    font-size: clamp(78px, 16vw, 150px);
  }
  .overlay-label.ok{
    border-color: rgba(34,197,94,.60);
    box-shadow: 0 0 0 4px rgba(34,197,94,.18), var(--shadow);
  }
  .overlay-label.bad{
    border-color: rgba(239,68,68,.60);
    box-shadow: 0 0 0 4px rgba(239,68,68,.18), var(--shadow);
  }
  .overlay-label.pop{ animation: overlayPop .26s ease-out; }
  @keyframes overlayPop{
    0%{ transform: scale(.88); opacity: .0; }
    100%{ transform: scale(1); opacity: 1; }
  }


  /* Attribution (optional, nur nach Klick sichtbar) */
  .attr-row{
    display:flex;
    justify-content:flex-end;
    margin-top: 10px;
  }
  .attr-btn{
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 850;
    opacity: .9;
  }
  .attr-box{
    margin-top: 8px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 12px;
    line-height: 1.55;
    word-break: break-word;
  }
  .attr-box a{ color: var(--text); text-decoration:none; border-bottom:1px solid transparent; }
  .attr-box a:hover{ border-bottom-color: var(--text); }

  /* Falsche Antworten nach der Antwort ausblenden */
  .option-btn.fade-out{ opacity: 0; transform: translateY(6px) scale(.98); }

  .container{max-width:var(--container); margin:0 auto; padding:0 18px;}
  .skip-link{
    position:absolute; left:-999px; top:10px;
    background:var(--card); color:var(--text);
    padding:10px 12px; border-radius:10px;
    border:1px solid var(--border);
  }
  .skip-link:focus{left:10px; outline:2px solid var(--focus)}

  /* Header */
  .site-header{
    position:sticky; top:0; z-index:20;
    backdrop-filter: blur(10px);
    background: rgba(10, 14, 24, .55);
    border-bottom:1px solid var(--border);
  }
  [data-theme="light"] .site-header{ background: rgba(246,247,251,.75); }

  .header-inner{
    display:flex; align-items:center; justify-content:space-between;
    padding:14px 0; gap:14px;
  }
  .brand{display:flex; align-items:center; gap:10px; text-decoration:none; color:var(--text); font-weight:700}
  .brand-mark{
    width:14px; height:14px; border-radius:6px;
    background: linear-gradient(135deg, var(--primary), var(--primary2));
    box-shadow: 0 10px 25px rgba(110,168,254,.25);
  }

  /* Dropdown */
  .nav-dropdown{ position: relative; display: inline-flex; align-items: center; }
  .nav-dropbtn{
    background: none; border: none; padding: 0; margin: 0; font-family: inherit;
    color: var(--muted); text-decoration: none; font-weight: 600;
    display: inline-flex; align-items: center; gap: 8px;
    cursor: pointer; height: 100%;
  }
  .nav-dropbtn:hover{ color: var(--text); transform: none; }
  .nav-caret{ font-size: .9em; opacity: 1; }
  .nav-menu{
    position: absolute;
    top: calc(100% + 10px);
    left: 0;
    min-width: 240px;
    padding: 10px;
    z-index: 6000;
    backdrop-filter: blur(10px);
    background: var(--card);
  }
  .nav-menu a{
    display: block;
    padding: 10px 10px;
    border-radius: 12px;
    text-decoration: none;
    color: var(--text);
    font-weight: 650;
  }
  .nav-menu a:hover{ background: rgba(110,168,254,.12); }
  .nav-menu a:focus{ outline: 2px solid var(--focus); outline-offset: 2px; }

  .header-actions{display:flex; gap:10px; align-items:center}
  .header-note{
    display:flex; align-items:center; gap:8px;
    padding:8px 10px;
    border-radius:12px;
    border:1px solid var(--border);
    background: rgba(255,255,255,.04);
    color: var(--muted);
    font-weight: 750;
    font-size: 12px;
    line-height: 1;
    white-space: nowrap;
  }
  [data-theme="light"] .header-note{ background: rgba(17,24,39,.03); }
  .header-note__label{
    letter-spacing: .06em; text-transform: uppercase;
    font-weight: 900; color: var(--muted);
  }
  .header-note__mail{
    color: var(--text);
    text-decoration: none;
    font-weight: 850;
  }
  .header-note__mail:hover{ text-decoration: underline; }
  @media (max-width: 720px){ .header-note__label{ display:none; } }

  .btn{
    display:inline-flex; align-items:center; justify-content:center;
    gap:8px; padding:10px 14px;
    border-radius:12px; border:1px solid var(--border);
    text-decoration:none; font-weight:800;
    color:var(--text); background: transparent;
    cursor:pointer; user-select:none;
  }
  .btn:focus{outline:2px solid var(--focus); outline-offset:2px}
  .btn-primary{
    border-color: transparent;
    background: linear-gradient(135deg, var(--primary), var(--primary2));
    color: #0b0f19;
  }
  [data-theme="light"] .btn-primary{ color:#ffffff; }
  .btn-secondary{ background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.02); }
  [data-theme="light"] .btn-secondary{ background: rgba(17,24,39,.04); border-color: rgba(17,24,39,.04); }
  .btn-ghost{ background: transparent; }
  .btn:hover{transform: translateY(-1px)}
  .btn:active{transform:none}
  .btn[disabled]{opacity:.55; cursor:not-allowed; transform:none;}

  .sr-only{
    position:absolute; width:1px; height:1px; padding:0; margin:-1px;
    overflow:hidden; clip:rect(0,0,0,0); border:0;
  }

  /* Layout */
  .hero{ padding: 10px 0 16px; }
  h1{margin:0 0 10px; font-size:38px; line-height:1.1}
  @media (max-width: 520px){ h1{font-size:32px} }
  .lead{margin:0; color:var(--muted); font-size:15px; line-height:1.6}

  .card{
    border:1px solid var(--border);
    border-radius: var(--radius);
    padding:16px;
    box-shadow: var(--shadow);
    transition: transform .12s ease, border-color .12s ease;
    background: rgba(255,255,255,.04);
  }
  [data-theme="light"] .card{ background: rgba(255,255,255,.92); }

  .grid{
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap);
    margin-top: 18px;
  }
  @media (max-width: 980px){ .grid{grid-template-columns: repeat(2, 1fr)} }
  @media (max-width: 640px){ .grid{grid-template-columns: 1fr} }

  .card-title{font-weight:900; font-size:16px; margin:0 0 8px}
  .card-desc{color:var(--muted); margin:0 0 12px; line-height:1.55}

  .level-meta{
    display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;
    color: var(--muted); font-weight: 750; font-size: 12px;
  }
  .pill{
    border:1px solid var(--border);
    background: rgba(255,255,255,.04);
    border-radius:999px;
    padding:5px 9px;
    font-weight:900;
    color: var(--muted);
    display:inline-flex;
    align-items:center;
    gap:6px;
  }
  [data-theme="light"] .pill{ background: rgba(17,24,39,.03); }

  .quiz-wrap{ display:none; margin-top: 18px; }
  .quiz-grid{ display:grid; grid-template-columns: 1fr; gap: var(--gap); }

  .quiz-card{ position:relative; overflow:hidden; }

  .row{ display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .stats{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }

  .progress{
    height: 12px;
    border-radius: 999px;
    border:1px solid var(--border);
    background: rgba(255,255,255,.03);
    overflow:hidden;
  }
  [data-theme="light"] .progress{ background: rgba(17,24,39,.02); }
  .progress > div{
    height:100%;
    width:0%;
    background: linear-gradient(135deg, var(--primary), var(--primary2));
  }

  .quiz-media{
    width:100%;
    border-radius: 16px;
    border:1px solid var(--border);
    overflow:hidden;
    background: rgba(255,255,255,.03);
    aspect-ratio: 1 / 1;
    display:flex;
    align-items:center;
    justify-content:center;
    margin-top: 14px;
  }
  [data-theme="light"] .quiz-media{ background: rgba(17,24,39,.02); }
  .quiz-media img{
    width:100%;
    height:100%;
    object-fit: contain;
    display:block;
  }

  .question{
    margin-top: 12px;
    font-weight: 950;
    font-size: 20px;
    line-height: 1.45;
  }

  .options{
    display:grid;
    grid-template-columns: 1fr;
    gap: 12px;
    margin-top: 12px;
  }

  .option-btn{
    width:100%;
    justify-content:space-between;
    text-align:left;
    border-color: rgba(255,255,255,.10);
    background: rgba(255,255,255,.03);
    font-weight: 900;
    font-size: clamp(13px, 1.2vw, 16px);
    line-height: 1.25;
    padding: 12px 14px;
    min-height: 52px;
    transition: opacity .22s ease, transform .22s ease;
  }
  [data-theme="light"] .option-btn{
    border-color: rgba(17,24,39,.12);
    background: rgba(17,24,39,.02);
  }
  .option-btn[disabled]{ cursor:not-allowed; transform:none; opacity:.80; }
  .option-btn.dim{ opacity:.45; }
  .option-btn.ok{
    border-color: rgba(34,197,94,.55);
    box-shadow: 0 0 0 3px rgba(34,197,94,.15);
  }
  .option-btn.bad{
    border-color: rgba(239,68,68,.55);
    box-shadow: 0 0 0 3px rgba(239,68,68,.15);
  }

  .actions{ display:flex; gap:10px; flex-wrap:wrap; margin-top: 14px; }

  .details{ margin-top: var(--gap); }
  .kv{
    display:grid;
    grid-template-columns: 1fr 1.4fr;
    gap: 10px 14px;
    margin-top: 10px;
  }
  @media (max-width: 640px){
    .kv{ grid-template-columns: 1fr; }
  }
  .k{ color: var(--muted); font-weight: 900; }
  .v{ font-weight: 750; }
  .source{
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-weight: 650;
    line-height:1.5;
    font-size: 13px;
    word-break: break-word;
  }
  .source a{ color: var(--text); text-decoration:none; border-bottom:1px solid transparent; }
  .source a:hover{ border-bottom-color: var(--text); }

  .toast{
    position: fixed;
    right: 16px;
    bottom: 16px;
    max-width: min(420px, calc(100vw - 32px));
    z-index: 80;
    display:flex;
    flex-direction:column;
    gap:10px;
    pointer-events:none;
  }
  .toast .t{
    pointer-events:none;
    border:1px solid var(--border);
    border-radius: 14px;
    background: rgba(17, 26, 46, .92);
    backdrop-filter: blur(10px);
    color: var(--text);
    box-shadow: var(--shadow);
    padding: 12px 14px;
    font-weight: 850;
  }
  [data-theme="light"] .toast .t{ background: rgba(255,255,255,.96); }
  .toast .t small{
    display:block;
    margin-top:6px;
    color: var(--muted);
    font-weight: 750;
  }

  body.in-quiz .hero .lead{ display:none; }
  body.in-quiz .hero h1{ display:none; }

  .site-footer{
    margin-top: 32px;
    padding: 18px 0 26px;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
  }
  .site-footer a{ color: var(--text); text-decoration: none; }
  .site-footer a:hover{ text-decoration: underline; }

  .footer-title{
    font-weight: 900;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0 0 6px;
  }
  .footer-text{ margin: 0 0 8px; }
  .footer-text:last-child{ margin-bottom: 0; }
  

  /* ---------------------------------------------------------
     Desktop: alles im Viewport (keine Page-Scrollbars)
     - Seite selbst bleibt fix im Viewport
     - Quiz-Card scrollt intern, falls Steckbrief zu lang ist
     --------------------------------------------------------- */
  body{ display:flex; flex-direction:column; min-height:100vh; }
  .site-header{ flex:0 0 auto; }
  main{ flex:1 1 auto; }

  @media (min-width: 900px){
    body.in-quiz{ height:100vh; overflow:hidden; }
    body.in-quiz main{ overflow:hidden; padding: 12px 0 14px; }
    body.in-quiz .hero{ height:100%; padding: 6px 0 10px; }
    body.in-quiz .quiz-wrap{ height:100%; }
    body.in-quiz .quiz-grid{ height:100%; }
    body.in-quiz .quiz-card{ max-height:100%; overflow:auto; }
    body.in-quiz .site-footer{ display:none; }

    /* Platz sparen */
    h1{ font-size:32px; }
    .question{ font-size:18px; margin-top:10px; }
    .quiz-media{
      aspect-ratio: 4 / 3;
      max-height: 38vh;
      margin-top: 10px;
    }
    .options{ grid-template-columns: 1fr 1fr; gap: 10px; }
    .option-btn{ min-height: 46px; padding: 10px 12px; }
    .actions{ margin-top: 10px; }
    .details{ margin-top: 12px; }
  }
</style>
</head>

<body>
  <a class="skip-link" href="#main">Zum Inhalt springen</a>

  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="{{ landing_url }}" aria-label="Zur Landing Page">
        <span class="brand-mark" aria-hidden="true"></span>
        <span class="brand-text">data-tales.dev</span>
      </a>

      <div class="nav-dropdown" data-dropdown>
          <button class="btn btn-ghost nav-dropbtn"
                  type="button"
                  aria-haspopup="true"
                  aria-expanded="false"
                  aria-controls="servicesMenu">
            Dienste <span class="nav-caret" aria-hidden="true">▾</span>
          </button>

          <div id="servicesMenu" class="card nav-menu" role="menu" hidden>
            <a role="menuitem" href="https://flybi-demo.data-tales.dev/">Flybi Dashboard Demo</a>
            <a role="menuitem" href="https://wms-wfs-sources.data-tales.dev/">WMS/WFS Server Viewer</a>
            <a role="menuitem" href="https://tree-locator.data-tales.dev/">Tree Locator</a>
            <a role="menuitem" href="https://plz.data-tales.dev/">PLZ → Koordinaten</a>
            <a role="menuitem" href="https://paw-wiki.data-tales.dev/">Paw Patrole Wiki</a>
            <a role="menuitem" href="https://paw-quiz.data-tales.dev/">Paw Patrole Quiz</a>
            <a role="menuitem" href="https://hp-quiz.data-tales.dev/">Harry Potter Quiz</a>
            <a role="menuitem" href="https://worm-attack-3000.data-tales.dev/">Wurm Attacke 3000</a>
          </div>
      </div>

      <div class="header-actions">
        <div class="header-note" aria-label="Feedback Kontakt">
          <span class="header-note__label">Änderung / Kritik:</span>
          <a class="header-note__mail" href="mailto:info@data-tales.dev">info@data-tales.dev</a>
        </div>

        <button class="btn btn-ghost" id="themeToggle" type="button" aria-label="Theme umschalten">
          <span aria-hidden="true" id="themeIcon">☾</span>
          <span class="sr-only">Theme umschalten</span>
        </button>
      </div>
    </div>
  </header>

  <main id="main">
    <section class="hero">
      <div class="container">
        <h1>{{ page_h1 }}</h1>
        <p class="lead">{{ page_subtitle }}</p>

        <div id="errorBanner" class="card" style="display:none; margin-top:18px;">
          <div class="card-title">Quiz nicht verfügbar</div>
          <div class="card-desc" id="errorText"></div>
        </div>

        <div id="levelWrap">
          <div class="grid" id="levelGrid"></div>
        </div>

        <div class="quiz-wrap" id="quizWrap">
          <div class="quiz-grid">

            <div class="card quiz-card" id="quizCard" style="display:block;">
              <div class="row">
                <div class="stats">
                  <span class="pill">Level <strong id="uiLevel">1</strong></span>
                  <span class="pill">Score <strong id="uiScore">0</strong></span>
                  <span class="pill">Frage <strong id="uiPos">1</strong>/15</span>
                </div>
              </div>

              <div style="margin-top:12px;">
                <div class="progress" aria-label="Progress">
                  <div id="uiBar"></div>
                </div>
              </div>

              <div class="quiz-media" aria-label="Quiz-Bild">
                <img id="quizImg" src="" alt="" loading="eager" decoding="async" />
              </div>

              <div class="question" id="uiQuestion">Wer ist das?</div>
              <div class="options" id="uiOptions"></div>

              <div class="actions">
                <button class="btn btn-secondary" id="btnBackToLevels" type="button">Level wählen</button>
                <button class="btn btn-ghost" id="btnPrev" type="button">Zurück</button>
                <button class="btn btn-primary" id="btnNext" type="button">Weiter</button>
                <button class="btn btn-ghost" id="btnAuto" type="button" title="Automatisch weiter nach Antwort">Auto: An</button>
              </div>

              <div class="attr-row">
                <button class="btn btn-ghost attr-btn" id="btnAttr" type="button" >ⓘ Quelle</button>
              </div>
              <div class="attr-box" id="attrBox" ></div>

            </div>

            <div class="card" id="resultCard" style="display:none;">
              <div class="card-title">Run abgeschlossen</div>
              <p class="card-desc" id="resultText"></p>
              <div class="actions">
                <button class="btn btn-secondary" id="btnAgain" type="button">Nochmal (gleiches Level)</button>
                <button class="btn btn-ghost" id="btnResultBack" type="button">Zur Level-Auswahl</button>
              </div>
            </div>

          </div>
        </div>

      </div>
    </section>
  </main>

  <footer class="site-footer" role="contentinfo">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-title">Hinweis</div>
        <p class="footer-text">
          Inoffizielles Fan-Projekt. Keine Verbindung zu Spin Master / Nickelodeon / Paramount oder anderen Rechteinhabern.
        </p>
        <p class="footer-text">
          Hinweise / Removal-Requests:
          <a href="mailto:info@data-tales.dev">info@data-tales.dev</a>
        </p>
      </div>
    </div>
  </footer>


  <div class="answer-overlay" id="answerOverlay" aria-hidden="true" hidden>
    <div class="overlay-label count pop" id="answerOverlayLabel">3</div>
  </div>

  <div class="toast" id="toast"></div>

<script>
(function(){
  // Dropdown (Header)
  const dd = document.querySelector('[data-dropdown]');
  if(dd){
    const btn = dd.querySelector('.nav-dropbtn');
    const menu = dd.querySelector('.nav-menu');
    function setOpen(isOpen){
      btn.setAttribute('aria-expanded', String(isOpen));
      menu.hidden = !isOpen;
      dd.classList.toggle('open', isOpen);
    }
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = btn.getAttribute('aria-expanded') === 'true';
      setOpen(!isOpen);
    });
    document.addEventListener('click', (e) => { if(!dd.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', (e) => { if(e.key === 'Escape') setOpen(false); });
    dd.addEventListener('focusout', () => { requestAnimationFrame(() => { if(!dd.contains(document.activeElement)) setOpen(false); }); });
    setOpen(false);
  }

  // Theme Toggle
  const themeKey = "theme";
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  function setTheme(mode){
    if(mode === "light"){
      root.setAttribute("data-theme","light");
      themeIcon.textContent = "☀";
    }else{
      root.removeAttribute("data-theme");
      themeIcon.textContent = "☾";
    }
    localStorage.setItem(themeKey, mode);
  }
  setTheme(localStorage.getItem(themeKey) || "dark");
  themeToggle.addEventListener("click", () => {
    const cur = localStorage.getItem(themeKey) || "dark";
    setTheme(cur === "light" ? "dark" : "light");
  });

  // UI refs
  const errorBanner = document.getElementById("errorBanner");
  const errorText = document.getElementById("errorText");
  const levelWrap = document.getElementById("levelWrap");
  const levelGrid = document.getElementById("levelGrid");
  const quizWrap = document.getElementById("quizWrap");
  const quizCard = document.getElementById("quizCard");
  const resultCard = document.getElementById("resultCard");

  const uiLevel = document.getElementById("uiLevel");
  const uiScore = document.getElementById("uiScore");
  const uiPos = document.getElementById("uiPos");
  const uiBar = document.getElementById("uiBar");
  const quizImg = document.getElementById("quizImg");
  const uiQuestion = document.getElementById("uiQuestion");
  const uiOptions = document.getElementById("uiOptions");

  const btnAttr = document.getElementById("btnAttr");
  const attrBox = document.getElementById("attrBox");

  const answerOverlay = document.getElementById("answerOverlay");
  const answerOverlayLabel = document.getElementById("answerOverlayLabel");


  const btnPrev = document.getElementById("btnPrev");
  const btnNext = document.getElementById("btnNext");
  const btnBackToLevels = document.getElementById("btnBackToLevels");

  const btnAuto = document.getElementById("btnAuto");

  const btnAgain = document.getElementById("btnAgain");
  const btnResultBack = document.getElementById("btnResultBack");
  const resultText = document.getElementById("resultText");

  const toast = document.getElementById("toast");

  // LocalStorage keys
  const RUNS_KEY = "pawQuizRuns.v1"; // map { "<level>": { run: "<token>", ts: <ms> } }
  const STATS_KEY = "pawQuizStats.v1"; // map { "<level>": { bestScore: n } }

  const SETTINGS_KEY = "pawQuizSettings.v1"; // { autoAdvance: bool, autoAdvanceMs: number, unlockMinScore: number }
  const DEFAULT_UNLOCK_MIN_SCORE = 9;   // >= 9/15 schaltet das nächste Level frei
  const DEFAULT_AUTO_ADVANCE = true;    // automatisch zur nächsten Frage nach Antwort
  const DEFAULT_AUTO_ADVANCE_MS = 900;  // Delay, damit Feedback sichtbar bleibt

  function loadSettings(){
    try{
      const obj = JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}");
      return (obj && typeof obj === "object") ? obj : {};
    }catch(_e){
      return {};
    }
  }
  function saveSettings(obj){
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(obj || {}));
  }

  const settings = loadSettings();
  let autoAdvance = (typeof settings.autoAdvance === "boolean") ? settings.autoAdvance : DEFAULT_AUTO_ADVANCE;
  let autoAdvanceMs = (typeof settings.autoAdvanceMs === "number" && settings.autoAdvanceMs >= 0) ? settings.autoAdvanceMs : DEFAULT_AUTO_ADVANCE_MS;
  let unlockMinScore = (typeof settings.unlockMinScore === "number" && settings.unlockMinScore >= 0) ? settings.unlockMinScore : DEFAULT_UNLOCK_MIN_SCORE;

  let advanceNonce = 0;
  function cancelAutoAdvance(){
    advanceNonce++;
    if(typeof btnNext !== "undefined" && btnNext){
      btnNext.textContent = "Weiter";
      // disabled-state wird durch loadQuestion()/renderQuestion neu gesetzt
      btnNext.disabled = false;
    }
  }

  function setAutoAdvance(enabled){
    autoAdvance = !!enabled;
    settings.autoAdvance = autoAdvance;
    saveSettings(settings);
    updateAutoButton();
  }

  function updateAutoButton(){
    if(!btnAuto) return;
    btnAuto.textContent = autoAdvance ? "Auto: An" : "Auto: Aus";
    btnAuto.setAttribute("aria-pressed", String(autoAdvance));
  }

  function toastMsg(title, detail){
    const el = document.createElement("div");
    el.className = "t";
    el.innerHTML = `${escapeHtml(title)}${detail ? `<small>${escapeHtml(detail)}</small>` : ""}`;
    toast.appendChild(el);
    setTimeout(() => el.remove(), 2600);
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function wait(ms){ return new Promise(r => setTimeout(r, ms)); }
  function nextFrame(){ return new Promise(r => requestAnimationFrame(() => r())); }

  function overlaySet(text, kind){
    if(!answerOverlay || !answerOverlayLabel) return;
    // Backdrop nur bei Richtig/Falsch (nicht bei 3-2-1)
    if(String(kind || "") === "count"){
      answerOverlay.classList.remove("verdict");
    }else{
      answerOverlay.classList.add("verdict");
    }
    answerOverlayLabel.textContent = String(text);
    answerOverlayLabel.className = `overlay-label ${kind || ""}`;
    // restart animation
    void answerOverlayLabel.offsetWidth;
    answerOverlayLabel.classList.add("pop");
  }
  async function playCountdownAndVerdictFromPromise(resultPromise, onAfterCountdown){
    if(!answerOverlay || !answerOverlayLabel){
      const res = await resultPromise;
      if(typeof onAfterCountdown === "function") onAfterCountdown(res);
      return res;
    }

    answerOverlay.hidden = false;
    answerOverlay.setAttribute("aria-hidden", "false");

    const stepMs = 600;
    overlaySet("3", "count"); await wait(stepMs);
    overlaySet("2", "count"); await wait(stepMs);
    overlaySet("1", "count"); await wait(stepMs);

    overlaySet("…", "count");
    const res = await resultPromise;

    await nextFrame();
    if(typeof onAfterCountdown === "function") onAfterCountdown(res);

    const isCorrect = !!(res && res.question && res.question.correct);
    overlaySet(isCorrect ? "RICHTIG" : "FALSCH", isCorrect ? "ok" : "bad");
    await wait(900);

    answerOverlay.hidden = true;
    answerOverlay.setAttribute("aria-hidden", "true");
    return res;
  }

  async function api(method, url, body){
    const init = { method, headers: {"Content-Type":"application/json"} };
    if(body) init.body = JSON.stringify(body);
    const r = await fetch(url, init);
    const j = await r.json().catch(() => ({ok:false, error:"Antwort ist kein JSON."}));
    if(!r.ok || !j.ok){
      const err = j && j.error ? j.error : `HTTP ${r.status}`;
      throw new Error(err);
    }
    return j;
  }

  function loadRuns(){
    try{
      const obj = JSON.parse(localStorage.getItem(RUNS_KEY) || "{}");
      return (obj && typeof obj === "object") ? obj : {};
    }catch(_e){
      return {};
    }
  }
  function saveRuns(obj){
    localStorage.setItem(RUNS_KEY, JSON.stringify(obj || {}));
  }
  function getRun(level){
    const m = loadRuns();
    const e = m[String(level)];
    return e && e.run ? String(e.run) : null;
  }
  function setRun(level, runToken){
    const m = loadRuns();
    m[String(level)] = {run: runToken, ts: Date.now()};
    saveRuns(m);
  }
  function clearRun(level){
    const m = loadRuns();
    delete m[String(level)];
    saveRuns(m);
  }

  function loadStats(){
    try{
      const obj = JSON.parse(localStorage.getItem(STATS_KEY) || "{}");
      return (obj && typeof obj === "object") ? obj : {};
    }catch(_e){
      return {};
    }
  }
  function saveStats(obj){
    localStorage.setItem(STATS_KEY, JSON.stringify(obj || {}));
  }
  function getBestScore(level){
    const s = loadStats();
    const e = s[String(level)];
    return e && typeof e.bestScore === "number" ? e.bestScore : 0;
  }
  function setBestScore(level, score){
    const s = loadStats();
    const cur = getBestScore(level);
    if(score > cur){
      s[String(level)] = {bestScore: score};
      saveStats(s);
    }
  }

  function isLevelUnlocked(level){
    if(unlockMinScore <= 0) return true;
    if(level <= 1) return true;
    return getBestScore(level - 1) >= unlockMinScore;
  }

  // Client state
  let levels = [];
  let currentLevel = 1;
  let runToken = null;
  let viewPos = 0;       // aktuell angezeigte Frage
  let nextPos = 0;       // erste unbeantwortete Frage (server state)
  let total = 15;

  function showError(msg){
    errorBanner.style.display = "block";
    errorText.textContent = msg;
  }
  function hideError(){
    errorBanner.style.display = "none";
    errorText.textContent = "";
  }
  function showLevels(){
    document.body.classList.remove("in-quiz");
    levelWrap.style.display = "block";
    quizWrap.style.display = "none";
    resultCard.style.display = "none";
    quizCard.style.display = "block";
  }
  function showQuiz(){
    document.body.classList.add("in-quiz");
    levelWrap.style.display = "none";
    quizWrap.style.display = "block";
    resultCard.style.display = "none";
    quizCard.style.display = "block";
  }
  function showResult(){
    document.body.classList.add("in-quiz");
    levelWrap.style.display = "none";
    quizWrap.style.display = "block";
    quizCard.style.display = "none";
    resultCard.style.display = "block";
  }

  function renderLevels(eligibleTotal){
    levelGrid.innerHTML = "";
    for(const lv of levels){
      const level = Number(lv.level);
      const activeRun = getRun(level);
      const best = getBestScore(level);


      const unlocked = isLevelUnlocked(level);
      const card = document.createElement("div");
      card.className = "card";

      const title = document.createElement("div");
      title.className = "card-title";
      title.textContent = `Level ${level}`;

      const desc = document.createElement("p");
      desc.className = "card-desc";

      const meta = document.createElement("div");
      meta.className = "level-meta";
      meta.innerHTML = `
        <span class="pill">Best <strong>${best}</strong>/15</span>
        ${activeRun ? `<span class="pill">Run gespeichert</span>` : ``}
        ${(!unlocked && !activeRun) ? `<span class="pill">Gesperrt (ab ${unlockMinScore}/15)</span>` : ``}
      `;

      const actions = document.createElement("div");
      actions.style.display = "flex";
      actions.style.gap = "10px";
      actions.style.flexWrap = "wrap";
      actions.style.marginTop = "10px";

      const primary = document.createElement("button");
      primary.className = "btn btn-primary";
      primary.type = "button";

      if(activeRun){
        primary.textContent = "Fortsetzen";
        primary.addEventListener("click", () => resumeLevel(level));
      }else if(!unlocked){
        primary.textContent = `Gesperrt (ab ${unlockMinScore}/15)`;
        primary.disabled = true;
      }else{
        primary.textContent = "Starten";
        primary.addEventListener("click", () => startLevelNew(level));
      }

      actions.appendChild(primary);

      card.appendChild(title);
      card.appendChild(desc);
      card.appendChild(meta);
      card.appendChild(actions);

      levelGrid.appendChild(card);
    }

    {
      const info = document.createElement("div");
      info.className = "card";
      info.style.gridColumn = "1 / -1";
      const et = (typeof eligibleTotal === "number") ? eligibleTotal : null;
      info.innerHTML = `
        <div class="card-title">Regeln</div>
        <p class="card-desc" style="margin:0;">
          Geeignete Charaktere: <strong>${et !== null ? et : "–"}</strong> (Filter: &lt; 5× "Unbekannt").<br/>
          Freischaltung: Level n+1 wird aktiv, wenn Level n mit <strong>≥ ${unlockMinScore}/15</strong> abgeschlossen wurde.<br/>
          Auto-Weiter: <strong>${autoAdvance ? "An" : "Aus"}</strong>
        </p>
      `;
      levelGrid.appendChild(info);
    }
  }

  function updateHUD(state){
    uiLevel.textContent = String(state.level || currentLevel);
    uiScore.textContent = String(state.score || 0);
    viewPos = Number(state.pos || 0);
    nextPos = Number(state.next || 0);
    total = Number(state.total || 15);

    uiPos.textContent = String(viewPos + 1);

    const progress = Math.min(1, Math.max(0, (nextPos) / total));
    uiBar.style.width = `${Math.round(progress * 100)}%`;

    btnPrev.disabled = (viewPos <= 0);
    // Next ist erlaubt, wenn:
    // - viewPos < nextPos  (also bereits beantwortet) oder
    // - viewPos == nextPos und Frage ist beantwortet (wird nach answer true)
    // Wir setzen das nach renderQuestion() nochmal.
  }

  function resetQuestionUI(){
    uiOptions.innerHTML = "";
    uiQuestion.textContent = "Wer ist das?";
    quizImg.src = "";
    quizImg.alt = "";

    // Attribution UI sauber zurücksetzen (ohne Crash)
    setAttribution(null);
  }


function setAttribution(q){
  // nutze die bereits oben definierten refs
  if(!btnAttr || !attrBox) return;

  // q kann null sein -> defensiv
  const src = (q && typeof q === "object" && q.source && typeof q.source === "object")
    ? q.source
    : null;

  const txt =
    (src && typeof src.attribution === "string" && src.attribution.trim())
      ? src.attribution.trim()
      : "Quelle wird geladen…";

  // Button immer sichtbar, Box standardmäßig zu
  btnAttr.hidden = false;
  attrBox.hidden = true;
  attrBox.textContent = txt;

  btnAttr.textContent = "ⓘ Quelle";
  btnAttr.setAttribute("aria-expanded", "false");
}

  function renderOptions(q){
    uiOptions.innerHTML = "";
    for(const o of (q.options || [])){
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn option-btn";
      b.dataset.id = o.id;
      b.innerHTML = `<span>${escapeHtml(o.text)}</span><span class="mark" aria-hidden="true"></span>`;

      if(q.answered){
        b.disabled = true;
      }else{
        // nur die aktuelle offene Frage darf beantwortet werden
        const isAnswerable = (viewPos === nextPos);
        b.disabled = !isAnswerable;
        if(isAnswerable){
          b.addEventListener("click", () => chooseAnswer(o.id));
        }
      }
      uiOptions.appendChild(b);
    }
  }

  function markButton(id, kind, mark){
    const btn = uiOptions.querySelector(`button[data-id="${CSS.escape(id)}"]`);
    if(!btn) return;
    btn.classList.remove("ok","bad","dim");
    if(kind) btn.classList.add(kind);
    const m = btn.querySelector(".mark");
    if(m) m.textContent = mark || "";
  }

  function lockOptions(){
    uiOptions.querySelectorAll("button").forEach(b => b.disabled = true);
  }

  function dimWrongExcept(correctId, keepId){
    uiOptions.querySelectorAll("button").forEach(b => {
      const id = b.dataset.id;
      if(id !== correctId && id !== keepId){
        b.classList.add("dim");
      }
    });
  }

  function applyAnsweredStyling(q){
    if(!q.answered) return;

    lockOptions();

    const selected = q.selected_id;
    const correctId = q.correct_id;

    // Reset classes
    uiOptions.querySelectorAll("button").forEach(b => {
      b.classList.remove("ok","bad","dim","fade-out");
      b.style.display = "";
    });

    if(selected && correctId){
      if(selected === correctId){
        markButton(correctId, "ok", "✓");
      }else{
        markButton(selected, "bad", "✕");
        markButton(correctId, "ok", "✓");
      }
    }
  }

  function hideWrongInstant(correctId){
    uiOptions.querySelectorAll("button").forEach(b => {
      const id = b.dataset.id;
      b.classList.remove("fade-out");
      b.style.display = (id === correctId) ? "" : "none";
    });
  }

  function fadeOutAndHideWrong(correctId, keepAlsoId){
    const keep = new Set([String(correctId || "")]);
    if(keepAlsoId) keep.add(String(keepAlsoId));

    const wrong = [];
    uiOptions.querySelectorAll("button").forEach(b => {
      const id = String(b.dataset.id || "");
      b.classList.remove("fade-out");
      if(!keep.has(id)){
        wrong.push(b);
        b.classList.add("fade-out");
      }else{
        b.style.display = "";
      }
    });
    setTimeout(() => {
      wrong.forEach(b => { b.style.display = "none"; });
    }, 280);
  }

async function loadQuestion(pos){
  resetQuestionUI();
  try{
    const res = await api("POST", "/api/run/question", {run: runToken, pos});
    runToken = res.updated_run;
    setRun(currentLevel, runToken);

    updateHUD(res.state);

    const q = res.question;              // <- ZUERST q holen
    if(!q) throw new Error("Frage ist leer (res.question).");

    // Quelle immer setzen (auch vor Beantwortung)
    setAttribution(q);

    quizImg.src = q.image_url;
    quizImg.alt = "Quiz-Bild";
    renderOptions(q);

    // Next-Button logik: erst nach renderOptions/answered
    btnNext.disabled = (!q.answered && viewPos === nextPos);

    if(q.answered){
      applyAnsweredStyling(q);

      // Falsche direkt ausblenden (falls du das willst)
      if(q.correct_id) hideWrongInstant(q.correct_id);
    }
  }catch(e){
    toastMsg("Fehler", e.message || "Frage konnte nicht geladen werden.");
    showError(e.message || "Frage konnte nicht geladen werden.");
  }
}

  async function chooseAnswer(choiceId){
    cancelAutoAdvance();

    const isAnswerable = (viewPos === nextPos);
    if(!isAnswerable){
      toastMsg("Nicht möglich", "Bitte beantworte die nächste offene Frage.");
      return;
    }

    const myNonce = ++advanceNonce;

    // Sofort UI sperren
    lockOptions();
    btnPrev.disabled = true;
    btnNext.disabled = true;
    btnBackToLevels.disabled = true;
    if(btnAuto) btnAuto.disabled = true;

    const answerPromise = api("POST", "/api/run/answer", {run: runToken, pos: viewPos, choice_id: choiceId});

    try{
      const res = await playCountdownAndVerdictFromPromise(answerPromise, (res) => {
        runToken = res.updated_run;
        setRun(currentLevel, runToken);

        updateHUD(res.state);
        const q = res.question;

        // answered UI im Hintergrund setzen (Overlay ist sichtbar)
        renderOptions(q);
        applyAnsweredStyling(q);
        setAttribution(q);

        // Navigation während Countdown/Verdict + Reveal sperren
        btnPrev.disabled = true;
        btnNext.disabled = true;
        btnBackToLevels.disabled = true;
        if(btnAuto) btnAuto.disabled = true;
      });

      if(myNonce !== advanceNonce) return;

      const q = res.question;

      // Nach dem Overlay: falsche Antworten ausblenden, richtige stehen lassen
      if(q?.correct_id){
        const keepAlso = (q.selected_id && q.selected_id !== q.correct_id) ? q.selected_id : null;
        fadeOutAndHideWrong(q.correct_id, keepAlso);
      }

      // 4 Sekunden die richtige Antwort stehen lassen (auch beim letzten Item)
      await wait(4000);
      if(myNonce !== advanceNonce) return;

      // Done?
      if(res.done && res.summary){
        finishRun(res.summary);
        return;
      }

      // Weiter: Auto oder manuell
      if(autoAdvance){
        const target = Math.min(nextPos, viewPos + 1);

        btnNext.textContent = "Weiter…";
        btnNext.disabled = true;

        await loadQuestion(target);

        btnNext.textContent = "Weiter";
        btnBackToLevels.disabled = false;
        if(btnAuto) btnAuto.disabled = false;
      }else{
        // Manuell: Next wieder freischalten
        btnPrev.disabled = (viewPos <= 0);
        btnNext.disabled = false;
        btnBackToLevels.disabled = false;
        if(btnAuto) btnAuto.disabled = false;
        toastMsg(q.correct ? "Richtig" : "Falsch", `Weiter mit "Weiter".`);
      }

    }catch(e){
      // Overlay sicher schließen
      if(answerOverlay){
        answerOverlay.hidden = true;
        answerOverlay.setAttribute("aria-hidden", "true");
      }

      btnBackToLevels.disabled = false;
      if(btnAuto) btnAuto.disabled = false;

      toastMsg("Antwort nicht möglich", e.message || "Bitte neu versuchen.");
      try{ await loadQuestion(viewPos); }catch(_e){}
    }
  }

  function finishRun(summary){
    // best score update
    setBestScore(currentLevel, Number(summary.score || 0));
    clearRun(currentLevel);

    const secs = Number(summary.duration_s || 0);
    const mm = Math.floor(secs / 60);
    const ss = secs % 60;

    const sc = Number(summary.score || 0);
    const correct = Number(summary.correct_n || 0);
    const acc = Number(summary.accuracy || 0);

    resultText.innerHTML = `
      <strong>Level ${summary.level}</strong><br/>
      Score: <strong>${sc}</strong> / 15<br/>
      Richtig: <strong>${correct}</strong><br/>
      Trefferquote: <strong>${Math.round(acc*100)}%</strong><br/>
      Zeit: <strong>${mm}:${String(ss).padStart(2,"0")}</strong>
    `;

    showResult();
    renderLevels();
    toastMsg("Run beendet", "Zurück zur Level-Auswahl.");
  }

  async function startLevelNew(level){
    hideError();
    cancelAutoAdvance();
    currentLevel = level;
    showQuiz();
    try{
      const res = await api("POST", "/api/run/start", {level});
      runToken = res.run;
      setRun(level, runToken);

      updateHUD(res.state);
      await loadQuestion(0);
      toastMsg(`Level ${level} gestartet`, "Fortschritt wird automatisch gespeichert.");
    }catch(e){
      showError(e.message || "Start fehlgeschlagen.");
      showLevels();
    }
  }

  async function resumeLevel(level){
    hideError();
    cancelAutoAdvance();
    const saved = getRun(level);
    if(!saved){
      toastMsg("Kein Run", "Nichts zum Fortsetzen.");
      return;
    }
    currentLevel = level;
    showQuiz();
    try{
      const res = await api("POST", "/api/run/resume", {run: saved});
      runToken = res.updated_run;
      setRun(level, runToken);

      updateHUD(res.state);

      if(res.done && res.summary){
        finishRun(res.summary);
        return;
      }

      await loadQuestion(viewPos);
      toastMsg(`Fortgesetzt: Level ${level}`, `Frage ${viewPos + 1}/15`);
    }catch(e){
      clearRun(level);
      renderLevels();
      showLevels();
      toastMsg("Fortsetzen nicht möglich", e.message || "Run ungültig/abgelaufen. Bitte neu starten.");
    }
  }

  // Buttons
  updateAutoButton();
  if(btnAuto){
    btnAuto.addEventListener("click", () => {
      cancelAutoAdvance();
      setAutoAdvance(!autoAdvance);
      toastMsg("Auto-Weiter", autoAdvance ? "Aktiv" : "Deaktiviert");
      renderLevels();
    });
  }

  btnPrev.addEventListener("click", async () => {
    cancelAutoAdvance();
    if(viewPos <= 0) return;
    await loadQuestion(viewPos - 1);
  });

  btnNext.addEventListener("click", async () => {
    cancelAutoAdvance();
    // Wenn aktuell unbeantwortet und "next", dann block
    if(viewPos === nextPos){
      // unbeantwortet
      return;
    }
    const newPos = Math.min(nextPos, viewPos + 1);
    await loadQuestion(newPos);
  });


  if(btnAttr && attrBox){
    btnAttr.addEventListener("click", () => {
      const isOpen = !attrBox.hidden;
      attrBox.hidden = isOpen;
      btnAttr.textContent = isOpen ? "ⓘ Quelle" : "Quelle ausblenden";
      btnAttr.setAttribute("aria-expanded", String(!isOpen));
    });
  }

  btnBackToLevels.addEventListener("click", () => {
    cancelAutoAdvance();
    // Run ist bereits persisted bei jedem API Call; hier nur UI zurück.
    renderLevels();
    showLevels();
    toastMsg("Fortschritt gespeichert", "Du kannst jederzeit fortsetzen.");
  });

  btnAgain.addEventListener("click", () => startLevelNew(currentLevel));
  btnResultBack.addEventListener("click", () => { renderLevels(); showLevels(); });

  // init
  (async () => {
    try{
      const res = await api("GET", "/api/levels");
      levels = res.levels || [];
      if(!levels.length) throw new Error("Keine Levels verfügbar.");

      renderLevels(res.eligible_total);
      showLevels();

      // Falls ein Run existiert -> Hinweis
      const anyRunLevel = levels.map(x => Number(x.level)).find(lv => !!getRun(lv));
      if(anyRunLevel){
        toastMsg("Run gefunden", `Level ${anyRunLevel} kann fortgesetzt werden.`);
      }
    }catch(e){
      showError(e.message || "Quizdaten konnten nicht geladen werden.");
      showLevels();
    }
  })();

})();
</script>
</body>
</html>
"""


@app.get("/")
def index() -> str:
    try:
        # Validate once
        _ = get_levels()
        return render_template_string(
            HTML,
            page_title=SERVICE_META["page_title"],
            page_h1=SERVICE_META["page_h1"],
            page_subtitle=SERVICE_META["page_subtitle"],
            landing_url=LANDING_URL,
            services=SERVICES,
        )
    except Exception:
        msg = (
            "Datenset konnte nicht geladen werden. "
            "Prüfe, ob 'out_pawpatrol_characters/characters_de.json' und die Bilder im Repo vorhanden sind "
            "oder setze DATA_JSON_PATH/DATA_BASE_DIR korrekt."
        )
        return render_template_string(
            HTML,
            page_title=SERVICE_META["page_title"],
            page_h1=SERVICE_META["page_h1"],
            page_subtitle=SERVICE_META["page_subtitle"],
            landing_url=LANDING_URL,
            services=SERVICES,
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
