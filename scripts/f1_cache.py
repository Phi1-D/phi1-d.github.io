"""Save a backup copy of the F1 data the dashboard uses, in case the live API is unreachable from a tablet.

Run by .github/workflows/f1-cache.yml. Writes f1/cache/*.json with the same names the page asks for.
"""
import json
import os
import time
import urllib.request

API = "https://api.jolpi.ca/ergast/f1/"
OUT = os.path.join(os.path.dirname(__file__), "..", "f1", "cache")


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "grand-prix-dashboard-cache/1.0"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:  # brief network blips: retry
            if i == 3:
                print(f"::warning::{path} failed: {e}")
                return None
            time.sleep((5, 15, 30)[i])
        finally:
            time.sleep(0.5)  # stay well inside the API's rate limit


def save(name, data):
    if data is None:
        return
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))


def main():
    os.makedirs(OUT, exist_ok=True)
    sched = get("current.json")
    save("schedule", sched)
    season = int(sched["MRData"]["RaceTable"]["season"]) if sched else time.gmtime().tm_year
    jobs = {
        "next-schedule": f"{season + 1}.json",
        "drivers": "current/driverStandings.json",
        "constructors": "current/constructorStandings.json",
        "last": "current/last/results.json",
        "prev-drivers": f"{season - 1}/driverStandings.json",
        "prev-constructors": f"{season - 1}/constructorStandings.json",
        "prev-last": f"{season - 1}/last/results.json",
    }
    for name, path in jobs.items():
        save(name, get(path))


if __name__ == "__main__":
    main()
