import streamlit as st
import random
import time

# 1. 페이지 기본 레이아웃 및 폰트 설정
st.set_page_config(
    page_title="당곡고 바카라 라이브 테이블",
    page_icon="🃏",
    layout="centered"
)

# 카드 등장 시 부드러운 스케일 및 페이드인 효과를 주기 위한 CSS 애니메이션 정의
st.markdown("""
<style>
@keyframes card-appear {
    0% { opacity: 0; transform: scale(0.6) translateY(20px) rotate(-5deg); }
    100% { opacity: 1; transform: scale(1) translateY(0) rotate(0deg); }
}
.card-animate {
    animation: card-appear 0.45s cubic-bezier(0.175, 0.885, 0.32, 1.2) forwards;
}
</style>
""", unsafe_allow_html=True)

# 2. 바카라 기본 상수 설정
SUITS = ['♠', '♥', '♦', '♣']
RANKS = [
    {'name': 'A', 'bacc_val': 1},
    {'name': '2', 'bacc_val': 2}, {'name': '3', 'bacc_val': 3}, {'name': '4', 'bacc_val': 4},
    {'name': '5', 'bacc_val': 5}, {'name': '6', 'bacc_val': 6}, {'name': '7', 'bacc_val': 7},
    {'name': '8', 'bacc_val': 8}, {'name': '9', 'bacc_val': 9},
    {'name': '10', 'bacc_val': 0}, {'name': 'J', 'bacc_val': 0}, {'name': 'Q', 'bacc_val': 0}, {'name': 'K', 'bacc_val': 0}
]

# 3. 덱 셔플 함수
def create_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append({"suit": suit, "name": rank['name'], "bacc_val": rank['bacc_val']})
    random.shuffle(deck)
    return deck

# 4. 세션 상태 관리 (상태 머신을 위한 변수 초기화)
if 'balance' not in st.session_state:
    st.session_state.balance = 10000
if 'deck' not in st.session_state:
    st.session_state.deck = create_deck()
if 'cheated' not in st.session_state:
    st.session_state.cheated = False
if 'click_violation_count' not in st.session_state:
    st.session_state.click_violation_count = 0
if 'last_click_time' not in st.session_state:
    st.session_state.last_click_time = 0.0
if 'game_history' not in st.session_state:
    st.session_state.game_history = []
if 'bead_plate' not in st.session_state:
    st.session_state.bead_plate = []  # 전광판용 이모지 리스트
if 'game_stage' not in st.session_state:
    st.session_state.game_stage = "betting"  # betting -> dealing -> result 순환
if 'bet_type' not in st.session_state:
    st.session_state.bet_type = "SPECTATOR"
if 'bet_amount' not in st.session_state:
    st.session_state.bet_amount = 0
if 'last_result_data' not in st.session_state:
    st.session_state.last_result_data = None
if 'bet_preset' not in st.session_state:
    st.session_state.bet_preset = 1000

# 바카라 점수 계산 (합산의 1의 자리)
def calculate_score(hand):
    return sum(card['bacc_val'] for card in hand) % 10

# 개별 카드 카드 HTML 렌더링 함수
def display_card_html(card):
    color = "#eb2f06" if card['suit'] in ['♥', '♦'] else "#1e272e"
    return f"""
    <div class="card-animate" style="
        width: 85px; height: 125px; background: white; border: 1px solid #ccc;
        border-radius: 8px; display: inline-block; margin: 4px; padding: 6px;
        color: {color}; box-shadow: 2px 2px 8px rgba(0,0,0,0.15); text-align: left;
    ">
        <div style="font-size: 15px; font-weight: bold; line-height: 1.1;">{card['name']}<br>{card['suit']}</div>
        <div style="font-size: 32px; text-align: center; margin-top: 5px;">{card['suit']}</div>
    </div>
    """

