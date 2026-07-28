import requests
import streamlit as st


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="2026년 송파구 전월세 데이터",
    page_icon="🏠",
    layout="wide",
)

SERVICE_NAME = "tbLnOpendataRentV"
RECEIPT_YEAR = "2026"
SONGPA_CODE = "11710"


# --------------------------------------------------
# 서울열린데이터광장 API 호출 함수
# 같은 요청을 반복하지 않도록 10분 동안 결과를 저장합니다.
# --------------------------------------------------
@st.cache_data(ttl=600)
def load_rent_data(api_key):
    # 서울열린데이터광장은 한 번에 최대 1,000건까지 요청할 수 있습니다.
    start_index = 1
    end_index = 1000

    # URL 마지막에 접수연도와 자치구 코드를 넣습니다.
    url = (
        f"http://openapi.seoul.go.kr:8088/"
        f"{api_key}/json/{SERVICE_NAME}/"
        f"{start_index}/{end_index}/"
        f"{RECEIPT_YEAR}/{SONGPA_CODE}/"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException:
        return None, "서울열린데이터광장에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요."

    except ValueError:
        return None, "서버 응답을 JSON 형식으로 읽지 못했습니다."

    # API 서버에서 faultInfo 오류를 보낸 경우 처리합니다.
    if "faultInfo" in data:
        fault_info = data["faultInfo"]

        if isinstance(fault_info, dict):
            message = fault_info.get("message", "API 요청 중 오류가 발생했습니다.")
        else:
            message = "API 요청 중 오류가 발생했습니다."

        return None, f"서울열린데이터광장 오류: {message}"

    # 정상 응답 안에서 서비스 데이터를 꺼냅니다.
    service_data = data.get(SERVICE_NAME)

    if not isinstance(service_data, dict):
        result = data.get("RESULT", {})
        message = result.get("MESSAGE", "API 응답 형식을 확인할 수 없습니다.")
        return None, message

    # API 처리 결과 코드를 확인합니다.
    result = service_data.get("RESULT", {})
    result_code = result.get("CODE")
    result_message = result.get("MESSAGE", "")

    if result_code != "INFO-000":
        return None, f"{result_message} ({result_code})"

    # 응답 데이터 중 2026년 송파구 자료만 다시 확인하여 추출합니다.
    rows = service_data.get("row", [])

    songpa_rows = [
        row
        for row in rows
        if str(row.get("RCPT_YR", "")) == RECEIPT_YEAR
        and str(row.get("CGG_CD", "")) == SONGPA_CODE
    ]

    # 화면에 보여줄 JSON 구조를 만듭니다.
    filtered_data = {
        SERVICE_NAME: {
            "list_total_count": service_data.get("list_total_count", 0),
            "RESULT": result,
            "row": songpa_rows,
        }
    }

    return filtered_data, None


# --------------------------------------------------
# 화면 구성
# --------------------------------------------------
st.title("🏠 2026년 송파구 전월세 JSON 데이터")

st.write(
    "서울열린데이터광장에서 접수연도 **2026년**, "
    "자치구 **송파구**의 전월세 데이터를 불러옵니다."
)

# Streamlit 비밀 금고에 인증키가 있는지 확인합니다.
if "SEOUL_KEY" not in st.secrets:
    st.error(
        "비밀 금고에 SEOUL_KEY가 설정되어 있지 않습니다. "
        "Streamlit Cloud의 Secrets 설정을 확인해 주세요."
    )
    st.stop()

# 코드에 인증키를 직접 작성하지 않고 비밀 금고에서 가져옵니다.
seoul_key = st.secrets["SEOUL_KEY"]

data, error_message = load_rent_data(seoul_key)

if error_message:
    st.error(error_message)
    st.stop()

service_data = data[SERVICE_NAME]
rows = service_data.get("row", [])

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "전체 조건 검색 건수",
        f"{service_data.get('list_total_count', 0):,}건",
    )

with col2:
    st.metric(
        "현재 불러온 건수",
        f"{len(rows):,}건",
    )

if not rows:
    st.info("조건에 해당하는 전월세 데이터가 없습니다.")
else:
    st.subheader("JSON 데이터")
    st.json(data)
