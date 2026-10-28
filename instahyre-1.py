import truststore
truststore.inject_into_ssl()

import requests
import time

SLEEP_SECONDS = 2

COOKIE_STRING = r"""
cf_clearance=RAqwM7goxZfAJe5Gec8W8ERUFZgbs4EimYOFZSxJCZQ-1789555776-1.2.1.1-kyIE0uooeoCxcP0_8_EBJqR.HRHa67WF9y9Tve6v4CtBh98hZLnxKMm91ymsIIQYsV84Cs8V9d7vw9lVDYkVprkko1D6SE5OsKWy4dhjg7BnOmjApU.mASR2TPyUwp2MrVbVHMb5vKjKH6lXoOX4b69mL7SP2yN6TKRfqwiyvwSW_0L409u0VlVhw6tPtnEBxz4xIx0GU4rWReBsMBLX.IgWgVF4BKpjMzsHrT2CCdnMBYFFCy9LQaaWC4mFNpk.6U2A7XKkR1_eR2t2F469TMmpQse0Nhbi7ZFSyvjd.rxwGS5nTziUyEMmixIfjoDFTQHdZ3mswG8VCtXeBxaispiXbiW80tNcbkP6dwOYP8gaXP5Cald6YD2O8FepYL0rBrzZZCV0aYnKCF8l8KeEC5UwkC6Kxd6za5Y_Y9PO.rrVIhyy6d7wUwchJF3fqdtGqMD.YKGhhSnaRKthqWWEASnoyldNA1dg97IXP3C.5M0kvnEibcGyfijCd5syzfwBAAYRF.0ko.JgLyF0Hseg9A; csrftoken=molzDEQCXOQuTMFJtnZUPFYCz7ECVQoX1h1DkVVF159RCDxAQRVZruM7fOyZW1s9; sessionid=sdv1rhky4n81w7jg0tutl1qkz3z4mrg5; _dd_s_v2=aid=acd0813c-bde4-46a2-ac06-324ad52b2bd6&id=c0f436b1-00e3-4a45-a200-4197a4857fc8&created=1789555757466&expire=1789556916760&c=0; _gid=GA1.2.304095287.1793191993; _gat_UA-45611607-3=1; _ga_0PQL61K7YN=GS2.1.s1793191987$o3$g1$t1793192974$j47$l0$h0; _ga=GA1.1.1386587682.1789555758
"""

LISTING_URL = "https://www.instahyre.com/api/v1/job_search"

APPLY_URL = (
    "https://www.instahyre.com/"
    "api/v1/candidate_opportunities/"
    "candidate_matching/apply"
)

# ============================================================
# SKILL SETS
# ============================================================
# 4 different skill-based search profiles to maximize coverage.
# Each set targets a different combination of skills to surface
# unique job listings that a single query might miss.

SKILL_SETS = {
    "Set 1 - SDET / Automation": [
        "Automation Testing", "Selenium", "Playwright", "Python", "pytest",
        "API Testing", "Postman", "Rest APIs", "Behavior Driven Development",
        "CI / CD", "CI", "Azure DevOps", "SQL", "Regression Testing", "Swagger",
    ],
    "Set 2 - Manual + Automation (Hybrid QA)": [
        "Manual Testing", "Automation Testing", "Functional Testing",
        "Regression Testing", "Test case design", "Defect Analysis",
        "API Testing", "Selenium", "Python", "Postman", "SQL",
        "Azure DevOps", "Agile", "Playwright", "Rest APIs",
    ],
    "Set 3 - API Testing Focus": [
        "API Testing", "Postman", "Swagger", "Rest APIs", "Python", "pytest",
        "SQL", "Automation Testing", "Regression Testing", "Functional Testing",
        "Azure DevOps", "CI / CD", "Defect Analysis", "Agile",
        "Behavior Driven Development",
    ],
    "Set 4 - Manual / Functional QA": [
        "Manual Testing", "Functional Testing", "Test case design",
        "Regression Testing", "Defect Analysis", "Agile", "SQL",
        "Azure DevOps", "API Testing", "Postman", "Swagger", "Rest APIs",
        "Automation Testing", "Selenium", "Python",
    ],
    "Set 5 - Automation Frameworks + CI": [
        "Selenium", "Playwright", "Python", "pytest",
        "Behavior Driven Development", "Automation Testing", "CI", "CI / CD",
        "Azure DevOps", "Regression Testing", "API Testing", "Postman",
        "Test case design", "SQL", "Agile",
    ],
    "Set 6 - All Profile Skills": [
        "Automation Testing", "Manual Testing", "API Testing",
        "Regression Testing", "Functional Testing", "Selenium", "Playwright",
        "Python", "Postman", "Behavior Driven Development", "pytest",
        "Swagger", "Rest APIs", "SQL", "Azure DevOps", "CI", "CI / CD",
        "Test case design", "Defect Analysis", "Agile",
    ],
}

# Base params common to all skill sets
BASE_PARAMS = [
    ("company_size", "0"),
    ("job_categories", "1"),
    ("job_functions", "10"),
    ("job_functions", "1"),
    ("job_type", "0"),
    ("source", "opportunities"),
    ("status", "0"),
    ("years", "3"),
]

# Base params with no job_categories/job_functions/years filter,
# so jobs excluded by those filters still surface.
BASE_PARAMS_UNFILTERED = [
    ("company_size", "0"),
    ("job_type", "0"),
    ("source", "opportunities"),
    ("status", "0"),
]

# Catch-all set(s): run with BASE_PARAMS_UNFILTERED instead of BASE_PARAMS.
# Empty skills list = no "skills" query param at all, so every opportunity
# is returned regardless of skill match (listed in SKILL_SETS or not).
CATCHALL_SKILL_SETS = {
    "Set 5 - Catch-All (All Opportunities, No Skill/Category/Function/Years Filter)": ["Python"],
}


