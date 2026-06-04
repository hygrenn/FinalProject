# backend/services/kis_service.py
from __future__ import annotations

import logging
from datetime import date as _date, datetime, timedelta, timezone

import httpx
from fastapi import HTTPException

_logger = logging.getLogger(__name__)
_KST = timezone(timedelta(hours=9))

from core.security import decrypt_aes
from services.kis_token_service import get_access_token

_REAL_URL = "https://openapi.koreainvestment.com:9443"
_PAPER_URL = "https://openapivts.koreainvestment.com:29443"

_TR_IDS = {
    "buy":     {"real": "TTTC0802U", "paper": "VTTC0802U"},
    "sell":    {"real": "TTTC0801U", "paper": "VTTC0801U"},
    "cancel":  {"real": "TTTC0803U", "paper": "VTTC0803U"},
    "balance": {"real": "TTTC8434R", "paper": "VTTC8434R"},
    "fill":    {"real": "TTTC8001R", "paper": "VTTC8001R"},
}


def _base_url(mode: str) -> str:
    return _PAPER_URL if mode == "paper" else _REAL_URL


def _tr_id(action: str, mode: str) -> str:
    return _TR_IDS[action][mode]


def _get_keys(user) -> tuple[str, str, str]:
    """user.mode에 따라 (app_key, app_secret, account_no) 복호화 반환."""
    mode = user.mode
    if mode == "paper":
        if not user.kis_paper_key_enc:
            raise HTTPException(status_code=400, detail="모의투자 KIS 키가 등록되지 않았습니다.")
        return (
            decrypt_aes(user.kis_paper_key_enc),
            decrypt_aes(user.kis_paper_secret_enc),
            user.kis_paper_account_no,
        )
    else:
        if not user.kis_real_key_enc:
            raise HTTPException(status_code=400, detail="실거래 KIS 키가 등록되지 않았습니다.")
        return (
            decrypt_aes(user.kis_real_key_enc),
            decrypt_aes(user.kis_real_secret_enc),
            user.kis_real_account_no,
        )


async def _headers(user) -> dict:
    app_key, app_secret, _ = _get_keys(user)
    token = await get_access_token(app_key, app_secret, user.mode)
    return {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "content-type": "application/json",
        "custtype": "P",
    }


async def place_order(
    user,
    stock_code: str,
    order_type: str,
    price_type: str,
    quantity: int,
    price: int = 0,
) -> dict:
    """
    KIS 주문 실행.
    order_type: "BUY" | "SELL"
    price_type: "MARKET" | "LIMIT"
    반환: {kis_order_no}
    """
    _, _, account_no = _get_keys(user)
    action = "buy" if order_type == "BUY" else "sell"
    ord_dvsn = "01" if price_type == "MARKET" else "00"

    headers = await _headers(user)
    headers["tr_id"] = _tr_id(action, user.mode)

    body = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": account_no[8:] if len(account_no) > 8 else "01",
        "PDNO": stock_code,
        "ORD_DVSN": ord_dvsn,
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price) if price_type == "LIMIT" else "0",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_base_url(user.mode)}/uapi/domestic-stock/v1/trading/order-cash",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"KIS 주문 실패: {exc.response.text}") from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"KIS 연결 실패: {exc}") from exc

    if data.get("rt_cd") != "0":
        raise HTTPException(status_code=400, detail=f"KIS 주문 거부: {data.get('msg1', '')}")

    return {"kis_order_no": data["output"]["ODNO"]}


async def cancel_order(user, kis_order_no: str) -> dict:
    """미체결 주문 취소."""
    _, _, account_no = _get_keys(user)
    headers = await _headers(user)
    headers["tr_id"] = _tr_id("cancel", user.mode)

    body = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": account_no[8:] if len(account_no) > 8 else "01",
        "KRX_FWDG_ORD_ORGNO": "",
        "ORGN_ODNO": kis_order_no,
        "ORD_DVSN": "00",
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": "0",
        "ORD_UNPR": "0",
        "QTY_ALL_ORD_YN": "Y",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_base_url(user.mode)}/uapi/domestic-stock/v1/trading/order-rvsecncl",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"KIS 취소 실패: {exc}") from exc

    if data.get("rt_cd") != "0":
        raise HTTPException(status_code=400, detail=f"KIS 취소 거부: {data.get('msg1', '')}")

    return {"cancelled": True}


async def poll_fill(user, kis_order_no: str) -> dict | None:
    """
    체결 확인.
    반환: {executed_price, filled_qty, filled_at} or None (미체결)
    """
    _, _, account_no = _get_keys(user)
    headers = await _headers(user)
    headers["tr_id"] = _tr_id("fill", user.mode)

    params = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": account_no[8:] if len(account_no) > 8 else "01",
        "INQR_STRT_DT": "",
        "INQR_END_DT": "",
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN": "00",
        "PDNO": "",
        "CCLD_DVSN": "01",
        "ORD_GNO_BRNO": "",
        "ODNO": kis_order_no,
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_base_url(user.mode)}/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        _logger.error("poll_fill KIS 조회 실패 (order_no=%s): %s", kis_order_no, exc)
        return None

    output = data.get("output1", [])
    for item in output:
        if item.get("odno") == kis_order_no and item.get("ccld_dvsn") == "1":
            return {
                "executed_price": int(item.get("avg_prvs", 0)),
                "filled_qty": int(item.get("tot_ccld_qty", 0)),
                "filled_at": _parse_ord_tmd(item.get("ord_tmd", "")),
            }
    return None


def _parse_ord_tmd(ord_tmd: str) -> datetime | None:
    """KIS ord_tmd (HHMMSS) → KST aware datetime (today 기준)."""
    if not ord_tmd or len(ord_tmd) < 6:
        return None
    try:
        today = _date.today()
        h, m, s = int(ord_tmd[0:2]), int(ord_tmd[2:4]), int(ord_tmd[4:6])
        return datetime(today.year, today.month, today.day, h, m, s, tzinfo=_KST)
    except (ValueError, IndexError):
        return None


async def get_balance(user) -> dict:
    """예수금 조회."""
    _, _, account_no = _get_keys(user)
    headers = await _headers(user)
    headers["tr_id"] = _tr_id("balance", user.mode)

    params = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": account_no[8:] if len(account_no) > 8 else "01",
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{_base_url(user.mode)}/uapi/domestic-stock/v1/trading/inquire-balance",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"잔고 조회 실패: {exc}") from exc

    output2 = data.get("output2", [{}])[0]
    return {
        "cash": int(output2.get("dnca_tot_amt", 0)),
        "total_eval": int(output2.get("tot_evlu_amt", 0)),
    }


async def test_kis_connection(app_key: str, app_secret: str, mode: str) -> bool:
    """KIS 연결 테스트 (기존 함수 유지)."""
    base_url = _PAPER_URL if mode == "paper" else _REAL_URL
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{base_url}/oauth2/tokenP",
                json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
                headers={"Content-Type": "application/json"},
            )
            return resp.status_code == 200 and bool(resp.json().get("access_token"))
        except Exception:
            return False
