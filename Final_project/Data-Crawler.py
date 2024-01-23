import json
import time

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By


def scrape_links():
    # Initialize an empty list to store the URLs
    url_list = []
    url_list.append("https://www.nhatot.com/mua-ban-can-ho-chung-cu-tp-ho-chi-minh")

    # Generate the URLs for i from 2 to 100 and append them to the list
    for i in range(43, 480):
        url = f"https://www.nhatot.com/mua-ban-can-ho-chung-cu-tp-ho-chi-minh?page={i}"
        url_list.append(url)

    for url in url_list:
        # Initialize the WebDriver for Microsoft Edge
        driver = webdriver.Edge()  # Replace 'path_to_edgedriver' with the actual path to your edgedriver executable

        # minimize the browser window
        driver.minimize_window()

        # Navigate to the website
        driver.get(url)  # Replace with the URL you want to scrape

        # Get the width and height of the browser window
        window_width = driver.execute_script("return window.innerWidth;")
        window_height = driver.execute_script("return window.innerHeight;")

        # Calculate the coordinates for the center of the screen
        center_x = window_width / 2
        center_y = window_height / 2

        # Use ActionChains to move to the center of the screen and perform a click
        action = ActionChains(driver)
        action.move_by_offset(center_x, center_y)
        action.click()
        action.perform()

        # Find ListAds element
        ListAds = driver.find_elements(By.CLASS_NAME, "ListAds_ListAds__rEu_9")

        # Find all <a> elements whose href attribute starts with the specific URL segment
        url_segment = "https://www.nhatot.com/mua-ban-can-ho-chung-cu"

        # Initialize an empty list to store the Links
        links = []

        # Check if ListAds is not empty and contains at least one element
        if ListAds:
            for j in range(len(ListAds)):
                # Iterate through each ListAds element
                for element in ListAds[j].find_elements(By.TAG_NAME, "a"):
                    # Get the href attribute value
                    href = element.get_attribute("href")

                    # Check if the href attribute starts with the specified url_segment
                    if href and href.startswith(url_segment):
                        links.append(href)

        # append link to Links.txt file
        with open("Links TP.HCM.txt", "a") as file:
            for link in links:
                file.write(link + "\n")

        # Close the browser
        driver.quit()


# scrape_links()


def extract_ids(file_name):
    # Read the content of Links.txt
    with open(file_name, 'r') as file:
        urls = file.readlines()

    # Extract the IDs from the URLs
    ids = []
    for url in urls:
        # Split the URL by '/'
        parts = url.split('/')
        # Get the part containing the ID
        id_part = parts[-1]
        # Remove any additional text after the ID
        id = id_part.split('.')[0]
        ids.append(id)

    # Remove duplicate IDs
    ids = list(set(ids))

    # Write the IDs to ID.txt
    with open('IDs TP.HCM.txt', 'w') as file:
        for id in ids:
            file.write(id + '\n')


# extract_ids('Links TP.HCM.txt')


def flatten_nested_tags(data, prefix='', dataframe=None):
    if dataframe is None:
        dataframe = pd.DataFrame()

    for key, value in data.items():
        new_key = prefix + '_' + key if prefix else key
        if isinstance(value, dict):
            dataframe = flatten_nested_tags(value, prefix=new_key, dataframe=dataframe)
        else:
            if isinstance(value, (list, dict)):
                # Handle nested lists or dictionaries by converting to a string
                value = str(value)
            dataframe[new_key] = [value]

    return dataframe


def extract_tags_from_multiple_websites(websites_data):
    # Create an empty dataframe
    combined_dataframe = pd.DataFrame()

    # Iterate through data from different websites
    for website_data in websites_data:
        # Use the modified function to extract and flatten tags
        flattened_data = flatten_nested_tags(website_data)

        # Concatenate the flattened data to the combined dataframe
        combined_dataframe = pd.concat([combined_dataframe, flattened_data], axis=0, ignore_index=True)

    return combined_dataframe


def save_website_data(data, file_name):
    # Open the file in write mode and save the JSON data
    with open(file_name, 'w') as file:
        json.dump(data, file)

    print(f"Data saved to {file_name}")


def scrape_data():
    # Define the URL template
    url_template = "https://gateway.chotot.com/v2/public/ad-listing/{id}?adview_position=true&tm=treatment2"

    # Read IDs from a file
    with open("IDs TP.HCM.txt", "r") as file:
        ids = file.read().splitlines()

    # Initialize a list to store website data
    websites_data = []

    # Maximum number of retry attempts
    max_retries = 3

    # Iterate through IDs and fetch website data
    for id in ids:
        for retry in range(max_retries):
            url = url_template.format(id=id)
            response = requests.get(url)

            if response.json() == {"message": "Không tìm thấy dữ liệu."}:
                print(f"Data not found for ID {id}, moving to the next ID.")
                break

            if response.status_code == 200:
                websites_data.append(response.json())
                break  # Successful, exit the retry loop
            else:
                print(f"Failed to fetch data for ID {id}, retrying ({retry + 1}/{max_retries})...")
                time.sleep(5)  # Wait for 5 seconds before retrying

        else:
            # All retries failed, exit the program
            print(f"Failed to fetch data for ID {id} after {max_retries} retries. Exiting.")
            exit()

    # Save the data to a JSON file
    save_website_data(websites_data, "TP.HCM websites_data.json")


# scrape_data()


def extract_websites_data(filename):
    # read websites_data.json and pass to extract_tags_from_multiple_websites
    with open(filename, "r") as file:
        websites_data = json.load(file)

    # Extract and flatten nested tags from multiple websites into a single dataframe
    result_dataframe = extract_tags_from_multiple_websites(websites_data)

    # Keep only the columns we need
    columns_to_keep = ['ad_list_id', 'ad_date', 'ad_account_id', 'ad_projectid', 'ad_project_oid', 'ad_account_oid',
                       'ad_account_name', 'ad_subject', 'ad_company_ad', 'ad_price', 'ad_videos', 'ad_images',
                       'ad_number_of_images', 'ad_avatar', 'ad_rooms', 'ad_size', 'ad_ward_name', 'ad_block',
                       'ad_floornumber', 'ad_contain_videos', 'ad_longitude', 'ad_latitude', 'ad_reviewer_nickname',
                       'ad_protection_entitlement', 'ad_detail_address', 'ad_street_name',
                       'ad_params_apartment_feature_value',
                       'ad_params_apartment_type_value', 'ad_params_balconydirection_value',
                       'ad_params_direction_value',
                       'ad_params_property_status_value', 'ad_toilets', 'ad_street_number',
                       'ad_params_property_legal_document_value', 'ad_params_furnishing_sell_value']

    result_dataframe = result_dataframe[columns_to_keep]

    # Write the dataframe to a excel file
    result_dataframe.to_excel("Giá căn hộ, chung cư TP.HCM.xlsx", index=False)


# extract_websites_data('TP.HCM websites_data.json')
