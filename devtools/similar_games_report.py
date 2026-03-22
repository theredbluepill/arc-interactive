#!/usr/bin/env python3
"""Multi-signal similarity scan over ``environment_files`` packages.

Compares **one canonical package per stem** (see ``--canonical-policy``) using:
registry/metadata fields, text bags (GAMES.md + metadata + module docstring),
normalized source (token Jaccard + SHA256 equality shortcut), and a heuristic ``levels`` source
fingerprint.

Emits JSON and Markdown under ``devtools/reports/`` by default.

Example::

    uv run python devtools/similar_games_report.py --top-k 15 --min-score 0.35
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import re
import sys
import tokenize
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ENV_DIR = ROOT / "environment_files"
GAMES_MD = ROOT / "GAMES.md"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "reports"

# Match check_registry.py
STEMS_OMITTED_FROM_GAMES = frozenset({"vc33", "ls20", "ft09"})

_TUTORIAL_STEMS = frozenset({"ez01", "ez02", "ez03", "ez04"})
_STEM_FAMILY_RE = re.compile(r"^([a-z]+?)(\d+)$", re.ASCII)


def _discover_packages() -> list[tuple[str, str, Path]]:
    out: list[tuple[str, str, Path]] = []
    if not ENV_DIR.is_dir():
        return out
    for stem_path in sorted(ENV_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not stem_path.is_dir():
            continue
        stem = stem_path.name
        for ver_path in sorted(stem_path.iterdir(), key=lambda p: p.name.lower()):
            if not ver_path.is_dir():
                continue
            meta = ver_path / "metadata.json"
            if meta.is_file():
                out.append((stem, ver_path.name, meta))
    return out


def _versions_by_stem(
    packages: list[tuple[str, str, Path]],
) -> dict[str, list[tuple[str, Path]]]:
    m: dict[str, list[tuple[str, Path]]] = {}
    for stem, ver, meta in packages:
        m.setdefault(stem, []).append((ver, meta))
    for stem in m:
        m[stem].sort(key=lambda x: x[0].lower())
    return m


def _is_hex8(name: str) -> bool:
    return len(name) == 8 and all(c in "0123456789abcdef" for c in name.lower())


def canonical_version(versions: list[str], policy: str) -> str:
    """Pick one version dir name for a stem."""
    if not versions:
        raise ValueError("empty versions")
    if len(versions) == 1:
        return versions[0]
    if policy == "first":
        return sorted(versions, key=lambda s: s.lower())[0]
    if policy == "last":
        return sorted(versions, key=lambda s: s.lower())[-1]
    if policy == "prefer_git_sha":
        hexes = [v for v in versions if _is_hex8(v)]
        if hexes:
            return sorted(hexes, key=lambda s: s.lower())[-1]
        if "v1" in versions:
            return "v1"
        return sorted(versions, key=lambda s: s.lower())[-1]
    raise ValueError(f"unknown policy {policy!r}")


def _parse_games_md_rows(path: Path) -> dict[str, dict[str, str]]:
    """stem -> {category, grid, levels, description, actions, preview}."""
    text = path.read_text(encoding="utf-8")
    rows: dict[str, dict[str, str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 8:
            continue
        stem = cells[1]
        if not stem or stem.lower() == "game":
            continue
        if set(stem) <= {"-", ":"}:
            continue
        category, grid, nlev, desc, preview, actions = (
            cells[2],
            cells[3],
            cells[4],
            cells[5],
            cells[6],
            cells[7],
        )
        if stem.startswith("-"):
            continue
        rows[stem] = {
            "category": category,
            "grid": grid,
            "levels": nlev,
            "description": desc,
            "preview": preview,
            "actions": actions,
        }
    return rows


def _stem_family_key(stem: str) -> str | None:
    m = _STEM_FAMILY_RE.match(stem)
    if not m:
        return None
    return m.group(1)


def _pair_labels(a: str, b: str) -> list[str]:
    labels: list[str] = []
    if a in _TUTORIAL_STEMS and b in _TUTORIAL_STEMS:
        labels.append("tutorial_series")
    fa, fb = _stem_family_key(a), _stem_family_key(b)
    if fa and fb and fa == fb:
        labels.append("same_prefix_numbered_family")
    # Explicit cross-reference in GAMES description (weak signal; filled later per-stem)
    return labels


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _word_bag(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return {w for w in text.split() if len(w) > 1}


def _strip_comments_normalize(source: str) -> str:
    """Remove comments; collapse whitespace for stable diffs."""
    out: list[str] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type in (tokenize.NL, tokenize.NEWLINE):
                out.append(" ")
            elif tok.string:
                out.append(tok.string)
                out.append(" ")
    except tokenize.TokenError:
        return re.sub(r"\s+", " ", source).strip()
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _module_docstring(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    body = tree.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[0].value.value
    return ""


def _levels_source_fingerprint(source: str) -> str | None:
    """SHA256 of normalized ``levels`` assignment RHS source, if found."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "levels":
                seg = ast.get_source_segment(source, node)
                if seg is None:
                    return None
                norm = _strip_comments_normalize(seg)
                return hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return None


