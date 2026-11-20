import asyncio
import base64
import json
import subprocess
import urllib.request
import websockets

ARTIFACT_DIR = r"C:\Users\erlan\.gemini\antigravity\brain\9f25c386-df19-4b3a-8c85-5edca4cddd01"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9444

async def main():
    # 0. Get real teacher token from API
    login_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/auth/login",
        data=json.dumps({"username": "teacher", "password": "themis_prof_2026"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(login_req) as resp:
        login_data = json.loads(resp.read().decode())
    token = login_data["token"]
    print(f"Logged in as teacher, token: {token[:20]}...")

    # 1. Start Chrome with dedicated debugging port and fresh profile
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={CDP_PORT}",
        r"--user-data-dir=C:\Users\erlan\AppData\Local\Temp\chrome_themis_verify2",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-gpu"
    ])
    print(f"Launched Chrome PID {proc.pid}")

    for _ in range(20):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=1) as resp:
                data = json.loads(resp.read().decode())
                print(f"CDP ready: {data.get('Browser')}")
                break
        except Exception:
            await asyncio.sleep(0.5)
    else:
        raise RuntimeError("Chrome CDP did not become ready in time")

    try:
        req = urllib.request.Request(f"http://127.0.0.1:{CDP_PORT}/json/new?http://127.0.0.1:8000", method="PUT")
        with urllib.request.urlopen(req) as resp:
            target = json.loads(resp.read().decode())
        ws_url = target["webSocketDebuggerUrl"]
        print(f"Connecting to ws: {ws_url}")

        async with websockets.connect(ws_url) as ws:
            msg_id = 0
            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                payload = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    res = json.loads(await ws.recv())
                    if res.get("id") == msg_id:
                        return res.get("result", {})

            await send("Page.enable")
            await send("Runtime.enable")
            await send("Emulation.setDeviceMetricsOverride", {
                "width": 1440,
                "height": 1100,
                "deviceScaleFactor": 1,
                "mobile": False
            })

            await asyncio.sleep(2.0)

            # Log in as teacher in localStorage and reload
            login_js = f"""
            (() => {{
                localStorage.setItem('themis_auth_token', '{token}');
                location.reload();
            }})()
            """
            await send("Runtime.evaluate", {"expression": login_js})
            await asyncio.sleep(3.5)

            # Switch to professor view, select student K, open accordion, scroll
            select_js = """
            (async () => {
                if (typeof switchView === 'function') {
                    switchView('professor');
                }
                if (typeof renderEvidenceCard === 'function') {
                    await renderEvidenceCard('stud_aai_042');
                }
                const transBody = document.getElementById('evidence-transcript-body');
                if (transBody && transBody.classList.contains('hidden') && typeof toggleEvidenceTranscript === 'function') {
                    toggleEvidenceTranscript();
                }
                const panel = document.getElementById('evidence-card-panel');
                if (panel) {
                    panel.scrollIntoView({ behavior: 'instant', block: 'center' });
                }
                return {
                    view: window.currentView,
                    selected: window.selectedReportStudentId,
                    card_title: document.querySelector('#evidence-card-content h3')?.textContent,
                    formula_text: document.querySelector('#evidence-card-content strong')?.textContent
                };
            })()
            """
            eval_res = await send("Runtime.evaluate", {"expression": select_js, "awaitPromise": True, "returnByValue": True})
            print("Selected Student K in dashboard:", eval_res)
            await asyncio.sleep(2.0)

            # Capture desktop screenshot
            shot_desktop = await send("Page.captureScreenshot", {"format": "png"})
            img_desktop = base64.b64decode(shot_desktop["data"])
            out_desktop = f"{ARTIFACT_DIR}\\desktop_evidence_card.png"
            with open(out_desktop, "wb") as f:
                f.write(img_desktop)
            print(f"SUCCESS: Desktop screenshot saved ({len(img_desktop)} bytes) -> {out_desktop}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
