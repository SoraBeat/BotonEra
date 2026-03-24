"""BotonEra Scraper - descarga sonidos de myinstants.com via HTML pagination."""
from __future__ import annotations
import json, random, re, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR    = Path(__file__).parent
SOUNDS_DIR  = BASE_DIR / "sounds"
CONFIG_PATH = BASE_DIR / "config.json"

SITE = "https://www.myinstants.com"

# All categories available on the site + special pages
ALL_SOURCES = [
    ("Tendencias",       f"{SITE}/en/trending/ar/"),
    ("Recientes",        f"{SITE}/en/recent/"),
    ("Anime & Manga",    f"{SITE}/en/categories/anime%20&%20manga/"),
    ("Games",            f"{SITE}/en/categories/games/"),
    ("Memes",            f"{SITE}/en/categories/memes/"),
    ("Movies",           f"{SITE}/en/categories/movies/"),
    ("Music",            f"{SITE}/en/categories/music/"),
    ("Politics",         f"{SITE}/en/categories/politics/"),
    ("Pranks",           f"{SITE}/en/categories/pranks/"),
    ("Reactions",        f"{SITE}/en/categories/reactions/"),
    ("Sound Effects",    f"{SITE}/en/categories/sound%20effects/"),
    ("Sports",           f"{SITE}/en/categories/sports/"),
    ("Television",       f"{SITE}/en/categories/television/"),
    ("Tiktok Trends",    f"{SITE}/en/categories/tiktok%20trends/"),
    ("Viral",            f"{SITE}/en/categories/viral/"),
    ("Whatsapp Audios",  f"{SITE}/en/categories/whatsapp%20audios/"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Referer": SITE,
}

COLORS = ["#6C63FF","#00D9FF","#FF6B6B","#FFD93D","#6BCB77",
          "#FF9A3C","#C77DFF","#4CC9F0","#F72585","#4361EE"]
EMOJIS = ["\U0001f50a","\U0001f4a5","\U0001f3b5","\U0001f3a4","\U0001f941",
          "\U0001f3b8","\U0001f514","\U0001f4a3","\U0001f3ba","\U0001f3bb",
          "\U0001f6a8","\U0001f602","\U0001f480","\U0001f923","\U0001f525",
          "\U0001f44f","\U0001f60e","\U0001f3ae","\U0001f680","\U0001f4af"]

RE_PLAY = re.compile(r"play\('(/[^']+\.mp3)'")


def _get(url, *, timeout=15, stream=False):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout, stream=stream)
            r.raise_for_status()
            return r
        except requests.exceptions.HTTPError as e:
            print(f"    HTTP {e.response.status_code} -- {url}")
            return None
        except Exception as e:
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
            else:
                print(f"    Error: {e}")
    return None


