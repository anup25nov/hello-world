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

PARAMS = [
    ("company_size", "0"),
    ("job_categories", "1"),
    ("job_functions", "10"),
    ("job_functions", "1"),
    ("job_type", "0"),

    ("skills", "Python"),
    ("skills", "Django"),
    ("skills", "Java"),
    ("skills", "FastAPI"),
    ("skills", "MySQL"),
    ("skills", "PostgreSQL"),
    ("skills", "MongoDB"),
    ("skills", "AWS"),
    ("skills", "Kafka"),
    ("skills", "Redis"),
    ("skills", "Celery"),
    ("skills", "Grafana"),
    ("skills", "JavaScript"),
    ("skills", "LLMs"),
    ("skills", "Claude"),

    ("source", "opportunities"),
    ("status", "0"),
    ("years", "3"),
]

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
def fetch_all_jobs():
    all_jobs = []
    page = 1

    while True:
        print(f"\nFetching page {page}...")

        response = session.get(
            LISTING_URL,
            params=PARAMS + [("page", page)],
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()
        jobs = data.get("objects", [])

        print(f"Found {len(jobs)} jobs")

        if not jobs:
            print("No more jobs. Stopping.")
            break

        all_jobs.extend(jobs)

        # Apply to jobs from this page
        for job in jobs:
            apply_job(job)
            time.sleep(2)

        page += 1

    return all_jobs

def main():
    print("=" * 70)
    print("INSTAHYRE AUTO APPLY")
    print("=" * 70)

    jobs = fetch_all_jobs()

    print("\nFinished.")
    print(f"Total jobs processed: {len(jobs)}")

if __name__ == "__main__":
    main()
