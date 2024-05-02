import os
import openai
from openai import OpenAI
import time
import pandas as pd
import random
import subprocess
import re
import ast
import time
import backoff 
import tiktoken

class TokenRateLimiter:
    def __init__(self, tokens_per_minute):
        self.tokens_per_minute = tokens_per_minute
        self.max_tokens = tokens_per_minute
        self.available_tokens = tokens_per_minute
        self.last_check = time.time()

    def add_tokens(self):
        now = time.time()
        elapsed = now - self.last_check
        self.available_tokens += (self.tokens_per_minute / 60) * elapsed
        self.available_tokens = min(self.available_tokens, self.max_tokens)
        self.last_check = now

    def wait_for_tokens(self, tokens_needed):
        self.add_tokens()
        while self.available_tokens < tokens_needed:
            time.sleep(1)
            self.add_tokens()

    def consume_tokens(self, tokens_used):
        self.available_tokens -= tokens_used

TOKENS_PER_MINUTE = 80000  # Example token rate limit
rate_limiter = TokenRateLimiter(TOKENS_PER_MINUTE)
os.environ["OPENAI_API_KEY"] = "SECRET KEY"

openai.api_key = "SECRET KEY"
encoder = tiktoken.encoding_for_model("gpt-4")
client = OpenAI()

relevance_prompt = """You are a highly detailed and accurate AI trained to analyze job descriptions and identify if they are in the field of environmental engineering, specifically related to climate innovation and solutions for improving human and ecological health. This includes, but is not limited to, areas like air quality, water conservation, carbon footprint analysis, waste management, and sustainable design.

**Project Objective**: Determine if a job description is related to environmental engineering, focusing on roles that would benefit from a Master of Engineering in Climate and Sustainability Engineering.

**Input**: A raw, unstructured job description text.

**Output**: A JSON string indicating the job's relevance to environmental engineering ('true', 'false', or 'maybe') and the exact Reference Text(s) from the job description that supports your determination. Include a 'maybe' category for ambiguous cases with a note on what information is lacking.

**Instructions**:
- Consider the overall context of the job description, not just isolated keywords.
- Include jobs that require skills or knowledge central to environmental engineering, even if not explicitly stated.
- Recognize related fields that focus on sustainability and environmental protection.
- For ambiguous cases, return 'maybe' and specify what additional information would clarify the job's relevance.

**Example Output**:
{
  "environ_checker": "true",
  "reference_text": "Seeking a Civil Engineer to develop solutions for water conservation and wastewater treatment projects... commitment to advancing climate resilience and ecological health."
}
Ensure your analysis is based solely on the provided text and do not infer or add information not present in the job description.
"""

relevance_tokens = context_tokens = len(encoder.encode(relevance_prompt))

@backoff.on_exception(backoff.expo, openai.RateLimitError)
def completion_with_backoff(**kwargs):
    tokens_needed = kwargs.get('max_tokens', 0) + context_tokens  # Estimate token usage
    rate_limiter.wait_for_tokens(tokens_needed)
    response = client.chat.completions.create(**kwargs)
    rate_limiter.consume_tokens(tokens_needed)  # Assume all tokens were used for simplicity
    return response

def relevance(description):
    model_choice = "gpt-3.5-turbo-0125"
    context_tokens = relevance_tokens + len(encoder.encode(description))
    if context_tokens > 16000:
        model_choice = "gpt-4-0125-preview"
    response = completion_with_backoff(
        model= model_choice,  # Choose the appropriate model
        messages=[
            {"role": "system", "content": relevance_prompt},
            {"role": "user", "content": description}
        ],  
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response_text = response.choices[0].message.content
    print(response_text)
    # Regular expression to extract keywords and ranking
    relevance_match = re.search(r'"environ_checker": "(.*?)"', response_text, re.DOTALL)
    relevance_ranking_match = re.search(r'"reference_text": "(.*?)"', response_text, re.DOTALL)
    relevance_requirements = relevance_match.group(1) if relevance_match else 'X'
    relevance_ranking = relevance_ranking_match.group(1) if relevance_ranking_match else 'X'

    return relevance_requirements, relevance_ranking

here = os.path.dirname(os.path.abspath(__file__))

input_csv = os.path.join(here, 'Extracted_after_education_traits.csv')  
output_csv = os.path.join(here, 'Final_extraction.csv')  
df = pd.read_csv(input_csv)

for index, row in df.iterrows():
    temp_description = row['Job_Description']
    temp_title = row['Job_Title']
    description = f"Job_Title: {temp_title} Job_Description: {temp_description}"
    start = time.time()
    relevancevar, relranking = relevance(description)
    df.at[index, 'environ_checker'] = str(relevancevar)
    df.at[index, 'reference_text'] = str(relranking)
    end = time.time()
    relevancetime = end - start
    print(relevancetime,'seconds to extract RELEVANCE requirements!')
    df.to_csv(output_csv, index=False)
    

