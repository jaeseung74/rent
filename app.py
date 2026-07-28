import requests
import streamlit as st


st.set_page_config(
    page_title="2026년 송파구 전월세 데이터",
    page_icon="🏠",
)

st.title("🏠 2026년 송파구 전월세 첫 번째 데이터")


@st.cache_data(ttl=600)
def load_first_data(api_key):
    # 요청 범위를 1~1로 설정하여 첫 번째 데이터 1건만 불러옵니다.
    # 2026: 접수연도, 11710: 송파구 자치구 코드
    url = (
        f"http://openapi.seoul.go.kr:8088/"
        f"{api_key}/json/tbLnOpendataRentV/"
        f"1/1/2026/11710/"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException:
        return None, "서울열린데이터광장에 연결하지 못했습니다."

    except ValueError:
        return None, "API 응답을 JSON 형식으로 읽지 못했습니다."

    # 인증키 오류 등으로 faultInfo가 반환된 경우입니다.
    if "faultInfo" in data:
        fault = data["faultInfo"]

        if isinstance(fault, dict):
            message = fault.get("message", "API 요청 중 오류가 발생했습니다.")
        else:
            message = "API 요청 중 오류가 발생했습니다."

        return None, message

    service_data = data.get("tbLnOpendataRentV")

    if not isinstance(service_data, dict):
        return None, "API 응답에서 전월세 데이터를 찾지 못했습니다."

    result = service_data.get("RESULT", {})
    result_code = result.get("CODE")
    result_message = result.get("MESSAGE", "")

    if result_code != "INFO-000":
        return None, f"{result_message} ({result_code})"

    rows = service_data.get("row", [])

    if not rows:
        return None, "2026년 송파구 전월세 데이터가 없습니다."

    # 첫 번째 행이 실제로 2026년 송파구 데이터인지 다시 확인합니다.
    first_row = rows[0]

    if (
        str(first_row.get("RCPT_YR", "")) != "2026"
        or str(first_row.get("CGG_CD", "")) != "11710"
    ):
        return None, "조건에 맞는 데이터를 불러오지 못했습니다."

    return first_row, None


# 인증키는 Streamlit 비밀 금고에서 불러옵니다.
if "SEOUL_KEY" not in st.secrets:
    st.error("Streamlit Secrets에 SEOUL_KEY를 등록해 주세요.")
    st.stop()

first_data, error_message = load_first_data(st.secrets["SEOUL_KEY"])

if error_message:
    st.error(error_message)
else:
    st.subheader("첫 번째 행 JSON 데이터")
    st.json(first_data)
