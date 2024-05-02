import re
import os
import time
import threading
import webbrowser
import requests
from PIL import Image, ImageTk
from sys import platform

import tkinter as tk
from tkinter import ttk
from tkinter import *

# Store data as a csv file written out
from csv import writer

# Assist with creating incremental timing for our scraping to seem more human
from time import sleep

# Dataframe stuff
import pandas as pd

# Random integer for more realistic timing for clicks, buttons and searches during scraping
from random import randint

# Threading:
from concurrent.futures import ThreadPoolExecutor, wait

from selenium import webdriver

# Starting/Stopping Driver: can specify ports or location but not remote access
from selenium.webdriver.chrome.service import Service as ChromeService

# Manages Binaries needed for WebDriver without installing anything directly
from webdriver_manager.chrome import ChromeDriverManager

# Allows searchs similar to beautiful soup: find_all
from selenium.webdriver.common.by import By

# Try to establish wait times for the page to load
from selenium.webdriver.support.ui import WebDriverWait

# Wait for specific condition based on defined task: web elements, boolean are examples
from selenium.webdriver.support import expected_conditions as EC

# Used for keyboard movements, up/down, left/right,delete, etc
from selenium.webdriver.common.keys import Keys

# Locate elements on page and throw error if they do not exist
from selenium.common.exceptions import NoSuchElementException, TimeoutException


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service


import io
import requests
from PIL import Image, ImageTk
import tkinter as tk
from sys import platform

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from random import randint
import pandas as pd
import numpy as np


def wait_for_captcha_solution(driver, captcha_css_selector):
    try:
        # Wait for the CAPTCHA element to be present
        captcha_present = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, captcha_css_selector))
        )
        print("CAPTCHA detected. Please solve the CAPTCHA to proceed.")
        # Wait for the CAPTCHA element to disappear (i.e., CAPTCHA solved manually)
        WebDriverWait(driver, 600).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, captcha_css_selector))
        )
        print("CAPTCHA solved. Continuing script execution.")
    except:
        # If the CAPTCHA doesn't appear or an error occurs, just proceed
        print("No CAPTCHA detected or an error occurred. Proceeding.")

def extract_salary_info(salary_str):
    # Convert non-string to string to ensure all operations can proceed
    salary_str = str(salary_str)
    
    salary_info = {
        'Salary_Low': np.nan,
        'Salary_High': np.nan,
        'Salary_Source': 'Employer' if '(Employer est.)' in salary_str else 'Glassdoor' if '(Glassdoor est.)' in salary_str else np.nan
    }

    # Proceed only if the salary string is not 'nan' (the string representation of NaN after conversion)
    if (salary_str != 'nan') and (salary_str != '-1'):
        # Remove unnecessary strings and prepare for float conversion
        clean_str = salary_str.replace('USD', '').replace('K', '*1000').replace('(Employer est.)', '').replace('(Glassdoor est.)', '').replace('Per Hour', '').strip()
        
        # Process salary range or single salary value
        if '-' in clean_str:
            salary_range = clean_str.split('-')
            salary_info['Salary_Low'] = eval(salary_range[0].strip())
            salary_info['Salary_High'] = eval(salary_range[1].strip())
        else:
            salary_info['Salary_Low'] = eval(clean_str)
            salary_info['Salary_High'] = salary_info['Salary_Low']
    return pd.Series(salary_info)

