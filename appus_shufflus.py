import streamlit as st
import pandas as pd
import random
import math
import os
from PIL import Image

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="Image Reveal Quiz",
    layout="centered"
)

st.title("🧩 Image Reveal Quiz")
st.write(
    "Answer questions correctly to reveal parts of a hidden image. "
    "Score **75% or higher** to reveal the complete image. **Max 3 attempts.**"
)

# -------------------------------------------------
# Configuration & File Paths
# -------------------------------------------------
# These files must exist in the same GitHub folder as this script
CSV_PATH = "questions.csv"
IMAGE_PATH = "hidden_image.jpg"

@st.cache_data
def load_data(csv_path):
    if os.path.exists(csv_path):
        # Expected format: Question, Choice1, Choice2, Choice3, Choice4, Answer
        return pd.read_csv(
            csv_path,
            header=None,
            names=["Question", "choice1", "choice2", "choice3", "choice4", "answer"]
        )
    return None

@st.cache_resource
def load_image(img_path):
    if os.path.exists(img_path):
        return Image.open(img_path).convert("RGB")
    return None

# -------------------------------------------------
# Data Loading Logic
# -------------------------------------------------
questions_df = load_data(CSV_PATH)
image = load_image(IMAGE_PATH)

if questions_df is None or image is None:
    st.error("⚠️ Error: Required files not found!")
    st.info(f"Please ensure '{CSV_PATH}' and '{IMAGE_PATH}' are in your GitHub repository.")
    st.stop()

# -------------------------------------------------
# Main Logic
# -------------------------------------------------
total_questions = len(questions_df)

# ---- Near-square grid calculation ----
cols = math.ceil(math.sqrt(total_questions))
rows = math.ceil(total_questions / cols)

img_width, img_height = image.size
tile_width = img_width // cols
tile_height = img_height // rows

if tile_width < 10 or tile_height < 10:
    st.error("The image is too small for this many questions. Use a larger image.")
    st.stop()

# -------------------------------------------------
# Initialize session state
# -------------------------------------------------
if "iteration" not in st.session_state:
    st.session_state.iteration = 1

if "shuffled_questions" not in st.session_state:
    # 1. Shuffle the order of the questions
    shuffled_indices = list(range(total_questions))
    random.shuffle(shuffled_indices)
    
    reordered_questions = []
    for idx in shuffled_indices:
        row = questions_df.iloc[idx]
        
        # 2. Shuffle the choices for THIS specific question
        choices = [row["choice1"], row["choice2"], row["choice3"], row["choice4"]]
        random.shuffle(choices)
        
        reordered_questions.append({
            "Question": row["Question"],
            "Choices": choices,
            "Correct": row["answer"]
        })
        
    st.session_state.shuffled_questions = reordered_questions

    # Initialize image tiles
    tiles = []
    for r in range(rows):
        for c in range(cols):
            left = c * tile_width
            upper = r * tile_height
            right = left + tile_width
            lower = upper + tile_height
            tiles.append(image.crop((left, upper, right, lower)))

    random.shuffle(tiles)

    st.session_state.tiles = tiles
    st.session_state.revealed = [False] * len(tiles)
    st.session_state.q_index = 0
    st.session_state.correct = 0
    st.session_state.completed = False

# -------------------------------------------------
# Helper: Display grid
# -------------------------------------------------
def show_grid():
    idx = 0
    for _ in range(rows):
        columns = st.columns(cols)
        for c in range(cols):
            if idx < len(st.session_state.tiles):
                if st.session_state.revealed[idx]:
                    columns[c].image(st.session_state.tiles[idx], use_container_width=True)
                else:
                    placeholder = Image.new("RGB", (tile_width, tile_height), (160, 160, 160))
                    columns[c].image(placeholder, use_container_width=True)
            idx += 1

# -------------------------------------------------
# Quiz UI
# -------------------------------------------------
if not st.session_state.completed:
    st.info(f"Attempt: {st.session_state.iteration} / 3")
    show_grid()
    st.divider()

    current_q = st.session_state.shuffled_questions[st.session_state.q_index]

    st.subheader(f"Question {st.session_state.q_index + 1} of {total_questions}")
    st.write(current_q["Question"])

    choice = st.radio(
        "Select an answer:",
        current_q["Choices"],
        index=None,
        key=f"q_{st.session_state.q_index}_iter_{st.session_state.iteration}"
    )

    if st.button("Submit Answer"):
        if choice == current_q["Correct"]:
            st.success("✅ Correct!")
            st.session_state.correct += 1

            # Find a random tile that isn't revealed yet
            hidden_tiles = [i for i, r in enumerate(st.session_state.revealed) if not r]
            if hidden_tiles:
                reveal_index = random.choice(hidden_tiles)
                st.session_state.revealed[reveal_index] = True
        else:
            st.error(f"❌ Incorrect. The correct answer was: {current_q['Correct']}")

        st.session_state.q_index += 1
        if st.session_state.q_index >= total_questions:
            st.session_state.completed = True
        st.rerun()

else:
    score = st.session_state.correct / total_questions
    st.subheader("✅ Quiz Complete")
    st.write(f"Final score: **{st.session_state.correct} / {total_questions}** ({score * 100:.1f}%)")

    if score >= 0.75:
        st.success("🎉 Congratulations! The image is fully revealed.")
        st.image(image, use_container_width=True)
        st.balloons()
    else:
        st.warning("Score below 75%. The image remains partially hidden.")
        show_grid()

    if st.session_state.iteration < 3:
        if st.button(f"Start Attempt {st.session_state.iteration + 1}"):
            next_iter = st.session_state.iteration + 1
            # Clear specific keys to reset the quiz loop
            for key in ["shuffled_questions", "tiles", "revealed", "q_index", "correct", "completed"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.iteration = next_iter
            st.rerun()
    else:
        st.error("Maximum attempts (3) reached.")
        if st.button("Reset Entire App"):
            st.session_state.clear()
            st.rerun()
