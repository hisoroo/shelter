"""Szkielet klasy Scraper do pobierania obrazów zwierząt,
logika parsowania jest dostarczana z zewnątrz."""

import os
import re
import traceback
from typing import Callable, List, Optional
import uuid

import requests
from bs4 import BeautifulSoup


ProfileLinkFinder = Callable[[BeautifulSoup, str], List[str]]
PetNameFinder = Callable[[BeautifulSoup], Optional[str]]
ImageUrlFinder = Callable[[BeautifulSoup, str], List[str]]


class Scraper:
    """Szkielet klasy do pobierania obrazów zwierząt."""

    def __init__(self, base_list_url: str, output_dir: str,
                 profile_link_finder: ProfileLinkFinder,
                 pet_name_finder: PetNameFinder,
                 image_url_finder: ImageUrlFinder,
                 start_page: int = 1, end_page: int = 5,
                 headers: Optional[dict] = None, timeout: int = 15):
        """
        Inicjalizuje scraper z wymaganymi funkcjami parsowania.

        Args:
            base_list_url: Bazowy URL strony listy zwierząt.
            output_dir: Folder do zapisu pobranych zdjęć.
            profile_link_finder: Funkcja (soup, page_url) -> lista URL-i profili.
            pet_name_finder: Funkcja (soup) -> imię zwierzęcia lub None.
            image_url_finder: Funkcja (soup, page_url) -> lista URL-i obrazów.
            start_page: Numer strony listy, od której zacząć.
            end_page: Numer strony listy, na której skończyć.
            headers: Nagłówki HTTP do użycia w żądaniach.
            timeout: Timeout dla żądań HTTP.
        """
        self.base_list_url = base_list_url
        self.output_dir = output_dir
        self.start_page = start_page
        self.end_page = end_page
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = timeout

        self.find_profile_links = profile_link_finder
        self.find_pet_name = pet_name_finder
        self.find_image_urls = image_url_finder

        self.profile_urls_to_scrape = set()
        self.total_downloaded_count = 0

        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Folder wyjściowy: {os.path.abspath(self.output_dir)}")

    @staticmethod
    def generate_foldername(name: Optional[str]) -> str:
        """Generuje nazwę folderu: imie-pieciocyfrowy_hash."""
        if not name:
            base_name = "bez_nazwy"
        else:
            name = name.strip()
            name = re.sub(r'[<>:"/\\|?*]', '', name)
            name = re.sub(r'\s+', '_', name)
            name = re.sub(r'_\(\d+\)$', '', name)
            base_name = name if name else "bez_nazwy"

        short_hash = uuid.uuid4().hex[:5]
        return f"{base_name}-{short_hash}"

    @staticmethod
    def generate_unique_filename() -> str:
        """Generuje unikalną nazwę pliku opartą na UUID."""
        return f"{uuid.uuid4().hex}.jpg"

    def _make_request(self, url: str) -> Optional[BeautifulSoup | int]:
        """Wykonuje żądanie GET i zwraca obiekt BeautifulSoup."""
        try:
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 404:
                print(f"  Info: Strona {url} nie znaleziona (404).")
                return 404
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.HTTPError as e:
            print(f"  Błąd HTTP podczas pobierania {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  Błąd sieci podczas pobierania {url}: {e}")
            return None
        except Exception as e:
            print(f"  Nieoczekiwany błąd podczas pobierania {url}: {e}")
            traceback.print_exc()
            return None

    def _download_image(self, img_url: str, save_path: str) -> bool:
        """Pobiera i zapisuje pojedynczy obraz. Zwraca True jeśli pobrano nowy plik."""
        if os.path.exists(save_path):
            return False

        try:
            img_response = requests.get(
                img_url, headers=self.headers, timeout=self.timeout, stream=True)
            img_response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except requests.exceptions.RequestException as img_e:
            print(f"      Błąd podczas pobierania obrazu {img_url}: {img_e}")
        except IOError as io_e:
            print(
                f"      Błąd zapisu pliku {os.path.basename(save_path)}: {io_e}")
        except Exception as general_e:
            print(
                f"      Nieoczekiwany błąd podczas przetwarzania obrazu {img_url}: {general_e}")
        return False

    def collect_profile_urls(self):
        """Faza 1: Zbieranie linków do profili zwierząt używając dostarczonej funkcji."""
        print("--- Faza 1: Zbieranie linków do profili ---")
        print(
            f"Przeszukiwanie stron listy od {self.start_page} do {self.end_page}...")

        for i in range(self.start_page, self.end_page + 1):
            current_list_url = f"{self.base_list_url.rstrip('/')}/page/{i}/" if i > 1 else self.base_list_url

            print(f"\nPrzetwarzanie strony listy {i}: {current_list_url}")
            result = self._make_request(current_list_url)

            if result == 404:
                print(
                    f"Strona listy {i} ({current_list_url}) nie znaleziona (404). Koniec paginacji.")
                break
            elif not isinstance(result, BeautifulSoup):
                print(
                    f"Nie udało się pobrać lub przetworzyć strony {current_list_url}. Pomijanie.")
                continue
            else:
                soup = result

            try:
                page_profile_urls = self.find_profile_links(
                    soup, current_list_url)
            except Exception as e:
                print(
                    f"Błąd podczas wywoływania funkcji find_profile_links: {e}")
                traceback.print_exc()
                page_profile_urls = []

            found_count = len(page_profile_urls)
            if found_count > 0:
                print(
                    f"Znaleziono {found_count} linków do profili na stronie {i}.")
                self.profile_urls_to_scrape.update(page_profile_urls)
            else:
                print(f"Nie znaleziono linków do profili na stronie {i}.")

        print(
            f"\n--- Zakończono Fazę 1: Zebrano {len(self.profile_urls_to_scrape)} unikalnych linków do profili ---")

    def download_images_from_profiles(self):
        """Faza 2: Pobieranie obrazów ze stron profili używając dostarczonych funkcji."""
        print("\n--- Faza 2: Pobieranie obrazów ze stron profili ---")
        processed_profiles = 0
        total_profiles = len(self.profile_urls_to_scrape)

        if total_profiles == 0:
            print("Brak linków do profili do przetworzenia.")
            return

        profile_to_folder_map = {}

        for profile_url in self.profile_urls_to_scrape:
            processed_profiles += 1
            print(
                f"\n[{processed_profiles}/{total_profiles}] Przetwarzanie profilu: {profile_url}")

            profile_soup = self._make_request(profile_url)
            if not isinstance(profile_soup, BeautifulSoup):
                print(
                    f"  Pominięto profil {profile_url} z powodu błędu pobierania.")
                continue

            if profile_url in profile_to_folder_map:
                pet_dir = profile_to_folder_map[profile_url]
                print(
                    f"  Używanie istniejącego folderu dla tego profilu: {os.path.basename(pet_dir)}")
            else:
                try:
                    pet_name = self.find_pet_name(profile_soup)
                except Exception as e:
                    print(
                        f"  Błąd podczas wywoływania funkcji find_pet_name: {e}")
                    traceback.print_exc()
                    pet_name = None

                folder_name = self.generate_foldername(pet_name)
                if not pet_name:
                    print(
                        "  Ostrzeżenie: Nie udało się znaleźć imienia zwierzęcia. Używanie nazwy 'bez_nazwy'.")
                print(
                    f"  Znaleziono imię: '{pet_name}' -> Folder: '{folder_name}'")

                pet_dir = os.path.join(self.output_dir, folder_name)
                os.makedirs(pet_dir, exist_ok=True)
                profile_to_folder_map[profile_url] = pet_dir

            try:
                profile_image_urls = self.find_image_urls(
                    profile_soup, profile_url)
            except Exception as e:
                print(
                    f"  Błąd podczas wywoływania funkcji find_image_urls: {e}")
                traceback.print_exc()
                profile_image_urls = []

            if not profile_image_urls:
                print(
                    f"  Ostrzeżenie: Nie znaleziono obrazów w galerii dla folderu '{os.path.basename(pet_dir)}'.")
                continue

            print(f"  Znaleziono {len(profile_image_urls)} obrazów w galerii.")

            page_downloaded_count = 0
            for img_url in profile_image_urls:
                filename = self.generate_unique_filename()
                img_path = os.path.join(pet_dir, filename)
                if self._download_image(img_url, img_path):
                    page_downloaded_count += 1

            if page_downloaded_count > 0:
                print(
                    f"  Pobrano {page_downloaded_count} nowych obrazów do folderu '{os.path.basename(pet_dir)}'.")
            else:
                print(
                    f"  Nie pobrano nowych obrazów do folderu '{os.path.basename(pet_dir)}' (mogły już istnieć).")
            self.total_downloaded_count += page_downloaded_count

        print(
            f"\n--- Zakończono Fazę 2: Przetworzono {processed_profiles} profili. ---")

    def run(self):
        """Uruchamia cały proces scrapowania."""
        self.collect_profile_urls()
        self.download_images_from_profiles()
        print("\n--- Podsumowanie ---")
        print(f"Przeszukano strony list: {self.start_page}-{self.end_page}")
        print(
            f"Zebrano unikalnych linków do profili: {len(self.profile_urls_to_scrape)}")
        print(f"Łącznie pobrano nowych obrazów: {self.total_downloaded_count}")
        print(
            f"Obrazy zapisano w folderze: {os.path.abspath(self.output_dir)}")
