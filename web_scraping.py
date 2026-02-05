import csv
import requests
import bs4
import re
import json

#from bs4 import BeautifulSoup
from pprint import pprint
from typing import Dict, List, Union


import csv
import requests
import bs4
import re
from pprint import pprint
from typing import Dict, List, Union


BASE_HIMYM_URL = "https://how-i-met-your-mother.fandom.com/wiki/"
BASE_LSF_URL = (
    "https://www.lsf.uni-saarland.de/qisserver/rds"
    "?state=wtree&search=1&trex=step&root120221=320944%7C310559%7C318658%7C311255"
    "&P.vx=kurz&lang=en&noDBAction=y&init=y&lang=en"
)


def problem_1(name: str) -> List[Dict[str, Union[str, List[str]]]]:
    """Extract character attributes from HIMYM wiki."""
    name_link = name.replace(" ", "_")
    url = BASE_HIMYM_URL + name_link

    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.RequestException:
        print(f"Error fetching URL: {url}")
        return []

    soup = bs4.BeautifulSoup(res.text, "lxml")
    infobox = soup.find("table", {"class": "infobox character"})
    if not infobox:
        return []

    info_list = []
    for row in infobox.find_all("tr"):
        header = row.find("th")
        value = row.find("td")
        if header and value:
            # Clean text and remove references [1], [2], etc.
            attr = header.get_text(strip=True)
            val = re.sub(r"\[.*?\]", "", value.get_text(" ", strip=True))
            info_list.append({"attribute": attr, "value": val})

    return info_list


def problem_2_1() -> List[Dict[str, str]]:
    """Get all courses and their URLs from LSF portal."""
    try:
        res = requests.get(BASE_LSF_URL, headers={"Accept-Language": "en-US,en;q=0.9"})
        res.raise_for_status()
    except requests.RequestException:
        print("Error fetching LSF main page.")
        return []

    soup = bs4.BeautifulSoup(res.text, "lxml")
    content_div = soup.find("div", {"class": "content_max_portal_qis"})
    if not content_div:
        return []

    all_links = content_div.find_all("a", {"class": "ueb"})
    # Find link containing 'Alle Lehrveranstaltungen' dynamically
    courses_url = None
    for link in all_links:
        if "Alle Lehrveranstaltungen" in link.get_text():
            courses_url = link.get("href")
            break
    if not courses_url:
        return []

    try:
        res_courses = requests.get(courses_url)
        res_courses.raise_for_status()
    except requests.RequestException:
        print(f"Error fetching courses page: {courses_url}")
        return []

    soup_courses = bs4.BeautifulSoup(res_courses.text, "lxml")
    tables = soup_courses.find_all("table", {"summary": "Übersicht über alle Veranstaltungen"})
    course_list = []

    for table in tables:
        for a_tag in table.find_all("a", {"class": "regular"}):
            name = a_tag.get_text(strip=True)
            url = a_tag.get("href", "").strip()
            course_list.append({"Name of Course": name, "URL": url})

    return course_list


def problem_2_2(url: str) -> Dict[str, Union[str, List[str]]]:
    """Extract course details from a course URL."""
    try:
        res = requests.get(url, headers={"Accept-Language": "en-US,en;q=0.9"})
        res.raise_for_status()
    except requests.RequestException:
        print(f"Error fetching course page: {url}")
        return {}

    soup = bs4.BeautifulSoup(res.text, "lxml")
    info_table = soup.find("table", {"summary": "Grunddaten zur Veranstaltung"})
    instructor_table = soup.find("table", {"summary": "Verantwortliche Dozenten"})

    data = {}
    # Extract key-value pairs from info table
    if info_table:
        for row in info_table.find_all("tr"):
            header = row.find("th")
            value = row.find("td")
            if header and value:
                key = header.get_text(strip=True)
                val = re.sub(r"\s+", " ", value.get_text(" ", strip=True))
                data[key] = val

    # Extract instructors
    instructors = []
    if instructor_table:
        th = instructor_table.find("th", class_="mod")
        if th:
            key = th.get_text(strip=True)
            data[key] = []
        for td in instructor_table.find_all("td", class_=["mod_n_odd", "mod_n_even"]):
            name = td.get_text(strip=True)
            if name:
                instructors.append(name)
        if instructors:
            data[key] = instructors

    return data


def problem_2_3(output_file: str = "file.csv") -> None:
    """Scrape all courses and their details, save to CSV."""
    courses = problem_2_1()
    if not courses:
        print("No courses found.")
        return

    # Determine full headers
    headers = set()
    course_details_list = []

    for course in courses:
        url = course.get("URL")
        if not url:
            continue
        details = problem_2_2(url)
        if not details:
            continue
        course_data = {**course, **details}
        course_details_list.append(course_data)
        headers.update(course_data.keys())

    headers = list(headers)
    with open(output_file, "w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for course_data in course_details_list:
            writer.writerow(course_data)


def main():
    print("Example: HIMYM character attributes")
    pprint(problem_1("Lily Aldrin"))

    # print("Example: All courses")
    # pprint(problem_2_1())

    # print("Example: Single course details")
    # pprint(problem_2_2("https://www.lsf.uni-saarland.de/qisserver/rds?state=verpublish&status=init&vmfile=no&publishid=136509&moduleCall=webInfo&publishConfFile=webInfo&publishSubDir=veranstaltung&noDBAction=y&init=y"))

    # print("Scrape all courses to CSV")
    # problem_2_3("courses.csv")



if __name__ == "__main__":
    main()

#References:
#https://www.crummy.com/software/BeautifulSoup/bs4/doc/
#https://www.youtube.com/watch?v=87Gx3U0BDlo
#https://scribbleghost.net/2020/07/09/scraping-a-webpage-with-browser-based-language/
#https://www.geeksforgeeks.org/python-program-to-convert-a-list-to-string/
#https://thispointer.com/get-first-key-value-pair-from-a-python-dictionary/
#https://docs.python.org/3/library/csv.html
#https://tutorial.eyehunts.com/python/python-remove-extra-spaces-between-words-example-code/
