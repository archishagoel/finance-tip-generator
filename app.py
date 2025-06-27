import streamlit as st
import requests
import json
import os

from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("WATSONX_API_KEY")

PROJECT_ID = "dcb560fa-bad2-4bd1-b579-146389917a26"
MODEL_ID = "meta-llama/llama-2-13b-chat"  # Example model, can change
REGION = "us-south"  # or whichever region your project is in

# === Get access token ===
def get_access_token(api_key):
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={api_key}"

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        return None

# === Call watsonx.ai Model ===
def generate_ai_tip(prompt, token):
    url = f"https://{REGION}.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "model_id": MODEL_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 1000
        },
        "project_id": PROJECT_ID  # ✅ Correct location for project_id
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["results"][0]["generated_text"]
    else:
        return f"Error: {response.text}"

# === Streamlit UI ===
st.title("💰 Personal Finance Tip Generator: ")

income = st.number_input("Monthly Income (₹)", min_value=0)
expenses = st.number_input("Monthly Expenses (₹)", min_value=0)
savings = st.number_input("Current Savings (₹)", min_value=0)
goal = st.number_input("Savings Goal (₹)", min_value=0)

if st.button("Get Tips"):
    # Logic-based suggestions
    logic_tips = []
    percent = (expenses / income) * 100 if income > 0 else 0


    if percent > 70:
        logic_tips.append("You're spending over 70% of income. Try cutting back on non-essentials.")
    if savings < goal:
        logic_tips.append("You are behind on your savings goal. Consider saving 20% each month.")

    # ✅ ADD THESE NEW RULES BELOW:
    if expenses > income * 0.8:
        logic_tips.append("Your spending is very high. Cut dining out and luxury shopping.")
    if income - expenses < 5000:
        logic_tips.append("Your surplus is too low. Consider finding a side gig for extra income.")
    if savings < goal and income - expenses > 0:
        months_needed = round((goal - savings) / (income - expenses))
        logic_tips.append(f"At your current savings rate, you can reach your goal in about {months_needed} months.")

    # ✅ Now build the prompt *from logic_tips* instead of repeating same static text
    combined_tips = "\n".join(logic_tips)
    prompt = (
    f"The user shared their income and expenses. Here are some calculated tips:\n"
    f"{combined_tips}\n"
    f"Rewrite these in a friendly, motivating style. "
    f"Additionally, based on this:\n"
    f"I earn ₹{income} per month and spend ₹{expenses}. "
    f"My current savings are ₹{savings} and I want to save up to ₹{goal}.\n"
    f"Suggest 3 realistic personal finance tips that help me reduce unnecessary spending, boost savings, and reach my goal faster. "
    f"Keep tips short, simple, and suitable for young adults."
)


   

    access_token = get_access_token(API_KEY)
    if access_token:
        ai_tip = generate_ai_tip(prompt, access_token)
    else:
        ai_tip = "Could not get access token. Check your API key."

    st.subheader("📊 Rule-Based Tips")
    for tip in logic_tips:
        st.write("- " + tip)

    st.subheader("🤖 AI-Generated Tips")
    st.write(ai_tip)
    if len(ai_tip.split()) < 5:
        st.warning("🤖 The AI response seems too short. Try different inputs or run again.")
