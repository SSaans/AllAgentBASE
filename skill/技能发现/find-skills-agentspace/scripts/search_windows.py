#!/usr/bin/env python3
"""Local Windows adapter: anonymous, read-only public skill discovery.

Uses Python's standard library. It neither reads credential files nor installs,
downloads, or executes skill content. It does not perform the upstream script's
heuristic security scan. Search results are untrusted metadata requiring review.
"""

import argparse
import concurrent.futures
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


USER_AGENT = "Codex-ReadOnly-Skill-Discovery/1.0"
SOURCES = ("skills-sh", "clawhub", "github")
TOPICS = ("claude-skills", "agent-skills", "claude-code-skills")
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class SearchFailure(Exception):
    def __init__(self, details):
        super().__init__(details["message"])
        self.details = details


def fetch_json(base_url, parameters):
    """GET public JSON with no Authorization header or credential lookup."""
    url = base_url + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("Response exceeded the 8 MiB safety limit")
            data = json.loads(body.decode("utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")
            return data, url
    except urllib.error.HTTPError as error:
        body = error.read(4096).decode("utf-8", errors="replace")
        try:
            message = json.loads(body).get("message", str(error))
        except (ValueError, AttributeError):
            message = str(error)
        remaining = error.headers.get("X-RateLimit-Remaining")
        rate_limited = error.code == 429 or (
            error.code == 403
            and (remaining == "0" or "rate limit" in str(message).lower())
        )
        raise SearchFailure({
            "url": url,
            "status": "rate_limited" if rate_limited else "http_error",
            "http_status": error.code,
            "message": str(message),
            "rate_limit_remaining": remaining,
            "rate_limit_reset_unix": error.headers.get("X-RateLimit-Reset"),
            "retry_after": error.headers.get("Retry-After"),
        }) from error
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        raise SearchFailure({
            "url": url, "status": "error", "message": str(error)
        }) from error


def match_percent(query, name, summary):
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    haystack = (str(name or "") + " " + str(summary or "")).lower()
    return round(100 * sum(token in haystack for token in tokens) / len(tokens)) if tokens else None


def unscanned(item):
    item["security_scan"] = "not_performed"
    return item


def search_skills_sh(query, limit):
    data, url = fetch_json("https://skills.sh/api/search", {"q": query, "limit": limit})
    rows = data.get("skills")
    if not isinstance(rows, list):
        raise SearchFailure({"url": url, "status": "schema_error", "message": "Missing skills array"})
    items = []
    for row in rows[:limit]:
        repo = row.get("source")
        slug = row.get("skillId") or row.get("name")
        items.append(unscanned({
            "registry": "skills.sh", "name": row.get("name") or slug,
            "slug": slug, "repo": repo, "summary": row.get("description"),
            "url": "https://skills.sh/" + str(repo) + "/" + str(slug),
            "installs": row.get("installs"),
            "raw_source": {"source": repo, "id": row.get("id"), "skillId": row.get("skillId")},
        }))
    return {"status": "ok", "endpoints": [url], "ranking": "API search order", "items": items}


def search_clawhub(query, limit):
    data, url = fetch_json("https://clawhub.ai/api/search", {"q": query, "limit": limit})
    rows = data.get("results")
    if not isinstance(rows, list):
        raise SearchFailure({"url": url, "status": "schema_error", "message": "Missing results array"})
    items = []
    for row in rows[:limit]:
        native_skill = (row.get("native") or {}).get("skill") or {}
        stats = native_skill.get("stats") or {}
        links = row.get("links") or {}
        canonical = row.get("canonicalUrl") or links.get("canonical")
        owner = row.get("ownerHandle") or (row.get("owner") or {}).get("handle")
        slug = row.get("slug") or native_skill.get("slug")
        if not canonical and owner and slug:
            canonical = "/" + str(owner) + "/skills/" + str(slug)
        items.append(unscanned({
            "registry": "clawhub", "name": row.get("displayName") or slug,
            "slug": slug, "owner": owner,
            "url": urllib.parse.urljoin("https://clawhub.ai", canonical) if canonical else None,
            "summary": row.get("summary") or native_skill.get("summary"),
            "installs": stats.get("installsAllTime", stats.get("installs")),
            "downloads": row.get("downloads", stats.get("downloads")),
            "stars": stats.get("stars"), "version": row.get("version"),
            "updated_at": row.get("updatedAt", native_skill.get("updatedAt")),
            "raw_source": {"source": row.get("source"), "id": row.get("id"),
                           "sourceIdentity": row.get("sourceIdentity"),
                           "install": row.get("install"), "links": links,
                           "stats": stats},
        }))
    return {"status": "ok", "endpoints": [url], "ranking": "API search order", "items": items}


def search_github(query, limit):
    # Match upstream's first-keyword + three-topic discovery scope.
    keyword = query.split()[0]
    items_by_repo = {}
    endpoints, errors = [], []
    incomplete = False
    for topic in TOPICS:
        try:
            data, url = fetch_json("https://api.github.com/search/repositories", {
                "q": keyword + " topic:" + topic, "per_page": limit,
            })
            endpoints.append(url)
            rows = data.get("items")
            if not isinstance(rows, list):
                raise SearchFailure({"url": url, "status": "schema_error", "message": "Missing items array"})
            incomplete = incomplete or bool(data.get("incomplete_results"))
            for row in rows:
                repo = row.get("full_name")
                if not repo:
                    continue
                if repo in items_by_repo:
                    items_by_repo[repo]["matched_topics"].append(topic)
                    continue
                items_by_repo[repo] = unscanned({
                    "registry": "github", "name": repo, "repo": repo,
                    "url": row.get("html_url"), "summary": row.get("description"),
                    "stars": row.get("stargazers_count"), "updated_at": row.get("updated_at"),
                    "archived": row.get("archived"), "matched_topics": [topic],
                    "match_percent": match_percent(query, repo, row.get("description")),
                    "raw_source": {"id": row.get("id"), "full_name": repo,
                                   "api_url": row.get("url"), "topics": row.get("topics")},
                })
        except SearchFailure as error:
            errors.append(dict(error.details, topic=topic))
            if error.details["status"] == "rate_limited":
                break
    items = sorted(items_by_repo.values(), key=lambda item: (
        -(item["match_percent"] or 0), -(item["stars"] or 0)
    ))[:limit]
    status = "partial" if (errors or incomplete) and endpoints else "ok"
    if errors and not endpoints:
        status = errors[0]["status"]
    return {"status": status, "endpoints": endpoints, "errors": errors,
            "keyword_used": keyword, "topics": list(TOPICS), "anonymous": True,
            "incomplete_results": incomplete,
            "ranking": "ASCII keyword coverage, then repository stars; not a quality score",
            "items": items}


def search_one(source, query, limit):
    started = time.monotonic()
    try:
        result = {"skills-sh": search_skills_sh, "clawhub": search_clawhub, "github": search_github}[source](query, limit)
    except SearchFailure as error:
        result = {"status": error.details["status"], "errors": [error.details], "items": []}
    except Exception as error:
        result = {"status": "error", "errors": [{"message": str(error)}], "items": []}
    result.update(source=source, count=len(result["items"]), elapsed_ms=round(1000 * (time.monotonic() - started)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Public search terms only; do not include private note contents")
    parser.add_argument("--source", choices=(*SOURCES, "all"), default="all")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results per source, 1-50 (default 10)")
    args = parser.parse_args()
    query = args.query.strip()
    if not query:
        parser.error("query must not be empty")
    if not 1 <= args.limit <= 50:
        parser.error("--limit must be between 1 and 50")
    sources = SOURCES if args.source == "all" else (args.source,)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources)) as pool:
        results = list(pool.map(lambda source: search_one(source, query, args.limit), sources))
    output = {"query": query, "limit": args.limit, "read_only": True,
              "security_scan": "not_performed",
              "notice": "Metadata only. Read original SKILL.md and bundled scripts before recommending or installing. This adapter does not run upstream heuristic scans, inspect installed skills, or install anything.",
              "sources": results}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if any(result["status"] in ("ok", "partial") for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
