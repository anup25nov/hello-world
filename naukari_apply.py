#!/usr/bin/env python3
"""
Naukri Auto-Apply — Three-Phase System
───────────────────────────────────────
Phase 1  python3 naukri_apply.py --discover
         Runs through all recommended jobs' chatbots, collects every unique
         question, uses OpenAI to propose an answer. Saves to questionnaire.json.
         Applications are NOT submitted.

Phase 2  python3 naukri_apply.py --validate
         Shows you every question + AI-proposed answer interactively.
         Press ENTER to accept, or type a new answer to override.
         Marks each as validated. questionnaire.json updated.

Phase 3  python3 naukri_apply.py --apply
         Applies to all recommended jobs. Uses validated answers from
         questionnaire.json. If a brand-new question appears at runtime,
         proposes via AI and saves it for future runs.
"""

import argparse, json, time, random, logging, os, re, sys
from datetime import datetime

import requests
from openai import OpenAI

# ══════════════════════════════════════════════
#  CREDENTIALS — loaded from config.json
#  When nauk_at expires (every ~1h), just update config.json
# ══════════════════════════════════════════════

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
NAUK_AT        = "eyJraWQiOiIzIiwidHlwIjoiSldUIiwiYWxnIjoiUlM1MTIifQ.eyJ1ZF9yZXNJZCI6MjE1NDE2ODUwLCJzdWIiOiIyMjg3Njc5NzQiLCJ1ZF91c2VybmFtZSI6ImFudXBtLnVnMTkuY3NAbml0cC5hYy5pbiIsInVkX2lzRW1haWwiOnRydWUsImlzcyI6IkluZm9FZGdlIEluZGlhIFB2dC4gTHRkLiIsInVzZXJBZ2VudCI6Ik1vemlsbGEvNS4wIChNYWNpbnRvc2g7IEludGVsIE1hYyBPUyBYIDEwXzE1XzcpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNTAuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImlwQWRyZXNzIjoiMTM2LjIyNi4yMzAuOTciLCJ1ZF9pc1RlY2hPcHNMb2dpbiI6ZmFsc2UsInVzZXJJZCI6MjI4NzY3OTc0LCJzdWJVc2VyVHlwZSI6IiIsInVzZXJTdGF0ZSI6IkFVVEhFTlRJQ0FURUQiLCJ1ZF9pc1BhaWRDbGllbnQiOmZhbHNlLCJ1ZF9lbWFpbFZlcmlmaWVkIjp0cnVlLCJ1c2VyVHlwZSI6ImpvYnNlZWtlciIsInNlc3Npb25TdGF0VGltZSI6IjIwMjYtMDgtMDZUMTk6MjI6MjYiLCJ1ZF9lbWFpbCI6ImFudXBtLnVnMTkuY3NAbml0cC5hYy5pbiIsInVzZXJSb2xlIjoidXNlciIsImV4cCI6MTc4NjU1MDYxMSwidG9rZW5UeXBlIjoiYWNjZXNzVG9rZW4iLCJpYXQiOjE3ODY1NDcwMTEsImp0aSI6ImZjZDZlYjc1ZDI4YzQzNDU4N2UwMGI2NWRlYzNjMDEzIiwicG9kSWQiOiJwcm9kLTViYmM2YmI1OWItcms0a3YifQ.FaPJhGgNJtQ2wyJQZG21N6YqKlw_MjLSRXyKf2ec20gPl6YKO1cNUTtXzWs5-rtMB8ylyjsrcdveIGS9cqUwnjRB8H4DadKb_q3v34Efd718k1Wddk5K31p6hB9gJmWvyA4SNeaVtwFTywUEYIFLyicS3ur2mtbOOzPHTselPSUS0M5h451TS7hLovLwe5FqPh3fI4n7mc7wzlsdnicdnxPtGl5CBr9FvRwt_3g1O_gJqRY-F_YTLK54mvWWolUkp0LBX_WN6017Xd44CjBcmnAEme7A6q6h78Y6H54ZlH8KhWvfRI7Y-TWiv5GboQo7piRmn2tVP8mX5PUoA73JBw"
COOKIES_RAW    = "_t_ds=10fa0c241786024340-210fa0c24-010fa0c24; J=0; _ga=GA1.1.2121957743.1786024343; nauk_rt=fcd6eb75d28c434587e00b65dec3c013; nauk_sid=fcd6eb75d28c434587e00b65dec3c013; nauk_otl=fcd6eb75d28c434587e00b65dec3c013; NKWAP=712e56e556aae7d882141e5a66f93cfb6f2888a4f4ffcc435c779ede2be417a57207b8e1f44ec4db~712e56e556aae7d882141e5a66f93cfb6f2888a4f4ffcc435c779ede2be417a57207b8e1f44ec4db~1~0; MYNAUKRI[UNID]=e1cdedeb74d443d1927e2c2162682f76; nauk_ps=default; test=naukri.com; _ff_ds=0525486001786026424-865A49A1B4C6-C0A4662F3383; promobnr=FASTJOB20; __insp_wid=1013263782; __insp_slim=1786110556431; __insp_nv=true; __insp_targlpu=aHR0cHM6Ly93d3cubmF1a3JpLmNvbS9uYXVrcmkzNjAtcHJvP3V0bVRlcm09TjM2MFByb19OQyZ1dG1Db250ZW50PURpd2FsaTE1VjIyJnV0bV9jYW1wYWlnbj1kdXNzaGVyYV9uYXVrcmkzNjBfcHJvX2NhbXBhaWduJnV0bV9tZWRpdW09bm90aWZpY2F0aW9uX2NlbnRlciZpZD00ZWUxYjA2MC05NTI0LTRlNTYtYjNhYi1kYWZkNmZiMjQyY2ImY3JlYXRlZEF0PTIwMjYtMDgtMDZUMTU6MDU6MjkuMDAw; __insp_targlpt=TmF1a3JpIDM2MCBQcm8gYnkgTmF1a3JpLmNvbQ%3D%3D; __insp_norec_sess=true; geo_country=IN; studio_rt=fae3cfec4cdb43dfaed70be7d00b8f63; ninja_auth_token=8e23a8e8c79a02da7ce230a1b292b3ba; ninjas_new_marketing_token=6da144ba52bb2334d3373fa482216e74; AWSALB=KGRcJD78xlThpA8c4/xfqECsf3UUf1OrPa9KsknRla4rNwb3Hj6G48kSw0R+2veHJvXoIFnz1YYlAOmkVYb+kw9VWlL+OsHn9TsqmYtv3E5ySeUQ3w0GHFDG3diX; AWSALBCORS=KGRcJD78xlThpA8c4/xfqECsf3UUf1OrPa9KsknRla4rNwb3Hj6G48kSw0R+2veHJvXoIFnz1YYlAOmkVYb+kw9VWlL+OsHn9TsqmYtv3E5ySeUQ3w0GHFDG3diX; _ga_JCSR1LRE3X=GS2.1.s1786110761$o1$g0$t1786110761$j60$l0$h0; _ga_7TYVEWTVRG=GS2.1.s1786110761$o1$g0$t1786110761$j60$l0$h0; _clck=1j8v7r1%5E2%5Eg8e%5E0%5E2410; nauk_cs=370; HitsFromTieup=571; wExp=N; tms_srcTemp=registerfree468x60; TieupFromTMS=10; bm_mi=59116316797130A4F044F675FAA6E06F~YAAQr/naF+PGoLOfAQAAGfR/9gC132hoGdVa+UVuLTUAkvRG9mqfKCFw5yca+5Z1PVSyiW80U0f42zb2zlS/gIoPSJowWZ8RqkaJG9c04Tu2Yh/JaLH1VEXseuR0Kgf6f+0T7hGKCnzN6gHetSKq+sxWTZPtJB7gvGFKNXz/gQRiDaggk4RRGqiu5iRV3DMWcGw22A0fR6nLtuhPAAN3EKlgJI59zycme6fzTXV3ek+Dlg5VsnaeNpKU64ogiPQk0IqVIhs2MREx+k6xjuhsAoYvmaQnl6pyhqoMD1usPatCnG7mTzOVC7re0aa42xELsf08sWm5FwFwKXMAs7EDsNx/TBoZtA==~1; ak_bmsc=32AE6E11E33CE067EC9C6849E3B02884~000000000000000000000000000000~YAAQr/naF3PHoLOfAQAA5PZ/9gBFJBR9VPYlG8n13CfKK6ET2DEuecql24Q7Y3xNnYzp4TPJcLM6421Mi277kd5YOl/1PgPSgcGM1fk6n95gtKM8+7FMAO2SEmSTDcuzdHAFr4c4B71uc5cNgXKpoI+fW3yN0tEGJOs3VKCNV1mK8uiGfhQPFKaMdiPJ0PM0m6LLk0Nvajq/H1J7fsJHi0TdWlW/mVTXTUkUxuvs8ZOCEFj5HK7Edv0mjnS2p6DxOHaH8l+UrT4l2AcXIs0ooxhdS8Fj9aemvZITN40yccEP+X5B9xrCgveZ4YFYrZbLFWU63CEHZ5oRxvbJshPwGDh3geMlSenL9QDdWU9rrJmliJGMdo61vKmFiNAJEJycFtSUROWCcwRS6inIZTj2z197kBri5uezYgnOKvkVxzJGNvqy3BZJbhatP8cbAyJnBMYaX67h3aFCmRjjYSk+ZWQ9pHPsmY7sRsG6PLwWZDlJna3epnQ37mmiQJuoPpFYWNIamhoRXNWSpUfvx56u0X7P5/GUi7MSzcwbvIR3Kl53CK4=; _gcl_aw=GCL.1786547012.CjwKCAjws_DTBhB_EiwAXZknGRLnV6HIYkcR62to9j8eVtNEIBUScDKRmvyi6NcP29reCg0cAkimNxoCN-UQAvD_BwE; _gcl_dc=GCL.1786547012.CjwKCAjws_DTBhB_EiwAXZknGRLnV6HIYkcR62to9j8eVtNEIBUScDKRmvyi6NcP29reCg0cAkimNxoCN-UQAvD_BwE; _gcl_gs=2.1.k1$i1786547011$u93512962; nauk_at=eyJraWQiOiIzIiwidHlwIjoiSldUIiwiYWxnIjoiUlM1MTIifQ.eyJ1ZF9yZXNJZCI6MjE1NDE2ODUwLCJzdWIiOiIyMjg3Njc5NzQiLCJ1ZF91c2VybmFtZSI6ImFudXBtLnVnMTkuY3NAbml0cC5hYy5pbiIsInVkX2lzRW1haWwiOnRydWUsImlzcyI6IkluZm9FZGdlIEluZGlhIFB2dC4gTHRkLiIsInVzZXJBZ2VudCI6Ik1vemlsbGEvNS4wIChNYWNpbnRvc2g7IEludGVsIE1hYyBPUyBYIDEwXzE1XzcpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNTAuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImlwQWRyZXNzIjoiMTM2LjIyNi4yMzAuOTciLCJ1ZF9pc1RlY2hPcHNMb2dpbiI6ZmFsc2UsInVzZXJJZCI6MjI4NzY3OTc0LCJzdWJVc2VyVHlwZSI6IiIsInVzZXJTdGF0ZSI6IkFVVEhFTlRJQ0FURUQiLCJ1ZF9pc1BhaWRDbGllbnQiOmZhbHNlLCJ1ZF9lbWFpbFZlcmlmaWVkIjp0cnVlLCJ1c2VyVHlwZSI6ImpvYnNlZWtlciIsInNlc3Npb25TdGF0VGltZSI6IjIwMjYtMDgtMDZUMTk6MjI6MjYiLCJ1ZF9lbWFpbCI6ImFudXBtLnVnMTkuY3NAbml0cC5hYy5pbiIsInVzZXJSb2xlIjoidXNlciIsImV4cCI6MTc4NjU1MDYxMSwidG9rZW5UeXBlIjoiYWNjZXNzVG9rZW4iLCJpYXQiOjE3ODY1NDcwMTEsImp0aSI6ImZjZDZlYjc1ZDI4YzQzNDU4N2UwMGI2NWRlYzNjMDEzIiwicG9kSWQiOiJwcm9kLTViYmM2YmI1OWItcms0a3YifQ.FaPJhGgNJtQ2wyJQZG21N6YqKlw_MjLSRXyKf2ec20gPl6YKO1cNUTtXzWs5-rtMB8ylyjsrcdveIGS9cqUwnjRB8H4DadKb_q3v34Efd718k1Wddk5K31p6hB9gJmWvyA4SNeaVtwFTywUEYIFLyicS3ur2mtbOOzPHTselPSUS0M5h451TS7hLovLwe5FqPh3fI4n7mc7wzlsdnicdnxPtGl5CBr9FvRwt_3g1O_gJqRY-F_YTLK54mvWWolUkp0LBX_WN6017Xd44CjBcmnAEme7A6q6h78Y6H54ZlH8KhWvfRI7Y-TWiv5GboQo7piRmn2tVP8mX5PUoA73JBw; is_login=1; bm_sv=EA36124D942FFBE6DBA6BA0DF3D7D708~YAAQr/naF0rioLOfAQAAOZGA9gCpwohjqITzR7JwqcRPwwldkStGdfR38bM6OhOhbQgW8v5bPnHGP6t6UmX8VI2+Y2HVgeWZfic6K7hbamxjggRE23qWRmduIZOUwTK3q9Lys12iPOWgm0KabI6M9j2wgt7KbhPGt2dANHZaN+lXLIBmTX1cbJjppvxUeZvJVVvta5wbWeVyC8Bvyg3Ov0B5vaLvyefxWwflr3ojIrYvkbeJ5gasI2yfqiCqXH4wgw==~1; HOWTORT=cl=1786547014409&r=https%3A%2F%2Fwww.naukri.com%2Fmnjuser%2Frecommendedjobs&nu=https%3A%2F%2Fwww.naukri.com%2Fmnjuser%2Frecommendedjobs&ul=1786547048565&hd=1786547048751; _gcl_au=1.1.2058476003.1786024343.-.-.1786024342.1910195586.1786468853.1786547048; _ga_K2YBNZVRLL=GS2.1.s1786547009$o6$g1$t1786547048$j21$l0$h0"

