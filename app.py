import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / "2.env")

st.set_page_config(page_title="개발 영향도 파악 및 테스트 서비스", page_icon="◆", layout="wide")
st.markdown("""
<style>
  .stApp { background:#f7f8fa; color:#172130; }
  header[data-testid="stHeader"] { background:rgba(247,248,250,.88); }
  .block-container { max-width:1200px; padding-top:2rem; padding-bottom:4rem; }
  .brand { font-size:1.3rem; font-weight:700; letter-spacing:-.5px; margin-bottom:3.5rem; }
  .brand span { color:#2357e8; } .eyebrow { color:#2357e8; font:600 .7rem monospace; letter-spacing:1.4px; }
  .hero h1 { font-size:clamp(2.5rem,6vw,4.4rem); line-height:1.1; letter-spacing:-3px; margin:.6rem 0; }
  .hero em { color:#2357e8; font-style:normal; } .sub { color:#687384; font-size:1.05rem; line-height:1.7; }
  [data-testid="stForm"] { background:white; border:1px solid #dde2e8; border-radius:16px; padding:1.8rem; }
  .section-title { font-size:1.15rem; font-weight:700; letter-spacing:-.5px; margin-bottom:.2rem; }
  .section-sub { color:#687384; font-size:.84rem; margin-bottom:1.2rem; }
  .summary { background:white; border:1px solid #dde2e8; border-left:5px solid #79e0c6; border-radius:14px; padding:1.3rem 1.5rem; font-size:1.05rem; line-height:1.75; margin-bottom:1rem; }
  .card { background:white; border:1px solid #dde2e8; border-radius:14px; padding:1.4rem; min-height:220px; margin-bottom:1rem; }
  .tag { display:inline-block; padding:3px 8px; border-radius:999px; background:#edf1f6; color:#5d6b7c; font-size:.72rem; font-weight:700; margin-right:6px; }
  .impact { border:1px solid #dde2e8; border-radius:10px; padding:.65rem .8rem; margin:.5rem 0; }
  .impact p { color:#687384; font-size:.8rem; margin:.25rem 0 0; }.empty { color:#687384; font-size:.9rem; }
  .notice { background:#fffaf0; border:1px solid #f1dfb5; border-radius:14px; padding:1.3rem; margin-top:.5rem; }
  @media(max-width:700px){.block-container{padding:1.2rem 1rem 3rem}.brand{margin-bottom:2.3rem}.hero h1{letter-spacing:-2px}.stForm{padding:1rem!important}}
</style>
""", unsafe_allow_html=True)


def ensure_list(value):
    return value if isinstance(value, list) else []


def analyze(request_text, change, system, conditions):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("2.env에서 OPENAI_API_KEY를 찾을 수 없습니다.")
    instructions = """당신은 기업 IT 변경관리 분석가입니다. 한국어로 답하세요.
입력에 시스템 연계도, API 목록, 프로그램명, DB 테이블명, 화면명, 배치명이 없다면 절대로 추측하거나 만들어 내지 마세요. 해당 영향 항목과 connections는 빈 배열로 두고 questions에 필요한 정보라고 쓰세요. 실제 테스트를 실행할 수는 없으므로 test_cases.status는 '미실행'으로 표시하세요. test_results는 케이스별 기대 결과를 바탕으로 한 '모의 결과'임을 분명히 하고, 실제 실행 로그처럼 주장하지 마세요. 테스트 케이스와 데이터는 명시된 요청 및 조건만 근거로 작성하고, 불명확한 전제는 questions에 넣으세요.
JSON만 반환하세요: {"summary":"문자열","core_tasks":["문자열"],"data_items":["문자열"],"change_analysis":"문자열","impact_items":[{"name":"문자열","type":"시스템|API|프로그램|DB|화면|배치","level":"높음|중간|낮음","reason":"문자열"}],"connections":[{"from":"문자열","to":"문자열","label":"문자열"}],"test_cases":[{"id":"TC-01","title":"문자열","target":"문자열","condition":"문자열","expected":"문자열","status":"미실행"}],"test_data":[{"case_id":"TC-01","product":"상품명","customer_id":"10자리 숫자 문자열","customer_attributes":["고객 속성"],"purpose":"목적"}],"test_results":[{"case_id":"TC-01","mode":"모의 결과","status":"예상 통과|확인 필요","result":"예상 결과 설명"}],"questions":["문자열"],"limitations":["문자열"]}"""
    prompt = f"다음 정보를 바탕으로 JSON 형식 분석 결과를 반환하세요.\n개발 요청: {request_text}\n변경 내용: {change or '(미입력)'}\n테스트 대상 시스템: {system or '(미입력)'}\n업무 조건: {conditions or '(미입력)'}"
    response = OpenAI(api_key=api_key).responses.create(model="gpt-6-luna", instructions=instructions, input=prompt, text={"format":{"type":"json_object"}})
    result = json.loads(response.output_text)
    for key in ("core_tasks", "data_items", "impact_items", "connections", "test_cases", "test_data", "test_results", "questions", "limitations"):
        result[key] = ensure_list(result.get(key))
    return result


