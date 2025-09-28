#!/usr/bin/env python3
import re
import time
import random
import threading
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Callable

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


class KlingEngine:
    BASE_URL = "https://higgsfield.ai/create/video"
    STATE_FILE = "state.json"

    UPLOAD_AREA = r"#create-content > div.absolute.top-\[52px\].w-\[20rem\].left-4 > form > div.px-4.pb-6.shrink-0.overflow-y-auto.pt-4.hide-scrollbar.space-y-4.max-h-\[calc\(100vh-12rem\)\] > div.bg-neutral-surface-subtle.p-2.size-full.rounded-lg.w-full.select-none > label > div"
    PROMPT_BOX = r"#prompt"
    GENERATE_BTN = 'button:has-text("Generate")'
    DOWNLOAD_BTN_TEMPLATE = r"#create-content > div.space-y-4.pb-8.md\:pb-0.feed-container > article:nth-child({idx}) > div.flex-1.h-full.gap-2.my-auto > div > div > div:nth-child(1) > button:nth-child(1)"
    ARTICLE_PROMPT_SELECTOR_TEMPLATE = r"#create-content > div.space-y-4.pb-8.md\:pb-0.feed-container > article:nth-child({idx}) [data-sentry-component='ViewPromptInteractable']"
    DELETE_IMG_BTN_XPATH = "/html/body/main/div/div[2]/div[1]/form/div[1]/div[1]/div/div[2]/button"

    DOWNLOAD_POLL_TIMEOUT = 60 * 20

    def __init__(self, root_folder: str, headless: bool = False, max_concurrent: int = 2, poll_interval: float = 10.0, selected_folders: Optional[List[str]] = None):
        self.root_folder = Path(root_folder)
        self.headless = headless
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.selected_folders = selected_folders  # List of folder names to process (None = all folders)

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.save_session_event = threading.Event()
        self.save_session_result = None

        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

        # Track videos generated in this session (to avoid downloading pre-existing ones)
        self.generated_in_session = set()  # Set of image paths that were queued in this session

    def pause(self):
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def is_paused(self):
        return self.pause_event.is_set()

    def stop(self):
        self.stop_event.set()

    def is_stopped(self):
        return self.stop_event.is_set()

    def wait_while_paused(self):
        while self.pause_event.is_set() and not self.stop_event.is_set():
            time.sleep(0.2)

    def human_delay(self, a=0.6, b=1.4):
        time.sleep(random.uniform(a, b))

    def log(self, level: str, message: str, callback: Optional[Callable] = None):
        if callback:
            callback(level, message)
        else:
            print(f"[{level}] {message}")

    def list_images_sorted(self, dir_path: Path) -> List[Path]:
        imgs = [p for p in dir_path.iterdir() if p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]
        def sort_key(p: Path):
            m = re.match(r"^(\d+)$", p.stem)
            if m:
                return (0, int(m.group(1)))
            m2 = re.match(r"^(\d+)[-_].*", p.stem)
            if m2:
                return (0, int(m2.group(1)))
            return (1, p.name.lower())
        return sorted(imgs, key=sort_key)

    def read_prompts(self, dir_path: Path) -> List[str]:
        txt = dir_path / "prompts.txt"
        if not txt.exists():
            raise FileNotFoundError(f"Không thấy {txt}")
        lines = [ln.rstrip("\n") for ln in txt.read_text(encoding="utf-8").splitlines()]
        return lines

    def normalize_prompt_text(self, s: str) -> str:
        if not s:
            return ""
        s = s.strip()
        s = re.sub(r"^\s*\d+\s*[:.\\-]\s*", "", s)
        return s.strip().lower()

    def upload_image(self, img_path: Path, log_callback):
        self.log("INFO", f"Uploading: {img_path.name}", log_callback)
        try:
            inputs = self.page.query_selector_all("input[type=file]")
        except Exception:
            inputs = []

        if inputs:
            for inp in inputs:
                try:
                    if inp.is_visible():
                        inp.set_input_files(str(img_path))
                        self.human_delay(0.4, 1.0)
                        return
                except Exception:
                    continue
            try:
                inputs[0].set_input_files(str(img_path))
                self.human_delay(0.4, 1.0)
                return
            except Exception:
                pass

        raise RuntimeError("Upload failed: could not find input[type=file]")

    def fill_prompt(self, prompt: str):
        self.page.wait_for_selector(self.PROMPT_BOX, timeout=15000, state="visible")
        self.page.fill(self.PROMPT_BOX, "")
        self.human_delay(0.2, 0.6)
        self.page.type(self.PROMPT_BOX, prompt, delay=random.randint(12, 30))
        self.human_delay(0.2, 0.6)

    def click_generate(self):
        self.page.wait_for_selector(self.GENERATE_BTN, timeout=15000, state="visible")
        self.page.click(self.GENERATE_BTN)
        self.human_delay(0.6, 1.4)

    def click_delete_uploaded_image(self):
        try:
            el = self.page.wait_for_selector(f'xpath={self.DELETE_IMG_BTN_XPATH}', timeout=8000, state="visible")
            el.click()
            self.human_delay(0.4, 1.0)
        except PWTimeoutError:
            pass

    def is_article_done(self, article_idx: int, log_callback=None) -> bool:
        """Check if article is done (no longer generating)"""
        try:
            article_sel = f"article:nth-child({article_idx})"
            article = self.page.query_selector(article_sel)
            if not article:
                return False

            # First check StatusBadge - if still generating, no need to hover
            status_badge = article.query_selector("[data-sentry-component='StatusBadge']")
            if status_badge:
                txt = (status_badge.text_content() or "").strip().lower()
                if "in queue" in txt or "in progress" in txt or "render" in txt or "generat" in txt or "queue" in txt or "progress" in txt:
                    return False  # Still generating, don't even try to download

            # Hover to reveal the download button
            try:
                article.hover(timeout=2000)
                time.sleep(0.3)
            except Exception:
                pass

            # Check for download button - ONLY indicator of completion
            download_btn = article.query_selector("button.button--fixed svg[viewBox='0 0 24 24']")
            if download_btn:
                parent_btn = download_btn.evaluate("el => el.closest('button')")
                if parent_btn:
                    return True

            # No download button = not ready yet
            return False
        except Exception:
            return False

    def count_active_generating(self, log_callback, max_articles=24) -> int:
        count = 0
        try:
            all_articles = self.page.query_selector_all("article")
        except Exception:
            all_articles = []

        for idx, article in enumerate(all_articles[:max_articles], start=1):
            try:
                status_badge = article.query_selector("[data-sentry-component='StatusBadge']")
                if status_badge:
                    txt = (status_badge.text_content() or "").strip().lower()
                    if txt and ("in queue" in txt or "in progress" in txt or "render" in txt or "generat" in txt or "queue" in txt or "progress" in txt):
                        count += 1
                        continue

                rendering_badge = article.query_selector("div.rounded-lg.absolute.inset-0.size-full.flex.flex-col.items-center.justify-center")
                if rendering_badge and rendering_badge.is_visible():
                    count += 1
                    continue
            except Exception:
                continue

        return min(count, self.max_concurrent)

    def find_download_buttons(self, max_articles=36):
        found = []
        for i in range(1, max_articles+1):
            sel = self.DOWNLOAD_BTN_TEMPLATE.format(idx=i)
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    found.append(i)
            except Exception:
                continue
        return found

    def fuzzy_match_prompt(self, prompt_norm: str, queued: List[Dict]) -> Optional[int]:
        if not prompt_norm:
            return None
        for i, q in enumerate(queued):
            if q['downloaded']:
                continue
            if q['prompt_norm'] == prompt_norm:
                return i
        for i, q in enumerate(queued):
            if q['downloaded']:
                continue
            a = q['prompt_norm']
            if prompt_norm.startswith(a[:40]) or a.startswith(prompt_norm[:40]):
                return i
        for i, q in enumerate(queued):
            if q['downloaded']:
                continue
            if prompt_norm in q['prompt_norm'] or q['prompt_norm'] in prompt_norm:
                return i
        pshort = prompt_norm[:20]
        for i, q in enumerate(queued):
            if q['downloaded']:
                continue
            if q['prompt_norm'].startswith(pshort) or pshort in q['prompt_norm']:
                return i
        return None

    def download_video_by_position(self, article_position: int, queued: List[Dict], log_callback) -> bool:
        """Download video by matching article position with queued item"""
        # Find queued item with matching article_position
        matched_q = None
        for q in queued:
            if q.get('article_position') == article_position and q['status'] == 'generating' and not q['downloaded']:
                matched_q = q
                break

        if not matched_q:
            return False

        # Check if article is done
        if not self.is_article_done(article_position, log_callback):
            return False

        # Check timestamp (safety: only download videos queued < 30 min ago)
        if matched_q.get('queued_timestamp'):
            elapsed = time.time() - matched_q['queued_timestamp']
            if elapsed > 1800:  # 30 minutes
                self.log("WARNING", f"Video too old (queued {elapsed/60:.1f} min ago), skipping", log_callback)
                return False

        # Verify prompt matches before downloading
        article_sel = f"article:nth-child({article_position})"
        article = self.page.query_selector(article_sel)
        if not article:
            return False

        try:
            # Extract prompt from article
            prompt_element = article.query_selector("[data-sentry-component='ViewPromptInteractable']")
            if prompt_element:
                article_prompt = prompt_element.text_content().strip().lower()
                expected_prompt = matched_q['prompt_norm'].lower()

                # Flexible matching: check if one contains the other (at least first 50 chars)
                expected_short = expected_prompt[:50] if len(expected_prompt) > 50 else expected_prompt
                article_short = article_prompt[:50] if len(article_prompt) > 50 else article_prompt

                if expected_short not in article_prompt and article_short not in expected_prompt:
                    self.log("WARNING", f"Prompt mismatch at position {article_position}! Skipping download.", log_callback)
                    self.log("INFO", f"  Expected: {expected_prompt[:80]}...", log_callback)
                    self.log("INFO", f"  Got: {article_prompt[:80]}...", log_callback)
                    return False

                self.log("INFO", f"✓ Prompt verified for {matched_q['img_path'].name}", log_callback)
            else:
                self.log("WARNING", f"Cannot find prompt element at position {article_position}, skipping", log_callback)
                return False
        except Exception as e:
            self.log("WARNING", f"Prompt verification failed: {e}", log_callback)
            return False

        # Hover on article to reveal download button
        try:
            article.hover(timeout=3000)
            time.sleep(0.5)
        except Exception:
            pass

        # Find and click download button
        try:
            self.log("INFO", f"Downloading: {matched_q['img_path'].stem}.mp4", log_callback)

            download_btn = None
            article = self.page.query_selector(article_sel)
            if article:
                download_btn = article.query_selector("button.button--fixed svg[viewBox='0 0 24 24']")
                if download_btn:
                    download_btn = download_btn.evaluate_handle("el => el.closest('button')").as_element()

            if not download_btn:
                sel = self.DOWNLOAD_BTN_TEMPLATE.format(idx=article_position)
                download_btn = self.page.query_selector(sel)

            if not download_btn:
                raise Exception("Download button not found")

            with self.page.expect_download(timeout=90_000) as dl_info:
                download_btn.click()
            dl = dl_info.value
            target = matched_q['img_path'].with_suffix('.mp4')
            dl.save_as(str(target))
            matched_q['downloaded'] = True
            matched_q['status'] = 'downloaded'
            self.log("SUCCESS", f"✓ {target.name}", log_callback)
            self.human_delay(0.8, 1.8)
            return True
        except Exception as ex:
            self.log("WARNING", f"Download failed: {ex}", log_callback)
            return False

    def check_and_download_done_videos(self, queued: List[Dict], log_callback) -> int:
        """Check all generating videos and download those that are done"""
        downloaded_count = 0
        for q in queued:
            if q['status'] == 'generating' and not q['downloaded'] and q.get('article_position'):
                if self.download_video_by_position(q['article_position'], queued, log_callback):
                    downloaded_count += 1
        return downloaded_count

    def process_subfolder(self, sub_dir: Path, log_callback, progress_callback):
        self.log("INFO", f"Processing folder: {sub_dir.name}", log_callback)
        images = self.list_images_sorted(sub_dir)

        try:
            prompts = self.read_prompts(sub_dir)
        except FileNotFoundError as e:
            self.log("WARNING", f"Skip folder: {e}", log_callback)
            return

        if len(prompts) < len(images):
            self.log("WARNING", f"prompts.txt has fewer lines ({len(prompts)}) than images ({len(images)}). Processing first {len(prompts)} images.", log_callback)
            images = images[:len(prompts)]

        # Build prompt map using number-based mapping (from auto_video_with_slots.py logic)
        prompt_map = {}
        for idx, prompt in enumerate(prompts):
            # Extract number from prompt (e.g., "1: text" -> 1)
            m = re.match(r"^\s*(\d+)\s*[:.–—-]\s*", prompt)
            if m:
                num = int(m.group(1))
                prompt_map[num] = prompt
            else:
                prompt_map[idx + 1] = prompt

        queued = []
        for img in images:
            # Extract number from filename
            m = re.match(r"^(\d+)", img.stem)
            if not m:
                self.log("WARNING", f"Cannot extract number from {img.name}, skipping...", log_callback)
                continue

            img_num = int(m.group(1))
            raw = prompt_map.get(img_num)
            if raw is None:
                self.log("WARNING", f"No prompt found for image number {img_num} ({img.name}), skipping...", log_callback)
                continue

            queued.append({
                'img_path': img,
                'prompt_raw': raw,
                'prompt_norm': self.normalize_prompt_text(raw),
                'status': 'pending',   # pending / queued / generating / downloaded
                'downloaded': False,
                'article_position': None,  # Will be set after queuing
                'session_uuid': str(uuid.uuid4()),  # Unique ID for this queue
                'queued_timestamp': None  # Will be set when queued
            })

        for q in queued:
            out = q['img_path'].with_suffix('.mp4')
            if out.exists():
                q['downloaded'] = True
                q['status'] = 'downloaded'

        total_to_download = sum(1 for q in queued if not q['downloaded'])
        if total_to_download == 0:
            self.log("INFO", f"All videos already exist for {sub_dir.name}. Skipping.", log_callback)
            return

        self.log("INFO", f"To process: {total_to_download} videos", log_callback)

        start_time = time.time()
        downloaded_total = sum(1 for q in queued if q['downloaded'])

        while downloaded_total < len(queued):
            if self.is_stopped():
                self.log("WARNING", "Tiến trình bị dừng bởi người dùng", log_callback)
                break

            self.wait_while_paused()

            elapsed = time.time() - start_time
            if elapsed > self.DOWNLOAD_POLL_TIMEOUT:
                self.log("ERROR", f"Timeout cho thư mục {sub_dir.name}. Đã tải {downloaded_total}/{len(queued)}", log_callback)
                break

            progress_callback(downloaded_total, len(queued))

            # STEP 1: Kiểm tra và download các video đã xong
            downloaded_now = self.check_and_download_done_videos(queued, log_callback)
            if downloaded_now > 0:
                downloaded_total += downloaded_now
                progress_callback(downloaded_total, len(queued))
                self.log("INFO", f"Đã tải: {downloaded_total}/{len(queued)}", log_callback)
                continue

            # STEP 2: Đếm số video đang generate
            time.sleep(2.0)
            active_generating = self.count_active_generating(log_callback, max_articles=36)
            available_slots = self.max_concurrent - active_generating

            self.log("INFO", f"Active: {active_generating}/{self.max_concurrent} | Slots: {available_slots}", log_callback)

            # STEP 3: Nếu có slot trống → Queue videos mới
            queued_count = 0
            if available_slots > 0:
                for q in queued:
                    if self.is_stopped():
                        break
                    self.wait_while_paused()
                    if queued_count >= available_slots:
                        break
                    if q['downloaded'] or q.get('status') in ('generating', 'downloaded'):
                        continue

                    self.log("INFO", f"Queue: {q['img_path'].name}", log_callback)

                    self.upload_image(q['img_path'], log_callback)
                    self.fill_prompt(q['prompt_raw'])

                    try:
                        self.page.wait_for_selector(
                            "div.rounded-lg.absolute.inset-0.size-full.flex.flex-col.items-center.justify-center",
                            state="visible",
                            timeout=3000
                        )
                        self.page.wait_for_selector(
                            "div.rounded-lg.absolute.inset-0.size-full.flex.flex-col.items-center.justify-center",
                            state="detached",
                            timeout=15000
                        )
                    except Exception:
                        pass

                    self.click_generate()
                    self.human_delay(0.6, 1.4)
                    self.click_delete_uploaded_image()

                    # Mark as generating and track position
                    q['status'] = 'generating'
                    q['queued_timestamp'] = time.time()
                    q['article_position'] = 1

                    # Shift other generating videos' positions
                    for other_q in queued:
                        if other_q != q and other_q.get('article_position') and other_q['status'] == 'generating':
                            other_q['article_position'] += 1

                    time.sleep(4.0)
                    queued_count += 1

            # STEP 4: Không có gì để làm → Sleep theo poll_interval
            if queued_count == 0:
                for _ in range(int(self.poll_interval / 0.5)):
                    if self.is_stopped():
                        break
                    self.wait_while_paused()
                    time.sleep(0.5)

        self.log("SUCCESS", f"Folder {sub_dir.name} finished. Downloaded: {sum(1 for q in queued if q['downloaded'])}/{len(queued)}", log_callback)
        progress_callback(downloaded_total, len(queued))

    def request_save_session(self) -> tuple[bool, str]:
        """Request session save from main thread (non-blocking)
        Returns: (success: bool, message: str)
        """
        if not self.context:
            return False, "Browser not started yet"

        # Signal the browser thread to save session
        self.save_session_result = None
        self.save_session_event.set()

        # Wait for result (max 5 seconds)
        for _ in range(50):
            if self.save_session_result is not None:
                result = self.save_session_result
                self.save_session_result = None
                return result
            time.sleep(0.1)

        return False, "Timeout waiting for session save"

    def _handle_save_session(self):
        """Internal method to handle save session request (called from browser thread)"""
        if self.save_session_event.is_set():
            self.save_session_event.clear()
            try:
                if self.context:
                    self.context.storage_state(path=self.STATE_FILE)
                    self.save_session_result = (True, "Session saved successfully")
                else:
                    self.save_session_result = (False, "Context not available")
            except Exception as e:
                self.save_session_result = (False, f"Error: {str(e)}")

    def launch_browser(self, log_callback: Optional[Callable] = None):
        """Launch browser and open page, but don't start processing yet"""
        if not log_callback:
            log_callback = lambda level, msg: print(f"[{level}] {msg}")

        self.playwright = sync_playwright().start()
        # Use Chromium instead of Chrome for better performance
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        storage_state = self.STATE_FILE if Path(self.STATE_FILE).exists() else None

        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            accept_downloads=True,
            viewport={"width": 1600, "height": 900},
            storage_state=storage_state
        )
        self.page = self.context.new_page()
        self.page.goto(self.BASE_URL, wait_until="load")
        self.human_delay(1.2, 2.6)

        if not storage_state:
            self.log("INFO", "Vui lòng đăng nhập trong cửa sổ trình duyệt. Sau khi đăng nhập xong, nhấn nút 'Lưu phiên' trong giao diện để lưu session.", log_callback)
            self.log("WARNING", "Lưu ý: Chỉ nhấn 'Lưu phiên' SAU KHI đã đăng nhập thành công!", log_callback)
        else:
            self.log("SUCCESS", "Đã tự động đăng nhập bằng phiên đã lưu", log_callback)

    def run(self, log_callback: Optional[Callable] = None, progress_callback: Optional[Callable] = None):
        """Start processing folders (browser must be already launched)"""
        if not log_callback:
            log_callback = lambda level, msg: print(f"[{level}] {msg}")
        if not progress_callback:
            progress_callback = lambda current, total: None

        if not self.browser or not self.page:
            self.log("ERROR", "Browser not launched. Call launch_browser() first.", log_callback)
            return

        try:
            # Get folders to process
            if self.selected_folders:
                # Process only selected folders in order
                folders_to_process = []
                for folder_name in self.selected_folders:
                    folder_path = self.root_folder / folder_name
                    if folder_path.is_dir():
                        folders_to_process.append(folder_path)
                    else:
                        self.log("WARNING", f"Folder not found: {folder_name}", log_callback)
            else:
                # Process all folders
                folders_to_process = sorted([child for child in self.root_folder.iterdir() if child.is_dir()])

            if not folders_to_process:
                self.log("WARNING", "Không có thư mục nào để xử lý!", log_callback)
                return

            self.log("INFO", f"Sẽ xử lý {len(folders_to_process)} thư mục", log_callback)

            for folder in folders_to_process:
                if self.is_stopped():
                    break
                self.wait_while_paused()
                self.process_subfolder(folder, log_callback, progress_callback)

            self.log("SUCCESS", "Tất cả thư mục đã được xử lý!", log_callback)
        finally:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()