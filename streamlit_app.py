import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="날씨 기반 패션 추천 봇", page_icon="👗")


# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    weather_api_key = st.text_input("OpenWeatherMap API Key", type="password")
    
    st.divider() # 구분선

    st.header("사용자 정보 🤵‍♀️")
    st.info("정확한 추천을 위해 정보를 입력해주세요. (선택 사항)")
    
    # 세션 상태에 사용자 정보 필드 초기화 (나이 추가)
    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "city": "Seoul",
            "gender": "여성",
            "age": "", # 나이 필드 추가
            "height": "",
            "weight": "",
            "skin_tone": "",
            "hair_color": ""
        }

    # 사용자 정보 입력을 위한 폼
    with st.form("user_info_form"):
        st.session_state.user_info["city"] = st.text_input("도시 (영문)", value=st.session_state.user_info["city"])
        st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info["gender"]))
        st.session_state.user_info["age"] = st.text_input("나이", value=st.session_state.user_info["age"]) # 나이 입력 UI 추가
        st.session_state.user_info["height"] = st.text_input("키 (cm)", value=st.session_state.user_info["height"])
        st.session_state.user_info["weight"] = st.text_input("몸무게 (kg)", value=st.session_state.user_info["weight"])
        st.session_state.user_info["skin_tone"] = st.text_input("피부톤 (예: 웜톤, 쿨톤)", value=st.session_state.user_info["skin_tone"])
        st.session_state.user_info["hair_color"] = st.text_input("머리색", value=st.session_state.user_info["hair_color"])
        
        submitted = st.form_submit_button("정보 저장")
        if submitted:
            st.success("정보가 저장되었습니다!")


# --- 메인 챗봇 화면 ---
st.title("👗 날씨 기반 패션 추천 봇")
st.write("내일 날씨와 나의 스타일에 어울리는 패션을 추천해드립니다.")


# --- 대표 질문 버튼 ---
st.subheader("어떤 추천을 원하세요? 👇")
example_questions = ["내일 뭐 입지? 👕", "주말 데이트룩 추천 💖", "중요한 미팅용 정장 추천 👔"]
cols = st.columns(len(example_questions))

# 프롬프트를 처리하기 위한 변수 초기화
prompt = None

for i, question in enumerate(example_questions):
    if cols[i].button(question, use_container_width=True):
        prompt = question # 버튼 클릭 시 해당 질문을 프롬프트로 설정

# 하단 채팅 입력 처리
chat_input = st.chat_input("메시지를 입력하세요...")
if chat_input:
    prompt = chat_input


# API 키 입력 확인 후 실행
if not openai_api_key or not weather_api_key:
    st.info("사이드바에서 API 키를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=openai_api_key)


# --- 날씨 정보 함수 ---
# --- 날씨 정보 함수 (디버깅 코드가 추가된 버전) ---
def get_weather_forecast(city, api_key):
    """지정된 도시의 내일 날씨 정보를 가져옵니다."""
    try:
        # 1단계: 도시 이름으로 위도/경도 찾기
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
        
        # --- 디버깅 코드 ---
        print(f"DEBUG: 지오코딩 API 요청 URL: {geo_url}")
        # ------------------
        
        geo_res = requests.get(geo_url).json()
        
        # --- 디버깅 코드 ---
        print(f"DEBUG: 지오코딩 API 응답: {geo_res}")
        # ------------------
        
        if not geo_res:
            return "도시를 찾을 수 없습니다. 영문 도시 이름을 확인해주세요."
        
        lat, lon = geo_res[0]['lat'], geo_res[0]['lon']

        # 2단계: 위도/경도로 날씨 예보 가져오기
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
        forecast_res = requests.get(forecast_url).json()

        # --- 디버깅 코드 ---
        print(f"DEBUG: 날씨 예보 API 응답: {forecast_res}")
        # ------------------

        if forecast_res.get("cod") != "200":
             # 여기서 에러 메시지를 포함하여 반환
             error_message = forecast_res.get('message', '알 수 없는 오류')
             return f"날씨 정보를 가져오는 데 실패했습니다: {error_message}"

        tomorrow = (datetime.now() + timedelta(days=1)).date()
        tomorrow_forecasts = [f for f in forecast_res['list'] if datetime.fromtimestamp(f['dt']).date() == tomorrow]
        
        if not tomorrow_forecasts:
            return "내일 날씨 정보를 찾을 수 없습니다."

        target_forecast = next((f for f in tomorrow_forecasts if datetime.fromtimestamp(f['dt']).hour >= 12), tomorrow_forecasts[0])

        temp = target_forecast['main']['temp']
        temp_min = min(f['main']['temp_min'] for f in tomorrow_forecasts)
        temp_max = max(f['main']['temp_max'] for f in tomorrow_forecasts)
        weather_desc = target_forecast['weather'][0]['description']
        rain_volume = target_forecast.get('rain', {}).get('3h', 0)
        
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


# --- 채팅 기록 표시 ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 어떤 옷을 추천해드릴까요?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --- 프롬프트가 있을 경우 (버튼 클릭 또는 채팅 입력) 챗봇 로직 실행 ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("내일 날씨를 확인하고, 패션을 추천하는 중..."):
            # 1. 날씨 정보 가져오기
            weather_info = get_weather_forecast(st.session_state.user_info["city"], weather_api_key)

            # 2. 사용자 정보 정리 (나이 정보 추가)
            user_info_text = f"- 성별: {st.session_state.user_info.get('gender') or '정보 없음'}\n"
            if st.session_state.user_info.get('age'):
                user_info_text += f"- 나이: {st.session_state.user_info.get('age')}세\n"
            if st.session_state.user_info.get('height'):
                user_info_text += f"- 키: {st.session_state.user_info.get('height')}cm\n"
            if st.session_state.user_info.get('weight'):
                user_info_text += f"- 몸무게: {st.session_state.user_info.get('weight')}kg\n"
            if st.session_state.user_info.get('skin_tone'):
                user_info_text += f"- 피부톤: {st.session_state.user_info.get('skin_tone')}\n"
            if st.session_state.user_info.get('hair_color'):
                user_info_text += f"- 머리색: {st.session_state.user_info.get('hair_color')}\n"

            # 3. OpenAI에 전달할 시스템 프롬프트 정의 (나이 고려 명시)
            system_prompt = f"""
            당신은 사용자의 정보와 내일 날씨를 기반으로 패션을 추천하는 전문 스타일리스트입니다.
            다음 지침에 따라 답변을 생성해주세요.

            1.  먼저, '내일 날씨 정보' 섹션을 만들어 전달받은 날씨 정보를 그대로 보여줍니다.
            2.  '패션 추천' 섹션에서 날씨와 사용자의 신체 정보, **나이**를 고려하여 모자, 겉옷, 상의, 하의 등 전체적인 스타일을 추천합니다.
            3.  '신발 추천' 섹션에서 날씨와 의상에 어울리는 신발을 구체적으로 추천합니다.
            4.  '우산 필요 여부' 섹션에서 날씨 정보의 강수 여부를 기반으로 우산을 챙겨야 할지 명확하게 알려줍니다.
            5.  만약 사용자 정보가 부족하다면(특히 키, 몸무게, 피부톤, 머리색, 나이 등), 성별에 따라 일반적이면서도 세련된 스타일 2가지를 제시해주세요.
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
                
                response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
