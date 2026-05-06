import streamlit as st
import pandas as pd
import time
import os
import random
import streamlit as st
import time
from streamlit_gsheets import GSheetsConnection

# --- 1. 基础配置 ---
st.set_page_config(page_title="工作记忆实验", layout="centered")

# 使用 CSS 模拟 PsychoPy 黑色背景和居中布局
st.markdown("""
    <style>
    /* 全局背景设为浅灰色 */
    .main { 
        background-color: #F5F5F5; 
        color: #000000; 
    }
    /* 所有文字、标签、Markdown 统一设为黑色 */
    .stMarkdown, p, label, .stSelectbox, .stRadio { 
        color: #000000 !important; 
        font-family: 'Microsoft YaHei';
        font-weight: 500;
    }
    /* 标题加粗加黑 */
    h1, h2, h3, h4 { 
        color: #000000 !important; 
        font-weight: bold !important;
    }
    /* 按钮样式：蓝色背景，白色文字，增强点击感 */
    div.stButton > button { 
        width: 100%; 
        height: 3.5em; 
        font-size: 18px; 
        background-color: #007BFF; 
        color: white !important; 
        border: none;
        border-radius: 8px;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
    }
    div.stButton > button:hover { 
        background-color: #0056b3; 
        color: white !important;
    }
    /* 单选框间距优化 */
    .stRadio div[role='radiogroup'] {
        padding: 10px;
        background-color: #FFFFFF;
        border-radius: 10px;
        border: 1px solid #DDD;
    }
    </style>
    """, unsafe_allow_html=True)

def next_stage():
    st.session_state.stage_idx += 1
    st.session_state.trial_status = "READY"
    st.session_state.cdt_trial = 1
    st.session_state.correct_count = 0
    st.rerun()

# 阶段序列
STAGES = [
    "WELCOME", "INFO", "RRS", "BDI", "STAI", "T1_VAS_BSRI", 
    "PRACTICE_INTRO", "CDT_PRACTICE", 
    "VIDEO_INDUCTION", "WRITING", "RUMINATION", "T2_VAS_BSRI", 
    "FORMAL_INTRO", "CDT_FORMAL", 
    "RECOVERY", "FINISH"
]
current_stage = STAGES[st.session_state.stage_idx]

# --- 2. 任务辅助逻辑 ---
def countdown(seconds, msg):
    p = st.empty()
    for i in range(seconds, -1, -1):
        p.markdown(f"<h2 style='color:red;'>⏳ {msg}: {i} 秒</h2>", unsafe_allow_html=True)
        time.sleep(1)
    p.empty()

# --- 2. 实验常量与量表题库 ---
RRS_ITEMS = ["我究竟做了什么要遭如此报应", "分析新近发生的事情试图找到原因", "想到“我为什么总是有这种反应”", "一个人走开，思考自己为什么会有这种感觉", "记录你自己的想法并做分析", "回想新近的情境，希望情形已经好转", "想到“为什么我有这样问题而别人没有。”", "想到“我为什么不能把事情做得更好一点﹖”", "分析自己的性格试图找到沮丧的原因", "独自去某个地方考虑自己的感受"]
BDI_ITEMS = ["悲伤程度", "对未来失望感", "失败感", "负罪感", "惩罚感", "自厌感", "自我谴责", "自杀意念", "哭泣次数", "易激惹", "社交退缩", "犹豫不决", "自我形象改变", "工作困难", "睡眠障碍", "易疲劳", "食欲减退", "体重减轻", "躯体关注", "性欲减退"]
STAI_ITEMS = ["我感到愉快。", "我感到神经过敏和不安。", "我感到自我满足。", "我希望能像别人那样高兴。", "我感到像一个失败者。", "我感到很宁静。", "我是“平静、冷静和镇定自若”的。", "我感到困难成堆，无法克服。", "我过分忧虑一些事，实际这些事无关紧要。", "我是高兴的。"]
BSRI_ITEMS = ["1. 此刻，我在反复思考自己的负面情绪。", "2. 此刻，我想知道我为什么会反复思虑自己的负面情绪。", "3. 此刻，我想知道我为什么总是感受到自己反复思虑负面情绪。", "4. 此刻，我在想:”为什么我有很多的问题而其他人没有?“", "5. 此刻，我正在脑海里反复回想，最近我说过或做过的事情。", "6. 此刻，我在想:“为什么我不能更好地处理事情?“", "7. 此刻，我很难摆脱自己的负面想法。", "8. 此刻，我正在想:“面对负面情绪为什么我除了反复思虑它，不能以更好的方式反应”。"]

# --- 3. 核心功能函数 ---
def next_stage():
    st.session_state.stage_idx += 1
    st.rerun()

