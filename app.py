import math
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="파이프 물량 및 견적 계산기", page_icon="📏", layout="centered")

# --- 자동 로그인 및 세션 관리 ---
query_params = st.query_params

if "authenticated" not in st.session_state:
    if query_params.get("auth") == "pass":
        st.session_state["authenticated"] = True
    else:
        st.session_state["authenticated"] = False

def check_password():
    user_id = st.session_state.get("username_input", "")
    user_pw = st.session_state.get("password_input", "")
    
    correct_id = st.secrets.get("auth", {}).get("username", "jamie")
    correct_pw = st.secrets.get("auth", {}).get("password", "benj2892@#")

    if user_id == correct_id and user_pw == correct_pw:
        st.session_state["authenticated"] = True
        st.query_params["auth"] = "pass"
        if "password_input" in st.session_state:
            del st.session_state["password_input"]
    else:
        st.session_state["authenticated"] = False
        st.error("⚠️ 아이디 또는 비밀번호가 올바르지 않습니다.")

if not st.session_state["authenticated"]:
    st.title("🔒 로그인 필요")
    st.text_input("아이디 (ID)", key="username_input")
    st.text_input("비밀번호 (PW)", type="password", key="password_input")
    st.button("로그인", on_click=check_password, type="primary")
    st.stop()

# --- 파이프 계산기 본문 ---
st.title("📏 파이프 물량 및 견적 계산기")

# 재질 선택 공통
materials = {
    "탄소강 / A105 / WPHY (0.0246615)": 0.0246615,
    "STS 304 (0.0249126)": 0.0249126,
    "STS 316 (0.0250697)": 0.0250697,
    "알루미늄 (0.0084823)": 0.0084823,
}

# 탭 생성 (직접 입력 vs ASME 규격 선택)
tab1, tab2 = st.tabs(["✍️ 직접 입력 모드", "📖 ASME B36.10/19 규격 선택 모드"])

# ==========================================
# 탭 1: 직접 입력 모드
# ==========================================
with tab1:
    st.subheader("1. 재질 선택")
    selected_mat_1 = st.selectbox("재질 선택 (직접입력)", list(materials.keys()), key="mat_1")
    factor_1 = materials[selected_mat_1]

    st.divider()
    st.subheader("2. 치수 및 길이 입력")
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        od_id_unit = st.radio("외경/내경 (OD/ID) 단위", ["밀리미터 (mm)", "인치 (inch / NPS)"], horizontal=True, key="unit_od")
    with col_u2:
        wt_unit = st.radio("두께 (WT) 단위", ["밀리미터 (mm)", "인치 (inch)"], horizontal=True, key="unit_wt")

    col1, col2 = st.columns(2)
    with col1:
        od_input = st.text_input("외경 (OD)", value="", placeholder="예: 12 또는 304.8", key="od_in")
        id_input = st.text_input("내경 (ID)", value="", placeholder="예: 10 또는 254.0", key="id_in")
    with col2:
        wt_input = st.text_input("두께 (WT)", value="", placeholder="예: 0.5 또는 12.7", key="wt_in")
        len_input_1 = st.text_input("총 길이 (Length, m)", value="1000.0", key="len_1")

    st.divider()
    st.subheader("3. 단가 및 환율 입력")
    col3, col4 = st.columns(2)
    with col3:
        price_input_1 = st.text_input("톤당 단가 ($ / Ton)", value="", placeholder="예: 1200.0", key="price_1")
    with col4:
        rate_input_1 = st.text_input("원/달러 환율 (KRW/USD)", value="1350.0", key="rate_1")

    st.divider()

    if st.button("견적 계산하기 (직접입력)", type="primary", use_container_width=True, key="btn_1"):
        try:
            od_scale = 25.4 if "인치" in od_id_unit else 1.0
            wt_scale = 25.4 if "인치" in wt_unit else 1.0

            od = float(od_input) * od_scale if od_input and od_input.strip() else None
            id_val = float(id_input) * od_scale if id_input and id_input.strip() else None
            wt = float(wt_input) * wt_scale if wt_input and wt_input.strip() else None
            length_m = float(len_input_1) if len_input_1 and len_input_1.strip() else 1.0

            inputs_count = sum([bool(od), bool(id_val), bool(wt)])
            if inputs_count < 2:
                st.error("⚠️ 외경(OD), 내경(ID), 두께(WT) 중 최소 2가지를 입력해 주세요.")
            else:
                calc_msg = ""
                if od is None:
                    od = id_val + (2 * wt)
                    calc_msg = f"산출된 외경(OD): {od:.2f} mm"
                elif id_val is None:
                    id_val = od - (2 * wt)
                    calc_msg = f"산출된 내경(ID): {id_val:.2f} mm"
                elif wt is None:
                    wt = (od - id_val) / 2.0
                    calc_msg = f"산출된 두께(WT): {wt:.2f} mm"
                else:
                    calc_msg = "직접 입력한 치수 검증 완료"

                if wt <= 0 or od <= 0 or id_val < 0 or od <= id_val:
                    st.error("⚠️ 물리적으로 불가능한 치수입니다. (OD <= ID 또는 WT <= 0)")
                else:
                    unit_kg = (od - wt) * wt * factor_1
                    unit_ton = unit_kg / 1000.0
                    total_ton = unit_ton * length_m
                    plate_width_mm = math.pi * (od - wt)
                    plate_width_m = plate_width_mm / 1000.0

                    price_val = float(price_input_1) if price_input_1.strip() else 0.0
                    ex_rate = float(rate_input_1) if rate_input_1.strip() else 1350.0
                    total_usd = total_ton * price_val
                    total_krw = total_usd * ex_rate

                    st.success("✨ 계산이 완료되었습니다!")
                    if calc_msg:
                        st.info(calc_msg)

                    st.metric(label="미터당 중량", value=f"{unit_kg:.4f} kg/m ({unit_ton:.6f} Ton/m)")
                    st.metric(label="총 중량 (Total Ton)", value=f"{total_ton:,.6f} Ton")
                    st.metric(label="소재 플레이트 폭 (전개폭)", value=f"{plate_width_mm:,.2f} mm ({plate_width_m:,.3f} m)")
                    st.metric(label="총 금액 (USD)", value=f"$ {total_usd:,.2f}")
                    st.metric(label="총 금액 (KRW)", value=f"₩ {total_krw:,.0f}")
        except ValueError:
            st.error("⚠️ 숫자 형식만 올바르게 입력해 주세요.")

