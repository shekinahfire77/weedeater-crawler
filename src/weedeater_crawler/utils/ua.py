import os
from fake_useragent import FakeUserAgent

_FA = None

def get_user_agent():
    global _FA
    mode = os.getenv("USER_AGENT_MODE", "random").lower()
    fixed = os.getenv("FIXED_USER_AGENT")
    if mode == "fixed" and fixed:
        return fixed
    if _FA is None:
        _FA = FakeUserAgent()
    return _FA.random
