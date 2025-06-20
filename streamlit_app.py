import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="날씨 기반 패션 추천 봇", page_icon="👗")


# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    # .toml 파일을 사용하지 않고 직접 API 키 입력받기
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    weather_api_key = st.text_input("OpenWeatherMap API Key", type="password")
    
    st.divider() # 구분선

    st.header("사용자 정보 🤵‍♀️")
    st.info("정확한 추천을 위해 정보를 입력해주세요. (선택 사항)")
    
    # 세션 상태에 사용자 정보 필드 초기화
    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "city": "Seoul",
            "gender": "여성",
            "height": "",
            "weight": "",
            "skin_tone": "",
            "hair_color": ""
        }

    # 사용자 정보 입력을 위한 폼
    with st.form("user_info_form"):
        st.session_state.user_info["city"] = st.text_input("도시 (영문)", value=st.session_state.user_info["city"])
        st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info["gender"]))
        st.session_state.user_info["height"] = st.text_input("키 (cm)", value=st.session_state.user_info["height"])
        st.session_state.user_info["weight"] = st.text_input("몸무게 (kg)", value=st.session_state.user_info["weight"])
        st.session_state.user_info["skin_tone"] = st.text_input("피부톤 (예: 웜톤, 쿨톤)", value=st.session_state.user_info["skin_tone"])
        st.session_state.user_info["hair_color"] = st.text_input("머리색", value=st.session_state.user_info["hair_color"])
        
        submitted = st.form_submit_button("정보 저장")
        if submitted:
            st.success("정보가 저장되었습니다!")


# --- 메인 챗봇 화면 ---
st.title("👗 날씨 기반 패션 추천 봇")

# API 키 입력 확인
if not openai_api_key or not weather_api_key:
    st.info("사이드바에서 API 키를 입력해주세요.")
    st.stop()

# API 클라이언트 초기화
client = OpenAI(api_key=openai_api_key)


# --- 날씨 정보 함수 ---
def get_weather_forecast(city, api_key):
    """지정된 도시의 내일 날씨 정보를 가져옵니다."""
    try:
        # 도시 이름으로 위도, 경도 찾기
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        geo_res = requests.get(geo_url).json()
        if not geo_res:
            return "도시를 찾을 수 없습니다. 영문 도시 이름을 확인해주세요."
        
        lat, lon = geo_res[0]['lat'], geo_res[0]['lon']

        # 5일/3시간 예보 데이터 가져오기
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
        forecast_res = requests.get(forecast_url).json()

        if forecast_res.get("cod") != "200":
             return f"날씨 정보를 가져오는 데 실패했습니다: {forecast_res.get('message')}"

        # 내일 날씨 데이터 필터링 (내일 정오 기준)
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        tomorrow_forecasts = [f for f in forecast_res['list'] if datetime.fromtimestamp(f['dt']).date() == tomorrow]
        
        if not tomorrow_forecasts:
            return "내일 날씨 정보를 찾을 수 없습니다."

        # 내일의 대표 날씨 정보 (정오 기준 또는 가장 이른 시간)
        target_forecast = next((f for f in tomorrow_forecasts if datetime.fromtimestamp(f['dt']).hour >= 12), tomorrow_forecasts[0])

        temp = target_forecast['main']['temp']
        temp_min = min(f['main']['temp_min'] for f in tomorrow_forecasts)
        temp_max = max(f['main']['temp_max'] for f in tomorrow_forecasts)
        weather_desc = target_forecast['weather'][0]['description']
        rain_volume = target_forecast.get('rain', {}).get('3h', 0)
        
        # 계절 판단
        month = tomorrow.month
        if month in [3, 4, 5]: season = "봄"
        elif month in [6, 7, 8]: season = "여름"
        elif month in [9, 10, 11]: season = "가을"
        else: season = "겨울"

        weather_info = (
            f"**계절**: {season}\n"
            f"**날씨**: {weather_desc}\n"
            f"**평균 기온**: {temp}°C (최저 {temp_min}°C / 최고 {temp_max}°C)\n"
            f"**강수 여부**: {'비 소식이 있습니다.' if rain_volume > 0 else '비 소식은 없습니다.'}"
        )
        return weather_info

    except Exception as e:
        return f"날씨 정보 조회 중 오류 발생: {e}"


st.write("내일 날씨에 어울리는 패션을 추천해드립니다. '내일 뭐 입지?'라고 물어보세요!")

# 세션 상태에 메시지 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 내일 입을 옷을 추천해드릴까요?"}]

# 이전 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 어시스턴트 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("내일 날씨를 확인하고, 패션을 추천하는 중..."):
            # 1. 날씨 정보 가져오기
            weather_info = get_weather_forecast(st.session_state.user_info["city"], weather_api_key)

            # 2. 사용자 정보 정리
            user_info_text = f"- 성별: {st.session_state.user_info.get('gender') or '정보 없음'}\n"
            if st.session_state.user_info.get('height'):
                user_info_text += f"- 키: {st.session_state.user_info.get('height')}cm\n"
            if st.session_state.user_info.get('weight'):
                user_info_text += f"- 몸무게: {st.session_state.user_info.get('weight')}kg\n"
            if st.session_state.user_info.get('skin_tone'):
                user_info_text += f"- 피부톤: {st.session_state.user_info.get('skin_tone')}\n"
            if st.session_state.user_info.get('hair_color'):
                user_info_text += f"- 머리색: {st.session_state.user_info.get('hair_color')}\n"

            # 3. OpenAI에 전달할 시스템 프롬프트 정의
            system_prompt = f"""
            당신은 사용자의 정보와 내일 날씨를 기반으로 패션을 추천하는 전문 스타일리스트입니다.
            다음 지침에 따라 답변을 생성해주세요.

            1.  먼저, '내일 날씨 정보' 섹션을 만들어 전달받은 날씨 정보를 그대로 보여줍니다.
            2.  '패션 추천' 섹션에서 날씨와 사용자의 신체 정보를 고려하여 모자, 겉옷, 상의, 하의 등 전체적인 스타일을 추천합니다.
            3.  '신발 추천' 섹션에서 날씨와 의상에 어울리는 신발을 구체적으로 추천합니다.
            4.  '우산 필요 여부' 섹션에서 날씨 정보의 강수 여부를 기반으로 우산을 챙겨야 할지 명확하게 알려줍니다.
            5.  만약 사용자 정보가 부족하다면(특히 키, 몸무게, 피부톤, 머리색 등), 성별에 따라 일반적이면서도 세련된 스타일 2가지를 제시해주세요.
            6.  모든 답변은 친절하고 상냥한 말투를 사용해주세요.
            """
            
            # 4. 최종 프롬프트 구성
            final_prompt = f"""
            아래 정보를 바탕으로 패션 추천을 부탁합니다.

            [내일 날씨 정보]
            {weather_info}

            [사용자 정보]
            {user_info_text}

            [사용자 요청]
            {prompt}
            """
            
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": final_prompt}
                    ],
                    stream=True,
                )
                
                # 스트리밍 응답 표시 및 저장
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
