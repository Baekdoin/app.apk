import streamlit as st

# 페이지 설정
st.set_page_config(page_title="파이프 물량 및 견적 계산기", page_icon="📏", layout="centered")

st.title("📏 파이프 물량 및 견적 계산기 (원화 단가 기준)")
st.write("외경, 내경, 두께 중 2개를 입력하세요. 인치(inch) 입력 시 자동으로 mm로 환산됩니다.")

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

# 2. 치수 입력 단위 선택
st.subheader("2. 치수 및 길이 입력")
unit_mode = st.radio("치수 입력 단위 선택", ["밀리미터 (mm)", "인치 (inch / NPS)"], horizontal=True)

col1, col2 = st.columns(2)

with col1:
    od_input = st.text_input("외경 (OD)", value="", placeholder="예: 12 또는 812.8")
    id_input = st.text_input("내경 (ID)", value="", placeholder="예: 10 또는 750.8")

with col2:
    wt_input = st.text_input("두께 (WT)", value="", placeholder="예: 0.5 또는 12.7")
    len_input = st.text_input("총 길이 (Length, m)", value="1.0")

st.divider()

# 3. 단가 및 환율 입력 (통화 선택 제거, 원화 단가 기준 통일)
st.subheader("3. 단가 및 환율 입력")
col3, col4 = st.columns(2)

with col3:
    price_input = st.text_input("톤당 단가 (원 / Ton)", value="", placeholder="예: 1500000")

with col4:
    rate_input = st.text_input("원/달러 환율 (KRW/USD)", value="1350.0")

st.divider()

# 계산 버튼
if st.button("견적 계산하기", type="primary", use_container_width=True):
    try:
        # 인치 모드일 경우 25.4 곱해서 mm로 자동 변환
        scale_factor = 25.4 if "인치" in unit_mode else 1.0

        od = float(od_input) * scale_factor if od_input.strip() else None
        id_val = float(id_input) * scale_factor if id_input.strip() else None
        wt = float(wt_input) * scale_factor if wt_input.strip() else None
        length_m = float(len_input) if len_input.strip() else 1.0

        # 입력값 개수 확인
        inputs_count = sum([bool(od), bool(id_val), bool(wt)])
        if inputs_count < 2:
            st.error("⚠️ 외경(OD), 내경(ID), 두께(WT) 중 최소 2가지를 입력해 주세요.")
        else:
            calc_msg = ""
            if od is None:
                od = id_val + (2 * wt)
                calc_msg = f"산출된 외경(OD): {od:.2f} mm ({od/25.4:.3f} inch)"
            elif id_val is None:
                id_val = od - (2 * wt)
                calc_msg = f"산출된 내경(ID): {id_val:.2f} mm ({id_val/25.4:.3f} inch)"
            elif wt is None:
                wt = (od - id_val) / 2.0
                calc_msg = f"산출된 두께(WT): {wt:.2f} mm ({wt/25.4:.3f} inch)"
            else:
                calc_msg = "직접 입력한 치수 검증 완료"

            if wt <= 0 or od <= 0 or id_val < 0 or od <= id_val:
                st.error("⚠️ 물리적으로 불가능한 치수입니다. (OD <= ID 또는 WT <= 0)")
            else:
                # 중량 계산
                unit_kg = (od - wt) * wt * factor
                unit_ton = unit_kg / 1000.0
                total_ton = unit_ton * length_m

                # 단가 및 환율 처리 (원화 단가 기준 고정)
                price_val = float(price_input) if price_input.strip() else 0.0
                ex_rate = float(rate_input) if rate_input.strip() else 1350.0

                total_krw = total_ton * price_val
                total_usd = total_krw / ex_rate if ex_rate > 0 else 0.0

                # 결과 출력
                st.success("✨ 계산이 완료되었습니다!")
                if calc_msg:
                    st.info(calc_msg)

                if "인치" in unit_mode:
                    st.write(f"🔄 **환산된 mm 치수 적용됨** (OD: {od:.2f} mm / ID: {id_val:.2f} mm / WT: {wt:.2f} mm)")

                st.metric(label="미터당 중량", value=f"{unit_kg:.4f} kg/m ({unit_ton:.6f} Ton/m)")
                st.metric(label="총 중량 (Total Ton)", value=f"{total_ton:,.6f} Ton")
                st.metric(label="총 금액 (KRW)", value=f"₩ {total_krw:,.0f}")
                st.metric(label="총 금액 (USD)", value=f"$ {total_usd:,.2f}")

    except ValueError:
        st.error("⚠️ 숫자 형식만 올바르게 입력해 주세요.")
