import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="AI 패션 추천 봇", page_icon="👗")


# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider()

    st.header("사용자 정보 🤵‍♀️")
    st.info("정확한 추천을 위해 정보를 입력해주세요. (선택 사항)")
    
    if "user_info" not in st.session_state:
        st.session_state.user_info = {
            "city": "Seoul",
            "gender": "여성",
            "age": "",
            "height": "",
            "weight": "",
            "skin_tone": "",
            "hair_color": ""
        }

    with st.form("user_info_form"):
        st.session_state.user_info["city"] = st.text_input("도시 (예: 서울, 부산)", value=st.session_state.user_info["city"])
        st.session_state.user_info["gender"] = st.radio("성별", ["여성", "남성"], index=["여성", "남성"].index(st.session_state.user_info["gender"]))
        st.session_state.user_info["age"] = st.text_input("나이", value=st.session_state.user_info["age"])
        st.session_state.user_info["height"] = st.text_input("키 (cm)", value=st.session_state.user_info["height"])
        st.session_state.user_info["weight"] = st.text_input("몸무게 (kg)", value=st.session_state.user_info["weight"])
        st.session_state.user_info["skin_tone"] = st.text_input("피부톤 (예: 웜톤, 쿨톤)", value=st.session_state.user_info["skin_tone"])
        st.session_state.user_info["hair_color"] = st.text_input("머리색", value=st.session_state.user_info["hair_color"])
        
        submitted = st.form_submit_button("정보 저장")
        if submitted:
            st.success("정보가 저장되었습니다!")


# --- 메인 챗봇 화면 ---
st.title("👗 AI 패션 추천 봇")
st.write("내일 날씨와 나의 스타일에 어울리는 패션을 추천해드립니다.")

st.subheader("어떤 추천을 원하세요? 👇")
example_questions = ["내일 뭐 입지? 👕", "주말 데이트룩 추천 💖", "중요한 미팅용 정장 추천 👔"]
cols = st.columns(len(example_questions))

prompt = None
for i, question in enumerate(example_questions):
    if cols[i].button(question, use_container_width=True):
        prompt = question

chat_input = st.chat_input("메시지를 입력하세요...")
if chat_input:
    prompt = chat_input


if not openai_api_key:
    st.info("사이드바에서 OpenAI API 키를 입력해주세요.")
    st.stop()

client = OpenAI(api_key=openai_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 어떤 옷을 추천해드릴까요?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("웹에서 최신 날씨를 검색하고, 맞춤 패션을 추천하는 중..."):
            
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

            system_prompt = f"""
            당신은 사용자의 정보와 최신 날씨를 기반으로 패션을 추천하는 전문 스타일리스트입니다.
            다음 지침에 따라 답변을 생성해주세요.

            1.  **가장 먼저, 주어진 '오늘 날짜'를 기준으로 '내일'의 날씨 정보를 웹 검색을 통해 실시간으로 확인합니다.** 날씨 정보에는 최고/최저 기온, 하늘 상태(맑음, 흐림 등), 강수 여부가 반드시 포함되어야 합니다.
            2.  확인한 날씨 정보를 바탕으로 '내일 날씨 정보' 섹션을 만들어 사용자에게 보여줍니다.
            3.  '패션 추천' 섹션에서 검색된 날씨와 전달받은 사용자의 신체 정보, 나이를 종합적으로 고려하여 모자, 겉옷, 상의, 하의 등 전체적인 스타일을 추천합니다.
            4.  '신발 추천' 섹션에서 날씨와 의상에 어울리는 신발을 구체적으로 추천합니다.
            5.  '우산 필요 여부' 섹션에서 검색된 날씨의 강수 여부를 기반으로 우산을 챙겨야 할지 명확하게 알려줍니다.
            6.  모든 답변은 친절하고 상냥한 말투를 사용해주세요.
            """
            
            # --- 수정된 부분: 오늘 날짜를 프롬프트에 명시적으로 추가 ---
            today_str = datetime.now().strftime("%Y년 %m월 %d일")
            
            final_prompt = f"""
            오늘은 {today_str}입니다.
            아래 사용자 정보와 요청을 바탕으로, 먼저 웹에서 내일 날씨를 검색한 후 패션 추천을 부탁합니다.

            [사용자 정보]
            - 거주 도시: {st.session_state.user_info["city"]}
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