def bullets(values, fallback):
    if values:
        st.markdown("\n".join(f"- {item}" for item in values))
    else:
        st.markdown(f"<p class='empty'>{fallback}</p>", unsafe_allow_html=True)


st.markdown("<div class='brand'><span>◆</span> ChangeScope</div>", unsafe_allow_html=True)
st.markdown("<div class='hero'><p class='eyebrow'>ANALYZE · PLAN · VERIFY</p><h1>개발 영향도 파악 및 테스트 서비스</h1><p class='sub'>개발 요청을 분석해 영향도와 테스트 준비 항목을 한눈에 정리합니다.</p></div>", unsafe_allow_html=True)

demo_report = {
    "summary": "[예시 데이터] 고객 연락처 변경 흐름에서 고객정보 갱신과 알림 발송을 검증하는 테스트 계획입니다. 아래 시스템·API 연결은 화면 확인을 위한 가상 예시입니다.",
    "core_tasks": ["고객 연락처 변경", "변경된 연락처로 알림 발송", "변경 이력 확인"],
    "data_items": ["고객 ID", "변경 전·후 휴대폰 번호", "연락처 변경 일시", "알림 발송 상태"],
    "change_analysis": "고객이 본인 인증을 마친 뒤 휴대폰 번호를 변경하면 고객정보를 갱신하고 새 번호로 변경 안내 알림을 발송하는 시나리오입니다. 실제 연계 구조는 예시에 포함되지 않았습니다.",
    "impact_items": [
        {"name": "고객관리 시스템 (예시)", "type": "시스템", "level": "높음", "reason": "고객 연락처 원장을 갱신하는 변경의 기준 시스템으로 가정한 데모 항목입니다."},
        {"name": "연락처 변경 API (예시)", "type": "API", "level": "높음", "reason": "인증된 변경 요청과 결과 응답을 처리하는 API로 가정했습니다."},
        {"name": "고객정보 테이블 (예시)", "type": "DB", "level": "중간", "reason": "새 연락처와 변경 시각 저장 여부를 검증하는 가상 테이블 항목입니다."},
        {"name": "알림 발송 화면 (예시)", "type": "화면", "level": "중간", "reason": "발송 결과와 실패 상태를 확인하는 화면으로 가정했습니다."}
    ],
    "connections": [
        {"from": "고객관리 화면 (예시)", "to": "연락처 변경 API (예시)", "label": "변경 요청"},
        {"from": "연락처 변경 API (예시)", "to": "고객정보 테이블 (예시)", "label": "정보 저장"},
        {"from": "연락처 변경 API (예시)", "to": "알림 서비스 (예시)", "label": "변경 알림"}
    ],
    "test_cases": [
        {"id": "TC-01", "title": "정상 연락처 변경", "target": "고객관리 시스템 (예시)", "condition": "본인 인증 성공, 유효한 새 번호", "expected": "새 번호와 변경 시각이 저장되고 변경 안내가 발송 대기 상태가 된다.", "status": "미실행 (예시)"},
        {"id": "TC-02", "title": "잘못된 번호 형식", "target": "연락처 변경 API (예시)", "condition": "번호 자릿수가 기준에 맞지 않음", "expected": "변경을 거부하고 기존 연락처가 유지된다.", "status": "미실행 (예시)"},
        {"id": "TC-03", "title": "알림 발송 실패 후 재처리", "target": "알림 서비스 (예시)", "condition": "연락처 저장 성공, 알림 제공자 오류", "expected": "연락처 변경은 유지되고 실패 상태와 재처리 필요 여부가 기록된다.", "status": "미실행 (예시)"}
    ],
    "test_data": [
        {"case_id": "TC-01", "purpose": "정상 변경", "data": "고객 ID: DEMO-1001, 변경 전 번호: 010-0000-1111, 변경 후 번호: 010-0000-2222", "note": "모두 가상 값이며 실제 개인정보를 사용하지 마세요."},
        {"case_id": "TC-02", "purpose": "입력값 검증", "data": "고객 ID: DEMO-1002, 변경 후 번호: 010-12", "note": "형식 검증용 가상 값입니다."},
        {"case_id": "TC-03", "purpose": "알림 실패 처리", "data": "고객 ID: DEMO-1003, 알림 모의 응답: PROVIDER_ERROR", "note": "테스트 환경에서만 사용하는 모의 응답입니다."}
    ],
    "questions": ["실제 고객관리 시스템, API 명세, DB 스키마와 화면 식별자를 확인해야 합니다.", "알림 발송 실패 시 재시도 횟수와 최종 처리 기준을 업무 담당자와 확정해야 합니다."],
    "limitations": ["이 화면의 영향 시스템·연계는 설명용 가상 예시이며 실제 구성에서 확인한 정보가 아닙니다.", "테스트는 실행되지 않았으며 상태값은 데모 표시입니다.", "예시 버튼은 OpenAI API를 호출하지 않습니다."]
}
from demo_data import DEMO_REPORT
demo_report = DEMO_REPORT

