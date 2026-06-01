import streamlit as st
import random
import time

# 1. 페이지 설정
st.set_page_config(
    page_title="당곡고 바카라 & 정직한 광산",
    page_icon="🃏",
    layout="centered"
)

# 2. 바카라 카드 정보 정의 (10, J, Q, K는 바카라 규칙상 0점)
SUITS = ['♠', '♥', '♦', '♣']
RANKS = [
    {'name': 'A', 'bacc_val': 1},
    {'name': '2', 'bacc_val': 2}, {'name': '3', 'bacc_val': 3}, {'name': '4', 'bacc_val': 4},
    {'name': '5', 'bacc_val': 5}, {'name': '6', 'bacc_val': 6}, {'name': '7', 'bacc_val': 7},
    {'name': '8', 'bacc_val': 8}, {'name': '9', 'bacc_val': 9},
    {'name': '10', 'bacc_val': 0}, {'name': 'J', 'bacc_val': 0}, {'name': 'Q', 'bacc_val': 0}, {'name': 'K', 'bacc_val': 0}
]

# 3. 덱 생성 및 셔플
def create_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append({
                "suit": suit,
                "name": rank['name'],
                "bacc_val": rank['bacc_val']
            })
    random.shuffle(deck)
    return deck

# 4. 세션 상태(Session State) 초기화
if 'balance' not in st.session_state:
    st.session_state.balance = 10000  # 시작 금액
if 'deck' not in st.session_state:
    st.session_state.deck = create_deck()
if 'cheated' not in st.session_state:
    st.session_state.cheated = False  # 치트 감지 여부
if 'click_violation_count' not in st.session_state:
    st.session_state.click_violation_count = 0  # 빠른 클릭 의심 누적 수
if 'last_click_time' not in st.session_state:
    st.session_state.last_click_time = 0.0
if 'game_history' not in st.session_state:
    st.session_state.game_history = []

# --- 바카라 규칙 연산 엔진 ---
# 바카라는 플레이어(Player)와 뱅커(Banker)의 카드 합 끝자리가 9에 가까운 쪽이 이기는 게임입니다.
def calculate_score(hand):
    return sum(card['bacc_val'] for card in hand) % 10

def play_baccarat(bet_type, bet_amount):
    # 덱이 부족하면 다시 채웁니다.
    if len(st.session_state.deck) < 10:
        st.session_state.deck = create_deck()

    deck = st.session_state.deck

    # 1단계: 각각 두 장씩 카드를 받습니다.
    p_hand = [deck.pop(), deck.pop()]
    b_hand = [deck.pop(), deck.pop()]

    p_score = calculate_score(p_hand)
    b_score = calculate_score(b_hand)

    p_third = None
    b_third = None

    # 내추럴(Natural) 규칙: 누군가 처음 2장의 합이 8 또는 9이면 즉시 게임 종료
    if p_score < 8 and b_score < 8:
        # 플레이어 추가 드로우 규칙: 합이 0~5일 때 한 장 더 받음
        if p_score <= 5:
            p_third = deck.pop()
            p_hand.append(p_third)
            p_score = calculate_score(p_hand)

        # 뱅커 추가 드로우 규칙 (플레이어가 3번째 카드를 받았는지 여부에 따라 다름)
        if p_third is None:
            # 플레이어가 스탠드한 경우 뱅커는 0~5일 때 한 장 더 받음
            if b_score <= 5:
                b_third = deck.pop()
                b_hand.append(b_third)
                b_score = calculate_score(b_hand)
        else:
            # 플레이어가 3번째 카드를 받은 경우 (바카라의 고유 공식 적용)
            p3_val = p_third['bacc_val']
            draw_banker = False
            
            if b_score <= 2:
                draw_banker = True
            elif b_score == 3 and p3_val != 8:
                draw_banker = True
            elif b_score == 4 and p3_val in [2, 3, 4, 5, 6, 7]:
                draw_banker = True
            elif b_score == 5 and p3_val in [4, 5, 6, 7]:
                draw_banker = True
            elif b_score == 6 and p3_val in [6, 7]:
                draw_banker = True

            if draw_banker:
                b_third = deck.pop()
                b_hand.append(b_third)
                b_score = calculate_score(b_hand)

    # 최종 결과 판정
    if p_score > b_score:
        winner = "PLAYER"
    elif b_score > p_score:
        winner = "BANKER"
    else:
        winner = "TIE"

    # 정산
    payout = 0
    win_status = False
    if bet_type == winner:
        win_status = True
        if bet_type == "PLAYER":
            payout = bet_amount * 2      # 1:1 지급 (원금 포함 2배)
        elif bet_type == "BANKER":
            payout = int(bet_amount * 1.95) # 5% 하우스 커미션 차감 (1.95배)
        elif bet_type == "TIE":
            payout = bet_amount * 9      # 타이 성공 시 8:1 지급 (원금 포함 9배)
        
        st.session_state.balance += (payout - bet_amount)
    else:
        st.session_state.balance -= bet_amount

    # 기록 누적
    st.session_state.game_history.insert(0, {
        "배팅": bet_type,
        "결과": f"PLAYER({p_score}) : BANKER({b_score}) ➔ {winner}",
        "변동": f"+{payout - bet_amount:,} G" if win_status else f"-{bet_amount:,} G"
    })

    return p_hand, b_hand, p_score, b_score, winner, win_status, payout

