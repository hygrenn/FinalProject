import httpx

_KIS_REAL_URL = "https://openapi.koreainvestment.com:9443"
_KIS_PAPER_URL = "https://openapivts.koreainvestment.com:29443"


async def test_kis_connection(app_key: str, app_secret: str, mode: str) -> bool:
    base_url = _KIS_PAPER_URL if mode == "paper" else _KIS_REAL_URL
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": app_key,
                    "appsecret": app_secret,
                },
                headers={"Content-Type": "application/json"},
            )
            return resp.status_code == 200 and bool(resp.json().get("access_token"))
        except Exception:
            return False
