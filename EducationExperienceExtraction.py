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


os.environ["OPENAI_API_KEY"] = "SECRET KEY"

openai.api_key = "SECRET KEY"
encoder = tiktoken.encoding_for_model("gpt-4")
client = OpenAI()

skills_prompt = "You are a detailed-oriented AI that specializes in analyzing job listings to identify specific required or desirable/preferred skills, experiences, and qualities and traits in the field of environmental engineering. Your analysis will guide the development of a master's program curriculum, ensuring it aligns with current industry demands. **Project Objective**: Extract specific skills, experiences, and qualities desired in candidates for environmental engineering roles. This data will assist in shaping a master's program that is relevant and valuable for students aspiring to enter the environmental engineering field with a Master’s degree. **Input**: A raw, unstructured text string containing a job description. Your task is to carefully analyze this text to identify and extract relevant information. **Output**: A JSON string presenting the extracted data, which includes a diverse range of skills, experiences, qualities, and traits sought by employers in the field. The output should also include an alignment rating. **YOUR JOB**: Identify and select key skills, experiences, traits, etc that are important for candidates applying to this environmental engineering role. This should be reflective of the actual requirements stated in the job description. Extract data that can be utilized for curriculum development and student guidance in professional settings. **Alignment Rating**: Include an alignment rating from 1 to 5, indicating how closely the extracted data aligns with the job description. A rating of 1 indicates poor alignment, while 5 indicates a direct and clear correspondence with the job description. **Example Output Formatting**: The output should be formatted as follows: { skills_and_qualities: [ ‘4 years of field experience in environmental consulting’, ‘Proficiency with Microsoft Office’, 'Proficiency in AutoCAD and/ or Microstation' ‘Experience in data management’, ‘Experience in technical report production’, ‘Knowledge of Advanced Environmental Assessment Techniques’, ‘Field data collection, processing and interpretation skills’, ‘Proficiency in Sustainable Design Principles’, ‘Effective Project Management Skills’, ‘Ability to produce a basic technical report’, ‘Proficient in Environmental Simulation Software’, ‘Ability to oversee subcontractors’, ‘Engineer in Training Certification (preferred)’, ‘Familiarity with environmental laws, regulations, compliance practices, and record-keeping requirements’, ‘Electronic inventory system usage skills’, ‘Experience from internship within discipline (Preferred)’], alignment_rating: 4 }. This output should strictly contain the relevant extracted data in the specified format, and should not include unnecessary words so it is easier to analyze this data. **Important**: Always provide authentic and accurate data based on the job description. Do not invent information. If certain information is not discernible, return ‘X’."
education_prompt = "You are a meticulous AI that analyzes raw job description text and extracts useful data regarding EDUCATION REQUIREMENTS to be returned as a JSON string that will be used in Python. You try as hard as you possibly can to ensure that the results you provide me with are as similar as possible to the text from which it came. **Project Objective**: Determine the required degree of education (bachelor's, master's, etc.) for a job given a text description of the job. **Input**: A raw, unstructured string that is the job description from which you will extract your data. Try as hard as you possibly can to ensure that the results you provide me with are as similar as possible to the text from which it came. If you cannot find any specified information return 'X' DO NOT MAKE THINGS UP. **Output**: A JSON string containing the educational requirements and the exact Reference Text from the job description that indicates these requirements. If the exact Reference Text is not present in the job description, return 'X' for the Reference Text. **YOUR JOB**: You will need to determine the educational requirements for the job listing, being: ‘No degree requirements,’ ‘Bachelor Preferred,’ ‘Bachelor Required,’ ‘Bachelors Required but Masters Preferred’, ‘Masters Required,’ or ‘Other.’ Extract the exact sentence or phrase (Reference Text) from the job description that indicates these requirements. It is incredibly important that this parameter is extracted as accurately and reliably as possible. Keep in mind that a master's is better than a bachelor's, so if a listing says 'bachelors or masters required' return 'Bachelor Required,' as we should consider the minimum requirements for the job. **Example Output Formatting**: For a job description that says ‘Required Qualifications: Bachelor’s Degree in Geotechnical Engineering, or closely related discipline. Minimum 3 years of relevant post-education work experience related to geotechnical engineering and foundation solution development. Engineer in Training Certification. Understanding of computer-based slope stability software. Willing to travel up to 20%. Preferred Qualifications: Master’s Degree in Engineering. Professional Engineer registration in Alaska or the ability to obtain within 18 months of employment. Experience with application of foundation capacity analysis in cold regions and permafrost ground conditions.’ with no other related information, the output should look like this: { education_requirements: ‘Bachelors Required but Masters Preferred’, reference_text: ‘Required Qualifications: Bachelor’s Degree in Geotechnical Engineering, or closely related discipline… Preferred Qualifications: Master’s Degree in Engineering.’ } and it should not include any other information or comments. **Important**: Double check your answer to ensure it is correct and then return just the JSON string containing the relevant data and nothing else. It is CRUCIAL that you never fabricate data. If information is missing, return X."
experience_prompt = "You are a meticulous AI that analyzes raw job description text and extracts useful data regarding YEARS OF EXPERIENCE REQUIREMENTS to be returned as a JSON string that will be used in Python. You try as hard as you possibly can to ensure that the results you provide me with are as similar as possible to the text from which it came. **Project Objective**: Determine the required number of years of experience (e.g., 0 for entry-level, 3-5 years, etc.) for a job given a text description of the job. **Input**: A raw, unstructured string that is the job description from which you will extract your data. Try as hard as you possibly can to ensure that the results you provide me with are as similar as possible to the text from which it came. If you cannot find any specified information return 'X' DO NOT MAKE THINGS UP. **Output**: A JSON string containing the years of experience requirements and the exact Reference Text from the job description that indicates these requirements. If the exact Reference Text is not present in the job description, return 'X' for the Reference Text. **YOUR JOB**: You will need to determine the experience requirements for the job listing, being numerical values with 0 being an entry level job with no experience requirements. Extract the exact sentence or phrase (Reference Text) from the job description that indicates these requirements. It is incredibly important that this parameter is extracted as accurately and reliably as possible. Keep in mind that if a listing says '3-5 years experience preferred,' return the lower number as we should consider the minimum requirements for the job. **Example Output Formatting**: For a job description that says ‘Required Qualifications: Bachelor’s Degree in Geotechnical Engineering. Minimum 3 years of relevant post-education work experience related to geotechnical engineering and foundation solution development. Engineer in Training Certification. Understanding of computer-based slope stability software. Willing to travel up to 20%. Preferred Qualifications: 5 years of experience in Engineering. Professional Engineer registration in Alaska or the ability to obtain within 18 months of employment. Experience with application of foundation capacity analysis in cold regions and permafrost ground conditions.’ with no other related information, the output should look like this: { years_of_experience: ‘3’, reference_text: ‘Minimum 3 years of relevant post-education work experience… Preferred Qualifications: 5 years of experience in Engineering.’ } and it should not include any other information or comments. **Important**: Double check your answer to ensure it is correct and then return just the JSON string containing the relevant data and nothing else. It is CRUCIAL that you never fabricate data. If information is missing, return X."

