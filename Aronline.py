import streamlit as st
import pandas as pd
import time
import os
import random
import streamlit as st
import time
from streamlit_gsheets import GSheetsConnection

# --- 1. 基础网页样式配置 (浅色护眼模式) ---
st.set_page_config(page_title="工作记忆实验", layout="centered")

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

# --- 2. 状态初始化 (在脚本最前端运行) ---
if 'stage_idx' not in st.session_state:
    st.session_state.stage_idx = 0
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'cdt_data' not in st.session_state:
    st.session_state.cdt_data = [] 
if 'cdt_trial' not in st.session_state:
    st.session_state.cdt_trial = 1
if 'correct_count' not in st.session_state:
    st.session_state.correct_count = 0
if 'trial_status' not in st.session_state:
    st.session_state.trial_status = "READY"
if 'block_idx' not in st.session_state:
    st.session_state.block_idx = 0
if 'in_boost_phase' not in st.session_state:
    st.session_state.in_boost_phase = False

# 【核心修复：清理了混入状态变量的 BUG】
STAGES = [
    "WELCOME", "INFO", "RRS", "BDI", "STAI", "T1_VAS_COMBINED", "T1_BSRI_INDEPENDENT", 
    "PRACTICE_INTRO", "CDT_PRACTICE", "VIDEO_INDUCTION", "WRITING", "RUMINATION", 
    "T2_VAS_BSRI", "FORMAL_INTRO", "CDT_FORMAL", "RECOVERY", "FINISH"
]

try:
    current_stage = STAGES[st.session_state.stage_idx]
except:
    st.session_state.stage_idx = 0
    st.rerun()

# --- 3. 实验常量与量表题库 ---
RRS_ITEMS = ["我究竟做了什么要遭如此报应", "分析新近发生的事情试图找到原因", "想到“我为什么总是有这种反应”", "一个人走开，思考自己为什么会有这种感觉", "记录你自己的想法并做分析", "回想新近的情境，希望情形已经好转", "想到“为什么我有这样问题而别人没有。”", "想到“我为什么不能把事情做得更好一点﹖”", "分析自己的性格试图找到沮丧的原因", "独自去某个地方考虑自己的感受"]
BDI_ITEMS = ["悲伤程度", "对未来失望感", "失败感", "负罪感", "惩罚感", "自厌感", "自我谴责", "自杀意念", "哭泣次数", "易激惹", "社交退缩", "犹豫不决", "自我形象改变", "工作困难", "睡眠障碍", "易疲劳", "食欲减退", "体重减轻", "躯体关注", "性欲减退"]
STAI_ITEMS = ["我感到愉快。", "我感到神经过敏和不安。", "我感到自我满足。", "我希望能像别人那样高兴。", "我感到像一个失败者。", "我感到很宁静。", "我是“平静、冷静和镇定自若”的。", "我感到困难成堆，无法克服。", "我过分忧虑一些事，实际这些事无关紧要。", "我是高兴的。"]
BSRI_ITEMS = ["1. 此刻，我在反复思考自己的负面情绪。", "2. 此刻，我想知道我为什么会反复思虑自己的负面情绪。", "3. 此刻，我想知道我为什么总是感受到自己反复思虑负面情绪。", "4. 此刻，我在想:”为什么我有很多的问题而其他人没有?“", "5. 此刻，我正在脑海里反复回想，最近我说过或做过的事情。", "6. 此刻，我在想:“为什么我不能更好地处理事情?“", "7. 此刻，我很难摆脱自己的负面想法。", "8. 此刻，我正在想:“面对负面情绪为什么我除了反复思虑它，不能以更好的方式反应”。"]

# --- 4. 任务辅助逻辑 ---
def next_stage():
    st.session_state.stage_idx += 1
    st.session_state.trial_status = "READY"
    st.session_state.cdt_trial = 1
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


