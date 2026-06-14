"""
Run this ONCE to upload career data to Azure AI Search.
"""
import pandas as pd
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType,
    SearchableField
)
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()

# Your Azure AI Search details
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")

# Get your Search Admin Key:
# portal.azure.com → AI Search → careercompass-search → Keys → Primary admin key
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")

INDEX_NAME = "careers"

# Step 1: Create search index
index_client = SearchIndexClient(SEARCH_ENDPOINT, AzureKeyCredential(SEARCH_KEY))

fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="title", type=SearchFieldDataType.String),
    SearchableField(name="description", type=SearchFieldDataType.String),
    SearchableField(name="skills", type=SearchFieldDataType.String),
    SimpleField(name="code", type=SearchFieldDataType.String),
]

index = SearchIndex(name=INDEX_NAME, fields=fields)
index_client.create_or_update_index(index)
print("✅ Index created")

# Step 2: Upload career data from O*NET CSV
df = pd.read_excel("onet_careers.xlsx", engine="openpyxl")
print(f"Loaded {len(df)} careers")

documents = []
for i, row in df.head(100).iterrows():  # Upload first 100 careers
    documents.append({
        "id": str(i),
        "title": str(row.get("Title", "")),
        "description": str(row.get("Description", "")),
        "skills": str(row.get("Skills", "programming, analysis, communication")),
        "code": str(row.get("O*NET-SOC Code", ""))
    })

# Upload to search
search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
result = search_client.upload_documents(documents)
print(f"✅ Uploaded {len(documents)} careers to knowledge base")