# 라이브 딜링 테이블 레이아웃 구현 (HTML/CSS)
def render_live_table(p_hand, b_hand, p_score, b_score, status_text=""):
    p_cards_html = "".join(display_card_html(c) for c in p_hand) if p_hand else "⏳ 딜링 대기 중"
    b_cards_html = "".join(display_card_html(c) for c in b_hand) if b_hand else "⏳ 딜링 대기 중"
    
    return f"""
    <div style="
        background-color: #0b3d2e; padding: 25px; border-radius: 18px; 
        border: 4px solid #d4af37; text-align: center; color: white; margin-bottom: 25px;
        box-shadow: inset 0px 0px 20px rgba(0,0,0,0.6);
    ">
        <div style="font-size: 14px; color: #d4af37; font-weight: bold; letter-spacing: 2px; margin-bottom: 15px;">
            ♠♥ DANGGOK LIVE TABLE ♦♣
        </div>
        <div style="display: flex; justify-content: space-around; align-items: flex-start; gap: 15px;">
            <!-- 플레이어 진영 -->
            <div style="flex: 1; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 12px; border: 1px dashed rgba(255,255,255,0.2);">
                <div style="font-size: 18px; color: #90caf9; font-weight: bold; margin-bottom: 8px;">PLAYER</div>
                <div style="font-size: 24px; font-weight: bold; color: #90caf9; margin-bottom: 10px;">{p_score if p_hand else '-'} 점</div>
                <div style="min-height: 140px; display: flex; justify-content: center; align-items: center; gap: 5px;">
                    {p_cards_html}
                </div>
            </div>
            <!-- 뱅커 진영 -->
            <div style="flex: 1; background: rgba(0,0,0,0.3); padding: 12px; border-radius: 12px; border: 1px dashed rgba(255,255,255,0.2);">
                <div style="font-size: 18px; color: #ef9a9a; font-weight: bold; margin-bottom: 8px;">BANKER</div>
                <div style="font-size: 24px; font-weight: bold; color: #ef9a9a; margin-bottom: 10px;">{b_score if b_hand else '-'} 점</div>
                <div style="min-height: 140px; display: flex; justify-content: center; align-items: center; gap: 5px;">
                    {b_cards_html}
                </div>
            </div>
        </div>
        <div style="margin-top: 20px; font-size: 18px; font-weight: bold; color: #fff; background: rgba(0,0,0,0.4); padding: 10px; border-radius: 8px;">
            📢 {status_text}
        </div>
    </div>
    """

# --- 상태 업데이트 콜백 함수 정의 ---
def make_bet(bet_type, amount):
    if amount > st.session_state.balance:
        amount = st.session_state.balance
    st.session_state.bet_type = bet_type
    st.session_state.bet_amount = amount
    st.session_state.game_stage = "dealing"

def set_preset(val):
    st.session_state.bet_preset = val

def trigger_next_round():
    st.session_state.game_stage = "betting"

# ==========================================
# 5. UI 시스템 분기 실행
# ==========================================

# [A] 오토마우스 사기 행위 적발 차단 화면
if st.session_state.cheated:
    st.error("🚨 치트(오토마우스) 행위 전면 적발! 영구 박탈 🚨")
    st.subheader("🤖 어허, 어디서 기계가 정직한 광산에 침입합니까?")
    st.markdown("""
    **"손은 눈보다 빠르다고 생각하셨습니까? 아니면 '딸깍 딸깍' 대충 기계 돌려서 날로 먹으려 하셨나요?"**  
    
    당곡 광산 소장님이 귀하의 비정상적 고속 연타(오토마우스)를 귀신같이 잡아냈습니다! 😤  
    
    **🚨 패널티 발생:**
    - 귀하의 모든 게임 자산은 **국고 환수 및 당곡 광산 소장님의 비상금**으로 강제 압수되었습니다. (잔액: **0 G**)
    - 정직하게 마우스를 한 땀 한 땀 누르는 정의로운 근로 시민이 되기 전까지 한 푼의 구제금도 지급되지 않습니다!  
    
    *교훈: 과도한 편법과 기계적 남용은 인생을 한순간에 파멸로 이끕니다. (확률과 통계 & 정보 윤리 연계 주제)*
    """)
    if st.button("진심으로 반성하고 정직한 손가락으로 살겠습니다 (게임 리셋)"):
        st.session_state.cheated = False
        st.session_state.balance = 10000
        st.session_state.click_violation_count = 0
        st.session_state.bead_plate = []
        st.session_state.game_history = []
        st.session_state.game_stage = "betting"
        st.rerun()
    st.stop()

