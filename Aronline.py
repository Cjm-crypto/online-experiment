import streamlit as st
import pandas as pd
import time
import os
import random
from streamlit_gsheets import GSheetsConnection
import numpy as np
import io
import wave

# --- 声音生成函数 (无需外部文件) ---
def play_beep():
    sample_rate = 44100
    duration = 0.5
    frequency = 1000
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = (np.sin(frequency * t * 2 * np.pi) * 32767).astype(np.int16)
    byte_io = io.BytesIO()
    with wave.open(byte_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    st.audio(byte_io.getvalue(), format="audio/wav", autoplay=True)

def show_noise_mask(placeholder):
    """显示噪音掩码图"""
    placeholder.image(get_noise_img(), use_container_width=True)

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
if 'stage_idx' not in st.session_state: st.session_state.stage_idx = 0
if 'results' not in st.session_state: st.session_state.results = {}
if 'cdt_data' not in st.session_state: st.session_state.cdt_data = []
if 'cdt_trial' not in st.session_state: st.session_state.cdt_trial = 1
if 'correct_count' not in st.session_state: st.session_state.correct_count = 0
if 'block_idx' not in st.session_state: st.session_state.block_idx = 0
if 'in_boost_phase' not in st.session_state: st.session_state.in_boost_phase = False
# --- 新增练习阶段需要的初始化 ---
if 'is_running' not in st.session_state: st.session_state.is_running = False
if 'cdt_step' not in st.session_state: st.session_state.cdt_step = "FIXATION"
if 'trial_num' not in st.session_state: st.session_state.trial_num = 1
if 'practice_correct' not in st.session_state: st.session_state.practice_correct = 0
# --- 新增正式阶段和保存需要的初始化 ---
if 'trial_status' not in st.session_state: st.session_state.trial_status = "READY"
if 'exp_id' not in st.session_state: import uuid; st.session_state.exp_id = str(uuid.uuid4())[:8]

STAGES = [
    "WELCOME", "INFO", "RRS", "BDI", "STAI", "T1_VAS_COMBINED", "T1_BSRI",
    "PRACTICE_INTRO", "CDT_PRACTICE", "VIDEO_INDUCTION", "WRITING", 
    "RUMINATION", "T2_VAS_COMBINED", "T2_BSRI", "FORMAL_INTRO", 
    "CDT_FORMAL", "RECOVERY", "FINISH"
]

# --- 3. 实验常量与量表题库 ---
RRS_ITEMS = ["我究竟做了什么要遭如此报应", "分析新近发生的事情试图找到原因", "想到“我为什么总是有这种反应”", "一个人走开，思考自己为什么会有这种感觉", "记录你自己的想法并做分析", "回想新近的情境，希望情形已经好转", "想到“为什么我有这样问题而别人没有。”", "想到“我为什么不能把事情做得更好一点﹖”", "分析自己的性格试图找到沮丧的原因", "独自去某个地方考虑自己的感受"]
BDI_ITEMS = ["悲伤程度", "对未来失望感", "失败感", "负罪感", "惩罚感", "自厌感", "自我谴责", "自杀意念", "哭泣次数", "易激惹", "社交退缩", "犹豫不决", "自我形象改变", "工作困难", "睡眠障碍", "易疲劳", "食欲减退", "体重减轻", "躯体关注", "性欲减退"]
STAI_ITEMS = ["我感到愉快。", "我感到神经过敏和不安。", "我感到自我满足。", "我希望能像别人那样高兴。", "我感到像一个失败者。", "我感到很宁静。", "我是“平静、冷静和镇定自若”的。", "我感到困难成堆，无法克服。", "我过分忧虑一些事，实际这些事无关紧要。", "我是高兴的。"]
BSRI_ITEMS = ["1. 此刻，我在反复思考自己的负面情绪。", "2. 此刻，我想知道我为什么会反复思虑自己的负面情绪。", "3. 此刻，我想知道我为什么总是感受到自己反复思虑负面情绪。", "4. 此刻，我在想:”为什么我有很多的问题而其他人没有?“", "5. 此刻，我正在脑海里反复回想，最近我说过或做过的事情。", "6. 此刻，我在想:“为什么我不能更好地处理事情?“", "7. 此刻，我很难摆脱自己的负面想法。", "8. 此刻，我正在想:“面对负面情绪为什么我除了反复思虑它，不能以更好的方式反应”。"]

# --- 4. 任务辅助逻辑 ---
def next_stage():
    st.session_state.stage_idx += 1
    st.session_state.cdt_trial = 1
    st.session_state.correct_count = 0
    st.rerun()

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
elif current_stage == "T1_BSRI":
    st.markdown("## 状态评估 (BSRI)")
    st.write("请根据此刻的真实感受，对以下描述进行打分（1=完全不符合，7=完全符合）：")
    bsri_res = [st.radio(q, [1, 2, 3, 4, 5, 6, 7], horizontal=True, key=f"t1_bsri_{i}") for i, q in enumerate(BSRI_ITEMS)]
    if st.button("确认提交 BSRI"):
        st.session_state.results["T1_BSRI_Sum"] = sum(bsri_res)
        next_stage()

# 8. CDT 练习任务指导语 
elif current_stage == "PRACTICE_INTRO":
    st.markdown("## 下面进入【练习阶段】")
    cdt_intro = """
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
    """
    st.markdown(cdt_intro)
    if st.button("准备好后，点击开始练习"): next_stage()
# 9. CDT 练习逻辑 (10组，60%要求)
elif current_stage == "CDT_PRACTICE":
    TOTAL_PRACTICE = 10
    placeholder = st.empty()
     # 1. 准备开始页面
    if not st.session_state.is_running:
        with placeholder.container():
            st.subheader(f"练习阶段 (目标正确率: 60%)")
            st.write("点击下方按钮后，程序将自动运行 10 组测试。")
            if st.button("开始练习测试"):
                st.session_state.is_running = True
                st.session_state.cdt_step = "FIXATION"
                st.rerun()

    # 2. 自动循环逻辑
    elif st.session_state.is_running:
        
        # --- 阶段 A: 注视点 (+) ---
        if st.session_state.cdt_step == "FIXATION":
            with placeholder.container():
                st.markdown(f"<p style='text-align:right;'>组次: {st.session_state.trial_num}/{TOTAL_PRACTICE}</p>", unsafe_allow_html=True)
                st.markdown("<h1 style='color:red; text-align:center; font-size:120px; padding:100px 0;'>+</h1>", unsafe_allow_html=True)
                time.sleep(1.0)
            st.session_state.cdt_step = "MEMORY"
            st.rerun()

        # --- 阶段 B: 四张图片呈现 ---
        elif st.session_state.cdt_step == "MEMORY":
            with placeholder.container():
                folder = "neutral" 
                # 这里假设你的图片放在 neutral 文件夹下
                try:
                    all_imgs = [f for f in os.listdir(folder) if f.lower().endswith(('.bmp', '.jpg', '.png'))]
                    sel_imgs = random.sample(all_imgs, 4)
                    
                    # 决定这一题是“一样”还是“不一样”
                    ans_same = random.choice([True, False])
                    # 存储到 session 用于判断
                    st.session_state.temp_ans = ans_same
                    if ans_same:
                        st.session_state.temp_probe = os.path.join(folder, random.choice(sel_imgs))
                    else:
                        st.session_state.temp_probe = os.path.join(folder, random.choice(list(set(all_imgs)-set(sel_imgs))))
                    
                    # 宫格呈现 2x2
                    c1, c2 = st.columns(2)
                    c1.image(os.path.join(folder, sel_imgs[0]), use_container_width=True)
                    c1.image(os.path.join(folder, sel_imgs[1]), use_container_width=True)
                    c2.image(os.path.join(folder, sel_imgs[2]), use_container_width=True)
                    c2.image(os.path.join(folder, sel_imgs[3]), use_container_width=True)
                    time.sleep(1.0)
                except Exception as e:
                    st.error(f"图片读取错误，请检查 neutral 文件夹: {e}")
                    st.stop()
            st.session_state.cdt_step = "MASK"
            st.rerun()

        # --- 阶段 C: 掩码页面 ---
        elif st.session_state.cdt_step == "MASK":
            with placeholder.container():
                st.image(get_noise_img(), use_container_width=True)
                time.sleep(2.2)
            st.session_state.cdt_step = "JUDGE"
            st.rerun()

        # --- 阶段 D: 判断页面 (需被试操作) ---
        elif st.session_state.cdt_step == "JUDGE":
            with placeholder.container():
                st.markdown("### 判断：刚才那组图片中是否有这一张？")
                st.image(st.session_state.temp_probe, width=300)
                col1, col2 = st.columns(2)
                res = None
                if col1.button("F (出现过)", key=f"f_{st.session_state.trial_num}"): res = True
                if col2.button("J (没出现过)", key=f"j_{st.session_state.trial_num}"): res = False
                
                if res is not None:
                    # 计分
                    if res == st.session_state.temp_ans:
                        st.session_state.practice_correct += 1
                        st.session_state.last_fb = "正确"
                    else:
                        st.session_state.last_fb = "错误"
                    st.session_state.cdt_step = "FEEDBACK"
                    st.rerun()

        # --- 阶段 E: 反馈并自动进入下一组 ---
        elif st.session_state.cdt_step == "FEEDBACK":
            with placeholder.container():
                if st.session_state.last_fb == "正确":
                    st.success("✔ 正确")
                else:
                    st.error("✘ 错误")
                time.sleep(0.6)
            
            # 检查是否做完 10 组
            if st.session_state.trial_num < TOTAL_PRACTICE:
                st.session_state.trial_num += 1
                st.session_state.cdt_step = "FIXATION" # 自动跳回第一步
                st.rerun()
            else:
                # 10 组完成，结算
                acc = st.session_state.practice_correct / TOTAL_PRACTICE
                if acc >= 0.6:
                    st.session_state.is_running = False # 停止自动循环
                    st.success(f"练习完成！正确率: {acc*100:.0f}%。达标，准备进入正式实验。")
                    if st.button("进入下一环节"): next_stage()
                else:
                    st.session_state.is_running = False 
                    st.error(f"正确率仅为 {acc*100:.0f}%，未达到 60%。请重新练习。")
                    if st.button("重新开始练习"):
                        st.session_state.trial_num = 1
                        st.session_state.practice_correct = 0
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
    txt = st.text_area("书写框：", height=300)
    timer_p = st.empty()
    for i in range(180, -1, -1):
        timer_p.markdown(f"## ⏳ 剩余时间: {i} 秒"); time.sleep(1)
    st.session_state.results["Writing"] = txt
    st.success("时间到！自动进入下一阶段"); time.sleep(1.5); next_stage()

# 12. 引导反刍 (45s x 4)
elif current_stage == "RUMINATION":
    prompts = [
        "想一想，为什么这种不公平和倒霉的事情，偏偏会发生在你身上？", # 补全了漏掉的逗号
        "想一想，当时的你，为什么没有能力去为自己辩解或反抗？",
        "想一想，这件事的发生，是不是暴露出了你骨子里的弱点？",
        "想一想，这件事对你现在的状态，究竟造成了多大无法挽回的负面影响？"
    ]
    if 'rum_idx' not in st.session_state: st.session_state.rum_idx = 0
    
    # 修改点：显示之前的书写内容，且设为不可编辑 (disabled)
    st.text_area("你刚才记录的事件：", value=st.session_state.results.get("Writing",""), height=200, disabled=True)
    
    idx = st.session_state.rum_idx
    st.markdown(f"### 【请闭眼深度思考】\n{prompts[idx]}")
    
    timer_p = st.empty()
    for i in range(45, -1, -1):
        timer_p.markdown(f"## ⏳ 思考倒计时: {i} 秒")
        time.sleep(1)
    
    play_beep() # 修改点：倒计时结束响铃
    
    if idx < len(prompts) - 1:
        st.session_state.rum_idx += 1
        st.rerun()
    else:
        next_stage()

# 13--- 后测评估 (修改点4：加入 BSRI) ---
elif current_stage == "T2_VAS_COMBINED":
    st.markdown("## 状态评估 (T2)")
    st.markdown("### 1. 请评估你此刻的【生理与心理唤醒度】")
    st.write("(如：心跳加速、警觉、紧张感)")
    st.info("【打分参考】\n\n0 - 30：感到平静、放松、没有波澜\n\n40 - 60：中等程度的激活，感到轻微的紧张或气愤\n\n70 - 100：非常强烈的紧张、气愤或激动")
    t1_aro = st.select_slider("滑动滑块评估唤醒度", options=list(range(101)), value=50, key="t2_aro_val")
    
    st.markdown("---")
    st.markdown("### 2. 请评估你此刻的【情绪效价】")
    st.info("【打分参考】\n\n0 - 30：感到偏向负面、郁郁、痛苦\n\n40 - 60：情绪中立，没有明显的好坏\n\n70 - 100：感到偏向正面、开心、愉悦")
    t1_val = st.select_slider("滑动滑块评估效价", options=list(range(101)), value=50, key="t2_val_val")
    
    if st.button("确认提交以上评估"):
        st.session_state.results["T2_Arousal"] = t2_aro
        st.session_state.results["T2_Valence"] = t2_val
        next_stage()


elif current_stage == "T2_BSRI":
    st.markdown("## 状态评估 (BSRI - T2)")
    st.write("请根据此刻的真实感受，对以下描述进行打分（1=完全不符合，7=完全符合）：")
    res = [st.radio(q, [1,2,3,4,5,6,7], horizontal=True, key=f"t2_bsri_{i}") for i, q in enumerate(BSRI_ITEMS)]
    if st.button("提交 T2 BSRI"):
        st.session_state.results["T2_BSRI_Sum"] = sum(res)
        next_stage()


# 14. 正式阶段 CDT 指导语 (全面还原)

elif current_stage == "FORMAL_INTRO":
    st.markdown("## 下面进行【正式实验任务】")
    st.markdown(f"""
    接下来将进行 **【两组实验任务】**。
    正式任务的要求与刚才练习阶段 **【完全一致】**。
    
    **唯一区别：**
    正式任务中，每次做出 F 或 J 判断后，请进行 **【信心检测】**。
    请根据 1-5 数字进行选择，1 代表完全猜测，5 代表非常确定。

    准备好后，点击下方按钮开始第一组任务。
    """)
    if st.button("开始正式任务"): 
        b_list = [("中性", "neutral"), ("负性", "negative")]
        user_name = st.session_state.results.get('Name', '')
        if len(user_name) % 2 == 0:
            b_list.reverse()
            
        # 将顺序存入内存并进入下一阶段
        st.session_state.blocks_order = b_list
        next_stage()  # 这一行也要缩进，表示点击按钮后才执行跳转
    
 # 核心修改：正式 CDT 逻辑 (记录 RT 和信心)
elif current_stage == "CDT_FORMAL":
    block_name, folder = st.session_state.blocks_order[st.session_state.block_idx]
    TOTAL_FORMAL = 60
    if st.session_state.in_boost_phase:
        st.markdown("### 加强回想中 (60s)"); t_p = st.empty()
        for i in range(60, -1, -1): t_p.markdown(f"## ⏳ {i}秒"); time.sleep(1)
        play_beep()
        if st.button("开始下一组"): st.session_state.in_boost_phase = False; st.session_state.cdt_trial = 1; st.rerun()
    else:
        st.markdown(f"### {block_name} ({st.session_state.cdt_trial}/60)")
        placeholder = st.empty()
        if st.session_state.trial_status == "READY":
            if st.button("开始测试试次"): st.session_state.trial_status = "SEQUENCE"; st.rerun()
        elif st.session_state.trial_status == "SEQUENCE":
            with placeholder.container():
                st.markdown("<h1 style='color:red; text-align:center;'>+</h1>", unsafe_allow_html=True); time.sleep(1.0)
                all_imgs = [f for f in os.listdir(folder) if f.lower().endswith(('.bmp', '.jpg', '.png'))]
                sel = random.sample(all_imgs, 4)
                st.session_state.ans_correct = random.choice([True, False])
                prb = random.choice(sel) if st.session_state.ans_correct else random.choice(list(set(all_imgs)-set(sel)))
                st.session_state.current_probe = os.path.join(folder, prb)
                c1, c2 = st.columns(2)
                c1.image(os.path.join(folder, sel[0])); c1.image(os.path.join(folder, sel[1]))
                c2.image(os.path.join(folder, sel[2])); c2.image(os.path.join(folder, sel[3]))
                time.sleep(1.8); placeholder.empty(); show_noise_mask(placeholder); time.sleep(2.2)
                st.session_state.start_time = time.time(); st.session_state.trial_status = "WAITING"; st.rerun()
        elif st.session_state.trial_status == "WAITING":
            st.image(st.session_state.current_probe, width=300)
            c1, c2 = st.columns(2)
            res = "F" if c1.button("F (出现过)") else ("J" if c2.button("J (没出现)") else None)
            if res:
                st.session_state.rt = time.time() - st.session_state.start_time
                st.session_state.cur_res = res; st.session_state.trial_status = "CONF"; st.rerun()
        elif st.session_state.trial_status == "CONF":
            conf = st.select_slider("信心值 (1-5)", options=[1,2,3,4,5], value=3)
            if st.button("提交结果"):
                is_correct = 1 if (st.session_state.cur_res=="F" and st.session_state.ans_correct) or (st.session_state.cur_res=="J" and not st.session_state.ans_correct) else 0
                st.session_state.cdt_data.append({"Block": block_name, "Trial": st.session_state.cdt_trial, "Resp": st.session_state.cur_res, "Correct": is_correct, "RT": round(st.session_state.rt, 3), "Conf": conf, "Is_Same": st.session_state.ans_correct})
                st.session_state.trial_status = "READY"
                if st.session_state.cdt_trial < TOTAL_FORMAL: st.session_state.cdt_trial += 1
                elif st.session_state.block_idx == 0: st.session_state.block_idx = 1; st.session_state.in_boost_phase = True
                else: next_stage()
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
    st.balloons()
    st.header("实验已全部完成！")
    
    # 构建最终数据表
    final_rows = []
    base_info = st.session_state.results 
    for d in st.session_state.cdt_data:
        row = {**base_info, **d, "Session_UUID": st.session_state.exp_id}
        final_rows.append(row)
    
    if not final_rows:
        st.warning("未检测到实验数据。")
        df_new = pd.DataFrame()
    else:
        df_new = pd.DataFrame(final_rows)
                # 保存逻辑
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # 读取并同步逻辑... (保持原样)
            existing_data = conn.read(worksheet="Sheet1")
            updated_df = pd.concat([existing_data, df_new], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("数据已同步至云端数据库。")
        except Exception as e:
            st.warning(f"自动同步未完成，请手动下载。")
            
        st.download_button(
            "点击下载实验数据 (CSV)", 
            df_new.to_csv(index=False).encode('utf-8-sig'), 
            f"Result_{base_info.get('Name','trial')}.csv"
        )