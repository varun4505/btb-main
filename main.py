import os
from pathlib import Path
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv


# ---------- App & Model Setup ----------
st.set_page_config(
    page_title="AI Recipe Generator",
    page_icon="🍳",
    layout="centered",
)

load_dotenv()

# First try to get from env, otherwise ask user
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.warning("🔑 Please enter your API key to continue.")
    API_KEY = st.text_input("Enter your Gemini API Key:", type="password")

if not API_KEY:
    st.stop()

# Configure model
import google.generativeai as genai
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


load_dotenv()

# Be flexible: support both GEMINI_API_KEY and GOOGLE_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ Missing API key. Please add GEMINI_API_KEY (preferred) or GOOGLE_API_KEY to your .env file and restart the app.")
    st.stop()


load_dotenv()

# Be flexible: support both GEMINI_API_KEY and GOOGLE_API_KEY
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("❌ Missing API key. Add GEMINI_API_KEY (preferred) or GOOGLE_API_KEY to your .env file.")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# ---------- Helpers ----------
ASSETS_DIR = Path(__file__).with_name("assets")
PROMPT_FILE = Path(__file__).with_name("prompt.txt")

DEFAULT_PROMPT = (
    "You are a professional chef and helpful cooking assistant.\n"
    "Only generate real food recipes. Do not create metaphorical, abstract, or non-food content.\n\n"
    "Create a detailed food recipe using these ingredients: {{INGREDIENTS}}.\n"
    "{{NO_FLAME_BLOCK}}\n"
    "Include:\n"
    "- Recipe name\n"
    "- A brief description of the dish\n"
    "- Ingredients list with quantities\n"
    "- Step-by-step instructions\n"
    "- Estimated total time\n"
    "- Serving size\n\n"
    "If the ingredients do not seem like food items, respond with: \n"
    '"⚠️ These ingredients do not seem like typical food items. Please enter real culinary ingredients."\n'
)


def load_prompt_template() -> str:
    try:
        text = PROMPT_FILE.read_text(encoding="utf-8").strip()
        return text if text else DEFAULT_PROMPT
    except Exception:
        return DEFAULT_PROMPT


def build_prompt(ingredients: str, no_flame: bool) -> str:
    tpl = load_prompt_template()
    no_flame_block = (
        "IMPORTANT: Create ONLY no-flame recipes. Do not use any methods that require ovens, stoves, open flames, grilling, or gas.\n"
        "Use only raw/cold/no-cook, room-temperature preparations.\n"
        if no_flame
        else ""
    )
    return (
        tpl.replace("{{INGREDIENTS}}", ingredients)
        .replace("{{NO_FLAME_BLOCK}}", no_flame_block)
    )


# ---------- Session State ----------
if "generated_recipe" not in st.session_state:
    st.session_state.generated_recipe = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ---------- UI ----------