# 타이틀 및 대시보드
st.title("🃏 당곡 바카라 무한 라이브 테이블")
st.caption("컴퓨터 정보 교과 & 확률과 통계 융합 프로젝트 실습")

st.metric(label="💰 나의 현재 자금", value=f"{st.session_state.balance:,} G")
st.markdown("---")

# [B] 파산 구제 광산 모드
if st.session_state.balance <= 0:
    st.warning("💸 자금을 모두 잃고 파산하였습니다! 당곡 광산에서 수동 노동을 통해 자금을 마련하세요.")
    st.subheader("⛏️ 당곡 친환경 석탄 광산")
    st.info("⚠️ 주의: 오토클릭 등 비정상적 고속 딸깍질 탐지 시 광산 소장이 극대노하여 평생 광산에 가둘 수 있습니다.")
    
    if st.button("⛏️ 곡괭이질 하기 (+1 G)", use_container_width=True):
        current_time = time.time()
        
        # 클릭 델타 타임 연산 및 오토 감지
        if st.session_state.last_click_time > 0:
            interval = current_time - st.session_state.last_click_time
            if interval < 0.22: # 0.22초 이하 연속 클릭 탐지
                st.session_state.click_violation_count += 1
            else:
                st.session_state.click_violation_count = max(0, st.session_state.click_violation_count - 1)
                
        st.session_state.last_click_time = current_time
        
        if st.session_state.click_violation_count >= 3:
            st.session_state.cheated = True
            st.session_state.balance = 0
            st.rerun()
            
        st.session_state.balance += 1
        st.success("쾅! 석탄을 캐서 1 G를 정직하게 획득했습니다!")
        st.rerun()