def _metadata_feature_bag(meta: dict[str, Any]) -> set[str]:
    bag: set[str] = set()
    for k in ("title", "description"):
        v = meta.get(k)
        if isinstance(v, str):
            bag |= _word_bag(v)
    tags = meta.get("tags")
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, str):
                bag.add(t.lower())
    tm = meta.get("training_metadata")
    if isinstance(tm, dict):
        for key in ("physics_rules", "reward_structure"):
            v = tm.get(key)
            if isinstance(v, str):
                bag.add(v.lower())
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, str):
                        bag.add(x.lower())
        for key in ("action_space", "episode_count"):
            v = tm.get(key)
            if v is not None:
                bag.add(str(v).lower())
        gr = tm.get("grid_range")
        if isinstance(gr, list):
            bag.add("grid_" + "_".join(str(x) for x in gr))
    return bag


def _registry_feature_bag(row: dict[str, str] | None) -> set[str]:
    if not row:
        return set()
    parts = " ".join(
        row.get(k, "")
        for k in ("category", "grid", "levels", "description", "actions")
    )
    return _word_bag(parts)


@dataclass
class StemFeatures:
    stem: str
    version: str
    meta_path: str
    py_path: str
    title: str
    meta_bag_size: int
    registry_bag_size: int
    text_bag_size: int
    code_norm_sha256: str
    levels_fingerprint: str | None
    training_metadata: dict[str, Any] | None


def load_stem_features(
    stem: str,
    version: str,
    meta_path: Path,
    games_rows: dict[str, dict[str, str]],
) -> StemFeatures | None:
    py_path = ENV_DIR / stem / version / f"{stem}.py"
    if not py_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(meta, dict):
        return None
    source = py_path.read_text(encoding="utf-8")
    norm = _strip_comments_normalize(source)
    code_hash = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    title = meta.get("title", "") if isinstance(meta.get("title"), str) else ""
    tm = meta.get("training_metadata")
    tm_dict = tm if isinstance(tm, dict) else None
    meta_bag = _metadata_feature_bag(meta)
    reg_bag = _registry_feature_bag(games_rows.get(stem))
    doc = _module_docstring(source)
    desc = ""
    if isinstance(meta.get("description"), str):
        desc = meta["description"]
    games_desc = (games_rows.get(stem) or {}).get("description", "")
    text_bag = meta_bag | reg_bag | _word_bag(doc) | _word_bag(desc) | _word_bag(games_desc)
    lev_fp = _levels_source_fingerprint(source)
    return StemFeatures(
        stem=stem,
        version=version,
        meta_path=str(meta_path.relative_to(ROOT)),
        py_path=str(py_path.relative_to(ROOT)),
        title=title,
        meta_bag_size=len(meta_bag),
        registry_bag_size=len(reg_bag),
        text_bag_size=len(text_bag),
        code_norm_sha256=code_hash,
        levels_fingerprint=lev_fp,
        training_metadata=tm_dict,
    )


