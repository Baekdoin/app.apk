import math
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="파이프 물량 및 견적 계산기", page_icon="📏", layout="centered")

# --- 로그인 세션 관리 ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    """ID/PW 검증 함수"""
    user_id = st.session_state.get("username_input", "")
    user_pw = st.session_state.get("password_input", "")
    
    # Streamlit Secrets에 저장된 값과 비교 (설정 안 되어있을 경우 대비 기본값 적용 가능)
    correct_id = st.secrets.get("auth", {}).get("username", "jamie")
    correct_pw = st.secrets.get("auth", {}).get("password", "benj2892@1")

    if user_id == correct_id and user_pw == correct_pw:
        st.session_state["authenticated"] = True
        del st.session_state["password_input"]  # 비밀번호 메모리 제거
    else:
        st.session_state["authenticated"] = False
        st.error("⚠️ 아이디 또는 비밀번호가 올바르지 않습니다.")

# 로그인되어 있지 않은 경우 로그인 폼 출력 후 종료
if not st.session_state["authenticated"]:
    st.title("🔒 로그인 필요")
    st.text_input("아이디 (ID)", key="username_input")
    st.text_input("비밀번호 (PW)", type="password", key="password_input")
    st.button("로그인", on_click=check_password, type="primary")
    st.stop()  # 로그인 전까지 아래 계산기 코드 실행 안 함

st.title("📏 파이프 물량 및 견적 계산기")
st.write("외경, 내경, 두께 중 2개를 입력하세요. 외경/내경과 두께 단위를 각각 독립적으로 설정할 수 있습니다.")

# 1. 재질 선택
materials = {
    "탄소강 / A105 / WPHY (0.0246615)": 0.0246615,
    "STS 304 (0.0249126)": 0.0249126,
    "STS 316 (0.0250697)": 0.0250697,
    "알루미늄 (0.0084823)": 0.0084823,
}
selected_mat = st.selectbox("1. 재질 선택", list(materials.keys()))
factor = materials[selected_mat]

st.divider()

# 2. 치수 입력 단위 선택 (외경/내경과 두께 단위 독립 분리)
st.subheader("2. 치수 및 길이 입력")

col_u1, col_u2 = st.columns(2)
with col_u1:
    od_id_unit = st.radio("외경/내경 (OD/ID) 단위", ["밀리미터 (mm)", "인치 (inch / NPS)"], horizontal=True)
with col_u2:
    wt_unit = st.radio("두께 (WT) 단위", ["밀리미터 (mm)", "인치 (inch)"], horizontal=True)

col1, col2 = st.columns(2)

with col1:
    od_input = st.text_input("외경 (OD)", value="", placeholder="예: 12 또는 304.8")
    id_input = st.text_input("내경 (ID)", value="", placeholder="예: 10 또는 254.0")

with col2:
    wt_input = st.text_input("두께 (WT)", value="", placeholder="예: 0.5 또는 12.7")
    len_input = st.text_input("총 길이 (Length, m)", value="1000.0")

st.divider()

# 3. 단가 및 환율 입력 (톤당 USD 기준)
st.subheader("3. 단가 및 환율 입력")
col3, col4 = st.columns(2)

with col3:
    price_input = st.text_input("톤당 단가 ($ / Ton)", value="", placeholder="예: 1200.0")

with col4:
    rate_input = st.text_input("원/달러 환율 (KRW/USD)", value="1350.0")

st.divider()

# 계산 버튼
if st.button("견적 계산하기", type="primary", use_container_width=True):
    try:
        # 독립된 단위 스케일 적용
        od_scale = 25.4 if "인치" in od_id_unit else 1.0
        wt_scale = 25.4 if "인치" in wt_unit else 1.0

        od = float(od_input) * od_scale if od_input and od_input.strip() else None
        id_val = float(id_input) * od_scale if id_input and id_input.strip() else None
        wt = float(wt_input) * wt_scale if wt_input and wt_input.strip() else None
        length_m = float(len_input) if len_input and len_input.strip() else 1.0

        # 입력값 개수 확인
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
                # 중량 계산
                unit_kg = (od - wt) * wt * factor
                unit_ton = unit_kg / 1000.0
                total_ton = unit_ton * length_m

                # 플레이트 전개 폭(Circumference) 계산 [중립축 기준: π * (OD - WT)]
                plate_width_mm = math.pi * (od - wt)
                plate_width_m = plate_width_mm / 1000.0

                # 단가 및 환율 처리
                price_val = float(price_input) if price_input.strip() else 0.0
                ex_rate = float(rate_input) if rate_input.strip() else 1350.0

                total_usd = total_ton * price_val
                total_krw = total_usd * ex_rate

                # 결과 출력
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