education_experience_prompt = """
You are a meticulous AI tasked with analyzing raw job description text to extract crucial data regarding both EDUCATION REQUIREMENTS and YEARS OF EXPERIENCE REQUIREMENTS, returning the results as a JSON string for use in Python. Your primary objectives are to determine the required educational degree (e.g., bachelor's, master's) and the necessary years of experience (e.g., 0 for entry-level, specific number of years) based on a job description. **Input**: A raw, unstructured string that is the job description. **Project Requirements**: 
1. If educational requirements are specified, extract and classify them as ‘No degree requirements,’ ‘Bachelor Preferred,’ ‘Bachelor Required,’ ‘Bachelors Required but Masters Preferred,’ ‘Masters Required,’ or ‘Other.’ If not specified, return 'X'.
2. For experience requirements, extract the minimum number of years required. If a range is provided, return the lower number. If not specified, return 'X'.
3. Ensure your outputs match the text as closely as possible. **Output**: A JSON string containing both the educational requirements and years of experience required, formatted as: 
{ "education_requirements": "<value>", "years_of_experience": "<value>" }.
If either information is missing from the job description, use 'X' for that value. **Example**: For a job description stating ‘Required Qualifications: Bachelor’s Degree in Geotechnical Engineering, or closely related discipline. Minimum 3 years of relevant post-education work experience. Preferred: Master’s Degree in Engineering.’, the output should be { "education_requirements": "Bachelors Required but Masters Preferred", "years_of_experience": "3" }. **Important**: Double check your answers for accuracy and reliability. Do not fabricate data.
"""


skills_tokens = context_tokens = len(encoder.encode(skills_prompt))
education_tokens = context_tokens = len(encoder.encode(education_prompt))
experience_tokens = context_tokens = len(encoder.encode(experience_prompt))
education_experience_tokens = context_tokens = len(encoder.encode(experience_prompt))


from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff
 
@backoff.on_exception(backoff.expo, openai.RateLimitError)
def completion_with_backoff(**kwargs):
    return client.chat.completions.create(**kwargs)
 
 

