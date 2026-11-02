import argparse, json, os, subprocess, sys, time

ap = argparse.ArgumentParser()
ap.add_argument("--host", default="127.0.0.1")
ap.add_argument("--port", type=int, default=5000)
ap.add_argument("--tasks", type=int, default=1000)
ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--timeout", type=int, default=120)
a = ap.parse_args()

run_dir = os.path.join("results", time.strftime("baseline_%Y%m%d_%H%M%S"))
os.makedirs(run_dir)
summary_file = os.path.join(run_dir, "summary.json")
procs, logs = [], []

def spawn(name, args):
    log = open(os.path.join(run_dir, name + ".log"), "w")
    logs.append(log)
    p = subprocess.Popen([sys.executable] + args, stdout=log, stderr=subprocess.STDOUT)
    procs.append(p)
    return p

ok = False
try:
    net = ["--host", a.host, "--port", str(a.port)]
    server = spawn("server", ["server.py", *net, "--tasks", str(a.tasks),
                              "--summary", summary_file])
    time.sleep(1)  # let the server bind its socket
    for i in range(1, a.workers + 1):
        spawn(f"worker{i}", ["worker.py", "--id", str(i), *net])

    start = time.time()
    code = server.wait(timeout=a.timeout)
    wall = time.time() - start

    with open(summary_file) as f:
        s = json.load(f)

    checks = {
        "server exit code 0": code == 0,
        f"{a.tasks} tasks completed": s["completed"] == a.tasks,
        "no reassignments": s["reassigned_task_count"] == 0,
        "no duplicate results": s["duplicate_results_dropped"] == 0,
    }
    for name, passed in checks.items():
        print(("PASS  " if passed else "FAIL  ") + name)
    print(f"Wall time: {wall:.2f}s | Server time: {s['total_completion_time']}")
    ok = all(checks.values())
except subprocess.TimeoutExpired:
    print(f"FAIL  timeout after {a.timeout}s")
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    print("FAIL  missing or invalid summary:", e)
finally:
    for p in procs:
        if p.poll() is None:
            p.terminate()
    for p in procs:
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()
    for l in logs:
        l.close()

print("BASELINE:", "PASS" if ok else "FAIL", "| logs in", run_dir)
sys.exit(0 if ok else 1)
