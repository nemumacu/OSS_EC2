import streamlit as st
import json
import random
import time

# 캐싱

@st.cache_data
def load_full_database():
    try:
        with open('quiz_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return [{"sentence": "데이터 파일이 없습니다.", "title": "오류", "author": "관리자"}]

@st.cache_data
def generate_quiz_set(player_name, seed_val):
    full_db = load_full_database()
    
    # 시드 값을 이용해 플레이어마다 다른 문제 세트 생성
    unique_seed = hash(player_name) + seed_val
    random.seed(unique_seed)
    
    sample_count = min(len(full_db), 10)
    selected = random.sample(full_db, sample_count)
    
    quiz_set = []
    for q in selected:
        correct = f"{q['title']}, {q['author']}"
        others = [f"{item['title']}, {item['author']}" for item in full_db 
                  if f"{item['title']}, {item['author']}" != correct]
        wrong_options = random.sample(others, min(len(others), 2))
        # 답이 아닌 항목들 중 랜덤 두 개 항목을 가져와 오답 항목 생성
        options = [correct] + wrong_options
        random.shuffle(options)
        
        quiz_set.append({
            "q": q['sentence'],
            "ans": correct,
            "options": options
        })
    return quiz_set

# 세션 상태 초기 설정
if 'user_progress' not in st.session_state:
    st.session_state.user_progress = {}

defaults = {
    'page': 'login',
    'login_done': False,
    'player_name': '',
    'current_index': 0,
    'score': 0,
    'quiz_data': [],
    'answers': [],
    'show_login_input': False,
    'submitted': False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if 'seed' not in st.session_state:
    st.session_state.seed = 42

# 우측 상단 헤더 (로그인 상태 표시, 플레이어명 표시, 로그아웃)
col1, col2 = st.columns([4, 1])

with col2:
    if not st.session_state.login_done:
        st.write("🔴 **unsigned**")
    else:
        st.write("🟢 **signed up**")
        st.caption(f"ID: {st.session_state.player_name}")
        if st.button("로그아웃"):
            for key in defaults.keys():
                st.session_state[key] = defaults[key] 
            st.rerun()

# 화면 구성

# [로그인 화면
if st.session_state.page == 'login':
    st.title("📖 문학 작품 첫 문장 맞추기")
    st.subheader("26-1 OSS 중간대체과제")
    st.write("이름: 김수연 / 학번: 2024508115")

    if not st.session_state.login_done:
        if st.button("플레이어 로그인하기"):
            st.session_state.show_login_input = True
        
        if st.session_state.show_login_input:
            name_input = st.text_input("플레이어명 입력:")
            
            if st.button("확인"):
                if name_input.strip():
                    st.session_state.player_name = name_input.strip()
                    st.session_state.login_done = True

                    print(f"\n>>> [SYSTEM] 새 플레이어 로그인: {st.session_state.player_name}")
                    print(f">>> [SYSTEM] 현재 세션 시드: {st.session_state.seed}")
                    
                    if name_input in st.session_state.user_progress:
                        st.session_state.seed = st.session_state.user_progress[name_input]
                    else:
                        st.session_state.user_progress[name_input] = 42
                        st.session_state.seed = 42
                        
                    st.success(f"✅ 환영합니다, {name_input}님")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("⚠️ 플레이어명을 정확히 입력해주세요.")
                # -------------------------------
    else:
        st.info(f"현재 접속: {st.session_state.player_name}님")
        if st.button("문제 풀기"):
            st.session_state.quiz_data = generate_quiz_set(st.session_state.player_name, st.session_state.seed)
            print(f">>> [QUIZ] 10문제 세트가 생성되었습니다.")
            st.session_state.page = 'quiz'
            st.session_state.current_index = 0
            st.rerun()

# 문제 풀이 화면
elif st.session_state.page == 'quiz':
    if not st.session_state.quiz_data:
        st.session_state.page = 'login'
        st.rerun()

    curr_idx = st.session_state.current_index
    if curr_idx >= len(st.session_state.quiz_data):
        st.session_state.page = 'result'
        st.rerun()

    data = st.session_state.quiz_data[curr_idx]
    st.title("✍️ 문제 풀이")
    st.markdown(f"<div style='text-align: right; color: gray;'>문제 {curr_idx + 1} / 10</div>", unsafe_allow_html=True)
    st.markdown(f"#### \"{data['q']}\"")
    
    choice = st.radio("정답 선택:", data['options'], key=f"q{curr_idx}", disabled=st.session_state.submitted)
    
    st.write("---")

    if st.session_state.submitted:
        user_ans = st.session_state.answers[-1]
        if user_ans == data['ans']:
            st.success("🎉 **정답입니다!**")
        else:
            st.error(f"❌ **오답입니다!** \n\n 정답은: **{data['ans']}**")

    if not st.session_state.submitted:
        if st.button("제출"):
            st.session_state.answers.append(choice)
            if choice == data['ans']:
                st.session_state.score += 1
            st.session_state.submitted = True
            
            print(f">>> [ANSWER] 문제 {curr_idx + 1}: 유저 선택 [{choice}] / 결과: {'정답(O)' if choice == data['ans'] else '오답(X)'}")
            
            st.rerun()
    else:
        btn_label = "결과 확인하기" if curr_idx == 9 else "다음 문제로"
        if st.button(btn_label):
            if curr_idx == 9:
                print(f"\n>>> [FINAL RESULT] 플레이어: {st.session_state.player_name}")
                print(f">>> [FINAL RESULT] 최종 점수: {st.session_state.score} / 10")
                print(f">>> [SYSTEM] 퀴즈 종료 -------------------------------\n")
                st.session_state.page = 'result'
            else:
                st.session_state.current_index += 1
            st.session_state.submitted = False
            st.rerun()

# 결과 화면 
elif st.session_state.page == 'result':
    st.title("📊 결과")
    st.header(f"{st.session_state.score} / 10점")

    
    
    if st.session_state.score == 10:
        st.balloons()
        st.success(f"모든 문장을 맞히셨습니다. 🏆")

    c1, c2, c3 = st.columns(3)
    
    if c1.button("처음부터 다시 풀기"):
        # 같은 문제 세트로 다시 시작
        print(f">>> 같은 문제 세트로 다시 풀기")
        st.session_state.update({'current_index': 0, 'score': 0, 'answers': [], 'page': 'quiz', 'submitted': False})
        st.rerun()
    
    if c2.button("새로운 문제 풀기"):
        print(f">>> 새 문제 세트로 풀기")
        st.session_state.seed += 1 
        st.session_state.user_progress[st.session_state.player_name] = st.session_state.seed
        print(f">>> [SYSTEM] 현재 세션 시드: {st.session_state.seed}")
    
        st.session_state.update({
            'current_index': 0, 'score': 0, 'answers': [], 'submitted': False,
            'quiz_data': generate_quiz_set(st.session_state.player_name, st.session_state.seed),
            'page': 'quiz'
        })
        st.rerun()
        
    if c3.button("오답 모아보기"):
        if st.session_state.score == 10:
            st.info("✨ 오답이 없습니다.")
        else:
            st.subheader("📝 오답 노트")
            for i, (q_data, user_ans) in enumerate(zip(st.session_state.quiz_data, st.session_state.answers)):
                if q_data['ans'] != user_ans:
                    with st.expander(f"문제 {i+1} 오답 정보"):
                        st.write(f"**제시된 문구:** {q_data['q']}")
                        st.markdown(f"**내가 고른 답:** :red[{user_ans}]")
                        st.markdown(f"**정답:** :green[{q_data['ans']}]")
