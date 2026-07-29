import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


# ---------------------------------------------------------
# 1. 앱 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="2026년 서울시 평균 전세가",
    page_icon="🏠",
    layout="wide",
)

st.title("🏠 2026년 서울시 자치구별 평균 전세가")
st.write(
    "서울시 전월세 데이터를 불러온 뒤 **전세 거래만 추출**하여 "
    "자치구별 평균 전세 보증금을 계산합니다."
)


# ---------------------------------------------------------
# 2. API 기본 정보
# ---------------------------------------------------------
BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE_NAME = "tbLnOpendataRentV"
RECEIPT_YEAR = "2026"

# 서울열린데이터광장은 한 번에 최대 1,000건까지 요청할 수 있습니다.
PAGE_SIZE = 1000


# ---------------------------------------------------------
# 3. API 오류 메시지를 읽는 함수
# ---------------------------------------------------------
def get_fault_message(data):
    """faultInfo 응답에서 오류 메시지를 찾아 반환합니다."""

    fault_info = data.get("faultInfo", {})

    if isinstance(fault_info, dict):
        return (
            fault_info.get("message")
            or fault_info.get("errorMessage")
            or fault_info.get("MESSAGE")
            or "API 요청 중 오류가 발생했습니다."
        )

    return "API 요청 중 오류가 발생했습니다."


# ---------------------------------------------------------
# 4. 2026년 전체 전월세 데이터를 불러오는 함수
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_rent_data(api_key):
    """
    2026년 데이터를 1,000건씩 나누어 모두 불러옵니다.

    캐시 유효시간은 3,600초(1시간)입니다.
    """

    all_rows = []
    start_index = 1
    total_count = None

    # 여러 번 API를 호출할 때 연결을 재사용합니다.
    session = requests.Session()

    while total_count is None or start_index <= total_count:
        end_index = start_index + PAGE_SIZE - 1

        # URL 마지막의 2026은 접수연도 조건입니다.
        url = (
            f"{BASE_URL}/{api_key}/json/{SERVICE_NAME}/"
            f"{start_index}/{end_index}/{RECEIPT_YEAR}/"
        )

        response = session.get(url, timeout=30)
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError as error:
            raise RuntimeError(
                "서버 응답을 JSON 형식으로 읽지 못했습니다."
            ) from error

        # 인증키 오류 등으로 faultInfo가 반환된 경우입니다.
        if "faultInfo" in data:
            raise RuntimeError(get_fault_message(data))

        service_data = data.get(SERVICE_NAME)

        # 서비스 데이터가 없으면 일반 오류 응답을 확인합니다.
        if not isinstance(service_data, dict):
            result = data.get("RESULT", {})
            code = result.get("CODE", "")
            message = result.get(
                "MESSAGE",
                "API 응답에서 전월세 데이터를 찾지 못했습니다.",
            )

            if code == "INFO-200":
                break

            raise RuntimeError(f"{message} ({code})")

        # API 처리 결과를 확인합니다.
        result = service_data.get("RESULT", {})
        result_code = result.get("CODE", "")
        result_message = result.get("MESSAGE", "")

        if result_code == "INFO-200":
            break

        if result_code != "INFO-000":
            raise RuntimeError(f"{result_message} ({result_code})")

        rows = service_data.get("row", [])

        # 데이터가 한 건일 때에도 리스트 형태로 맞춥니다.
        if isinstance(rows, dict):
            rows = [rows]

        all_rows.extend(rows)

        try:
            total_count = int(service_data.get("list_total_count", 0))
        except (TypeError, ValueError):
            total_count = len(all_rows)

        # 마지막 페이지까지 불러왔으면 반복을 끝냅니다.
        if not rows or end_index >= total_count:
            break

        start_index = end_index + 1

    return all_rows