_cfg = {}
_cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
if os.path.exists(_cfg_path):
    try:
        with open(_cfg_path) as _f:
            _cfg = json.load(_f)
    except Exception:
        pass

if not OPENAI_API_KEY:
    OPENAI_API_KEY = _cfg.get("openai_api_key")
if not NAUK_AT:
    NAUK_AT = _cfg.get("nauk_at")
if not COOKIES_RAW:
    COOKIES_RAW = _cfg.get("cookies_raw")

if not OPENAI_API_KEY or not NAUK_AT or not COOKIES_RAW:
    print("❌  Missing credentials! Must set OPENAI_API_KEY, NAUK_AT, and COOKIES_RAW in env or config.json.")
    print(f"{not OPENAI_API_KEY} | {not NAUK_AT} | {not COOKIES_RAW}")
    sys.exit(1)

# Ensure nauk_at is cleaned from COOKIES_RAW and then replaced with the fresh NAUK_AT
_cookie_parts = []
for _part in COOKIES_RAW.split(";"):
    _part = _part.strip()
    if _part and not _part.lower().startswith("nauk_at="):
        _cookie_parts.append(_part)
COOKIES_RAW = "; ".join(_cookie_parts) + f"; nauk_at={NAUK_AT}"

# ── Check token expiry upfront ──────────────────────────────────
import base64 as _b64, time as _time
try:
    _payload = NAUK_AT.split(".")[1]
    _payload += "=" * (4 - len(_payload) % 4)   # pad base64
    _exp = json.loads(_b64.b64decode(_payload))["exp"]
    _now = int(_time.time())
    if _exp < _now:
        from datetime import datetime as _dt
        _expired_at = _dt.fromtimestamp(_exp).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n❌  nauk_at token EXPIRED at {_expired_at} IST")
        print("    Get a fresh token:")
        print("    1. Open https://www.naukri.com in Chrome (logged in)")
        print("    2. F12 → Application → Cookies → copy 'nauk_at' value")
        print("    3. Paste it into config.json → 'nauk_at' field")
        print("    4. Also copy the full cookie string → 'cookies_raw' field")
        print(f"\n    Current token was issued: {_dt.fromtimestamp(_exp-3600).strftime('%H:%M')}  |  expired: {_expired_at}")
        sys.exit(1)
    else:
        _mins = (_exp - _now) // 60
        print(f"✅  Token valid for {_mins} more minutes")
