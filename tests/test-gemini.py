from google import genai

client = genai.Client(
    vertexai=True,
    project="capstone-project-479414",
    location="us-central1",
)

resp = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say 'hello from Vertex AI'",
)

print(resp.text)
