from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

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
# 2. API 기본 설정
# ---------------------------------------------------------
BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE_NAME = "tbLnOpendataRentV"
RECEIPT_YEAR = "2026"

# 서울열린데이터광장은 한 번에 최대 1,000건까지 요청할 수 있습니다.
PAGE_SIZE = 1000

# 동시에 요청할 페이지 수입니다.
# 너무 크게 설정하면 API 서버에 부담을 줄 수 있으므로 6개로 제한합니다.
MAX_WORKERS = 6


# ---------------------------------------------------------
# 3. API 오류 메시지 확인
# ---------------------------------------------------------
def get_fault_message(data):
    """faultInfo 응답에서 오류 메시지를 꺼냅니다."""

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
# 4. API의 특정 범위를 요청하는 함수
# ---------------------------------------------------------
def request_page(api_key, start_index, end_index):
    """API에서 지정된 범위의 데이터를 가져옵니다."""

    url = (
        f"{BASE_URL}/{api_key}/json/{SERVICE_NAME}/"
        f"{start_index}/{end_index}/{RECEIPT_YEAR}/"
    )

    response = requests.get(
        url,
        timeout=(5, 20),
    )

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as error:
        raise RuntimeError(
            "서버 응답을 JSON 형식으로 읽지 못했습니다."
        ) from error

    # 인증키 오류 등이 있을 때 반환되는 값입니다.
    if "faultInfo" in data:
        raise RuntimeError(get_fault_message(data))

    service_data = data.get(SERVICE_NAME)

    if not isinstance(service_data, dict):
        result = data.get("RESULT", {})
        code = result.get("CODE", "")
        message = result.get(
            "MESSAGE",
            "API 응답에서 전월세 데이터를 찾지 못했습니다.",
        )

        raise RuntimeError(f"{message} ({code})")

    result = service_data.get("RESULT", {})
    result_code = result.get("CODE", "")
    result_message = result.get("MESSAGE", "")

    if result_code == "INFO-200":
        return [], 0

    if result_code != "INFO-000":
        raise RuntimeError(
            f"{result_message} ({result_code})"
        )

    rows = service_data.get("row", [])

    # 데이터가 한 건일 때에도 리스트로 맞춥니다.
    if isinstance(rows, dict):
        rows = [rows]

    try:
        total_count = int(
            service_data.get("list_total_count", 0)
        )
    except (TypeError, ValueError):
        total_count = 0

    return rows, total_count


# ---------------------------------------------------------
# 5. 전세 데이터만 집계하는 함수
# ---------------------------------------------------------
def add_jeonse_rows(rows, deposit_sums, deal_counts):
    """
    한 페이지의 데이터에서 전세 거래만 추출하여
    자치구별 보증금 합계와 거래 건수를 계산합니다.
    """

    for row in rows:
        receipt_year = str(
            row.get("RCPT_YR", "")
        ).strip()

        rent_type = str(
            row.get("RENT_SE", "")
        ).strip()

        borough = str(
            row.get("CGG_NM", "")
        ).strip()

        # 2026년 전세 거래만 사용합니다.
        if receipt_year != RECEIPT_YEAR:
            continue

        if rent_type != "전세":
            continue

        if not borough:
            continue

        # 보증금 값을 숫자로 변환합니다.
        deposit_text = (
            str(row.get("GRFE", ""))
            .replace(",", "")
            .strip()
        )

        try:
            deposit = float(deposit_text)
        except (TypeError, ValueError):
            continue

        # 잘못된 음수 보증금은 제외합니다.
        if deposit < 0:
            continue

        deposit_sums[borough] += deposit
        deal_counts[borough] += 1


# ---------------------------------------------------------
# 6. 첫 번째 전세 거래를 찾는 함수
# ---------------------------------------------------------
def find_first_jeonse(rows):
    """한 페이지에서 첫 번째 2026년 전세 거래를 찾습니다."""

    for row in rows:
        if (
            str(row.get("RCPT_YR", "")).strip()
            == RECEIPT_YEAR
            and str(row.get("RENT_SE", "")).strip()
            == "전세"
        ):
            return row.copy()

    return None


