from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scraper import Scraper


def czestochowa_find_profile_links(soup: BeautifulSoup, page_url: str) -> List[str]:
    """Znajduje linki do profili na stronie listy schroniska w Częstochowie."""
    found_links = []
    profile_link_tags = soup.find_all('a', string='zobacz')
    for profile_link_tag in profile_link_tags:
        if profile_link_tag and 'href' in profile_link_tag.attrs:
            profile_url = urljoin(page_url, profile_link_tag['href'])
            if '/zwierzeta/' in profile_url:
                found_links.append(profile_url)
    return found_links


def czestochowa_find_pet_name(soup: BeautifulSoup) -> Optional[str]:
    """Znajduje imię zwierzęcia na stronie profilu schroniska w Częstochowie."""
    pet_name_strong_tag = soup.select_one('div.name h4 strong')
    if pet_name_strong_tag:
        return pet_name_strong_tag.get_text(strip=True)
    pet_name_tag = soup.select_one('h1.title-pets')
    if pet_name_tag:
        return pet_name_tag.get_text(strip=True)
    pet_name_tag = soup.select_one('h1')
    if pet_name_tag:
        return pet_name_tag.get_text(strip=True)
    return None


def czestochowa_find_image_urls(soup: BeautifulSoup, page_url: str) -> List[str]:
    """Znajduje URL-e obrazów w galerii na stronie profilu schroniska w Częstochowie."""
    image_urls = []
    gallery_ul = soup.find('ul', class_='slides')
    if gallery_ul:
        gallery_items = gallery_ul.find_all('li')
        for item in gallery_items:
            img_tag = item.find('img')
            if img_tag:
                img_src = img_tag.get('data-src') or img_tag.get('src')
                if img_src:
                    absolute_img_url = urljoin(page_url, img_src)
                    image_urls.append(absolute_img_url)
    return image_urls


if __name__ == "__main__":
    CZ_BASE_LIST_URL_PSY = 'https://schroniskoczestochowa.pl/lista-zwierzat/psy/'
    CZ_OUTPUT_DIR_PSY = 'schronisko_czest_dataset'
    START_PAGE = 1
    END_PAGE = 5
    TIMEOUT = 20

    print(f"Rozpoczynanie scrapowania dla: {CZ_BASE_LIST_URL_PSY}")
    scraper_psy = Scraper(
        base_list_url=CZ_BASE_LIST_URL_PSY,
        output_dir=CZ_OUTPUT_DIR_PSY,
        profile_link_finder=czestochowa_find_profile_links,
        pet_name_finder=czestochowa_find_pet_name,
        image_url_finder=czestochowa_find_image_urls,
        start_page=START_PAGE,
        end_page=END_PAGE,
        timeout=TIMEOUT
    )
    scraper_psy.run()
    print("\nZakończono scrapowanie.")