class GlassdoorScraperGUI:
    def __init__(self, root):
        self.root = root
        self.job_search_list= []

        self.root.title("Glassdoor Scraper")

        # Label and Text Entry for Search Query
        self.label = tk.Label(root, text="Enter the glassdoor.com search query you would like to scrape all listings for.\nFor necessary keywords use \" \"")
        self.label.pack()

        self.entry = tk.Entry(root, width=50)
        self.entry.pack()
        
        # Create a frame for the buttons
        button_frame = tk.Frame(root)

        # Create the buttons and add them to the frame
        self.submit_button = tk.Button(button_frame, text="Submit", command=self.add_search_query)
        self.scrape_button = tk.Button(button_frame, text="Scrape All", command=self.start_scraping)
        self.move_up = tk.Button(button_frame, text="Move Row Up", command=self.up)
        self.move_down = tk.Button(button_frame, text="Move Row Down", command=self.down)
        self.open_file = tk.Button(button_frame, text="View Data as HTML", command=self.openfile)


        # Pack the buttons into the frame
        self.submit_button.pack(side=tk.LEFT)
        self.scrape_button.pack(side=tk.LEFT)
        self.move_up.pack(side=tk.LEFT)
        self.move_down.pack(side=tk.LEFT)
        self.open_file.pack(side=tk.LEFT)

        # Pack the frame above the tree, centered horizontally
        button_frame.pack(side=tk.TOP, pady=(10, 0))

        # Create a Treeview for the grid
        self.columns = ("Search Query", "Status", "Total Results Displayed", "Total Results Available", "Total Listings Scraped", "Time to Scrape", "CSV File Path")
        self.tree = ttk.Treeview(root, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the treeview to update the scrollbar
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind('<ButtonRelease-1>', self.tree.selection())    

        self.scrapeList = []
        self.beenScraped = [
            "\"Title: Environmental\"",
            "\"Title: Geotechnical\"",
            "\"agricultural\"",
            "\"climate change\"",
            "\"Conservation\"",
            "\"ecological\"",
            "\"Energy Transition\"",
            "\"Environmental Impact\"",
            "\"Hydrologic\"",
            "\"pollution\"",
            "\"Waste Management\"",
            "\"Water Quality\"",
            "\"Natural Resources\"",
            "\"Environmental Science\"",
            "\"Hydrology\"",
            "\"Carbon Footprint\"",
            "\"earthquake\"",
            "\"hydroelectric\""
        ]

        self.scraping = False

    def down(self):
        rows = self.tree.selection()
        for row in reversed(rows):
            self.tree.move(row, self.tree.parent(row), self.tree.index(row) + 1)
            # Assuming the first element of 'values' is what's stored in scrapeList
            value = self.tree.item(row, 'values')[0]
            if value in self.scrapeList:
                i = self.scrapeList.index(value)
                if i < len(self.scrapeList) - 1:
                    self.scrapeList[i], self.scrapeList[i + 1] = self.scrapeList[i + 1], self.scrapeList[i]

    def up(self):
        rows = self.tree.selection()
        for row in rows:
            self.tree.move(row, self.tree.parent(row), self.tree.index(row) - 1)
            # Assuming the first element of 'values' is what's stored in scrapeList
            value = self.tree.item(row, 'values')[0]
            if value in self.scrapeList:
                i = self.scrapeList.index(value)
                if i > 0:
                    self.scrapeList[i], self.scrapeList[i - 1] = self.scrapeList[i - 1], self.scrapeList[i]

    def add_search_query(self):
        search_query = self.entry.get()
        self.search_query = search_query
        self.tree.insert('', tk.END, iid=search_query, values=(search_query, 'Unscraped','', '', '', '', ''))
        self.scrapeList.append(search_query)
        self.entry.delete(0, tk.END)
        self.tree.pack()

    def start_scraping(self):
        if self.scraping == False and len(self.scrapeList) != 0:
            # Start scraping in a separate thread
            scraping_thread = threading.Thread(target=self.run_scraper)
            scraping_thread.start()

    def run_scraper(self):
        self.scraping = True

        for search_query in self.scrapeList:
            done = False
            current_row = list(self.tree.item(search_query, 'values'))
            if current_row[1] == 'Unscraped':
                break
            done = True

        if done == True:
            print("Done!")
            return True
        
        current_row[1] = 'Scraping!'
        updated_row = tuple(current_row)
        self.tree.item(search_query, values=updated_row)

        options= webdriver.ChromeOptions()

        # Going undercover:
        options.add_argument("--incognito")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        #pagination_url = 'https://www.glassdoor.com/Job/{}-{}-jobs-SRCH_IL.0,13_IN1_KO14,30.htm'

        # for scraping past week / updating dataframe regularly use: &fromAge=7 after search query
        #start = time.time()

        #job_=search_query.replace(' ', '-')
        job_=search_query.replace(' ', '+')
        # job_=job_.replace('(', '%28')
        # job_=job_.replace(')', '%29')
        # job_=job_.replace(':', '%3A')

        search_location = 'united-states'
        jobfile=job_
        if "\"" in job_:
            jobfile = job_.replace("\"", "__")
        filename = f'glassdoor_job_data_{search_location}_engineer_{jobfile}.csv'
        filename = filename.replace(" ", "_").replace("/", "_").replace("\\", "_")

        if(len(self.beenScraped)!=0):
            processed_strings = ["-" + s.replace(" ", "+") for s in self.beenScraped]
            pastSearches = "+".join(processed_strings)
            pagination_url = 'https://www.glassdoor.com/Job/jobs.htm?sc.occupationParam=%28Title%3A+%22Engineer%22%29+AND+{}+{}'

            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                options=options)
            driver.get(pagination_url.format(job_,pastSearches))     
        else:
            pagination_url = 'https://www.glassdoor.com/Job/jobs.htm?sc.occupationParam=%28Title%3A+%22Engineer%22%29+AND+{}'

            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                options=options)
            driver.get(pagination_url.format(job_))     

        captcha_css_selector = "cf-challenge"
        wait_for_captcha_solution(driver, captcha_css_selector)
        try:
            driver.minimize_window()
        except: 
            driver.set_window_position(-2000, 0)
        sleep(randint(2, 6))
        
        # calculate total number of entries given by glassdoor
        try:
            numTotal = driver.find_element(By.CLASS_NAME, 'SearchResultsHeader_jobCount__12dWB').text
            num = re.findall(r'\d+', numTotal.replace(',', ''))
            numTotal = int(num[0]) if num else None
        except Exception as e:
            print("Error finding total number of jobs:", e)
            numTotal = 0
        shortenedResults = (numTotal > 900)
        current_row = list(self.tree.item(search_query, 'values'))
        current_row[2] = numTotal
        updated_row = tuple(current_row)
        self.tree.item(search_query, values = updated_row)

        #load all entries and count actual number available to us (max is 900)
        #counter to help resolve bugged out load more button
        
        jobs = driver.find_elements(By.CLASS_NAME, "JobsList_jobListItem__JBBUV")
        max_retry_clicks = 3  # Maximum number of retries for clicking the "Load more" button

        while True:
            try:
                load_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test="load-more"]'))
                )
                driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                
                retries = 0
                while retries < max_retry_clicks:
                    try:
                        load_more_button.click()
                        print("Clicked 'Load more'")
                        break  # Exit the retry loop on successful click
                    except (ElementClickInterceptedException, ElementNotInteractableException):
                        # Handle possible modals or overlays here
                        try:
                            driver.find_element(By.CLASS_NAME, "CloseButton").click()
                        except (NoSuchElementException, ElementNotInteractableException):
                            pass  # If no close button is found, ignore and retry click
                        
                        retries += 1
                        sleep(.5)  # Wait a bit before retrying to give time for any overlays to be handled

                if retries == max_retry_clicks:
                    print("Max retries reached, unable to click 'Load more'")
                    break

                WebDriverWait(driver, 10).until(lambda _: len(driver.find_elements(By.CLASS_NAME, "JobsList_jobListItem__JBBUV")) > len(jobs))
            except (TimeoutException, NoSuchElementException):
                print("No new jobs loaded or button clicked max times")
                break

            jobs = driver.find_elements(By.CLASS_NAME, "JobsList_jobListItem__JBBUV")
            print(f"New jobs fetched, count: {len(jobs)}")

        p = len(jobs)
        print(f"Total job listings loaded: {p}")

        current_row = list(self.tree.item(search_query, 'values'))
        current_row[3] = p
        updated_row = tuple(current_row)
        self.tree.item(search_query, values = updated_row)

        df = pd.DataFrame(columns = ['Job_Title', 'Job_Link', 'Job_ID', 'Company_Name', 'Location', 'Posted_Date', 'Salary','Salary_Low', 'Salary_High', 'Salary_Est', 'Salary_Type', 'Salary_Source', 'Job_Description',
           'Company-Size', 'Company-Founded', 'Company-Type', 'Company-Industry', 'Company-Sector', 'Company-Revenue'])
        
        start = time.time()


        job_index = 0
        while job_index < p-1:

            sleep(2)
            
            # Close any modal if present
            try:
                driver.find_element(By.CLASS_NAME, "ModalContainer").click()
            except NoSuchElementException:
                pass
            sleep(.1)

            try:
                driver.find_element(By.CLASS_NAME, "CloseButton").click()  # Clicking the X.
            except NoSuchElementException:
                pass

            # Process each job
            while job_index < p-1 and len(df.index) < p-1:
                job = jobs[job_index] 
                job_index += 1
                try:
                    driver.find_element(By.CLASS_NAME, "ModalContainer").click()
                except NoSuchElementException:
                    pass
                try:
                    driver.find_element(By.CLASS_NAME, "CloseButton").click()
                except NoSuchElementException:
                    pass
                try:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(job))
                    job.click()
                except Exception as e:
                    print("Error clicking the element:", e)
                sleep(1.5)
                collected_successfully = False

                salary_checker_count = 0
                while not collected_successfully:
                    try:
                        # Extract job details
                        try:
                            job_title = job.find_element(By.CLASS_NAME,"JobCard_jobTitle__rbjTE").text
                        except NoSuchElementException:
                            print("Job Title class name element has been updated. Check Glassdoor")
                        try:
                            job_link = job.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        except NoSuchElementException:
                            print("Job link class name element has been updated. Check Glassdoor")
                        try:
                            job_id = job.find_element(By.CSS_SELECTOR, "a").get_attribute("id")
                        except NoSuchElementException:
                            print("Job ID class name element has been updated. Check Glassdoor")
                        try:
                            location = job.find_element(By.CLASS_NAME,"JobCard_location__N_iYE").text
                        except NoSuchElementException:
                            print("Location class name element has been updated. Check Glassdoor")       
                        try:
                            company_name = job.find_element(By.CLASS_NAME,"EmployerProfile_employerName__8w0tV").text
                        except NoSuchElementException:
                            print("Company name class name element has been updated. Check Glassdoor")   
                        try:
                            posted_date = job.find_element(By.CLASS_NAME, "JobCard_listingAge__KuaxZ").text
                        except NoSuchElementException:
                            print("Posted date class name element has been updated. Check Glassdoor")
    

                        # Salary extraction logic
                        salary = '-1'  # Default value
                        
                        # if it cant find the salary, increase the counter by 1, if it can find it set it back to 0
                        try:
                            salary = job.find_element(By.CLASS_NAME, "JobCard_salaryEstimate___m9kY").text
                            salary_checker_count = 0
                        except NoSuchElementException:
                            salary_checker_count = salary_checker_count + 1
                            pass

                        # if it has been 10 salaries in a row that arent there, odds are the class name has been updated to prevent scraping in glassdoor
                        if(salary_checker_count>= 10):
                            print("There have been 10 entries in a row where you didnt get salary information... it seems the salary class name element has been updated. Check Glassdoor and update the code")
                        
                        # Extract job description
                        job_description = '-1' #default
                        
                        # Close any modal if present
                        try:
                            driver.find_element(By.CLASS_NAME, "ModalContainer").click()
                        except NoSuchElementException:
                            pass
                        sleep(.1)

                        try:
                            driver.find_element(By.CLASS_NAME, "CloseButton").click()  # Clicking the X.
                        except NoSuchElementException:
                            pass

                        try:
                            show_more_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, "JobDetails_showMore__j5Z_h"))
                            )
                            show_more_button.click()
                            time.sleep(1) 
                        except Exception as e:
                            print("Show more button not found or not clickable:", e)

                        # had to separate for cases in which there is no show more button, to still scrape with the same logic
                        try:
                            job_description_element = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".JobDetails_jobDescription__6VeBn"))
                            )
                            job_description = job_description_element.text
                        except Exception as e:
                            print("Failed to find job description element:", e)

                        
                        #Company info (default -1 again):
                        company_size = company_founded = company_type = company_industry = company_sector = company_revenue = '-1'

                        try:
                            # Find the company overview grid by class name
                            overview_grid = driver.find_element(By.CLASS_NAME, "JobDetails_companyOverviewGrid__CV62w")
                            
                            # Define labels to search for within the overview items
                            labels = {
                                "Size": "company_size",
                                "Founded": "company_founded",
                                "Type": "company_type",
                                "Industry": "company_industry",
                                "Sector": "company_sector",
                                "Revenue": "company_revenue",
                            }
                            
                            # Find all overview items by class name
                            overview_items = overview_grid.find_elements(By.CLASS_NAME, "JobDetails_overviewItem__35s2T")
                            
                            for item in overview_items:
                                # Extract label and value from each overview item
                                label_element = item.find_element(By.CLASS_NAME, "JobDetails_overviewItemLabel__5vi0o")
                                value_element = item.find_element(By.CLASS_NAME, "JobDetails_overviewItemValue__5TqNi")
                                label_text = label_element.text
                                value_text = value_element.text
                                
                                # Check if the label text is one of the specified labels
                                if label_text in labels:
                                    # Set the corresponding variable based on the label
                                    if label_text == "Size":
                                        company_size = value_text
                                    elif label_text == "Founded":
                                        company_founded = value_text
                                    elif label_text == "Type":
                                        company_type = value_text
                                    elif label_text == "Industry":
                                        company_industry = value_text
                                    elif label_text == "Sector":
                                        company_sector = value_text
                                    elif label_text == "Revenue":
                                        company_revenue = value_text
                                    
                        except NoSuchElementException:
                            # If the overview grid is missing, all overview details keep their default '-1'
                            pass
                        salary_details = extract_salary_info(salary)
                        salary_est = salary_type = '-1'
                        # save to DataFrame
                        df.loc[len(df)] = [job_title, job_link, job_id, company_name, location, posted_date, salary, salary_details['Salary_Low'], salary_details['Salary_High'], salary_est, salary_type, salary_details['Salary_Source'], job_description, company_size, company_founded, company_type, company_industry, company_sector, company_revenue]
                        collected_successfully = True

                        ##MIGHT HAVE ISSUES -- START
                        #Update number of jobs scraped in GUI
                        current_row = list(self.tree.item(search_query, 'values'))
                        current_row[4] = str(job_index)
                        updated_row = tuple(current_row)
                        self.tree.item(search_query, values = updated_row)
                        
                        current = time.time()
                        current_row = list(self.tree.item(search_query, 'values'))
                        current_row[5] = str(round((current - start)/60, 2))
                        updated_row = tuple(current_row)
                        self.tree.item(search_query, values = updated_row)
                    
                        #save after every page          
                        # Check if the file already exists
                        if os.path.exists(filename):
                            # Load the existing data
                            existing_df = pd.read_csv(filename)
                            # Combine old and new data
                            combined_df = pd.concat([existing_df, df], ignore_index=True)
                            # Save the combined data
                            combined_df.to_csv(filename, index=False)
                        else:
                            # Save new data
                            df.to_csv(filename, index=False)
                        
                        #clear dataframe
                        #clear dataframe
                        df = pd.DataFrame(columns = ['Job_Title', 'Job_Link', 'Job_ID', 'Company_Name', 'Location', 'Posted_Date', 'Salary','Salary_Low', 'Salary_High', 'Salary_Est', 'Salary_Type', 'Salary_Source', 'Job_Description',
           'Company-Size', 'Company-Founded', 'Company-Type', 'Company-Industry', 'Company-Sector', 'Company-Revenue'])
                        current_row = list(self.tree.item(search_query, 'values'))
                        current_row[6] = filename
                        updated_row = tuple(current_row)
                        self.tree.item(search_query, values = updated_row)

                        ## MIGHT HAVE ISSUES -- END
                            
                    except Exception as e:
                        print("Error in collecting job details:", e)
                
        driver.quit()
        current_row = list(self.tree.item(search_query, 'values'))
        current_row[1] = 'Done!'
        if not shortenedResults:
            self.beenScraped.append(search_query)
            print(self.beenScraped)
        self.scraping=False
        updated_row = tuple(current_row)
        self.tree.item(search_query, values = updated_row)
        self.start_scraping()

            
    def openfile(self):
        rows = self.tree.selection()
        for row in rows:
            filename = self.tree.item(row, 'values')[5]
            data = pd.read_csv(filename)
            html = data.to_html()
            path = os.path.abspath(filename.replace('csv','html'))
            url = 'file://' + os.path.abspath(os.getcwd()) + "/" + filename
            with open(path, 'w') as f:
                f.write(html)
            webbrowser.open(url)
            

def main():
    root = tk.Tk()
    root.title("Glassdoor Scraper")
    root.resizable(0, 0)
    app = GlassdoorScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
