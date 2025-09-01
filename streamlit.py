import streamlit as st

# --- Page 1: Introduction and Donation Call to Action ---

def show_intro_page():
    st.title("Kandersteg Trivia Challenge! 🏔️")
    st.header("Help send our scout group to Switzerland!")
    st.image("https://github.com/Kim2783/Kandersteg/blob/main/scouts%20jpeg.jpg", caption="Your scout group photo here.") # Use a relevant image!

    st.write("""
    Welcome to the Kandersteg Trivia Challenge! To help our scouts fund their trip to the amazing Kandersteg International Scout Centre in Switzerland, we're asking for a small donation to participate in this fun quiz.
    
    Test your knowledge of scouting, Switzerland, and Kandersteg, and see if you can make it to the top of our leaderboard!
    """)
    
    st.info("Donations are handled through a secure PayPal link managed by the scout group. Your contribution is greatly appreciated!")

    # This is the crucial part for payment redirection
    paypal_link = "https://www.paypal.com/donate?campaign_id=UJM5RGT9FMXGN&fbclid=IwY2xjawMi4whleHRuA2FlbQIxMQABHkMOASLwqaSCE8PFTEwRgbRhOWJF5Up2_mZqGfMqYL3uEOvjpji4RjQfuphV_aem_rzZ9uBUxPR5i_6RlkUBTcQ"
    st.markdown(f'<a href="{paypal_link}" target="_blank"><button style="background-color:#0070ba;color:white;border-radius:5px;border:none;padding:10px 20px;">Donate and Start the Quiz!</button></a>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.write("Already donated? Enter your name below to play!")

    # This form captures the user's name to identify them on the leaderboard
    with st.form("name_form"):
        player_name = st.text_input("Enter your name to play:")
        start_button = st.form_submit_button("Start Quiz")
        if start_button and player_name:
            st.session_state.player_name = player_name
            st.session_state.quiz_started = True
            st.session_state.current_question = 0
            st.session_state.score = 0
            st.session_state.quiz_completed = False
            st.experimental_rerun()


# --- Page 2: The Quiz Itself ---

def show_quiz_page():
    st.title(f"Welcome, {st.session_state.player_name}!")
    st.subheader("Quiz Time!")

    # A simple list of questions and answers. You can make this much more complex.
    questions = [
        {"question": "What country is Kandersteg located in?", "options": ["Germany", "Switzerland", "France", "Austria"], "answer": "Switzerland"},
        {"question": "What is the highest peak in the Swiss Alps?", "options": ["Mont Blanc", "Matterhorn", "Monte Rosa", "Jungfrau"], "answer": "Monte Rosa"},
        # Add more questions here...
    ]
    
    if st.session_state.current_question < len(questions):
        q = questions[st.session_state.current_question]
        st.write(f"**Question {st.session_state.current_question + 1}:** {q['question']}")
        
        # Use a form to handle the user's answer
        with st.form(key=f"q_form_{st.session_state.current_question}"):
            user_answer = st.radio("Choose your answer:", q['options'])
            submit_answer = st.form_submit_button("Submit Answer")

            if submit_answer:
                if user_answer == q['answer']:
                    st.success("Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"Incorrect. The correct answer was: {q['answer']}")
                st.session_state.current_question += 1
                st.experimental_rerun()
    else:
        st.session_state.quiz_completed = True
        st.title("Quiz Finished! 🎉")
        st.write(f"Your final score is: **{st.session_state.score} / {len(questions)}**")
        st.write("Congratulations! Thank you for playing and supporting our trip.")
        
        # This is where you would submit the score to the leaderboard
        submit_to_leaderboard(st.session_state.player_name, st.session_state.score)

# --- The Leaderboard Page ---

def show_leaderboard():
    st.markdown("---")
    st.subheader("Leaderboard 🏆")
    
    # Load and display the leaderboard data
    # This is the tricky part - see the next section for how to handle this.
    try:
        df = load_leaderboard_data()
        df.sort_values(by="Score", ascending=False, inplace=True)
        st.table(df) # Using st.table is simple and effective
    except FileNotFoundError:
        st.write("No scores have been submitted yet. Be the first to play!")

# --- Main App Logic ---

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
    
if not st.session_state.quiz_started:
    show_intro_page()
else:
    if not st.session_state.quiz_completed:
        show_quiz_page()
    else:
        show_intro_page() # Show the intro page again after completion
    
    show_leaderboard()
