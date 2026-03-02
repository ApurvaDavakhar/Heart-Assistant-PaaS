import streamlit as st
from streamlit_lottie import st_lottie
import requests
import pandas as pd
import qrcode
from io import BytesIO
import socket
import plotly.express as px
from brain import analyze_vitals, analyze_meal
from datetime import date
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pushbullet import Pushbullet
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import BernoulliNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn import svm
from sklearn.neural_network import MLPClassifier

st.set_page_config(page_title="Dr. Robo Mega Project", page_icon="🤖", layout="wide")

# --- SESSION STATE FOR ML LAB ---
if 'ml_results' not in st.session_state: st.session_state.ml_results = {}
if 'uploaded_df' not in st.session_state: st.session_state.uploaded_df = None

# --- WATCH ALERT & UTILS ---
def send_watch_alert(risk_score):
    try:
        token = "o.yaFXkdxQwCrffm7J1r3Qa3AYDasBP76D" 
        pb = Pushbullet(token)
        title = "🚨 Dr. Robo: HIGH RISK" if risk_score == 1 else "✅ Dr. Robo: STABLE"
        pb.push_note(title, "Check Dr. Robo App for details.")
    except: pass

def generate_pdf(df):
    pdf_path = "Heart_Health_Report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 22); c.drawString(100, 750, "DR. ROBO CLINICAL REPORT")
    c.setFont("Helvetica", 12); c.drawString(100, 720, f"Generated: {date.today()} | Patient Record")
    c.line(100, 710, 500, 710)
    avg_bp = df['BP'].mean(); avg_hr = df['HR'].mean()
    c.drawString(100, 680, f"Total Records: {len(df)}")
    c.drawString(100, 660, f"Average BP: {avg_bp:.1f} mmHg"); c.drawString(100, 640, f"Average HR: {avg_hr:.1f} BPM")
    c.drawString(100, 610, f"High Risk Incident Days: {len(df[df['Result']==1])}")
    c.setFont("Helvetica-Oblique", 10); c.drawString(100, 550, "Note: Share this report with your cardiologist for clinical review.")
    c.save(); return pdf_path

def save_to_history(data_list, result):
    history_file = "patient_history.csv"
    cols = ['Age','Sex','Weight','Sugar','BP','HR','Sleep','Steps','Smoke','CP','Result','Date']
    new_data = pd.DataFrame([data_list + [result, date.today()]], columns=cols)
    if not os.path.isfile(history_file): new_data.to_csv(history_file, index=False)
    else: new_data.to_csv(history_file, mode='a', header=False, index=False)

def load_lottie(url):
    try: return requests.get(url).json()
    except: return None

# Animations
HELLO_URL = "https://lottie.host/5a65cd42-949b-4185-8845-562203a6bb64/NSmkbO4QRS.json"
DOC_URL   = "https://lottie.host/82ab9717-0989-493b-9779-970ec24e45bb/4zDFgUhSfp.json"
CHEF_URL  = "https://lottie.host/1cb383b0-8b82-488b-a813-82e376ad76ae/VpBWKI5rAO.json"

if 'mode' not in st.session_state: st.session_state.mode = "greeting"

# --- SIDEBAR ---
with st.sidebar:
    st.title("Dr. Robo 🩺")
    if st.session_state.mode == "greeting": st_lottie(load_lottie(HELLO_URL), height=180)
    elif st.session_state.mode == "consulting": st_lottie(load_lottie(DOC_URL), height=180)
    elif st.session_state.mode == "chef": st_lottie(load_lottie(CHEF_URL), height=180)
    menu = st.radio("Navigation", ["Check Health", "Analytics & PDF Report", "Expert ML Research Lab"])

