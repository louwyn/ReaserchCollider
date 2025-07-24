import streamlit as st
import pandas as pd
import json
import openai
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os


# Fetch the OpenAI API key from environment variables
# Retrieve the key
api_key = st.secrets["OPENAI_API_KEY"]

# (Optional) expose it as an env‑var for libraries that auto‑detect it
os.environ["OPENAI_API_KEY"] = api_key

from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
)

# Check if the OpenAI API key is set
if api_key:
    print("OpenAI API key is set")
else:
    print("OpenAI API key is not set")


# --- Resource Loading Function ---
# Cache the resource loading to avoid reloading on every run.
@st.cache_resource
def load_resources():
    # Load the CSV file with professor metadata.
    csv_file = 'Data.csv'
    df = pd.read_csv(csv_file)
    # Create a full name column.
    df['name'] = df['First Name:'] + ' ' + df['Last Name:']
    # Create a CV key column.
    df['cv_key'] = df['name'] + " CV.pdf"
    # Build metadata DataFrame.
    metadata_columns = ['name', 'WashU Email Address:', 'School:', 'Department:', 'Title:']
    professors_metadata = df[metadata_columns].copy()

    # Load the JSON file containing CV texts.
    json_file = 'combined.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    # Map each professor's cv_key to its corresponding CV text.
    cv_series = df['cv_key'].map(cv_data).fillna("")
    professors_metadata['cv'] = cv_series

    # Filter for professors with non-empty CV text.
    df_nonempty = professors_metadata[professors_metadata['cv'] != ""]
    df_nonempty = pd.DataFrame(df_nonempty)

    # Define a text spliter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,           # ~½-1 page
        chunk_overlap=200          # keeps context
    )

    # Create a Document for each professor's CV (with metadata).
    documents = []
    for idx, row in df_nonempty.iterrows():
        metadata = {
            "name": row['name'],
            "WashU Email Address:": row['WashU Email Address:'],
            "School:": row['School:'],
            "Department:": row['Department:'],
            "Title:": row['Title:']
        }

        # Split the CV and keep the metadata on every chunk
        for chunk in text_splitter.split_text(str(row["cv"])):
            documents.append(Document(page_content=chunk, metadata=metadata))

    # Build the vector store using FAISS (cloud-compatible)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    
    # Create FAISS vector store from documents
    vectorstore = FAISS.from_documents(documents, embeddings)

    # Build the retriever based on the vectorstore
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 10}  # Return top 10 most similar documents
    )

    # Set up the LLM.
    llm = ChatOpenAI(model = "gpt-4o")

    return retriever, llm

# Load resources once.
retriever, llm = load_resources()


# --- Similarity Search Function ---
def search_research(query):
    results = retriever.invoke(query)

    # 👇 keep only the first chunk we see for each professor
    unique = {}
    for doc in results:
        name = doc.metadata["name"]
        if name not in unique:        # first (i.e., most-similar) chunk wins
            unique[name] = doc
        if len(unique) == 10:      # stop once we have enough unique profs
            break
    results = list(unique.values())


    output_lines = []
    output_lines.append(f"Research Query: {query}\n")
    output_lines.append("Matching Professors:\n")
    for i, doc in enumerate(results, start=1):
        metadata = doc.metadata
        output_lines.append(f"Result {i}:")
        output_lines.append("Name: " + metadata.get("name", "N/A"))
        output_lines.append("WashU Email Address: " + metadata.get("WashU Email Address:", "N/A"))
        output_lines.append("School: " + metadata.get("School:", "N/A"))
        output_lines.append("Department: " + metadata.get("Department:", "N/A"))
        output_lines.append("Title: " + metadata.get("Title:", "N/A"))
        output_lines.append("-" * 40)

        # Extract the professor's CV (adjust length as needed)
        snippet = doc.page_content[:8290]
 
        # Create the prompt for the LLM.
        prompt = (
            f"Research Query: '{query}'.\n"
            f"Professor: {metadata.get('name', 'N/A')}.\n"
            f"CV Snippet: {snippet}\n\n"
            "Based on the research query and the attached CV above, please provide a short summary "
            "explaining why this professor was selected, highlighting how the CV content matches "
            "the research interests. Focus on the positives and the matching components."
        )
        # Generate the summary using the LLM.
        result = llm.invoke(prompt)
        summary = result.content if hasattr(result, "content") else result
        output_lines.append("Summary:")
        output_lines.append(summary)
        output_lines.append("=" * 40 + "\n")
    return "\n".join(output_lines)




st.markdown(
    """
    <style>
    .custom-heading {
        color: #89CFF0;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
    }
    .custom-paragraph {
        color: #89CFF0;
        font-size: 1.2rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 class='custom-heading'>Research Collider</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p class='custom-paragraph'>Find Professors with Matching Research Interests in the Association of Chinese Professors(ACP) at WashU</p>",
    unsafe_allow_html=True
)



# Text box for the search query.
query = st.text_area("Specify the expertise you are looking for (At least 20 words):", "Find biomedical imaging researcher exploring optical coherence tomography photonic chip development heart organoid analysis ultrafast noninvasive 3D imaging innovations platform. 
")

min_words = 20

# When the button is clicked, perform the search.
if st.button("Search"):
    if not query:
            st.error("Please enter a search query.")
    elif len(query.split()) < min_words:
            st.warning(
                f"Query too short. Please provide at least {min_words} words "
            )
    elif len(query.split()) >= min_words:
        with st.spinner("Searching..."):
            finalresults = search_research(query)
            
            filter_prompt = PromptTemplate.from_template(
            """
            You are matching a user's research inquiry to a list of researchers.

            • Carefully read the inquiry and each researcher's portfolio.  
            • Keep a researcher **only if** their expertise meaningfully aligns with the inquiry.  
            • Return the portfolios of the selected researchers **exactly as-is** (no edits).  

            User inquiry:
            {query}

            Researchers' portfolios:
            {finalresults}
            """
            )


            #invoke the chain
            filtered_output = (filter_prompt | llm).invoke(
               {"query": query, "finalresults": finalresults}      # key matches {results}
            )
            
            display_text = (
                filtered_output.content          # ChatOpenAI / ChatMessage object
                if hasattr(filtered_output, "content")
                else str(filtered_output)        # fallback for plain-string LLMs
            )

                        
            st.text_area("Results", display_text, height=600)
    else:
        st.error("Please enter a search query.")