with st.expander("예시 데이터로 화면 미리보기", expanded=False):
    st.caption("금융 상품 신청 간소화 사례입니다. 영향 시스템은 실제 내부 구성이 아닌 가상 예시입니다.")
    if st.button("금융 상품 예시 결과 표시", key="load_demo", use_container_width=True):
        st.session_state.report = demo_report
        st.rerun()

with st.form("analysis_form"):
    st.markdown("<div class='section-title'>01 · 개발 요청 입력</div><div class='section-sub'>변경 요청과 테스트 맥락을 입력하세요.</div>", unsafe_allow_html=True)
    request_text = st.text_area("개발 요청 내용 *", value="금융 상품별 신청 프로세스 간소화", height=110)
    change = st.text_area("개발 변경 내용", value="금융 상품별 신청 프로세스", height=85)
    c1, c2 = st.columns(2)
    system = c1.text_input("테스트 대상 시스템", value="현대카드 앱")
    conditions = c2.text_input("업무 조건", value="본인인증 단계 필수 포함")
    submitted = st.form_submit_button("AI 분석 시작 →", use_container_width=True, type="primary")

if submitted:
    if not request_text.strip():
        st.error("개발 요청 내용을 입력한 뒤 분석을 시작해 주세요.")
    else:
        try:
            with st.spinner("요청을 분석하고 테스트 계획을 구성하고 있습니다…"):
                st.session_state.report = analyze(request_text, change, system, conditions)
        except Exception as error:
            st.error(f"AI 분석 중 오류가 발생했습니다: {error}")

