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
# 탭 2: ASME B36.10 / B36.19 규격 선택 모드 (최대 48"까지 확장)
# ==========================================
with tab2:
    st.subheader("1. 재질 선택")
    selected_mat_2 = st.selectbox("재질 선택 (규격선택)", list(materials.keys()), key="mat_2")
    factor_2 = materials[selected_mat_2]

    st.divider()
    st.subheader("2. ASME 표준 규격 선택 (NPS 1/2\" ~ 48\")")

    # 제공해주신 ASME B36.10/19 표준 표 기준 전체 규격 DB (1/2" ~ 48")[cite: 4]
    asme_pipe_db = {
        "1/2\" (NPS 1/2)": {"od": 21.3, "schs": {"Sch 10S / 10": 2.11, "Sch 40 / 40S": 2.77, "Sch 80 / 80S": 3.73}},
        "3/4\" (NPS 3/4)": {"od": 26.7, "schs": {"Sch 10S / 10": 2.11, "Sch 40 / 40S": 2.87, "Sch 80 / 80S": 3.91}},
        "1\" (NPS 1)": {"od": 33.4, "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.38, "Sch 80 / 80S": 4.55}},
        "1-1/4\" (NPS 1-1/4)": {"od": 42.2, "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.56, "Sch 80 / 80S": 4.85}},
        "1-1/2\" (NPS 1-1/2)": {"od": 48.3, "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.68, "Sch 80 / 80S": 5.08}},
        "2\" (NPS 2)": {"od": 60.3, "schs": {"Sch 10S / 10": 2.77, "Sch 40 / 40S": 3.91, "Sch 80 / 80S": 5.54}},
        "2-1/2\" (NPS 2-1/2)": {"od": 73.0, "schs": {"Sch 10S / 10": 3.05, "Sch 40 / 40S": 5.16, "Sch 80 / 80S": 7.01}},
        "3\" (NPS 3)": {"od": 88.9, "schs": {"Sch 10S / 10": 3.05, "Sch 40 / 40S": 5.49, "Sch 80 / 80S": 7.62}},
        "3-1/2\" (NPS 3-1/2)": {"od": 101.6, "schs": {"Sch 10S / 10": 3.05, "Sch 40 / 40S": 5.74, "Sch 80 / 80S": 8.08}},
        "4\" (NPS 4)": {"od": 114.3, "schs": {"Sch 10S / 10": 3.05, "Sch 40 / 40S": 6.02, "Sch 80 / 80S": 8.56}},
        "5\" (NPS 5)": {"od": 141.3, "schs": {"Sch 10S / 10": 3.40, "Sch 40 / 40S": 6.55, "Sch 80 / 80S": 9.53}},
        "6\" (NPS 6)": {"od": 168.3, "schs": {"Sch 5S": 2.77, "Sch 10S / 10": 3.40, "Sch 40 / 40S": 7.11, "Sch 80 / 80S": 10.97}},
        "8\" (NPS 8)": {"od": 219.1, "schs": {"Sch 5S": 2.77, "Sch 10S / 10": 3.76, "Sch 40 / STD": 8.18, "Sch 80 / XS": 12.70}},
        "10\" (NPS 10)": {"od": 273.1, "schs": {"Sch 5S": 3.40, "Sch 10S / 10": 4.19, "Sch 40 / STD": 9.27, "Sch 80 / XS": 15.06}},
        "12\" (NPS 12)": {"od": 323.8, "schs": {"Sch 5S": 3.96, "Sch 10S / 10": 4.57, "Sch 40 / STD": 9.52, "Sch 80 / XS": 17.48}},
        "14\" (NPS 14)": {"od": 355.6, "schs": {"Sch 10S": 4.78, "STD": 9.53, "Sch 40": 11.13, "XS": 12.70, "Sch 80": 19.05}},
        "16\" (NPS 16)": {"od": 406.4, "schs": {"Sch 10S": 4.78, "STD": 9.53, "Sch 40": 12.70, "XS": 12.70, "Sch 80": 21.44}},
        "18\" (NPS 18)": {"od": 457.0, "schs": {"Sch 10S": 4.19, "STD": 9.53, "Sch 40": 14.27, "XS": 12.70, "Sch 80": 23.80}},
        "20\" (NPS 20)": {"od": 508.0, "schs": {"Sch 10S": 5.54, "STD": 9.53, "Sch 40": 15.06, "XS": 12.70, "Sch 80": 26.19}},
        "22\" (NPS 22)": {"od": 558.8, "schs": {"Sch 10S": 5.54, "STD": 9.53, "Sch 40": 15.90, "XS": 12.70, "Sch 80": 28.58}},
        "24\" (NPS 24)": {"od": 609.6, "schs": {"Sch 5S": 5.54, "Sch 10S / 10": 6.35, "STD": 9.53, "Sch 20": 9.53, "Sch 40": 17.48, "XS": 12.70, "Sch 80": 30.96}},
        # --- 24" 초과 대구경 신규 추가 (표 기준 반영) ---[cite: 4]
        "26\" (NPS 26)": {"od": 660.4, "schs": {"Sch 10": 7.92, "STD": 9.53, "Sch 20": 12.70, "XS": 12.70}},
        "28\" (NPS 28)": {"od": 711.2, "schs": {"Sch 10": 7.92, "STD": 9.53, "Sch 20": 12.70, "Sch 30": 15.88, "XS": 12.70}},
        "30\" (NPS 30)": {"od": 762.0, "schs": {"Sch 5S": 6.35, "Sch 10 / 10S": 7.92, "STD": 9.53, "Sch 20": 12.70, "Sch 30": 15.88, "XS": 12.70}},
        "32\" (NPS 32)": {"od": 812.8, "schs": {"Sch 10": 7.92, "STD": 9.53, "Sch 20": 12.70, "Sch 30": 15.88, "Sch 40": 17.48, "XS": 12.70}},
        "34\" (NPS 34)": {"od": 863.6, "schs": {"Sch 10": 7.92, "STD": 9.53, "Sch 20": 12.70, "Sch 30": 15.88, "Sch 40": 17.48, "XS": 12.70}},
        "36\" (NPS 36)": {"od": 914.4, "schs": {"Sch 10": 7.92, "STD": 9.53, "Sch 20": 12.70, "Sch 30": 15.88, "Sch 40": 19.05, "XS": 12.70}},
        "38\" (NPS 38)": {"od": 965.2, "schs": {"STD": 9.53, "XS": 12.70}},
        "40\" (NPS 40)": {"od": 1016.0, "schs": {"STD": 9.53, "XS": 12.70}},
        "42\" (NPS 42)": {"od": 1066.8, "schs": {"STD": 9.53, "XS": 12.70}},
        "44\" (NPS 44)": {"od": 1117.6, "schs": {"STD": 9.53, "XS": 12.70}},
        "46\" (NPS 46)": {"od": 1168.4, "schs": {"STD": 9.53, "XS": 12.70}},
        "48\" (NPS 48)": {"od": 1219.2, "schs": {"STD": 9.53, "XS": 12.70}}
    }

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        selected_nps = st.selectbox("파이프 사이즈 (NPS)", list(asme_pipe_db.keys()), key="nps_select")
    
    available_schs = asme_pipe_db[selected_nps]["schs"]
    with col_s2:
        selected_sch = st.selectbox("스케줄 (Schedule)", list(available_schs.keys()), key="sch_select")

    auto_od = asme_pipe_db[selected_nps]["od"]
    auto_wt = available_schs[selected_sch]
    auto_id = auto_od - (2 * auto_wt)

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

            unit_kg = (auto_od - auto_wt) * auto_wt * factor_2
            unit_ton = unit_kg / 1000.0
            total_ton = unit_ton * length_m

            plate_width_mm = math.pi * (auto_od - auto_wt)
            plate_width_m = plate_width_mm / 1000.0

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
