
import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from openai import OpenAI

load_dotenv()

# ---------------- CONFIGURATION ----------------

st.set_page_config(
    page_title="HR Handbook - RRF",
    page_icon="📘"
)

st.title("📘 HR Handbook Chatbot")
st.subheader("Hybrid Search using RRF")

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

MODEL = "openai/gpt-4o-mini"


# ---------------- PDF EXTRACTION ----------------

def extract_pdf(pdf):

    reader = PdfReader(pdf)

    text = ""

    for page_num, page in enumerate(
        reader.pages, start=1
    ):

        page_text = page.extract_text()

        if page_text:
            text += (
                f"\n[Page {page_num}]\n"
                + page_text
            )

    return text


# ---------------- CHUNKING ----------------

def chunk_text(
    text,
    chunk_size=100,
    overlap=10
):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ---------------- KEYWORD INDEX ----------------

def build_keyword_index(chunks):

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    vectors = vectorizer.fit_transform(
        chunks
    )

    return vectorizer, vectors


# ---------------- SEMANTIC INDEX ----------------

@st.cache_resource
def get_embedding_model():

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


def build_semantic_index(chunks):

    model = get_embedding_model()

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True
    )

    return embeddings


# ---------------- KEYWORD SEARCH ----------------

def keyword_search(
    query,
    vectorizer,
    vectors,
    top_k=5
):

    query_vector = vectorizer.transform(
        [query]
    )

    scores = cosine_similarity(
        query_vector,
        vectors
    )[0]

    ranked = scores.argsort()[::-1]

    return [
        int(i)
        for i in ranked
        if scores[i] > 0
    ][:top_k]


# ---------------- SEMANTIC SEARCH ----------------

def semantic_search(
    query,
    embeddings,
    top_k=5
):

    model = get_embedding_model()

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )

    scores = cosine_similarity(
        query_embedding,
        embeddings
    )[0]

    ranked = scores.argsort()[::-1]

    return [
        int(i)
        for i in ranked[:top_k]
    ]


# ---------------- RRF ----------------

def reciprocal_rank_fusion(
    rankings,
    k=60
):

    scores = {}

    for ranking in rankings:

        for rank, doc_id in enumerate(
            ranking, start=1
        ):

            scores[doc_id] = (
                scores.get(doc_id, 0)
                + 1 / (k + rank)
            )

    return sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )


# ---------------- HYBRID RETRIEVAL ----------------

def retrieve(
    query,
    chunks,
    vectorizer,
    keyword_vectors,
    embeddings,
    top_k=4
):

    keyword_results = keyword_search(
        query,
        vectorizer,
        keyword_vectors,
        top_k=10
    )

    semantic_results = semantic_search(
        query,
        embeddings,
        top_k=10
    )

    combined = reciprocal_rank_fusion(
        [
            keyword_results,
            semantic_results
        ]
    )

    return [
        {
            "text": chunks[doc_id],
            "score": score,
            "id": doc_id
        }
        for doc_id, score in combined[:top_k]
    ]


# ---------------- LLM ANSWER ----------------

def generate_answer(query, context):

    prompt = f"""
You are an HR Handbook Assistant.

Answer only using the context below.
Do not invent HR policies.

If the answer is unavailable, say:
"The HR handbook does not specify this."

Context:
{context}

Question:
{query}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


# ---------------- STREAMLIT UI ----------------

uploaded_pdf = st.file_uploader(
    "Upload HR Handbook PDF",
    type="pdf"
)

if uploaded_pdf:

    if st.button("Build RRF Index"):

        with st.spinner("Processing PDF..."):

            text = extract_pdf(uploaded_pdf)

            chunks = chunk_text(text)

            vectorizer, keyword_vectors = (
                build_keyword_index(chunks)
            )

            embeddings = build_semantic_index(
                chunks
            )

            st.session_state.chunks = chunks
            st.session_state.vectorizer = vectorizer
            st.session_state.keyword_vectors = (
                keyword_vectors
            )
            st.session_state.embeddings = embeddings

            st.session_state.ready = True

            st.success(
                f"Index built! {len(chunks)} chunks"
            )


if st.session_state.get("ready"):

    query = st.text_input(
        "Ask a question about the HR Handbook"
    )

    top_k = st.slider(
        "Number of retrieved chunks",
        1, 10, 4
    )

    if st.button("Search and Generate Answer"):

        results = retrieve(
            query,
            st.session_state.chunks,
            st.session_state.vectorizer,
            st.session_state.keyword_vectors,
            st.session_state.embeddings,
            top_k
        )

        context = "\n\n".join(
            item["text"]
            for item in results
        )

        st.subheader("Retrieved Chunks")

        for item in results:

            st.write(
                f"Chunk {item['id']} | "
                f"RRF Score: {item['score']:.4f}"
            )

            st.write(item["text"])

        answer = generate_answer(
            query,
            context
        )

        st.subheader("HR Assistant Answer")

        st.write(answer)
