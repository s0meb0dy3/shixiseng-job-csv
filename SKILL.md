---
name: shixiseng-job-csv
description: Extract internship or campus-job listings from Shixiseng with agent-browser and write structured CSV files. Use when the user wants to search 实习僧, scrape public job pages, export positions into CSV, collect fields such as title/salary/location/description/company, or turn a manual browsing workflow on 实习僧 into a repeatable data-extraction task.
---

# Shixiseng Job Csv

Use `agent-browser` for navigation and extraction. Prefer a dedicated browser session for scraping; `--auto-connect` is acceptable for inspection, but it is less stable if the user changes tabs.

Prerequisites:

- `agent-browser` is installed and available in `PATH`.
- `python3` is available for the bundled export script.

## Workflow

Before collecting paginated results, decide the page count with this rule:

- If the user explicitly specifies a page count, use that count.
- If the user does not specify a page count, default to 3 pages.

1. Open the search page.

```bash
agent-browser open 'https://www.shixiseng.com'
agent-browser snapshot -i
```

2. Fill the keyword box and execute the search.

```bash
agent-browser fill @e10 'agent'
agent-browser click @e9
agent-browser wait 3000
agent-browser get url
agent-browser snapshot -i
```

3. Collect candidate detail links from the search results.

Prefer detail-page URLs over list-page text because the list often contains icon-font glyph noise.

```bash
agent-browser eval "JSON.stringify(Array.from(document.querySelectorAll('a')).map(a => ({text:(a.innerText||'').trim(), href:a.href})).filter(x => x.href.includes('/intern/')).slice(0,20), null, 2)"
```

4. For multi-page export, finish the current page before clicking the next-page button.

Use the result-page paginator, collect the detail links for page 1, click the next-page button, collect page 2, then repeat until the required page count is reached. If the user did not specify a page count, stop after page 3.

```bash
AGENT_BROWSER_SESSION=crawl agent-browser get url
AGENT_BROWSER_SESSION=crawl agent-browser eval "JSON.stringify(Array.from(new Set(Array.from(document.querySelectorAll('a')).map(a => a.href).filter(href => href.includes('/intern/')))).slice(0,20), null, 2)"
AGENT_BROWSER_SESSION=crawl agent-browser click @e73
AGENT_BROWSER_SESSION=crawl agent-browser wait 3000
AGENT_BROWSER_SESSION=crawl agent-browser get url
AGENT_BROWSER_SESSION=crawl agent-browser snapshot -i
```

Keep a manifest with one object per detail page:

```json
[
  {
    "search_keyword": "llm算法",
    "source_page": 1,
    "url": "https://www.shixiseng.com/intern/inn_xxx?pcm=pc_SearchList"
  }
]
```

5. Open each detail page and extract fields from the page title and `document.body.innerText`.

Quote URLs that contain `?` to avoid `zsh` globbing errors.

```bash
AGENT_BROWSER_SESSION=job1 agent-browser open 'https://www.shixiseng.com/intern/inn_xxx?pcm=pc_SearchList'
AGENT_BROWSER_SESSION=job1 agent-browser wait 1500
AGENT_BROWSER_SESSION=job1 agent-browser eval "JSON.stringify({title: document.title, text: document.body.innerText})"
```

6. For more than a handful of jobs, use the bundled script instead of hand-normalizing every record.

Use these columns by default:

`title, company, refresh_time, salary, city, education, attendance, duration, benefits, deadline, location, company_description, job_description, url`

```bash
python3 scripts/export_shixiseng_jobs_csv.py ./manifest.json --output ./shixiseng_jobs.csv --session shixiseng-export
```

The script reads the manifest, opens each detail page with `agent-browser`, applies the same rule-based parsing, and writes the CSV.

## Parsing Heuristics

- `document.title` usually contains a clean `职位-公司-实习僧` string even when the list page is noisy.
- `document.body.innerText` usually follows this order near the top:
  `job title` -> `refresh time` -> `salary city education attendance duration [benefits...]`
- The `职位描述：` section is reliable. Extract text until `投递要求：`.
- `截止日期：` and `工作地点：` appear as stable labels on detail pages.
- `公司简介` is followed by the company name and one short company description.
- Keep descriptions as one CSV cell. Replace internal newlines with spaces or semicolons.

## Site-Specific Pitfalls

- `agent-browser wait --load networkidle` can time out on Shixiseng. If the page is visibly loaded, fall back to `wait 1500` or `wait 3000`.
- `--auto-connect` may attach to the user's active Chrome tab instead of the Shixiseng tab. For repeatable scraping, prefer a dedicated `agent-browser` session.
- Opening the encoded result URL directly is often more reliable than interacting with the home-page search box.
- The home-page search button can be blocked by suggestion overlays. If needed, navigate straight to `/interns?...keyword=...` instead of forcing the home-page form.
- On the result page, the next-page button is usually the right-arrow button near the bottom. Re-snapshot after paging because refs can change.
- Treat pagination as an explicit requirement. Default to 3 pages only when the user does not provide a page count.
- Search result titles may contain icon-font artifacts. Validate titles from the detail page before writing CSV.
- If the site opens login prompts, keep extracting only the public fields unless the user explicitly wants to use an authenticated context.
- For broad export, collect URLs page by page first, then run the detail-page export script. Do not mix list-page navigation and detail-page extraction in the same browser session if you need deterministic pagination.

## Output Rules

- Write the CSV into the current workspace unless the user specifies another path.
- Use ASCII column names.
- Preserve original Chinese content inside field values.
- Include the source job URL in every row.
- Add `source_page` and `search_keyword` when exporting paginated results.
- When pagination is not specified, record results from pages 1-3. When pagination is specified, record exactly that many pages unless the site runs out of results earlier.
- If some fields are missing, leave the cell empty instead of inventing values.
- After writing the file, verify the header row and at least the first few records.

## Minimal Deliverable

For a first pass, export 3-10 records with clean columns and verified URLs. Expand pagination only after the structure is confirmed.

## Bundled Script

- `scripts/export_shixiseng_jobs_csv.py`
  Use when the manifest already exists and the task is to batch-export detail pages into a CSV with consistent columns.
