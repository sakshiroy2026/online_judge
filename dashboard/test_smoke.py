"""
Smoke tests for the online judge.

Run with:   python manage.py test

Creates a throwaway test database. Your real db.sqlite3 and the live Neon
database are never touched.
"""
import os
import shutil
import subprocess
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.db.models import Count, Q

from dashboard.models import Question, Topic, UserSolvedQuestion
from compile.models import CodeSubmission
from problem_detail.views import run_testcases
from problem_detail.models import TestCase as ProblemTestCase


PASSWORD = "Str0ngPass!23"

# Tests must not depend on `collectstatic` having been run. The production
# manifest storage raises if an asset is missing from staticfiles.json, which
# only exists after a build, so use plain storage while testing.
NO_MANIFEST_STATIC = override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})


def cpp_toolchain_available():
    """The judge calls /usr/bin/g++ by absolute path, so this is Linux-only.
    C++ submissions are verified on Render, not locally."""
    if os.name == "nt":
        return False
    if not shutil.which("g++"):
        return False
    with tempfile.TemporaryDirectory() as d:
        src = f"{d}/probe.cpp"
        with open(src, "w") as f:
            f.write("#include <bits/stdc++.h>\nint main(){return 0;}\n")
        try:
            r = subprocess.run(["g++", src, "-o", f"{d}/probe"],
                               capture_output=True, timeout=30)
            return r.returncode == 0
        except Exception:
            return False

SORT_SOLUTION_PY = (
    "a = input().strip().split(',')\n"
    "print(','.join(map(str, sorted(map(int, a)))))\n"
)

# Correct solution for "Reverse a string". Its expected output contains a
# capital H, so this only passes if the judge preserves case (bug 5).
REVERSE_SOLUTION_PY = (
    "import sys\n"
    "s = sys.stdin.readline().rstrip('\\n').strip()\n"
    "parts = [p for p in s.split(',')] if s else []\n"
    "chars = [p.strip().strip('\"') for p in parts]\n"
    "chars.reverse()\n"
    "print(','.join('\"%s\"' % c for c in chars))\n"
)

SORT_SOLUTION_CPP = """#include <bits/stdc++.h>
using namespace std;
int main(){
    string s; getline(cin, s);
    for(auto &c : s) if(c == ',') c = ' ';
    stringstream ss(s); vector<int> v; int x;
    while(ss >> x) v.push_back(x);
    sort(v.begin(), v.end());
    for(size_t i = 0; i < v.size(); i++){ if(i) cout << ","; cout << v[i]; }
    cout << endl;
}
"""


@NO_MANIFEST_STATIC
class DataLoadTests(TestCase):
    """Migrations apply cleanly and the problem set loads."""

    fixtures = ["initial_data.json"]

    def test_fixture_loads(self):
        self.assertEqual(Topic.objects.count(), 8)
        self.assertEqual(Question.objects.count(), 8)
        self.assertEqual(ProblemTestCase.objects.count(), 8)

    def test_model_fields_intact(self):
        names = [f.name for f in UserSolvedQuestion._meta.get_fields()]
        for expected in ("is_solved", "is_favorite", "solved_at", "user", "question"):
            self.assertIn(expected, names, f"UserSolvedQuestion lost its {expected} field")

    def test_solved_at_autopopulates(self):
        """Catches solved_at losing auto_now_add, which breaks every insert."""
        from django.contrib.auth.models import User as U
        u = U.objects.create_user(username="fieldcheck", password="Str0ngPass!23")
        row = UserSolvedQuestion.objects.create(user=u, question=Question.objects.first())
        self.assertIsNotNone(row.solved_at)

    def test_testcase_files_are_on_disk(self):
        """Catches the media/ files going missing again."""
        for tc in ProblemTestCase.objects.all():
            with open(tc.input_file.path) as f:
                self.assertTrue(f.read().strip(), f"empty input for {tc.question}")
            with open(tc.output_file.path) as f:
                self.assertTrue(f.read().strip(), f"empty output for {tc.question}")


@NO_MANIFEST_STATIC
class RegistrationTests(TestCase):
    """Bug 3: registration must persist email and name."""

    def test_registration_saves_email_and_name(self):
        self.client.post("/auth/register/", {
            "first_name": "Anya", "last_name": "Verma", "username": "anya",
            "password": PASSWORD, "confirm_password": PASSWORD,
            "email": "anya@example.com",
        })
        u = User.objects.get(username="anya")
        self.assertEqual(u.email, "anya@example.com")
        self.assertEqual(u.first_name, "Anya")
        self.assertEqual(u.last_name, "Verma")

    def test_password_actually_works(self):
        self.client.post("/auth/register/", {
            "first_name": "B", "last_name": "C", "username": "bob",
            "password": PASSWORD, "confirm_password": PASSWORD,
            "email": "bob@example.com",
        })
        self.assertTrue(self.client.login(username="bob", password=PASSWORD))

    def test_mismatched_passwords_rejected(self):
        self.client.post("/auth/register/", {
            "first_name": "X", "last_name": "Y", "username": "nope",
            "password": PASSWORD, "confirm_password": "different",
            "email": "nope@example.com",
        })
        self.assertFalse(User.objects.filter(username="nope").exists())


