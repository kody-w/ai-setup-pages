import html
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gen


def product(name="rapp-brainstem"):
    return json.loads((ROOT / "products" / f"{name}.json").read_text())


class RetiredHostTests(unittest.TestCase):
    def setUp(self):
        self.hosts = gen.load_hosts()
        self.by_slug = {h["slug"]: h for h in self.hosts}

    def test_every_retired_host_points_to_a_live_host(self):
        for h in self.hosts:
            r = h.get("retired")
            if r:
                self.assertIn(r["use"], self.by_slug, h["slug"])
                self.assertFalse(self.by_slug[r["use"]].get("retired"), h["slug"])

    def test_retired_page_still_renders_and_points_to_the_replacement(self):
        p = product()
        page = gen.render(p, self.by_slug["gemini"], self.hosts)
        new_url = p["page_url"].format(slug="antigravity")
        self.assertIn("retired for personal Google accounts", page)
        self.assertIn(f'href="{new_url}"', page)
        agent = page[page.index('data-agent-readable="true"'):]
        self.assertIn(new_url, agent.split("<h3>")[0])  # agents see it before step 0
        self.assertIn("gemini mcp add", page)  # the old steps stay for accounts that still work

    def test_link_lists_offer_only_live_hosts(self):
        p = product()
        page = gen.render(p, self.by_slug["mcp"], self.hosts)
        self.assertIn(p["page_url"].format(slug="antigravity"), page)
        self.assertNotIn(p["page_url"].format(slug="gemini"), page)

    def test_antigravity_config_block_is_valid_json(self):
        page = gen.render(product(), self.by_slug["antigravity"], self.hosts)
        self.assertEqual([], re.findall(r"\{\{[A-Z_]+\}\}", page))
        block = next(html.unescape(b) for b in re.findall(r"<pre>(.*?)</pre>", page, re.S) if "mcpServers" in b)
        server = json.loads(block)["mcpServers"]["brainstem"]
        self.assertEqual(300, server["timeoutSeconds"])
        self.assertTrue(server["command"].startswith("/Users/you/"))


if __name__ == "__main__":
    unittest.main()