except Exception:
    pass   # If decode fails, let the API call fail naturally


# ══════════════════════════════════════════════
#  CANDIDATE PROFILE  (used by AI for answers)
# ══════════════════════════════════════════════

# ── Your background — AI uses this to answer unknown questions ──
CANDIDATE_PROFILE = """
Full Name       : Anup Mishra
Email           : anupm.ug19.cs@nitp.ac.in
Phone           : (provide if asked)
LinkedIn        : https://www.linkedin.com/in/anup-mishra-bb40a0192/
GitHub          : https://github.com/anupmishra
Education       : B.Tech Computer Science, NIT Patna, 2019
Total experience: 3 years
Skills          : Python, JavaScript, Node.js, React, AWS, GCP,
                  MySQL, PostgreSQL, MongoDB, REST APIs, Microservices,
                  System Design, Solution Engineering, Backend Development
Current city    : Gurgaon (Gurugram), Haryana
Open to relocate: Yes — willing to move anywhere in India
Notice period   : 60 days (serving notice: No — available in 30 days)
Current CTC     : 20 LPA
Expected CTC    : 30 LPA
Work mode       : Comfortable with Onsite / Hybrid / Remote
Hackerrank/coding test platform: Hackerrank
Previous interviews at current employer listed: No
Attended interview at the company before: No
Gender          : Male
PF (Provident Fund): Yes
"""

QUESTIONNAIRE_FILE = "questionnaire.json"
TRACKED_JOBS_FILE = "applied_jobs.json"
MIN_DELAY = 2
MAX_DELAY = 5
MAX_JOBS  = 100

def load_applied_jobs() -> set[str]:
    return set()

def save_applied_jobs(jobs_set: set[str]):
    pass

# ── Pre-seeded answers (bootstrapped into questionnaire on first run) ──
# Derived from real Naukri chatbot curl examples.
# key = normalized question text (lowercase), value = exact answer to send
BOOTSTRAP_QA = [
    # Experience
    {"question": "how many years of experience do you have",
     "answer": "3", "options": []},
    # City / location
    {"question": "which city are you currently residing in",
     "answer": "Gurgaon", "options": []},
    {"question": "please select the city you are currently residing or willing to relocate to",
     "answer": "Gurgaon", "options": []},
    {"question": "are you currently living in or ready to relocate",
     "answer": "Yes", "options": ["Yes", "No"]},
    {"question": "currently residing in",
     "answer": "Gurgaon", "options": []},
    # Work mode
    {"question": "are you okay with onsite work mode",
     "answer": "Yes", "options": ["Yes", "No"]},
    {"question": "are you comfortable working from office",
     "answer": "Yes", "options": ["Yes", "No"]},
    {"question": "work from office",
     "answer": "Yes", "options": ["Yes", "No"]},
    # LinkedIn
    {"question": "please share your linkedin profile",
     "answer": "https://www.linkedin.com/in/anup-mishra-bb40a0192/", "options": []},
    {"question": "linkedin profile url",
     "answer": "https://www.linkedin.com/in/anup-mishra-bb40a0192/", "options": []},
    {"question": "share your linkedin",
     "answer": "https://www.linkedin.com/in/anup-mishra-bb40a0192/", "options": []},
    # Coding platform / test
    {"question": "which platform did you take the test",
     "answer": "Hackerrank", "options": []},
    {"question": "hackerrank",
     "answer": "Hackerrank", "options": []},
    # PF
    {"question": "do you have pf",
     "answer": "Yes", "options": ["Yes", "No"]},
    # Previous interviews
    {"question": "have you received any call or attended any interview",
     "answer": "No", "options": ["YES", "NO"]},
    {"question": "attended any interview with",
     "answer": "No", "options": ["YES", "NO"]},
    # Notice period
    {"question": "notice period",
     "answer": "30", "options": []},
    {"question": "serving notice period",
     "answer": "No", "options": ["Yes", "No"]},
    # CTC
    {"question": "current ctc",
     "answer": "12", "options": []},
    {"question": "expected ctc",
     "answer": "20", "options": []},
    {"question": "current salary",
     "answer": "12", "options": []},
    {"question": "expected salary",
     "answer": "20", "options": []},
    # Relocation
    {"question": "willing to relocate",
     "answer": "Yes", "options": ["Yes", "No"]},
    {"question": "open to relocation",
     "answer": "Yes", "options": ["Yes", "No"]},
    # B2B / B2C
    {"question": "where have you mostly worked in",
     "answer": "B2B", "options": ["B2B", "B2C"]},
    # Immediate joiner
    {"question": "immediate joiner",
     "answer": "No", "options": ["Yes", "No"]},
    {"question": "available to join immediately",
     "answer": "No", "options": ["Yes", "No"]},
    # Technical skills
    {"question": "how many years of experience do you have in iceberg",
     "answer": "3", "options": []},
    {"question": "how many years of experience do you have in llms",
     "answer": "3", "options": []},
    {"question": "how many years of experience do you have in natural language",
     "answer": "1", "options": []},
    {"question": "how many years of experience do you have in solution engineering",
     "answer": "3", "options": []},
    {"question": "how many years of experience do you have in bpf",
     "answer": "0", "options": []},
    {"question": "filled the form",
     "answer": "No", "options": ["Yes", "No"]},
]


# ══════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════
#  QUESTIONNAIRE HELPERS
# ══════════════════════════════════════════════

