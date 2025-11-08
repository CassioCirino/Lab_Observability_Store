import subprocess, threading, time, os

def run_stress_once(duration=60, cpu_workers=2, mem_mb=200):
    # try stress-ng if present
    try:
        subprocess.run(["stress-ng","--cpu",str(cpu_workers),"--vm", "1", "--vm-bytes", f"{mem_mb}M", "--timeout", f"{duration}s"], check=True)
        return
    except Exception:
        pass

    # fallback: CPU busy loops and allocate memory
    stop = False
    def busy():
        while not stop:
            x=0
            for i in range(1000000):
                x += i*i
    threads=[]
    for _ in range(cpu_workers):
        t=threading.Thread(target=busy,daemon=True)
        t.start()
        threads.append(t)
    # allocate memory
    alloc=[]
    try:
        alloc.append(bytearray(mem_mb*1024*1024))
    except Exception:
        pass
    time.sleep(duration)
    stop=True
    time.sleep(1)

if __name__=="__main__":
    run_stress_once(30)