# ---------------------------------------------------------
# 5. Streamlit 비밀 금고에서 인증키 불러오기
# ---------------------------------------------------------
try:
    seoul_key = st.secrets["SEOUL_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "Streamlit 비밀 금고에 SEOUL_KEY가 없습니다. "
        "앱 설정의 Secrets에 인증키를 등록해 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 6. API 데이터 불러오기
# ---------------------------------------------------------
try:
    with st.spinner("2026년 전월세 데이터를 불러오고 있습니다..."):
        rows = load_rent_data(seoul_key)

except requests.Timeout:
    st.error("API 서버의 응답 시간이 너무 오래 걸립니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

except requests.RequestException:
    st.error("서울열린데이터광장에 연결하지 못했습니다. 인터넷 연결을 확인해 주세요.")
    st.stop()

except RuntimeError as error:
    st.error(str(error))
    st.stop()

except Exception:
    st.error("데이터를 처리하는 중 예상하지 못한 오류가 발생했습니다.")
    st.stop()


if not rows:
    st.info("2026년에 해당하는 전월세 데이터가 없습니다.")
    st.stop()


# ---------------------------------------------------------
# 7. JSON 데이터를 표 형태로 변환
# ---------------------------------------------------------
rent_df = pd.DataFrame(rows)

required_columns = {"RCPT_YR", "CGG_NM", "RENT_SE", "GRFE"}

if not required_columns.issubset(rent_df.columns):
    st.error("API 응답에 분석에 필요한 항목이 없습니다.")
    st.stop()


# 접수연도가 2026년인 데이터만 다시 확인합니다.
rent_df = rent_df[
    rent_df["RCPT_YR"].astype(str).str.strip() == RECEIPT_YEAR
].copy()

# 전월세 구분에서 '전세'만 추출합니다.
jeonse_df = rent_df[
    rent_df["RENT_SE"].astype(str).str.strip() == "전세"
].copy()

# 보증금에 쉼표가 들어 있을 경우 제거한 후 숫자로 변환합니다.
jeonse_df["GRFE"] = pd.to_numeric(
    jeonse_df["GRFE"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.strip(),
    errors="coerce",
)

# 자치구명이나 보증금이 없는 행은 평균 계산에서 제외합니다.
jeonse_df = jeonse_df.dropna(subset=["CGG_NM", "GRFE"])

# 잘못된 음수 값이 있을 경우 제외합니다.
jeonse_df = jeonse_df[jeonse_df["GRFE"] >= 0]

if jeonse_df.empty:
    st.info("2026년 데이터에서 전세 거래를 찾지 못했습니다.")
    st.stop()


# ---------------------------------------------------------
# 8. 자치구별 평균 전세가 계산
# ---------------------------------------------------------
borough_average = (
    jeonse_df.groupby("CGG_NM", as_index=False)
    .agg(
        평균전세가_만원=("GRFE", "mean"),
        전세거래건수=("GRFE", "size"),
    )
    # 평균 전세가가 높은 자치구부터 정렬합니다.
    .sort_values("평균전세가_만원", ascending=False)
    .reset_index(drop=True)
)

borough_average["평균전세가_만원"] = (
    borough_average["평균전세가_만원"].round(1)
)


# ---------------------------------------------------------
# 9. 평균 전세가가 가장 높은 자치구 표시
# ---------------------------------------------------------
highest_borough = borough_average.iloc[0]

st.metric(
    label="평균 전세가가 가장 높은 자치구",
    value=(
        f"{highest_borough['CGG_NM']} "
        f"{highest_borough['평균전세가_만원']:,.0f}만 원"
    ),
)

st.caption(
    f"2026년 전세 거래 {len(jeonse_df):,}건을 기준으로 계산했습니다. "
    "전세가는 전세 보증금의 평균이며 단위는 만 원입니다."
)


# ---------------------------------------------------------
# 10. 막대 색상 지정
# ---------------------------------------------------------
# 평균 전세가 상위 5개 구: 빨간색
# 평균 전세가 하위 5개 구: 파란색
# 나머지 자치구: 검정색
bar_colors = []
borough_count = len(borough_average)

for index in range(borough_count):
    if index < 5:
        bar_colors.append("red")
    elif index >= borough_count - 5:
        bar_colors.append("blue")
    else:
        bar_colors.append("black")


# ---------------------------------------------------------
# 11. 자치구별 평균 전세가 막대그래프
# ---------------------------------------------------------
figure = go.Figure(
    data=[
        go.Bar(
            x=borough_average["CGG_NM"],
            y=borough_average["평균전세가_만원"],
            marker_color=bar_colors,
            customdata=borough_average[["전세거래건수"]],
            text=[
                f"{value:,.0f}"
                for value in borough_average["평균전세가_만원"]
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "평균 전세가: %{y:,.0f}만 원<br>"
                "전세 거래 건수: %{customdata[0]:,}건"
                "<extra></extra>"
            ),
        )
    ]
)

figure.update_layout(
    title="2026년 서울시 자치구별 평균 전세가",
    xaxis_title="자치구",
    yaxis_title="평균 전세가(만 원)",
    height=650,
    showlegend=False,
    margin=dict(l=30, r=30, t=80, b=100),
)

figure.update_xaxes(tickangle=-45)
figure.update_yaxes(tickformat=",")

st.plotly_chart(
    figure,
    width="stretch",
    config={"displayModeBar": False},
)

st.caption(
    "🔴 평균 전세가 상위 5개 구 · "
    "🔵 평균 전세가 하위 5개 구 · "
    "⚫ 나머지 자치구"
)


# ---------------------------------------------------------
# 12. 계산 결과와 JSON 데이터 형태 확인
# ---------------------------------------------------------
with st.expander("자치구별 평균 전세가 표 보기"):
    display_df = borough_average.copy()

    display_df.columns = [
        "자치구",
        "평균 전세가(만 원)",
        "전세 거래 건수",
    ]

    st.dataframe(
        display_df,
        hide_index=True,
        width="stretch",
    )


with st.expander("전세 JSON 데이터 첫 번째 행 보기"):
    # 원본 JSON 데이터 중 첫 번째 전세 거래를 보여줍니다.
    first_jeonse_index = jeonse_df.index[0]
    st.json(rent_df.loc[first_jeonse_index].to_dict())
