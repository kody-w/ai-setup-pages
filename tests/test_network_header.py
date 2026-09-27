import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import gen


class NetworkHeaderTests(unittest.TestCase):
    def test_rendered_readme_uses_public_network_header_bytes(self):
        product = json.loads((ROOT / "products" / "rapp-brainstem.json").read_text())
        hosts = gen.load_hosts()
        host = next(h for h in hosts if h["slug"] == "claude")
        readme = gen.render_readme(product, host, hosts)
        expected = gen.network_header("rapp-brainstem-claude")
        self.assertIn(expected, readme)
        start = readme.index("<!-- rapp1:network-header:start -->")
        end_marker = "<!-- rapp1:network-header:end -->"
        end = readme.index(end_marker, start) + len(end_marker)
        self.assertEqual(expected, readme[start:end])

    def test_network_header_is_public_and_dependency_free(self):
        header = gen.network_header("rappterbook-join")
        self.assertIn("https://kody-w.github.io/rapp-hive-public/portfolio/badges/rappterbook-join.svg", header)
        self.assertIn("https://github.com/kody-w/rapp-hive-public/blob/main/portfolio/repos/rappterbook-join.md", header)
        self.assertNotIn("rapp1_network", pathlib.Path(gen.__file__).read_text())


if __name__ == "__main__":
    unittest.main()
