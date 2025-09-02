import streamlit as st
import pandas as pd
from gspread_pandas import Spread, Client
from gspread import service_account_from_dict
import gspread
import json

# --- 1. LOAD AND PARSE SECRETS ---
# This block runs first to get the credentials.
try:
    service_account_str = st.secrets["gcp_service_account"]
    creds_dict = json.loads(service_account_str)
    scoped_creds = service_account_from_dict(creds_dict)
except (KeyError, json.JSONDecodeError) as e:
    st.error(f"Error with Google Sheets credentials: {e}. Please check your secrets.toml file.")
    st.stop()

# --- 2. CREATE THE CLIENTS (GLOBAL SCOPE) ---
# These clients are created once in the main script body.
# All functions below can now see and use them.
try:
    # CHANGED: Use the modern gspread.Client constructor
    gspread_client = gspread.Client(auth=scoped_creds)
    
    gspread_pandas_client = Client(gspread_client)
except Exception as e:
    st.error(f"Failed to authorize Google Sheets client: {e}")
    st.stop()

# --- 3. DEFINE FUNCTIONS ---

def submit_to_leaderboard(name, score):
    """Submits a new score to the Google Sheet."""
    try:
        # Use the globally defined client to open the spreadsheet.
        spread = gspread_pandas_client.open(st.secrets["spreadsheet_name"])
        data = pd.DataFrame([{"Name": name, "Score": score}])
        # Append data to the sheet without headers.
        spread.df_to_sheets(data, index=False, headers=False, start='A2', replace=False)
        st.success("Your score has been added to the leaderboard!")
    except Exception as e:
        st.error(f"Error submitting to leaderboard: {e}")

@st.cache_data(ttl=60) # Cache the data for 60 seconds
def load_leaderboard_data():
    """Loads leaderboard data from the Google Sheet."""
    try:
        # Use the globally defined client to open the spreadsheet.
        spread = gspread_pandas_client.open(st.secrets["spreadsheet_name"])
        df = spread.sheet_to_df(index=False, header_rows=1)
        if 'Score' in df.columns:
            df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.warning(f"Could not load leaderboard data. Error: {e}")
        return pd.DataFrame(columns=["Name", "Score"])

def show_intro_page():
    """Displays the intro page and the name input form."""
    st.title("Kandersteg Trivia Challenge! 🏔️")
    st.header("Help send our scout group to Switzerland!")
    st.image("https://raw.githubusercontent.com/Kim2783/Kandersteg/main/scouts%20jpeg.jpg", caption="Help send us to Kandersteg!")

    st.write("""
    Welcome to the Kandersteg Trivia Challenge! To help our scouts fund their trip, we're asking for a small donation to participate in this fun quiz. Test your knowledge and see if you can make it to the top of our leaderboard!
    """)
    st.info("Donations are handled through a secure PayPal link. Your contribution is greatly appreciated!")

    paypal_link = "https://www.paypal.com/donate?campaign_id=UJM5RGT9FMXGN"
    st.link_button("Donate and Start the Quiz!", paypal_link)

    st.markdown("---")
    st.write("Already donated? Enter your name below to play!")

    with st.form("name_form"):
        player_name = st.text_input("Enter your name to play:", key="player_name_input")
        start_button = st.form_submit_button("Start Quiz")
        if start_button and player_name:
            st.session_state.player_name = player_name
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.quiz_completed = False
            st.rerun()

def show_quiz_page():
    """Displays the quiz questions and handles scoring."""
    st.title(f"Good Luck, {st.session_state.player_name}!")

    questions = [
        {"question": "What country is Kandersteg located in?", "options": ["Germany", "Switzerland", "France", "Austria"], "answer": "Switzerland"},
        {"question": "What is the highest peak in the Swiss Alps?", "options": ["Mont Blanc", "Matterhorn", "Monte Rosa", "Jungfrau"], "answer": "Monte Rosa"},
    ]

    if st.session_state.current_question >= len(questions):
        st.session_state.quiz_completed = True
        submit_to_leaderboard(st.session_state.player_name, st.session_state.score)
        st.rerun()

    q = questions[st.session_state.current_question]
    st.write(f"**Question {st.session_state.current_question + 1}:** {q['question']}")

    with st.form(key=f"q_form_{st.session_state.current_question}"):
        user_answer = st.radio("Choose your answer:", q['options'], key=f"radio_{st.session_state.current_question}")
        submit_answer = st.form_submit_button("Submit Answer")
        if submit_answer:
            if user_answer == q['answer']:
                st.session_state.score += 1
                st.success("Correct!")
            else:
                st.error(f"Incorrect. The correct answer was: {q['answer']}")
            st.session_state.current_question += 1
            st.rerun()

def show_leaderboard():
    """Displays the sorted leaderboard."""
    st.subheader("Leaderboard 🏆")
    df = load_leaderboard_data()
    if not df.empty:
        df_sorted = df.sort_values(by=["Score", "Name"], ascending=[False, True])
        st.dataframe(df_sorted.reset_index(drop=True))
    else:
        st.write("No scores have been submitted yet. Be the first to play!")

# --- 4. MAIN APP LOGIC ---

# Initialize session state variables
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False

# Control the page flow
if not st.session_state.quiz_started:
    show_intro_page()
    show_leaderboard()
elif st.session_state.quiz_completed:
    st.title("Quiz Finished! 🎉")
    st.write(f"Your final score is: **{st.session_state.score}**")
    st.write("Thank you for playing and supporting our trip!")
    show_leaderboard()
    if st.button("Play Again"):
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.rerun()
else:
    show_quiz_page()
