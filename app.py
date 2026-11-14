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

materials = {
    "탄소강 / A105 / WPHY (0.0246615)": 0.0246615,
    "STS 304 (0.0249126)": 0.0249126,
    "STS 316 (0.0250697)": 0.0250697,
    "알루미늄 (0.0084823)": 0.0084823,
}

# 지역별 운임 표 Total 금액에 0.27을 곱해 USD로 환산 반영[cite: 4]
shipping_destinations = {
    "지역 미선택 (운임 미포함)": 0.0,
    "Jebel Ali": 2123.75 * 0.27,      # 약 $573.41
    "Hamriyah": 2023.75 * 0.27,      # 약 $546.41
    "Sharjah": 1923.75 * 0.27,       # 약 $519.41
    "Ras Al Khaimah (SAQR)": 2133.75 * 0.27, # 약 $576.11
    "Fujairah (city only)": 1973.75 * 0.27,  # 약 $532.91
    "Fujairah (Dibba)": 2173.75 * 0.27,      # 약 $586.91
    "Abu Dhabi (Kizad)": 2823.75 * 0.27,     # 약 $762.41
    "Abu Dhabi (Mussafah)": 2823.75 * 0.27,  # 약 $762.41
    "Abu Dhabi (Ruwais)": 3823.75 * 0.27     # 약 $1,032.41
}

tab1, tab2 = st.tabs(["✍️ 직접 입력 모드", "📖 ASME B36.10/19 규격 조회 모드"])

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
        wt_unit = st.radio("두께 (WT) 단위", ["밀리미터 (mm)", "인치 (inch)"], horizontal=True, key="wt_unit")

    col1, col2 = st.columns(2)
    with col1:
        od_input = st.text_input("외경 (OD)", value="", placeholder="예: 12 또는 304.8", key="od_in")
        id_input = st.text_input("내경 (ID)", value="", placeholder="예: 10 또는 254.0", key="id_in")
    with col2:
        wt_input = st.text_input("두께 (WT)", value="", placeholder="예: 0.5 또는 12.7", key="wt_in")
        len_input_1 = st.text_input("총 길이 (Length, m)", value="1000.0", key="len_1")

    pipe_unit_len = st.number_input("파이프 본당 기준 길이 (m)", min_value=1.0, value=12.0, step=1.0, key="pipe_unit_len")

    st.divider()
    st.subheader("3. 단가 및 운송 목적지 입력")
    col3, col4 = st.columns(2)
    with col3:
        price_input_1 = st.text_input("톤당 단가 ($ / Ton)", value="", placeholder="예: 1200.0", key="price_1")
    with col4:
        rate_input_1 = st.text_input("원/달러 환율 (KRW/USD)", value="1350.0", key="rate_1")

    selected_dest = st.selectbox("도착 지역 선택 (운송비 산출용 - 1AED=0.27USD 적용)", list(shipping_destinations.keys()), key="dest_select")

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

                    od_inch = od / 25.4
                    
                    if 18.0 <= od_inch <= 20.0:
                        truck_capacity = 12
                        tier_desc = "18\"~20\" 구간 (총 12개 적재)"[cite: 3]
                    elif 22.0 <= od_inch <= 24.0:
                        truck_capacity = 9
                        tier_desc = "22\"~24\" 구간 (총 9개 적재)"[cite: 3]
                    elif 26.0 <= od_inch <= 32.0:
                        truck_capacity = 5
                        tier_desc = "26\"~32\" 구간 (총 5개 적재)"[cite: 3]
                    elif 34.0 <= od_inch <= 52.0:
                        truck_capacity = 3
                        tier_desc = "34\"~52\" 구간 (총 3개 적재)"[cite: 3]
                    elif od_inch >= 54.0:
                        truck_capacity = 1
                        tier_desc = "54\" 이상 구간 (총 1개 적재)"[cite: 3]
                    else:
                        truck_capacity = 12
                        tier_desc = "18\" 미만 소구경 (기본 12개 적재 기준)"

                    total_pipes = math.ceil(length_m / pipe_unit_len)
                    required_trucks = math.ceil(total_pipes / truck_capacity)

                    # USD 환산된 1대당 운임비 × 트럭 수
                    unit_freight_cost_usd = shipping_destinations[selected_dest]
                    total_freight_cost_usd = required_trucks * unit_freight_cost_usd

                    price_val = float(price_input_1) if price_input_1.strip() else 0.0
                    ex_rate = float(rate_input_1) if rate_input_1.strip() else 1350.0
                    material_usd = total_ton * price_val

                    # 최종 합산 가격 (자재비 USD + 운임비 USD) -> KRW 환산
                    grand_total_usd = material_usd + total_freight_cost_usd
                    grand_total_krw = grand_total_usd * ex_rate

                    st.success("✨ 계산이 완료되었습니다!")
                    if calc_msg:
                        st.info(calc_msg)

                    st.metric(label="미터당 중량", value=f"{unit_kg:.4f} kg/m ({unit_ton:.6f} Ton/m)")
                    st.metric(label="총 중량 (Total Ton)", value=f"{total_ton:,.6f} Ton")
                    st.metric(label="소재 플레이트 폭 (전개폭)", value=f"{plate_width_mm:,.2f} mm ({plate_width_m:,.3f} m)")
                    
                    st.metric(label="🚚 필요한 트럭 수", value=f"{required_trucks} 대", delta=f"총 파이프 {total_pipes}본 / {tier_desc}")

                    if selected_dest != "지역 미선택 (운임 미포함)":
                        st.metric(label=f"📦 총 운송비 ({selected_dest} 기준)", value=f"$ {total_freight_cost_usd:,.2f}", delta=f"1대당 $ {unit_freight_cost_usd:,.2f} × {required_trucks}대")
                    else:
                        st.info("💡 지역을 선택하시면 USD 환산 총 운송비 및 최종 합산 견적이 함께 산출됩니다.")

                    st.metric(label="자재 순수 금액 (USD)", value=f"$ {material_usd:,.2f}")
                    
                    st.divider()
                    st.metric(label="🔥 최종 총가격 (자재비 + 운송비 포함)", value=f"$ {grand_total_usd:,.2f}", delta=f"환율 적용 ₩ {grand_total_krw:,.0f}")
        except ValueError:
            st.error("⚠️ 숫자 형식만 올바르게 입력해 주세요.")

