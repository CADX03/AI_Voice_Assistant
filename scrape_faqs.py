import re
import requests
from bs4 import BeautifulSoup
import json


# get all the faqs from the continente website
def get_faqs():
    url = "https://www.continente.pt/loja-online/ajuda/"
    page = requests.get(url)

    soup = BeautifulSoup(page.content, "html.parser")

    faqs_data = {}

    categories_section = soup.find("div", {"class": "row no-margin padding-sm-down-x-15 padding-md-up-x-70 help-page--tiles"})

    categories = categories_section.find_all("div", {"class": "help-page--tile"})

    # for each category, get the name and the questions (ex: Primeira compra, Registo, etc...)
    for category in categories:
        category_name = category.find("p", {"class": "help-page--card-header-title"}).text
        category_data = {"name": category_name, "questions": []}

        questions = category.find_all("a", {"class": "help-question--anchor"})

        #for each question, get the title and corresponding information (ex: "Como devo fazer o registo?", etc...)
        for question in questions:
            question_data = {}
            question_title = get_p(question.find("p"))
            question_page_link = question["href"]
            question_content = get_question_content(question_page_link)
            question_data["title"] = question_title
            question_data["link"] = question_page_link
            question_data["content"] = question_content
            category_data["questions"].append(question_data)

        faqs_data[category_name] = category_data

    return faqs_data

# get content of a specific question page
def get_question_content(question_page_link):
    page_data = []
    page_content = requests.get(question_page_link)
    page_soup = BeautifulSoup(page_content.content, "html.parser")

    
    question_answer = page_soup.select("div[class=col-12]")[0] # find only div with exact class match, not more or less classes
    if not question_answer: # error proofing
        print("Error: question_answer not found")
        return ""
    
    for tag in question_answer:
        if tag.name == "p":
            page_data.append(get_p(tag))
        elif tag.name == "ul":
            page_data.append(get_ul(tag))
        elif tag.name == "ol":
            page_data.append(get_ol(tag))
            
    return "\n".join(page_data)

def get_p(content):
    text = content.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text) # remove weird extra spaces or \n,\r,\t chars that appear
    return text.strip()
    
def get_li(content):
    return " ".join(get_p(p) for p in content.find_all("p"))

def get_ul(content):
    result = []
    for li in content.find_all("li"):
        text = get_li(li)
        if (text): # if not empty, prevents empty lines
            result.append(f"- {text}")
    return "\n".join(result)
    
def get_ol(content):
    result = []
    counter = 1
    for li in content.find_all("li"):
        text = get_li(li)
        if (text): # if not empty
            result.append(f"{counter}. {get_li(li)}")
        counter += 1
    return "\n".join(result)

def main():
    faqs_data = get_faqs()

    with open ("faqs_data.json", "w") as result_file:
        result_file.write(
            json.dumps(faqs_data, indent=4, ensure_ascii=False)
    )

if __name__ == "__main__":
   main()
