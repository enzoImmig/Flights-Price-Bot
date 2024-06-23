from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import time
import datetime
import pandas as pd
import argparse
import email
import imaplib

def build_url(origin, inbound, outbound, destination, adt, chd, inf, trip, cabin, redemption, sort):
    base_url = "https://www.latamairlines.com/br/pt/oferta-voos?"
    
    formated_inbound = datetime.datetime.strptime(inbound, '%Y-%m-%d 00:00:00').strftime('%Y-%m-%d')
    formated_outbound = datetime.datetime.strptime(outbound, '%Y-%m-%d 00:00:00').strftime('%Y-%m-%d')

    url = base_url + "origin=" + origin
    url += "&inbound=" + formated_inbound + "T12%3A00%3A00.000Z"
    url += "&outbound=" + formated_outbound + "T12%3A00%3A00.000Z"
    url += "&destination=" + destination
    url += "&adt=" + str(adt)
    url += "&chd=" + str(chd)
    url += "&inf=" + str(inf)
    url += "&trip=" + trip
    url += "&cabin=" + cabin
    url += "&redemption=" + redemption
    url += "&sort=" + sort

    print(url)

    return url

def extract_flight_table(request):

    # pass all the parameters to build the urls, convert to str and trim
    search_url = build_url(*list(map(str.strip, list(map(str, request)))))

    # setting driver en connection
    #op = webdriver.ChromeOptions()
    #op.add_argument("--headless")
    #op.add_argument("--window-size=1920,1080")
    #user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    #op.add_argument(f'--user-agent={user_agent}')
    #driver = webdriver.Chrome(options=op)
    driver = webdriver.Chrome()
    driver.get(search_url)
    driver.maximize_window()

    time.sleep(1)

    #checks cookies pop up
    try:
        element = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "//*[@id='cookies-politics--dialog__body']/div/div/div/div/section/h2"))
        )

        if element:
            print("Cookies policy pop-up appeard!")
            #clicks accept cookie
            driver.find_element(By.XPATH, "//*[@id='cookies-politics-button']").click()
    
    except:
        print("Pop-up cookies didn't appear")

    try:
        element = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/main/div/div/div/div/ol/li"))
        )
    except TimeoutException:
        driver.get_screenshot_as_file("screenshot.png")
        print("Page didn't load correctly")

    flight_list = driver.find_elements(By.XPATH, f"/html/body/div[1]/div[1]/main/div/div/div/div/ol/li")
    n_adds = 0
    df_extracted_data = pd.DataFrame(columns=['Amount', 'Duration', 'Operator'])
    arr_extracted_data = list()
    
    # extract data from list of flights
    for i in range(len(flight_list)):
        flight_XPath = f"/html/body/div[1]/div[1]/main/div/div/div/div/ol/li[{i+1}]"
        flight = driver.find_element(By.XPATH, flight_XPath)

        try:
            amount = driver.find_element(By.XPATH, flight_XPath + f"//*[@id='FlightInfoComponent{i-n_adds}']/div[2]/div/div/div/span").text
            arr_extracted_data.append(amount)

            duration = driver.find_element(By.XPATH, flight_XPath + f"//*[@id='ContainerFlightInfo{i-n_adds}']/span[2]").text
            arr_extracted_data.append(duration)

            operator = driver.find_element(By.XPATH, flight_XPath + f"//*[@id='ContainerFooterCard{i-n_adds}']/div/div/div[2]").text
            arr_extracted_data.append(operator)

            #print(amount, duration, operator)

        except:
            n_adds += 1
            print("Couldn't get the information on this flight")

        df_to_append = pd.DataFrame([{'Amount': amount.replace('BRL ', ''), 'Duration': duration, 'Operator': operator}])
        df_extracted_data = pd.concat([df_extracted_data, df_to_append], ignore_index=True)

    driver.quit()

    print(str(len(df_extracted_data.values)) + " itens extraidos.")
    return df_extracted_data

def run():

    # fazer input do usuário, tipo prendcher um form e jogar os dados num csv ou banco de dados algo desse tipo
    #parser = argparse.ArgumentParser(
     #   description="Bot to check flight prices at Latam"
    #)

    # Fazer a leitura do dataframe com os pedidos
    requests = pd.read_excel("requests.xlsx")
    print(requests)

    output_df = pd.DataFrame()

    start_time = datetime.datetime.now()

    # Para cada pedido, extrair os dados
    for index, request in requests.iterrows():
        print(request.values)

        request.values[2] -= datetime.timedelta(days=3)
        request.values[1] -= datetime.timedelta(days=3)
        inbound_main = request.values[1]
        outbound_main = request.values[2]

        for i in range(7):
            for j in range(7):
                request.values[2] += datetime.timedelta(days=i)
                request.values[1] += datetime.timedelta(days=j)

                df_flights = extract_flight_table(request.values)
                df_flights['date_saida'] = request.values[2]
                df_flights['date_chegada'] = request.values[1]
                output_df = pd.concat([output_df, df_flights])

                request.values[1] = inbound_main
                request.values[2] = outbound_main

    output_df.to_excel(f"testing.xlsx", index=False)   

    end_time = datetime.datetime.now()

    print(end_time - start_time)

if "__main__":
    status = run()