def load_q() -> dict:
    if os.path.exists(QUESTIONNAIRE_FILE):
        with open(QUESTIONNAIRE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_q(q: dict):
    with open(QUESTIONNAIRE_FILE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=2, ensure_ascii=False)


def bootstrap_questionnaire(q: dict) -> int:
    """Pre-seed questionnaire from BOOTSTRAP_QA. Won't overwrite existing entries."""
    added = 0
    for entry in BOOTSTRAP_QA:
        key = qkey(entry["question"])
        if key not in q:
            q[key] = {"question": entry["question"], "answer": entry["answer"]}
            added += 1
    return added


def qkey(question: str) -> str:
    """Stable, normalized key for a question string."""
    q = re.sub(
        r"^(I am sorry I didn.t understand!|Sorry! I am not trained to answer this query[^!]*!)\s*",
        "", question
    ).strip()
    return re.sub(r"\s+", " ", q).strip().lower()


def clean_q(question: str) -> str:
    """Remove Naukri's noise prefix from a question."""
    q = re.sub(
        r"^(I am sorry I didn.t understand!|Sorry! I am not trained to answer this query[^!]*!)\s*",
        "", question
    ).strip()
    return q or question


# City preference order when options are presented
CITY_PREFERENCE = ["bengaluru", "noida", "hyderabad", "gurgaon", "gurugram", "delhi", "pune", "mumbai"]


def pick_best_city(options: list[str]) -> str | None:
    """Pick the best city from a list of options based on CITY_PREFERENCE order."""
    opts_lower = [(v.lower(), v) for v in options]
    for preferred in CITY_PREFERENCE:
        for opt_low, opt_orig in opts_lower:
            if preferred in opt_low:
                return opt_orig
    # Fallback: first option
    return options[0] if options else None


def map_to_option(raw_answer: str, opt_vals: list[str]) -> str:
    """
    Map any raw answer to the best matching option text.
    Handles: exact, case-insensitive, number→range, 0→'No experience', substring.
    Returns raw_answer unchanged if no options or no match found.
    """
    if not opt_vals:
        return raw_answer

    ra = raw_answer.strip()
    ra_lower = ra.lower()

    # 1. Exact match
    if ra in opt_vals:
        return ra

    # 2. Case-insensitive exact
    ci = next((v for v in opt_vals if v.lower() == ra_lower), None)
    if ci:
        return ci

    # 3. Numeric mapping
    try:
        num = int(ra)
        if num == 0:
            # "0" / "No experience" / "Less than 1" / "None"
            no_exp = next((v for v in opt_vals if any(
                x in v.lower() for x in ["no exp", "no ex", "none", "0", "less than", "< 1", "<1", "not"]
            )), None)
            return no_exp or opt_vals[0]
        # Try exact number match (option text is just the number)
        exact = next((v for v in opt_vals if v.strip() == str(num)), None)
        if exact:
            return exact
        # Try range match: "1-3 years", "<3 years", "3-5 years", ">8 years"
        for opt in opt_vals:
            nums = [int(n) for n in re.findall(r"\d+", opt)]
            opt_lower = opt.lower()
            if len(nums) == 1:
                # "<3" means less than 3, so 1 or 2 qualifies
                if "<" in opt and num < nums[0]:
                    return opt
                if ">" in opt and num > nums[0]:
                    return opt
                if nums[0] == num:
                    return opt
            elif len(nums) == 2 and nums[0] <= num <= nums[1]:
                return opt
    except ValueError:
        pass

    # 4. Substring match
    sub = next((v for v in opt_vals if ra_lower in v.lower() or v.lower() in ra_lower), None)
    if sub:
        return sub

    # 5. No match — return as-is (resolve() will handle it)
    return raw_answer


def lookup_answer(question: str, options: list, questionnaire: dict) -> str | None:
    """
    Generic answer resolution:
    1. Exact key match in questionnaire
    2. Best substring key match
    3. City options → pick by preference order
    4. 'experience in X' → CANDIDATE_SKILLS / AI
    Returns None → caller uses ai_propose(question)
    All found answers are passed through map_to_option() automatically.
    """
    key = qkey(question)
    opt_vals = [o.get("value", o.get("text", o)) if isinstance(o, dict) else str(o) for o in options]

    # 1. Exact key match
    if key in questionnaire:
        answer = questionnaire[key]["answer"]
        return map_to_option(answer, opt_vals)

    # 2. Best substring match — prefer longer stored keys (more specific)
    candidates = [
        (stored_key, entry)
        for stored_key, entry in questionnaire.items()
        if stored_key in key or key in stored_key
    ]
    if candidates:
        # Pick the most specific (longest) matching key
        best_key, best_entry = max(candidates, key=lambda x: len(x[0]))
        answer = best_entry["answer"]
        mapped = map_to_option(answer, opt_vals)
        if mapped != answer:
            log.info(f"  🔄 Mapped '{answer}' → '{mapped}' via option list")
        return mapped

    # 3. City selection
    if opt_vals and any(
        any(city in v.lower() for city in ["bengaluru", "hyderabad", "noida", "gurgaon", "delhi", "pune", "mumbai"])
        for v in opt_vals
    ):
        best = pick_best_city(opt_vals)
        if best:
            log.info(f"  🏙️  City pick {opt_vals} → '{best}'")
            return best

    # 4. 'experience in X' pattern
    exp_match = re.search(
        r"how many years? of experience do you have (?:in|as|with|building)\s+(.+?)\??\.?$",
        key, re.IGNORECASE
    )
    if exp_match:
        skill = exp_match.group(1).strip()
        return ai_experience_for_skill(skill, opt_vals)

    return None   # unknown — caller uses ai_propose


# Skills the candidate has meaningful experience in
CANDIDATE_SKILLS = {
    # Core (3 years)
    "python": 3, "backend": 3, "coding": 3, "software development": 3,
    "solution engineering": 3, "rest api": 3, "microservices": 3,
    "javascript": 3, "node.js": 3, "nodejs": 3, "sql": 3,
    "mysql": 3, "postgresql": 3, "cloud": 3, "aws": 3, "gcp": 3,
    "system design": 3, "iceberg": 2,
    # Moderate (1-2 years)
    "llm": 2, "llms": 2, "large language model": 2,
    "react": 2, "mongodb": 2, "docker": 1,
    "machine learning": 1, "ml": 1, "ml engineering": 1,
    "natural language processing": 1, "nlp": 1,
    "ai agents": 1, "building ai agents": 1,
    "applied ai": 1, "generative ai": 1, "gen ai": 1,
    "front end": 1, "frontend": 1,
    # Zero / minimal
    "c++": 0, "java": 0, "bpf": 0, "conversational ai": 0,
    "site reliability": 0, "sre": 0, "devops": 0,
    "incident management": 0, "compute": 0, "kubernetes": 0,
}


def ai_experience_for_skill(skill: str, options: list[str]) -> str:
    """
    Return years of experience for a specific skill from CANDIDATE_SKILLS,
    or ask AI if unknown. Then map to best matching option via map_to_option().
    """
    skill_lower = skill.lower().strip("?.")

    years = None
    for sk, yrs in CANDIDATE_SKILLS.items():
        if sk in skill_lower or skill_lower in sk:
            years = yrs
            break

    if years is None:
        prompt = f"""Candidate profile:
{CANDIDATE_PROFILE}

Question: How many years of experience do you have in {skill}?
Answer with ONLY a single integer (0, 1, 2, or 3). No other text."""
        resp = ai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5, temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
        try:
            years = int(re.search(r"\d+", raw).group())
        except Exception:
            years = 0

    log.info(f"  🔧 Skill '{skill}' → {years} years")
    return map_to_option(str(years), options) if options else str(years)


# ══════════════════════════════════════════════
#  OPENAI
# ══════════════════════════════════════════════

_client = None

def ai_client():
    global _client
    if not _client:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def ai_propose(question: str, options: list = None) -> str:
    """
    Ask GPT-4o-mini to answer a Naukri chatbot question.
    Can receive options to help choose the best one.
    """
    options_text = ""
    if options:
        options_text = "\nAvailable options:\n" + "\n".join(f"- {o}" for o in options)

    prompt = f"""You are filling a job application on behalf of a candidate.

Candidate profile:
{CANDIDATE_PROFILE}

Question: {question}{options_text}

Answer rules:
- For Yes/No questions: answer Yes or No
- For experience questions: answer with just a number (e.g. 3)
- For city/location questions: answer Gurgaon
- For CTC questions: answer the number in LPA (current=12, expected=20)
- For notice period: answer 30
- Pick one of the available options if they are provided and match well.
- Keep answers very short — one word or a number when possible.
- Do NOT explain anything, just the answer"""

    resp = ai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0,
    )
    return resp.choices[0].message.content.strip().strip('"').strip("'")


