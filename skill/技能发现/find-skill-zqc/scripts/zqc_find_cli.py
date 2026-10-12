#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装前查 · 找技能（find-skill-zqc）CLI · 安全优先的 Skill 查找与安装。

融合两条数据线：
  1) 发现线 = SkillHub 公开 API /api/skills（关键词分词搜索，返回 description_zh/热度/分类）
  2) 安全线 = 装前查公开分片（catalog.json 档位标注 + tools/{shard}.json 证据详情 + authors.json 作者信誉）

工作流：
  find    多关键词搜 SkillHub + 装前查档位合并 → 安全优先排序推荐
  inspect 单个候选的安全详情（证据 / 能力 / 隐私去向 / 作者信誉）
  install 安装闸门：green/yellow 直接装；orange/red 必须先确认；未收录提示无独立评估

仅 Python 3 标准库；纯文本输出；零 API Key。数据失败时降级为「纯 SkillHub 发现 + 无安全标注」。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

# ── 数据源 ──────────────────────────────────────────────────────────────
DEFAULT_ROOT = "https://s.zhuangqiancha.com/"
DATA_ROOT = os.environ.get("ZQC_DATA_URL", DEFAULT_ROOT).rstrip("/") + "/"
SITE_URL = os.environ.get("ZQC_SITE_URL", "https://www.zhuangqiancha.com").rstrip("/")
SH_API = "https://api.skillhub.cn"
SH_WEB = "https://skillhub.cn"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "zqc_find_cache")
CACHE_TTL = 3600
HTTP_TIMEOUT = 60

GRADE_LABEL = {
    "red": "高风险",
    "orange": "谨慎",
    "yellow": "观察",
    "green": "未见风险",
    "unknown": "待评估",
}
# 安全优先排序权重：值越小越靠前（green/yellow 优先 → 未收录/待评估 → orange → red）
GRADE_RANK_FIND = {"green": 0, "yellow": 1, "unknown": 2, None: 3, "orange": 4, "red": 5}
SEV_RANK = {"P0": 0, "P1": 1, "P2": 2, None: 9}
BASIS_CN = {"code": "代码实锤", "doc": "文档自述", "doc_combo": "文档高危组合"}

EXFIL_RULES = {
    "R4_sensitive_file_exfil",
    "R5_external_exfil",
    "R8_suspicious_egress",
    "R9_env_credential_send",
}
PRIVACY_CAPS = {"privacy_upload", "cred_access"}
CLASS_CN = {
    "suspicious": "可疑",
    "official_api": "官方",
    "cdn": "CDN",
    "unknown": "未分类",
}

_SKILLHUB_RE = re.compile(
    r"https?://(?:www\.)?skillhub\.cn/skills/([^/\s?#]+)/([^/\s?#]+)",
    re.I,
)
_GITHUB_RE = re.compile(
    r"https?://(?:www\.)?github\.com/([^/\s?#]+)/([^/\s?#]+)",
    re.I,
)


# ── 基础工具 ────────────────────────────────────────────────────────────
def fnv1a(s: str) -> int:
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def shard_of(slug: str) -> int:
    return fnv1a(slug) % 256


def _cache_path(url: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, key + ".json")


