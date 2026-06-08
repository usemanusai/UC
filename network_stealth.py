import httpx
import logging
import random
import json
import asyncio
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class NetworkStealth:
    """
    Manages proxy-VLAN binding and residential IP validation.
    """
    def __init__(self, proxy_list: list):
        self.proxy_list = proxy_list
        self.current_proxy = None

    async def validate_ip_quality(self, proxy: str) -> Dict:
        """Checks if the proxy IP is residential and gets its ASN/Org info."""
        proxies = proxy
        if not proxy.startswith(('http://', 'https://')):
            proxies = 'http://' + proxy
        
        # We need to construct the proxies parameter for httpx.AsyncClient properly
        # httpx expects either a single string proxy or a dict like {'all://': proxy}
        try:
            async with httpx.AsyncClient(proxies=proxies, timeout=10.0) as client:
                response = await client.get('https://ipapi.co/json/')
                if response.status_code == 200:
                    data = response.json()
                    asn = data.get('asn', '')
                    org = data.get('org', '')
                    is_residential = self._check_residential_asn(asn, org)
                    logger.info(f"[Network] IP: {data.get('ip')} | ISP: {org} | Residential: {is_residential}")
                    return {"valid": True, "residential": is_residential, "data": data}
        except Exception as e:
            logger.error(f"[Network] Proxy validation failed: {e}")
            
        return {"valid": False, "residential": False}

    def _check_residential_asn(self, asn: str, org: str) -> bool:
        """Heuristic to detect residential ISPs based on organization names."""
        datacenter_keywords = ('AWS', 'Google', 'Microsoft', 'DigitalOcean', 'Hetzner', 'OVH', 'Linode', 'Azure')
        org_upper = org.upper()
        for kw in datacenter_keywords:
            if kw.upper() in org_upper:
                return False
        return True

    async def get_next_proxy(self) -> Optional[str]:
        """
        Selects a unique proxy from the list and strictly validates Residential ISP.
        If a Datacenter proxy is detected, it automatically rotates to find a clean Residential IP.
        """
        if not self.proxy_list:
            return None
            
        max_attempts = len(self.proxy_list)
        for _ in range(max_attempts):
            candidate = random.choice(self.proxy_list)
            res = await self.validate_ip_quality(candidate)
            if res.get('valid') and res.get('residential'):
                self.current_proxy = candidate
                return self.current_proxy
            else:
                logger.warning(f"[Network] Rejected proxy {candidate}: Non-Residential/Datacenter detected. Rotating...")
                
        logger.error("[Network] No pure residential proxies available. Falling back to default proxy list.")
        self.current_proxy = random.choice(self.proxy_list)
        return self.current_proxy

    @staticmethod
    def inject_cookies_cdp(driver, cookies_json: str):
        """Injects historical cookies via CDP to warm up the session."""
        try:
            cookies = json.loads(cookies_json)
            for cookie in cookies:
                driver.execute_cdp_cmd('Network.setCookie', cookie)
            logger.info(f"[Network] Injected {len(cookies)} historical cookies.")
        except Exception as e:
            logger.error(f"[Network] Cookie injection failed: {e}")


def apply_network_stealth(driver, proxy_list: list) -> Optional[str]:
    """
    Module-level function to validate and return a residential proxy from proxy_list.
    """
    ns = NetworkStealth(proxy_list)
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import threading
            from concurrent.futures import Future

            def run_coro():
                f = Future()
                def run():
                    try:
                        res = asyncio.run(ns.get_next_proxy())
                        f.set_result(res)
                    except Exception as ex:
                        f.set_exception(ex)
                threading.Thread(target=run).start()
                return f.result()
            
            return run_coro()
        else:
            return asyncio.run(ns.get_next_proxy())
    except Exception as e:
        logger.error(f"[Network] apply_network_stealth failed: {e}")
        return None


if __name__ == '__main__':
    ns = NetworkStealth(['127.0.0.1:8080'])
    print(ns._check_residential_asn('AS13335', 'Cloudflare, Inc.'))
