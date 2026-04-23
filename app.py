import streamlit as st
import pandas as pd
import openai
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import json

# 1. UI 설정
st.set_page_config(page_title="Alibaba Expert Automation", layout="wide")
st.title("🚀 알리바바 상품 등록 최적화 도구 (v2.0)")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    st.divider()
    st.subheader("💰 가격 및 기본 정보")
    min_price = st.number_input("Min Price (FOB)", value=10.0)
    max_price = st.number_input("Max Price (FOB)", value=15.0)
    currency = st.selectbox("Currency", ["USD", "KRW", "EUR"])
    moq = st.number_input("MOQ (최소 주문 수량)", value=10)
    origin = st.text_input("Place of Origin", value="South Korea")
    brand = st.text_input("Brand Name", value="Custom/OEM")

# 2. 메인 입력 영역
tab1, tab2 = st.tabs(["🔗 스마트스토어 링크 분석", "📸 이미지 스크린샷 분석"])

raw_data = ""

with tab1:
    url = st.text_input("스마트스토어 상품 링크를 입력하세요")
    if url and st.button("링크 분석 시작"):
        # 간단한 크롤링 로직 (실제 운영 시에는 더 정교한 스크래퍼 필요)
        try:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            title = soup.find('h3').text if soup.find('h3') else "상품명을 가져오지 못함"
            raw_data = f"상품명: {title}\nURL: {url}"
            st.success(f"데이터 수집 완료: {title}")
        except:
            st.error("링크를 읽어오지 못했습니다.")

with tab2:
    uploaded_file = st.file_uploader("상품 스크린샷 업로드", type=["png", "jpg", "jpeg"])

# 3. AI 로직 및 엑셀 생성
if st.button("알리바바 엑셀 생성 (PIS 5.0 최적화)"):
    if not api_key:
        st.warning("API Key를 입력해주세요.")
    else:
        openai.api_key = api_key
        with st.spinner("AI가 알리바바 최적화 데이터를 생성 중입니다..."):
            
            # AI 프롬프트 (속성 매칭 강화)
            prompt = f"""
            Analyze the following product data and generate 3 variations for Alibaba.com bulk upload.
            Product Context: {raw_data}
            
            Return the result in JSON format with these fields:
            - title: (SEO Optimized English title, max 128 chars)
            - description: (Professional HTML description with benefits and specs)
            - category: (Most relevant Alibaba category path)
            - attributes: [{{ "name": "Material", "value": "..." }}, {{ "name": "Technics", "value": "..." }}, ...]
            - keywords: (3-5 comma separated keywords)
            """
            
            # AI 호출 (예시 구조)
            # response = openai.ChatCompletion.create(...) 
            
            # 가상 데이터 생성 (테스트용)
            data_list = []
            for i in range(3):
                row = {
                    "Product title": f"Premium Custom T-shirt Variation {i+1} - OEM ODM Service",
                    "Product image 1": "이미지 URL을 넣어주세요",
                    "Product description": f"High quality product description for variation {i+1}",
                    "Place of origin": origin,
                    "Brand name": brand,
                    "Category": "Apparel > T-shirts",
                    "Price Unit": currency,
                    "Min. Price": min_price,
                    "Max. Price": max_price,
                    "Min. Order Quantity": moq,
                    "Product attribute name 1": "Material",
                    "Product attribute value 1": "100% Cotton",
                    "Product attribute name 2": "Technics",
                    "Product attribute value 2": "Silk screen printing"
                }
                data_list.append(row)

            # 4. 엑셀 다운로드
            df = pd.DataFrame(data_list)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Alibaba default template')
            
            st.download_button(
                label="📥 최적화된 알리바바 엑셀 다운로드",
                data=output.getvalue(),
                file_name="alibaba_upload_ready.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
