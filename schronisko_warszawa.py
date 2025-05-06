"""Funkcje parsowania specyficzne dla strony schroniskowroclaw.pl."""

import os
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper import Scraper


class WarszawaScraper(Scraper):
    def _get_page_url(self, page_number: int) -> str:
        """Generuje URL dla danego numeru strony listy dla schroniska w Warszawie."""
        if page_number == 1:
            return self.base_list_url
        return f"{self.base_list_url}&pet_page={page_number}" 

def find_wwa_profile_links(soup: BeautifulSoup, page_url: str) -> List[str]:
    """
    Znajduje linki do profili zwierząt na stronie listy schroniska w Warszawie.
    """
    profile_links = []
    link_tags = soup.find_all('a', string='dowiedz się więcej')
    for link_tag in link_tags:
        href = link_tag.get('href')
        if href:
            full_url = urljoin(page_url, href)
            profile_links.append(full_url)
    return profile_links


def find_wwa_pet_name(soup: BeautifulSoup) -> Optional[str]:
    """
    Znajduje imię zwierzęcia na stronie profilu schroniska w Warszawie.
    """
    name_tag = soup.find('h2')
    if name_tag:
        small_tag = name_tag.find('small')
        if small_tag:
            small_tag.extract()
        return name_tag.get_text(strip=True)
    return None


def find_wwa_image_urls(soup: BeautifulSoup, page_url: str) -> List[str]:
    """
    Znajduje URL-e obrazów na stronie profilu schroniska w Warszawie.
    """
    image_urls = []
    gallery_divs = soup.find_all('div', class_='pet-detail-gallery-thumb-square')
    for div in gallery_divs:
        img_tag = div.find('img')
        if img_tag:
            src = img_tag.get('src')
            if src:
                full_url = urljoin(page_url, src)
                image_urls.append(full_url)

    if not image_urls:
        print(
            f"Ostrzeżenie: Nie znaleziono obrazów dla {page_url} (selektor: div.pet-detail-gallery-thumb-square img).")

    return image_urls


if __name__ == "__main__":

    BASE_URL = 'https://napaluchu.waw.pl/zwierzeta/zwierzeta-do-adopcji/?pet_breed=-1&pet_sex=0&pet_weight=0&pet_age=0&pet_date_from=&pet_date_to=&pet_name=&submit-form='
    OUTPUT_DIR = 'schronisko_wwa_dataset'
    START_PAGE = 1
    END_PAGE = 31

    print(f"Rozpoczynanie scrapowania z {BASE_URL}")
    print(f"Strony: {START_PAGE}-{END_PAGE}")
    print(f"Folder wyjściowy: {os.path.abspath(OUTPUT_DIR)}")


    wwa_scraper = WarszawaScraper(
        base_list_url=BASE_URL,
        output_dir=OUTPUT_DIR,
        profile_link_finder=find_wwa_profile_links,
        pet_name_finder=find_wwa_pet_name,
        image_url_finder=find_wwa_image_urls,
        start_page=START_PAGE,
        end_page=END_PAGE,
    )

    wwa_scraper.run()

    print("\n--- Zakończono skrypt main_wr.py ---")
