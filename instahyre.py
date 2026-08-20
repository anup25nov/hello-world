import truststore
truststore.inject_into_ssl()

import requests
import time

SLEEP_SECONDS = 2

COOKIE_STRING = r"""
cf_clearance=NXKGbYQuLasSGMY.MwXGYuA.tNQsDLCdHUv3_w0gIqc-1786024944-1.2.1.1-XWBxj1qpWEkMvGjKzl5EmM05QylDuoBPH_84jry4OO6ldUpQWUrQlz_xWFB_0V57a3abS05cYoQrIb4qjtS.XEZpyCgjllz2Q140hiDZ.lJ57dWrH7TPzuYp7oHCQGfnBvBHnlJtwDInC1bxfUjImuELMDTXZW5V0DngxCbumwwUxhWi0iKP3GzqQIw3ONjspmgGD1la78Zz0MvUzuCv1.f1xlX7olLuHtUN4jyeUTXXJE2F_ks6TpTb0HR6QSloqqqeX_YqTolKg4O7BYGEfTC.jDf_A6WKY3EQL7RVP4wcOP5ZuDSJu80BopeA7CX4XbVAtYERULOIblblgu8O_UTI62Rn2lzubrIortD_QdDsRDm.oey8eqA4cCPnMlCKUUKfOCkLBw8FrI2MFI6pGat2l3mm55wmtnTtS4mzxbiSw0LzgGYdt7uhOxzp84gbvML_vP1DmTrCtMiCFZwgem50qHSmrlNptwSoMpJChM8JelmXK_Km3u_HrCym_.VPlDVHpNxdEVOx0sN68pI94w; csrftoken=rADShNlHIAmzYyTKueCPFx7fCqpNpLUUL9UUKNQd1BCso4YLHa7y8fvdT5PTvrQJ; sessionid=riu8b76nhfi5nhbnzf2m3ni86mpjzfjt; _gcl_au=1.1.1033739731.1786024945; _clck=190ig1w%5E2%5Eg8d%5E0%5E2409; _gid=GA1.2.1983631359.1786448037; _ga=GA1.2.1423957839.1786024907; _ga_0PQL61K7YN=GS2.1.s1786459611$o5$g1$t1786460699$j25$l0$h0; _gat_UA-45611607-3=1
"""

LISTING_URL = "https://www.instahyre.com/api/v1/job_search"

APPLY_URL = (
    "https://www.instahyre.com/"
    "api/v1/candidate_opportunities/"
    "candidate_opportunity/apply"
)

# ============================================================
# SKILL SETS
# ============================================================
# 4 different skill-based search profiles to maximize coverage.
# Each set targets a different combination of skills to surface
# unique job listings that a single query might miss.

SKILL_SETS = {
    "Set 1 - Full Stack Backend": [
        "Python", "Django", "Java", "FastAPI", "MySQL",
        "PostgreSQL", "MongoDB", "AWS", "Kafka", "Redis",
        "Celery", "Grafana", "JavaScript", "LLMs", "Claude",
    ],
    "Set 2 - Backend + AI/ML": [
        "Python", "FastAPI", "Microservices", "PostgreSQL",
        "Kafka", "MongoDB", "AWS", "Docker", "REST APIs",
        "SQL", "Redis", "Celery", "SQLAlchemy", "LLMs", "MCP",
    ],
    "Set 3 - Backend + Cloud": [
        "Python", "Microservices", "Kafka", "PostgreSQL",
        "MongoDB", "AWS", "Docker", "Redis", "Celery",
        "SQLAlchemy", "REST APIs", "DynamoDB", "S3", "Flask",
        "Sanic",
    ],
    "Set 4 - AI/LLM Focused": [
        "Python", "FastAPI", "LLMs", "MCP", "Claude",
        "Microservices", "PostgreSQL", "MongoDB", "Kafka",
        "AWS", "Docker", "REST APIs", "Redis", "SQLAlchemy",
        "Celery",
    ],
    "Set 5 - All python": [
            "Python"
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


def build_params(skills):
    """Build the full query params for a given list of skills."""
    params = list(BASE_PARAMS)
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
        "is_interested": True,
        "id": None,
        "job_id": job_id,
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

def fetch_jobs_for_skill_set(set_name, skills, seen_job_ids):
    """
    Fetch all pages of jobs for a given skill set.
    Skips jobs already seen (by job ID) to avoid duplicate applications.
    Returns (new_jobs_list, updated_seen_job_ids).
    """
    new_jobs = []
    page = 1
    params = build_params(skills)
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
    Iterate through all 4 skill sets, fetch and apply to jobs.
    Deduplicates across sets so the same job is only applied to once.
    """
    all_jobs = []
    seen_job_ids = set()

    for set_name, skills in SKILL_SETS.items():
        print()
        print("=" * 70)
        print(f"  SKILL SET: {set_name}")
        print(f"  Skills: {' | '.join(skills)}")
        print("=" * 70)

        new_jobs, seen_job_ids = fetch_jobs_for_skill_set(
            set_name, skills, seen_job_ids
        )
        all_jobs.extend(new_jobs)

        # Brief pause between skill sets to be polite to the API
        if skills != list(SKILL_SETS.values())[-1]:
            print(f"\n  Pausing {SLEEP_SECONDS}s before next skill set...")
            time.sleep(SLEEP_SECONDS)

    return all_jobs


def main():
    print("=" * 70)
    print("INSTAHYRE AUTO APPLY — MULTI-SKILL SET MODE")
    print(f"Running {len(SKILL_SETS)} skill sets")
    print("=" * 70)

    jobs = fetch_all_jobs()

    print()
    print("=" * 70)
    print("FINISHED")
    print(f"Total unique jobs processed: {len(jobs)}")
    print("=" * 70)


if __name__ == "__main__":
    main()