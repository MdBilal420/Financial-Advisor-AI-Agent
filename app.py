
import os
import streamlit as st


from lyzr_agent_api.client import AgentAPI
from lyzr_agent_api.models.environment import EnvironmentConfig, FeatureConfig


from lyzr_automata import Agent,Task
from lyzr_automata.pipelines.linear_sync_pipeline import LinearSyncPipeline
from lyzr_automata.ai_models.openai import OpenAIModel

import requests
from bs4 import BeautifulSoup
import re
import json

from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())

lyzr_api_key = os.getenv("LYZR_API_KEY", "")
openai_api_key = os.getenv("OPENAI_API_KEY", "")
serper_api_key = os.getenv("SERPER_API_KEY","")



st.set_page_config(
    page_title = "Lyzr Advyzr"
)


if not openai_api_key:
    openai_api_key = st.sidebar.text_input("Enter your OpenAI API key:", type="password")

if not lyzr_api_key:
    lyzr_api_key = st.sidebar.text_input("Enter your Lyzr API key:", type="password")

if not serper_api_key:
    serper_api_key = st.sidebar.text_input("Enter your Serper API key:", type="password")

client = AgentAPI(x_api_key=lyzr_api_key)

environment_config = EnvironmentConfig(
    name="Lyzr_Advyzr",
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
            "temperature": 0.2,
            "top_p": 0.9,
        },
        "env":{
                "OPENAI_API_KEY": openai_api_key
            }},
)

environment = client.create_environment_endpoint(json_body=environment_config)

os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

st.title("Lyzr Advyzr")
st.write("Personalized Investment Portfolio Advisor using Lyzr's API.")
open_ai_text_completion_model = OpenAIModel(
    api_key=openai_api_key,
    parameters={
        "model":"gpt-4-turbo-preview",
        "temperature":0.2,
        "max_tokens":1500
    }
)

def searchWeb(query):
    url = "https://google.serper.dev/search"

    payload = json.dumps({  # Convert dict to JSON string
        "q": query,
        "gl": "in"
    })

    headers = {
        "X-API-KEY": serper_api_key,
        "Content-Type": "application/json"
    }

    response = requests.post(  # Use post() directly instead of request()
        url=url,
        headers=headers,
        data=payload
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return []

    try:
        res = response.json()
        return [it.get('link') for it in res.get('organic', [])]
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []


def parseURL(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, features="html.parser")

        textContent = re.sub(r'\s{4,}','   ',soup.get_text())
        return textContent
    except requests.exceptions.RequestException as e:
        print(f"Error URL not working {url}:{e}")
        return ""

def researchData(query):
    result = searchWeb(query)
    data = []
    for i in result:
        print("URL+++",i)
        target_domains = {"smallcase", "mstock", "screener", "groww","etmoney"} 
        if any(domain in i.lower() for domain in target_domains):
            parsed_data = parseURL(i)
            data.append(parsed_data)
    return data[:6]


    
def extractData(text):
    try:
        truncated_text = ""
        if isinstance(text, type([])):  # Alternative: isinstance(text, list)
            truncated_text = ' '.join(text[:6])[:4000]
        else:
            truncated_text = str(text)[:4000]

        analyst_agent = Agent(
            role="analyst",
            prompt_persona=f"""you are an expert analyst and you have to find out the list of companies from {truncated_text} along with their some financial details in tabular format."""
        )

        task1 = Task(
            name="stock analysis",
            model=open_ai_text_completion_model,
            agent=analyst_agent,
            instructions=f"""Analyse the list of companies from {truncated_text} along with their some financial details in tabular format. 
            Do not write any extra details just the name on of the companies is enough."""
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


def get_investment_amount(income, expenses, savings, debt):
    try:
        available_for_investment = income - expenses- savings - debt

        # Ensure the investment amount is non-negative
        investment_amount = max(0, available_for_investment)

        return investment_amount

    except Exception as e:
        print(f"Error: {e}")
        return None


def fund_allocation(list,riskTolerance,timeline,investment,financial_goal):
    try:
        print("FUND",list,riskTolerance,timeline,investment,financial_goal)

        analyst_agent = Agent(
            role="wealth investor",
            prompt_persona=f"""Act like an experienced financial advisor with 20 years of expertise in wealth management, retirement planning, and investment strategies. Your clients range from individuals to small business owners seeking guidance on optimizing their financial health. Provide comprehensive, step-by-step advice that takes into account both {riskTolerance} and {timeline} needs."""
        )

        task1 = Task(
            name="Wealth investment",
            model=open_ai_text_completion_model,
            agent=analyst_agent,
            instructions=f"""You are an experienced investment advisor specializing in portfolio optimization. 
            Your task is to distribute a given {investment} amount across these {list} of companies based on the following inputs:
    {riskTolerance}: Adjust allocations to balance between high-risk and low-risk companies.
    {timeline}: Optimize the allocation for short-term or long-term growth.
    {financial_goal}: Prioritize stability, income generation, or aggressive growth as specified.
    Ensure the distribution is diversified, aligns with financial best practices,in rupees and maximizes the likelihood of achieving the {financial_goal}. Provide clear percentages and amount for allocation to each company and justify your reasoning
            """
        )

        output = LinearSyncPipeline(
            name="Fund Manager",
            completion_message="Fund Allocated",
            tasks=[
                task1
            ]
        ).run()
        return output[0]['task_output']

    except Exception as e:
        print(f"Error: {e}")
        return None



result=[]
list = []
investment = ''

col1, col2, col3, col4 = st.columns(4)
income = 0
expenses = 0 
savings = 0 
debt = 0
with col1:
    income_str = st.text_input("Income: ")
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
    
financial_goal =  st.text_input("Financial goal: ")
col5, col6 = st.columns(2)
with col5:
    riskTolerance = st.selectbox("Risk tolerance?",
    ("conservative", "moderate", "aggressive"),
    )
with col6:    
    timeline = st.selectbox("Timeline?",
    ("short-term", "medium-term",  "long-term"),
    )



marketTrends = st.button("Get Latest Market Trends")
if marketTrends:
    print("D++++",riskTolerance,timeline)
    with st.spinner("Wait, please. Fetching latest trends and opportunities..."):
        query = f"What are the best {timeline} stocks with {riskTolerance} risk currently ?"
        text = researchData(query)
        list.append(extractData(text))
if(len(list)):
    investment = get_investment_amount(income, expenses, savings, debt)
    if(investment > 0):
        st.success(f'{investment} is the amount that can be invested', icon="✅")
    else:
        st.warning('There is no amount left to invest', icon="⚠️")
    allocation = fund_allocation(list,riskTolerance,timeline,investment,financial_goal)
    if(allocation):
        st.markdown(allocation)