def _suspicious_components(
    pairs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Connected components over pairs flagged ``suspicious_overlap`` (undirected)."""
    adj: dict[str, set[str]] = {}
    for p in pairs:
        if not p.get("suspicious_overlap"):
            continue
        a, b = p["a"], p["b"]
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    seen: set[str] = set()
    comps: list[dict[str, Any]] = []
    for start in sorted(adj.keys(), key=str.lower):
        if start in seen:
            continue
        stack = [start]
        comp: set[str] = set()
        while stack:
            u = stack.pop()
            if u in comp:
                continue
            comp.add(u)
            seen.add(u)
            for v in adj.get(u, ()):
                if v not in comp:
                    stack.append(v)
        comps.append(
            {
                "stems": sorted(comp, key=str.lower),
                "size": len(comp),
            }
        )
    comps.sort(key=lambda c: (-c["size"], c["stems"][0] if c["stems"] else ""))
    return comps


def _score_pair(
    bags_a: tuple[set[str], set[str], set[str], set[str]],
    bags_b: tuple[set[str], set[str], set[str], set[str]],
    hash_a: str,
    hash_b: str,
    lev_a: str | None,
    lev_b: str | None,
    w_meta: float,
    w_text: float,
    w_code: float,
    w_level: float,
) -> tuple[float, dict[str, float]]:
    meta_a, reg_a, text_a, code_a = bags_a
    meta_b, reg_b, text_b, code_b = bags_b
    s_meta = 0.5 * (_jaccard(meta_a, meta_b) + _jaccard(reg_a, reg_b))
    s_text = _jaccard(text_a, text_b)
    if hash_a == hash_b:
        s_code = 1.0
    else:
        # Token Jaccard on comment-stripped source (fast vs O(n*m) difflib per pair).
        s_code = _jaccard(code_a, code_b)
    if lev_a and lev_b:
        s_level = 1.0 if lev_a == lev_b else 0.0
    else:
        s_level = 0.0
    wsum = w_meta + w_text + w_code + w_level
    if wsum <= 0:
        composite = 0.0
    else:
        composite = (
            w_meta * s_meta + w_text * s_text + w_code * s_code + w_level * s_level
        ) / wsum
    detail = {
        "meta_registry": round(s_meta, 4),
        "text": round(s_text, 4),
        "code": round(s_code, 4),
        "levels": round(s_level, 4),
        "composite": round(composite, 4),
    }
    return composite, detail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Output directory for JSON and Markdown (default: devtools/reports)",
    )
    parser.add_argument(
        "--canonical-policy",
        choices=("prefer_git_sha", "first", "last"),
        default="prefer_git_sha",
        help="How to pick a version when a stem has multiple dirs (default: prefer_git_sha)",
    )
    parser.add_argument(
        "--include-reference",
        action="store_true",
        help="Include vc33, ls20, ft09 (normally excluded from public-benchmark view)",
    )
    parser.add_argument(
        "--only-games-md",
        action="store_true",
        help="Only stems that appear in GAMES.md (still respects --include-reference)",
    )
    parser.add_argument("--top-k", type=int, default=12, help="Neighbors per stem in report")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.25,
        help="Minimum composite score to include in pair list",
    )
    parser.add_argument(
        "--w-meta",
        type=float,
        default=1.0,
        help="Weight for metadata+registry Jaccard blend",
    )
    parser.add_argument(
        "--w-text", type=float, default=1.0, help="Weight for full text Jaccard"
    )
    parser.add_argument(
        "--w-code",
        type=float,
        default=1.2,
        help="Weight for code token Jaccard (1.0 if normalized SHA256 matches)",
    )
    parser.add_argument(
        "--w-level",
        type=float,
        default=0.8,
        help="Weight for levels source fingerprint match (0 if missing)",
    )
    args = parser.parse_args()

    packages = _discover_packages()
    by_stem = _versions_by_stem(packages)
    games_rows = _parse_games_md_rows(GAMES_MD) if GAMES_MD.is_file() else {}

    stems_ordered = sorted(by_stem.keys(), key=lambda s: s.lower())
    canonical: dict[str, tuple[str, Path]] = {}
    for stem in stems_ordered:
        vers = [v for v, _ in by_stem[stem]]
        cv = canonical_version(vers, args.canonical_policy)
        meta_path = next(p for v, p in by_stem[stem] if v == cv)
        canonical[stem] = (cv, meta_path)

    features: dict[str, StemFeatures] = {}
    skipped: list[dict[str, str]] = []
    for stem, (cv, meta_path) in canonical.items():
        if not args.include_reference and stem in STEMS_OMITTED_FROM_GAMES:
            continue
        if args.only_games_md and stem not in games_rows:
            continue
        f = load_stem_features(stem, cv, meta_path, games_rows)
        if f is None:
            skipped.append({"stem": stem, "version": cv, "reason": "missing_or_bad_py_meta"})
            continue
        features[stem] = f

    # Token bags for code similarity (fast vs full-file difflib on every pair).
    code_bags: dict[str, set[str]] = {}
    meta_bags: dict[str, set[str]] = {}
    reg_bags: dict[str, set[str]] = {}
    text_bags: dict[str, set[str]] = {}
    for stem, feat in features.items():
        py_path = ROOT / feat.py_path
        raw = py_path.read_text(encoding="utf-8")
        norm = _strip_comments_normalize(raw)
        code_bags[stem] = _word_bag(norm)
        meta = json.loads((ROOT / feat.meta_path).read_text(encoding="utf-8"))
        meta_bags[stem] = _metadata_feature_bag(meta)
        reg_bags[stem] = _registry_feature_bag(games_rows.get(stem))
        doc = _module_docstring(raw)
        desc = meta.get("description", "") if isinstance(meta.get("description"), str) else ""
        games_desc = (games_rows.get(stem) or {}).get("description", "")
        text_bags[stem] = (
            meta_bags[stem]
            | reg_bags[stem]
            | _word_bag(doc)
            | _word_bag(desc)
            | _word_bag(games_desc)
        )

    stems = sorted(features.keys(), key=lambda s: s.lower())
    pairs_out: list[dict[str, Any]] = []
    neighbors: dict[str, list[dict[str, Any]]] = {s: [] for s in stems}

    for i, sa in enumerate(stems):
        for sb in stems[i + 1 :]:
            fa, fb = features[sa], features[sb]
            comp, detail = _score_pair(
                (meta_bags[sa], reg_bags[sa], text_bags[sa], code_bags[sa]),
                (meta_bags[sb], reg_bags[sb], text_bags[sb], code_bags[sb]),
                features[sa].code_norm_sha256,
                features[sb].code_norm_sha256,
                fa.levels_fingerprint,
                fb.levels_fingerprint,
                args.w_meta,
                args.w_text,
                args.w_code,
                args.w_level,
            )
            if comp < args.min_score:
                continue
            labels = _pair_labels(sa, sb)
            desc_a = (games_rows.get(sa) or {}).get("description", "")
            desc_b = (games_rows.get(sb) or {}).get("description", "")
            if sa in desc_b.lower() or sb in desc_a.lower():
                labels.append("cross_name_in_description")
            suspicious = "same_prefix_numbered_family" not in labels and "tutorial_series" not in labels
            row = {
                "a": sa,
                "b": sb,
                "version_a": fa.version,
                "version_b": fb.version,
                "score": detail["composite"],
                "detail": detail,
                "labels": sorted(set(labels)),
                "suspicious_overlap": suspicious,
                "same_code_hash": fa.code_norm_sha256 == fb.code_norm_sha256,
                "same_levels_fingerprint": bool(
                    fa.levels_fingerprint
                    and fb.levels_fingerprint
                    and fa.levels_fingerprint == fb.levels_fingerprint
                ),
            }
            pairs_out.append(row)
            neighbors[sa].append({"stem": sb, **detail})
            neighbors[sb].append({"stem": sa, **detail})

    for s in stems:
        neighbors[s].sort(key=lambda r: r["composite"], reverse=True)
        neighbors[s] = neighbors[s][: args.top_k]

    pairs_out.sort(key=lambda r: (-r["score"], r["a"], r["b"]))

    suspicious_components = _suspicious_components(pairs_out)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "options": {
            "canonical_policy": args.canonical_policy,
            "include_reference": args.include_reference,
            "only_games_md": args.only_games_md,
            "top_k": args.top_k,
            "min_score": args.min_score,
            "weights": {
                "meta": args.w_meta,
                "text": args.w_text,
                "code": args.w_code,
                "level": args.w_level,
            },
        },
        "stem_count": len(stems),
        "skipped": skipped,
        "pairs": pairs_out,
        "suspicious_components": suspicious_components,
        "neighbors": neighbors,
        "features": {s: asdict(features[s]) for s in stems},
    }
    json_path = args.out_dir / "similar_games.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md_lines = [
        "# Similar games report",
        "",
        f"Canonical package per stem (`{args.canonical_policy}`), "
        f"{len(stems)} stems compared.",
        "",
        "## Weights",
        "",
        f"- meta/registry: {args.w_meta}, text: {args.w_text}, "
        f"code: {args.w_code}, levels fingerprint: {args.w_level}",
        "",
        f"## Top pairs (min composite {args.min_score:.3f})",
        "",
        "| Score | A | B | meta | text | code | lvl | Labels | Suspicious |",
        "|------:|---|---|-----:|-----:|-----:|----:|--------|------------|",
    ]
    for p in pairs_out[:200]:
        d = p["detail"]
        lbl = ", ".join(p["labels"]) if p["labels"] else "—"
        susp = "yes" if p["suspicious_overlap"] else "no"
        md_lines.append(
            f"| {d['composite']} | {p['a']} | {p['b']} | {d['meta_registry']} | "
            f"{d['text']} | {d['code']} | {d['levels']} | {lbl} | {susp} |"
        )
    if len(pairs_out) > 200:
        md_lines.append("")
        md_lines.append(f"*({len(pairs_out) - 200} more pairs in similar_games.json)*")

    md_lines.extend(
        [
            "",
            "## Suspicious overlap components",
            "",
            "Undirected connected components over pairs with **Suspicious** = yes "
            "(batch-triage one component at a time).",
            "",
        ]
    )
    if not suspicious_components:
        md_lines.append("*None.*")
    else:
        for i, comp in enumerate(suspicious_components, 1):
            comp_line = ", ".join(f"`{s}`" for s in comp["stems"])
            md_lines.append(f"{i}. ({comp['size']} stems) {comp_line}")

    md_lines.extend(
        [
            "",
            f"## Per-stem nearest neighbors (top {args.top_k})",
            "",
        ]
    )
    for s in stems:
        md_lines.append(f"### {s}")
        if not neighbors[s]:
            md_lines.append("*No neighbors above threshold.*")
            continue
        for n in neighbors[s]:
            md_lines.append(
                f"- **{n['stem']}** composite={n['composite']} "
                f"(meta={n['meta_registry']}, text={n['text']}, "
                f"code={n['code']}, lvl={n['levels']})"
            )
        md_lines.append("")

    md_lines.extend(
        [
            "## Skipped stems",
            "",
        ]
    )
    if not skipped:
        md_lines.append("*None.*")
    else:
        for row in skipped:
            md_lines.append(f"- `{row['stem']}` ({row['version']}): {row['reason']}")

    md_path = args.out_dir / "similar_games.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote {json_path.relative_to(ROOT)} and {md_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