def build_params(skills, base_params=BASE_PARAMS):
    """Build the full query params for a given list of skills."""
    params = list(base_params)
    for skill in skills:
        params.append(("skills", skill))
    return params


# ============================================================
# COOKIE PARSER
# ============================================================

def parse_cookies(cookie_string):
    cookies = {}

    for item in cookie_string.replace("\n", " ").split(";"):
        item = item.strip()

        if not item or "=" not in item:
            continue

        key, value = item.split("=", 1)

        cookies[key.strip()] = value.strip()

    return cookies


cookies = parse_cookies(COOKIE_STRING)

required = [
    "sessionid",
    "csrftoken",
]

missing = [x for x in required if x not in cookies]

if missing:
    raise RuntimeError(
        "Missing required cookies: " + ", ".join(missing)
    )

# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.cookies.update(cookies)

csrf_token = cookies["csrftoken"]

session.headers.update({
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Content-Type": "application/json",
    "Origin": "https://www.instahyre.com",
    "Referer": "https://www.instahyre.com/candidate/opportunities/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "X-CSRFToken": csrf_token,
})


# ============================================================
# FETCH JOBS
# ============================================================


# ============================================================
# APPLY
# ============================================================

def apply_job(job):

    job_id = job.get("id")

    title = job.get("title", "Unknown")

    employer = job.get("employer") or {}

    company = employer.get(
        "company_name",
        "Unknown company"
    )

    location = job.get(
        "locations",
        ""
    )

    print()
    print("-" * 70)
    print(f"Job ID   : {job_id}")
    print(f"Title    : {title}")
    print(f"Company  : {company}")
    print(f"Location : {location}")
    print("-" * 70)

    if not job_id:
        print("SKIPPED: No job ID")
        return False

    payload = {
        "job_id": job_id,
        "is_interested": True,
        "is_activity_page_job": False,
    }

    try:

        response = session.post(
            APPLY_URL,
            json=payload,
            timeout=30,
        )

        print("POST status:", response.status_code)

        try:
            result = response.json()
            print("Response:", result)
        except ValueError:
            print("Response:", response.text[:1000])

        if 200 <= response.status_code < 300:
            print("APPLIED")
            return True

        print("FAILED")
        return False

    except requests.RequestException as e:

        print("REQUEST ERROR:", e)

        return False


# ============================================================
# MAIN
# ============================================================

def fetch_jobs_for_skill_set(set_name, skills, seen_job_ids, base_params=BASE_PARAMS):
    """
    Fetch all pages of jobs for a given skill set.
    Skips jobs already seen (by job ID) to avoid duplicate applications.
    Returns (new_jobs_list, updated_seen_job_ids).
    """
    new_jobs = []
    page = 1
    params = build_params(skills, base_params)
    applied_count = 0
    skipped_count = 0

    while True:
        print(f"\n  [{set_name}] Fetching page {page}...")

        try:
            response = session.get(
                LISTING_URL,
                params=params + [("page", page)],
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"  [{set_name}] Request error on page {page}: {e}")
            break

        data = response.json()
        jobs = data.get("objects", [])

        print(f"  [{set_name}] Found {len(jobs)} jobs on page {page}")

        if not jobs:
            print(f"  [{set_name}] No more jobs. Moving on.")
            break

        for job in jobs:
            job_id = job.get("id")

            if job_id in seen_job_ids:
                title = job.get("title", "Unknown")
                print(f"\n  SKIPPED (duplicate): {title} (ID: {job_id})")
                skipped_count += 1
                continue

            seen_job_ids.add(job_id)
            new_jobs.append(job)

            apply_job(job)
            applied_count += 1
            time.sleep(SLEEP_SECONDS)

        page += 1

    print(f"\n  [{set_name}] Summary: "
        f"{applied_count} applied, {skipped_count} skipped (duplicates)")

    return new_jobs, seen_job_ids


def fetch_all_jobs():
    """
    Iterate through all skill sets (filtered + catch-all), fetch and
    apply to jobs. Deduplicates across sets so the same job is only
    applied to once.
    """
    all_jobs = []
    seen_job_ids = set()

    # (skill_sets, base_params) groups, run in order.
    groups = [
        (SKILL_SETS, BASE_PARAMS),
        (CATCHALL_SKILL_SETS, BASE_PARAMS_UNFILTERED),
    ]
    all_set_names = [
        name for skill_sets, _ in groups for name in skill_sets
    ]

    for skill_sets, base_params in groups:
        for set_name, skills in skill_sets.items():
            print()
            print("=" * 70)
            print(f"  SKILL SET: {set_name}")
            print(f"  Skills: {' | '.join(skills)}")
            print("=" * 70)

            new_jobs, seen_job_ids = fetch_jobs_for_skill_set(
                set_name, skills, seen_job_ids, base_params
            )
            all_jobs.extend(new_jobs)

            # Brief pause between skill sets to be polite to the API
            if set_name != all_set_names[-1]:
                print(f"\n  Pausing {SLEEP_SECONDS}s before next skill set...")
                time.sleep(SLEEP_SECONDS)

    return all_jobs


def main():
    total_sets = len(SKILL_SETS) + len(CATCHALL_SKILL_SETS)
    print("=" * 70)
    print("INSTAHYRE AUTO APPLY — MULTI-SKILL SET MODE")
    print(f"Running {total_sets} skill sets")
    print("=" * 70)

    jobs = fetch_all_jobs()

    print()
    print("=" * 70)
    print("FINISHED")
    print(f"Total unique jobs processed: {len(jobs)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
