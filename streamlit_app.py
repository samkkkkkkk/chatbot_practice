import streamlit as st
import requests
from openai import OpenAI
from datetime import datetime, timedelta

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="AI 패션 추천 봇", page_icon="👗")


# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 설정 🔑")
    # 날씨 API 키 입력란 제거
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider() # 구분선

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
        # 도시 입력은 한글도 가능하도록 안내 수정
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
    prompt = chat
