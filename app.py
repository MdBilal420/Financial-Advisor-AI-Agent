
import os
import streamlit as st


from lyzr_agent_api.client import AgentAPI
from lyzr_agent_api.models.environment import EnvironmentConfig, FeatureConfig
from lyzr_agent_api.models.agents import AgentConfig
from lyzr_agent_api.models.chat import ChatRequest


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


def getAdvice():
    agent_config = AgentConfig(
    env_id= environment["env_id"],  
    system_prompt="Act like an experienced financial advisor with 20 years of expertise in wealth management, retirement planning, and investment strategies. Your clients range from individuals to small business owners seeking guidance on optimizing their financial health. Provide comprehensive, step-by-step advice that takes into account both short-term needs and long-term goals.",
    name="Financial Advisor Agent",
    agent_description="This agent provides expert financial guidance, offering tailored strategies for wealth management, retirement planning, and investment growth.",
    )
    agent = client.create_agent_endpoint(json_body=agent_config)
    print("AGENT",agent)
    response = client.chat_with_agent(
        json_body=ChatRequest(
            user_id="user-id",
            agent_id=agent["agent_id"],
            message="What are the best investment strategies for balancing short-term liquidity needs with long-term wealth growth?",
            session_id="session-id",
        )
    )
    return response

# print("RESPONSE",response)

result=[]
with st.form("my_form"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.text_input("income: ")

    with col2:
        st.text_input("Expenses: ")

    with col3:
        st.text_input("Savings: ")

    with col4:
        st.text_input("Debt: ")
    
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

    
    submitted = st.form_submit_button("Submit")
    if submitted:
        with st.spinner("Wait, please. I am working on it..."):
            result.append(getAdvice())


if(len(result)):
    st.markdown(result[0]["response"])