def play_beep():
    if os.path.exists("beep.wav"):
        st.audio("beep.wav", autoplay=True)

def countdown_timer(seconds, message):
    placeholder = st.empty()
    for i in range(seconds, -1, -1):
        placeholder.markdown(f"<h2 style='color: #FF4B4B;'>⏳ {message}: {i} 秒</h2>", unsafe_allow_html=True)
        time.sleep(1)
    placeholder.empty()

# --- 4. 实验流程控制 ---

# 1. 欢迎页
if current_stage == "WELCOME":
    st.markdown("# 欢迎参加本次心理学测试")
    st.markdown("### 【温馨提示】")
    st.write("1. 实验过程中请保持专注，不要中途离开。")
    st.write("2. 请在安静的环境下完成。")
    st.write("3. 实验涉及音频，请调节好音量并佩戴耳机。")
    if st.button("我已准备好，点击进入"): next_stage()

# 2. 信息采集
elif current_stage == "INFO":
    st.markdown("## 实验信息录入")
    with st.form("info"):
        sid = st.text_input("被试编号", "A01")
        sex = st.selectbox("性别", ["男", "女"])
        age = st.number_input("年龄", 1, 100, 20)
        st.write("（所写内容均保密不会泄露）")
        if st.form_submit_button("确认"):
            st.session_state.results.update({"ID": sid, "Sex": sex, "Age": age})
            next_stage()

# 3-5. 基础问卷 (RRS, BDI, STAI)
elif current_stage == "RRS":
    st.markdown("## 【特质反刍问卷】")
    st.markdown("**打分标准：1=从不，2=有时，3=经常，4=总是**")
    rrs_res = []
    for i, q in enumerate(RRS_ITEMS):
        r = st.radio(f"{i+1}. {q}", [1, 2, 3, 4], horizontal=True, key=f"rrs_{i}")
        rrs_res.append(r)
    if st.button("提交 RRS 问卷"):
        st.session_state.results["RRS_Sum"] = sum(rrs_res)
        next_stage()

elif current_stage == "BDI":
    st.markdown("## 【BDI-II 抑郁量表】")
    st.markdown("**打分标准：请根据描述选择：0=无/很少，1=轻度，2=中度，3=严重**")
    bdi_res = []
    for i, q in enumerate(BDI_ITEMS):
        r = st.radio(f"{i+1}. {q}", [0, 1, 2, 3], horizontal=True, key=f"bdi_{i}")
        bdi_res.append(r)
    if st.button("提交 BDI 问卷"):
        st.session_state.results["BDI_Sum"] = sum(bdi_res)
        next_stage()

elif current_stage == "STAI":
    st.markdown("## 【STAI-T 特质焦虑问卷】")
    st.markdown("**打分标准：1=几乎没有，2=有些，3=经常，4=几乎总是**")
    stai_res = []
    for i, q in enumerate(STAI_ITEMS):
        r = st.radio(f"{i+1}. {q}", [1, 2, 3, 4], horizontal=True, key=f"stai_{i}")
        stai_res.append(r)
    if st.button("提交 STAI 问卷"):
        st.session_state.results["STAI_Sum"] = sum(stai_res)
        next_stage()


# 6 & 13. VAS 与 BSRI
elif current_stage == "T1_VAS_COMBINED":
    st.markdown("## 状态评估 (T1)")
    
    # 唤醒度部分
    st.markdown("### 1. 请评估你此刻的【生理与心理唤醒度】")
    st.write("(如：心跳加速、警觉、紧张感)")
    st.info("【打分参考】\n\n0 - 30：感到平静、放松、没有波澜\n\n40 - 60：中等程度的激活，感到轻微的紧张或气愤\n\n70 - 100：非常强烈的紧张、气愤或激动")
    t1_aro = st.select_slider("滑动滑块评估唤醒度", options=list(range(101)), value=50, key="t1_aro_val")
    
    st.markdown("---")
    
    # 效价部分
    st.markdown("### 2. 请评估你此刻的【情绪效价】")
    st.info("【打分参考】\n\n0 - 30：感到偏向负面、郁郁、痛苦\n\n40 - 60：情绪中立，没有明显的好坏\n\n70 - 100：感到偏向正面、开心、愉悦")
    t1_val = st.select_slider("滑动滑块评估效价", options=list(range(101)), value=50, key="t1_val_val")
    
    if st.button("确认提交以上评估"):
        st.session_state.results["T1_Arousal"] = t1_aro
        st.session_state.results["T1_Valence"] = t1_val
        next_stage()