# ══════════════════════════════════════════════
#  OPTION MATCHING
# ══════════════════════════════════════════════

def resolve(raw_answer: str, naukri_options: list) -> tuple[str, str]:
    """
    Map raw_answer → (text_to_send, id_to_send) that Naukri accepts.

    Naukri chatbot has two flavours:
      a) Options with real numeric IDs → send id + matching text
      b) Options with empty IDs ("")   → send exact text, id="-1"
    """
    if not naukri_options:
        return raw_answer, "-1"

    vals = [o.get("value", o.get("text", "")) for o in naukri_options]
    ids  = [str(o.get("id", ""))              for o in naukri_options]
    has_numeric = any(
        oid.strip() not in ("", "-1", "0") and oid.strip().lstrip("-").isdigit()
        for oid in ids
    )

    # City priority list (Gurgaon > Bengaluru > Hyderabad > Noida > Delhi)
    CITY_PRIORITY = ["gurgaon", "gurugram", "bengaluru", "bangalore", "hyderabad", "noida", "delhi"]

    def find_by_text(answer: str):
        # 1. Exact match
        idx = next((i for i, v in enumerate(vals) if v.lower() == answer.lower()), None)
        if idx is not None:
            return idx
        # 2. Partial: answer is substring of option (e.g. "Bengaluru" → "Bengaluru, Karnataka")
        idx = next((i for i, v in enumerate(vals) if answer.lower() in v.lower()), None)
        if idx is not None:
            return idx
        # 3. Partial: option is substring of answer
        idx = next((i for i, v in enumerate(vals) if v.lower() in answer.lower()), None)
        if idx is not None:
            return idx
        # 4. City priority fallback: if options look like cities/locations, pick highest priority city
        for city in CITY_PRIORITY:
            city_idx = next((i for i, v in enumerate(vals) if city in v.lower()), None)
            if city_idx is not None:
                return city_idx
        return None

    if has_numeric:
        # Try match by ID first
        idx = next((i for i, oid in enumerate(ids) if oid == raw_answer), None)
        if idx is None:
            idx = find_by_text(raw_answer)
        if idx is not None:
            return vals[idx], ids[idx]
        return raw_answer, "-1"
    else:
        # Empty IDs — Naukri wants exact text
        idx = find_by_text(raw_answer)
        if idx is not None:
            return vals[idx], "-1"
        return raw_answer, "-1"


# ══════════════════════════════════════════════
#  HTTP SESSION
# ══════════════════════════════════════════════

def parse_cookies(raw: str) -> dict:
    out = {}
    for p in raw.split(";"):
        p = p.strip()
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def build_session() -> requests.Session:
    s = requests.Session()
    s.cookies.update(parse_cookies(COOKIES_RAW))
    s.cookies.set("nauk_at", NAUK_AT, domain=".naukri.com")
    s.headers.update({
        "User-Agent":       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept":           "application/json",
        "Accept-Language":  "en-GB,en-US;q=0.9,en;q=0.8",
        "Content-Type":     "application/json",
        "Origin":           "https://www.naukri.com",
        "Referer":          "https://www.naukri.com/mnjuser/recommendedjobs",
        "Sec-Fetch-Dest":   "empty",
        "Sec-Fetch-Mode":   "cors",
        "Sec-Fetch-Site":   "same-origin",
        "X-Requested-With": "XMLHttpRequest",
        "Appid":            "105",
        "Systemid":         "Naukri",
        "sec-ch-ua":        '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
        "sec-ch-ua-mobile":  "?0",
        "sec-ch-ua-platform": '"macOS"',
    })
    return s


# ══════════════════════════════════════════════
#  NAUKRI API
# ══════════════════════════════════════════════

def fetch_jobs(session: requests.Session) -> list[dict]:
    url = "https://www.naukri.com/jobapi/v2/search/recom-jobs"
    
    seen_ids = set()
    aggregated_jobs = []
    
    cluster_ids = ["similar_jobs", "profile", "preference"]
    
    for cid in cluster_ids:
        log.info(f"🔍 Fetching recommended jobs for cluster '{cid}'…")
        payload = {
            "clusterId": cid,
            "src": "recommClusterApi",
            "clusterSplitDate": {
                "apply": "2026-12-08 15:27:25",
                "preference": "2026-12-08 15:31:27",
                "profile": "2026-12-08 15:28:11",
                "similar_jobs": "2026-12-08 15:26:55"
            },
            "searches": None,
        }
        try:
            resp = session.post(url, json=payload, headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache", "Expires": "0",
                "Gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
                "appid": "105",
                "systemid": "Naukri",
                "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"'
            })
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 429):
                print(f"\n❌  Naukri API returned {e.response.status_code} Forbidden/Rate Limited.")
                print("    This is temporary. Please wait 5-10 minutes and try again.")
                print("    If it persists, refresh your cookies/token in config.json.")
                sys.exit(1)
            log.error(f"  ❌ Error fetching recom-jobs for cluster '{cid}': {e}")
            continue
        except Exception as e:
            log.error(f"  ❌ Error fetching recom-jobs for cluster '{cid}': {e}")
            continue

        data = resp.json()
        job_list = data.get("jobDetails", data.get("jobs", []))
        if not job_list:
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    job_list = v; break
        
        added_count = 0
        for j in job_list:
            jid = str(j.get("jobId", j.get("id", "")))
            if jid and jid not in seen_ids:
                seen_ids.add(jid)
                aggregated_jobs.append({
                    "id": jid,
                    "title": j.get("title", j.get("jobTitle", "Unknown")),
                    "company": j.get("companyName", j.get("company", "Unknown"))
                })
                added_count += 1
        log.info(f"   Fetched {len(job_list)} jobs ({added_count} new)")

    log.info(f"📋 Total unique aggregated recommended jobs: {len(aggregated_jobs)}")
    return aggregated_jobs