# --- 카드 비주얼화 헬퍼 함수 ---
def display_card_html(card):
    color = "#eb2f06" if card['suit'] in ['♥', '♦'] else "#1e272e"
    return f"""
    <div style="
        width: 80px; height: 120px; background: white; border: 1px solid #ccc;
        border-radius: 6px; display: inline-block; margin: 4px; padding: 5px;
        color: {color}; box-shadow: 1px 1px 5px rgba(0,0,0,0.1); text-align: left;
    ">
        <div style="font-size: 14px; font-weight: bold;">{card['name']}<br>{card['suit']}</div>
        <div style="font-size: 28px; text-align: center; margin-top: 5px;">{card['suit']}</div>
    </div>
    """

# --- 메인 화면 렌더링 ---

# 오토마우스 사기꾼 모드 활성화 시 분기 처리
if st.session_state.cheated:
    st.error("🚨 치트 의심 행위 영구 박탈 🚨")
    st.subheader("🤖 기계가 사람 행세를 하려 합니까?")
    st.markdown("""
    **"어디서 잔머리를 굴려서 쉽게 돈을 벌려고 해? 아주 뇌 빼고 딸깍질하다가 딱 걸렸죠?"**  
    당신은 신성한 노동의 전당인 당곡 광산에서 부정한 방법(오토마우스 등 비정상적 고속 클릭)을 사용했습니다.  
    
    정의사회 구현을 위해 **모든 자산은 국가와 학교 자치회로 국고 환수 및 압수** 조치 되었습니다. 💸 (잔액: **0 G**)  
    정정당당하고 정직한 근로자가 되기 전까지 당신에게 한 푼의 지원금도 지급되지 않습니다! 
    """)
    if st.button("진심으로 반성하고 정직하게 살겠습니다 (리셋)"):
        st.session_state.cheated = False
        st.session_state.balance = 10000
        st.session_state.click_violation_count = 0
        st.rerun()
    st.stop()

st.title("🃏 당곡 바카라 & 자금 구제 광산")
st.caption("컴퓨터 정보 교과 & 확률 통계 융합 프로젝트 실습")

# 잔고 대시보드
st.metric(label="💰 나의 현재 자금", value=f"{st.session_state.balance:,} G")
st.markdown("---")

# 파산 상태: 광산 기능 활성화
if st.session_state.balance <= 0:
    st.warning("💸 자금을 모두 잃고 파산하였습니다! 당곡 광산에서 수동 노동을 통해 자금을 마련하세요.")
    st.subheader("⛏️ 당곡 친환경 석탄 광산")
    st.info("※ 주의: 꼼수를 부리거나 기계 장치(오토마우스)를 사용할 경우, 광산 소장님이 극도로 분노하여 자산을 영원히 몰수할 수 있습니다.")
    
    # 클릭당 1원 벌기 버튼
    if st.button("⛏️ 곡괭이질 하기 (+1 G)", use_container_width=True):
        current_time = time.time()
        
        # 오토마우스 감지 로직 (클릭 간격 체크)
        if st.session_state.last_click_time > 0:
            interval = current_time - st.session_state.last_click_time
            # Streamlit 웹 구조상 물리적인 인간의 정상 클릭+웹 전송 갱신 시간은 대개 0.35초 이상입니다.
            # 0.22초 이하의 비정상적 주기로 연속 클릭 시 카운트를 누적시킵니다.
            if interval < 0.22:
                st.session_state.click_violation_count += 1
            else:
                # 정상 속도로 클릭하면 경고 수치 서서히 감소
                st.session_state.click_violation_count = max(0, st.session_state.click_violation_count - 1)
        
        st.session_state.last_click_time = current_time
        
        # 오토클릭 의심 한계 도달 (3회 이상 찰나의 순간 클릭이 탐지될 경우)
        if st.session_state.click_violation_count >= 3:
            st.session_state.cheated = True
            st.session_state.balance = 0
            st.rerun()
            
        st.session_state.balance += 1
        st.success("쾅! 석탄 1kg을 캐서 1 G를 얻었습니다! (정직한 노동의 가치)")
        st.rerun()