# --- 6. T1 BSRI 评估 (独立界面) ---
elif current_stage == "T1_BSRI_INDEPENDENT":
    st.markdown("## 状态评估 (BSRI)")
    st.write("请根据此刻的真实感受，对以下描述进行打分（1=完全不符合，7=完全符合）：")
    bsri_res = []
    for i, q in enumerate(BSRI_QUESTIONS):
        r = st.radio(q, [1, 2, 3, 4, 5, 6, 7], horizontal=True, key=f"t1_bsri_{i}")
        bsri_res.append(r)
    if st.button("确认提交 BSRI"):
        st.session_state.results["T1_BSRI_Sum"] = sum(bsri_res)
        next_stage()


# 7. CDT 任务指导语 (还原文档)
elif current_stage == "PRACTICE_INTRO":
    st.markdown("## 下面进入【练习阶段】")
    st.markdown("""
    接下来的练习旨在帮您熟悉任务流程：
    1. 屏幕中央会出现一个红色的“+”字，请盯住它。
    2. 随后，屏幕会闪现【4张面孔】，请努力记住它们的脸部特征。
    3. 接着屏幕会短暂空白。
    4. 最后，屏幕中央会出现【1张面孔】。

    **请判断：**
    最后出现的这张脸，是否在刚才那组（4张脸）中出现过？
    - 如果是（**一样/出现过**），请点击屏幕上的 **【F】** 按钮；
    - 如果不是（**全新/没出现过**），请点击屏幕上的 **【J】** 按钮。

    *正确率未达 60% 会持续练习。*
    **【温馨提示】：请确保您的输入法处于【英文】状态。**
    """)
    if st.button("准备好后，点击开始练习"): next_stage()
# 5. CDT 练习逻辑 (5组，60%要求)
elif current_stage == "CDT_PRACTICE":
    total = 5
    st.markdown(f"### 练习阶段 ({st.session_state.cdt_trial}/{total})")
    placeholder = st.empty()

    if st.session_state.trial_status == "READY":
        if st.button(f"开始第 {st.session_state.cdt_trial} 组练习"):
            st.session_state.trial_status = "PLAYING"; st.rerun()

    elif st.session_state.trial_status == "PLAYING":
        with placeholder.container():
            st.markdown("<h1 style='color:red;'>+</h1>", unsafe_allow_html=True); time.sleep(1.0)
            # 模拟显示4张图
            st.write("【 4张面孔 记忆中... 】"); time.sleep(1.8)
            st.write("【 噪音掩码 】"); time.sleep(0.6)
            st.session_state.ans_correct = random.choice([True, False]) # 模拟答案
            st.session_state.trial_status = "WAITING"; st.rerun()

    elif st.session_state.trial_status == "WAITING":
        st.markdown("#### 判断：这张脸出现过吗？")
        c1, c2 = st.columns(2)
        if c1.button("F (出现过)"):
            if st.session_state.ans_correct: st.session_state.correct_count += 1
            st.session_state.trial_status = "READY"
            if st.session_state.cdt_trial < total: st.session_state.cdt_trial += 1
            else:
                acc = st.session_state.correct_count / total
                if acc < 0.6: 
                    st.error(f"正确率 {acc*100}% 未达标，重新练习"); time.sleep(2)
                    st.session_state.cdt_trial = 1; st.session_state.correct_count = 0
                else: next_stage()
            st.rerun()
        if c2.button("J (没出现)"):
            if not st.session_state.ans_correct: st.session_state.correct_count += 1
            st.session_state.trial_status = "READY"
            if st.session_state.cdt_trial < total: st.session_state.cdt_trial += 1
            else:
                acc = st.session_state.correct_count / total
                if acc < 0.6: 
                    st.error(f"正确率 {acc*100}% 未达标，重新练习"); time.sleep(2)
                    st.session_state.cdt_trial = 1; st.session_state.correct_count = 0
                else: next_stage()
            st.rerun()

# 10. 诱发视频播放
elif current_stage == "VIDEO_INDUCTION":
    st.markdown("### 接下来，您将观看一段电影片段。")
    st.markdown("请佩戴好耳机，保持安静，全程不要转移视线。")
    st.markdown("请尽量让自己【完全沉浸】在画面的情境与情绪中。")
    if os.path.exists("Shenpan.mp4"): st.video("Shenpan.mp4")
    if st.button("播放完毕"): next_stage()

# 11. 书写阶段 (180s 倒计时)
elif current_stage == "WRITING":
    st.markdown("### 正如刚才视频中那种颠倒黑白、令人窒息的不公与气愤。")
    st.markdown("请在下方输入框写下你人生中经历过的，最让你感到**【被严重误解、不公平对待、极度挫败却又无能为力】**的一个事件。")
    txt = st.text_area("书写框（倒计时结束后自动继续）...", height=300)
    countdown_timer(180, "书写剩余时间")
    play_beep()
    if st.button("点击进入下一阶段"):
        st.session_state.results["Writing"] = txt
        next_stage()

