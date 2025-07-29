import os
from langchain_huggingface import HuggingFaceEndpoint

os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

llm = HuggingFaceEndpoint(
    repo_id="google/flan-t5-large",
    task="text2text-generation",
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    temperature=0.1,
    max_new_tokens=50
)

test_input = "What is the capital of France?"
output = llm.invoke(test_input)

print("Model output:", output)