# ==========================================
# 탭 2: ASME B36.10 / B36.19 규격 선택 모드
# ==========================================
with tab2:
    st.subheader("1. 재질 선택")
    selected_mat_2 = st.selectbox("재질 선택 (규격선택)", list(materials.keys()), key="mat_2")
    factor_2 = materials[selected_mat_2]

    st.divider()
    st.subheader("2. ASME 표준 규격 선택 (NPS & Schedule)")

    # ASME B36.10 / B36.19 주요 대표 규격 DB (NPS 기준 외경 mm 및 Sch별 두께 mm 매핑)
    # 형식: "NPS 표시": { 외경(OD_mm), { "Sch종류": 두께(mm), ... } }
    asme_pipe_db = {
        "1/2\" (NPS 1/2)": {
            "od": 21.3,
            schs: {"Sch 10S / 10": 2.11, "Sch 40 / 40S": 2.77, "Sch 80 / 80S": 3.73}
        },
        "3/4\" (NPS 3/4)": {
            "od": 26.7,
            "schs": {"Sch 10S / 10": 2.11, "Sch 40 / 40S": 2.87, "Sch 80 / 80S": 3.91}
        },
        "1\" (NPS 1)": {
            "od": 33.4,
            "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.38, "Sch 80 / 80S": 4.55}
        },
        "1-1/4\" (NPS 1-1/4)": {
            "od": 42.2,
            "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.56, "Sch 80 / 80S": 4.85}
        },
        "1-1/2\" (NPS 1-1/2)": {
            "od": 48.3,
            "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.68, "Sch 80 / 80S": 5.08}
        },
        "2\" (NPS 2)": {
            "od": 60.3,
            "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.91, "Sch 80 / 80S": 5.54}
        },
        "3\" (NPS 3)": {
            "od": 88.9,
            "schs": {"Sch 10S / 10": 3.05, "Sch 40 / 40S": 5.49, "Sch 80 / 80S": 7.62}
        },
        "4\" (NPS 4)": {
            "od": 114.3,
            "schs": {"Sch 10S / 10": 3.05, "Sch 40 / 40S": 6.02, "Sch 80 / 80S": 8.56}
        },
        "6\" (NPS 6)": {
            "od": 168.3,
            "schs": {"Sch 5S": 2.77, "Sch 10S / 10": 3.40, "Sch 40 / 40S": 7.11, "Sch 80 / 80S": 10.97}
        },
        "8\" (NPS 8)": {
            "od": 219.1,
            "schs": {"Sch 5S": 2.77, "Sch 10S / 10": 3.76, "Sch 40 / 40S": 8.18, "Sch 80 / 80S": 12.70}
        },
        "10\" (NPS 10)": {
            "od": 273.1,
            "schs": {"Sch 5S": 3.40, "Sch 10S / 10": 4.19, "Sch 40 / 40S": 9.27, "Sch 80 / 80S": 15.06}
        },
        "12\" (NPS 12)": {
            "od": 323.8,
            "schs": {"Sch 5S": 3.96, "Sch 10S / 10": 4.57, "Sch 40 / 40S": 9.52, "Sch 80 / 80S": 17.48}
        },
        "14\" (NPS 14)": {
            "od": 355.6,
            "schs": {"Sch 10S": 4.78, "Sch 40": 11.13, "Sch 80": 19.05}
        },
        "16\" (NPS 16)": {
            "od": 406.4,
            "schs": {"Sch 10S": 4.78, "Sch 40": 12.70, "Sch 80": 21.44}
        },
        "18\" (NPS 18)": {
            "od": 457.0,
            "schs": {"Sch 10S": 4.19, "Sch 40": 14.27, "Sch 80": 23.80}
        },
        "20\" (NPS 20)": {
            "od": 508.0,
            "schs": {"Sch 10S": 5.54, "Sch 40": 15.06, "Sch 80": 26.19}
        },
        "24\" (NPS 24)": {
            "od": 610.0,
            "schs": {"Sch 10S": 6.35, "Sch 40": 17.48, "Sch 80": 30.96}
        }
    }

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        selected_nps = st.selectbox("파이프 사이즈 (NPS)", list(asme_pipe_db.keys()), key="nps_select")
    
    # 선택된 NPS에 따른 스케줄 목록 동적 연동
    available_schs = asme_pipe_db[selected_nps]["schs"]
    with col_s2:
        selected_sch = st.selectbox("스케줄 (Schedule)", list(available_schs.keys()), key="sch_select")

    # 자동 매핑된 OD와 WT 가져오기
    auto_od = asme_pipe_db[selected_nps]["od"]
    auto_wt = available_schs[selected_sch]
    auto_id = auto_od - (2 * auto_wt)

    # 화면에 자동 매핑된 mm/inch 치수 안내
    st.info(f"📌 **선택 규격 적용 치수** 👉 외경(OD): **{auto_od} mm** ({auto_od/25.4:.3f}인치) | 두께(WT): **{auto_wt} mm** | 내경(ID): **{auto_id:.2f} mm**")

    len_input_2 = st.text_input("총 길이 (Length, m)", value="1000.0", key="len_2")

    st.divider()
    st.subheader("3. 단가 및 환율 입력")
    col3_2, col4_2 = st.columns(2)
    with col3_2:
        price_input_2 = st.text_input("톤당 단가 ($ / Ton)", value="", placeholder="예: 1200.0", key="price_2")
    with col4_2:
        rate_input_2 = st.text_input("원/달러 환율 (KRW/USD)", value="1350.0", key="rate_2")

    st.divider()

    if st.button("견적 계산하기 (규격선택)", type="primary", use_container_width=True, key="btn_2"):
        try:
            length_m = float(len_input_2) if len_input_2 and len_input_2.strip() else 1.0

            # 중량 계산
            unit_kg = (auto_od - auto_wt) * auto_wt * factor_2
            unit_ton = unit_kg / 1000.0
            total_ton = unit_ton * length_m

            # 플레이트 폭 계산
            plate_width_mm = math.pi * (auto_od - auto_wt)
            plate_width_m = plate_width_mm / 1000.0

            # 단가 및 환율 처리
            price_val = float(price_input_2) if price_input_2.strip() else 0.0
            ex_rate = float(rate_input_2) if rate_input_2.strip() else 1350.0
            total_usd = total_ton * price_val
            total_krw = total_usd * ex_rate

            st.success("✨ ASME 규격 기반 계산이 완료되었습니다!")
            st.metric(label="미터당 중량", value=f"{unit_kg:.4f} kg/m ({unit_ton:.6f} Ton/m)")
            st.metric(label="총 중량 (Total Ton)", value=f"{total_ton:,.6f} Ton")
            st.metric(label="소재 플레이트 폭 (전개폭)", value=f"{plate_width_mm:,.2f} mm ({plate_width_m:,.3f} m)")
            st.metric(label="총 금액 (USD)", value=f"$ {total_usd:,.2f}")
            st.metric(label="총 금액 (KRW)", value=f"₩ {total_krw:,.0f}")

        except ValueError:
            st.error("⚠️ 숫자 형식만 올바르게 입력해 주세요.")
