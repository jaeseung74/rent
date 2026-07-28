# rent

스트림릿 앱 하나(main.py)를 만들어줘. 2026년 지치구별 평균전월세를 보여주는 앱을 만들거야.
스트림릿 클라우드에 올릴 거야. 아래에 공식 API 문서에서 복사한 내용을 붙였어.

- 인증키는 비밀 금고(secrets)의 SEOUL_KEY에서 불러와. 코드에는 절대 쓰지 마.
접수연도는 2026년인 데이터만 불러와줘
전월세구분에서 전세만 추출해서,  자치구별 월세 평균을 계산해줘
자치구별 평균전세가를 막대그래프로 그려줘. 평균전세가로 정렬하고, 상위 5개 구는 빨간색으로, 하위 5개는 파란색, 나머지는 검정색으로 해줘. 평균 전세가가 가장 높은 자치구는 지표 카드로 크게.
- 필요한 라이브러리 목록(requirements.txt)도 같이 줘. 버전 숫자 없이 이름만 줘.
- 초보자용 한국어 주석을 달고 main.py 전체 코드를 한 번에 줘.
 

──── 아래는 서울열린데이터 광장 공식 문서에서 복사한 부분 ────

샘플 URL
샘플 URL	서울시 부동산 전월세가 정보
http://openapi.seoul.go.kr:8088/(인증키)/xml/tbLnOpendataRentV/1/5/
예제	
<?xml version="1.0" encoding="UTF-8"?>
<tbLnOpendataRentV>
<list_total_count>2545185</list_total_count>
<RESULT>
<CODE>INFO-000</CODE>
<MESSAGE>정상 처리되었습니다</MESSAGE>
</RESULT>
<row>
<RCPT_YR>2026</RCPT_YR>
<CGG_CD>11710</CGG_CD>
<CGG_NM>송파구</CGG_NM>
<STDG_CD>10400</STDG_CD>
<STDG_NM>송파동</STDG_NM>
<LOTNO_SE>1</LOTNO_SE>
<LOTNO_SE_NM>대지</LOTNO_SE_NM>
<MNO>0117</MNO>
<SNO>0014</SNO>
<FLR>-1</FLR>
<CTRT_DAY>20260727</CTRT_DAY>
<RENT_SE>월세</RENT_SE>
<RENT_AREA>43.32</RENT_AREA>
<GRFE>2000</GRFE>
<RTFE>33</RTFE>
<BLDG_NM>(117-14)</BLDG_NM>
<ARCH_YR>1988</ARCH_YR>
<BLDG_USG>연립다세대</BLDG_USG>
<CTRT_PRD>26.08~27.08</CTRT_PRD>
<NEW_UPDT_YN>신규</NEW_UPDT_YN>
<CTRT_UPDT_USE_YN/>
<BFR_GRFE/>
<BFR_RTFE/>
</row>
<row>
<RCPT_YR>2026</RCPT_YR>
<CGG_CD>11710</CGG_CD>
<CGG_NM>송파구</CGG_NM>
<STDG_CD>11400</STDG_CD>
<STDG_NM>마천동</STDG_NM>
<LOTNO_SE/>
<LOTNO_SE_NM/>
<MNO>0125</MNO>
<SNO>0023</SNO>
<FLR/>
<CTRT_DAY>20260727</CTRT_DAY>
<RENT_SE>월세</RENT_SE>
<RENT_AREA>54</RENT_AREA>
<GRFE>5500</GRFE>
<RTFE>45</RTFE>
<BLDG_NM>(125-23)</BLDG_NM>
<ARCH_YR/>
<BLDG_USG>단독다가구</BLDG_USG>
<CTRT_PRD>26.09~28.09</CTRT_PRD>
<NEW_UPDT_YN>신규</NEW_UPDT_YN>
<CTRT_UPDT_USE_YN/>
<BFR_GRFE/>
<BFR_RTFE/>
</row>
<row>
<RCPT_YR>2026</RCPT_YR>
<CGG_CD>11230</CGG_CD>
<CGG_NM>동대문구</CGG_NM>
<STDG_CD>10400</STDG_CD>
<STDG_NM>전농동</STDG_NM>
<LOTNO_SE>1</LOTNO_SE>
<LOTNO_SE_NM>대지</LOTNO_SE_NM>
<MNO>0130</MNO>
<SNO>0128</SNO>
<FLR>3</FLR>
<CTRT_DAY>20260727</CTRT_DAY>
<RENT_SE>월세</RENT_SE>
<RENT_AREA>28.63</RENT_AREA>
<GRFE>5000</GRFE>
<RTFE>20</RTFE>
<BLDG_NM>(130-128)</BLDG_NM>
<ARCH_YR>2015</ARCH_YR>
<BLDG_USG>연립다세대</BLDG_USG>
<CTRT_PRD>26.08~28.08</CTRT_PRD>
<NEW_UPDT_YN>신규</NEW_UPDT_YN>
<CTRT_UPDT_USE_YN/>
<BFR_GRFE/>
<BFR_RTFE/>
</row>
<row>
<RCPT_YR>2026</RCPT_YR>
<CGG_CD>11710</CGG_CD>
<CGG_NM>송파구</CGG_NM>
<STDG_CD>11100</STDG_CD>
<STDG_NM>방이동</STDG_NM>
<LOTNO_SE>1</LOTNO_SE>
<LOTNO_SE_NM>대지</LOTNO_SE_NM>
<MNO>0154</MNO>
<SNO>0013</SNO>
<FLR>5</FLR>
<CTRT_DAY>20260727</CTRT_DAY>
<RENT_SE>월세</RENT_SE>
<RENT_AREA>21.66</RENT_AREA>
<GRFE>500</GRFE>
<RTFE>56</RTFE>
<BLDG_NM>(154-13)</BLDG_NM>
<ARCH_YR>2002</ARCH_YR>
<BLDG_USG>연립다세대</BLDG_USG>
<CTRT_PRD>26.07~28.07</CTRT_PRD>
<NEW_UPDT_YN>신규</NEW_UPDT_YN>
<CTRT_UPDT_USE_YN/>
<BFR_GRFE/>
<BFR_RTFE/>
</row>
<row>
<RCPT_YR>2026</RCPT_YR>
<CGG_CD>11215</CGG_CD>
<CGG_NM>광진구</CGG_NM>
<STDG_CD>10700</STDG_CD>
<STDG_NM>화양동</STDG_NM>
<LOTNO_SE>1</LOTNO_SE>
<LOTNO_SE_NM>대지</LOTNO_SE_NM>
<MNO>0024</MNO>
<SNO>0006</SNO>
<FLR>3</FLR>
<CTRT_DAY>20260727</CTRT_DAY>
<RENT_SE>전세</RENT_SE>
<RENT_AREA>14.7</RENT_AREA>
<GRFE>9450</GRFE>
<RTFE>0</RTFE>
<BLDG_NM>(24-6)</BLDG_NM>
<ARCH_YR>2013</ARCH_YR>
<BLDG_USG>연립다세대</BLDG_USG>
<CTRT_PRD>26.08~28.08</CTRT_PRD>
<NEW_UPDT_YN>신규</NEW_UPDT_YN>
<CTRT_UPDT_USE_YN/>
<BFR_GRFE/>
<BFR_RTFE/>
</row>
</tbLnOpendataRentV>


