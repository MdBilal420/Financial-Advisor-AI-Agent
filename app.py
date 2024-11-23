
import os
import streamlit as st


from lyzr_agent_api.client import AgentAPI
from lyzr_agent_api.models.environment import EnvironmentConfig, FeatureConfig
from lyzr_agent_api.models.agents import AgentConfig
from lyzr_agent_api.models.chat import ChatRequest

from lyzr_automata import Agent,Task
from lyzr_automata.pipelines.linear_sync_pipeline import LinearSyncPipeline
from lyzr_automata.ai_models.openai import OpenAIModel

import requests
from bs4 import BeautifulSoup
import re


from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

lyzr_api_key = os.getenv("LYZR_API_KEY", "")
openai_api_key = os.getenv("OPENAI_API_KEY", "")

client = AgentAPI(x_api_key=lyzr_api_key)

environment_config = EnvironmentConfig(
    name="Test Environment",
    features=[
        FeatureConfig(
            type="SHORT_TERM_MEMORY",
            config={},          
            priority=0,
        )
    ],
    tools=[],
    llm_config={
        "provider": "openai",
        "model": "gpt-4o-mini",
        "config": {
            "temperature": 0.5,
            "top_p": 0.9,
        },
        "env":{
                "OPENAI_API_KEY": openai_api_key
            }},
)

environment = client.create_environment_endpoint(json_body=environment_config)

st.set_page_config(
    page_title = "Investment Advisor Agent"
)


if not openai_api_key:
    openai_api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")

os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

st.title("Investment Advisor Agent")
st.write("Personalized Investment Portfolio Advisor using Lyzr's API.")
open_ai_text_completion_model = OpenAIModel(
    api_key=openai_api_key,
    parameters={
        "model":"gpt-4-turbo-preview",
        "temperature":0.2,
        "max_tokens":1500
    }
)

def get_investment_amount(income, expenses, savings, debt):
    try:
        available_for_investment = income - expenses- savings - debt

        # Ensure the investment amount is non-negative
        investment_amount = max(0, available_for_investment)

        return investment_amount

    except Exception as e:
        print(f"Error: {e}")
        return None


def getAdvice():
    agent_config = AgentConfig(
    env_id= environment["env_id"],  
    system_prompt="Act like an experienced financial advisor with 20 years of expertise in wealth management, retirement planning, and investment strategies. Your clients range from individuals to small business owners seeking guidance on optimizing their financial health. Provide comprehensive, step-by-step advice that takes into account both short-term needs and long-term goals.",
    name="Financial Advisor Agent",
    agent_description="This agent provides expert financial guidance, offering tailored strategies for wealth management, retirement planning, and investment growth.",
    )
    agent = client.create_agent_endpoint(json_body=agent_config)
    
    response = client.chat_with_agent(
        json_body=ChatRequest(
            user_id="user-id",
            agent_id=agent["agent_id"],
            message="What are the best investment amount for balancing short-term liquidity needs with long-term wealth growth?",
            session_id="session-id",
        )
    )
    return response

def parseURL():
    url = "https://www.screener.in/screens/515361/largecaptop-100midcap101-250smallcap251/"
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, features="html.parser")

        textContent = re.sub(r'\s{4,}','   ',soup.get_text())
        return textContent
    except requests.exceptions.RequestException as e:
        print(f"Error URL not working {url}:{e}")
        return None
    
def extractData(text):
    try:
        analyst_agent = Agent(
            role="analyst",
            prompt_persona=f"""you are an expert analyst and you have to find out the list of companies from {text} along with their some financial details in tabular format."""
        )

        task1 = Task(
            name="stock analysis",
            model=open_ai_text_completion_model,
            agent=analyst_agent,
            instructions=f'Analyse the list of companies from {text} along with their some financial details in tabular format'
        )

        output = LinearSyncPipeline(
            name="Analyst Pipeline",
            completion_message="List fetched",
            tasks=[
                task1
            ]
        ).run()
        return output[0]['task_output']
    except requests.exceptions.RequestException as e:
        print(f"Error URL not working {url}:{e}")
        return None

result=[]
list = []
investment = ''
with st.form("personal_finance"):
    col1, col2, col3, col4 = st.columns(4)
    income = 0
    expenses = 0 
    savings = 0 
    debt = 0
    with col1:
        income_str = st.text_input("income: ")
        income = float(income_str) if income_str.strip() else 0

    with col2:
        expenses_str = st.text_input("Expenses: ")
        expenses = float(expenses_str) if expenses_str.strip() else 0

    with col3:
        savings_str = st.text_input("Savings: ")
        savings = float(savings_str) if savings_str.strip() else 0

    with col4:
        debt_str = st.text_input("Debt: ")
        debt = float(debt_str) if debt_str.strip() else 0
    
    print("Details", income, expenses, savings, debt)
    submitted = st.form_submit_button(
        "Get investing amount ?"
    )

    if submitted:
        print("Details=====>", income, expenses, savings, debt)
        with st.spinner("Wait, please. I am working on it..."):
            investment = get_investment_amount(income, expenses, savings, debt)
            if(investment > 0):
                st.success(f'{investment} is the amount that can be invested', icon="✅")
            else:
                st.warning('There is no amount left to invest', icon="⚠️")

    
st.text_input("Financial goals: ")
col5, col6 = st.columns(2)
with col5:
    riskTolerance = st.selectbox("Risk tolerance?",
    ("conservative", "moderate", "aggressive"),
    )
with col6:    
    timeline = st.selectbox("Risk tolerance?",
    ("short-term", "medium-term",  "long-term"),
    )


marketTrends = st.button("Get Latest Market Trends")
if marketTrends:
    with st.spinner("Wait, please. Fetching latest trends and opportunities..."):
        text = parseURL()
        list.append(extractData(text))

# if(len(result)):
#     st.markdown(result[0]["response"])

if(len(list)):
    st.markdown(list[0])
