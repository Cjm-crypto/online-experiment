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
    .main { background-color: #000000; color: white; }
    .stMarkdown { text-align: center; font-family: 'Microsoft YaHei'; }
    h1, h2, h3, h4 { color: #FFFFFF !important; }
    div.stButton > button { width: 100%; height: 4em; font-size: 18px; background-color: #333333; color: white; border: 1px solid #555; }
    div.stButton > button:hover { border-color: #FF4B4B; color: #FF4B4B; }
    .stRadio > label { font-size: 18px !important; color: #EEEEEE !important; }
    </style>
    """, unsafe_allow_html=True)

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

# --- 4. 初始化 Session 状态 ---
if 'stage_idx' not in st.session_state:
    st.session_state.stage_idx = 0
    st.session_state.results = {}
    st.session_state.cdt_results = []
    st.session_state.cdt_trial = 1

STAGES = ["WELCOME", "INFO", "RRS", "BDI", "STAI", "T1_VAS_BSRI", "CDT_PRE_INSTR", "CDT_TASK", "VIDEO_INSTR", "VIDEO_PLAY", "WRITING", "RUMINATION", "T2_VAS_BSRI", "CDT_FORMAL", "RECOVERY", "FINISH"]
current_stage = STAGES[st.session_state.stage_idx]

# --- 5. 实验流程控制 ---

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
elif current_stage in ["RRS", "BDI", "STAI"]:
    items = RRS_ITEMS if current_stage=="RRS" else (BDI_ITEMS if current_stage=="BDI" else STAI_ITEMS)
    st.markdown(f"## 【{current_stage} 问卷阶段】")
    st.write("根据你的真实情况进行打分：")
    ans = []
    for i, q in enumerate(items):
        r = st.radio(q, [1,2,3,4] if current_stage!="BDI" else [0,1,2,3], horizontal=True, key=f"{current_stage}_{i}")
        ans.append(r)
    if st.button("提交本阶段"):
        st.session_state.results[f"{current_stage}_Sum"] = sum(ans)
        next_stage()

# 6 & 13. VAS 与 BSRI
elif current_stage in ["T1_VAS_BSRI", "T2_VAS_BSRI"]:
    tag = "前测" if "T1" in current_stage else "后测"
    st.markdown(f"## 评估环节 ({tag})")
    
    st.markdown("#### 请评估你此刻的【生理与心理唤醒度】")
    st.write("0-30: 平静/放松；40-60: 轻微紧张；70-100: 非常强烈紧张")
    aro = st.slider("滑动滑块打分", 0, 100, 50, key=f"{current_stage}_aro")
    
    st.markdown("#### 请评估你此刻的【情绪效价】")
    st.write("0-30: 极度郁闷；40-60: 情绪中立；70-100: 极度开心")
    val = st.slider("滑动滑块打分", 0, 100, 50, key=f"{current_stage}_val")
    
    st.write("---")
    st.markdown("#### BSRI 评估")
    st.write("1=完全不符合，4=中立，7=完全符合")
    bs_ans = []
    for i, q in enumerate(BSRI_ITEMS):
        r = st.radio(q, [1,2,3,4,5,6,7], horizontal=True, key=f"{current_stage}_bs_{i}")
        bs_ans.append(r)
    if st.button("确认提交"):
        st.session_state.results.update({f"{tag}_Aro": aro, f"{tag}_Val": val, f"{tag}_BSRI_Sum": sum(bs_ans)})
        next_stage()

# 7. CDT 任务指导语 (还原文档)
elif current_stage == "CDT_PRE_INSTR":
    st.markdown("## 接下来的任务流程")
    st.write("1. 屏幕中央会出现红色的“+”，请盯住它。")
    st.write("2. 随后屏幕会闪现【4张面孔】，请努力记住他们的特征。")
    st.write("3. 接着屏幕短暂空白后，会出现【1张面孔】。")
    st.markdown("### **请判断：最后出现的这张脸，是否在刚才那组（4张脸）中出现过？**")
    if st.button("进入测试"): next_stage()

# 8 & 14. CDT 任务主体 (F/J 按钮版)
elif current_stage in ["CDT_TASK", "CDT_FORMAL"]:
    is_formal = (current_stage == "CDT_FORMAL")
    total_trials = 10 if not is_formal else 20
    
    st.markdown(f"### CDT 任务 ({st.session_state.cdt_trial} / {total_trials})")
    
    # 模拟任务序列
    placeholder = st.empty()
    
    # 1. 注视点
    placeholder.markdown("<h1 style='color: red; font-size: 100px;'>+</h1>", unsafe_allow_html=True)
    time.sleep(1.0)
    
    # 2. 记忆项 (4张图 2x2 布局)
    placeholder.empty()
    try:
        folder = "neutral" # 默认读 neutral 文件夹
        all_imgs = [f for f in os.listdir(folder) if f.lower().endswith(('.bmp', '.jpg', '.png'))]
        # 随机选 4 张记忆，1 张探测
        selected = random.sample(all_imgs, 4)
        probe = random.choice(selected) if random.random() > 0.5 else random.choice(list(set(all_imgs)-set(selected)))
        
        # 显示 4 张
        m_col1, m_col2 = placeholder.columns(2)
        with m_col1:
            st.image(os.path.join(folder, selected[0]), width=200)
            st.image(os.path.join(folder, selected[1]), width=200)
        with m_col2:
            st.image(os.path.join(folder, selected[2]), width=200)
            st.image(os.path.join(folder, selected[3]), width=200)
        time.sleep(1.8)
    
    # 3. 掩码 (噪音干扰)
    placeholder.empty()
    placeholder.markdown("### [ 噪音掩码 ]")
    time.sleep(0.6)
    
    # 4. 探测与判断 (核心修改：F/J 按钮)
    placeholder.empty()
    st.markdown("#### 请判断探测面孔是否出现过？")
    st.image("https://via.placeholder.com/150", width=250) # 探测图
    
    start_time = time.time()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("F (一样 / 出现过)"):
            rt = time.time() - start_time
            st.session_state.cdt_results.append({"Trial": st.session_state.cdt_trial, "Resp": "F", "RT": rt})
            if st.session_state.cdt_trial < total_trials: 
                st.session_state.cdt_trial += 1
                st.rerun()
            else: 
                st.session_state.cdt_trial = 1
                next_stage()
    with c2:
        if st.button("J (全新 / 没出现)"):
            rt = time.time() - start_time
            st.session_state.cdt_results.append({"Trial": st.session_state.cdt_trial, "Resp": "J", "RT": rt})
            if st.session_state.cdt_trial < total_trials: 
                st.session_state.cdt_trial += 1
                st.rerun()
            else: 
                st.session_state.cdt_trial = 1
                next_stage()

# 10. 诱发视频播放
elif current_stage == "VIDEO_PLAY":
    st.markdown("### 请全神贯注观看视频")
    if os.path.exists("Shenpan.mp4"):
        st.video("Shenpan.mp4")
        if st.button("视频已播放结束"): next_stage()
    else:
        st.error("视频缺失")
        if st.button("跳过"): next_stage()

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