요청인자
변수명	타입	변수설명	값설명
KEY	String(필수)	인증키	OpenAPI 에서 발급된 인증키
TYPE	String(필수)	요청파일타입	xml : xml, xml파일 : xmlf, 엑셀파일 : xls, json파일 : json
SERVICE	String(필수)	서비스명	tbLnOpendataRentV
START_INDEX	INTEGER(필수)	요청시작위치	정수 입력 (페이징 시작번호 입니다 : 데이터 행 시작번호)
END_INDEX	INTEGER(필수)	요청종료위치	정수 입력 (페이징 끝번호 입니다 : 데이터 행 끝번호)
RCPT_YR	STRING(선택)	접수연도	YYYY
CGG_CD	STRING(선택)	자치구코드	5자리 정수
CGG_NM	STRING(선택)	자치구명	문자열
STDG_CD	STRING(선택)	법정동코드	5자리 정수
LOTNO_SE	STRING(선택)	지번구분	1:대지,2:산,3:블럭
MNO	STRING(선택)	본번	4자리 정수
SNO	STRING(선택)	부번	4자리 정수
CTRT_DAY	STRING(선택)	계약일	YYYYMMDD
BLDG_NM	STRING(선택)	건물명	문자열
BLDG_USG	STRING(선택)	건물용도	아파트/단독다가구/연립다세대/오피스텔 택1
출력값
No	출력명	출력설명
공통	list_total_count	총 데이터 건수 (정상조회 시 출력됨)
공통	RESULT.CODE	요청결과 코드 (하단 메세지설명 참고)
공통	RESULT.MESSAGE	요청결과 메시지 (하단 메세지설명 참고)
1	RCPT_YR	접수연도
2	CGG_CD	자치구코드
3	CGG_NM	자치구명
4	STDG_CD	법정동코드
5	STDG_NM	법정동명
6	LOTNO_SE	지번구분
7	LOTNO_SE_NM	지번구분명
8	MNO	본번
9	SNO	부번
10	FLR	층
11	CTRT_DAY	계약일
12	RENT_SE	전월세 구분
13	RENT_AREA	임대면적(㎡)
14	GRFE	보증금(만원)
15	RTFE	임대료(만원)
16	BLDG_NM	건물명
17	ARCH_YR	건축년도
18	BLDG_USG	건물용도
19	CTRT_PRD	계약기간
20	NEW_UPDT_YN	신규갱신여부
21	CTRT_UPDT_USE_YN	계약갱신권사용여부
22	BFR_GRFE	종전 보증금
23	BFR_RTFE	종전 임대료
샘플 테스트
접수연도	
자치구코드	
자치구명	
법정동코드	
지번구분	
본번	
부번	
계약일	
건물명	
건물용도	
결과확인
요청주소	
메시지 설명
INFO-000	정상 처리되었습니다
ERROR-300	필수 값이 누락되어 있습니다.
요청인자를 참고 하십시오.
INFO-100	인증키가 유효하지 않습니다.
인증키가 없는 경우, 열린 데이터 광장 홈페이지에서 인증키를 신청하십시오.
ERROR-301	파일타입 값이 누락 혹은 유효하지 않습니다.
요청인자 중 TYPE을 확인하십시오.
ERROR-310	해당하는 서비스를 찾을 수 없습니다.
요청인자 중 SERVICE를 확인하십시오.
ERROR-331	요청시작위치 값을 확인하십시오.
요청인자 중 START_INDEX를 확인하십시오.
ERROR-332	요청종료위치 값을 확인하십시오.
요청인자 중 END_INDEX를 확인하십시오.
ERROR-333	요청위치 값의 타입이 유효하지 않습니다.
요청위치 값은 정수를 입력하세요.
ERROR-334	요청종료위치 보다 요청시작위치가 더 큽니다.
요청시작조회건수는 정수를 입력하세요.
ERROR-335	샘플데이터(샘플키:sample) 는 한번에 최대 5건을 넘을 수 없습니다.
요청시작위치와 요청종료위치 값은 1 ~ 5 사이만 가능합니다.
ERROR-336	데이터요청은 한번에 최대 1000건을 넘을 수 없습니다.
요청종료위치에서 요청시작위치를 뺀 값이 1000을 넘지 않도록 수정하세요.
ERROR-500	서버 오류입니다.
지속적으로 발생시 열린 데이터 광장으로 문의(Q&A) 바랍니다.
ERROR-600	데이터베이스 연결 오류입니다.
지속적으로 발생시 열린 데이터 광장으로 문의(Q&A) 바랍니다.
ERROR-601	SQL 문장 오류 입니다.
지속적으로 발생시 열린 데이터 광장으로 문의(Q&A) 바랍니다.
INFO-200	해당하는 데이터가 없습니다.