# Mobile responsive CSS
st.markdown("""
<style>
    /* Mobile responsive design */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1rem !important;
            max-width: 100% !important;
        }
        
        /* Make forms stack on mobile */
        .stColumns > div {
            min-width: 100% !important;
            margin-bottom: 1rem !important;
        }
        
        /* Adjust text areas for mobile */
        .stTextArea textarea {
            font-size: 16px !important; /* Prevents zoom on iOS */
            min-height: 120px !important;
        }
        
        /* Better button sizing on mobile */
        .stButton > button {
            width: 100% !important;
            padding: 0.75rem !important;
            font-size: 16px !important;
        }
        
        /* Adjust download button */
        .stDownloadButton > button {
            width: 100% !important;
            padding: 0.75rem !important;
            font-size: 14px !important;
        }
        
        /* Chat input adjustments */
        .stChatInput > div {
            width: 100% !important;
        }
        
        /* Title and text adjustments */
        h1 {
            font-size: 2rem !important;
            text-align: center !important;
        }
        
        h2, h3 {
            font-size: 1.5rem !important;
        }
        
        /* Info box adjustments */
        .stInfo {
            margin-bottom: 1rem !important;
        }
        
        /* Checkbox styling */
        .stCheckbox {
            margin-bottom: 1rem !important;
        }
    }
    
    /* Small mobile devices */
    @media (max-width: 480px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        h1 {
            font-size: 1.75rem !important;
        }
        
        /* Smaller margins on very small screens */
        .stMarkdown {
            margin-bottom: 0.5rem !important;
        }
    }
    
    /* Tablet adjustments */
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            max-width: 90% !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("🍲 AI Recipe Generator")
st.caption("Enter ingredients you have, choose options in the sidebar, and get a chef-crafted recipe.")

# ---------- Input Form ----------

# Use responsive columns - stack on mobile
is_mobile = st.container()
with is_mobile:
    # On mobile, this will stack vertically due to CSS
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("recipe_form", clear_on_submit=False):
            ingredients = st.text_area(
                "Ingredients",
                placeholder="e.g. chicken, rice, onions",
                help="Comma-separated list works great. Be as specific as you like!",
                height=100,
            )
            submitted = st.form_submit_button("Generate Recipe", use_container_width=True)

            if submitted:
                if ingredients and ingredients.strip():
                    prompt = build_prompt(ingredients.strip(), st.session_state.get("no_flame", False))
                    with st.spinner("Cooking up ideas..."):
                        try:
                            response = model.generate_content(prompt)
                            st.session_state.generated_recipe = response.text
                        except Exception as e:
                            st.error(f"Something went wrong while generating the recipe: {e}")
                else:
                    st.warning("Please enter some ingredients first.")

    with col2:
        st.info(
            "💡 **Tip:** Include quantities (e.g., '2 eggs, 1 cup rice') for more precise results."
        )
        st.checkbox("🚫 No cooking with fire/gas", key="no_flame")
        
        if st.session_state.generated_recipe:
            st.markdown("---")
            st.download_button(
                "📄 Download Recipe",
                data=st.session_state.generated_recipe,
                file_name="recipe.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ---------- Recipe Display ----------
if st.session_state.generated_recipe:
    st.markdown("---")
    st.subheader("Your Recipe")
    st.markdown(st.session_state.generated_recipe)


# ---------- Recipe Assistant Chat ----------
if st.session_state.generated_recipe:
    st.markdown("---")
    st.subheader("🤖 Recipe Assistant")
    st.caption("Ask questions about the recipe above. I'll keep answers short and focused.")

    # Display chat history (prefer chat_message if available)
    use_chat = hasattr(st, "chat_message")
    if use_chat:
        for question, answer in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                st.write(answer)
    else:
        for question, answer in st.session_state.chat_history:
            st.write(f"**You:** {question}")
            st.write(f"**Assistant:** {answer}")
            st.write("")

    # Chat input
    if use_chat:
        user_question = st.chat_input("Ask a question about the recipe…")
        ask_clicked = user_question is not None and user_question.strip() != ""
    else:
        user_question = st.text_input("Ask a question about the recipe:", key="chat_input")
        ask_clicked = st.button("Ask") and bool(user_question)

    if ask_clicked:
        with st.spinner("Thinking…"):
            chat_prompt = f"""
Based on this recipe:
{st.session_state.generated_recipe}

Please answer this question: {user_question}

Keep your answer helpful, concise, and related to the recipe. If the question is not related to cooking or the recipe, politely redirect to recipe-related topics.
"""
            try:
                chat_response = model.generate_content(chat_prompt)
                st.session_state.chat_history.append((user_question, chat_response.text))
                if not use_chat and "chat_input" in st.session_state:
                    del st.session_state["chat_input"]
                st.rerun()
            except Exception as e:
                st.error(f"Chat failed: {e}")

    cols = st.columns(2)
    if cols[0].button("Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    if cols[1].button("Clear Recipe", use_container_width=True):
        st.session_state.generated_recipe = ""
        st.session_state.chat_history = []
        st.rerun()
