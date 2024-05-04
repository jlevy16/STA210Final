# STA210Final
This is the repository for my STA210 Final Project

For this project, I design a web scraping application that allows me to collect job data. In total, I collected around 20,000 entries. After removing all incomplete, faulty, and duplicate data, I was left with 7,000 relevant entries. Unfortunately, GitHub would not allow me to use this CSV file because of its size. Here is the dataset if you are interested: https://drive.google.com/file/d/14Gx2Ct4VTxE5MnpD7PRUu-JTK45ilrpD/view?usp=sharing

The issue with this data, however, is that the more interesting parameters (required level of education, required experience, required skills, domain, etc) are not easily extricable from this dataset. Instead, they are embedded in lengthy text based job descriptions that have no standard for formatting. I tried to implement a variety of basic NLP methodologies to reliably extract these data points (sentiment analysis, named entity recognition, regex, etc), but each of them were insufficient, and seemed to introduce a form of bias in their preference to certain companies job description formatting. 

To combat this issue, I manually extracted around 120 of these features from the dataset, and used this to fine tune a language model (GPT-3.5), which proved far more reliable in terms of extraction.

I wanted to go outside of the scope of STA210 to explore the process of procuring a dataset, as this seemed quite interesting to me and was more relevant to my concentration in machine learning. 

Unfortunately, this took me an extremely long time, and ultimately left me with little to no time at all for the analysis. I think that there was much more interesting information to be extracted from the data, and regardless will analyze and update this project just for my own sake. 

Also, for reference, I have been having a github issue where nothing will push following my work on a ECE661 final project. I am trying to resolve this, but it cost me my ability to make periodic meaningful commits for this assingment, and for this I appologize. I learned that I was able to upload files directly, which allowed me to get this done, but it was not ideal as now I have no history for me to review and reference in the future. 