report = st.session_state.get("report")
if report:
    st.markdown("<br><p class='eyebrow'>ANALYSIS REPORT</p><h2>변경 영향 분석 결과</h2>", unsafe_allow_html=True)
    if report.get("is_demo"):
        st.info("데모 화면입니다. 영향 대상은 가상 아키텍처이며, 테스트 결과는 실제 실행 결과가 아닌 모의 결과입니다.")
    st.markdown(f"<div class='summary'>{report.get('summary', '분석 요약이 제공되지 않았습니다.')}</div>", unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("### 02 · 요청 내용 요약")
            a, b = st.columns(2)
            with a:
                st.markdown("**핵심 업무**")
                bullets(report.get('core_tasks', []), "추출된 핵심 업무가 없습니다.")
            with b:
                st.markdown("**주요 데이터 항목**")
                bullets(report.get('data_items', []), "추출된 데이터 항목이 없습니다.")
            st.divider()
            st.markdown("**분석된 변경 내용**")
            st.write(report.get('change_analysis', '변경 내용을 추가로 확인해 주세요.'))
    with right:
        with st.container(border=True):
            st.markdown("### 03 · 영향 대상")
            impacts = report.get('impact_items', [])
            if impacts:
                for item in impacts:
                    st.markdown(f"**{item.get('name', '미분류')}**　`{item.get('type', '기타')}`　영향도: **{item.get('level', '미정')}**")
                    st.caption(item.get('reason', '영향 이유가 제공되지 않았습니다.'))
            else:
                st.info("확인된 대상이 없습니다. 연계 정보가 부족한 상태입니다.")
    with st.container(border=True):
        st.markdown("### 04 · 영향도 연결 구조")
        connections = report.get('connections', [])
        if connections:
            import graphviz
            diagram = graphviz.Digraph("impact", format="svg")
            diagram.attr(rankdir="LR", bgcolor="white", pad="0.25", nodesep="0.45", ranksep="0.7", fontname="Malgun Gothic")
            diagram.attr("node", shape="box", style="rounded,filled", fillcolor="#f5f7fb", color="#cbd5e1", fontname="Malgun Gothic", fontsize="11", margin="0.16,0.1")
            diagram.attr("edge", color="#2357e8", fontcolor="#536173", fontname="Malgun Gothic", fontsize="9", arrowsize="0.7")
            node_ids = {}
            for connection in connections:
                for endpoint in (connection.get('from', ''), connection.get('to', '')):
                    if endpoint and endpoint not in node_ids:
                        node_ids[endpoint] = f"n{len(node_ids)}"
                        diagram.node(node_ids[endpoint], endpoint)
                if connection.get('from') and connection.get('to'):
                    diagram.edge(node_ids[connection['from']], node_ids[connection['to']], label=connection.get('label', ''))
            st.graphviz_chart(diagram, use_container_width=True)
        else:
            st.info("시각화할 연계 정보가 없습니다.")
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("### 05 · 테스트 케이스")
            st.caption("모든 케이스는 생성된 계획이며 실제 테스트 실행 상태는 미실행입니다.")
            cases = report.get('test_cases', [])
            if cases:
                st.dataframe(cases, use_container_width=True, hide_index=True)
            else:
                st.info("생성된 테스트 케이스가 없습니다.")
    with right:
        with st.container(border=True):
            st.markdown("### 06 · 테스트 데이터")
            data_rows = report.get('test_data', [])
            if data_rows:
                st.dataframe(data_rows, use_container_width=True, hide_index=True)
            else:
                st.info("생성된 테스트 데이터가 없습니다.")
    with st.container(border=True):
        st.markdown("### 07 · 테스트 결과")
        st.warning("모의 결과입니다. 앱 또는 백엔드에서 테스트를 실행해 수집한 결과가 아닙니다.")
        results = report.get('test_results', [])
        if results:
            st.dataframe(results, use_container_width=True, hide_index=True)
        else:
            st.info("테스트 실행 환경이 연결되지 않아 결과를 만들 수 없습니다. 케이스는 미실행 상태입니다.")
    with st.container(border=True):
        st.markdown("### 확인 필요 사항")
        qcol, lcol = st.columns(2)
        with qcol:
            st.markdown("**추가 확인**")
            bullets(report.get('questions', []), "추가 확인 사항이 없습니다.")
        with lcol:
            st.markdown("**연동 및 실행 제한**")
            bullets(report.get('limitations', []), "실행 제한이 없습니다.")
    st.download_button("리포트(JSON) 저장 ↓", data=json.dumps(report, ensure_ascii=False, indent=2), file_name="change-scope-report.json", mime="application/json")
