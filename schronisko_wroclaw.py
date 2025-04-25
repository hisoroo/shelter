"""Funkcje parsowania specyficzne dla strony schroniskowroclaw.pl."""

import os
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper import Scraper


def find_wroclaw_profile_links(soup: BeautifulSoup, page_url: str) -> List[str]:
    """
    Znajduje linki do profili zwierząt na stronie listy schroniska we Wrocławiu.
    """
    profile_links = []
    link_tags = soup.find_all('a', class_='breakdance-image-link')
    for link_tag in link_tags:
        href = link_tag.get('href')
        if href:
            full_url = urljoin(page_url, href)
            profile_links.append(full_url)
    return profile_links


def find_wroclaw_pet_name(soup: BeautifulSoup) -> Optional[str]:
    """
    Znajduje imię zwierzęcia na stronie profilu schroniska we Wrocławiu.
    """
    name_tag = soup.find('h1', class_='bde-heading')
    if name_tag:
        return name_tag.get_text(strip=True)

    print("Ostrzeżenie: Nie znaleziono selektora dla imienia zwierzęcia (h1.bde-heading).")
    return None


def find_wroclaw_image_urls(soup: BeautifulSoup, page_url: str) -> List[str]:
    """
    Znajduje URL-e obrazów na stronie profilu schroniska we Wrocławiu.
    """
    image_urls = []
    img_tags = soup.find_all('img', class_='breakdance-image-object')
    for img_tag in img_tags:
        src = img_tag.get('src')
        if src:
            full_url = urljoin(page_url, src)
            image_urls.append(full_url)

    if not image_urls:
        print(
            f"Ostrzeżenie: Nie znaleziono obrazów dla {page_url} (selektor: img.breakdance-image-object).")

    return image_urls


if __name__ == "__main__":

    BASE_URL = 'https://schroniskowroclaw.pl/gatunek-zwierzecia/psy/'
    OUTPUT_DIR = 'schronisko_wroc_dataset'
    START_PAGE = 1
    END_PAGE = 5
    print(f"Rozpoczynanie scrapowania z {BASE_URL}")
    print(f"Strony: {START_PAGE}-{END_PAGE}")
    print(f"Folder wyjściowy: {os.path.abspath(OUTPUT_DIR)}")

    wroclaw_scraper = Scraper(
        base_list_url=BASE_URL,
        output_dir=OUTPUT_DIR,
        profile_link_finder=find_wroclaw_profile_links,
        pet_name_finder=find_wroclaw_pet_name,
        image_url_finder=find_wroclaw_image_urls,
        start_page=START_PAGE,
        end_page=END_PAGE
    )

    wroclaw_scraper.run()

    print("\n--- Zakończono skrypt main_wr.py ---")
