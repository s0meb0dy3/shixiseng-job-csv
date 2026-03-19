#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from typing import Any


EVAL_JS = r"""JSON.stringify({title: document.title, text: document.body.innerText, url: location.href})"""


def run_agent_browser(session: str, *args: str) -> str:
    env = os.environ.copy()
    env["AGENT_BROWSER_SESSION"] = session
    proc = subprocess.run(["agent-browser", *args], capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "agent-browser command failed")
    return proc.stdout.strip()


def load_manifest(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    rows: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str):
            rows.append({"url": item, "source_page": "", "search_keyword": ""})
            continue
        rows.append(
            {
                "url": item.get("url", ""),
                "source_page": item.get("source_page", ""),
                "search_keyword": item.get("search_keyword", ""),
            }
        )
    return [row for row in rows if row["url"]]


def compact_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_between(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    segment = text.split(start, 1)[1]
    if end in segment:
        segment = segment.split(end, 1)[0]
    return " ".join(line.strip() for line in segment.splitlines() if line.strip())


def parse_title_company(page_title: str) -> tuple[str, str]:
    match = re.match(r"^(.*?)(?:实习招聘|校招招聘)?-(.*?)(?:实习生招聘)?-实习僧$", page_title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return page_title.replace("-实习僧", "").strip(), ""


def parse_page_fields(payload: dict[str, str], manifest_row: dict[str, Any]) -> dict[str, str]:
    page_title = payload.get("title", "")
    text = payload.get("text", "")
    lines = compact_lines(text)

    title, company = parse_title_company(page_title)
    refresh_time = ""
    salary = ""
    city = ""
    education = ""
    attendance = ""
    duration = ""
    benefits = ""
    deadline = ""
    location = ""
    company_description = ""
    job_description = extract_between(text, "职位描述：", "投递要求：")

    for idx, line in enumerate(lines):
        if not refresh_time and re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} 刷新", line):
            refresh_time = line.replace(" 刷新", "")
            if idx + 1 < len(lines):
                info_match = re.match(r"^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(.*))?$", lines[idx + 1])
                if info_match:
                    salary = info_match.group(1)
                    city = info_match.group(2)
                    education = info_match.group(3)
                    attendance = info_match.group(4)
                    duration = info_match.group(5)
                    benefits = (info_match.group(6) or "").strip()
            if idx + 2 < len(lines):
                tail = lines[idx + 2]
                if tail not in {"扫码手机查看", "投个简历", "职位描述："} and "职位描述" not in tail:
                    benefits = "; ".join(filter(None, [benefits, tail])).strip("; ")
        if line == "截止日期：" and idx + 1 < len(lines):
            deadline = lines[idx + 1]
        if line == "工作地点：" and idx + 1 < len(lines):
            location = lines[idx + 1]
        if line == "公司简介":
            if idx + 1 < len(lines) and not company:
                company = lines[idx + 1]
            if idx + 2 < len(lines):
                company_description = lines[idx + 2].strip("“”\"")
            break

    return {
        "search_keyword": str(manifest_row.get("search_keyword", "")),
        "source_page": str(manifest_row.get("source_page", "")),
        "title": title,
        "company": company,
        "refresh_time": refresh_time,
        "salary": salary,
        "city": city,
        "education": education,
        "attendance": attendance,
        "duration": duration,
        "benefits": benefits,
        "deadline": deadline,
        "location": location,
        "company_description": company_description,
        "job_description": job_description,
        "url": payload.get("url", manifest_row["url"]),
    }


def fetch_payload(session: str, url: str) -> dict[str, str]:
    run_agent_browser(session, "open", url)
    run_agent_browser(session, "wait", "1500")
    output = run_agent_browser(session, "eval", EVAL_JS)
    return json.loads(json.loads(output.splitlines()[-1]))


def write_csv(rows: list[dict[str, str]], output_path: str) -> None:
    fieldnames = [
        "search_keyword",
        "source_page",
        "title",
        "company",
        "refresh_time",
        "salary",
        "city",
        "education",
        "attendance",
        "duration",
        "benefits",
        "deadline",
        "location",
        "company_description",
        "job_description",
        "url",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Shixiseng job detail pages to CSV using agent-browser.")
    parser.add_argument("manifest", help="JSON file with job URLs. Each item may be a URL string or an object with url/source_page/search_keyword.")
    parser.add_argument("--output", required=True, help="Destination CSV path.")
    parser.add_argument("--session", default="shixiseng-export", help="agent-browser session name.")
    args = parser.parse_args()

    manifest_rows = load_manifest(args.manifest)
    parsed_rows: list[dict[str, str]] = []

    for idx, item in enumerate(manifest_rows, start=1):
        url = item["url"]
        print(f"[{idx}/{len(manifest_rows)}] {url}", file=sys.stderr)
        try:
            payload = fetch_payload(args.session, url)
            parsed_rows.append(parse_page_fields(payload, item))
        except Exception as exc:
            print(f"Failed: {url} -> {exc}", file=sys.stderr)
            parsed_rows.append(
                {
                    "search_keyword": str(item.get("search_keyword", "")),
                    "source_page": str(item.get("source_page", "")),
                    "title": "",
                    "company": "",
                    "refresh_time": "",
                    "salary": "",
                    "city": "",
                    "education": "",
                    "attendance": "",
                    "duration": "",
                    "benefits": "",
                    "deadline": "",
                    "location": "",
                    "company_description": "",
                    "job_description": "",
                    "url": url,
                }
            )

    write_csv(parsed_rows, args.output)
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