# ---------------------------------------------------------
# 7. 전체 데이터 병렬 요청 및 집계
# ---------------------------------------------------------
@st.cache_data(
    ttl=21600,  # 6시간
    show_spinner=False,
)
def load_jeonse_summary(api_key):
    """
    첫 페이지를 요청하여 전체 건수를 확인한 뒤,
    나머지 페이지를 여러 개씩 동시에 불러옵니다.

    원본 전체 데이터를 저장하지 않고
    자치구별 집계 결과만 반환합니다.
    """

    # 자치구별 보증금 합계
    deposit_sums = defaultdict(float)

    # 자치구별 전세 거래 건수
    deal_counts = defaultdict(int)

    first_jeonse = None

    # 첫 페이지는 전체 데이터 건수를 확인하기 위해 먼저 요청합니다.
    first_rows, total_count = request_page(
        api_key,
        1,
        PAGE_SIZE,
    )

    add_jeonse_rows(
        first_rows,
        deposit_sums,
        deal_counts,
    )

    first_jeonse = find_first_jeonse(first_rows)

    # 두 번째 페이지부터 요청 범위를 만듭니다.
    page_ranges = []

    for start_index in range(
        PAGE_SIZE + 1,
        total_count + 1,
        PAGE_SIZE,
    ):
        end_index = min(
            start_index + PAGE_SIZE - 1,
            total_count,
        )

        page_ranges.append(
            (start_index, end_index)
        )

    # 요청할 페이지가 있으면 동시에 불러옵니다.
    if page_ranges:

        def fetch_range(index_range):
            start_index, end_index = index_range

            return request_page(
                api_key,
                start_index,
                end_index,
            )

        worker_count = min(
            MAX_WORKERS,
            len(page_ranges),
        )

        with ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:

            # executor.map은 여러 요청을 동시에 실행하면서
            # 결과는 원래 페이지 순서대로 전달합니다.
            page_results = executor.map(
                fetch_range,
                page_ranges,
            )

            for rows, _ in page_results:
                if first_jeonse is None:
                    first_jeonse = find_first_jeonse(rows)

                add_jeonse_rows(
                    rows,
                    deposit_sums,
                    deal_counts,
                )

    # 자치구별 평균 전세가 데이터프레임을 만듭니다.
    summary_rows = []

    for borough in deposit_sums:
        count = deal_counts[borough]

        if count == 0:
            continue

        average_deposit = (
            deposit_sums[borough] / count
        )

        summary_rows.append(
            {
                "CGG_NM": borough,
                "평균전세가_만원": round(
                    average_deposit,
                    1,
                ),
                "전세거래건수": count,
            }
        )

    borough_average = pd.DataFrame(summary_rows)

    if not borough_average.empty:
        borough_average = (
            borough_average
            .sort_values(
                "평균전세가_만원",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    total_jeonse_count = sum(
        deal_counts.values()
    )

    return (
        borough_average,
        first_jeonse,
        total_count,
        total_jeonse_count,
    )


# ---------------------------------------------------------
# 8. 비밀 금고에서 인증키 불러오기
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
# 9. 사용자가 원할 때만 캐시 삭제
# ---------------------------------------------------------
if st.button("🔄 최신 데이터 다시 불러오기"):
    load_jeonse_summary.clear()
    st.rerun()


# ---------------------------------------------------------
# 10. 데이터 불러오기
# ---------------------------------------------------------
try:
    with st.spinner(
        "2026년 전세 데이터를 불러오고 있습니다..."
    ):
        (
            borough_average,
            first_jeonse,
            total_count,
            total_jeonse_count,
        ) = load_jeonse_summary(seoul_key)

except requests.Timeout:
    st.error(
        "API 서버의 응답 시간이 너무 오래 걸립니다. "
        "잠시 후 다시 시도해 주세요."
    )
    st.stop()

except requests.RequestException:
    st.error(
        "서울열린데이터광장에 연결하지 못했습니다. "
        "잠시 후 다시 시도해 주세요."
    )
    st.stop()

except RuntimeError as error:
    st.error(str(error))
    st.stop()

except Exception as error:
    st.error(
        "데이터를 처리하는 중 오류가 발생했습니다."
    )

    # Streamlit Cloud 로그에서 실제 오류를 확인할 수 있습니다.
    st.exception(error)
    st.stop()


if borough_average.empty:
    st.info(
        "2026년 데이터에서 전세 거래를 찾지 못했습니다."
    )
    st.stop()


# ---------------------------------------------------------
# 11. 평균 전세가가 가장 높은 자치구 표시
# ---------------------------------------------------------
highest_borough = borough_average.iloc[0]

st.metric(
    label="평균 전세가가 가장 높은 자치구",
    value=(
        f"{highest_borough['CGG_NM']} "
        f"{highest_borough['평균전세가_만원']:,.0f}만 원"
    ),
)

col1, col2 = st.columns(2)

col1.metric(
    "2026년 전체 조회 건수",
    f"{total_count:,}건",
)

col2.metric(
    "분석에 사용된 전세 거래",
    f"{total_jeonse_count:,}건",
)

st.caption(
    "전세가는 전세 보증금의 평균이며 단위는 만 원입니다. "
    "조회 결과는 6시간 동안 캐시에 저장됩니다."
)


# ---------------------------------------------------------
# 12. 막대 색상 지정
# ---------------------------------------------------------
bar_colors = []
borough_count = len(borough_average)

for index in range(borough_count):

    # 평균 전세가 상위 5개 자치구
    if index < 5:
        bar_colors.append("red")

    # 평균 전세가 하위 5개 자치구
    elif index >= borough_count - 5:
        bar_colors.append("blue")

    # 나머지 자치구
    else:
        bar_colors.append("black")


# ---------------------------------------------------------
# 13. 자치구별 평균 전세가 막대그래프
# ---------------------------------------------------------
figure = go.Figure(
    data=[
        go.Bar(
            x=borough_average["CGG_NM"],
            y=borough_average["평균전세가_만원"],
            marker_color=bar_colors,
            customdata=borough_average[
                ["전세거래건수"]
            ],
            text=[
                f"{value:,.0f}"
                for value in borough_average[
                    "평균전세가_만원"
                ]
            ],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "평균 전세가: %{y:,.0f}만 원<br>"
                "전세 거래 건수: "
                "%{customdata[0]:,.0f}건"
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
    margin=dict(
        l=30,
        r=30,
        t=80,
        b=100,
    ),
)

figure.update_xaxes(
    tickangle=-45
)

figure.update_yaxes(
    tickformat=","
)

st.plotly_chart(
    figure,
    width="stretch",
    config={
        "displayModeBar": False
    },
)

st.caption(
    "🔴 평균 전세가 상위 5개 구 · "
    "🔵 평균 전세가 하위 5개 구 · "
    "⚫ 나머지 자치구"
)


# ---------------------------------------------------------
# 14. 계산 결과 표
# ---------------------------------------------------------
with st.expander(
    "자치구별 평균 전세가 표 보기"
):
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


# ---------------------------------------------------------
# 15. 첫 번째 전세 JSON 데이터
# ---------------------------------------------------------
with st.expander(
    "전세 JSON 데이터 첫 번째 행 보기"
):
    if first_jeonse:
        st.json(first_jeonse)
    else:
        st.info(
            "표시할 전세 JSON 데이터가 없습니다."
        )
