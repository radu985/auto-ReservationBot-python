"""
VFS Global Guinea-Bissau Website Automation Module
Handles website monitoring, auto-booking, and Cloudflare bypass
"""

import time
import os
import sys
import random
import json
import logging
import ssl
import urllib3
import requests
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import base64
import subprocess
import platform

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:  # Selenium not installed in this environment
    webdriver = None
    By = WebDriverWait = Select = EC = Options = ActionChains = Keys = None
    TimeoutException = NoSuchElementException = WebDriverException = Exception

try:
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext, expect
except ImportError:  # Playwright not installed in this environment
    sync_playwright = None
    Browser = Page = BrowserContext = None
    def expect(*args, **kwargs):  # type: ignore
        return None

# Handle both direct execution and module import
try:
    from PyQt6 import QtCore
    from .csv_io import ClientRecord, load_clients
except ImportError:
    try:
        from PyQt6 import QtCore
        from csv_io import ClientRecord, load_clients
    except ImportError:
        try:
            from PyQt5 import QtCore
            from csv_io import ClientRecord, load_clients
        except ImportError:
            # Fallback for when PyQt is not available
            QtCore = None
            from csv_io import ClientRecord, load_clients


@dataclass
class BookingResult:
    """Result of a booking attempt."""
    success: bool
    booking_reference: Optional[str] = None
    error_message: Optional[str] = None
    client_email: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class AvailabilityStatus:
    """Website availability status."""
    available: bool
    slots_count: int = 0
    next_available_date: Optional[str] = None
    last_checked: Optional[str] = None
    error_message: Optional[str] = None