def fetch_json(url: str, ttl: int = CACHE_TTL, retries: int = 2):
    """GET + 内存/磁盘缓存。瞬时网络失败重试 retries 次（沙箱/弱网下避免安全层静默丢失）。

    404 视为永久不存在（返回 None）；429/5xx 退避重试；其余异常重试后仍失败则抛出，
    由调用方决定降级策略（find 会退回纯 SkillHub 发现，install 会提示未收录）。
    """
    cp = _cache_path(url)
    if ttl > 0 and os.path.exists(cp) and (time.time() - os.path.getmtime(cp)) < ttl:
        try:
            with open(cp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    req = urllib.request.Request(url, headers={"User-Agent": "zqc-find-cli/1.0.0"})
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                data = json.loads(r.read().decode("utf-8"))
            try:
                with open(cp, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(1.2 * (attempt + 1))
                continue
            raise
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(0.8 * (attempt + 1))
                continue
    raise last_err if last_err else RuntimeError("fetch failed: %s" % url)


def _g(tool: dict, *keys, default=None):
    for k in keys:
        if tool.get(k) is not None:
            return tool.get(k)
    return default


def _grade_cn(g) -> str:
    return GRADE_LABEL.get(g, str(g))


def _trunc(s, n=120):
    if s is None:
        return ""
    s = str(s).replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _as_int(v) -> int:
    try:
        return int(v or 0)
    except (TypeError, ValueError):
        return 0


def parse_ref(text: str) -> dict:
    """把用户输入解析为 slug / 搜索线索（SkillHub URL → 裸 slug）。"""
    raw = (text or "").strip()
    if not raw:
        return {"kind": "ambiguous", "note": "空输入"}

    if raw.startswith("skillhub:"):
        return {"kind": "slug", "slug": raw, "raw_slug": raw.split(":", 1)[1]}
    if raw.startswith("github:"):
        return {"kind": "slug", "slug": raw, "raw_slug": raw.split(":", 1)[1]}

    m = _SKILLHUB_RE.search(raw)
    if m:
        name = urllib.parse.unquote(m.group(2))
        return {
            "kind": "slug",
            "slug": "skillhub:%s" % name,
            "raw_slug": name,
            "source_url": "https://skillhub.cn/skills/%s/%s" % (m.group(1), m.group(2)),
            "note": "SkillHub 链接 → slug skillhub:%s" % name,
        }

    m = _GITHUB_RE.search(raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return {
            "kind": "slug",
            "slug": "github:%s/%s" % (owner, repo),
            "raw_slug": "%s/%s" % (owner, repo),
            "source_url": "https://github.com/%s/%s" % (owner, repo),
            "note": "GitHub 链接 → slug github:%s/%s" % (owner, repo),
        }

    return {"kind": "search", "keyword": raw, "source_url": None}


# ── 装前查数据访问 ───────────────────────────────────────────────────────
def get_catalog():
    """catalog.json → (tools: list[dict], exported_at)。列式文件，全量 11 万+。"""
    doc = fetch_json(DATA_ROOT + "catalog.json")
    if not doc or not isinstance(doc.get("rows"), list):
        return [], None
    cols = doc.get("cols", [])
    tools = []
    for row in doc["rows"]:
        o = dict(zip(cols, row))
        if o.get("summary") in (None, ""):
            fc = int(o.get("finding_count") or 0)
            o["summary"] = ("命中 %d 条证据" % fc) if fc > 0 else "暂未发现风险信号"
        tools.append(o)
    return tools, doc.get("exported_at")


def get_catalog_index():
    """catalog → {slug: tool}，供 find 交叉标注档位。"""
    tools, _exported_at = get_catalog()
    return {t.get("slug"): t for t in tools if t.get("slug")}


def get_tool_detail(slug: str):
    """tools/{shard}.json → {tool, findings, cve} 或 None。"""
    sh = "%03d" % shard_of(slug)
    doc = fetch_json(DATA_ROOT + "tools/%s.json" % sh)
    if not doc:
        return None
    tool = doc.get("tools", {}).get(slug)
    if not tool:
        return None
    return {
        "tool": tool,
        "findings": doc.get("findings", {}).get(slug, []),
        "cve": doc.get("cveFindings", {}).get(slug, []),
        "exported_at": doc.get("exported_at"),
    }


def get_authors():
    doc = fetch_json(DATA_ROOT + "authors.json")
    return (doc.get("authors", []) if doc else []), (doc.get("exported_at") if doc else None)


def get_tool_domains(slug: str):
    """tool_domains.json → 该 slug 的外联域名摘要；失败返回 None。"""
    url = DATA_ROOT + "tool_domains.json"
    cp = _cache_path(url)
    doc = None
    if os.path.exists(cp):
        try:
            with open(cp, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception:
            doc = None
    if doc is None:
        req = urllib.request.Request(url, headers={"User-Agent": "zqc-find-cli/1.0.0"})
        try:
            with urllib.request.urlopen(req, timeout=12) as r:
                doc = json.loads(r.read().decode("utf-8"))
            try:
                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cp, "w", encoding="utf-8") as f:
                    json.dump(doc, f)
            except Exception:
                pass
        except Exception:
            return None
    if not isinstance(doc, dict):
        return None
    td = doc.get("tool_domains") or {}
    return td.get(slug)


def detail_url(slug: str) -> str:
    return "%s/tool/%s" % (SITE_URL, urllib.parse.quote(str(slug), safe=""))


def _owasp_tags(finding: dict) -> list:
    raw = _g(finding, "owasp_category", default="") or ""
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def _print_privacy(findings: list, tool: dict, domains):
    exfil = [
        f for f in (findings or [])
        if _g(f, "rule_id") in EXFIL_RULES or "MCP04" in _owasp_tags(f)
    ]
    caps = _g(tool, "capabilities") or []
    priv_caps = []
    if isinstance(caps, list):
        for c in caps:
            if not isinstance(c, dict):
                continue
            name = str(c.get("capability") or "")
            if name in PRIVACY_CAPS or name.endswith("exfil") or "privacy" in name:
                priv_caps.append(c)

    print("隐私去向：")
    if domains and int(domains.get("total") or 0) > 0:
        total = int(domains.get("total") or 0)
        sus = int(domains.get("suspicious") or 0)
        off = int(domains.get("official_api") or 0)
        cdn = int(domains.get("cdn") or 0)
        print("  外联域名：共 %d（可疑 %d / 官方 %d / CDN %d）" % (total, sus, off, cdn))
        sample = domains.get("sample") or []
        shown = 0
        for ref in sample:
            if not isinstance(ref, dict):
                continue
            d = ref.get("domain") or ""
            if not d:
                continue
            cls = CLASS_CN.get(str(ref.get("classification") or ""), str(ref.get("classification") or ""))
            print("  - %s（%s）" % (d, cls))
            shown += 1
            if shown >= 5:
                break
        if total > shown:
            print("  …其余见详情页")
    elif exfil or priv_caps:
        print("  未见域名图谱抽样；检出可能涉及数据外传的信号（见下）。")
    else:
        print("  未见外传信号（当前规则与已公开域名摘要下）。")

    if exfil:
        print("  外传类证据 %d 条：" % len(exfil))
        for f in sorted(exfil, key=lambda x: SEV_RANK.get(_g(x, "severity"), 9))[:5]:
            print("  [%s] %s — %s" % (
                _g(f, "severity", default="—"),
                _g(f, "rule_id", default="?"),
                _trunc(_g(f, "evidence", default=""), 80),
            ))
    if priv_caps and not exfil:
        for c in priv_caps[:3]:
            label = c.get("label") or c.get("capability")
            ev = c.get("evidence")
            if isinstance(ev, list):
                ev = ev[0] if ev else ""
            print("  能力：%s — %s" % (label, _trunc(ev, 80)))


# ── 发现线：SkillHub API ────────────────────────────────────────────────
def sh_search(keyword: str, category: str | None = None, page_size: int = 5) -> list[dict]:
    """GET /api/skills 关键词分词搜索，返回归一化后的 skills 列表。"""
    params = {"keyword": keyword, "sortBy": "score", "pageSize": str(page_size)}
    if category:
        params["category"] = category
    url = SH_API + "/api/skills?" + urllib.parse.urlencode(params)
    try:
        payload = fetch_json(url, ttl=300)
    except Exception:
        return []
    if not isinstance(payload, dict) or payload.get("code") != 0:
        return []
    data = payload.get("data") or {}
    skills = data.get("skills") or []
    out = []
    for s in skills:
        if not isinstance(s, dict) or not s.get("slug"):
            continue
        labels = s.get("labels") or {}
        out.append({
            "slug": s.get("slug"),
            "name": s.get("name") or s.get("title") or s.get("slug"),
            "category": s.get("category"),
            "description_zh": s.get("description_zh") or s.get("description") or "",
            "downloads": _as_int(s.get("downloads")),
            "installs": _as_int(s.get("installs")),
            "stars": _as_int(s.get("stars")),
            "ownerName": s.get("ownerName") or "",
            "version": s.get("version"),
            "verified": bool(s.get("verified")) if s.get("verified") is not None else None,
            "requires_api_key": labels.get("requires_api_key"),
            "pricing_type": labels.get("pricing_type"),
            "source": s.get("source"),
            "labels": labels,
            "score": s.get("score"),
        })
    return out


def sh_detail(slug: str) -> dict | None:
    """GET /api/v1/skills/{slug} → 详情（含 securityReports 官方报告）。"""
    url = SH_API + "/api/v1/skills/" + urllib.parse.quote(str(slug), safe="")
    try:
        payload = fetch_json(url, ttl=600)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    skill = payload.get("skill") or {}
    sec = payload.get("securityReports") or {}
    out = {k: skill.get(k) for k in ("summary", "summary_zh", "tags", "subCategories")}
    out["securityReports"] = sec
    return out


# ── find：多关键词搜索 + 装前查档位合并 ──────────────────────────────────
def _merge_candidates(skill_rows: list[dict]) -> list[dict]:
    """SkillHub 多关键词命中 → 按 slug 去重合并（保留热度最高的版本）。"""
    merged: dict[str, dict] = {}
    for s in skill_rows:
        slug = s["slug"]
        cur = merged.get(slug)
        if cur is None:
            merged[slug] = s
            continue
        if _as_int(s.get("downloads")) + _as_int(s.get("installs")) > \
           _as_int(cur.get("downloads")) + _as_int(cur.get("installs")):
            if s.get("description_zh"):
                merged[slug] = s
    return list(merged.values())


def _author_repo_map():
    """authors.json → {display_name: {tool_count, red_count}}，best-effort。"""
    try:
        authors, _exported_at = get_authors()
    except Exception:
        return {}
    m = {}
    for a in authors:
        name = _g(a, "display_name")
        if name:
            m[str(name)] = a
    return m


def cmd_find(args):
    """多关键词搜索 SkillHub + 装前查档位标注，安全优先排序输出推荐。

    稳健性：SkillHub 实时搜索不可用时，自动退回「装前查目录检索」（安全层仍在）；
    两者都不可用才报错。
    """
    keywords = [args.keyword] + (args.kw or [])
    keywords = [k for k in keywords if k and k.strip()]
    if not keywords:
        print("缺少关键词。用法：find <关键词> [--kw 更多关键词]")
        return
    print("装前查 · 找技能")
    print("解析：关键词 = %s%s" % (
        " / ".join(keywords),
        " · 分类 = %s" % args.category if args.category else "",
    ))
    print("-" * 60)

    # 安全线先加载（无论发现线成败，都要交叉标注）
    zqc_index = {}
    zqc_tools = []
    zqc_exported = None
    try:
        zqc_tools, zqc_exported = get_catalog()
        zqc_index = {t.get("slug"): t for t in zqc_tools if t.get("slug")}
    except Exception:
        zqc_index = {}

    # 1) 发现线：多词搜 SkillHub，合并去重
    all_rows: list[dict] = []
    sh_fail = 0
    for kw in keywords:
        rows = sh_search(kw, category=args.category, page_size=args.page_size)
        if not rows:
            sh_fail += 1
        all_rows.extend(rows)
    candidates = _merge_candidates(all_rows)

    # 1b) 发现线降级：SkillHub 不可用/无命中 → 装前查目录本地检索（仍有档位）
    if not candidates and zqc_tools:
        print("SkillHub 实时搜索无命中或不可用，改用装前查目录检索（档位标注不受影响）。")
        for kw in keywords:
            kl = kw.lower().strip()
            for t in zqc_tools:
                if not isinstance(t, dict):
                    continue
                hay = " ".join([
                    str(t.get("name") or ""),
                    str(t.get("slug") or ""),
                    str(t.get("author") or ""),
                ]).lower()
                if kl and kl in hay and t.get("source") == "skillhub":
                    candidates.append({
                        "slug": str(t.get("slug", "")).replace("skillhub:", "", 1),
                        "name": t.get("name"),
                        "category": t.get("category"),
                        "description_zh": t.get("summary") or "",
                        "downloads": _as_int(t.get("downloads")),
                        "installs": _as_int(t.get("install_count")),
                        "stars": 0,
                        "ownerName": t.get("author") or "",
                        "version": None,
                        "verified": None,
                        "requires_api_key": None,
                        "pricing_type": None,
                        "source": "skillhub",
                        "labels": {},
                        "score": None,
                        "zqc": t,
                        "zqc_slug": t.get("slug"),
                        "grade": t.get("grade") or "unknown",
                        "finding_count": _as_int(t.get("finding_count")),
                        "top_severity": t.get("top_severity"),
                        "zqc_author": t.get("author"),
                        "zqc_install_count": _as_int(t.get("install_count")),
                        "zqc_downloads": _as_int(t.get("downloads")),
                    })
        candidates = _merge_candidates(candidates)

    if not candidates:
        print("未找到匹配候选（SkillHub 与装前查目录均无命中/不可用）。")
        return

    # 2) 交叉标注档位（SkillHub 命中侧）
    authors_map = _author_repo_map()
    for c in candidates:
        if c.get("zqc"):
            continue  # 目录降级路径已自带
        zslug = "skillhub:%s" % c["slug"]
        zt = zqc_index.get(zslug)
        if zt:
            c["zqc"] = zt
            c["zqc_slug"] = zslug
            c["grade"] = zt.get("grade") or "unknown"
            c["finding_count"] = _as_int(zt.get("finding_count"))
            c["top_severity"] = zt.get("top_severity")
            c["zqc_author"] = zt.get("author")
            c["zqc_install_count"] = _as_int(zt.get("install_count"))
            c["zqc_downloads"] = _as_int(zt.get("downloads"))
            if not c.get("ownerName") and zt.get("author"):
                c["ownerName"] = zt.get("author")
        else:
            c["zqc"] = None
            c["grade"] = None
            c["finding_count"] = 0
            c["top_severity"] = None

    # 3) 安全优先排序：green/yellow 优先 → 未收录/待评估 → orange → red；
    #    同档按「热度 + 命中关键词数」降序
    def heat(c):
        return _as_int(c.get("downloads")) + _as_int(c.get("installs")) + \
               _as_int(c.get("zqc_install_count")) + _as_int(c.get("zqc_downloads"))

    def kw_hit(c):
        n = 0
        for kw in keywords:
            k = kw.lower()
            if k in str(c.get("name", "")).lower() or k in str(c.get("description_zh", "")).lower():
                n += 1
        return n

    candidates.sort(
        key=lambda c: (
            GRADE_RANK_FIND.get(c.get("grade"), 9),
            -heat(c),
            -kw_hit(c),
            c.get("slug", ""),
        )
    )

    if args.safe_only:
        candidates = [c for c in candidates if c.get("grade") in ("green", "yellow")]
    if args.free_only:
        candidates = [
            c for c in candidates
            if str(c.get("requires_api_key", "")).lower() not in ("true", "1")
        ]

    # 4) 输出
    shown = 0
    green_yellow = [c for c in candidates if c.get("grade") in ("green", "yellow")]
    others = [c for c in candidates if c.get("grade") not in ("green", "yellow")]
    ordered = green_yellow + others
    for c in ordered[: args.limit]:
        shown += 1
        g = c.get("grade")
        zt = c.get("zqc")
        if g == "green":
            badge = "🟢 未见风险"
        elif g == "yellow":
            badge = "🟡 观察"
        elif g == "orange":
            badge = "🟠 谨慎"
        elif g == "red":
            badge = "🔴 高风险"
        elif zt is not None:
            badge = "⚪ 待评估"
        else:
            badge = "⚪ 装前查未收录"

        line = "%d. %s  %s" % (shown, _trunc(c.get("name", "?"), 48), badge)
        extra = []
        if c.get("finding_count"):
            extra.append("证据 %d 条%s" % (
                c["finding_count"],
                ("（最高 %s）" % c["top_severity"]) if c.get("top_severity") else "",
            ))
        if extra:
            line += " · " + " · ".join(extra)
        print(line)

        desc = c.get("description_zh") or ""
        if desc:
            print("   用途：%s" % _trunc(desc, 150))
        if c.get("grade") == "red" and c.get("zqc"):
            print("   关键信号：%s" % _trunc(str(c["zqc"].get("summary") or ""), 120))

        author = c.get("ownerName") or (zt or {}).get("author")
        ar = ""
        if author:
            arow = authors_map.get(str(author))
            if arow:
                ar = "（共 %s 工具 · 红 %s）" % (
                    _g(arow, "tool_count", default="—"),
                    _g(arow, "red_count", default=0),
                )
        hot = "热度：下载 %s%s" % (
            c.get("downloads") or c.get("zqc_downloads") or 0,
            (" · 作者 %s%s" % (author, ar)) if author else "",
        )
        print("   %s" % hot)
        print("   主页：%s/skills/%s" % (SH_WEB, c.get("slug")))
        if zt:
            print("   装前查：%s" % detail_url("skillhub:%s" % c.get("slug")))
        else:
            print("   注：装前查暂未收录，无独立安全评估，安装风险请自行判断。")
        print()

    if shown == 0:
        print("没有符合条件的候选（试去掉 --safe-only / --free-only 再看）。")
        return

    print("-" * 60)
    print("说明：")
    print("  - 🟢/🟡 可安全安装；🟠/🔴 安装前请先看证据再决定。")
    print("  - 排序 = 安全档位优先（绿/黄在前），同档按热度与关键词命中度。")
    if zqc_exported:
        print("  - 装前查数据截至：%s" % str(zqc_exported)[:19])
    print("  - 看单个工具安全详情：python3 scripts/zqc_find_cli.py inspect <slug>")


# ── inspect：单工具安全详情 ──────────────────────────────────────────────
def cmd_inspect(args):
    ref = parse_ref(args.slug)
    slug = None
    source_hint = ref.get("source_url")

    if ref["kind"] == "slug" and ref.get("slug"):
        slug = ref["slug"]
    else:
        # 关键词：先在 SkillHub 搜，再对 top 候选交叉装前查档位
        kw = ref.get("keyword") or args.slug
        rows = sh_search(kw, page_size=5)
        if not rows:
            print("SkillHub 搜索无命中（%s）。" % kw)
            return
        zqc_index = {}
        try:
            zqc_index = get_catalog_index()
        except Exception:
            pass
        cands = []
        for r in rows:
            zt = zqc_index.get("skillhub:%s" % r["slug"])
            cands.append((r, zt))
        cands.sort(key=lambda x: GRADE_RANK_FIND.get(
            (x[1] or {}).get("grade"), 9))
        print("「%s」候选（按装前查档位优先排序）：" % kw)
        for i, (r, zt) in enumerate(cands[:8], 1):
            g = (zt or {}).get("grade")
            badge = _grade_cn(g) if g else "未收录"
            print("  %d. %s  %s  %s" % (i, _trunc(r.get("name", "?"), 30), badge, r["slug"]))
        print("用 `inspect <slug>` 查看指定候选的安全详情。")
        return

    d = get_tool_detail(slug)
    if not d:
        print("装前查未收录该工具（slug=%s）。" % slug)
        print("提示：可先用装前查 Skill（/装前查）触发按需扫描，收录后再来 inspect。")
        return

    t = d["tool"]
    findings = d["findings"] or []
    cve = d["cve"] or []
    g = _g(t, "grade", default="unknown")
    print("=" * 60)
    print("工具：%s" % _g(t, "name", default=slug))
    print("slug：%s" % slug)
    print("装前查评级：%s（%s）" % (_grade_cn(g), g))
    basis = _g(t, "grade_evidence_basis")
    if basis:
        print("证据依据：%s" % BASIS_CN.get(str(basis), str(basis)))
    if _g(t, "ungated"):
        print("标记：证据待取证（档位可能尚不完整）")
    print("作者：%s    来源：%s" % (_g(t, "author", default="匿名"), _g(t, "source", default="—")))
    url = _g(t, "source_url") or source_hint
    if url:
        print("来源链接：%s" % url)
    if _g(t, "description"):
        print("简介：%s" % _trunc(_g(t, "description"), 200))
    print("证据数：%s    最高严重度：%s" % (_g(t, "finding_count", default=0), _g(t, "top_severity", default="—")))
    at = _g(t, "author_tools")
    ar = _g(t, "author_reds")
    if at is not None:
        print("作者信誉：共 %s 个工具 · 其中高风险 %s" % (at, ar if ar is not None else "—"))
    if g in ("red", "orange"):
        print("⚠ 该工具被评为「%s」，安装前请确认你接受其权限范围与数据去向。" % _grade_cn(g))
    print("更多细节：%s" % detail_url(slug))
    print("-" * 60)
    domains = get_tool_domains(slug) if slug else None
    _print_privacy(findings, t, domains)
    print("-" * 60)
    if findings:
        print("评估证据（前 %d 条）：" % min(len(findings), args.limit))
        for f in sorted(findings, key=lambda x: SEV_RANK.get(_g(x, "severity"), 9))[: args.limit]:
            print("  [%s] %s — %s" % (
                _g(f, "severity", default="—"),
                _g(f, "rule_id", default="?"),
                _trunc(_g(f, "evidence", default=""), 100),
            ))
    else:
        print("暂未公开具体证据条目（现有规则下未见命中，或证据尚未公开）。")
    if cve:
        print("-" * 60)
        print("关联 CVE（%d）：" % len(cve))
        for c in cve[: args.limit]:
            print("  %s [%s] %s" % (
                _g(c, "cve_id"), _g(c, "severity", default="?"),
                _trunc(_g(c, "description"), 80),
            ))
    print("=" * 60)
    print("装前查基于公开代码与声明独立评估，结论不构成担保。")


# ── install：安装闸门 ────────────────────────────────────────────────────
def _resolve_grade(raw_slug: str) -> tuple[str, dict | None]:
    """查装前查该工具档位。返回 (grade, detail)。grade 可能为 None=未收录。"""
    zslug = "skillhub:%s" % raw_slug
    try:
        d = get_tool_detail(zslug)
    except Exception:
        d = None
    if d:
        return _g(d["tool"], "grade", default="unknown"), d
    # 目录兜底（部分新工具可能未进详情分片但进了 catalog）
    try:
        idx = get_catalog_index()
    except Exception:
        idx = {}
    zt = idx.get(zslug)
    if zt:
        return (zt.get("grade") or "unknown"), None
    return None, None


def cmd_install(args):
    ref = parse_ref(args.slug)
    raw_slug = ref.get("raw_slug")
    if not raw_slug or ref["kind"] != "slug":
        print("无法解析 slug（支持 skillhub:<slug> 或 SkillHub 链接）。输入：%s" % args.slug)
        return
    if not args.dir:
        print("必须指定 --dir（当前 Agent 的 skills 目录）。")
        print("例：python3 scripts/zqc_find_cli.py install %s --dir ~/.cursor/skills" % raw_slug)
        return

    grade, detail = _resolve_grade(raw_slug)
    zslug = "skillhub:%s" % raw_slug

    print("装前查 · 安装闸门")
    print("工具：%s" % raw_slug)
    if grade is None:
        print("档位：⚪ 装前查未收录 — 无独立安全评估，安装风险请自行判断。")
    else:
        print("档位：%s（%s）" % (_grade_cn(grade), grade))
        if detail:
            t = detail["tool"]
            print("证据数：%s    最高严重度：%s" % (
                _g(t, "finding_count", default=0), _g(t, "top_severity", default="—")))
            print("更多细节：%s" % detail_url(zslug))

    # 闸门：red / orange 必须确认；unknown 也要提示
    if grade in ("red", "orange") and not args.yes:
        print()
        print("⛔ 该工具为「%s」，安装前必须确认。" % _grade_cn(grade))
        if detail and detail["findings"]:
            print("  关键证据：")
            for f in sorted(detail["findings"], key=lambda x: SEV_RANK.get(_g(x, "severity"), 9))[:5]:
                print("    [%s] %s — %s" % (
                    _g(f, "severity", default="—"),
                    _g(f, "rule_id", default="?"),
                    _trunc(_g(f, "evidence", default=""), 90),
                ))
        print()
        print("请先向用户确认「已了解该工具权限范围与数据去向，仍要安装」；")
        print("确认后重跑：python3 scripts/zqc_find_cli.py install %s --dir %s --yes" % (raw_slug, args.dir))
        sys.exit(3)

    # 检查 skillhub CLI
    has_cli = False
    try:
        r = subprocess.run(["command", "-v", "skillhub"], capture_output=True, text=True, timeout=10)
        has_cli = bool(r.stdout.strip())
    except Exception:
        has_cli = False
    if not has_cli:
        print()
        print("未检测到 skillhub CLI，先安装 CLI（仅 CLI，不装默认 Skill）…")
        cmd = ("curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh "
               "| bash -s -- --cli-only")
        try:
            subprocess.run(cmd, shell=True, check=True, timeout=120)
        except Exception as e:
            print("CLI 安装失败：%s" % e)
            print("可手动执行：%s" % cmd)
            sys.exit(4)
        print("skillhub CLI 已安装。")

    print()
    print("开始安装 %s → %s …" % (raw_slug, args.dir))
    try:
        r = subprocess.run(
            ["skillhub", "install", raw_slug, "--dir", args.dir],
            capture_output=True, text=True, timeout=180,
        )
    except FileNotFoundError:
        print("skillhub 命令不存在，请先安装 CLI。")
        sys.exit(4)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip() or "(无输出)")
    if r.returncode == 0:
        print("✅ %s 已安装" % raw_slug)
        if grade == "unknown":
            print("提示：装前查对该工具评级为「待评估」，建议使用后留意其行为。")
        sys.exit(0)
    print("安装失败（exit=%s）。" % r.returncode)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser(description="装前查 · 找技能 CLI 1.0.0（安全优先查找/安装 Skill）")
    sub = p.add_subparsers(dest="cmd")

    pf = sub.add_parser("find", help="多关键词搜索 SkillHub + 装前查档位标注")
    pf.add_argument("keyword", help="主关键词（如：周报）")
    pf.add_argument("--kw", action="append", default=[], help="更多候选词（可多次）")
    pf.add_argument("--category", default=None, help="一级分类 key（见 references/categories.md）")
    pf.add_argument("--limit", type=int, default=8)
    pf.add_argument("--page-size", type=int, default=5)
    pf.add_argument("--safe-only", action="store_true", help="只保留 green/yellow")
    pf.add_argument("--free-only", action="store_true", help="只保留无需 API Key 的免费项")

    pi = sub.add_parser("inspect", help="查看单个工具的安全详情（slug 或 SkillHub 链接）")
    pi.add_argument("slug", help="skillhub:<slug>、SkillHub/GitHub 链接或关键词")
    pi.add_argument("--limit", type=int, default=15)

    pinst = sub.add_parser("install", help="安装 Skill（含安全闸门）")
    pinst.add_argument("slug", help="skillhub:<slug> 或 SkillHub 链接")
    pinst.add_argument("--dir", default=os.environ.get("ZQC_SKILLS_DIR", ""), help="skills 目录（必须）")
    pinst.add_argument("--yes", action="store_true", help="跳过 red/orange 确认闸门（已向用户确认后使用）")

    args = p.parse_args()
    if args.cmd == "find":
        cmd_find(args)
    elif args.cmd == "inspect":
        cmd_inspect(args)
    elif args.cmd == "install":
        cmd_install(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
