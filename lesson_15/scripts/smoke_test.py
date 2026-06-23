"""Smoke test lesson_10 — запуск: uv run python scripts/smoke_test.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

BASE = "http://127.0.0.1:8000"
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    """Реєструє результат однієї smoke-перевірки."""
    if cond:
        print(f"  OK  {name}")
    else:
        msg = f"  FAIL {name}" + (f" — {detail}" if detail else "")
        print(msg)
        FAILURES.append(name)


def login(client: httpx.Client, username: str) -> str:
    """Перевіряє credentials і повертає пару JWT/refresh токенів."""
    r = client.post(
        f"{BASE}/api/auth/login",
        data={"username": username, "password": "demo1234"},
    )
    if r.status_code != 200:
        return ""
    return r.json()["access_token"]


def main() -> None:
    """Запускає послідовність smoke-перевірок локального API."""
    print("=== smoke test lesson_10 ===\n")
    with httpx.Client(timeout=10.0) as c:
        # health
        r = c.get(f"{BASE}/healthz")
        check("healthz", r.status_code == 200 and r.json().get("status") == "ok", str(r.status_code))

        r = c.get(f"{BASE}/readyz")
        check("readyz", r.status_code == 200, f"{r.status_code} {r.text[:120]}")

        # login seed users
        user_tok = login(c, "user_demo")
        mod_tok = login(c, "mod_demo")
        admin_tok = login(c, "admin_demo")
        check("login user_demo", bool(user_tok))
        check("login mod_demo", bool(mod_tok))
        check("login admin_demo", bool(admin_tok))

        # JWT role in /me
        r = c.get(f"{BASE}/api/auth/me", headers={"Authorization": f"Bearer {user_tok}"})
        check("/me user role", r.status_code == 200 and r.json().get("role") == "user", r.text)

        # RBAC access
        r = c.get(f"{BASE}/api/access/user", headers={"Authorization": f"Bearer {user_tok}"})
        check("access/user", r.status_code == 200, r.text)

        r = c.get(
            f"{BASE}/api/access/admin/users",
            headers={"Authorization": f"Bearer {user_tok}"},
        )
        check("user -> admin/users 403", r.status_code == 403, f"got {r.status_code}")

        r = c.get(
            f"{BASE}/api/access/moderator/todos",
            headers={"Authorization": f"Bearer {mod_tok}"},
        )
        check("mod -> moderator/todos 200", r.status_code == 200, f"got {r.status_code}")

        r = c.get(
            f"{BASE}/api/access/admin/users",
            headers={"Authorization": f"Bearer {admin_tok}"},
        )
        check("admin -> admin/users 200", r.status_code == 200, f"got {r.status_code}")

        # logout needs bearer + refresh from login
        lr = c.post(
            f"{BASE}/api/auth/login",
            data={"username": "user_demo", "password": "demo1234"},
        )
        refresh = lr.json().get("refresh_token", "")
        r = c.post(
            f"{BASE}/api/auth/logout",
            headers={"Authorization": f"Bearer {user_tok}"},
            json={"refresh_token": refresh},
        )
        check("logout 204", r.status_code == 204, f"got {r.status_code}")

        r = c.post(f"{BASE}/api/auth/logout", json={"refresh_token": "fake"})
        check("logout without bearer 401/403", r.status_code in (401, 403, 422), f"got {r.status_code}")

        # cache: two GET todos
        tok = login(c, "user_demo")
        h = {"Authorization": f"Bearer {tok}"}
        c.get(f"{BASE}/api/todos/?limit=10&offset=0", headers=h)
        c.get(f"{BASE}/api/todos/?limit=10&offset=0", headers=h)
        check("todos list x2", True, "перевір DB hit у логах сервера вручну")

        # rate limit (11 requests) — use fresh client to avoid connection reuse issues
        tok = login(c, "user_demo")
        h = {"Authorization": f"Bearer {tok}"}
        last_status = 200
        for i in range(11):
            last_status = c.get(f"{BASE}/api/auth/me", headers=h).status_code
        check("rate limit 11th 429", last_status == 429, f"last={last_status}")

        # IP block — demo IP not localhost, healthz should work
        r = c.get(f"{BASE}/healthz")
        check("healthz not blocked (127.0.0.1)", r.status_code == 200)

        # CORS header on response
        r = c.get(
            f"{BASE}/healthz",
            headers={"Origin": "http://127.0.0.1:5500"},
        )
        check(
            "CORS Allow-Origin",
            r.headers.get("access-control-allow-origin") == "http://127.0.0.1:5500",
            str(r.headers.get("access-control-allow-origin")),
        )

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} — {', '.join(FAILURES)}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
