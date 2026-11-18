import io, os, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.dirname(__file__))
import reddit_thread as rt


class T(unittest.TestCase):
    def test_extract_post_id(self):
        for u in ["https://www.reddit.com/r/x/comments/abc123/title/",
                  "https://old.reddit.com/r/x/comments/abc123/title",
                  "https://redd.it/abc123",
                  "https://www.reddit.com/r/x/comments/abc123/title/?utm=1"]:
            self.assertEqual(rt.extract_post_id(u), "abc123")
        for u in ["https://example.com/r/x/comments/abc123/", "https://www.reddit.com/r/x/", "nonsense"]:
            with self.assertRaises(ValueError):
                rt.extract_post_id(u)

    def test_format_thread(self):
        data = [
            {"data": {"children": [{"data": {"subreddit": "x", "title": "Hi", "author": "op", "score": 5,
                                             "selftext": "body text", "permalink": "/r/x/comments/abc123/hi/"}}]}},
            {"data": {"children": [
                {"kind": "t1", "data": {"author": "a", "score": 3, "body": "top", "replies": {"data": {"children": [
                    {"kind": "t1", "data": {"author": "b", "score": 1, "body": "[deleted]", "replies": ""}},
                    {"kind": "more", "data": {"count": 4}}]}}}},
            ]}},
        ]
        self.assertEqual(rt.format_thread(data), "\n".join([
            "r/x: Hi", "by op (5 points)", "https://www.reddit.com/r/x/comments/abc123/hi/", "",
            "body text", "", "a (3): top", "  b (1): [deleted]", "  [4 more replies]"]))

    def run_main(self, env, envfile={}):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(rt, "load_env", return_value=envfile), \
             redirect_stdout(out), redirect_stderr(err):
            rc = rt.main(["https://redd.it/abc123"])
        return rc, out.getvalue(), err.getvalue()

    def test_missing_credentials(self):
        with mock.patch.object(rt, "http", side_effect=AssertionError("network")):
            rc, out, err = self.run_main({})
        self.assertEqual(rc, 1)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("reddit_thread: "))
        self.assertIn(rt.ENV_PATH, err)
        self.assertEqual(len(err.strip().splitlines()), 1)

    def test_no_secret_in_output(self):
        import urllib.error
        e = urllib.error.HTTPError("https://x/SECRETVAL", 401, "bad SECRETVAL", {}, None)
        with mock.patch.object(rt, "http", side_effect=e):
            rc, out, err = self.run_main({"REDDIT_CLIENT_ID": "IDVAL", "REDDIT_CLIENT_SECRET": "SECRETVAL"})
        self.assertEqual(rc, 1)
        self.assertNotIn("SECRETVAL", out + err)
        self.assertIn("HTTP 401", err)
        # token never printed on a thread-call failure
        calls = [{"access_token": "TOKENVAL"}, e]
        with mock.patch.object(rt, "http", side_effect=calls):
            rc, out, err = self.run_main({"REDDIT_CLIENT_ID": "IDVAL", "REDDIT_CLIENT_SECRET": "SECRETVAL"})
        self.assertNotIn("TOKENVAL", out + err)
        self.assertIn("HTTP 401", err)

    def test_load_env(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write('# c\n\nA=1\nB="two"\nC=\'three\'\nD=\nE = x\n')
        try:
            self.assertEqual(rt.load_env(f.name), {"A": "1", "B": "two", "C": "three", "E": "x"})
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
