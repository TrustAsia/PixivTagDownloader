"""
API interaction module for the Pixiv Tag Downloader application.
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from config import config
from utils import random_delay

class PixivAPI:
    """Handle interactions with the Pixiv API."""

    def __init__(self, session):
        """
        Initialize the API module.

        Args:
            session (requests.Session): Authenticated session
        """
        self.session = session
        self.base_url = "https://www.pixiv.net"
        self.api_url = "https://www.pixiv.net/ajax"

    def get_user_info(self, uid):
        """
        Get information about a Pixiv user.

        Args:
            uid (str): User ID

        Returns:
            dict: User information or None if failed
        """
        try:
            url = f"{self.api_url}/user/{uid}?full=1"
            response = self.session.get(url, timeout=config.get("timeout"))
            data = response.json()

            if data.get("error", False):
                print(f"Error fetching user info: {data.get('message', 'Unknown error')}")
                return None

            user_data = data.get("body", {})
            user_info = {
                "uid": uid,
                "name": user_data.get("name", f"User_{uid}"),
                "profile_img": user_data.get("image", ""),
                "is_followed": user_data.get("isFollowed", False)
            }

            random_delay(config.get("min_delay"), config.get("max_delay"))
            return user_info
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None

    def get_user_works(self, uid, work_type="all"):
        """
        Get all works by a user.

        Args:
            uid (str): User ID
            work_type (str): Type of works to get ("all", "illustrations", "manga", "novels")

        Returns:
            list: List of work IDs or empty list if failed
        """
        try:
            works = []

            # First, get the list of illustration and manga IDs
            if work_type in ["all", "illustrations", "manga"]:
                # Get illustration IDs
                url = f"{self.api_url}/user/{uid}/illusts?lang=zh"
                response = self.session.get(url, timeout=config.get("timeout"))
                data = response.json()

                if not data.get("error", False):
                    illust_ids = data.get("body", {}).get("illusts", [])
                    if isinstance(illust_ids, list):
                        works.extend([{"id": str(illust_id), "type": "illust"} for illust_id in illust_ids])
                    elif isinstance(illust_ids, dict):
                        works.extend([{"id": str(pid), "type": "illust"} for pid in illust_ids.keys()])

                # Get manga IDs
                url = f"{self.api_url}/user/{uid}/manga?lang=zh"
                response = self.session.get(url, timeout=config.get("timeout"))
                data = response.json()

                if not data.get("error", False):
                    manga_ids = data.get("body", {}).get("manga", [])
                    if isinstance(manga_ids, list):
                        works.extend([{"id": str(manga_id), "type": "manga"} for manga_id in manga_ids])
                    elif isinstance(manga_ids, dict):
                        works.extend([{"id": str(pid), "type": "manga"} for pid in manga_ids.keys()])

            # Get novel IDs
            if work_type in ["all", "novels"]:
                url = f"{self.api_url}/user/{uid}/novels?lang=zh"
                response = self.session.get(url, timeout=config.get("timeout"))
                data = response.json()

                if not data.get("error", False):
                    novel_ids = data.get("body", {}).get("novels", [])
                    if isinstance(novel_ids, list):
                        works.extend([{"id": str(novel_id), "type": "novel"} for novel_id in novel_ids])
                    elif isinstance(novel_ids, dict):
                        works.extend([{"id": str(pid), "type": "novel"} for pid in novel_ids.keys()])

            # If we still don't have any works, try an alternative approach
            if not works:
                # Try to get all works from the user's profile page
                url = f"{self.base_url}/ajax/user/{uid}/profile/all"
                response = self.session.get(url, timeout=config.get("timeout"))
                data = response.json()

                if not data.get("error", False):
                    body = data.get("body", {})

                    # Extract illustration IDs
                    illusts = body.get("illusts", {})
                    if isinstance(illusts, dict):
                        works.extend([{"id": pid, "type": "illust"} for pid in illusts.keys()])

                    # Extract manga IDs
                    manga = body.get("manga", {})
                    if isinstance(manga, dict):
                        works.extend([{"id": pid, "type": "manga"} for pid in manga.keys()])

                    # Extract novel IDs
                    novels = body.get("novels", {})
                    if isinstance(novels, dict):
                        works.extend([{"id": pid, "type": "novel"} for pid in novels.keys()])

            random_delay(config.get("min_delay"), config.get("max_delay"))
            return works
        except Exception as e:
            print(f"Error getting user works: {e}")
            return []

    def get_artwork_details(self, pid):
        """
        Get details about an artwork (illustration or manga).

        Args:
            pid (str): Artwork ID

        Returns:
            dict: Artwork details or None if failed
        """
        try:
            url = f"{self.api_url}/illust/{pid}"
            response = self.session.get(url, timeout=config.get("timeout"))
            data = response.json()

            if data.get("error", False):
                print(f"Error fetching artwork details: {data.get('message', 'Unknown error')}")
                return None

            body = data.get("body", {})

            # Extract artwork details
            artwork = {
                "pid": pid,
                "title": body.get("title", f"Artwork_{pid}"),
                "description": body.get("description", ""),
                "author_uid": body.get("userId", ""),
                "author_name": body.get("userName", ""),
                "tags": [tag.get("tag", "") for tag in body.get("tags", {}).get("tags", [])],
                "type": "manga" if body.get("pageCount", 1) > 1 else "illust",
                "page_count": body.get("pageCount", 1),
                "create_date": body.get("createDate", ""),
                "width": body.get("width", 0),
                "height": body.get("height", 0),
                "series": {}
            }

            # Check if artwork is part of a series
            if body.get("seriesNavData"):
                series_data = body.get("seriesNavData")
                artwork["series"] = {
                    "id": series_data.get("seriesId", ""),
                    "title": series_data.get("title", "")
                }

            random_delay(config.get("min_delay"), config.get("max_delay"))
            return artwork
        except Exception as e:
            print(f"Error getting artwork details: {e}")
            return None

    def get_novel_details(self, pid):
        """
        Get details about a novel.

        Args:
            pid (str): Novel ID

        Returns:
            dict: Novel details or None if failed
        """
        try:
            url = f"{self.api_url}/novel/{pid}"
            response = self.session.get(url, timeout=config.get("timeout"))
            data = response.json()

            if data.get("error", False):
                print(f"Error fetching novel details: {data.get('message', 'Unknown error')}")
                return None

            body = data.get("body", {})

            # Extract novel details
            novel = {
                "pid": pid,
                "title": body.get("title", f"Novel_{pid}"),
                "description": body.get("description", ""),
                "author_uid": body.get("userId", ""),
                "author_name": body.get("userName", ""),
                "tags": [tag.get("tag", "") for tag in body.get("tags", {}).get("tags", [])],
                "type": "novel",
                "create_date": body.get("createDate", ""),
                "text_length": body.get("textLength", 0),
                "series": {}
            }

            # Check if novel is part of a series
            if body.get("seriesNavData"):
                series_data = body.get("seriesNavData")
                novel["series"] = {
                    "id": series_data.get("seriesId", ""),
                    "title": series_data.get("title", "")
                }

            # Get novel content
            novel_content = self.get_novel_content(pid)
            if novel_content:
                novel["content"] = novel_content
            else:
                # If we couldn't get the content, try again with a different approach
                print(f"Retrying to get content for novel {pid} with alternative method...")
                # Add a delay before retrying
                random_delay(config.get("min_delay") * 2, config.get("max_delay") * 2)
                novel_content = self.get_novel_content(pid)
                if novel_content:
                    novel["content"] = novel_content
                else:
                    print(f"Warning: Could not retrieve content for novel {pid}")

            random_delay(config.get("min_delay"), config.get("max_delay"))
            return novel
        except Exception as e:
            print(f"Error getting novel details: {e}")
            return None

    def get_novel_content(self, pid):
        """
        Get the content of a novel.

        Args:
            pid (str): Novel ID

        Returns:
            str: Novel content or empty string if failed
        """
        try:
            # Method 1: Try the AJAX API
            url = f"{self.api_url}/novel/{pid}/content"
            response = self.session.get(url, timeout=config.get("timeout"))
            data = response.json()

            if not data.get("error", False):
                content = data.get("body", {}).get("content", "")

                # Convert HTML content to plain text if needed
                if content and "<" in content and ">" in content:
                    soup = BeautifulSoup(content, "html.parser")
                    content = soup.get_text()

                if content:
                    random_delay(config.get("min_delay"), config.get("max_delay"))
                    return content

            # Method 2: Try the direct method
            print(f"AJAX API failed for novel {pid}, trying direct method...")
            content = self.get_novel_content_direct(pid)
            if content:
                random_delay(config.get("min_delay"), config.get("max_delay"))
                return content

            # Method 3: Try a different API endpoint
            print(f"Direct method failed for novel {pid}, trying another API endpoint...")
            url = f"{self.base_url}/ajax/novel/{pid}"
            response = self.session.get(url, timeout=config.get("timeout"))
            data = response.json()

            if not data.get("error", False):
                body = data.get("body", {})
                content = body.get("content", "")
                if content:
                    # Convert HTML content to plain text if needed
                    if "<" in content and ">" in content:
                        soup = BeautifulSoup(content, "html.parser")
                        content = soup.get_text()

                    random_delay(config.get("min_delay"), config.get("max_delay"))
                    return content

            # Method 4: Try the novel viewer page
            print(f"All API methods failed for novel {pid}, trying novel viewer page...")
            url = f"{self.base_url}/novel/view.php?id={pid}"
            headers = {
                "Referer": self.base_url,
                "User-Agent": config.get("user_agent")
            }

            response = self.session.get(url, headers=headers, timeout=config.get("timeout"))

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Try to find the novel content in the viewer page
                novel_content_div = soup.select_one(".novelbody")
                if novel_content_div:
                    content = novel_content_div.get_text(strip=True)
                    if content:
                        random_delay(config.get("min_delay"), config.get("max_delay"))
                        return content

            print(f"All methods failed to get content for novel {pid}")
            return ""
        except Exception as e:
            print(f"Error getting novel content: {e}")
            return ""

    def get_artwork_urls(self, pid):
        """
        Get the URLs of all images in an artwork.

        Args:
            pid (str): Artwork ID

        Returns:
            list: List of image URLs or empty list if failed
        """
        try:
            url = f"{self.api_url}/illust/{pid}/pages"
            response = self.session.get(url, timeout=config.get("timeout"))
            data = response.json()

            if data.get("error", False):
                print(f"Error fetching artwork URLs: {data.get('message', 'Unknown error')}")
                return []

            pages = data.get("body", [])
            image_urls = []

            for i, page in enumerate(pages):
                # Get the original image URL
                original_url = page.get("urls", {}).get("original", "")
                if original_url:
                    image_urls.append({
                        "url": original_url,
                        "index": i
                    })

            random_delay(config.get("min_delay"), config.get("max_delay"))
            return image_urls
        except Exception as e:
            print(f"Error getting artwork URLs: {e}")
            return []

    def get_novel_content_direct(self, pid):
        """
        Get the content of a novel directly from the novel page.
        This is a fallback method when the API fails.

        Args:
            pid (str): Novel ID

        Returns:
            str: Novel content or empty string if failed
        """
        try:
            # Try to get the novel content from the novel page
            url = f"{self.base_url}/novel/show.php?id={pid}"
            headers = {
                "Referer": self.base_url,
                "User-Agent": config.get("user_agent")
            }

            response = self.session.get(url, headers=headers, timeout=config.get("timeout"))

            if response.status_code != 200:
                print(f"Failed to access novel page for {pid}: HTTP {response.status_code}")
                return ""

            soup = BeautifulSoup(response.text, "html.parser")

            # Method 1: Try to find the novel content in the page
            novel_content_div = soup.select_one("#novel_content")
            if novel_content_div:
                content = novel_content_div.get_text(strip=True)
                if content:
                    return content

            # Method 2: Try to extract the novel content from the page's JavaScript
            scripts = soup.find_all("script")
            for script in scripts:
                if not script.string:
                    continue

                script_text = script.string

                # Look for novel content in JavaScript
                if "pixiv.context.novel" in script_text or "novel.content" in script_text:
                    import re
                    # Try different regex patterns
                    patterns = [
                        r'"content":"(.*?)","',
                        r'content:"(.*?)",',
                        r'content:\s*"(.*?)",',
                        r'novel\.content\s*=\s*"(.*?)";'
                    ]

                    for pattern in patterns:
                        content_match = re.search(pattern, script_text, re.DOTALL)
                        if content_match:
                            # Unescape the content
                            content = content_match.group(1)
                            content = content.replace("\\n", "\n").replace("\\\"", "\"").replace("\\\\", "\\")
                            if content:
                                return content

            # Method 3: Try to find the novel content in a different element
            novel_text_divs = soup.select(".novel_view")
            if novel_text_divs:
                for div in novel_text_divs:
                    content = div.get_text(strip=True)
                    if content:
                        return content

            print(f"Could not extract content from novel page for {pid}")
            return ""
        except Exception as e:
            print(f"Error getting novel content directly: {e}")
            return ""

    def extract_all_tags(self, works):
        """
        Extract all unique tags from a list of works.

        Args:
            works (list): List of work IDs

        Returns:
            list: List of unique tags
        """
        all_tags = set()

        for work in works:
            work_id = work["id"]
            work_type = work["type"]

            if work_type in ["illust", "manga"]:
                details = self.get_artwork_details(work_id)
            elif work_type == "novel":
                details = self.get_novel_details(work_id)
            else:
                continue

            if details and "tags" in details:
                all_tags.update(details["tags"])

        # Remove empty tags and sort
        return sorted([tag for tag in all_tags if tag])
