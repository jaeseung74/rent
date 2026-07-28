import json
from typing import Any, Optional
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------
# 1. 앱의 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="2026년 송파구 전월세 데이터",
    page_icon="🏠",
    layout="wide",
)

# 서울열린데이터광장 API 기본 정보입니다.
BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE_NAME = "tbLnOpendataRentV"
REQUEST_TYPE = "json"

# 이번 앱에서 사용할 조회 조건입니다.
TARGET_YEAR = "2026"
TARGET_GU_CODE = "11710"
TARGET_GU_NAME = "송파구"

# 서울열린데이터광장은 한 번에 최대 1,000건까지 요청할 수 있습니다.
PAGE_SIZE = 1000


# ---------------------------------------------------------
# 2. 사용자에게 보여줄 오류 메시지
# ---------------------------------------------------------
API_ERROR_MESSAGES = {
    "ERROR-300": "필수 요청값이 빠졌습니다. API 요청 형식을 확인해 주세요.",
    "INFO-100": "인증키가 유효하지 않습니다. Streamlit 비밀 금고의 SEOUL_KEY를 확인해 주세요.",
    "ERROR-301": "요청 파일 형식이 올바르지 않습니다.",
    "ERROR-310": "요청한 API 서비스를 찾을 수 없습니다.",
    "ERROR-331": "데이터 요청 시작 위치가 올바르지 않습니다.",
    "ERROR-332": "데이터 요청 종료 위치가 올바르지 않습니다.",
    "ERROR-333": "데이터 요청 위치는 정수여야 합니다.",
    "ERROR-334": "요청 시작 위치가 종료 위치보다 큽니다.",
    "ERROR-335": "샘플 인증키는 한 번에 최대 5건만 요청할 수 있습니다.",
    "ERROR-336": "한 번에 요청할 수 있는 최대 데이터 수는 1,000건입니다.",
    "ERROR-500": "서울열린데이터광장 서버에서 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
    "ERROR-600": "서울열린데이터광장 데이터베이스 연결에 문제가 발생했습니다.",
    "ERROR-601": "서울열린데이터광장 내부 데이터 처리 중 오류가 발생했습니다.",
    "INFO-200": "조건에 맞는 데이터가 없습니다.",
}


class SeoulAPIError(Exception):
    """서울열린데이터광장 API 오류를 구분하기 위한 사용자 정의 예외입니다."""


def find_fault_info(data: Any) -> Optional[Any]:
    """
    JSON 응답 안에 faultInfo가 있는지 재귀적으로 찾습니다.
    faultInfo는 인증 또는 요청 형식에 문제가 있을 때 올 수 있습니다.
    """
    if isinstance(data, dict):
        if "faultInfo" in data:
            return data["faultInfo"]

        for value in data.values():
            found = find_fault_info(value)
            if found is not None:
                return found

    elif isinstance(data, list):
        for item in data:
            found = find_fault_info(item)
            if found is not None:
                return found

    return None


def format_fault_message(fault_info: Any) -> str:
    """faultInfo의 코드와 메시지를 읽기 쉬운 한국어 문장으로 바꿉니다."""
    if not isinstance(fault_info, dict):
        return str(fault_info)

    code = (
        fault_info.get("errorCode")
        or fault_info.get("CODE")
        or fault_info.get("code")
        or ""
    )
    message = (
        fault_info.get("errorMessage")
        or fault_info.get("MESSAGE")
        or fault_info.get("message")
        or fault_info.get("faultString")
        or ""
    )

    if code and message:
        return f"{message} (오류 코드: {code})"
    if message:
        return str(message)
    if code:
        return f"오류 코드: {code}"

    return json.dumps(fault_info, ensure_ascii=False)


def build_request_url(api_key: str, start_index: int, end_index: int) -> str:
    """
    API 요청 주소를 만듭니다.

    선택 인자는 공식 문서에 나온 순서대로 URL 뒤에 붙입니다.
    여기서는 접수연도 2026과 송파구 코드 11710을 API 단계에서 지정합니다.
    """
    safe_key = quote(str(api_key), safe="")

    return (
        f"{BASE_URL}/{safe_key}/{REQUEST_TYPE}/{SERVICE_NAME}/"
        f"{start_index}/{end_index}/{TARGET_YEAR}/{TARGET_GU_CODE}/"
    )


