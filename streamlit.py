import streamlit as st
import pandas as pd
# CHANGED: Import 'Spread' and 'Client'
from gspread_pandas import Spread, Client 
from gspread import service_account_from_dict
import gspread # Ensure gspread is imported
import json

# --- CORRECTED CREDENTIALS LOADING ---
try:
    service_account_str = st.secrets["gcp_service_account"]
    creds_dict = json.loads(service_account_str) 
    scoped_creds = service_account_from_dict(creds_dict)
except (KeyError, json.JSONDecodeError) as e:
    st.error(f"Error with Google Sheets credentials: {e}. Please check your secrets.toml file.")
    st.stop()

# --- CORRECTED FUNCTIONS ---

# The corrected function to submit data
def submit_to_leaderboard(name, score):
    try:
        # Use the 'scoped_creds' object for authentication
        spread = Spread(
            st.secrets["spreadsheet_name"], 
            creds=scoped_creds # CHANGED: Use the processed credentials object
        )
        data = pd.DataFrame([{"Name": name, "Score": score}])
        # Append data to the sheet starting at the next empty row, without headers
        # This assumes you have a header row ("Name", "Score") in your sheet already
        spread.df_to_sheets(data, index=False, headers=False, start='A2', replace=False)
        st.success("Your score has been added to the leaderboard!")
    except Exception as e:
        st.error(f"Error submitting to leaderboard: {e}")

# The corrected function to load data
@st.cache_data
def load_leaderboard_data():
    try:
        # Use the 'scoped_creds' object for authentication
        spread = Spread(
            st.secrets["spreadsheet_name"], 
            creds=scoped_creds # CHANGED: Use the processed credentials object
        )
        df = spread.sheet_to_df(index=False, header_rows=1)
        # Ensure the 'Score' column is numeric for correct sorting
        if 'Score' in df.columns:
            df['Score'] = pd.to_numeric(df['Score'], errors='coerce')
        return df
    except Exception as e:
        st.warning(f"Could not load leaderboard data. Error: {e}")
        return pd.DataFrame(columns=["Name", "Score"])
        
# --- PAGE 1: INTRODUCTION AND DONATION CALL TO ACTION ---

def show_intro_page():
    st.title("Kandersteg Trivia Challenge! 🏔️")
    st.header("Help send our scout group to Switzerland!")
    # NOTE: Ensure this image URL is publicly accessible or upload it with your repo.
    st.image("https://raw.githubusercontent.com/Kim2783/Kandersteg/main/scouts%20jpeg.jpg", caption="Help send us to Kandersteg!")

    st.write("""
    Welcome to the Kandersteg Trivia Challenge! To help our scouts fund their trip to the amazing Kandersteg International Scout Centre in Switzerland, we're asking for a small donation to participate in this fun quiz.
    
    Test your knowledge of scouting, Switzerland, and Kandersteg, and see if you can make it to the top of our leaderboard!
    """)
    
    st.info("Donations are handled through a secure PayPal link managed by the scout group. Your contribution is greatly appreciated!")

    paypal_link = "https://www.paypal.com/donate?campaign_id=UJM5RGT9FMXGN" # Cleaned link
    st.markdown(f'<a href="{paypal_link}" target="_blank"><button style="background-color:#0070ba;color:white;border-radius:5px;border:none;padding:10px 20px;font-size:16px;">Donate and Start the Quiz!</button></a>', unsafe_allow_html=True)
    
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


# --- PAGE 2: THE QUIZ ITSELF ---

def show_quiz_page():
    st.title(f"Good Luck, {st.session_state.player_name}!")
    st.subheader("Quiz Time!")

    questions = [
        {"question": "What country is Kandersteg located in?", "options": ["Germany", "Switzerland", "France", "Austria"], "answer": "Switzerland"},
        {"question": "What is the highest peak in the Swiss Alps?", "options": ["Mont Blanc", "Matterhorn", "Monte Rosa", "Jungfrau"], "answer": "Monte Rosa"},
        # Add more questions here...
    ]
    
    # Check if the quiz is finished
    if st.session_state.current_question >= len(questions):
        st.session_state.quiz_completed = True
        st.title("Quiz Finished! 🎉")
        st.write(f"Your final score is: **{st.session_state.score} / {len(questions)}**")
        st.write("Congratulations! Thank you for playing and supporting our trip.")
        
        # Submit the score to the leaderboard
        submit_to_leaderboard(st.session_state.player_name, st.session_state.score)
        
        if st.button("Play Again"):
            st.session_state.quiz_started = False
            st.rerun()
        return # Stop executing the rest of the function

    # Display the current question
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

# --- THE LEADERBOARD PAGE ---

def show_leaderboard():
    st.markdown("---")
    st.subheader("Leaderboard 🏆")
    
    df = load_leaderboard_data()
    
    if not df.empty:
        # Sort by score (descending), then by name (ascending)
        df_sorted = df.sort_values(by=["Score", "Name"], ascending=[False, True])
        st.dataframe(df_sorted.reset_index(drop=True))
    else:
        st.write("No scores have been submitted yet. Be the first to play!")

# --- MAIN APP LOGIC ---

# Initialize session state variables
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False

# Control the page flow
if not st.session_state.quiz_started:
    show_intro_page()
    show_leaderboard() # Show leaderboard on the intro page as well
else:
    if not st.session_state.quiz_completed:
        show_quiz_page()
    else:
        # After quiz is done, show the final score and leaderboard
        st.success("Your score has been submitted!")
        show_leaderboard()
        if st.button("Go to Start Page"):
            st.session_state.quiz_started = False
            st.session_state.quiz_completed = False
            st.rerun()
