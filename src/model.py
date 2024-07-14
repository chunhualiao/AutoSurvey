import time
import requests
import json
from tqdm import tqdm
import threading
import logging

class APIModel:

    def __init__(self, model, api_key, api_url) -> None:
        self.__api_key = api_key
        self.__api_url = api_url
        self.model = model
        
    def __req(self, text, temperature, max_try = 5):
        url = f"{self.__api_url}"
        pay_load_dict = {"model": f"{self.model}","messages": [{
                "role": "user",
                "temperature":temperature,
                "content": f"{text}"}]}
        payload = json.dumps(pay_load_dict)
        headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {self.__api_key}',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json'
        }
#        try:
#            response = requests.request("POST", url, headers=headers, data=payload)
#            return json.loads(response.text)['choices'][0]['message']['content']
#        except:
#            for _ in range(max_try):
#                try:
#                    response = requests.request("POST", url, headers=headers, data=payload)
#                    return json.loads(response.text)['choices'][0]['message']['content']
#                except:
#                    pass
#            return None
        for _ in range(max_try):
            try:
                response = requests.request("POST", url, headers=headers, data=payload)
                response.raise_for_status()  # Check for HTTP errors

                response_data = json.loads(response.text)

                # Type Check AFTER successful JSON parsing
                if 'choices' in response_data and len(response_data['choices']) > 0:  
                    content = response_data['choices'][0]['message']['content']
                    if isinstance(content, str):
                        return content
                    else:
                        error_msg = f"LLM API returned unexpected content type: {type(content)}. Content: {content}"
                        print(error_msg)
                        logging.error(error_msg)
                        raise TypeError(error_msg)
                else:
                    error_msg = f"LLM API response missing 'choices' or empty 'choices' list: {response_data}"
                    print(error_msg)
                    logging.error(error_msg)
                    raise ValueError(error_msg)

            except requests.exceptions.RequestException as e:
                logging.error(f"Request error during API request: {e}, Retry attempt: {_ + 1}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}, Retry attempt: {_ + 1}")

            time.sleep(0.2) # Short delay before trying next time

        # If all retries fail
        logging.error("All API request retries failed.")
        return None    

    # def req(self, text, temperature=1):
    #     url = f"{self.__api_url}"
    #     pay_load_dict = {"model": f"{self.model}","messages": [{
    #             "role": "user",
    #             "temperature":temperature,
    #             "content": f"{text}"}]}
    #     payload = json.dumps(pay_load_dict)
    #     headers = {
    #     'Accept': 'application/json',
    #     'Authorization': f'Bearer {self.__api_key}',
    #     'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    #     'Content-Type': 'application/json'
    #     }
        
    #     response = requests.request("POST", url, headers=headers, data=payload)
    #     print(response)
    #     print(response.text)
    #     return json.loads(response.text)['choices'][0]['message']['content']

    def chat(self, text, temperature=1):
        response = self.__req(text, temperature=temperature, max_try=5)
        return response

    def __chat(self, text, temperature, res_l, idx):

        response = self.__req(text, temperature=temperature)
        res_l[idx] = response
        return response
        
    def batch_chat(self, text_batch, temperature=0):
        max_threads=5 # limit max concurrent threads using model API
        logging.info(f"entering api_model. batch_chat(), max threads= {max_threads}...")

        logging.info(f"Input {len(text_batch)} text_batch:")
        for i, prompt in enumerate(text_batch):
           logging.info(f"Prompt {i+1}: {prompt}")

        res_l = ['No response'] * len(text_batch)
        thread_l = []
        for i, text in zip(range(len(text_batch)), text_batch):

            # Wait for a thread to finish if the maximum number is reached
            while len(thread_l) >= max_threads: 
                for t in thread_l:
                    if not t .is_alive():
                        thread_l.remove(t)
                time.sleep(0.3) # Short delay to avoid busy-waiting

            thread = threading.Thread(target=self.__chat, args=(text, temperature, res_l, i))
            thread_l.append(thread)
            thread.start()
            time.sleep(0.2)

        for thread in tqdm(thread_l):
            thread.join()

        logging.info(f"resulting contents {len(res_l)} :")
        for i, content in enumerate(res_l):
           logging.info(f"Content {i+1}: {content}")

        return res_l