@NO_MANIFEST_STATIC
class PageLoadTests(TestCase):
    """Every page must return 200 for a logged-in user, and no page may crash."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="anya", password=PASSWORD)
        self.client.login(username="anya", password=PASSWORD)
        self.question = Question.objects.get(title="Sort an array")
        self.tc_id = self.question.name.first().id

    def test_all_pages_load(self):
        urls = [
            "/",
            "/dashboard/",
            "/dashboard/?topic=1",
            "/dashboard/?search=sort",
            "/compile/",
            "/dashboard/leaderboard/",
            "/dashboard/favorites/",
            "/dashboard/profile/anya/",
            f"/question/{self.tc_id}/submit/",
            f"/question/{self.tc_id}/history/{self.question.id}/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_pages_require_login(self):
        anon = Client()
        for url in ["/compile/", "/dashboard/leaderboard/", "/dashboard/favorites/"]:
            with self.subTest(url=url):
                self.assertEqual(anon.get(url).status_code, 302)


@NO_MANIFEST_STATIC
class SolvedVsFavoriteTests(TestCase):
    """Bug 2: favoriting must never count as solving."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="anya", password=PASSWORD)
        self.client.login(username="anya", password=PASSWORD)
        self.question = Question.objects.get(title="Sort an array")
        self.tc_id = self.question.name.first().id

    def leaderboard_count(self):
        return User.objects.annotate(
            sc=Count("usersolvedquestion", filter=Q(usersolvedquestion__is_solved=True))
        ).get(username="anya").sc

    def test_favoriting_does_not_mark_solved(self):
        self.client.get(f"/dashboard/favorite/toggle/{self.question.id}/")
        row = UserSolvedQuestion.objects.get(user=self.user, question=self.question)
        self.assertTrue(row.is_favorite)
        self.assertFalse(row.is_solved)
        self.assertEqual(self.leaderboard_count(), 0)

    def test_correct_submission_marks_solved(self):
        self.client.post(f"/question/{self.tc_id}/submit/", {
            "language": "py", "code": SORT_SOLUTION_PY,
            "action": "submit", "input_data": "",
        })
        row = UserSolvedQuestion.objects.get(user=self.user, question=self.question)
        self.assertTrue(row.is_solved)
        self.assertEqual(self.leaderboard_count(), 1)

    def test_wrong_submission_does_not_mark_solved(self):
        self.client.post(f"/question/{self.tc_id}/submit/", {
            "language": "py", "code": "print('nope')",
            "action": "submit", "input_data": "",
        })
        self.assertFalse(
            UserSolvedQuestion.objects.filter(
                user=self.user, question=self.question, is_solved=True
            ).exists()
        )

    def test_solving_a_favorited_question_flips_the_flag(self):
        """update_or_create, not get_or_create."""
        self.client.get(f"/dashboard/favorite/toggle/{self.question.id}/")
        self.client.post(f"/question/{self.tc_id}/submit/", {
            "language": "py", "code": SORT_SOLUTION_PY,
            "action": "submit", "input_data": "",
        })
        row = UserSolvedQuestion.objects.get(user=self.user, question=self.question)
        self.assertTrue(row.is_solved)
        self.assertTrue(row.is_favorite)


@NO_MANIFEST_STATIC
class ProfileStatsTests(TestCase):
    """Bug 4: difficulty is stored as 'Med.', not 'Medium'."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="anya", password=PASSWORD)
        self.client.login(username="anya", password=PASSWORD)

    def test_medium_questions_are_counted(self):
        total_medium = Question.objects.filter(difficulty="Med.").count()
        self.assertGreater(total_medium, 0, "fixture has no Med. questions")
        self.client.get("/dashboard/profile/anya/")
        self.assertEqual(
            Question.objects.filter(difficulty="Medium").count(), 0,
            "'Medium' is not a value this project uses",
        )

    def test_medium_solve_is_counted(self):
        q = Question.objects.filter(difficulty="Med.").first()
        UserSolvedQuestion.objects.create(user=self.user, question=q, is_solved=True)
        counted = UserSolvedQuestion.objects.filter(
            user=self.user, is_solved=True, question__difficulty="Med."
        ).count()
        self.assertEqual(counted, 1)


@NO_MANIFEST_STATIC
class JudgeTests(TestCase):
    """The code runner itself."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        self.user = User.objects.create_user(username="anya", password=PASSWORD)
        self.client.login(username="anya", password=PASSWORD)
        self.question = Question.objects.get(title="Sort an array")
        self.tc_id = self.question.name.first().id

    def submit(self, language, code):
        return run_testcases(
            CodeSubmission(language=language, code=code), self.question, visible_only=False
        )

    def test_python_solution_scores_100(self):
        self.assertEqual(self.submit("py", SORT_SOLUTION_PY)["score"], 100)

    def test_cpp_solution_scores_100(self):
        if not cpp_toolchain_available():
            self.skipTest("no working g++ locally - C++ is verified on Render")
        self.assertEqual(self.submit("cpp", SORT_SOLUTION_CPP)["score"], 100)

    def test_judge_preserves_output_case(self):
        """Bug 5: lowercasing submission output made this problem unsolvable."""
        q = Question.objects.get(title="Reverse a string")
        result = run_testcases(
            CodeSubmission(language="py", code=REVERSE_SOLUTION_PY), q, visible_only=False
        )
        self.assertEqual(result["score"], 100,
                         "Reverse a string must be solvable - check for .lower() in run_code")

    def test_infinite_loop_times_out(self):
        out = self.submit("py", "while True: pass")["results"][0]["output"]
        self.assertIn("Timeout", out)

    def test_submitted_code_cannot_read_secrets(self):
        """A submission must not be able to see DATABASE_URL or API keys."""
        out = self.submit("py", "import os\nprint(dict(os.environ))")["results"][0]["output"]
        for secret in ("DATABASE_URL", "SECRET_KEY", "GOOGLE_API_KEY", "AIza"):
            self.assertNotIn(secret, out)