def skills(description):
    model_choice = "gpt-4"
    context_tokens = skills_tokens + len(encoder.encode(description))
    if context_tokens > 8000:
        model_choice = "gpt-4-1106-preview"
    response = completion_with_backoff(
        model= model_choice,  # Choose the appropriate model
        messages=[
            {"role": "system", "content": skills_prompt},
            {"role": "user", "content": description}
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response_text = response.choices[0].message.content
    print(response_text)
    # Regular expression to extract keywords and ranking
    skills_match = re.search(r'"skills_and_qualities": "(.*?)"', response_text, re.DOTALL)
    skills_ranking_match = re.search(r'"reference_text": "(.*?)"', response_text, re.DOTALL)
    skills_requirements = skills_match.group(1) if skills_match else 'X'
    skills_ranking = skills_ranking_match.group(1) if skills_ranking_match else 'X'

    return skills_requirements, skills_ranking



def education(description):
    model_choice = "gpt-4"
    context_tokens = education_tokens + len(encoder.encode(description))
    if context_tokens > 8000:
        model_choice = "gpt-4-1106-preview"
    response = completion_with_backoff(
        model = model_choice,  # Choose the appropriate model
        messages=[
            {"role": "system", "content": education_prompt},
            {"role": "user", "content": description}
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response_text = response.choices[0].message.content
    print(response_text)
    education_match = re.search(r'"education_requirements": "(.*?)"', response_text, re.DOTALL)
    education_ranking_match = re.search(r'"reference_text": "(.*?)"', response_text, re.DOTALL)
    education_requirements = education_match.group(1) if education_match else 'X'
    education_ranking = education_ranking_match.group(1) if education_ranking_match else 'X'
    
    return education_requirements, education_ranking


def experience(description):
    model_choice = "gpt-4"
    context_tokens = experience_tokens + len(encoder.encode(description))
    if context_tokens > 8000:
        model_choice = "gpt-4-1106-preview"
    response = completion_with_backoff(
        model = model_choice,  # Choose the appropriate model
        messages=[
            {"role": "system", "content": experience_prompt},
            {"role": "user", "content": description}
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response_text = response.choices[0].message.content
    print(response_text)
    experience_match = re.search(r'"years_of_experience": "(.*?)"', response_text, re.DOTALL)
    experience_ranking_match = re.search(r'"reference_text": "(.*?)"', response_text, re.DOTALL)
    experience_requirements = experience_match.group(1) if experience_match else 'X'
    experience_ranking = experience_ranking_match.group(1) if experience_ranking_match else 'X'
    
    return experience_requirements, experience_ranking


def education_experience(description):
    model_choice = "gpt-3.5-turbo-0125"
    context_tokens = education_experience_tokens + len(encoder.encode(description))
    if context_tokens > 16000:
        print("Input too long for model")
        return 
    response = completion_with_backoff(
        model = model_choice,  # Choose the appropriate model
        messages=[
            {"role": "system", "content": education_experience_prompt},
            {"role": "user", "content": description}
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    response_text = response.choices[0].message.content
    print(response_text)
    experience_match = re.search(r'"education_requirements": "(.*?)"', response_text, re.DOTALL)
    experience_ranking_match = re.search(r'"years_of_experience": "(.*?)"', response_text, re.DOTALL)
    experience_requirements = experience_match.group(1) if experience_match else 'X'
    experience_ranking = experience_ranking_match.group(1) if experience_ranking_match else 'X'
    
    return experience_requirements, experience_ranking





here = os.path.dirname(os.path.abspath(__file__))

input_csv = os.path.join(here, 'Non_EnvEng_data.csv')  # Replace with your CSV file name
output_csv = os.path.join(here, 'Final_Extraction_nonEnv_Parsed.csv')  # Replace with your CSV file name
df = pd.read_csv(input_csv)

df['education_requirements'] = df['education_requirements'].astype('object')
df['years_of_experience'] = df['years_of_experience'].astype('object')

start = time.time()
for index, row in df.iterrows():
    description = row['Job_Description']

    #start = time.time()
    #requirementsvar, rranking = skills(description)
    #df.at[index, 'skills_and_qualities'] = str(requirementsvar)
    #df.at[index, 'alignment_rating'] = str(rranking)
    #end = time.time()
    #skilltime = end - start
    #print(skilltime,'seconds to extract skills!')
    #if skilltime<25:
    #    time.sleep(25-skilltime)
    educationvar, eranking = education_experience(description)
    df.at[index, 'education_requirements'] = str(educationvar)
    df.at[index, 'years_of_experience'] = str(eranking)
    end = time.time()
    educationtime = end - start
    print('Trial ' + str(index) + ': ', educationtime,'seconds to extract educational and experience requirements!')
    df.to_csv(output_csv, index=False)
 
