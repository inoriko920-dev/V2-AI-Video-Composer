"""Archive GitHub repository metadata for ONE repo, read-only. Never archive secret values."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile

REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
ROOT = Path("github_metadata_export")
BASE = "https://api.github.com/repos/" + REPO
ROOT.mkdir(parents=True, exist_ok=True)
errors: list[dict] = []
counts: dict[str, int] = {}
secrets_redacted = [0]
patterns = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"sk-[0-9A-Za-z_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{12,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ya29\.[0-9A-Za-z_-]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\\s\\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(authorization\\s*:\\s*(?:bearer|token)\\s+)[^\\s,;\\\"]+"),
]

def clean(obj):
    if isinstance(obj, str):
        for pat in patterns:
            obj, count = pat.subn("[REDACTED_SECRET]", obj)
            secrets_redacted[0] += count
        return obj
    if isinstance(obj, list):
        return [clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    return obj

def write(rel, obj):
    dest = ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(clean(obj), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def get(endpoint):
    url = endpoint if endpoint.startswith("http") else BASE + endpoint
    for attempt in range(4):
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + TOKEN,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "one-repo-backup-export"
        })
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404, 422):
                errors.append({"endpoint": endpoint, "status": exc.code, "message": str(exc)})
                return None
            if exc.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            errors.append({"endpoint": endpoint, "status": exc.code, "message": str(exc)})
            return None
        except Exception as exc:
            if attempt < 3:
                time.sleep(2 ** attempt)
                continue
            errors.append({"endpoint": endpoint, "status": "network", "message": str(exc)})
            return None

def all_pages(endpoint, key=None, cap=5000):
    out = []
    page = 1
    while len(out) < cap:
        joiner = "&" if "?" in endpoint else "?"
        res = get(endpoint + joiner + "per_page=100&page=" + str(page))
        if res is None:
            break
        items = res.get(key, []) if key and isinstance(res, dict) else res
        if not isinstance(items, list):
            errors.append({"endpoint": endpoint, "status": "unexpected_schema"})
            break
        out.extend(items)
        if len(items) < 100:
            break
        page += 1
    return out[:cap]

def archive_collection(name, endpoint, key=None):
    value = all_pages(endpoint, key)
    write("COLLECTIONS/" + name + ".json", value)
    counts[name] = len(value)
    print(name + "=" + str(len(value)), flush=True)
    return value

def optional_object(name, endpoint):
    value = get(endpoint)
    if value is not None:
        write("SETTINGS/" + name + ".json", value)
    return value

now = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).isoformat()
optional_object("repository", "")
optional_object("topics", "/topics")
optional_object("languages", "/languages")
optional_object("branch_main", "/branches/main")
optional_object("actions_permissions", "/actions/permissions")
optional_object("actions_workflow_permissions", "/actions/permissions/workflow")
optional_object("environments", "/environments")
optional_object("rulesets", "/rulesets")
optional_object("main_protection", "/branches/main/protection")

branches = archive_collection("branches", "/branches")
tags = archive_collection("tags", "/tags")
labels = archive_collection("labels", "/labels")
milestones = archive_collection("milestones", "/milestones?state=all")
releases = archive_collection("releases", "/releases")
issues = archive_collection("issues_and_pr_issue_views", "/issues?state=all")
prs = archive_collection("pull_requests", "/pulls?state=all")
workflows = archive_collection("actions_workflows", "/actions/workflows", "workflows")
runs = archive_collection("actions_workflow_runs", "/actions/runs", "workflow_runs")
artifacts = archive_collection("actions_artifact_index", "/actions/artifacts", "artifacts")
for rel in releases:
    n = rel["id"]
    optional_object("release_" + str(n), "/releases/" + str(n))
    write("RELEASES/release_" + str(n) + "_assets_metadata.json", all_pages("/releases/" + str(n) + "/assets"))
for issue in issues:
    n = issue["number"]
    d = "ISSUES_AND_PR_DISCUSSIONS/issue_" + str(n).zfill(4) + "/"
    write(d + "issue_metadata.json", get("/issues/" + str(n)) or issue)
    write(d + "comments.json", all_pages("/issues/" + str(n) + "/comments"))
    write(d + "events.json", all_pages("/issues/" + str(n) + "/events"))
for pr in prs:
    n = pr["number"]
    d = "PULL_REQUESTS/pr_" + str(n).zfill(4) + "/"
    write(d + "pull_request.json", get("/pulls/" + str(n)) or pr)
    for title, suffix in [
        ("review_comments", "/comments"),
        ("reviews", "/reviews"),
        ("changed_files", "/files"),
        ("commits", "/commits"),
    ]:
        write(d + title + ".json", all_pages("/pulls/" + str(n) + suffix))
for run in runs:
    run_id = run["id"]
    d = "ACTIONS_RUNS/run_" + str(run_id) + "/"
    write(d + "summary.json", run)
    # Run metadata and every accessible job/step record, not unbounded logs.
    write(d + "jobs.json", all_pages("/actions/runs/" + str(run_id) + "/jobs", "jobs"))
    write(d + "artifacts.json", all_pages("/actions/runs/" + str(run_id) + "/artifacts", "artifacts"))

write("EXPORT_ERRORS_AND_LIMITATIONS.json", errors)
write("EXPORT_COUNTS.json", counts)
readme = """GITHUB METADATA ARCHIVE - ONE REPOSITORY ONLY
Repository: """ + REPO + """
Snapshot WIB: """ + now + """

Includes accessible issue/PR conversation history, comments, reviews, changed-file lists,
release and release-assets metadata, Actions run/job/artifact METADATA, and repository settings.
Full Actions raw logs, secrets, account-wide settings, actual older release binary bytes,
webhooks, PR review threads, and exact GitHub IDs/account state are NOT guaranteed.
Git refs and source live in the existing verified Git Bundle and source ZIP.
Never attempt to upload this archive to GitHub as if it were a Git Bundle.
REST restoring issue/PR JSON cannot preserve immutable GitHub IDs, timestamps,
GitHub Actions run history, or exact old comment authorship.
Secrets are NOT archived. Some API endpoints may be denied, see EXPORT_ERRORS_AND_LIMITATIONS.json.
"""
(ROOT / "README_METADATA_RESTORE.txt").write_text(readme, encoding="utf-8")
index = {"repo": REPO, "snapshot_wib": now, "counts": counts,
         "errors": len(errors), "redaction_matches": secrets_redacted[0],
         "scope": "single-repository-only"}
write("EXPORT_STATUS.json", index)
# Ensure no token leak even if an API response carried a literal secret in an unexpected field.
raw_token = TOKEN.encode()
for p in ROOT.rglob("*"):
    if p.is_file() and raw_token in p.read_bytes():
        raise SystemExit("ERROR: GitHub workflow token accidentally contained in export")
if len(prs) == 0 or len(runs) == 0 or len(releases) == 0:
    raise SystemExit("ERROR: essential GitHub metadata empty")
with zipfile.ZipFile("GITHUB-METADATA-" + REPO.split("/")[1] + ".zip", "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as z:
    for p in ROOT.rglob("*"):
        if p.is_file():
            z.write(p, p.as_posix())
print("METADATA_BACKUP_PASS", json.dumps(index, ensure_ascii=False), flush=True)