# 获取本地图片或生成高还原度文本提示的通用函数
def get_cdt_stimulus(folder="neutral"):
    try:
        all_imgs = [f for f in os.listdir(folder) if f.lower().endswith(('.bmp', '.jpg', '.png'))]
        if len(all_imgs) >= 4:
            selected = random.sample(all_imgs, 4)
            is_same = random.choice([True, False])
            probe = random.choice(selected) if is_same else random.choice(list(set(all_imgs) - set(selected)))
            return selected, probe, is_same, folder
    except:
        pass
    return None, None, random.choice([True, False]), folder


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
    st.markdown("## 实验个人信息录入")
    with st.form("info"):
        user_name = st.text_input("请输入您的姓名", "") # 改为姓名
        sex = st.selectbox("性别", ["男", "女"])
        age = st.number_input("年龄", 1, 100, 20)
        st.write("（您的个人资料将严格保密）")
        if st.form_submit_button("确认并开始"):
            if user_name.strip() == "":
                st.error("请输入姓名后再点击确认。")
            else:
                st.session_state.results.update({"Name": user_name, "Sex": sex, "Age": age})
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


# 6.VAS 评估 (T1)
elif current_stage == "T1_VAS_COMBINED":
    st.markdown("## 状态评估 (T1)")
    st.markdown("### 1. 请评估你此刻的【生理与心理唤醒度】")
    st.write("(如：心跳加速、警觉、紧张感)")
    st.info("【打分参考】\n\n0 - 30：感到平静、放松、没有波澜\n\n40 - 60：中等程度的激活，感到轻微的紧张或气愤\n\n70 - 100：非常强烈的紧张、气愤或激动")
    t1_aro = st.select_slider("滑动滑块评估唤醒度", options=list(range(101)), value=50, key="t1_aro_val")
    
    st.markdown("---")
    st.markdown("### 2. 请评估你此刻的【情绪效价】")
    st.info("【打分参考】\n\n0 - 30：感到偏向负面、郁郁、痛苦\n\n40 - 60：情绪中立，没有明显的好坏\n\n70 - 100：感到偏向正面、开心、愉悦")
    t1_val = st.select_slider("滑动滑块评估效价", options=list(range(101)), value=50, key="t1_val_val")
    
    if st.button("确认提交以上评估"):
        st.session_state.results["T1_Arousal"] = t1_aro
        st.session_state.results["T1_Valence"] = t1_val
        next_stage()

# 7. T1 BSRI 评估 (T1) ---
elif current_stage == "T1_BSRI_INDEPENDENT":
    st.markdown("## 状态评估 (BSRI)")
    st.write("请根据此刻的真实感受，对以下描述进行打分（1=完全不符合，7=完全符合）：")
    bsri_res = [st.radio(q, [1, 2, 3, 4, 5, 6, 7], horizontal=True, key=f"t1_bsri_{i}") for i, q in enumerate(BSRI_ITEMS)]
    if st.button("确认提交 BSRI"):
        st.session_state.results["T1_BSRI_Sum"] = sum(bsri_res)
        next_stage()

