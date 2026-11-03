
import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from openai import OpenAI

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

st.set_page_config(
    page_title="HR Guardrails",
    page_icon="🛡️"
)

st.title("🛡️ HR Handbook Chatbot")
st.subheader("Implementation using Guardrails")


client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openai/gpt-4o-mini"


# ---------------- PDF EXTRACTION ----------------

def extract_pdf(pdf):

    reader = PdfReader(pdf)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# ---------------- CHUNKING ----------------

def chunk_text(text, size=800, overlap=150):

    chunks = []

    start = 0

    while start < len(text):

        chunks.append(
            text[start:start + size].strip()
        )

        start += size - overlap

    return [
        chunk for chunk in chunks
        if chunk
    ]


# ---------------- INPUT GUARDRAIL ----------------

def validate_input(query):

    if not query.strip():

        return False, "Question cannot be empty."

    if len(query) > 1000:

        return False, "Question is too long."

    blocked_words = [
        "hack", "bomb", "kill", "attack"
    ]

    if any(
        word in query.lower()
        for word in blocked_words
    ):

        return False, "Unsafe input detected."

    return True, "Input accepted."


# ---------------- KEYWORD RETRIEVAL ----------------

def build_index(chunks):

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(
        chunks
    )

    return vectorizer, vectors


def retrieve(query, vectorizer, vectors, chunks):

    query_vector = vectorizer.transform(
        [query]
    )

    scores = cosine_similarity(
        query_vector,
        vectors
    )[0]

    best_index = scores.argmax()

    best_score = scores[best_index]

    if best_score <= 0:

        return [], best_score

    return [
        chunks[best_index]
    ], best_score


# ---------------- OUTPUT GUARDRAIL ----------------

def validate_output(answer):

    if not answer:

        return (
            "Unable to generate a response."
        )

    forbidden_phrases = [
        "ignore all previous instructions",
        "reveal confidential information"
    ]

    for phrase in forbidden_phrases:

        if phrase in answer.lower():

            return (
                "Response blocked by output "
                "validation."
            )

    return answer


# ---------------- LLM ----------------

def generate_answer(query, context):

    prompt = f"""
You are a professional HR policy assistant.

Rules:
- Answer only from the HR handbook context.
- Do not invent policy.
- Do not reveal confidential information.
- If the information is unavailable, say so.

Context:
{context}

Question:
{query}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content


# ---------------- UI ----------------


# ---------------- STREAMLIT UI ----------------

st.write(
    "Upload your HR Handbook PDF to begin."
)

uploaded_pdf = st.file_uploader(
    "Upload HR Handbook PDF",
    type="pdf"
)

if uploaded_pdf:

    st.success(
        f"PDF uploaded: {uploaded_pdf.name}"
    )

    if st.button("Build Index"):

        with st.spinner(
            "Step 1/3: Extracting text from PDF..."
        ):

            text = extract_pdf(uploaded_pdf)

        if not text.strip():

            st.error(
                "No text could be extracted. "
                "The PDF may be scanned or image-based."
            )

        else:

            st.info(
                f"Extracted {len(text):,} characters."
            )

            with st.spinner(
                "Step 2/3: Splitting document..."
            ):

                chunks = chunk_text(text)

            st.info(
                f"Created {len(chunks)} chunks."
            )

            with st.spinner(
                "Step 3/3: Building TF-IDF index..."
            ):

                vectorizer, vectors = build_index(
                    chunks
                )

                st.session_state.chunks = chunks
                st.session_state.vectorizer = vectorizer
                st.session_state.vectors = vectors

                st.session_state.ready = True

            st.success(
                "HR Handbook index successfully built!"
            )


# ---------------- QUESTION INTERFACE ----------------

if st.session_state.get("ready", False):

    st.divider()

    st.subheader("Ask your HR Handbook")

    query = st.text_input(
        "Enter your HR question"
    )

    if st.button("Ask HR Assistant"):

        valid, message = validate_input(query)

        if not valid:

            st.warning(message)

        else:

            with st.spinner(
                "Searching the HR Handbook..."
            ):

                chunks, score = retrieve(
                    query,
                    st.session_state.vectorizer,
                    st.session_state.vectors,
                    st.session_state.chunks
                )

            if not chunks or score < 0.05:

                st.warning(
                    "No relevant HR policy found. "
                    "Please try another question."
                )

            else:

                context = "\n\n".join(chunks)

                with st.spinner(
                    "Generating answer using OpenRouter..."
                ):

                    answer = generate_answer(
                        query,
                        context
                    )

                safe_answer = validate_output(
                    answer
                )

                st.subheader("HR Assistant Answer")

                st.write(safe_answer)

                with st.expander(
                    "View Retrieved Context"
                ):

                    st.write(context)