def _extract_sounds_from_page(html: str) -> list[tuple[str, str]]:
    """Returns list of (name, mp3_path) from an HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    buttons = soup.find_all("button", onclick=RE_PLAY)
    for btn in buttons:
        m = RE_PLAY.search(btn.get("onclick", ""))
        if not m:
            continue
        mp3_path = m.group(1)
        name = ""
        parent = btn.find_parent(class_=re.compile(r"instant"))
        if parent:
            a = parent.find("a", href=re.compile(r"/instant/"))
            if a:
                name = a.get_text(strip=True)
        if not name:
            title_attr = btn.get("title", "")
            if "de " in title_attr:
                name = title_attr.split("de ", 1)[-1].strip()
        if not name:
            name = Path(mp3_path).stem.replace("-", " ").replace("_", " ").title()
        results.append((name, mp3_path))
    return results


def collect_from_source(
    label: str,
    base_url: str,
    max_sounds: int,
    seen_urls: set[str],
) -> list[dict]:
    """Scrape all pages of a single source URL, skipping already-seen MP3 paths."""
    items: list[dict] = []
    page = 1
    consecutive_empty = 0

    while len(items) < max_sounds:
        url = f"{base_url}?page={page}"
        r = _get(url)
        if not r:
            break

        found = _extract_sounds_from_page(r.text)
        if not found:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
            page += 1
            time.sleep(0.3)
            continue
        consecutive_empty = 0

        new_on_page = 0
        for name, mp3_path in found:
            if len(items) >= max_sounds:
                break
            if mp3_path in seen_urls:
                continue
            mp3_url = SITE + mp3_path
            items.append({"name": name, "sound": mp3_url})
            seen_urls.add(mp3_path)
            new_on_page += 1

        print(f"    [{label}] p{page}: +{new_on_page} nuevos  (total esta fuente: {len(items)})")

        if new_on_page == 0:
            # All sounds on this page were already seen globally — stop source
            break

        page += 1
        time.sleep(0.3)

    return items


def collect_sounds_search(query: str, max_sounds: int, seen_urls: set[str]) -> list[dict]:
    """Scrape search pages for a given query."""
    items: list[dict] = []
    base_url = f"{SITE}/es/search/?name={quote_plus(query)}&page="
    page = 1

    while len(items) < max_sounds:
        url = base_url + str(page)
        r = _get(url)
        if not r:
            break
        found = _extract_sounds_from_page(r.text)
        if not found:
            break
        new_on_page = 0
        for name, mp3_path in found:
            if len(items) >= max_sounds:
                break
            if mp3_path in seen_urls:
                continue
            items.append({"name": name, "sound": SITE + mp3_path})
            seen_urls.add(mp3_path)
            new_on_page += 1
        print(f"  Pagina {page}: +{new_on_page}  (total: {len(items)})")
        if new_on_page == 0:
            break
        page += 1
        time.sleep(0.3)

    return items


def _safe_filename(name: str) -> str:
    safe = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    safe = re.sub(r"\s+", " ", safe)
    return safe[:80] + ".mp3"


def download_one(item: dict, dest_dir: Path, existing: set) -> tuple[str, Path | None]:
    name, url = item["name"], item["sound"]
    fname = _safe_filename(name)
    if fname in existing:
        return name, dest_dir / fname
    r = _get(url, timeout=30, stream=True)
    if not r:
        return name, None
    dest = dest_dir / fname
    try:
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        existing.add(fname)
        kb = dest.stat().st_size // 1024
        print(f"    OK  {fname}  ({kb} KB)")
        return name, dest
    except Exception as e:
        print(f"    ERR {fname}: {e}")
        dest.unlink(missing_ok=True)
        return name, None


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"mic_device_id": None, "monitor_device_id": None, "volume": 1.0, "sounds": []}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    args = sys.argv[1:]
    query, max_snd, workers = "", 9_999_999, 8
    clean: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--max" and i + 1 < len(args):
            try:
                max_snd = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif args[i] == "--workers" and i + 1 < len(args):
            try:
                workers = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            clean.append(args[i])
            i += 1
    if clean:
        query = " ".join(clean)

    print()
    print("  ==============================================")
    print("   BotonEra Scraper  //  myinstants.com")
    print("  ==============================================")
    print()
    if query:
        print(f"  Modo     : Busqueda  \"{query}\"")
    else:
        print(f"  Modo     : Todas las categorias ({len(ALL_SOURCES)} fuentes)")
    print(f"  Destino  : {SOUNDS_DIR}")
    if max_snd < 9_999_999:
        print(f"  Limite   : {max_snd} sonidos")
    print(f"  Hilos DL : {workers}")
    print("  " + "-" * 44)

    SOUNDS_DIR.mkdir(exist_ok=True)
    existing_files = {f.name for f in SOUNDS_DIR.glob("*.mp3")}
    cfg = load_config()
    existing_paths = {s["path"] for s in cfg.get("sounds", [])}

    seen_urls: set[str] = set()  # MP3 paths seen this run — deduplicates across sources
    all_items: list[dict] = []

    if query:
        print(f"\n  Buscando \"{query}\"...")
        items = collect_sounds_search(query, max_snd, seen_urls)
        all_items.extend(items)
        print(f"\n  {len(all_items)} sonidos encontrados.")
    else:
        print("\n  Recorriendo todas las categorias...\n")
        for label, base_url in ALL_SOURCES:
            remaining = max_snd - len(all_items)
            if remaining <= 0:
                break
            print(f"  >> {label}")
            items = collect_from_source(label, base_url, remaining, seen_urls)
            all_items.extend(items)
            print(f"     {len(items)} sonidos nuevos  |  Total acumulado: {len(all_items)}\n")
        print(f"  {len(all_items)} sonidos unicos en total.\n")

    if not all_items:
        print("  ERROR: No se encontraron sonidos.")
        return

    print("  " + "-" * 44)
    print(f"  Descargando {len(all_items)} sonidos con {workers} hilos...\n")

    downloaded, skipped, failed = 0, 0, 0
    new_entries: list[dict] = []
    total = len(all_items)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {
            pool.submit(download_one, item, SOUNDS_DIR, existing_files): item
            for item in all_items
        }
        done = 0
        for future in as_completed(future_map):
            done += 1
            try:
                name, dest = future.result()
            except Exception as e:
                print(f"    [{done:05d}/{total}] ERROR: {e}")
                failed += 1
                continue
            if dest is None:
                failed += 1
                continue
            dest_str = str(dest)
            if dest_str in existing_paths:
                skipped += 1
                continue
            new_entries.append({
                "id": uuid.uuid4().hex[:12],
                "name": name,
                "path": dest_str,
                "color": random.choice(COLORS),
                "emoji": random.choice(EMOJIS),
                "keybind": "",
            })
            existing_paths.add(dest_str)
            downloaded += 1

    if new_entries:
        cfg.setdefault("sounds", []).extend(new_entries)
        save_config(cfg)

    print()
    print("  " + "-" * 44)
    print("  LISTO!")
    print(f"    Descargados : {downloaded}")
    print(f"    Ya existian : {skipped}")
    print(f"    Fallidos    : {failed}")
    print(f"  Carpeta : {SOUNDS_DIR}")
    print(f"  config.json actualizado con {downloaded} entradas nuevas.")
    if downloaded:
        print("\n  Abri (o reinicia) BotonEra para ver los sonidos!")
    print()


if __name__ == "__main__":
    main()