class VFSAutomation:
    """Main VFS Global Guinea-Bissau automation class."""
    
    def __init__(self, headless: bool = False, use_playwright: bool = True):
        self.headless = headless
        self.use_playwright = use_playwright
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.driver = None
        
        # VFS Guinea-Bissau URLs (default to Guinea‑Bissau / Portuguese / Portugal)
        self.base_url = "https://visa.vfsglobal.com"
        self.booking_url = "https://visa.vfsglobal.com/gnb/pt/prt/book-appointment"
        self.login_url = "https://visa.vfsglobal.com/gnb/pt/prt/login"
        
        # Enhanced rate limiting settings
        self.min_delay = 3
        self.max_delay = 8
        self.max_retries = 5
        self.monitoring_duration = 4  # minutes
        
        # Cloudflare bypass settings
        self.user_agents = self._get_stealth_user_agents()
        self.current_user_agent = None
        self.session_id = self._generate_session_id()
        
        # Setup logging first
        self._setup_logging()
        
        # Advanced bypass settings
        self.proxy_list = self._load_proxy_list()
        self.current_proxy = None
        self.proxy_rotation_enabled = True
        self.captcha_solving_enabled = True
        self.browser_fingerprint_rotation = True
        
        # Safety and detection avoidance
        self.request_count = 0
        self.last_request_time = 0
        self.cf_challenge_detected = False
        self.stealth_mode = True
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        self.bypass_attempts = 0
        self.max_bypass_attempts = 10
        # Quarantine list for bad proxies (epoch seconds)
        self.quarantined_proxies: Dict[str, float] = {}
        # Backoff for WAF/CF blocks
        self.block_backoff_seconds = 60
        self.block_backoff_multiplier = 1.5
        self.block_backoff_max = 300

    def environment_ready(self) -> Tuple[bool, str]:
        """Quick check that required browser backends are available."""
        if self.use_playwright and sync_playwright is None:
            return False, "Playwright not installed. Run: pip install playwright && python -m playwright install"
        if not self.use_playwright and webdriver is None:
            return False, "Selenium not installed. Run: pip install selenium"
        return True, "ok"
        
        # Disable SSL warnings for stealth
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def _setup_logging(self) -> None:
        """Setup logging for automation."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('vfs_automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _random_delay(self) -> None:
        """Add random delay to avoid detection."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        
    def _get_stealth_user_agents(self) -> List[str]:
        """Get comprehensive list of stealth user agents."""
        return [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        ]
    
    def _get_user_agent(self) -> str:
        """Get random user agent to avoid detection."""
        if not self.current_user_agent:
            self.current_user_agent = random.choice(self.user_agents)
        return self.current_user_agent
    
    def _rotate_user_agent(self) -> str:
        """Rotate to a new user agent."""
        self.current_user_agent = random.choice(self.user_agents)
        self.logger.info(f"Rotated to new user agent: {self.current_user_agent[:50]}...")
        return self.current_user_agent
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for tracking."""
        timestamp = str(int(time.time()))
        random_bytes = str(random.randint(100000, 999999))
        return hashlib.md5(f"{timestamp}{random_bytes}".encode()).hexdigest()[:16]
    
    def _load_proxy_list(self) -> List[Dict[str, str]]:
        """Load proxy list from file or create default list."""
        proxy_file = Path("proxies.txt")
        proxies = []
        
        if proxy_file.exists():
            try:
                with open(proxy_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            parts = line.split(':')
                            if len(parts) >= 2:
                                proxy = {
                                    'host': parts[0],
                                    'port': parts[1],
                                    'username': parts[2] if len(parts) > 2 else None,
                                    'password': parts[3] if len(parts) > 3 else None
                                }
                                proxies.append(proxy)
            except Exception as e:
                self.logger.warning(f"Failed to load proxy list: {e}")
        
        # Add some free proxy services as fallback
        if not proxies:
            proxies = [
                {'host': '8.8.8.8', 'port': '8080', 'username': None, 'password': None},
                {'host': '1.1.1.1', 'port': '8080', 'username': None, 'password': None},
                {'host': '9.9.9.9', 'port': '8080', 'username': None, 'password': None}
            ]
        
        self.logger.info(f"Loaded {len(proxies)} proxies")
        return proxies
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the list."""
        if not self.proxy_list or not self.proxy_rotation_enabled:
            return None
        
        proxy = random.choice(self.proxy_list)
        self.current_proxy = proxy
        self.logger.info(f"Using proxy: {proxy['host']}:{proxy['port']}")
        return proxy
    
    def _rotate_proxy(self) -> Optional[Dict[str, str]]:
        """Rotate to a new proxy."""
        if not self.proxy_list or not self.proxy_rotation_enabled:
            return None
        
        # Remove current proxy and quarantined proxies from rotation temporarily
        now = time.time()
        available_proxies = []
        for p in self.proxy_list:
            key = f"{p.get('host')}:{p.get('port')}"
            if p == self.current_proxy:
                continue
            expiry = self.quarantined_proxies.get(key)
            if expiry and expiry > now:
                continue
            available_proxies.append(p)
        
        # Cleanup expired quarantines
        self.quarantined_proxies = {k: v for k, v in self.quarantined_proxies.items() if v > now}
        if not available_proxies:
            available_proxies = self.proxy_list
        
        proxy = random.choice(available_proxies)
        self.current_proxy = proxy
        self.logger.info(f"Rotated to proxy: {proxy['host']}:{proxy['port']}")
        return proxy
    
    def _test_proxy(self, proxy: Dict[str, str]) -> bool:
        """Test if a proxy is working."""
        try:
            proxy_url = f"http://{proxy['host']}:{proxy['port']}"
            proxies = {'http': proxy_url, 'https': proxy_url}
            
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def _get_browser_fingerprint(self) -> Dict[str, any]:
        """Generate a realistic browser fingerprint."""
        screen_resolutions = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1600, 'height': 900}
        ]
        
        timezones = [
            'Europe/London', 'America/New_York', 'Europe/Paris',
            'Asia/Tokyo', 'Australia/Sydney', 'America/Los_Angeles'
        ]
        
        languages = [
            ['en-US', 'en'], ['en-GB', 'en'], ['pt-PT', 'pt'],
            ['fr-FR', 'fr'], ['de-DE', 'de'], ['es-ES', 'es']
        ]
        
        return {
            'viewport': random.choice(screen_resolutions),
            'timezone': random.choice(timezones),
            'languages': random.choice(languages),
            'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
            'hardware_concurrency': random.choice([2, 4, 8, 16]),
            'device_memory': random.choice([2, 4, 8, 16]),
            'connection': {
                'effectiveType': random.choice(['3g', '4g', '5g']),
                'rtt': random.randint(50, 200),
                'downlink': random.uniform(1.0, 10.0)
            }
        }
    
    def _solve_captcha(self, page_content: str) -> bool:
        """Attempt to solve CAPTCHA challenges."""
        if not self.captcha_solving_enabled:
            return False
        
        try:
            # Check for common CAPTCHA types
            captcha_indicators = [
                'captcha', 'recaptcha', 'hcaptcha', 'cloudflare',
                'challenge', 'verification', 'robot'
            ]
            
            if not any(indicator in page_content.lower() for indicator in captcha_indicators):
                return False
            
            self.logger.info("CAPTCHA detected, attempting to solve...")
            
            # Strategy 1: Wait for auto-solve (some CAPTCHAs solve themselves)
            for delay in [5, 10, 15, 20]:
                time.sleep(delay)
                if not self._detect_cloudflare_challenge(page_content):
                    self.logger.info("CAPTCHA auto-solved")
                    return True
            
            # Strategy 2: Try to find and click solve button
            if self.use_playwright and self.page:
                solve_buttons = [
                    'button[class*="solve"]',
                    'button[class*="verify"]',
                    'button[class*="challenge"]',
                    'input[type="submit"][value*="solve"]',
                    'input[type="submit"][value*="verify"]'
                ]
                
                for button_selector in solve_buttons:
                    try:
                        button = self.page.query_selector(button_selector)
                        if button and button.is_visible():
                            button.click()
                            self.logger.info("Clicked CAPTCHA solve button")
                            time.sleep(5)
                            return True
                    except:
                        continue
            
            # Strategy 3: Use external CAPTCHA solving service (placeholder)
            # In production, integrate with services like 2captcha, anti-captcha, etc.
            self.logger.warning("CAPTCHA solving not implemented - manual intervention required")
            return False
            
        except Exception as e:
            self.logger.error(f"CAPTCHA solving failed: {e}")
            return False
    
    def _inject_advanced_stealth_scripts(self) -> None:
        """Inject advanced stealth scripts to avoid detection."""
        if not self.use_playwright or not self.page:
            return
        
        try:
            fingerprint = self._get_browser_fingerprint()
            
            advanced_stealth_script = """
            // Advanced Cloudflare and bot detection bypass
            
            // 1. Remove webdriver traces (check if property exists first)
            if (navigator.hasOwnProperty('webdriver')) {{
                try {{
                    delete navigator.webdriver;
                }} catch (e) {{
                    // Property cannot be deleted, skip
                }}
            }}
            
            if (!navigator.hasOwnProperty('webdriver')) {{
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                    configurable: true
                }});
            }}
            
            // 2. Mock realistic browser properties
            try { const __p = Object.getOwnPropertyDescriptor(navigator,'platform'); if(!__p || __p.configurable){ Object.defineProperty(navigator,'platform',{ get: () => __PLATFORM__, configurable: true }); } } catch(e){}
            
            try { const __hc = Object.getOwnPropertyDescriptor(navigator,'hardwareConcurrency'); if(!__hc || __hc.configurable){ Object.defineProperty(navigator,'hardwareConcurrency',{ get: () => __HC__, configurable: true }); } } catch(e){}
            
            try { const __dm = Object.getOwnPropertyDescriptor(navigator,'deviceMemory'); if(!__dm || __dm.configurable){ Object.defineProperty(navigator,'deviceMemory',{ get: () => __DM__, configurable: true }); } } catch(e){}
            
            // 3. Mock screen properties
            try { Object.defineProperty(screen,'width',{ get: () => __VW__, configurable: true }); } catch(e){}
            try { Object.defineProperty(screen,'height',{ get: () => __VH__, configurable: true }); } catch(e){}
            try { Object.defineProperty(screen,'availWidth',{ get: () => __VW__, configurable: true }); } catch(e){}
            try { Object.defineProperty(screen,'availHeight',{ get: () => (__VH__ - 40), configurable: true }); } catch(e){}
            
            // 4. Mock connection
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    effectiveType: __ET__,
                    rtt: __RTT__,
                    downlink: __DOWNLINK__,
                    saveData: false
                }}),
            }});
            
            // 5. Mock languages (guarded)
            try {
                const __langDesc = Object.getOwnPropertyDescriptor(navigator, 'languages');
                if (!__langDesc || __langDesc.configurable) {
                    Object.defineProperty(navigator, 'languages', {{
                        get: () => __LANGUAGES__,
                        configurable: true
                    }});
                }
            } catch (e) {}
            
            // 6. Mock plugins with realistic data
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [
                    {{
                        name: 'Chrome PDF Plugin',
                        filename: 'internal-pdf-viewer',
                        description: 'Portable Document Format'
                    }},
                    {{
                        name: 'Chrome PDF Viewer',
                        filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                        description: ''
                    }},
                    {{
                        name: 'Native Client',
                        filename: 'internal-nacl-plugin',
                        description: ''
                    }},
                    {{
                        name: 'Widevine Content Decryption Module',
                        filename: 'widevinecdmadapter.dll',
                        description: 'Enables Widevine licenses for playback of HTML audio/video content.'
                    }}
                ],
                configurable: true
            }});
            
            // 7. Mock chrome object
            window.chrome = {{
                runtime: {{
                    onConnect: undefined,
                    onMessage: undefined,
                }},
                loadTimes: function() {{ return {{}}; }},
                csi: function() {{ return {{}}; }},
                app: {{
                    isInstalled: false,
                    InstallState: {{
                        DISABLED: 'disabled',
                        INSTALLED: 'installed',
                        NOT_INSTALLED: 'not_installed'
                    }},
                    RunningState: {{
                        CANNOT_RUN: 'cannot_run',
                        READY_TO_RUN: 'ready_to_run',
                        RUNNING: 'running'
                    }}
                }}
            }};
            
            // 8. Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Reflect;
            
            // 9. Mock permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
            
            // 10. Mock battery API
            Object.defineProperty(navigator, 'getBattery', {{
                get: () => () => Promise.resolve({{
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                }}),
            }});
            
            // 11. Mock media devices
            Object.defineProperty(navigator, 'mediaDevices', {{
                get: () => ({{
                    enumerateDevices: () => Promise.resolve([]),
                    getUserMedia: () => Promise.reject(new Error('Permission denied')),
                    getDisplayMedia: () => Promise.reject(new Error('Permission denied'))
                }}),
            }});
            
            // 12. Simulate human-like behavior
            let mouseX = 0, mouseY = 0;
            document.addEventListener('mousemove', (e) => {{
                mouseX = e.clientX;
                mouseY = e.clientY;
            }});
            
            // Random mouse movements
            setInterval(() => {{
                if (Math.random() < 0.1) {{
                    const event = new MouseEvent('mousemove', {{
                        clientX: mouseX + (Math.random() - 0.5) * 10,
                        clientY: mouseY + (Math.random() - 0.5) * 10
                    }});
                    document.dispatchEvent(event);
                }}
            }}, 1000);
            
            // Random clicks
            setInterval(() => {{
                if (Math.random() < 0.05) {{
                    const event = new MouseEvent('click', {{
                        clientX: mouseX,
                        clientY: mouseY
                    }});
                    document.dispatchEvent(event);
                }}
            }}, 2000);
            
            // Random scroll events
            setInterval(() => {{
                if (Math.random() < 0.1) {{
                    window.scrollBy(0, (Math.random() - 0.5) * 10);
                }}
            }}, 3000);
            
            console.log('Advanced stealth mode activated');
            """
            
            # Replace placeholders safely
            replaced_script = advanced_stealth_script
            try:
                replaced_script = replaced_script.replace("__PLATFORM__", json.dumps(fingerprint['platform']))
                replaced_script = replaced_script.replace("__HC__", str(fingerprint['hardware_concurrency']))
                replaced_script = replaced_script.replace("__DM__", str(fingerprint['device_memory']))
                replaced_script = replaced_script.replace("__VW__", str(fingerprint['viewport']['width']))
                replaced_script = replaced_script.replace("__VH__", str(fingerprint['viewport']['height']))
                replaced_script = replaced_script.replace("__ET__", json.dumps(fingerprint['connection']['effectiveType']))
                replaced_script = replaced_script.replace("__RTT__", str(fingerprint['connection']['rtt']))
                replaced_script = replaced_script.replace("__DOWNLINK__", str(fingerprint['connection']['downlink']))
                replaced_script = replaced_script.replace("__LANGUAGES__", json.dumps(fingerprint['languages']))
            except Exception:
                pass
            
            # Ensure script runs before any page scripts
            try:
                self.context.add_init_script(replaced_script)
            except Exception:
                pass
            self.page.evaluate(replaced_script)
            self.logger.info("Advanced stealth scripts injected successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to inject stealth scripts: {e}")
    
    def _rotate_browser_fingerprint(self) -> None:
        """Rotate browser fingerprint to avoid detection."""
        if not self.browser_fingerprint_rotation:
            return
        
        try:
            if self.use_playwright and self.page:
                # Generate new fingerprint
                fingerprint = self._get_browser_fingerprint()
                
                # Update viewport
                self.page.set_viewport_size({
                    'width': fingerprint['viewport']['width'],
                    'height': fingerprint['viewport']['height']
                })
                
                # Update user agent
                new_ua = random.choice(self.user_agents)
                self.current_user_agent = new_ua
                
                # Re-inject stealth scripts with new fingerprint
                self._inject_advanced_stealth_scripts()
                
                self.logger.info("Browser fingerprint rotated successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to rotate browser fingerprint: {e}")
    
    def _detect_cloudflare_challenge(self, page_content: str) -> bool:
        """Detect if Cloudflare challenge is present."""
        cf_indicators = [
            "Checking your browser before accessing",
            "This process is automatic",
            "cloudflare",
            "cf-challenge",
            "cf-browser-verification",
            "DDoS protection by Cloudflare"
        ]
        akamai_indicators = [
            "Acesso restrito devido a atividade incomum",
            "403201",
            "atividade incomum",
            "Your access has been temporarily restricted",
            "activity from your network is unusual"
        ]
        text = page_content.lower()
        return any(ind.lower() in text for ind in cf_indicators) or any(ind.lower() in text for ind in akamai_indicators)
    
    def _handle_cloudflare_challenge(self) -> bool:
        """Handle Cloudflare challenge with advanced multi-strategy bypass."""
        self.logger.warning("Edge/WAF challenge detected (Cloudflare/Akamai). Implementing advanced bypass...")
        self.cf_challenge_detected = True
        self.bypass_attempts += 1
        
        if self.bypass_attempts > self.max_bypass_attempts:
            self.logger.error(f"Maximum bypass attempts ({self.max_bypass_attempts}) exceeded")
            return False
        
        # Strategy 1: Advanced stealth scripts with fingerprint rotation
        if self._try_advanced_stealth_bypass():
            return True
            
        # Strategy 2: Proxy rotation with stealth (quarantine current proxy)
        if self._try_proxy_rotation_bypass(quarantine_current=True):
            return True
            
        # Strategy 3: CAPTCHA solving
        if self._try_captcha_solving_bypass():
            return True
            
        # Strategy 4: Browser restart with new fingerprint
        if self._try_browser_restart():
            return True
            
        # Strategy 5: Selenium fallback with proxy
        if self._try_selenium_fallback():
            return True
            
        # Strategy 6: Basic wait with user agent rotation (fallback)
        if self._try_basic_cf_bypass():
            return True
            
        # Strategy 7: Enhanced user agent rotation with headers
        if self._try_enhanced_ua_rotation():
            return True
            
        # Strategy 8: Header spoofing bypass
        if self._try_header_spoofing_bypass():
            return True
            
        # Strategy 9: JavaScript challenge solving
        if self._try_javascript_challenge_bypass():
            return True
            
        # Strategy 10: Multi-browser approach
        if self._try_multi_browser_bypass():
            return True
            
        self.logger.error("All Cloudflare bypass strategies failed")
        # Exponential backoff before next attempt/run
        try:
            wait_s = int(self.block_backoff_seconds)
            self.logger.warning(f"Backing off for {wait_s}s before next attempt...")
            time.sleep(wait_s)
            self.block_backoff_seconds = min(
                int(self.block_backoff_seconds * self.block_backoff_multiplier),
                self.block_backoff_max
            )
        except Exception:
            pass
        return False
    
    def _try_enhanced_ua_rotation(self) -> bool:
        """Enhanced user agent rotation with realistic headers."""
        try:
            self.logger.info("Attempting enhanced user agent rotation bypass...")
            
            if self.use_playwright and self.page:
                # Rotate to a more realistic user agent
                realistic_uas = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
                ]
                
                new_ua = random.choice(realistic_uas)
                self.current_user_agent = new_ua
                
                # Update user agent and headers
                self.page.evaluate(f"""
                    Object.defineProperty(navigator, 'userAgent', {{
                        get: () => '{new_ua}',
                        configurable: true
                    }});
                """)
                
                # Set realistic headers
                self.page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                })
                
                # Wait and check
                for delay in [5000, 10000, 15000]:
                    self.page.wait_for_timeout(delay)
                    content = self.page.content()
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Enhanced UA rotation bypass successful")
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.error(f"Enhanced UA rotation bypass failed: {e}")
            return False
    
    def _try_header_spoofing_bypass(self) -> bool:
        """Try header spoofing to bypass Cloudflare."""
        try:
            self.logger.info("Attempting header spoofing bypass...")
            
            if self.use_playwright and self.page:
                # Spoof realistic headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                }
                
                self.page.set_extra_http_headers(headers)
                
                # Navigate with spoofed headers
                self.page.goto(self.booking_url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait and check
                for delay in [3000, 6000, 9000]:
                    self.page.wait_for_timeout(delay)
                    content = self.page.content()
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Header spoofing bypass successful")
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.error(f"Header spoofing bypass failed: {e}")
            return False
    
    def _try_javascript_challenge_bypass(self) -> bool:
        """Try to solve JavaScript challenges."""
        try:
            self.logger.info("Attempting JavaScript challenge bypass...")
            
            if self.use_playwright and self.page:
                # Execute challenge-solving JavaScript
                challenge_script = """
                // Wait for challenge to load
                setTimeout(() => {
                    // Look for challenge elements
                    const challengeElements = document.querySelectorAll('[data-ray], [id*="challenge"], [class*="challenge"]');
                    
                    if (challengeElements.length > 0) {
                        // Simulate human interaction
                        challengeElements.forEach(element => {
                            element.click();
                            element.dispatchEvent(new Event('mouseover'));
                            element.dispatchEvent(new Event('mouseout'));
                        });
                        
                        // Wait for challenge to complete
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    }
                }, 1000);
                """
                
                self.page.evaluate(challenge_script)
                
                # Wait for challenge resolution
                for delay in [5000, 10000, 15000, 20000]:
                    self.page.wait_for_timeout(delay)
                    content = self.page.content()
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("JavaScript challenge bypass successful")
                        return True
                        
            return False
            
        except Exception as e:
            self.logger.error(f"JavaScript challenge bypass failed: {e}")
            return False
    
    def _try_multi_browser_bypass(self) -> bool:
        """Try switching between different browser engines."""
        try:
            self.logger.info("Attempting multi-browser bypass...")
            
            # Switch browser engine
            original_use_playwright = self.use_playwright
            
            try:
                # Stop current browser
                self.stop_browser()
                time.sleep(2)
                
                # Switch to alternative browser
                self.use_playwright = not original_use_playwright
                
                # Start new browser
                if self.use_playwright:
                    success = self._start_playwright()
                else:
                    success = self._start_selenium()
                
                if success:
                    # Navigate and check
                    if self.use_playwright and self.page:
                        self.page.goto(self.booking_url, wait_until='domcontentloaded', timeout=30000)
                        time.sleep(5)
                        content = self.page.content()
                    else:
                        self.driver.get(self.booking_url)
                        time.sleep(5)
                        content = self.driver.page_source
                    
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Multi-browser bypass successful")
                        return True
                
            finally:
                # Restore original browser preference
                self.use_playwright = original_use_playwright
                
            return False
            
        except Exception as e:
            self.logger.error(f"Multi-browser bypass failed: {e}")
            return False
    
    def _try_basic_cf_bypass(self) -> bool:
        """Try basic Cloudflare bypass with user agent rotation."""
        try:
            if self.use_playwright and self.page:
                # Rotate user agent
                new_ua = random.choice(self.user_agents)
                self.current_user_agent = new_ua
                self.logger.info(f"Rotating to user agent: {new_ua[:50]}...")
                
                # Update user agent
                self.page.evaluate(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{new_ua}'}})")
                
                # Wait with progressive delays
                for delay in [3000, 5000, 8000, 12000]:
                    self.page.wait_for_timeout(delay)
                    content = self.page.content()
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Basic CF bypass successful with user agent rotation")
                        return True
                        
            elif self.driver:
                # Selenium approach
                new_ua = random.choice(self.user_agents)
                self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{new_ua}'}})")
                
                for delay in [3, 5, 8, 12]:
                    time.sleep(delay)
                    content = self.driver.page_source
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Basic CF bypass successful with Selenium")
                        return True
                        
        except Exception as e:
            self.logger.debug(f"Basic CF bypass failed: {str(e)}")
            
        return False
    
    def _try_js_challenge_solving(self) -> bool:
        """Try JavaScript challenge solving."""
        try:
            if self.use_playwright and self.page:
                self.logger.info("Attempting JavaScript challenge solving...")
                
                # Inject advanced stealth scripts
                stealth_script = """
                // Advanced Cloudflare bypass techniques
                if (navigator.hasOwnProperty('webdriver')) {
                    try {
                        delete navigator.webdriver;
                    } catch (e) {
                        // Property cannot be deleted, skip
                    }
                }
                
                if (!navigator.hasOwnProperty('webdriver')) {
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                }
                
                // Mock more browser properties
                Object.defineProperty(navigator, 'plugins', {
                    get: () => Array.from({length: 5}, (_, i) => ({
                        name: `Plugin ${i}`,
                        filename: `plugin-${i}.dll`,
                        description: `Plugin ${i} Description`
                    })),
                });
                
                // Mock screen properties
                Object.defineProperty(screen, 'width', {get: () => 1920});
                Object.defineProperty(screen, 'height', {get: () => 1080});
                Object.defineProperty(screen, 'availWidth', {get: () => 1920});
                Object.defineProperty(screen, 'availHeight', {get: () => 1040});
                
                // Mock connection
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 50,
                        downlink: 2,
                        saveData: false
                    }),
                });
                
                // Remove automation traces
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Mock chrome object
                window.chrome = {
                    runtime: {
                        onConnect: undefined,
                        onMessage: undefined,
                    },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: {}
                };
                
                // Simulate human-like behavior
                setTimeout(() => {
                    document.dispatchEvent(new Event('mousemove'));
                    document.dispatchEvent(new Event('click'));
                }, 1000);
                """
                
                self.page.evaluate(stealth_script)
                
                # Wait for challenge resolution
                for delay in [5000, 10000, 15000]:
                    self.page.wait_for_timeout(delay)
                    content = self.page.content()
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("JavaScript challenge solving successful")
                        return True
                        
        except Exception as e:
            self.logger.debug(f"JavaScript challenge solving failed: {str(e)}")
            
        return False
    
    def _try_browser_restart(self) -> bool:
        """Try restarting browser with new fingerprint."""
        try:
            self.logger.info("Attempting browser restart with new fingerprint...")
            
            # Stop current browser
            if self.use_playwright:
                if self.page:
                    self.page.close()
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
            elif self.driver:
                self.driver.quit()
            
            # Wait before restart
            time.sleep(5)
            
            # Restart with new fingerprint
            if self.start_browser():
                # Navigate to target URL
                if self.use_playwright:
                    self.page.goto(self.booking_url, wait_until='networkidle', timeout=30000)
                else:
                    self.driver.get(self.booking_url)
                
                # Check if challenge is resolved
                if self.use_playwright:
                    content = self.page.content()
                else:
                    content = self.driver.page_source
                    
                if not self._detect_cloudflare_challenge(content):
                    self.logger.info("Browser restart bypass successful")
                    return True
                    
        except Exception as e:
            self.logger.debug(f"Browser restart failed: {str(e)}")
            
        return False
    
    def _try_selenium_fallback(self) -> bool:
        """Try Selenium as fallback when Playwright fails."""
        try:
            if self.use_playwright:
                self.logger.info("Attempting Selenium fallback...")
                
                # Stop Playwright
                if self.page:
                    self.page.close()
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                
                # Switch to Selenium
                self.use_playwright = False
                if self.start_browser():
                    self.driver.get(self.booking_url)
                    time.sleep(10)  # Wait for page load
                    
                    content = self.driver.page_source
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Selenium fallback successful")
                        return True
                        
        except Exception as e:
            self.logger.debug(f"Selenium fallback failed: {str(e)}")
            
        return False
    
    def _try_advanced_stealth_bypass(self) -> bool:
        """Try advanced stealth bypass with fingerprint rotation."""
        try:
            if self.use_playwright and self.page:
                self.logger.info("Attempting advanced stealth bypass...")
                
                # Rotate browser fingerprint
                self._rotate_browser_fingerprint()
                
                # Inject advanced stealth scripts
                self._inject_advanced_stealth_scripts()
                
                # Wait with progressive delays
                for delay in [3000, 5000, 8000, 12000, 15000]:
                    self.page.wait_for_timeout(delay)
                    content = self.page.content()
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Advanced stealth bypass successful")
                        return True
                        
            elif self.driver:
                # Selenium approach with advanced stealth
                self.logger.info("Attempting Selenium advanced stealth bypass...")
                
                # Execute advanced stealth script
                stealth_script = """
                if (navigator.hasOwnProperty('webdriver')) {
                    try {
                        delete navigator.webdriver;
                    } catch (e) {
                        // Property cannot be deleted, skip
                    }
                }
                
                if (!navigator.hasOwnProperty('webdriver')) {
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                }
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', filename: 'internal-nacl-plugin'}
                    ],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'pt-PT', 'pt'],
                });
                
                window.chrome = {
                    runtime: { onConnect: undefined, onMessage: undefined },
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: {}
                };
                
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                """
                
                self.driver.execute_script(stealth_script)
                
                for delay in [3, 5, 8, 12, 15]:
                    time.sleep(delay)
                    content = self.driver.page_source
                    if not self._detect_cloudflare_challenge(content):
                        self.logger.info("Selenium advanced stealth bypass successful")
                        return True
                        
        except Exception as e:
            self.logger.debug(f"Advanced stealth bypass failed: {str(e)}")
            
        return False
    
    def _try_proxy_rotation_bypass(self, quarantine_current: bool = False) -> bool:
        """Try proxy rotation bypass.
        quarantine_current: if True, put the current proxy in a short-term blacklist after a block.
        """
        try:
            if not self.proxy_list:
                return False
                
            self.logger.info("Attempting proxy rotation bypass...")
            
            # Try up to 3 different proxies
            for attempt in range(3):
                proxy = self._rotate_proxy()
                if not proxy:
                    continue
                
                # Test proxy first
                if not self._test_proxy(proxy):
                    self.logger.warning(f"Proxy {proxy['host']}:{proxy['port']} failed test, trying next...")
                    continue
                
                # Restart browser with proxy
                if self._restart_browser_with_proxy(proxy):
                    # Wait and check if challenge is resolved
                    for delay in [5000, 10000, 15000]:
                        time.sleep(delay / 1000)
                        if self.use_playwright:
                            content = self.page.content()
                        else:
                            content = self.driver.page_source
                            
                        if not self._detect_cloudflare_challenge(content):
                            self.logger.info(f"Proxy rotation bypass successful with {proxy['host']}:{proxy['port']}")
                            return True

            # Quarantine current proxy after failed attempts
            if quarantine_current and self.current_proxy:
                key = f"{self.current_proxy.get('host')}:{self.current_proxy.get('port')}"
                self.quarantined_proxies[key] = time.time() + 60 * 30  # 30 minutes
                self.logger.warning(f"Quarantined proxy {key} for 30 minutes due to block")
                
        except Exception as e:
            self.logger.debug(f"Proxy rotation bypass failed: {str(e)}")
            
        return False
    
    def _try_captcha_solving_bypass(self) -> bool:
        """Try CAPTCHA solving bypass."""
        try:
            if not self.captcha_solving_enabled:
                return False
                
            self.logger.info("Attempting CAPTCHA solving bypass...")
            
            if self.use_playwright and self.page:
                content = self.page.content()
                if self._solve_captcha(content):
                    # Wait for resolution
                    for delay in [5000, 10000, 15000]:
                        self.page.wait_for_timeout(delay)
                        content = self.page.content()
                        if not self._detect_cloudflare_challenge(content):
                            self.logger.info("CAPTCHA solving bypass successful")
                            return True
            elif self.driver:
                content = self.driver.page_source
                if self._solve_captcha(content):
                    for delay in [5, 10, 15]:
                        time.sleep(delay)
                        content = self.driver.page_source
                        if not self._detect_cloudflare_challenge(content):
                            self.logger.info("CAPTCHA solving bypass successful")
                            return True
                            
        except Exception as e:
            self.logger.debug(f"CAPTCHA solving bypass failed: {str(e)}")
            
        return False
    
    def _restart_browser_with_proxy(self, proxy: Dict[str, str]) -> bool:
        """Restart browser with proxy configuration."""
        try:
            # Stop current browser
            if self.use_playwright:
                if self.page:
                    self.page.close()
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
            elif self.driver:
                self.driver.quit()
            
            # Wait before restart
            time.sleep(3)
            
            # Configure proxy
            proxy_url = f"http://{proxy['host']}:{proxy['port']}"
            if proxy['username'] and proxy['password']:
                proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            
            # Restart with proxy
            if self.use_playwright:
                return self._start_playwright_with_proxy(proxy_url)
            else:
                return self._start_selenium_with_proxy(proxy_url)
                
        except Exception as e:
            self.logger.error(f"Failed to restart browser with proxy: {e}")
            return False
    
    def _start_playwright_with_proxy(self, proxy_url: str) -> bool:
        """Start Playwright with proxy configuration."""
        try:
            self.playwright = sync_playwright().start()
            
            # Advanced stealth arguments with proxy
            stealth_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-logging',
                '--disable-gpu-logging',
                '--silent',
                '--log-level=3',
                '--user-agent=' + self._get_user_agent(),
                f'--proxy-server={proxy_url}'
            ]
            
            # Launch browser with proxy
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=stealth_args,
                ignore_default_args=['--enable-automation']
            )
            
            # Create context with proxy
            self.context = self.browser.new_context(
                user_agent=self._get_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='Europe/London',
                permissions=['geolocation'],
                geolocation={'latitude': 11.8037, 'longitude': -15.1804},
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none',
                proxy={'server': proxy_url}
            )
            
            # Inject stealth scripts
            self.context.add_init_script(self._get_stealth_script())
            
            self.page = self.context.new_page()
            
            # Set headers
            self.page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })
            
            self.logger.info(f"Playwright started with proxy: {proxy_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Playwright with proxy: {e}")
            return False
    
    def _start_selenium_with_proxy(self, proxy_url: str) -> bool:
        """Start Selenium with proxy configuration."""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
            
            # Anti-detection arguments with proxy
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument(f'--user-agent={self._get_user_agent()}')
            options.add_argument(f'--proxy-server={proxy_url}')
            
            # Additional stealth options
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            
            # Execute stealth script
            self.driver.execute_script(self._get_stealth_script())
            
            self.logger.info(f"Selenium started with proxy: {proxy_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Selenium with proxy: {e}")
            return False
    
    def _get_stealth_script(self) -> str:
        """Get basic stealth script for injection."""
        return """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                {name: 'Native Client', filename: 'internal-nacl-plugin'}
            ],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'pt-PT', 'pt'],
        });
        
        window.chrome = {
            runtime: { onConnect: undefined, onMessage: undefined },
            loadTimes: function() { return {}; },
            csi: function() { return {}; },
            app: {}
        };
        
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """
    
    def start_browser(self) -> bool:
        """Start browser with anti-detection measures."""
        try:
            if self.use_playwright:
                return self._start_playwright()
            else:
                return self._start_selenium()
        except Exception as e:
            try:
                self.last_error = f"Failed to start browser: {str(e)}"
            except Exception:
                pass
            self.logger.error(f"Failed to start browser: {str(e)}")
            return False
            
    def _start_playwright(self) -> bool:
        """Start Playwright browser with advanced stealth settings."""
        try:
            # Ensure Playwright uses a stable browsers path next to the executable when frozen
            try:
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(sys.executable)
                else:
                    base_dir = str(Path(__file__).resolve().parents[2])
                browsers_dir = os.path.join(base_dir, 'pw-browsers')
                os.makedirs(browsers_dir, exist_ok=True)
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_dir
            except Exception:
                pass
            # Guard for asyncio loop: run Playwright startup in a dedicated thread if needed
            try:
                import asyncio
                if asyncio.get_event_loop().is_running():
                    from threading import Event, Thread
                    result_holder: Dict[str, any] = {}
                    done = Event()
                    def start_pw():
                        try:
                            result_holder['pw'] = sync_playwright().start()
                        except Exception as e:
                            result_holder['err'] = e
                        finally:
                            done.set()
                    t = Thread(target=start_pw, daemon=True)
                    t.start()
                    done.wait(timeout=30)
                    if 'err' in result_holder:
                        raise result_holder['err']
                    self.playwright = result_holder.get('pw')
                else:
                    self.playwright = sync_playwright().start()
            except Exception:
                self.playwright = sync_playwright().start()
            
            # Advanced stealth arguments
            stealth_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-plugins',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-logging',
                '--disable-gpu-logging',
                '--silent',
                '--log-level=3',
                '--user-agent=' + self._get_user_agent()
            ]
            
            # Launch browser with stealth options. Prefer local Chrome channel first to avoid downloads.
            try:
                self.browser = self.playwright.chromium.launch(
                    channel='chrome',
                    headless=self.headless,
                    args=stealth_args,
                    ignore_default_args=['--enable-automation']
                )
                self.logger.info("Launched Playwright using local Chrome channel.")
            except Exception as _ch_err:
                self.logger.warning(f"Chrome channel launch failed, falling back to bundled Chromium: {_ch_err}")
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless,
                    args=stealth_args,
                    ignore_default_args=['--enable-automation']
                )
            
            # Create context with advanced stealth settings
            self.context = self.browser.new_context(
                user_agent=self._get_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='Europe/London',
                permissions=['geolocation'],
                geolocation={'latitude': 11.8037, 'longitude': -15.1804},  # Guinea-Bissau coordinates
                color_scheme='light',
                reduced_motion='no-preference',
                forced_colors='none'
            )
            
            # Inject advanced stealth scripts
            self.context.add_init_script(self._get_stealth_script())
            
            self.page = self.context.new_page()
            
            # Set additional headers
            self.page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            })
            
            # Inject advanced stealth scripts after page creation
            self._inject_advanced_stealth_scripts()
            
            self.logger.info("Playwright browser started with advanced stealth mode")
            return True
            
        except Exception as e:
            try:
                self.last_error = f"Failed to start Playwright: {str(e)}"
            except Exception:
                pass
            self.logger.error(f"Failed to start Playwright: {str(e)}")
            return False
            
    def _start_selenium(self) -> bool:
        """Start Selenium WebDriver with stealth settings."""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument('--headless')
                
            # Anti-detection arguments
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument(f'--user-agent={self._get_user_agent()}')
            
            # Additional stealth options
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            
            # Execute stealth script
            self.driver.execute_script("""
                if (navigator.hasOwnProperty('webdriver')) {
                    try {
                        delete navigator.webdriver;
                    } catch (e) {
                        // Property cannot be deleted, skip
                    }
                }
                
                if (!navigator.hasOwnProperty('webdriver')) {
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                }
            """)
            
            self.logger.info("Selenium WebDriver started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Selenium: {str(e)}")
            return False
            
    def stop_browser(self) -> None:
        """Stop browser and cleanup."""
        try:
            if self.use_playwright:
                if self.page:
                    self.page.close()
                if self.context:
                    self.context.close()
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
            else:
                if self.driver:
                    self.driver.quit()
                    
            self.logger.info("Browser stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping browser: {str(e)}")
            
    def check_availability(self, duration_minutes: int = 4) -> AvailabilityStatus:
        """Monitor website for availability with enhanced safety and rate limiting."""
        self.logger.info(f"Starting enhanced availability monitoring for {duration_minutes} minutes")
        self.logger.info(f"Session ID: {self.session_id}")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        check_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while datetime.now() < end_time:
            try:
                check_count += 1
                self.request_count += 1
                
                # Enhanced rate limiting based on request count
                if self.request_count > 10:
                    # Increase delays after many requests
                    base_delay = random.uniform(60, 120)  # 1-2 minutes
                    self.logger.info(f"High request count ({self.request_count}), using extended delay: {base_delay:.1f}s")
                else:
                    base_delay = random.uniform(30, 60)  # 30-60 seconds
                
                # Check for Cloudflare challenges
                if self.cf_challenge_detected:
                    base_delay *= 2  # Double delay after CF challenge
                    self.logger.warning("Extended delay due to previous Cloudflare challenge")
                
                self.logger.info(f"Check #{check_count} - Request #{self.request_count}")
                
                if self.use_playwright:
                    status = self._check_availability_playwright()
                else:
                    status = self._check_availability_selenium()
                
                # Reset error counter on successful check
                consecutive_errors = 0
                
                if status.available:
                    self.logger.info(f"🎉 AVAILABILITY FOUND! Slots: {status.slots_count}")
                    self.logger.info(f"Total checks performed: {check_count}")
                    return status
                else:
                    if status.error_message:
                        self.logger.warning(f"Check #{check_count} failed: {status.error_message}")
                    else:
                        self.logger.info(f"Check #{check_count}: No slots available")
                
                # Adaptive delay based on response
                if status.error_message and "cloudflare" in status.error_message.lower():
                    delay = base_delay * 3  # Triple delay for CF issues
                    self.cf_challenge_detected = True
                    # Rotate user agent for next attempt
                    self._rotate_user_agent()
                elif status.error_message and "no slots" in status.error_message.lower():
                    delay = base_delay * 1.5  # Slightly longer delay for no slots
                else:
                    delay = base_delay
                
                self.logger.info(f"Waiting {delay:.1f} seconds before next check...")
                time.sleep(delay)
                
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Error during monitoring (attempt {consecutive_errors}): {str(e)}")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(f"Too many consecutive errors ({consecutive_errors}), attempting recovery...")
                    
                    # Try to recover by restarting browser
                    try:
                        self.stop_browser()
                        time.sleep(5)
                        if self.use_playwright:
                            self._start_playwright()
                        else:
                            self._start_selenium()
                        consecutive_errors = 0
                        self.logger.info("Browser recovery successful, continuing monitoring...")
                    except Exception as recovery_error:
                        self.logger.error(f"Recovery failed: {recovery_error}")
                        return AvailabilityStatus(
                            available=False,
                            last_checked=datetime.now().isoformat(),
                            error_message=f"Monitoring stopped due to {consecutive_errors} consecutive errors and recovery failure"
                        )
                
                # Exponential backoff on errors
                error_delay = min(300, 60 * (2 ** consecutive_errors))  # Max 5 minutes
                self.logger.warning(f"Error backoff: waiting {error_delay} seconds")
                time.sleep(error_delay)
        
        self.logger.info(f"Monitoring completed. Total checks: {check_count}")
        return AvailabilityStatus(
            available=False,
            last_checked=datetime.now().isoformat(),
            error_message=f"No availability found within {duration_minutes} minutes ({check_count} checks performed)"
        )
        
    def _check_availability_playwright(self) -> AvailabilityStatus:
        """Check availability using Playwright with Cloudflare detection."""
        try:
            # Navigate with stealth measures
            self.page.goto(self.booking_url, wait_until='networkidle', timeout=30000)
            self._random_delay()
            
            # Check for Cloudflare challenge
            page_content = self.page.content()
            if self._detect_cloudflare_challenge(page_content):
                self.logger.warning("Cloudflare challenge detected during availability check")
                if not self._handle_cloudflare_challenge():
                    return AvailabilityStatus(
                        available=False,
                        last_checked=datetime.now().isoformat(),
                        error_message="Cloudflare challenge not resolved"
                    )
                # Re-get content after challenge resolution
                page_content = self.page.content()
            
            # Enhanced slot detection selectors for VFS Global
            slot_selectors = [
                # VFS Global specific selectors
                '[data-testid="appointment-slot"]',
                '[data-testid="time-slot"]',
                '[data-testid="available-slot"]',
                '.appointment-slot',
                '.available-slot',
                '.time-slot',
                '.booking-slot',
                '.slot-available',
                '.calendar-day.available',
                '.calendar-day.bookable',
                '.calendar-day.selectable',
                
                # Radio button selectors
                'input[type="radio"][name*="slot"]',
                'input[type="radio"][name*="appointment"]',
                'input[type="radio"][name*="time"]',
                'input[type="radio"][name*="date"]',
                
                # Generic appointment selectors
                '[class*="slot"][class*="available"]',
                '[class*="appointment"][class*="available"]',
                '[class*="time"][class*="available"]',
                '[class*="booking"][class*="available"]',
                '[class*="date"][class*="available"]',
                
                # VFS Global booking system selectors
                '.vfs-slot-available',
                '.vfs-appointment-slot',
                '.vfs-time-slot',
                '.vfs-booking-slot',
                '.vfs-calendar-slot',
                
                # Button selectors
                'button[class*="slot"]',
                'button[class*="appointment"]',
                'button[class*="time"]',
                'button[class*="booking"]',
                'button[class*="available"]',
                
                # Link selectors
                'a[href*="appointment"]',
                'a[href*="booking"]',
                'a[href*="slot"]',
                'a[href*="time"]',
                
                # Table/row selectors
                'tr[class*="available"]',
                'td[class*="available"]',
                'div[class*="row"][class*="available"]',
                
                # Form selectors
                'select option[value*="available"]',
                'select option:not([disabled])',
                
                # Generic available elements
                '[class*="available"]:not([class*="unavailable"])',
                '[class*="bookable"]',
                '[class*="selectable"]',
                '[class*="enabled"]'
            ]
            
            slots_found = 0
            for selector in slot_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements:
                        slots_found = len(elements)
                        self.logger.info(f"Found {slots_found} slots using selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
            # Check for "No appointments available" message
            no_slots_selectors = [
                'text="No appointments available"',
                'text="No slots available"',
                'text="No available appointments"',
                'text="All appointments are fully booked"',
                '.no-appointments',
                '.no-slots',
                '.fully-booked',
                '[class*="no"][class*="appointment"]',
                '[class*="no"][class*="slot"]'
            ]
            
            no_slots = False
            for selector in no_slots_selectors:
                try:
                    if self.page.query_selector(selector):
                        no_slots = True
                        self.logger.info(f"No slots message found with selector: {selector}")
                        break
                except:
                    continue
            
            # Additional content-based detection
            if not no_slots and slots_found == 0:
                # Check page content for availability indicators
                content_lower = page_content.lower()
                if any(phrase in content_lower for phrase in [
                    'no appointments', 'no slots', 'fully booked', 'not available'
                ]):
                    no_slots = True
                elif any(phrase in content_lower for phrase in [
                    'book appointment', 'select time', 'available dates', 'choose slot'
                ]):
                    # Page suggests availability but no specific slots found
                    slots_found = 1  # Assume at least one slot is available
            
            return AvailabilityStatus(
                available=slots_found > 0 and not no_slots,
                slots_count=slots_found,
                last_checked=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Error checking availability: {str(e)}")
            return AvailabilityStatus(
                available=False,
                last_checked=datetime.now().isoformat(),
                error_message=str(e)
            )
            
    def _check_availability_selenium(self) -> AvailabilityStatus:
        """Check availability using Selenium."""
        try:
            self.driver.get(self.booking_url)
            self._random_delay()
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for appointment slots
            slot_selectors = [
                '[data-testid="appointment-slot"]',
                '.appointment-slot',
                '.available-slot',
                'input[type="radio"][name*="slot"]',
                '.calendar-day.available'
            ]
            
            slots_found = 0
            for selector in slot_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        slots_found = len(elements)
                        break
                except:
                    continue
                    
            return AvailabilityStatus(
                available=slots_found > 0,
                slots_count=slots_found,
                last_checked=datetime.now().isoformat()
            )
            
        except Exception as e:
            return AvailabilityStatus(
                available=False,
                last_checked=datetime.now().isoformat(),
                error_message=str(e)
            )
            
    def book_appointment(self, client: ClientRecord) -> BookingResult:
        """Book appointment for a single client."""
        self.logger.info(f"Starting booking process for {client.email}")
        
        try:
            # Navigate to booking page
            if self.use_playwright:
                self.page.goto(self.booking_url, wait_until='networkidle')
            else:
                self.driver.get(self.booking_url)
                
            self._random_delay()
            
            # Fill booking form
            if self.use_playwright:
                success = self._fill_form_playwright(client)
            else:
                success = self._fill_form_selenium(client)
                
            if not success:
                return BookingResult(
                    success=False,
                    error_message="Failed to fill booking form",
                    client_email=client.email,
                    timestamp=datetime.now().isoformat()
                )
                
            # Submit booking
            if self.use_playwright:
                booking_ref = self._submit_booking_playwright()
            else:
                booking_ref = self._submit_booking_selenium()
                
            if booking_ref:
                self.logger.info(f"Booking successful for {client.email}: {booking_ref}")
                return BookingResult(
                    success=True,
                    booking_reference=booking_ref,
                    client_email=client.email,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return BookingResult(
                    success=False,
                    error_message="Failed to submit booking",
                    client_email=client.email,
                    timestamp=datetime.now().isoformat()
                )
                
        except Exception as e:
            self.logger.error(f"Booking failed for {client.email}: {str(e)}")
            return BookingResult(
                success=False,
                error_message=str(e),
                client_email=client.email,
                timestamp=datetime.now().isoformat()
            )
            
    def _fill_form_playwright(self, client: ClientRecord) -> bool:
        """Fill booking form using Playwright with enhanced selectors and human-like behavior."""
        try:
            # Wait for page to load completely
            self.page.wait_for_load_state('networkidle')
            self._random_delay()
            
            # Enhanced form field selectors
            form_selectors = {
                'first_name': [
                    'input[name="firstName"]',
                    'input[name="first_name"]',
                    'input[name="givenName"]',
                    'input[id*="first"]',
                    'input[placeholder*="first"]',
                    '#firstName',
                    '#first_name'
                ],
                'last_name': [
                    'input[name="lastName"]',
                    'input[name="last_name"]',
                    'input[name="surname"]',
                    'input[id*="last"]',
                    'input[placeholder*="last"]',
                    '#lastName',
                    '#last_name'
                ],
                'email': [
                    'input[name="email"]',
                    'input[name="emailAddress"]',
                    'input[type="email"]',
                    'input[id*="email"]',
                    'input[placeholder*="email"]',
                    '#email',
                    '#emailAddress'
                ],
                'phone': [
                    'input[name="phone"]',
                    'input[name="phoneNumber"]',
                    'input[name="mobile"]',
                    'input[id*="phone"]',
                    'input[placeholder*="phone"]',
                    '#phone',
                    '#phoneNumber'
                ],
                'passport': [
                    'input[name="passportNumber"]',
                    'input[name="passport"]',
                    'input[id*="passport"]',
                    'input[placeholder*="passport"]',
                    '#passportNumber',
                    '#passport'
                ]
            }
            
            # Fill personal details with human-like typing
            self._fill_field_human_like(form_selectors['first_name'], client.first_name)
            self._random_delay()
            
            self._fill_field_human_like(form_selectors['last_name'], client.last_name)
            self._random_delay()
            
            self._fill_field_human_like(form_selectors['email'], client.email)
            self._random_delay()
            
            phone_number = f"{client.mobile_country_code}{client.mobile_number}"
            self._fill_field_human_like(form_selectors['phone'], phone_number)
            self._random_delay()
            
            # Fill passport details
            if client.passport_number:
                self._fill_field_human_like(form_selectors['passport'], client.passport_number)
                self._random_delay()
            
            # Select nationality with multiple selector attempts
            if client.current_nationality:
                nationality_selectors = [
                    'select[name="nationality"]',
                    'select[name="country"]',
                    'select[id*="nationality"]',
                    'select[id*="country"]',
                    '#nationality',
                    '#country'
                ]
                self._select_option_human_like(nationality_selectors, client.current_nationality)
                self._random_delay()
            
            # Select visa type
            if client.service_center:
                visa_selectors = [
                    'select[name="visaType"]',
                    'select[name="serviceType"]',
                    'select[id*="visa"]',
                    'select[id*="service"]',
                    '#visaType',
                    '#serviceType'
                ]
                self._select_option_human_like(visa_selectors, client.service_center)
                self._random_delay()
            
            # Fill additional fields if available
            if hasattr(client, 'date_of_birth') and client.date_of_birth:
                dob_selectors = [
                    'input[name="dateOfBirth"]',
                    'input[name="dob"]',
                    'input[type="date"]',
                    'input[id*="birth"]',
                    '#dateOfBirth',
                    '#dob'
                ]
                self._fill_field_human_like(dob_selectors, client.date_of_birth)
                self._random_delay()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill form with Playwright: {str(e)}")
            return False
    
    def _fill_field_human_like(self, selectors: List[str], value: str) -> bool:
        """Fill a form field with human-like typing behavior."""
        for selector in selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    # Clear field first
                    element.click()
                    element.fill('')
                    
                    # Type with human-like delays
                    for char in value:
                        element.type(char)
                        time.sleep(random.uniform(0.05, 0.15))  # Random typing delay
                    
                    self.logger.debug(f"Successfully filled field {selector} with value: {value}")
                    return True
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {str(e)}")
                continue
        return False
    
    def _select_option_human_like(self, selectors: List[str], option_value: str) -> bool:
        """Select an option with human-like behavior."""
        for selector in selectors:
            try:
                element = self.page.query_selector(selector)
                if element:
                    # Try different selection methods
                    try:
                        # Method 1: Select by visible text
                        element.select_option(label=option_value)
                    except:
                        try:
                            # Method 2: Select by value
                            element.select_option(value=option_value)
                        except:
                            # Method 3: Select by index (if it's a dropdown)
                            options = element.query_selector_all('option')
                            for i, option in enumerate(options):
                                if option_value.lower() in option.text_content().lower():
                                    element.select_option(index=i)
                                    break
                    
                    self.logger.debug(f"Successfully selected option {option_value} in {selector}")
                    return True
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {str(e)}")
                continue
        return False
            
    def _fill_form_selenium(self, client: ClientRecord) -> bool:
        """Fill booking form using Selenium."""
        try:
            # Fill personal details
            self.driver.find_element(By.NAME, "firstName").send_keys(client.first_name)
            self.driver.find_element(By.NAME, "lastName").send_keys(client.last_name)
            self.driver.find_element(By.NAME, "email").send_keys(client.email)
            self.driver.find_element(By.NAME, "phone").send_keys(f"{client.mobile_country_code}{client.mobile_number}")
            
            # Select nationality
            if client.current_nationality:
                nationality_select = Select(self.driver.find_element(By.NAME, "nationality"))
                nationality_select.select_by_visible_text(client.current_nationality)
                
            # Fill passport details
            if client.passport_number:
                self.driver.find_element(By.NAME, "passportNumber").send_keys(client.passport_number)
                
            # Select visa type
            if client.service_center:
                visa_select = Select(self.driver.find_element(By.NAME, "visaType"))
                visa_select.select_by_visible_text(client.service_center)
                
            self._random_delay()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill form with Selenium: {str(e)}")
            return False
            
    def _submit_booking_playwright(self) -> Optional[str]:
        """Submit booking using Playwright."""
        try:
            # Click submit button
            self.page.click('button[type="submit"]')
            self._random_delay()
            
            # Wait for confirmation page
            self.page.wait_for_selector('.booking-confirmation, .confirmation-number', timeout=10000)
            
            # Extract booking reference
            booking_ref = self.page.query_selector('.booking-reference, .confirmation-number')
            if booking_ref:
                return booking_ref.text_content().strip()
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to submit booking with Playwright: {str(e)}")
            return None
            
    def _submit_booking_selenium(self) -> Optional[str]:
        """Submit booking using Selenium."""
        try:
            # Click submit button
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            submit_btn.click()
            self._random_delay()
            
            # Wait for confirmation page
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.booking-confirmation, .confirmation-number'))
            )
            
            # Extract booking reference
            try:
                booking_ref_element = self.driver.find_element(By.CSS_SELECTOR, '.booking-reference, .confirmation-number')
                return booking_ref_element.text.strip()
            except NoSuchElementException:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to submit booking with Selenium: {str(e)}")
            return None
            
    def book_multiple_clients(self, clients: List[ClientRecord], max_clients: int = 5) -> List[BookingResult]:
        """Book appointments for multiple clients."""
        self.logger.info(f"Starting batch booking for {min(len(clients), max_clients)} clients")
        
        results = []
        successful_bookings = 0
        
        for i, client in enumerate(clients[:max_clients]):
            if successful_bookings >= max_clients:
                break
                
            self.logger.info(f"Processing client {i+1}/{min(len(clients), max_clients)}: {client.email}")
            
            # Check availability before each booking
            availability = self.check_availability(duration_minutes=1)
            if not availability.available:
                self.logger.warning(f"No availability found for {client.email}")
                results.append(BookingResult(
                    success=False,
                    error_message="No availability",
                    client_email=client.email,
                    timestamp=datetime.now().isoformat()
                ))
                continue
                
            # Attempt booking
            result = self.book_appointment(client)
            results.append(result)
            
            if result.success:
                successful_bookings += 1
                self.logger.info(f"Successfully booked {client.email}")
            else:
                self.logger.error(f"Failed to book {client.email}: {result.error_message}")
                
            # Add delay between bookings
            if i < len(clients) - 1:
                self._random_delay()
                
        self.logger.info(f"Batch booking completed. Success: {successful_bookings}/{len(clients[:max_clients])}")
        return results
        
    def save_booking_results(self, results: List[BookingResult], filename: str = None) -> None:
        """Save booking results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"booking_results_{timestamp}.json"
            
        try:
            results_data = []
            for result in results:
                results_data.append({
                    'success': result.success,
                    'booking_reference': result.booking_reference,
                    'error_message': result.error_message,
                    'client_email': result.client_email,
                    'timestamp': result.timestamp
                })
                
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2)
                
            self.logger.info(f"Booking results saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save booking results: {str(e)}")


if QtCore is not None:
    class VFSBotWorker(QtCore.QThread):
        """QThread worker for VFS automation."""
        
        # Signals
        status_updated = QtCore.pyqtSignal(str)
        availability_found = QtCore.pyqtSignal(object)  # AvailabilityStatus
        booking_completed = QtCore.pyqtSignal(object)   # BookingResult
        error_occurred = QtCore.pyqtSignal(str)
        progress_updated = QtCore.pyqtSignal(int, int)  # current, total
        
        def __init__(self, headless: bool = True, use_playwright: bool = True, start_url: Optional[str] = None):
            super().__init__()
            self.headless = headless
            self.use_playwright = use_playwright
            self.vfs_automation = None
            self.monitoring_duration = 4  # minutes
            self.max_clients = 5
            self._stop_requested = False
            self.start_url = start_url
        
        def run(self) -> None:
            """Main worker thread execution."""
            try:
                self.status_updated.emit("Starting VFS automation...")
                
                # Initialize automation
                self.vfs_automation = VFSAutomation(
                    headless=self.headless,
                    use_playwright=self.use_playwright
                )
                ready, reason = self.vfs_automation.environment_ready()
                if not ready:
                    self.error_occurred.emit(reason)
                    return
                
                # Override start URLs if provided
                if self.start_url:
                    self.vfs_automation.login_url = self.start_url
                    # Derive booking URL from login path when possible
                    try:
                        if "/login" in self.start_url:
                            self.vfs_automation.booking_url = self.start_url.replace("/login", "/book-appointment")
                    except Exception:
                        pass
                
                if not self.vfs_automation.start_browser():
                    self.error_occurred.emit("Failed to start browser")
                    return
                    
                self.status_updated.emit("Browser started. Monitoring for availability...")
                
                # Monitor for availability
                availability = self.vfs_automation.check_availability(self.monitoring_duration)
                
                if availability.available:
                    self.availability_found.emit(availability)
                    self.status_updated.emit(f"Availability found! {availability.slots_count} slots available.")
                    
                    # Load clients and attempt booking
                    clients = load_clients()
                    if clients:
                        self.status_updated.emit(f"Starting booking for {len(clients)} clients...")
                        results = self.vfs_automation.book_multiple_clients(clients, self.max_clients)
                        
                        # Emit results
                        for i, result in enumerate(results):
                            self.booking_completed.emit(result)
                            self.progress_updated.emit(i + 1, len(results))
                            
                        # Save results
                        self.vfs_automation.save_booking_results(results)
                        self.status_updated.emit("Booking process completed!")
                    else:
                        self.error_occurred.emit("No client data found. Please add clients first.")
                else:
                    self.status_updated.emit("No availability found during monitoring period.")
                    
            except Exception as e:
                self.error_occurred.emit(f"Automation error: {str(e)}")
            finally:
                if self.vfs_automation:
                    self.vfs_automation.stop_browser()
                self.status_updated.emit("Automation stopped.")
                
        def stop(self) -> None:
            """Stop the worker thread."""
            self._stop_requested = True
            if self.vfs_automation:
                self.vfs_automation.stop_browser()
            self.quit()
            self.wait()
else:
    # Fallback class when PyQt6 is not available
    class VFSBotWorker:
        """Fallback worker for VFS automation when PyQt6 is not available."""
        
        def __init__(self, headless: bool = True, use_playwright: bool = True, start_url: Optional[str] = None):
            self.headless = headless
            self.use_playwright = use_playwright
            self.vfs_automation = None
            self.monitoring_duration = 4  # minutes
            self.max_clients = 5
            self._stop_requested = False
            self.start_url = start_url
            # Dummy signal methods
            self.status_updated = lambda x: None
            self.availability_found = lambda x: None
            self.booking_completed = lambda x: None
            self.error_occurred = lambda x: None
            self.progress_updated = lambda x, y: None
        
        def run(self) -> None:
            """Main worker execution (fallback)."""
            try:
                self.status_updated("Starting VFS automation...")
                
                # Initialize automation
                self.vfs_automation = VFSAutomation(
                    headless=self.headless,
                    use_playwright=self.use_playwright
                )
                ready, reason = self.vfs_automation.environment_ready()
                if not ready:
                    self.error_occurred(reason)
                    return
                if self.start_url:
                    self.vfs_automation.login_url = self.start_url
                    try:
                        if "/login" in self.start_url:
                            self.vfs_automation.booking_url = self.start_url.replace("/login", "/book-appointment")
                    except Exception:
                        pass
                
                if not self.vfs_automation.start_browser():
                    self.error_occurred("Failed to start browser")
                    return
                    
                self.status_updated("Browser started. Monitoring for availability...")
                
                # Monitor for availability
                availability = self.vfs_automation.check_availability(self.monitoring_duration)
                
                if availability.available:
                    self.availability_found(availability)
                    self.status_updated(f"Availability found! {availability.slots_count} slots available.")
                    
                    # Load clients and attempt booking
                    clients = load_clients()
                    if clients:
                        self.status_updated(f"Starting booking for {len(clients)} clients...")
                        results = self.vfs_automation.book_multiple_clients(clients, self.max_clients)
                        
                        # Emit results
                        for i, result in enumerate(results):
                            self.booking_completed(result)
                            self.progress_updated(i + 1, len(results))
                            
                        # Save results
                        self.vfs_automation.save_booking_results(results)
                        self.status_updated("Booking process completed!")
                    else:
                        self.error_occurred("No client data found. Please add clients first.")
                else:
                    self.status_updated("No availability found during monitoring period.")
                    
            except Exception as e:
                self.error_occurred(f"Automation error: {str(e)}")
            finally:
                if self.vfs_automation:
                    self.vfs_automation.stop_browser()
                self.status_updated("Automation stopped.")
                
        def stop(self) -> None:
            """Stop the worker."""
            self._stop_requested = True
            if self.vfs_automation:
                self.vfs_automation.stop_browser()
