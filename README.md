# smartHireSearch
large language model based project for a client improve current hiring process
<img width="786" alt="image" src="https://github.com/fjing1/smartHireSearch/assets/32583955/d8f577aa-1408-46b1-ba26-df9909dbc6d9">

# Target users
The system is aimed at serving three primary user groups:
Recruiters: Seeking efficient tools for managing and matching a high volume of candidates and job openings and ensuring high-quality matches to reduce time-to-hire.
Job Seekers: Desiring timely responses and higher engagement rates from recruiters.

# Project Motivation：Project Motivation:
A recruitment agency already has a pool of candidates while fetching numerous job openings from sites like LinkedIn, Indeed, and Glassdoor. The agency is seeking to enhance the efficiency of its recruitment team by providing high-quality candidates to improve the match to job openings, thereby optimizing the recruitment process.


# Metrics

## For Recruiters:
Time-to-Screen
Sum of all screening times / Number of applications screened
Lower: indicates more efficient screening,  recruitment team is quickly evaluating incoming applications
Interview Success Rate:
Number of Candidates Interviewed / Number of Candidates Matched
Higher: indicates an effective matching process
Number of new Job Seeker

## For Job Seekers:
Application Response Rate:
Number of applications responded to / Total number of applications
Higher: indicates better responsiveness
Time-to-Respond:
Sum of all response times / Number of applications responded to
Lower: indicates faster communication
Interview Rate:
Number of interviews secured / Total number of applications 
Higher: indicates better match quality and effective communication

## Secondary Metrics - Time-to-Hire:
Average Time-to-Hire
Sum of all time-to-hire / Number of hires 
Lower: more efficient hiring process
Hiring Success Rate:
Number of Candidates Hired / Number of Candidates Interviewed 
Higher: indicates an effective filtering during interviews
Number of Candidates Hired
Higher: indicates an effective filtering during interviews
First-Year Retention Rate:
Number of hires still employed after one year / Total number of hires one year ago 
Higher: effective recruitment and onboarding


# Data

## Using -Apify (scraper)
Data Collection:
Job Descriptions:
Source: Scrape data from job sites like LinkedIn
Method: Utilize a web scraper like Apify to automate the collection of job descriptions.
Resumes and User Preferences:
Source: Directly from job seekers through a web frontend
Method: Provide a user-friendly interface for job seekers to submit their resumes and preferences.

Data Storage:
Location: Store the collected data in a cloud-based environment, utilizing AWS services.

Databases:
SQL Database: Use for structured data, ensuring efficient querying and management.
Elasticsearch (NoSQL): Employ for unstructured or semi-structured data like job descriptions and resumes, benefiting from its full-text search capabilities and scalability.


ETL/ELT Pipeline:
Job Description Pipeline: Schedule API calls to collect job descriptions, perform transformations (flattening, cleanup), and save the processed data into the database.
Resume Pipeline: Triggered by user upload, summarize resumes, store raw data in S3, and processed data in the database.
Matching Algorithm Pipeline: Extract and process data from resumes and job descriptions using a language model, and then send notifications based on matches. This can be triggered either on a schedule or initiated by the user.

# Solution
Automated Screening: Implement systems with LLMs to automatically screen resumes and portfolios, shortlisting candidates by their qualifications, experience, and role suitability. Job-candidate matching algorithms can incorporate factors like working style, preferred company culture, and career aspirations.
Learning from Feedback: Implement LLMs that can learn from successful hires and feedback from employers and job seekers to continually improve the matching accuracy.


# Architecture Diagram
<img width="900" alt="image" src="https://github.com/fjing1/smartHireSearch/assets/32583955/389d0044-ec30-4e61-94dc-faa0fd6a6b19">


# Cost Estimation
Cost Estimation

After discussion, we assume 100 job seekers, 1 job description. The average tokens for a job seeker resume profile is 1000 tokens, job description is 2000 tokens. Thus, one match cost 100 * 1000 + 2000 = 102k tokens. We approximately to 100k tokens for GPT4 API, as we searched the cost will be around the cost is  USD $0.01 per 1,000 token. Therefore, for 100,000 input tokens, the cost would be $1.00. 
We estimate everyday, we have an average 1000 new job posts. Thus the daily cost is 1000$. 
For the output, we expect ranking results per job post.
Output token cost is $0.01 per 1,000 token. Output cost per job post is less than 1000 token, but for convenience, we say it cost 0.01$ 