# [C] 바카라 라이브 게임 테이블 진행
else:
    # ------------------------------------
    # Stage 1: 배팅 구역 (배팅 대기)
    # ------------------------------------
    if st.session_state.game_stage == "betting":
        st.subheader("🎲 배팅 구역")
        
        # 배팅 자금 조절 슬라이더 및 프리셋
        col_bet1, col_bet2 = st.columns([2, 1])
        with col_bet1:
            bet_amount = st.number_input(
                "배팅금 설정 (최소 100 G)", 
                min_value=100, 
                max_value=st.session_state.balance, 
                value=min(st.session_state.bet_preset, st.session_state.balance),
                step=100
            )
            st.session_state.bet_preset = bet_amount
        with col_bet2:
            st.write("") # 간격 조절
            st.button("올인 💥", use_container_width=True, on_click=set_preset, args=(st.session_state.balance,))

        # 배팅 선택지 버튼
        col_p, col_b, col_t = st.columns(3)
        with col_p:
            st.button("PLAYER 에 배팅 (2.00배)", use_container_width=True, type="primary", on_click=make_bet, args=("PLAYER", bet_amount))
        with col_b:
            st.button("BANKER 에 배팅 (1.95배)", use_container_width=True, type="secondary", on_click=make_bet, args=("BANKER", bet_amount))
        with col_t:
            st.button("TIE 에 배팅 (9.00배)", use_container_width=True, on_click=make_bet, args=("TIE", bet_amount))

        st.write("")
        
        # ⏱️ 실시간 오토플레이 타이머 가동 (유저 미입력 시 강제 자동 관전 진행)
        countdown_placeholder = st.empty()
        for remaining in range(7, 0, -1):
            countdown_placeholder.markdown(f"⏱️ **배팅 남은 시간: {remaining}초** (아무 버튼도 누르지 않으면 자동으로 이번 라운드가 시작됩니다!)")
            time.sleep(1)
            
        # 루프를 끝까지 생존했다면 사용자가 아무 행동도 안 한 것 ➔ 자동으로 SPECTATOR 모드 딜링 시작
        st.session_state.bet_type = "SPECTATOR"
        st.session_state.bet_amount = 0
        st.session_state.game_stage = "dealing"
        st.rerun()

    # ------------------------------------
    # Stage 2: 딜링 애니메이션 구역 (역동적 딜링)
    # ------------------------------------
    elif st.session_state.game_stage == "dealing":
        st.subheader("🎲 딜러가 카드를 셔플하고 분배 중입니다...")
        
        table_placeholder = st.empty()
        
        if len(st.session_state.deck) < 10:
            st.session_state.deck = create_deck()
            
        deck = st.session_state.deck
        p_hand = []
        b_hand = []
        
        # 1. 플레이어 첫 번째 카드
        p_hand.append(deck.pop())
        table_placeholder.markdown(render_live_table(p_hand, b_hand, calculate_score(p_hand), 0, "🔵 플레이어 첫 번째 카드 오픈 중..."), unsafe_allow_html=True)
        time.sleep(0.7)
        
        # 2. 뱅커 첫 번째 카드
        b_hand.append(deck.pop())
        table_placeholder.markdown(render_live_table(p_hand, b_hand, calculate_score(p_hand), calculate_score(b_hand), "🔴 뱅커 첫 번째 카드 오픈 중..."), unsafe_allow_html=True)
        time.sleep(0.7)
        
        # 3. 플레이어 두 번째 카드
        p_hand.append(deck.pop())
        table_placeholder.markdown(render_live_table(p_hand, b_hand, calculate_score(p_hand), calculate_score(b_hand), "🔵 플레이어 두 번째 카드 오픈 중..."), unsafe_allow_html=True)
        time.sleep(0.7)
        
        # 4. 뱅커 두 번째 카드
        b_hand.append(deck.pop())
        table_placeholder.markdown(render_live_table(p_hand, b_hand, calculate_score(p_hand), calculate_score(b_hand), "🔴 뱅커 두 번째 카드 오픈 중..."), unsafe_allow_html=True)
        time.sleep(0.7)
        
        p_score = calculate_score(p_hand)
        b_score = calculate_score(b_hand)
        
        p_third = None
        
        # 내추럴 규칙 판정
        if p_score >= 8 or b_score >= 8:
            table_placeholder.markdown(render_live_table(p_hand, b_hand, p_score, b_score, "💥 내추럴(Natural) 발생! 즉시 승패를 결정합니다."), unsafe_allow_html=True)
            time.sleep(1.0)
        else:
            # 플레이어 3번째 카드 수령 조건
            if p_score <= 5:
                p_third = deck.pop()
                p_hand.append(p_third)
                p_score = calculate_score(p_hand)
                table_placeholder.markdown(render_live_table(p_hand, b_hand, p_score, b_score, "🔵 플레이어 규칙에 따른 추가 카드 수령 완료."), unsafe_allow_html=True)
                time.sleep(1.0)
                
            # 뱅커 3번째 카드 수령 조건 (바카라 규칙 룰테이블 연산)
            draw_banker = False
            if p_third is None:
                if b_score <= 5:
                    draw_banker = True
            else:
                p3_val = p_third['bacc_val']
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
                b_hand.append(deck.pop())
                b_score = calculate_score(b_hand)
                table_placeholder.markdown(render_live_table(p_hand, b_hand, p_score, b_score, "🔴 뱅커 규칙에 따른 추가 카드 수령 완료."), unsafe_allow_html=True)
                time.sleep(1.0)
                
        # 최종 승부 결과 판정
        if p_score > b_score:
            winner = "PLAYER"
            emoji = "🔵"
            status_text = "🏆 플레이어(PLAYER)의 승리입니다!"
        elif b_score > p_score:
            winner = "BANKER"
            emoji = "🔴"
            status_text = "🏆 뱅커(BANKER)의 승리입니다!"
        else:
            winner = "TIE"
            emoji = "🟢"
            status_text = "🤝 타이(TIE) 무승부입니다!"
            
        table_placeholder.markdown(render_live_table(p_hand, b_hand, p_score, b_score, status_text), unsafe_allow_html=True)
        time.sleep(1.2)
        
        # 6. 배팅 정산 및 결과 전이 로직
        bet_type = st.session_state.bet_type
        bet_amount = st.session_state.bet_amount
        payout = 0
        win_status = False
        
        if bet_type != "SPECTATOR":
            if bet_type == winner:
                win_status = True
                if bet_type == "PLAYER":
                    payout = bet_amount * 2
                elif bet_type == "BANKER":
                    payout = int(bet_amount * 1.95)
                elif bet_type == "TIE":
                    payout = bet_amount * 9
                st.session_state.balance += (payout - bet_amount)
            else:
                st.session_state.balance -= bet_amount
                
        # 실시간 히스토리 누적
        st.session_state.bead_plate.append(emoji)
        profit_text = "관전 모드 (변동 없음)" if bet_type == "SPECTATOR" else (f"+{(payout - bet_amount):,} G" if win_status else f"-{bet_amount:,} G")
        
        st.session_state.game_history.insert(0, {
            "라운드": len(st.session_state.bead_plate),
            "배팅": bet_type,
            "상세 점수": f"P({p_score}) : B({b_score})",
            "결과": f"{emoji} {winner}",
            "손익": profit_text
        })
        
        # 결과 요약 임시 저장
        st.session_state.last_result_data = {
            "p_score": p_score, "b_score": b_score, "winner": winner, "emoji": emoji,
            "win_status": win_status, "payout": payout, "bet_type": bet_type, "bet_amount": bet_amount
        }
        
        st.session_state.game_stage = "result"
        st.rerun()

    # ------------------------------------
    # Stage 3: 결과 화면 및 다음 자동 라운드 준비
    # ------------------------------------
    elif st.session_state.game_stage == "result":
        res = st.session_state.last_result_data
        
        if res:
            st.subheader("🔔 매치 정산서")
            if res["bet_type"] == "SPECTATOR":
                st.info(f"📢 이번 라운드는 **관전 모드**였습니다. 결과: {res['emoji']} {res['winner']} 승리!")
            else:
                if res["win_status"]:
                    st.success(f"🎉 예측 성공! 승자는 **{res['emoji']} {res['winner']}** 입니다. **+{res['payout'] - res['bet_amount']:,} G** 수익!")
                else:
                    st.error(f"😢 예측 실패... 승자는 **{res['emoji']} {res['winner']}** 입니다. **-{res['bet_amount']:,} G** 손실...")

        # 수동 스킵 버튼
        st.button("즉시 다음 라운드 진행 ➔", use_container_width=True, type="primary", on_click=trigger_next_round)
        
        # 다음 판 자동 갱신 타이머
        countdown_result = st.empty()
        for remaining in range(4, 0, -1):
            countdown_result.markdown(f"⏱️ **{remaining}초 후 다음 배팅 라운드가 자동으로 진행됩니다...**")
            time.sleep(1)
            
        st.session_state.game_stage = "betting"
        st.rerun()

# ==========================================
# 6. 전광판 및 전체 매치 기록 (누적)
# ==========================================
st.markdown("---")

if st.session_state.bead_plate:
    st.subheader("📊 실시간 바카라 전광판 (Bead Plate)")
    bead_html = "".join([f"<span style='font-size: 22px; margin: 2px;'>{emoji}</span>" for emoji in st.session_state.bead_plate])
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 12px; border-left: 6px solid #2f3542; line-height: 2.2; max-height: 150px; overflow-y: auto;">
        {bead_html}
    </div>
    """, unsafe_allow_html=True)

if st.session_state.game_history:
    st.subheader("📝 전체 게임 장부 (All History)")
    st.dataframe(st.session_state.game_history, use_container_width=True)

# 초기화 버튼
if st.button("🔄 전체 전적 및 자금 초기화"):
    st.session_state.balance = 10000
    st.session_state.bead_plate = []
    st.session_state.game_history = []
    st.session_state.game_stage = "betting"
    st.rerun()