# ==========================================
# 탭 2: ASME B36.10 / B36.19 규격 조회 모드
# ==========================================
with tab2:
    st.subheader("📖 ASME 표준 규격 치수 조회 (1/2\" ~ 48\")")

    asme_pipe_db = {
        "1/2\" (NPS 1/2, DN 15)": {"od": 21.3, "schs": {"S10": 2.11, "STD / S40": 2.77, "XS / S80": 3.73, "S160": 4.78, "XXS": 7.47, "S5S": 1.65, "S10S": 2.11, "S40S": 2.77, "S80S": 3.73}},
        "3/4\" (NPS 3/4, DN 20)": {"od": 26.7, "schs": {"S5": 1.65, "S10": 2.11, "S30": 2.41, "STD / S40": 2.87, "XS / S80": 3.91, "S160": 5.56, "XXS": 7.82, "S5S": 1.65, "S10S": 2.11, "S40S": 2.87, "S80S": 3.91}},
        "1\" (NPS 1, DN 25)": {"od": 33.4, "schs": {"S5": 1.65, "S10": 2.77, "S30": 2.90, "STD / S40": 3.38, "XS / S80": 4.55, "S160": 6.35, "XXS": 9.09, "S5S": 1.65, "S10S": 2.77, "S40S": 3.38, "S80S": 4.55}},
        "1 1/4\" (NPS 1-1/4, DN 32)": {"od": 42.2, "schs": {"S5": 1.65, "S10": 2.77, "S30": 2.97, "STD / S40": 3.56, "XS / S80": 4.85, "S160": 6.35, "XXS": 9.70, "S5S": 1.65, "S10S": 2.77, "S40S": 3.56, "S80S": 4.85}},
        "1 1/2\" (NPS 1-1/2, DN 40)": {"od": 48.3, "schs": {"S5": 1.65, "S10": 2.77, "S30": 3.18, "STD / S40": 3.68, "XS / S80": 5.08, "S160": 7.14, "XXS": 10.15, "S5S": 1.65, "S10S": 2.77, "S40S": 3.68, "S80S": 5.08}},
        "2\" (NPS 2, DN 50)": {"od": 60.3, "schs": {"S5": 1.65, "S10": 2.77, "S30": 3.18, "STD / S40": 3.91, "XS / S80": 5.54, "S160": 8.74, "XXS": 11.07, "S5S": 1.65, "S10S": 2.77, "S40S": 3.91, "S80S": 5.54}},
        "2 1/2\" (NPS 2-1/2, DN 65)": {"od": 73.0, "schs": {"S5": 2.11, "S10": 3.05, "S30": 4.78, "STD / S40": 5.16, "XS / S80": 7.01, "S160": 9.53, "XXS": 14.02, "S5S": 2.11, "S10S": 3.05, "S40S": 5.16, "S80S": 7.01}},
        "3\" (NPS 3, DN 80)": {"od": 88.9, "schs": {"S5": 2.11, "S10": 3.05, "S30": 4.78, "STD / S40": 5.49, "XS / S80": 7.62, "S160": 11.13, "XXS": 15.24, "S5S": 2.11, "S10S": 3.05, "S40S": 5.49, "S80S": 7.62}},
        "3 1/2\" (NPS 3-1/2, DN 90)": {"od": 101.6, "schs": {"S5": 2.11, "S10": 3.05, "S30": 4.78, "STD / S40": 5.74, "XS / S80": 8.08, "S5S": 2.11, "S10S": 3.05, "S40S": 5.74, "S80S": 8.08}},
        "4\" (NPS 4, DN 100)": {"od": 114.3, "schs": {"S5": 2.11, "S10": 3.05, "S30": 4.78, "STD / S40": 6.02, "XS / S80": 8.56, "S120": 11.13, "S160": 13.49, "XXS": 17.12, "S5S": 2.11, "S10S": 3.05, "S40S": 6.02, "S80S": 8.56}},
        "5\" (NPS 5, DN 125)": {"od": 141.3, "schs": {"S5": 2.77, "S10": 3.40, "STD / S40": 6.55, "XS / S80": 9.53, "S120": 12.70, "S160": 15.88, "XXS": 19.05, "S5S": 2.77, "S10S": 3.40, "S40S": 6.55, "S80S": 9.53}},
        "6\" (NPS 6, DN 150)": {"od": 168.3, "schs": {"S5": 2.77, "S10": 3.40, "STD / S40": 7.11, "XS / S80": 10.97, "S120": 14.27, "S160": 18.26, "XXS": 21.95, "S5S": 2.77, "S10S": 3.40, "S40S": 7.11, "S80S": 10.97}},
        "8\" (NPS 8, DN 200)": {"od": 219.1, "schs": {"S5": 2.77, "S10": 3.76, "S20": 6.35, "S30": 7.04, "STD / S40": 8.18, "S60": 10.31, "XS / S80": 12.70, "S100": 15.09, "S120": 18.26, "S140": 20.62, "S160": 23.01, "XXS": 22.23, "S5S": 2.77, "S10S": 3.76, "S40S": 8.18, "S80S": 12.70}},
        "10\" (NPS 10, DN 250)": {"od": 273.0, "schs": {"S5": 3.40, "S10": 4.19, "S20": 6.35, "S30": 7.80, "STD / S40": 9.27, "S60": 12.70, "XS / S80": 12.70, "S100": 15.09, "S120": 18.26, "S140": 21.44, "S160": 25.40, "XXS": 25.40, "S5S": 3.40, "S10S": 4.19, "S40S": 9.27, "S80S": 12.70}},
        "12\" (NPS 12, DN 300)": {"od": 323.8, "schs": {"S5": 3.96, "S10": 4.57, "S20": 6.35, "S30": 8.38, "STD": 9.53, "S40": 10.31, "S60": 14.27, "XS": 12.70, "S80": 17.48, "S100": 21.44, "S120": 25.40, "S140": 28.58, "S160": 33.32, "XXS": 25.40, "S5S": 3.96, "S10S": 4.57, "S40S": 9.53, "S80S": 12.70}},
        "14\" (NPS 14, DN 350)": {"od": 355.6, "schs": {"S5": 3.96, "S10": 4.78, "S20": 6.35, "S30": 7.92, "STD / S40": 9.53, "S60": 11.13, "XS": 12.70, "S80": 15.09, "S100": 19.05, "S120": 23.83, "S140": 27.79, "S160": 31.75, "S5S": 3.96, "S10S": 4.78, "S40S": 9.53, "S80S": 12.70}},
        "16\" (NPS 16, DN 400)": {"od": 406.4, "schs": {"S10": 4.19, "S20": 6.35, "S30": 7.92, "STD / S40": 9.53, "S60": 12.70, "XS": 12.70, "S80": 16.66, "S100": 21.44, "S120": 26.19, "S140": 30.96, "S160": 36.53, "XXS": 40.49, "S10S": 4.19, "S40S": 9.53, "S80S": 12.70}},
        "18\" (NPS 18, DN 450)": {"od": 457.0, "schs": {"S10": 4.19, "S20": 6.35, "S30": 7.92, "STD": 9.53, "S40": 11.13, "S60": 14.27, "XS": 12.70, "S80": 19.05, "S100": 23.83, "S120": 29.36, "S140": 34.93, "S160": 39.67, "XXS": 45.24, "S10S": 4.19, "S40S": 9.53, "S80S": 12.70}},
        "20\" (NPS 20, DN 500)": {"od": 508.0, "schs": {"S10": 4.78, "S20": 6.35, "S30": 9.53, "STD": 9.53, "S40": 12.70, "S60": 15.09, "XS": 12.70, "S80": 20.62, "S100": 26.19, "S120": 32.54, "S140": 38.10, "S160": 44.45, "XXS": 50.01, "S10S": 4.78, "S40S": 9.53, "S80S": 12.70}},
        "22\" (NPS 22, DN 550)": {"od": 558.8, "schs": {"S10": 4.78, "S20": 6.35, "S30": 9.53, "STD": 9.53, "S40": 12.70, "S60": 15.90, "XS": 12.70, "S80": 22.23, "S100": 28.58, "S120": 34.93, "S140": 41.28, "S160": 47.63, "XXS": 53.98, "S10S": 4.78}},
        "24\" (NPS 24, DN 600)": {"od": 609.6, "schs": {"S5": 5.54, "S10": 6.35, "S20": 9.53, "S30": 14.27, "STD": 9.53, "S40": 17.48, "S60": 24.61, "XS": 12.70, "S80": 30.96, "S100": 38.89, "S120": 46.02, "S140": 52.37, "S160": 59.54, "S5S": 5.54, "S10S": 6.35, "S40S": 9.53, "S80S": 12.70}},
        "26\" (NPS 26, DN 650)": {"od": 660.4, "schs": {"S10": 7.92, "S20": 12.70, "STD": 9.53, "XS": 12.70}},
        "28\" (NPS 28, DN 700)": {"od": 711.2, "schs": {"S10": 7.92, "S20": 12.70, "S30": 15.88, "STD": 9.53, "XS": 12.70}},
        "30\" (NPS 30, DN 750)": {"od": 762.0, "schs": {"S5": 6.35, "S10": 7.92, "S20": 12.70, "S30": 15.88, "STD": 9.53, "XS": 12.70, "S5S": 6.35, "S10S": 7.92}},
        "32\" (NPS 32, DN 800)": {"od": 812.8, "schs": {"S10": 7.92, "S20": 12.70, "S30": 15.88, "STD": 9.53, "S40": 17.48, "XS": 12.70}},
        "34\" (NPS 34, DN 850)": {"od": 863.6, "schs": {"S10": 7.92, "S20": 12.70, "S30": 15.88, "STD": 9.53, "S40": 17.48, "XS": 12.70}},
        "36\" (NPS 36, DN 900)": {"od": 914.4, "schs": {"S10": 7.92, "S20": 12.70, "S30": 15.88, "STD": 9.53, "S40": 19.05, "XS": 12.70}},
        "38\" (NPS 38, DN 950)": {"od": 965.2, "schs": {"STD": 9.53, "XS": 12.70}},
        "40\" (NPS 40, DN 1000)": {"od": 1016.0, "schs": {"STD": 9.53, "XS": 12.70}},
        "42\" (NPS 42, DN 1050)": {"od": 1066.8, "schs": {"STD": 9.53, "XS": 12.70}},
        "44\" (NPS 44, DN 1100)": {"od": 1117.6, "schs": {"STD": 9.53, "XS": 12.70}},
        "46\" (NPS 46, DN 1150)": {"od": 1168.4, "schs": {"STD": 9.53, "XS": 12.70}},
        "48\" (NPS 48, DN 1200)": {"od": 1219.2, "schs": {"STD": 9.53, "XS": 12.70}}
    }

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        selected_nps = st.selectbox("파이프 사이즈 (NPS / DN)", list(asme_pipe_db.keys()), key="nps_select")
    
    available_schs = asme_pipe_db[selected_nps]["schs"]
    with col_s2:
        selected_sch = st.selectbox("스케줄 (Schedule)", list(available_schs.keys()), key="sch_select")

    auto_od = asme_pipe_db[selected_nps]["od"]
    auto_wt = available_schs[selected_sch]
    auto_id = auto_od - (2 * auto_wt)

    st.divider()

    st.markdown("### 📐 규격 치수 환산 결과")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric(label="두께 (WT)", value=f"{auto_wt:.2f} mm", delta=f"{auto_wt/25.4:.3f} inch")
    with col_r2:
        st.metric(label="외경 (OD)", value=f"{auto_od:.1f} mm", delta=f"{auto_od/25.4:.3f} inch")
    with col_r3:
        st.metric(label="내경 (ID)", value=f"{auto_id:.2f} mm", delta=f"{auto_id/25.4:.3f} inch")
