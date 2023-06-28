from random import choice
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Edge
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
from itertools import chain


TIME_LIMIT = 5


def scrape_recipes(
    recipe_website: str,
    loading_screen_css_selector: str | None,
    recipes_css_selector: str,
    next_button_css_selector: str | None | bool,
):
    recipe_links: list[str] = []
    options = Options()
    options.add_argument("--headless=new")
    options.add_extension("cookie_acceptor_extension.crx")
    options.add_extension("adblock_extension.crx")
    browser = Edge(options=options)
    browser.get(recipe_website)

    while True:
        if isinstance(loading_screen_css_selector, str):
            loading_screen_invisible = (
                expected_conditions.invisibility_of_element_located(
                    (By.CSS_SELECTOR, loading_screen_css_selector)
                )
            )

            WebDriverWait(browser, TIME_LIMIT).until(loading_screen_invisible)

        if isinstance(next_button_css_selector, str):
            recipe_elements_located = (
                expected_conditions.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR, recipes_css_selector)
                )
            )

            WebDriverWait(browser, TIME_LIMIT).until(recipe_elements_located)

        recipe_elements = browser.find_elements(By.CSS_SELECTOR, recipes_css_selector)
        element_count = len(recipe_elements)

        for recipe_element in recipe_elements:
            recipe_link = recipe_element.get_attribute("href")
            if isinstance(recipe_link, str):
                recipe_links.append(recipe_link)

        if next_button_css_selector == False:
            break

        if isinstance(next_button_css_selector, str):
            try:
                next_button = browser.find_element(
                    By.CSS_SELECTOR, next_button_css_selector
                )

                if next_button.get_attribute("disabled") is not None:
                    break

                next_button.click()
            except NoSuchElementException:
                break

        if next_button_css_selector is None:
            if element_count == 0:
                break
            url = browser.current_url
            page_field_index = url.find("page=")
            page_number_start_index = page_field_index + len("page=")
            page_number = int(url[page_number_start_index:])
            page_number += 1
            new_url = url[:page_number_start_index] + str(page_number)
            browser.get(new_url)

    browser.quit()

    return recipe_links


matprat = (
    "https://www.matprat.no/oppskrifter?filtersActive=-101,23",
    "div.matprat-loader__overlay",
    "a.cm-list-item.themed-teaser",
    'button[aria-label="neste"]',
)

tine = (
    "https://www.tine.no/oppskrifter/tema/superrask-middag?page=1",
    None,
    "a.m-recipe-card__link",
    None,
)

meny = (
    "https://meny.no/oppskrifter/middagstips/Rask/",
    None,
    "a.c-recipe-li",
    'a[aria-label="Neste side"]',
)

rema = (
    "https://www.rema.no/oppskrifter/middagstips/middag-under-20-min/",
    None,
    "div > a",
    False,
)

kiwi = ("https://kiwi.no/tema/middag/rask/", None, "a.block-box.recipe-teaser", False)


recipe_websites = (matprat, tine, meny, rema, kiwi)

with ThreadPoolExecutor() as executor:
    recipe_links = list(
        executor.map(lambda args: scrape_recipes(*args), recipe_websites)
    )

recipe_links = list(chain.from_iterable(recipe_links))

recipe_link = choice(recipe_links)

print(f"Randomly selected recipe: {recipe_link}")