def request_one_page(
    api_key: str,
    start_index: int,
    end_index: int,
) -> tuple[list[dict[str, Any]], int]:
    """API에서 한 페이지의 JSON 데이터를 요청합니다."""
    url = build_request_url(api_key, start_index, end_index)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise SeoulAPIError(
            "서울열린데이터광장 서버의 응답이 늦어 요청 시간이 초과되었습니다. "
            "잠시 후 다시 시도해 주세요."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise SeoulAPIError(
            "서울열린데이터광장 서버에 연결하지 못했습니다. "
            "인터넷 연결 상태를 확인한 뒤 다시 시도해 주세요."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "알 수 없음"
        raise SeoulAPIError(
            f"서울열린데이터광장 서버가 HTTP 오류를 반환했습니다. "
            f"(상태 코드: {status_code})"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise SeoulAPIError(
            "API 요청 중 예상하지 못한 네트워크 오류가 발생했습니다."
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise SeoulAPIError(
            "서버 응답을 JSON으로 해석하지 못했습니다. "
            "서울열린데이터광장 서비스 상태를 확인해 주세요."
        ) from exc

    # 응답 어디에든 faultInfo가 있으면 정상 데이터로 처리하지 않습니다.
    fault_info = find_fault_info(payload)
    if fault_info is not None:
        raise SeoulAPIError(
            "서울열린데이터광장 API가 오류 정보를 반환했습니다. "
            + format_fault_message(fault_info)
        )

    # 정상 응답은 서비스명(tbLnOpendataRentV)을 최상위 키로 가집니다.
    # 인증키 오류 등 일부 오류 응답은 RESULT가 바로 최상위에 올 수도 있습니다.
    if isinstance(payload, dict) and SERVICE_NAME in payload:
        service_data = payload[SERVICE_NAME]
    elif isinstance(payload, dict) and "RESULT" in payload:
        service_data = payload
    else:
        raise SeoulAPIError(
            "API 응답 구조가 예상과 다릅니다. "
            "서울열린데이터광장 서비스가 정상인지 확인해 주세요."
        )

    if not isinstance(service_data, dict):
        raise SeoulAPIError("API 응답의 데이터 형식이 올바르지 않습니다.")

    result = service_data.get("RESULT", {})
    result_code = str(result.get("CODE", "")).strip()
    result_message = str(result.get("MESSAGE", "")).strip()

    # INFO-200은 오류라기보다 조회 결과가 없다는 뜻입니다.
    if result_code == "INFO-200":
        return [], 0

    if result_code != "INFO-000":
        friendly_message = API_ERROR_MESSAGES.get(
            result_code,
            result_message or "알 수 없는 API 오류가 발생했습니다.",
        )
        raise SeoulAPIError(
            f"{friendly_message}"
            + (f" (응답 코드: {result_code})" if result_code else "")
        )

    rows = service_data.get("row", [])

    # 데이터가 1건일 때 사전(dict)으로 올 가능성까지 대비합니다.
    if isinstance(rows, dict):
        rows = [rows]
    elif not isinstance(rows, list):
        rows = []

    try:
        total_count = int(service_data.get("list_total_count", len(rows)))
    except (TypeError, ValueError):
        total_count = len(rows)

    return rows, total_count


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_songpa_data(_api_key: str) -> tuple[list[dict[str, Any]], int]:
    """
    2026년 송파구 전월세 데이터를 모두 가져옵니다.

    API의 1회 요청 제한이 1,000건이므로 여러 번 나누어 요청합니다.
    결과는 1시간 동안 캐시하여 같은 데이터를 반복 요청하지 않도록 합니다.
    """
    first_rows, total_count = request_one_page(_api_key, 1, PAGE_SIZE)
    all_rows = list(first_rows)

    # 첫 페이지 이후의 데이터가 있으면 1,000건씩 추가 요청합니다.
    for start_index in range(PAGE_SIZE + 1, total_count + 1, PAGE_SIZE):
        end_index = min(start_index + PAGE_SIZE - 1, total_count)
        page_rows, _ = request_one_page(_api_key, start_index, end_index)
        all_rows.extend(page_rows)

    # API 요청 조건과 별개로, 앱에서도 연도와 자치구를 다시 확인합니다.
    # 혹시 다른 지역이나 다른 연도의 데이터가 섞여도 화면에 표시되지 않습니다.
    filtered_rows = [
        row
        for row in all_rows
        if str(row.get("RCPT_YR", "")).strip() == TARGET_YEAR
        and str(row.get("CGG_CD", "")).strip() == TARGET_GU_CODE
        and str(row.get("CGG_NM", "")).strip() == TARGET_GU_NAME
    ]

    return filtered_rows, total_count


# ---------------------------------------------------------
# 3. 화면 구성
# ---------------------------------------------------------
st.title("🏠 2026년 송파구 전월세 JSON 데이터")
st.write(
    "서울열린데이터광장의 **부동산 전월세가 정보 API**에서 "
    "접수연도 2026년, 송파구 데이터만 불러옵니다."
)
st.caption(
    "인증키는 코드에 저장하지 않고 Streamlit 비밀 금고의 "
    "`SEOUL_KEY`에서만 읽습니다."
)

# 인증키를 Streamlit 비밀 금고에서 가져옵니다.
# 키가 없을 때는 실제 인증키를 화면에 노출하지 않고 설정 방법만 안내합니다.
try:
    seoul_key = str(st.secrets["SEOUL_KEY"]).strip()
except Exception:
    st.error(
        "비밀 금고에서 `SEOUL_KEY`를 찾지 못했습니다. "
        "Streamlit Cloud의 App settings → Secrets에 "
        '`SEOUL_KEY = "발급받은 인증키"` 형식으로 등록해 주세요.'
    )
    st.stop()

if not seoul_key:
    st.error(
        "`SEOUL_KEY` 값이 비어 있습니다. "
        "Streamlit Cloud 비밀 금고에 유효한 인증키를 입력해 주세요."
    )
    st.stop()

# 버튼을 누른 뒤에도 슬라이더 등의 조작으로 데이터가 사라지지 않도록
# session_state에 조회 결과를 저장합니다.
if "songpa_rows" not in st.session_state:
    st.session_state.songpa_rows = None
if "api_total_count" not in st.session_state:
    st.session_state.api_total_count = 0

if st.button("2026년 송파구 데이터 불러오기", type="primary"):
    try:
        with st.spinner("서울열린데이터광장에서 데이터를 불러오는 중입니다..."):
            rows, api_total_count = fetch_all_songpa_data(seoul_key)

        st.session_state.songpa_rows = rows
        st.session_state.api_total_count = api_total_count

        if rows:
            st.success(f"2026년 송파구 데이터 {len(rows):,}건을 불러왔습니다.")
        else:
            st.info("2026년 송파구에 해당하는 데이터가 없습니다.")

    except SeoulAPIError as exc:
        st.session_state.songpa_rows = None
        st.session_state.api_total_count = 0
        st.error(str(exc))
    except Exception:
        st.session_state.songpa_rows = None
        st.session_state.api_total_count = 0
        st.error(
            "데이터 처리 중 예상하지 못한 오류가 발생했습니다. "
            "잠시 후 다시 시도해 주세요."
        )

rows = st.session_state.songpa_rows

if rows is not None:
    if not rows:
        st.info("표시할 데이터가 없습니다.")
        st.stop()

    dataframe = pd.DataFrame(rows)

    # API 출력값의 원래 순서에 가깝게 열을 정렬합니다.
    preferred_columns = [
        "RCPT_YR",
        "CGG_CD",
        "CGG_NM",
        "STDG_CD",
        "STDG_NM",
        "LOTNO_SE",
        "LOTNO_SE_NM",
        "MNO",
        "SNO",
        "FLR",
        "CTRT_DAY",
        "RENT_SE",
        "RENT_AREA",
        "GRFE",
        "RTFE",
        "BLDG_NM",
        "ARCH_YR",
        "BLDG_USG",
        "CTRT_PRD",
        "NEW_UPDT_YN",
        "CTRT_UPDT_USE_YN",
        "BFR_GRFE",
        "BFR_RTFE",
    ]
    ordered_columns = [
        column for column in preferred_columns if column in dataframe.columns
    ]
    extra_columns = [
        column for column in dataframe.columns if column not in ordered_columns
    ]
    dataframe = dataframe[ordered_columns + extra_columns]

    # 여러 페이지에서 받은 row를 하나로 합친 JSON 문서입니다.
    full_json = {
        SERVICE_NAME: {
            "list_total_count": len(rows),
            "RESULT": {
                "CODE": "INFO-000",
                "MESSAGE": "정상 처리되었습니다",
            },
            "row": rows,
        }
    }

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("API 조회 건수", f"{st.session_state.api_total_count:,}건")
    metric2.metric("조건 검증 후 건수", f"{len(dataframe):,}건")
    metric3.metric("열 개수", f"{len(dataframe.columns):,}개")

    st.subheader("데이터 형태")
    st.write(f"행: **{dataframe.shape[0]:,}개**, 열: **{dataframe.shape[1]:,}개**")

    dtype_table = pd.DataFrame(
        {
            "열 이름": dataframe.columns,
            "Pandas 자료형": [str(dtype) for dtype in dataframe.dtypes],
        }
    )
    st.dataframe(dtype_table, width="stretch", hide_index=True)

    st.subheader("표 형태 데이터")
    st.dataframe(
        dataframe,
        width="stretch",
        height=520,
        hide_index=True,
    )

    st.subheader("JSON 데이터 미리보기")
    max_preview = min(500, len(rows))
    default_preview = min(50, max_preview)

    preview_count = st.slider(
        "화면에 표시할 JSON 행 수",
        min_value=1,
        max_value=max_preview,
        value=default_preview,
    )

    preview_json = {
        SERVICE_NAME: {
            "list_total_count": len(rows),
            "RESULT": {
                "CODE": "INFO-000",
                "MESSAGE": "정상 처리되었습니다",
            },
            "row": rows[:preview_count],
        }
    }
    st.json(preview_json, expanded=2)

    # 전체 JSON은 화면이 지나치게 길어지는 것을 막기 위해 파일로 내려받게 합니다.
    json_bytes = json.dumps(
        full_json,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    st.download_button(
        label="전체 JSON 파일 다운로드",
        data=json_bytes,
        file_name="songpa_rent_2026.json",
        mime="application/json",
    )
