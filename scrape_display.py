from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import pandas as pd
import time
import os, shutil
import json

master_df = pd.DataFrame()
# folder = "/Users/cat/Workspace/ren/test/Prices/"
folder = "./Prices/"

import os
from dotenv import load_dotenv

load_dotenv()

email = os.getenv('EMAIL')
passw = os.getenv("PASSW")

basket_str = os.getenv('BASKET')
basket = json.loads(basket_str)

metals_str = os.getenv("METALS_LIST")
metals_list = json.loads(metals_str)

download_path = os.getenv("DOWNLOAD_DIR")

def rm():
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)

def dl():
    rm()
    # os.makedirs(folder)

    time.sleep(5)
    url = 'https://ise-metal-quotes.com/'

    prefs = {
        "download.default_directory": f"{download_path}", # Set your directory path
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1 
    }

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)

    browser = webdriver.Chrome(options=options)
    

    browser.get(url)



    def accept_cookies():
        path_button = '#check-agb-en'
        browser.find_element(By.CSS_SELECTOR,path_button).click()
        path_accept = '#klaro > div > div > div.cm-modal.cm-klaro > div.cm-footer > div > button.cm-btn.cm-btn-success.cm-btn-info.cm-btn-accept'
        time.sleep(1)
        browser.find_element(By.CSS_SELECTOR,path_accept).click()
        time.sleep(1)
        
    accept_cookies()

    def login(email, passw):
        path_login_button = '#mainnav > div.content > div > div.mainnav > ul > li:nth-child(7) > a'
        browser.find_element(By.CSS_SELECTOR,path_login_button).click()
        time.sleep(1)
        path_email_input = '#defaultForm-email'
        # path_email_input.click()
        email_input = browser.find_element(By.CSS_SELECTOR,path_email_input)
        email_input.send_keys(email) 
        time.sleep(1)
        path_pass_input = '#defaultForm-pass'
        pass_input = browser.find_element(By.CSS_SELECTOR,path_pass_input)
        pass_input.send_keys(passw) 
        # path_pass_input.click()
        # path_pass_input.send_keys(passw)
        time.sleep(1)
        login_btn = '#login > div.modal-footer.d-flex.justify-content-center > button'
        pass_input = browser.find_element(By.CSS_SELECTOR,login_btn) 
        pass_input.click()
        time.sleep(1)

        

    login(email, passw)


    def download(num):
        browser.execute_script(f"downloadCSV({num},true)")
    
    for i, n in metals_list:
        download(i)

    max_test = 15
    def waiter():
        count = 0
        # Iterate directory
        for path in os.listdir(folder):
            # check if current path is a file
            if os.path.isfile(os.path.join(folder, path)):
                count += 1
        print('File count:', count)
        if count == len(metals_list):
            return 1
        else: return 0
    
    for i in range(max_test):
        if waiter() == 1:
            break
        else:
           time.sleep(1) 

    browser.quit()

dl()

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator
import math


master_df = pd.DataFrame()

# Iterate over each file
def r(master_df,file_path, element_name):
    filename = folder+f"prices-{str(file_path)}.csv"
    # Read file into a DataFrame
    df = pd.read_csv(filename ,thousands=',')
    # if "Min. Price" not in df.columns or "Max. Price" not in df.columns:
    #     print(f"Error in {filename}: Expected columns not found.")
    df["Avg. Price"] = (df["Min. Price"] + df["Max. Price"]) / 2

    # Rename the 'Avg. Price' column to the current element's name
    df = df.rename(columns={"Avg. Price": element_name})
    # print(df.columns)
    # Merge with master DataFrame
    if master_df.empty:
        master_df = df[["Date", element_name]]
    else:
        master_df = master_df.merge(df[["Date", element_name]], on="Date", how="outer")
    return master_df

for file_path, element_name in metals_list:
    master_df = r(master_df,file_path, element_name)
    
    
master_df = master_df.sort_values(by="Date")
end_date = master_df['Date'].max()

# Convert the 'Date' column to datetime format if it's not already
master_df['Date'] = pd.to_datetime(master_df['Date'])

def calculate_basket(master_df):

    # Calculate the price of the basket for each row
    def basket_price(row, basket):
        price = 0
        for element, percentage in basket.items():
            if pd.notna(row[element]):
                price += row[element] * percentage
            else:
                return None  # Return None if any required element is missing
        return price

    master_df['Basket Price'] = master_df.apply(lambda row: basket_price(row, basket), axis=1)

    return master_df
    # Show the updated DataFrame

master_df = calculate_basket(master_df)

def save_xl():
    file_path = './prices.xlsx'  # Specify the file path and name for your Excel file
    master_df.to_excel(file_path, index=False)
# save_xl() # uncomment to save to ecxel


def verify():
    # Helper function to get data from original CSV based on file number
    def get_data_from_csv(file_num, element_name):
        filename = folder + f"prices-{str(file_num)}.csv"
        df = pd.read_csv(filename, thousands=',')
        df[element_name] = (df["Min. Price"] + df["Max. Price"]) / 2
        return df[["Date", element_name]]

    # Go through each element column in master_df
    for file_num, element_name in metals_list:
        # Extract rows where the values for the current column are not NaN
        filtered_master_df = master_df[master_df[element_name].notna()][["Date", element_name]]
        
        # Fetch original data from the respective CSV
        original_df = get_data_from_csv(file_num, element_name)
        
        # Cross-check values and dates against the original CSV
        merged_df = pd.merge(filtered_master_df, original_df, on="Date", how="inner", suffixes=('_master', '_original'))
        
        # Check if values match
        if not (merged_df[element_name + '_master'] == merged_df[element_name + '_original']).all():
            print(f"Discrepancy detected in {element_name} data!")
        else:
            print(f"{element_name} data matches with original CSV.")

# verify()


import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.io as pio

def display_plotly():
    master_df['Date'] = pd.to_datetime(master_df['Date'])

    end_date = master_df['Date'].max() 
    # start_date = end_date - pd.DateOffset(years=x)  # for showing x years
    start_date = pd.to_datetime('28/09/2018')
    filtered_df = master_df[master_df['Date'] >= start_date]

    filtered_basket = {k: v for k, v in basket.items() if v > 0}


    time_difference = end_date - start_date
    difference_in_days = time_difference.days
    difference_in_years = math.floor(difference_in_days / 365.25)
    # Sample data
    x_values = filtered_df['Date']
    y_values = [filtered_df[element_name] for element_name in filtered_basket.keys()]
    # y_values = [filtered_df[element_name] for element_name in names]

    # Create figure
    fig = make_subplots()

    for i, element_name in enumerate(filtered_basket.keys()):
        fig.add_trace(go.Scatter(x=x_values, y=y_values[i], mode='lines+markers', name=element_name))


    # Add trace for basket price with red color and increased thickness
    fig.add_trace(go.Scatter(x=x_values, y=filtered_df['Basket Price'], mode='lines+markers', name='Basket Price', line=dict(color='red', width=4)))

    # Set layout options
    fig.update_layout(
        title=f'Average Prices of Elements over the Last {difference_in_years} Years',
        xaxis_title='Date',
        yaxis_title='Price',
        hovermode='x',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(t=40, b=40, l=40, r=40),
    )

    # Show plot

    fig.write_html('./prices.html')
    # fig.show()

display_plotly()

rm()
