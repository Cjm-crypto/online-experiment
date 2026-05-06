import streamlit as st
import pandas as pd
import time
import os
import random

# --- 1. 基础配置 ---
st.set_page_config(page_title="工作记忆实验", layout="centered")

# 初始化 Session State (用于跨页面保存数据和控制流程)
if 'page' not in st.session_state:
    st.session_state.page = "START"  # 控制当前实验阶段
if 'results' not in st.session_state:
    st.session_state.results = {}     # 存储所有回答数据
if 'exp_info' not in st.session_state:
    st.session_state.exp_info = {}    # 存储被试信息

# --- 辅助函数：问卷渲染 ---
def run_survey(title, items, options):
    st.subheader(f"【{title}】")
    responses = []
    for i, item in enumerate(items):
        res = st.radio(f"{i+1}. {item}", options, horizontal=True, key=f"{title}_{i}")
        responses.append(res)
    return responses

# --- 2. 实验逻辑控制 ---

# A. 开始页面 & 被试信息录入
if st.session_state.page == "START":
    st.title("欢迎参加本次心理学测试")
    with st.form("info_form"):
        subject_id = st.text_input("被试编号", value="A01")
        gender = st.selectbox("性别", ["男", "女"])
        age = st.number_input("年龄", min_value=1, max_value=100, value=20)
        submitted = st.form_submit_button("开始实验")
        if submitted:
            st.session_state.exp_info = {"ID": subject_id, "Gender": gender, "Age": age}
            st.session_state.page = "SURVEY_RRS"
            st.rerun()

# B. 问卷阶段：RRS
elif st.session_state.page == "SURVEY_RRS":
    items = ["我究竟做了什么要遭如此报应", "分析新近发生的事情试图找到原因", "想到“我为什么总是有这种反应”"] # 示例，你可以补全
    st.info("1=从不，2=有时，3=经常，4=总是")
    res = run_survey("RRS 特质反刍问卷", items, [1, 2, 3, 4])
    if st.button("提交并进入下一阶段"):
        st.session_state.results['RRS_Sum'] = sum(res)
        st.session_state.page = "VAS_T1"
        st.rerun()

# C. VAS 量表 (生理与心理唤醒度)
elif st.session_state.page == "VAS_T1":
    st.subheader("请评估你此刻的状态")
    v1 = st.select_slider("【生理与心理唤醒度】(0极度平静 - 100极度紧张)", options=list(range(101)), value=50)
    v2 = st.select_slider("【情绪效价】(0极度郁闷 - 100极度开心)", options=list(range(101)), value=50)
    if st.button("下一步"):
        st.session_state.results['T1_Aro'] = v1
        st.session_state.results['T1_Valence'] = v2
        st.session_state.page = "VIDEO_PROMPT"
        st.rerun()

# D. 视频诱发阶段
elif st.session_state.page == "VIDEO_PROMPT":
    st.write("### 接下来，您将观看一段电影片段。")
    st.write("请佩戴好耳机，保持安静，尽量让自己【完全沉浸】在画面的情境与情绪中。")
    if st.button("准备好了，开始播放"):
        st.session_state.page = "VIDEO_PLAY"
        st.rerun()

elif st.session_state.page == "VIDEO_PLAY":
    video_path = "Shenpan.mp4" 
    if os.path.exists(video_path):
        st.video(video_path)
        st.write("视频播放结束后，请点击下方按钮。")
        if st.button("视频已看完"):
            st.session_state.page = "WRITING"
            st.rerun()
    else:
        st.error("找不到视频文件 Shenpan.mp4，请检查路径。")
        if st.button("跳过进入下一步"):
            st.session_state.page = "WRITING"
            st.rerun()

# E. 书写/反刍诱发
elif st.session_state.page == "WRITING":
    st.subheader("思考与书写")
    st.write("请在下框中写下你刚才视频后的感受，以及人生中让你感到被误解、不公平的事件。")
    user_text = st.text_area("你的感受...", height=200)
    
    # 模拟倒计时 (网页端不强制锁定，仅作提示)
    st.warning("建议书写时长：3分钟")
    
    if st.button("书写完毕"):
        st.session_state.results['writing_content'] = user_text
        st.session_state.page = "CDT_TASK"
        st.rerun()

# F. CDT 记忆任务 (简化展示)
elif st.session_state.page == "CDT_TASK":
    st.subheader("记忆任务阶段")
    st.write("由于网页端精度限制，请根据提示进行操作。")
    
    # 这里的 CDT 逻辑需要简化，网页端很难做 1.8s 的自动切换
    # 演示：展示一组图，然后进行判断
    st.image("https://via.placeholder.com/400x300.png?text=Memory+Images+Group", caption="请努力记住这组面孔")
    
    time_placeholder = st.empty()
    for i in range(3, 0, -1):
        time_placeholder.write(f"请记忆... {i}")
        time.sleep(1)
    time_placeholder.empty()
    
    st.write("---")
    st.image("https://via.placeholder.com/150.png?text=Probe+Face", caption="这张脸刚才出现过吗？")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("F (出现过)"):
            st.session_state.results['cdt_resp'] = "F"
            st.session_state.page = "FINISH"
            st.rerun()
    with col2:
        if st.button("J (没出现)"):
            st.session_state.results['cdt_resp'] = "J"
            st.session_state.page = "FINISH"
            st.rerun()

# G. 实验结束与数据导出
elif st.session_state.page == "FINISH":
    st.balloons()
    st.success("实验已完成！感谢您的参与。")
    
    # 汇总所有数据
    final_data = {**st.session_state.exp_info, **st.session_state.results}
    df = pd.DataFrame([final_data])
    
    st.write("### 您的数据记录：")
    st.dataframe(df)
    
    # 下载按钮
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="点击下载实验结果 CSV",
        data=csv,
        file_name=f"result_{st.session_state.exp_info.get('ID','temp')}.csv",
        mime='text/csv',
    )
    
    if st.button("重新开始"):
        st.session_state.page = "START"
        st.rerun()