# 8. CDT 练习任务指导语 
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
    """)
    if st.button("准备好后，点击开始练习"): next_stage()
# 9. CDT 练习逻辑 (5组，60%要求)
elif current_stage == "CDT_PRACTICE":
    total = 5
    st.markdown(f"### 练习阶段 ({st.session_state.cdt_trial}/{total})")
    placeholder = st.empty()

    if st.session_state.trial_status == "READY":
        if st.button(f"开始第 {st.session_state.cdt_trial} 组练习"):
            st.session_state.trial_status = "PLAYING"
            st.rerun()

    elif st.session_state.trial_status == "PLAYING":
        with placeholder.container():
            st.markdown("<h1 style='color:red; text-align:center;'>+</h1>", unsafe_allow_html=True)
            time.sleep(1.0)
            
            # 尝试加载真实本地图片，没有则使用高亮文本提示
            selected, probe, is_correct, folder = get_cdt_stimulus("neutral")
            if selected:
                col1, col2 = st.columns(2)
                col1.image(os.path.join(folder, selected[0]), use_column_width=True)
                col1.image(os.path.join(folder, selected[1]), use_column_width=True)
                col2.image(os.path.join(folder, selected[2]), use_column_width=True)
                col2.image(os.path.join(folder, selected[3]), use_column_width=True)
                st.session_state.current_probe_img = os.path.join(folder, probe)
            else:
                st.info("【 4张面孔 记忆中... (本地文件夹无图片) 】")
                st.session_state.current_probe_img = None
                
            time.sleep(1.8)
            st.markdown("<h3 style='text-align:center;'>【 噪音掩码 】</h3>", unsafe_allow_html=True)
            time.sleep(0.6)
            
            st.session_state.ans_correct = is_correct
            st.session_state.trial_status = "WAITING"
            st.rerun()

    elif st.session_state.trial_status == "WAITING":
        st.markdown("#### 判断：最后出现的这张脸在刚才那组（4张脸）中出现过吗？")
        if st.session_state.current_probe_img:
            st.image(st.session_state.current_probe_img, width=250)
        else:
            st.info("【 探测面孔 】")
            
        c1, c2 = st.columns(2)
        resp = None
        if c1.button("F (出现过)"): resp = True
        if c2.button("J (没出现)"): resp = False
        
        if resp is not None:
            if resp == st.session_state.ans_correct:
                st.session_state.correct_count += 1
            st.session_state.trial_status = "READY"
            if st.session_state.cdt_trial < total:
                st.session_state.cdt_trial += 1
            else:
                acc = st.session_state.correct_count / total
                if acc < 0.6: 
                    st.error(f"正确率 {acc*100:.0f}% 未达 60%，即将重测。")
                    time.sleep(2)
                    st.session_state.cdt_trial = 1
                    st.session_state.correct_count = 0
                else:
                    next_stage()
            st.rerun()

# 10. 诱发视频播放
elif current_stage == "VIDEO_INDUCTION":
    st.markdown("### 接下来，您将观看一段电影片段。")
    st.markdown("请佩戴好耳机，保持安静，全程不要转移视线。")
    st.markdown("请尽量让自己【完全沉浸】在画面的情境与情绪中。")
    if os.path.exists("Shenpan.mp4"): st.video("Shenpan.mp4")
    if st.button("播放完毕，进入下一步"): next_stage()

# 11. 书写阶段 (180s 倒计时)
elif current_stage == "WRITING":
    st.markdown("### 正如刚才视频中那种颠倒黑白、令人窒息的不公与气愤。")
    st.markdown("请在下方输入框写下你人生中经历过的，最让你感到**【被严重误解、不公平对待、极度挫败却又无能为力】**的一个事件。")
    txt = st.text_area("书写框...", height=300)
    countdown_timer(180, "书写剩余时间")
    play_beep()
    if st.button("书写完毕（或提前结束）"):
        st.session_state.results["Writing_Content"] = txt
        next_stage()

# 12. 引导反刍 (45s x 4)
elif current_stage == "RUMINATION":
    prompts = [
        "想一想，为什么这种不公平和倒霉的事情，偏偏会发生在你身上？", # 补全了漏掉的逗号
        "想一想，当时的你，为什么没有能力去为自己辩解或反抗？",
        "想一想，这件事的发生，是不是暴露出了你骨子里的弱点？",
        "想一想，这件事对你现在的状态，究竟造成了多大无法挽回的负面影响？"
    ]
    if 'rum_idx' not in st.session_state: 
        st.session_state.rum_idx = 0
        st.session_state.rum_timer_started = False

    st.markdown(f"## 深度思考 ({st.session_state.rum_idx+1}/{len(prompts)})")
    st.markdown(f"### {prompts[st.session_state.rum_idx]}")
    
    # 强制进行倒计时
    countdown_timer(45, "思考剩余时间")
    play_beep()
    
    if st.button("进入下一个思考点"):
        if st.session_state.rum_idx < len(prompts) - 1:
            st.session_state.rum_idx += 1
            st.rerun()
        else:
            next_stage()

# 13. T2 评估
elif current_stage == "T2_VAS_BSRI":
    st.header("状态评估")
    t2_aro = st.slider("请评估你此刻的【生理与心理唤醒度】", 0, 100, 50)
    t2_val = st.slider("请评估你此刻的【情绪效价】", 0, 100, 50)
    if st.button("提交评估"):
        st.session_state.results.update({"T2_Arousal": t2_aro, "T2_Valence": t2_val})
        next_stage()

# 14. 正式阶段 CDT 指导语 (全面还原)
if 'block_idx' not in st.session_state:
    st.session_state.block_idx = 0  # 0代表第一组，1代表第二组
if 'in_boost_phase' not in st.session_state:
    st.session_state.in_boost_phase = False

if current_stage == "FORMAL_INTRO":
    st.markdown("## 下面进行【正式实验任务】")
    st.markdown(f"""
    接下来将进行 **【两组实验任务】**。
    正式任务的要求与刚才练习阶段 **【完全一致】**。
    
    **唯一区别：**
    正式任务中，每次做出 F 或 J 判断后，请进行 **【信心检测】**。
    请根据 1-5 数字进行选择，1 代表完全猜测，5 代表非常确定。
    
    【温馨提示】：请确保您的输入法处于【英文】状态。
    准备好后，点击下方按钮开始第一组任务。
    """)
    
    # 【自动平衡逻辑】：根据编号末位奇偶决定 Block 顺序
    if 'blocks_order' not in st.session_state:
        # 定义两组
        b_list = [("中性模块", "neutral", 1.8), ("负性模块", "negative", 1.8)]
        # 获取编号最后一位数字
        sub_id = st.session_state.results.get('ID', 'A01')
        try:
            last_digit = int(''.join(filter(str.isdigit, sub_id))[-1])
            if last_digit % 2 == 0:
                b_list.reverse() # 偶数则反转顺序
        except:
            pass 
        st.session_state.blocks_order = b_list

    if st.button("开始第一组任务"):
        next_stage()

# 15. 正式 CDT 逻辑
elif current_stage == "CDT_FORMAL":
    # 获取当前组的信息
    block_name, folder, enc_time = st.session_state.blocks_order[st.session_state.block_idx]
    total_trials = 55 # 每组 55 次
    
    # A. 如果正在进行“加强诱发环节” (Block 间提示)
    if st.session_state.in_boost_phase:
        st.markdown(f"### 第一组任务已完成。接下来进行第二组任务：**{st.session_state.blocks_order[1][0]}**。")
        st.write("---")
        st.markdown("### 请再次闭上眼，回想刚才令你痛苦、气愤的事件")
        st.markdown("### 努力重新沉浸在那种情绪中。**请务必专心！**")
        
        # 60秒倒计时
        countdown_timer(60, "回想倒计时")
        play_beep() # 叮！
        
        st.success("加强环节结束。准备好后，点击下方按钮开始第二组任务。")
        if st.button("开始第二组任务"):
            st.session_state.in_boost_phase = False
            st.session_state.cdt_trial = 1
            st.rerun()

    # B. 正常的试次逻辑
    else:
        st.markdown(f"## {block_name} ({st.session_state.cdt_trial} / {total_trials})")
        placeholder = st.empty()

        # 状态 1: 准备好
        if st.session_state.trial_status == "READY":
            if st.button(f"开始第 {st.session_state.cdt_trial} 组测试", key=f"formal_btn_{st.session_state.block_idx}_{st.session_state.cdt_trial}"):
                st.session_state.trial_status = "PLAYING"
                st.rerun()

        # 状态 2: 播放序列
        elif st.session_state.trial_status == "PLAYING":
            with placeholder.container():
                st.markdown("<h1 style='color:red; text-align:center;'>+</h1>", unsafe_allow_html=True)
                time.sleep(1.0)
                
                # 读取图片
                selected, probe, is_correct, _ = get_cdt_stimulus(folder)
                if selected:
                    col1, col2 = st.columns(2)
                    col1.image(os.path.join(folder, selected[0]), use_column_width=True)
                    col1.image(os.path.join(folder, selected[1]), use_column_width=True)
                    col2.image(os.path.join(folder, selected[2]), use_column_width=True)
                    col2.image(os.path.join(folder, selected[3]), use_column_width=True)
                    st.session_state.current_probe_img = os.path.join(folder, probe)
                else:
                    st.write("【 4张面孔 记忆中... 】")
                    st.session_state.current_probe_img = None
                
                time.sleep(enc_time) # 1.8秒
                st.markdown("<h3 style='text-align:center;'>【 噪音掩码 】</h3>", unsafe_allow_html=True)
                time.sleep(0.6)
                
                st.session_state.ans_correct = is_correct
                st.session_state.trial_status = "WAITING"
                st.rerun()

        # 状态 3: 判断响应
        elif st.session_state.trial_status == "WAITING":
            st.markdown("#### 判断：这张脸出现过吗？")
            if st.session_state.current_probe_img:
                st.image(st.session_state.current_probe_img, width=250)
            
            c1, c2 = st.columns(2)
            res = None
            if c1.button("F (出现过)"): res = "F"
            if c2.button("J (没出现)"): res = "J"
            
            if res:
                st.session_state.current_resp = res
                st.session_state.trial_status = "CONFIDENCE"
                st.rerun()

        # 状态 4: 信心检测 (1-5)
        elif st.session_state.trial_status == "CONFIDENCE":
            st.markdown(f"#### 您刚才的选择是：**{st.session_state.current_resp}**")
            conf = st.select_slider("请评估您刚才判断的【信心程度】（1=完全猜测，5=非常确定）：", options=[1, 2, 3, 4, 5], value=3)
            
            if st.button("确认并进入下一题"):
                # 保存详尽数据
                st.session_state.cdt_data.append({
                    "Block": block_name,
                    "Trial": st.session_state.cdt_trial,
                    "Response": st.session_state.current_resp,
                    "Confidence": conf,
                    "Correct": (st.session_state.current_resp == "F" and st.session_state.ans_correct) or (st.session_state.current_resp == "J" and not st.session_state.ans_correct)
                })
                
                # 检查是否完成本组
                if st.session_state.cdt_trial < total_trials:
                    st.session_state.cdt_trial += 1
                    st.session_state.trial_status = "READY"
                else:
                    # 本组完成
                    if st.session_state.block_idx == 0:
                        # 第一组结束，进入加强环节
                        st.session_state.block_idx = 1
                        st.session_state.in_boost_phase = True
                        st.session_state.trial_status = "READY"
                    else:
                        # 第二组也结束，进入下一实验阶段
                        next_stage()
                st.rerun()


# 16. 恢复阶段
elif current_stage == "RECOVERY":
    st.markdown("## 实验任务已全部完成")
    st.markdown("### 接下来请观看一段轻松的视频以平复心情。")
    if os.path.exists("cat_video.mp4"):
        st.video("cat_video.mp4")
    else:
        st.warning("恢复视频 (cat_video.mp4) 缺失。")
    if st.button("观看完毕，进入最后结算"): next_stage()

# 17. 在实验结束阶段 (FINISH)
elif current_stage == "FINISH":
    st.title("实验全部完成！")
    all_data = {**st.session_state.results}
    # 将 CDT 55*2 条数据平铺
    for d in st.session_state.cdt_data:
        key = f"{d['Block']}_T{d['Trial']}"
        all_data[f"{key}_Resp"] = d["Resp"]; all_data[f"{key}_Conf"] = d["Conf"]
    
    final_df = pd.DataFrame([all_data])
    
    # Google Sheets 绝不覆盖逻辑：读取 -> 追加 -> 全量写回
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            old_df = conn.read(worksheet="Sheet1")
            updated_df = pd.concat([old_df, final_df], ignore_index=True)
        except:
            updated_df = final_df # 如果表是空的，则直接写
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("数据已成功同步至主试后台（Google Sheets）！")
    except Exception as e:
        st.warning(f"自动保存失败，请点击下方下载数据并发送给主试：{e}")
    
    st.download_button("📥 点击下载备份数据 CSV", final_df.to_csv(index=False).encode('utf-8-sig'), f"Data_{all_data.get('Name','user')}.csv")