# 12. 引导反刍 (45s x 4)
elif current_stage == "RUMINATION":
    prompts = [
        "想一想，为什么这种不公平和倒霉的事情，偏偏会发生在你身上？"
        "想一想，当时的你，为什么没有能力去为自己辩解或反抗？",
        "想一想，这件事的发生，是不是暴露出了你骨子里的弱点？",
        "想一想，这件事对你现在的状态，究竟造成了多大无法挽回的负面影响？"
    ]
    if 'rum_idx' not in st.session_state: st.session_state.rum_idx = 0
    st.markdown(f"## 深度思考 ({st.session_state.rum_idx+1}/3)")
    st.markdown(f"### {prompts[st.session_state.rum_idx]}")
    countdown_timer(45, "思考剩余时间")
    play_beep()
    if st.button("进入下一个思考点"):
        if st.session_state.rum_idx < len(prompts)-1:
            st.session_state.rum_idx += 1
            st.rerun()
        else:
            next_stage()

# 9. T2 评估
elif current_stage == "T2_VAS_BSRI":
    st.header("状态评估 (后测)")
    st.slider("唤醒度", 0, 100, 50); st.slider("效价", 0, 100, 50)
    if st.button("提交评估"): next_stage()

# 10. 正式阶段 CDT 指导语 (全面还原)
elif current_stage == "FORMAL_INTRO":
    st.markdown("## 下面进行【正式实验任务】")
    st.markdown("""
    正式任务的要求与刚才练习阶段 **【完全一致】**。
    唯一的区别是：
    1. 正式任务包含 **20 组**。
    2. 每次做出 F 或 J 判断后，请点击下方滑块评估您对刚才判断的 **【信心程度】**。
    
    1 代表完全猜测，5 代表非常有信心。
    
    准备好后，点击下方按钮开始正式任务。
    """)
    if st.button("开始正式任务"): next_stage()

# 11. 正式 CDT 逻辑 (20组 + 信心评分)
elif current_stage == "CDT_FORMAL":
    total = 20
    st.markdown(f"### 正式阶段 ({st.session_state.cdt_trial}/{total})")
    placeholder = st.empty()

    if st.session_state.trial_status == "READY":
        if st.button(f"开始第 {st.session_state.cdt_trial} 组正式测试"):
            st.session_state.trial_status = "PLAYING"; st.rerun()

    elif st.session_state.trial_status == "PLAYING":
        with placeholder.container():
            st.markdown("<h1 style='color:red;'>+</h1>", unsafe_allow_html=True); time.sleep(1.0)
            st.write("【 4张面孔 记忆中... 】"); time.sleep(1.8)
            st.write("【 噪音掩码 】"); time.sleep(0.6)
            st.session_state.trial_status = "WAITING"; st.rerun()

    elif st.session_state.trial_status == "WAITING":
        st.markdown("#### 判断：这张脸出现过吗？")
        c1, c2 = st.columns(2)
        resp = None
        if c1.button("F (出现过)"): resp = "F"
        if c2.button("J (没出现)"): resp = "J"
        
        if resp:
            conf = st.select_slider("信心评价", options=[1,2,3,4,5], value=3)
            if st.button("确认提交本组结果"):
                st.session_state.cdt_data.append({"Trial": st.session_state.cdt_trial, "Resp": resp, "Conf": conf})
                st.session_state.trial_status = "READY"
                if st.session_state.cdt_trial < total: st.session_state.cdt_trial += 1
                else: next_stage()
                st.rerun()

# 阶段 12:恢复阶段
elif current_stage == "RECOVERY":
    st.markdown("## 实验任务已全部完成")
    st.markdown("### 接下来请观看一段轻松的视频以平复心情。")
    if os.path.exists("cat_video.mp4"):
        st.video("cat_video.mp4")
    else:
        st.warning("恢复视频 (cat_video.mp4) 缺失。")
    if st.button("观看完毕，进入最后结算"): next_stage()

# 阶段 13:在实验结束阶段 (FINISH)
elif current_stage == "FINISH":
    st.title("实验完成")
    
    # 1. 连接到 Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 2. 读取现有数据（为了追加）
    try:
        existing_data = conn.read(worksheet="Sheet1")
    except:
        existing_data = pd.DataFrame() # 如果是第一次，创建一个空的

    # 3. 准备当前被试的数据
    new_data = pd.DataFrame([{**st.session_state.results}])
    
    # 4. 自动上传/提交
    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)
    
    st.success("数据已自动同步至主试后台表格！")
    st.balloons()