# --- MODULE 1: CHECK HEALTH (STAYS AS IS) ---
if menu == "Check Health":
    if st.session_state.mode == "greeting":
        st.title("👋 Welcome to Dr. Robo Clinic")
        with st.form("VitalsForm"):
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", 18, 100, 30); sex = st.selectbox("Sex (1=M, 0=F)", [1, 0])
                weight = st.number_input("Weight (kg)", 30, 150, 70); sugar = st.number_input("Sugar", 70, 250, 100); bp = st.number_input("BP", 90, 200, 120)
            with col2:
                hr = st.number_input("HR", 50, 150, 75); sleep = st.number_input("Sleep", 1, 12, 7); steps = st.number_input("Steps", 0, 20000, 5000); smoke = st.selectbox("Smoker?", [0, 1]); cp = st.selectbox("Chest Pain (0-3)", [0, 1, 2, 3])
            
            if st.form_submit_button("Start Consultation"):
                vitals = [age, sex, weight, sugar, bp, hr, sleep, steps, smoke, cp]
                res, prob, acc = analyze_vitals(vitals)
                save_to_history(vitals, res)
                st.session_state.prediction, st.session_state.prob = res, prob
                st.session_state.mode = "consulting"; send_watch_alert(res); st.rerun()

    elif st.session_state.mode == "consulting":
        st.title("🩺 Diagnosis Result")
        if st.session_state.prediction == 1: st.error(f"ABNORMAL CONDITION DETECTED (Prob: {st.session_state.prob*100:.1f}%)")
        else: st.success(f"STABLE CONDITION DETECTED (Prob: {st.session_state.prob*100:.1f}%)")
        if st.button("Consult Chef Robo ➔"): st.session_state.mode = "chef"; st.rerun()

    elif st.session_state.mode == "chef":
        st.title("👨‍🍳 Meal Advisor")
        meal = st.text_input("What is your dinner plan?")
        if meal: st.info(analyze_meal(meal, st.session_state.prediction))
        if st.button("Back to Clinic"): st.session_state.mode = "greeting"; st.rerun()

# --- MODULE 2: ANALYTICS & PDF REPORT (STAYS AS IS) ---
elif menu == "Analytics & PDF Report":
    st.title("📊 Clinical History & Reporting")
    if os.path.exists("patient_history.csv"):
        df_history = pd.read_csv("patient_history.csv")
        st.plotly_chart(px.line(df_history, x='Date', y='BP', title='Historical Blood Pressure Trend'))
        if st.button("Generate Official PDF Report"):
            path = generate_pdf(df_history)
            with open(path, "rb") as f: st.download_button("📥 Download PDF for Doctor", f, file_name=path)
    else: st.warning("No clinical history available yet.")

# --- MODULE 3: EXPERT ML RESEARCH LAB (THE PURCHASED DASHBOARD) ---
elif menu == "Expert ML Research Lab":
    st.title("🧪 Machine Learning Health Prediction Lab")
    st.write("Compare different medical algorithms using the system dataset.")
    
    # 1. Upload Section
    uploaded_file = st.file_uploader("Upload Healthcare Dataset (heart.csv)", type=["csv"])
    if uploaded_file:
        st.session_state.uploaded_df = pd.read_csv(uploaded_file)
        st.success("Dataset successfully loaded for training!")

    if st.session_state.uploaded_df is not None:
        df = st.session_state.uploaded_df
        X = df.iloc[:, :-1].values; Y = df.iloc[:, -1].values
        X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
        
        # 2. Individual Algorithm Buttons (Like the Purchased Dashboard)
        st.markdown("### Run Performance Tests")
        col1, col2, col3 = st.columns(3)
        
        # Mapping buttons to models
        algs = {
            "Run KNN": KNeighborsClassifier(n_neighbors=10),
            "Run Naive Bayes": BernoulliNB(),
            "Run Decision Tree": DecisionTreeClassifier(criterion="entropy"),
            "Run SVM": svm.SVC(probability=True),
            "Run Random Forest": RandomForestClassifier(n_estimators=200),
            "Run Logistic": LogisticRegression(),
            "Run Gradient Boosting": GradientBoostingClassifier(),
            "Run MLP": MLPClassifier(max_iter=500),
            "Run Ensemble": VotingClassifier(estimators=[('rf', RandomForestClassifier()), ('dt', DecisionTreeClassifier())], voting='soft')
        }

        # Logic to display buttons and store results
        for i, (btn_name, model) in enumerate(algs.items()):
            with [col1, col2, col3][i % 3]:
                if st.button(btn_name):
                    model.fit(X_train, y_train)
                    preds = model.predict(X_test)
                    acc = accuracy_score(y_test, preds) * 100
                    st.session_state.ml_results[btn_name] = acc
                    st.write(f"**{btn_name.split(' ')[1]} Accuracy:** {acc:.2f}%")

        # 3. Graph Button (Like the Purchased Dashboard)
        st.divider()
        if st.session_state.ml_results:
            if st.button("Generate Comparison Graph"):
                res_df = pd.DataFrame(list(st.session_state.ml_results.items()), columns=['Algorithm', 'Accuracy'])
                st.plotly_chart(px.bar(res_df, x='Algorithm', y='Accuracy', color='Accuracy', title="Multi-Model Accuracy Comparison"))

# --- QR CODE SIDEBAR ---
with st.sidebar:
    st.divider()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('8.8.8.8', 1)); ip = s.getsockname()[0]
    except: ip = 'localhost'
    finally: s.close()
    url = f"http://{ip}:{st.get_option('server.port')}"
    qr = qrcode.make(url); buf = BytesIO(); qr.save(buf)
    st.image(buf, caption=f"Network Gateway: {url}")