def _extract_raw_questions(data: dict) -> list:
    """
    Safely extract list of screening/chatbot questions from response dictionary.
    Handles both root-level keys and nested lists inside job details.
    """
    keys = ["questionnaire", "chatBotQuestionnaire", "screeningQuestions", "questions", "screeningQuestionnaire", "chatBotQuestions", "botQuestions"]

    # 1. Try extracting from root level
    for key in keys:
        val = data.get(key)
        if not val:
            continue
        if isinstance(val, list):
            return val
        elif isinstance(val, dict):
            for q_key in ["questions", "questionList", "list", "screeningQuestions"]:
                q_val = val.get(q_key)
                if isinstance(q_val, list):
                    return q_val

    # 2. Try extracting from nested jobs list
    jobs = data.get("jobs") or data.get("jobDetails") or []
    if isinstance(jobs, list):
        for job in jobs:
            if not isinstance(job, dict):
                continue
            for key in keys:
                val = job.get(key)
                if not val:
                    continue
                if isinstance(val, list):
                    return val
                elif isinstance(val, dict):
                    for q_key in ["questions", "questionList", "list", "screeningQuestions"]:
                        q_val = val.get(q_key)
                        if isinstance(q_val, list):
                            return q_val

    return []


def extract_api_questionnaire(data: dict, questionnaire: dict) -> int:
    """
    If the apply API response contains a questionnaire (questions + options),
    pre-resolve all answers and seed them into our questionnaire dict.
    Returns number of new questions pre-answered.
    """
    raw_qs = _extract_raw_questions(data)
    if not raw_qs:
        return 0

    seeded = 0
    for q in raw_qs:
        q_text = q.get("text") or q.get("question") or q.get("label") or q.get("questionName") or ""
        if not q_text:
            continue
        key = qkey(q_text)
        
        opts_raw = q.get("options") or q.get("choices") or q.get("answerOption") or []
        if isinstance(opts_raw, dict):
            opts_list = [{"value": str(v), "id": str(k)} for k, v in opts_raw.items()]
        else:
            opts_list = opts_raw

        # Use lookup_answer with the known options to pre-resolve
        answer = lookup_answer(q_text, opts_list, questionnaire)
        if answer is None:
            answer = ai_propose(q_text)

        if key not in questionnaire:
            questionnaire[key] = {"question": q_text, "answer": answer}
            log.info(f"  📥 Pre-answered from API: '{q_text[:55]}' → '{answer}'")
            seeded += 1

    return seeded


def do_apply(session: requests.Session, job_id: str, questionnaire: dict) -> tuple[dict, str]:
    """
    POST apply for a job. Extracts chatbot appName from response.
    Also pre-seeds any questionnaire Naukri returns in the apply response.
    Returns (response_dict, chatbot_app_name).
    """
    resp = session.post(
        "https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply",
        json={"strJobsarr": [job_id], "src": "NAUKRI_APPLY", "applySrc": "drecomm_profile",
              "logstr": "drecomm", "applyTypeId": "107", "crossdomain": False, "jquery": 1, "chatBotSD": True},
        headers={
            "authorization": f"ACCESSTOKEN = {NAUK_AT}",
            "clientid": "d3skt0p",
            "systemid": "jobseeker",
            "appid": "105",
            "Cache-Control": "max-age=0"
        },
    )
    resp.raise_for_status()
    data = resp.json()
    log.info(f"  📝 First apply response: {data}")

    # Pre-seed questionnaire from API response if available
    n = extract_api_questionnaire(data, questionnaire)
    if n:
        log.info(f"  📋 Pre-seeded {n} questions from apply API response")

    app_name = data.get("chatBotAppName", data.get("appName", f"{job_id}_apply"))
    return data, app_name


def get_api_questions(data: dict) -> dict:
    """
    Extracts all screening/chatbot questions from the apply response,
    mapping normalized qkey -> {"id": qid, "options": opt_vals, "type": q_type}
    """
    raw_qs = _extract_raw_questions(data)
    if not raw_qs:
        return {}

    mapping = {}
    for q in raw_qs:
        q_text = q.get("text") or q.get("question") or q.get("label") or q.get("questionName") or ""
        if not q_text:
            continue

        # Extract ID (numeric or string)
        qid = q.get("id") or q.get("questionId") or q.get("qId")
        if qid is not None:
            qid = str(qid)

        opts_raw = q.get("options") or q.get("choices") or q.get("answerOption") or []
        if isinstance(opts_raw, dict):
            opts_list = [{"value": str(v), "id": str(k)} for k, v in opts_raw.items()]
        else:
            opts_list = opts_raw

        opt_vals = [
            o.get("value", o.get("text", o.get("label", o)))
            if isinstance(o, dict) else str(o)
            for o in opts_list
        ]

        q_type = q.get("type") or q.get("questionType") or ""

        mapping[qkey(q_text)] = {
            "id": qid,
            "text": q_text,
            "options": opts_list,
            "opt_vals": opt_vals,
            "type": q_type
        }
    return mapping


def find_question_info(question_text: str, api_questions: dict) -> tuple[str, dict] | tuple[None, None]:
    norm_q = qkey(question_text)
    # 1. Exact normalized match
    if norm_q in api_questions:
        return api_questions[norm_q]["id"], api_questions[norm_q]

    # 2. Substring match
    for api_q_norm, info in api_questions.items():
        if api_q_norm in norm_q or norm_q in api_q_norm:
            return info["id"], info

    return None, None


def do_second_apply(session: requests.Session, job_id: str, answers: dict) -> dict:
    """
    POST apply for a job with the gathered chatbot answers (applyData).
    Called after chatbot conversation is completed.
    """
    payload = {
        "strJobsarr": [job_id],
        "src": "NAUKRI_APPLY",
        "applySrc": "drecomm_profile",
        "logstr": "drecomm",
        "applyTypeId": "107",
        "crossdomain": False,
        "jquery": 1,
        "chatBotSD": True,
        "applyData": {
            job_id: {
                "answers": answers
            }
        },
        "qupData": {}
    }

    log.info(f"  📤 Submitting final answers to apply API for job {job_id}…")

    resp = session.post(
        "https://www.naukri.com/cloudgateway-workflow/workflow-services/apply-workflow/v1/apply",
        json=payload,
        headers={
            "authorization": f"ACCESSTOKEN = {NAUK_AT}",
            "clientid": "d3skt0p",
            "systemid": "jobseeker",
            "appid": "105",
            "Cache-Control": "max-age=0"
        },
    )
    resp.raise_for_status()
    return resp.json()



def commit_save_apply(session: requests.Session, redirect_url: str) -> bool:
    """
    Perform GET request to the redirect URL to finalize/commit the application.
    """
    if not redirect_url:
        return False
    try:
        log.info(f"  💾 Committing application via saveApply…")
        # Ensure we set headers and cookies correctly
        resp = session.get(redirect_url, headers={
            "Referer": "https://www.naukri.com/mnjuser/recommendedjobs",
            "Cache-Control": "max-age=0"
        })
        resp.raise_for_status()
        if "jobapplied" in resp.text.lower() or "success" in resp.text.lower() or resp.status_code == 200:
            log.info("  🎉 Application successfully committed to Naukri!")
            return True
        else:
            log.warning(f"  ⚠️ saveApply response status: {resp.status_code}, might not have succeeded.")
            return False
    except Exception as e:
        log.error(f"  ❌ Failed to commit application via saveApply: {e}")
        return False


