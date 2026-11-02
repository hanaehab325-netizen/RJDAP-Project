import subprocess
import sys
import time
import re
import csv
from pathlib import Path

root = Path(__file__).resolve().parent
logs = root / "logs"
logs.mkdir(exist_ok=True)
results = []

for n in range(1, 6):
    files = [open(logs / f"{name}_{n}.log", "w")
             for name in ["server", "w1", "w2", "w3", "w4"]]

    server = subprocess.Popen(
        [sys.executable, "-u", "server.py"],
        cwd=root, stdout=files[0], stderr=subprocess.STDOUT
    )
    workers = []
    error = None

    try:
        for _ in range(100):
            if "waiting for 4 workers" in (logs / f"server_{n}.log").read_text():
                break
            if server.poll() is not None:
                raise RuntimeError("Server failed to start")
            time.sleep(0.1)
        else:
            raise TimeoutError("Server not ready")

        for i in range(1, 5):
            workers.append(subprocess.Popen(
                [sys.executable, "-u", "worker.py", str(i)],
                cwd=root, stdout=files[i], stderr=subprocess.STDOUT
            ))

        server.wait(timeout=60)
        for worker in workers:
            worker.wait(timeout=5)

    except (TimeoutError, subprocess.TimeoutExpired, RuntimeError) as e:
        error = str(e)

    finally:
        for p in [server, *workers]:
            if p.poll() is None:
                p.kill()
            p.wait()
        for f in files:
            f.close()

    text = (logs / f"server_{n}.log").read_text()
    worker_text = "".join(
        (logs / f"w{i}_{n}.log").read_text() for i in range(1, 5)
    )

    tasks = re.findall(r"Task (\d+) done", text)
    sums = re.findall(
        r"Task (\d+): (\d+) \+ (\d+) = (\d+)", worker_text
    )
    duration = re.search(
        r"All 1000 tasks completed in ([\d.]+)s", text
    )

    passed = (
        error is None
        and server.returncode == 0
        and all(w.returncode == 0 for w in workers)
        and len(workers) == 4
        and len(tasks) == len(set(tasks)) == len(sums) == 1000
        and len({t for t, a, b, c in sums}) == 1000
        and all(int(a) == int(t) and int(b) == 2 * int(t)
                and int(c) == 3 * int(t) for t, a, b, c in sums)
        and all(f"Worker {i} registered:" in text for i in range(1, 5))
        and text.count("SEND ACK_RESULT") == 1000
        and duration is not None
    )

    status = "PASS" if passed else "FAIL"
    seconds = duration.group(1) if duration else ""
    results.append([n, status, seconds])
    print(f"Run {n}: {status} | {len(tasks)}/1000 tasks")

    if error:
        print("Error:", error)

with open(logs / "baseline_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Run", "Status", "Seconds"])
    writer.writerows(results)

sys.exit(1 if any(r[1] == "FAIL" for r in results) else 0)