# 정상 상태: 바카라 게임 플레이 가능
else:
    st.subheader("🎲 배팅 구역")
    
    col_input1, col_input2 = st.columns([2, 1])
    with col_input1:
        bet_amount = st.number_input(
            "배팅금 설정 (최소 100 G)", 
            min_value=100, 
            max_value=st.session_state.balance, 
            value=min(1000, st.session_state.balance),
            step=100
        )
    with col_input2:
        st.write("") # 간격 조절용
        if st.button("올인 💥", use_container_width=True):
            bet_amount = st.session_state.balance
            
    st.write(f"현재 선택된 배팅액: **{bet_amount:,} G**")
    
    # 바카라는 세 개의 배팅 영역이 있습니다.
    col_p, col_b, col_t = st.columns(3)
    
    # 플레이어 배팅 버튼 (2.0배 지급)
    with col_p:
        if st.button("PLAYER 에 배팅 (2.0배)", use_container_width=True, type="primary"):
            p_hand, b_hand, p_score, b_score, winner, win_status, payout = play_baccarat("PLAYER", bet_amount)
            st.session_state.last_result = {
                "p_hand": p_hand, "b_hand": b_hand, 
                "p_score": p_score, "b_score": b_score, 
                "winner": winner, "win_status": win_status, "payout": payout
            }
            
    # 뱅커 배팅 버튼 (1.95배 지급 - 수수료 5% 포함)
    with col_b:
        if st.button("BANKER 에 배팅 (1.95배)", use_container_width=True, type="secondary"):
            p_hand, b_hand, p_score, b_score, winner, win_status, payout = play_baccarat("BANKER", bet_amount)
            st.session_state.last_result = {
                "p_hand": p_hand, "b_hand": b_hand, 
                "p_score": p_score, "b_score": b_score, 
                "winner": winner, "win_status": win_status, "payout": payout
            }
            
    # 타이 배팅 버튼 (9.0배 고배당)
    with col_t:
        if st.button("TIE (무승부) 에 배팅 (9.0배)", use_container_width=True):
            p_hand, b_hand, p_score, b_score, winner, win_status, payout = play_baccarat("TIE", bet_amount)
            st.session_state.last_result = {
                "p_hand": p_hand, "b_hand": b_hand, 
                "p_score": p_score, "b_score": b_score, 
                "winner": winner, "win_status": win_status, "payout": payout
            }

    # 결과 표기 영역
    if 'last_result' in st.session_state:
        res = st.session_state.last_result
        st.markdown("---")
        st.subheader("🔔 게임 결과 발표")
        
        col_res_p, col_res_b = st.columns(2)
        
        with col_res_p:
            st.markdown(f"### 🔵 PLAYER : {res['p_score']}점")
            p_cards_html = "".join(display_card_html(c) for c in res['p_hand'])
            st.markdown(p_cards_html, unsafe_allow_html=True)
            
        with col_res_b:
            st.markdown(f"### 🔴 BANKER : {res['b_score']}점")
            b_cards_html = "".join(display_card_html(c) for c in res['b_hand'])
            st.markdown(b_cards_html, unsafe_allow_html=True)
            
        st.write("")
        if res['win_status']:
            st.success(f"🎉 예측 성공! 승자는 **{res['winner']}** 입니다. **{res['payout']:,} G**를 돌려받았습니다!")
        else:
            st.error(f"😢 예측 실패... 승자는 **{res['winner']}** 입니다. 배팅금을 잃었습니다.")

# 최근 전적 기록 히스토리
if st.session_state.game_history:
    with st.expander("📝 최근 게임 장부 기록 보기"):
        st.table(st.session_state.game_history[:10]) # 최근 10개만 출력
