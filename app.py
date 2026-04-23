import streamlit as st
import pandas as pd
import openai
from io import BytesIO
import json
import base64
from PIL import Image

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Alibaba Bulk Upload Expert", layout="wide")
st.title("📦 알리바바 상품 등록 자동화 (v2.1 - PIS 5.0 대응)")

# 2. 사이드바 - 설정 및 고정값 입력
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider()
    st.header("💰 가격 및 기본 정보 (고정값)")
    # 이 부분에 입력한 값이 엑셀에 자동으로 들어갑니다.
    currency = st.selectbox("통화 (Currency)", ["USD", "KRW", "EUR"], index=0)
    min_price = st.number_input("최소 가격 (Min Price)", value=10.0, step=0.1)
    max_price = st.number_input("최대 가격 (Max Price)", value=15.0, step=0.1)
    moq = st.number_input("최소 주문량 (MOQ)", value=10, step=1)
    origin = st.text_input("원산지 (Place of Origin)", value="South Korea")
    brand = st.text_input("브랜드 (Brand Name)", value="Custom/OEM")
    
    st.divider()
    num_variants = st.slider("제품당 생성할 변형 버전 수", 1, 5, 3)

# 3. 알리바바 엑셀 템플릿 컬럼 정의
ALIBABA_COLUMNS = [
    'Product title', 'Product image 1', 'Product image 2', 'Product image 3', 
    'Product description', 'Place of origin', 'Brand name', 'Category',
    'Price Unit', 'Min. Price', 'Max. Price', 'Min. Order Quantity',
    'Product attribute name 1', 'Product attribute value 1',
    'Product attribute name 2', 'Product attribute value 2',
    'Product attribute name 3', 'Product attribute value 3',
    'Product attribute name 4', 'Product attribute value 4'
]

# 이미지 인코딩 함수
def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# 4. 메인 분석 로직
uploaded_file = st.file_uploader("상품 스크린샷을 업로드하세요", type=['png', 'jpg', 'jpeg'])

if st.button("🚀 분석 및 엑셀 생성 시작"):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    elif not uploaded_file:
        st.error("이미지를 업로드해주세요.")
    else:
        openai.api_key = api_key
        
        with st.spinner("AI가 상품을 분석하고 알리바바 규격으로 변환 중입니다..."):
            base64_image = encode_image(uploaded_file)
            
            # AI 프롬프트 - 엑셀 컬럼에 정확히 매칭되도록 JSON 구조 강제
            prompt = f"""
            You are an Alibaba.com SEO expert. Analyze this product image and generate {num_variants} variations.
            The goal is a Product Information Score (PIS) of 5.0.
            
            Return ONLY a JSON list of objects. Each object MUST have these keys exactly:
            - title: (SEO optimized English title, include keywords like Wholesale, Custom, OEM)
            - category: (Appropriate Alibaba category path)
            - description: (Detailed HTML description with features and specifications)
            - attr_name1: "Material", attr_val1: (extract from image or infer)
            - attr_name2: "Technics", attr_val2: (extract from image or infer)
            - attr_name3: "Style", attr_val3: (extract from image or infer)
            - attr_name4: "Feature", attr_val4: (extract from image or infer)
            """

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                    response_format={ "type": "json_object" }
                )
                
                res_data = json.loads(response.choices[0].message.content)
                # JSON 키가 리스트인지 확인 (GPT 응답 구조에 따라 대응)
                items = res_data.get('variations', res_data.get('items', list(res_data.values())[0]))

                # 5. 데이터프레임 구성 (사이드바 입력값 결합)
                final_rows = []
                for item in items:
                    row = {
                        'Product title': item.get('title'),
                        'Product image 1': "https://your-image-url.com", # 실제 URL 처리 로직 필요 시 추가
                        'Product description': item.get('description'),
                        'Place of origin': origin,
                        'Brand name': brand,
                        'Category': item.get('category'),
                        'Price Unit': currency,
                        'Min. Price': min_price,
                        'Max. Price': max_price,
                        'Min. Order Quantity': moq,
                        'Product attribute name 1': item.get('attr_name1'),
                        'Product attribute value 1': item.get('attr_val1'),
                        'Product attribute name 2': item.get('attr_name2'),
                        'Product attribute value 2': item.get('attr_val2'),
                        'Product attribute name 3': item.get('attr_name3'),
                        'Product attribute value 3': item.get('attr_val3'),
                        'Product attribute name 4': item.get('attr_name4'),
                        'Product attribute value 4': item.get('attr_val4'),
                    }
                    final_rows.append(row)

                # 6. 엑셀 파일 생성 및 다운로드
                df = pd.DataFrame(final_rows, columns=ALIBABA_COLUMNS)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Alibaba Template')
                
                st.success("✅ 분석 완료! 아래 버튼을 눌러 엑셀을 다운로드하세요.")
                st.download_button(
                    label="📥 알리바바 업로드용 엑셀 다운로드",
                    data=output.getvalue(),
                    file_name="alibaba_bulk_upload.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.table(df[['Product title', 'Min. Price', 'Max. Price', 'Product attribute value 1']])

            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