def chatbot(session: requests.Session, app_name: str, text: str, ans_id: str = "-1",
            sess_id: str = "", status: str = "Fresh") -> dict:
    """
    app_name: the full chatbot app name, e.g. '100826010030_apply' or
              '100826010030_100826020751_apply' for multi-job batches.
    """
    payload = {
        "input": {"text": [text], "id": [ans_id]},
        "appName": app_name, "domain": "Naukri",
        "conversation": app_name, "channel": "web",
        "status": status, "utmSource": "", "utmContent": "", "deviceType": "WEB",
    }
    if sess_id:
        payload["conversation_session_id"] = sess_id
    resp = session.post(
        "https://www.naukri.com/cloudgateway-chatbot/chatbot-services/botapi/v5/respond",
        json=payload,
        headers={"authorization": f"Bearer {NAUK_AT}", "appid": "", "systemid": ""},
    )
    resp.raise_for_status()
    return resp.json()


def extract_question(resp: dict) -> str:
    raw = " ".join(s.get("response", "") for s in resp.get("speechResponse", []) if s.get("type") == "text")
    return clean_q(raw)


# ══════════════════════════════════════════════
#  CHATBOT RUNNER  (shared by all phases)
# ══════════════════════════════════════════════

def run_chatbot(session: requests.Session, app_name: str,
                questionnaire: dict, commit: bool, api_questions: dict = None) -> tuple[str, dict]:
    """
    Drive the full chatbot Q&A loop.
    app_name: full chatbot session name (may be multi-job like 'id1_id2_apply')
    commit=False  → discover mode — collects questions, does NOT apply
    commit=True   → apply mode   — submits application
    Returns: (outcome, chatbot_answers) where outcome is "applied" | "discovered" | "failed"
    """
    sess_id, status = "", "Fresh"
    prev_q, stuck = None, 0
    send_text, send_id = "start", "-1"

    chatbot_answers = {}
    if api_questions:
        for norm_q, info in api_questions.items():
            qid = info["id"]
            if not qid:
                continue
            q_text = info.get("text") or ""
            opts = info.get("options") or []
            
            # Pre-resolve answer
            ans = lookup_answer(q_text, opts, questionnaire)
            if ans is None:
                ans = ai_propose(q_text, info.get("opt_vals") or [])
                
            if opts and ans:
                send_text, send_id = resolve(ans, opts)
                chatbot_answers[qid] = [send_text]
            elif ans:
                chatbot_answers[qid] = ans
            else:
                chatbot_answers[qid] = [] if opts else ""

    for turn in range(30):
        # ── Kick-off / send answer ──
        if turn == 0:
            resp = chatbot(session, app_name, "start", "-1", sess_id, status)
        else:
            resp = chatbot(session, app_name, send_text, send_id, sess_id, status)

        sess_id  = resp.get("conversation_session_id", sess_id)
        status   = "Continue"
        committed = resp.get("dataCommitted", False)
        node     = resp.get("currentNodeName", "")

        # Accumulate/merge answers from the server response applyData
        bot_apply_data = resp.get("applyData") or {}
        if bot_apply_data:
            for jid, job_data in bot_apply_data.items():
                if isinstance(job_data, dict):
                    ans_dict = job_data.get("answers") or {}
                    for qid, val in ans_dict.items():
                        chatbot_answers[qid] = val

        if committed:
            if not commit:
                log.info(f"  🔍 [discover] chatbot completed at node '{node}'")
                return "discovered", chatbot_answers
            else:
                log.info(f"  ✅ Applied! node='{node}'")
                return "applied", chatbot_answers

        question = extract_question(resp)
        options  = resp.get("options", [])
        opt_vals = [o.get("value", o.get("text", "")) for o in options]

        if not question:
            return ("discovered" if not commit else "applied"), chatbot_answers

        # Stuck-loop detection
        if question == prev_q:
            stuck += 1
            if stuck >= 3:
                log.warning(f"  ⚠️  Stuck on '{question[:55]}' — skipping")
                return "failed", chatbot_answers
        else:
            stuck, prev_q = 0, question

        # ── Smart answer lookup (fuzzy, city-aware, skill-aware) ──────
        raw_answer = lookup_answer(question, options, questionnaire)

        if raw_answer is not None:
            log.info(f"  📋 Found   Q: {question[:65]}")
            log.info(f"         → A: {raw_answer}")
            # Save new questions discovered at runtime
            key = qkey(question)
            if key not in questionnaire:
                questionnaire[key] = {
                    "question":  question,
                    "options":   opt_vals,
                    "answer":    raw_answer,
                    "validated": False,
                    "source":    "runtime",
                }
        else:
            # Truly unknown — ask full AI
            raw_answer = ai_propose(question, opt_vals)
            log.info(f"  🤖 AI      Q: {question[:65]}")
            log.info(f"         → A: {raw_answer}  (unvalidated)")
            key = qkey(question)
            questionnaire[key] = {
                "question":  question,
                "options":   opt_vals,
                "answer":    raw_answer,
                "validated": False,
                "source":    "ai",
            }

        send_text, send_id = resolve(raw_answer, options)
        log.info(f"       sending: text='{send_text}', id='{send_id}'")

        # Keep track of the answer for applyData
        if api_questions:
            qid, info = find_question_info(question, api_questions)
            if qid:
                if info["options"]:
                    chatbot_answers[qid] = [send_text]
                else:
                    chatbot_answers[qid] = send_text

        time.sleep(random.uniform(0.3, 0.8))

    log.warning(f"  ⚠️  Max turns reached")
    return "failed", chatbot_answers


# ══════════════════════════════════════════════
#  PHASE 1 — DISCOVER
# ══════════════════════════════════════════════

def phase_discover(session):
    print("\n" + "═"*65)
    print("🔍  PHASE 1 — DISCOVER")
    print("    Collecting all chatbot questions. No applications submitted.")
    print("═"*65 + "\n")

    questionnaire = load_q()
    added = bootstrap_questionnaire(questionnaire)
    if added:
        save_q(questionnaire)
        log.info(f"🌱 Bootstrapped {added} known answers into questionnaire")
    jobs = fetch_jobs(session)[:MAX_JOBS]
    new_q_count = 0

    for i, job in enumerate(jobs, 1):
        log.info(f"[{i}/{len(jobs)}] {job['title']} @ {job['company']}  (ID: {job['id']})")
        try:
            ar, app_name = do_apply(session, job["id"], questionnaire)
            ar_str  = json.dumps(ar).lower()
            ar_code = ar.get("responseCode", ar.get("code", 0))
            if "already" in ar_str or ar_code in (4004, 409):
                log.info("  ⏭️  Already applied — skip"); continue
            if ar.get("chatBotRequired") or ar.get("isChatBot") or "chatbot" in ar_str:
                log.info(f"  🤖 Chatbot session: {app_name}")
                before = len(questionnaire)
                run_chatbot(session, app_name, questionnaire, commit=False, api_questions=get_api_questions(ar))
                new_q_count += len(questionnaire) - before
            else:
                log.info("  ℹ️  No chatbot for this job")
        except requests.HTTPError as e:
            sc = e.response.status_code if e.response else "?"
            if sc == 422: log.info("  ⏭️  Already applied (422)")
            else: log.error(f"  ❌ HTTP {sc}: {e}")
        except Exception as e:
            log.error(f"  ❌ {e}")

        save_q(questionnaire)
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    save_q(questionnaire)
    print("\n" + "═"*65)
    print(f"✅  Discovery done! {new_q_count} new questions added (bootstrap excluded).")
    print(f"📄  Total questions in {QUESTIONNAIRE_FILE}: {len(questionnaire)}")
    print(f"\n👉  Run:  python3 naukri_apply.py --validate")
    print("═"*65)


