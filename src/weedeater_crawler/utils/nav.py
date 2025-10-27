from scrapy_playwright.page import PageMethod

# Helpers for smart navigation and infinite scroll

def infinite_scroll(max_rounds=10, scroll_delay=0.5):
    return [
        PageMethod("evaluate", "(max, delay) => new Promise(async res => {\n            let lastHeight = 0;\n            for (let i=0;i<max;i++){\n              await new Promise(r=>setTimeout(r, delay*1000));\n              await window.scrollTo(0, document.body.scrollHeight);\n              const h = document.body.scrollHeight;\n              if (h === lastHeight) break;\n              lastHeight = h;\n            }\n            res();\n          })", max_rounds, scroll_delay)
    ]


def login_sequence(email: str, password: str, email_sel: str, pass_sel: str, submit_sel: str):
    return [
        PageMethod("fill", email_sel, email),
        PageMethod("fill", pass_sel, password),
        PageMethod("click", submit_sel),
        PageMethod("wait_for_load_state", state="networkidle"),
    ]