# ══════════════════════════════════════════════
#  PHASE 2 — VALIDATE  (interactive)
# ══════════════════════════════════════════════


# ══════════════════════════════════════════════
#  PHASE 3 — APPLY
# ══════════════════════════════════════════════

def phase_apply(session):
    print("\n" + "═"*65)
    print("🚀  PHASE 3 — APPLY")
    print("═"*65 + "\n")

    questionnaire = load_q()
    added = bootstrap_questionnaire(questionnaire)
    if added:
        save_q(questionnaire)
        log.info(f"🌱 Bootstrapped {added} known answers")

    if not questionnaire:
        print(f"⚠️  questionnaire.json not found. Run --discover first or create it manually.")
        return

    applied_jobs = load_applied_jobs()

    jobs = fetch_jobs(session)[:MAX_JOBS]
    log.info(f"Will apply to {len(jobs)} jobs\n")
    results = {"applied": [], "chatbot": [], "already_applied": [], "failed": []}

    for i, job in enumerate(jobs, 1):
        log.info(f"[{i}/{len(jobs)}] {job['title']} @ {job['company']}  (ID: {job['id']})")
        if job["id"] in applied_jobs:
            log.info("  ⏭️  Already applied (tracked locally)")
            results["already_applied"].append(job)
            continue

        try:
            ar, app_name = do_apply(session, job["id"], questionnaire)
            ar_str  = json.dumps(ar).lower()
            ar_code = ar.get("responseCode", ar.get("code", 0))
            job_status = ar.get("applyStatus", {}).get(job["id"], 0)

            if "already" in ar_str or ar_code in (4004, 409) or job_status in (409001, 409, 4004):
                log.info("  ⏭️  Already applied")
                results["already_applied"].append(job)
                applied_jobs.add(job["id"])
                save_applied_jobs(applied_jobs)
                continue

            redirect_url = ar.get("applyRedirectUrl")

            api_questions = get_api_questions(ar)

            if ar.get("chatBotRequired") or ar.get("isChatBot") or "chatbot" in ar_str:
                log.info(f"  🤖 Chatbot: {app_name}")
                outcome, chatbot_answers = run_chatbot(session, app_name, questionnaire, commit=True, api_questions=api_questions)
                if outcome == "applied":
                    try:
                        sec_ar = do_second_apply(session, job["id"], chatbot_answers)
                        redirect_url = sec_ar.get("applyRedirectUrl") or redirect_url
                        log.info(f"  📝 Second apply response: {sec_ar}")
                        
                        # Log message from second apply response
                        jobs_res = sec_ar.get("jobs") or []
                        if not jobs_res:
                            status_code = sec_ar.get("statusCode")
                            msg = sec_ar.get("message")
                            if msg:
                                log.info(f"  ✉️  API Response: {msg}")
                            elif status_code is not None:
                                log.info(f"  ✉️  API Response Code: {status_code}")
                        else:
                            for job_res in jobs_res:
                                msg = job_res.get("message")
                                status = job_res.get("status")
                                if msg:
                                    log.info(f"  ✉️  API Response: {msg} (Status: {status})")
                                elif status:
                                    log.info(f"  ✉️  API Response Status: {status}")
                    except Exception as e:
                        log.error(f"  ❌ Failed to submit second apply with answers: {e}")
                    # Finalize application by hitting the saveRedirect URL
                    commit_save_apply(session, redirect_url)
                    results["chatbot"].append(job)
                    applied_jobs.add(job["id"])
                    save_applied_jobs(applied_jobs)
                else:
                    results["failed"].append(job)
            elif api_questions:
                log.info(f"  📋 Static Questionnaire present ({len(api_questions)} questions)")
                chatbot_answers = {}
                for norm_q, info in api_questions.items():
                    qid = info["id"]
                    if not qid:
                        continue
                    q_text = info.get("text") or ""
                    opts = info.get("options") or []
                    
                    ans = lookup_answer(q_text, opts, questionnaire)
                    if ans is None:
                        ans = ai_propose(q_text, info.get("opt_vals") or [])
                        
                    if opts and ans:
                        send_text, send_id = resolve(ans, opts)
                        chatbot_answers[qid] = [send_text]
                    elif ans:
                        chatbot_answers[qid] = ans
                    else:
                        chatbot_answers[qid] = [] if opts else ""
                
                try:
                    sec_ar = do_second_apply(session, job["id"], chatbot_answers)
                    redirect_url = sec_ar.get("applyRedirectUrl") or redirect_url
                    log.info(f"  📝 Second apply response: {sec_ar}")
                    
                    # Log message from second apply response
                    jobs_res = sec_ar.get("jobs") or []
                    if not jobs_res:
                        status_code = sec_ar.get("statusCode")
                        msg = sec_ar.get("message")
                        if msg:
                            log.info(f"  ✉️  API Response: {msg}")
                        elif status_code is not None:
                            log.info(f"  ✉️  API Response Code: {status_code}")
                    else:
                        for job_res in jobs_res:
                            msg = job_res.get("message")
                            status = job_res.get("status")
                            if msg:
                                log.info(f"  ✉️  API Response: {msg} (Status: {status})")
                            elif status:
                                log.info(f"  ✉️  API Response Status: {status}")
                except Exception as e:
                    log.error(f"  ❌ Failed to submit second apply with answers: {e}")
                
                commit_save_apply(session, redirect_url)
                results["chatbot"].append(job)
                applied_jobs.add(job["id"])
                save_applied_jobs(applied_jobs)
            else:
                log.info("  ✅ Applied directly")
                commit_save_apply(session, redirect_url)
                results["applied"].append(job)
                applied_jobs.add(job["id"])
                save_applied_jobs(applied_jobs)

        except requests.HTTPError as e:
            sc = e.response.status_code if e.response else "?"
            if sc == 422:
                log.info("  ⏭️  Already applied (422)")
                results["already_applied"].append(job)
                applied_jobs.add(job["id"])
                save_applied_jobs(applied_jobs)
            else:
                log.error(f"  ❌ HTTP {sc}: {e}")
                results["failed"].append(job)
        except Exception as e:
            log.error(f"  ❌ {e}"); results["failed"].append(job)

        save_q(questionnaire)           # persist any new questions found at runtime
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        log.info(f"  Waiting {delay:.1f}s…\n")
        time.sleep(delay)

    print("\n" + "═"*65)
    print("📊  SUMMARY")
    print("═"*65)
    print(f"  ✅ Applied (direct):     {len(results['applied'])}")
    print(f"  🤖 Applied (chatbot):    {len(results['chatbot'])}")
    print(f"  ⏭️  Already applied:      {len(results['already_applied'])}")
    print(f"  ❌ Failed:               {len(results['failed'])}")
    print(f"  📋 Total:                {len(jobs)}")

    out = f"naukri_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results → {out}")
    print("═"*65)


# ══════════════════════════════════════════════
#  ENTRYPOINT
# ══════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Naukri Auto-Apply")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--discover", action="store_true", help="Scan chatbots, collect questions into questionnaire.json")
    g.add_argument("--apply",    action="store_true", help="Apply to all recommended jobs using questionnaire.json")
    args = p.parse_args()

    session = build_session()
    if args.discover:
        phase_discover(session)
    else:
        phase_apply(session)


if __name__ == "__main__":
    main()
