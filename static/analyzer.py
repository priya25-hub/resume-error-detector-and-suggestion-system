"""
DSA-based resume analysis engine.
  * Trie ............ vocabulary storage + fuzzy (edit-distance) lookup for spelling
  * Hash tables ..... misspelling map, weak-phrase map, action-verb set (O(1) lookup)
  * KMP ............. pattern matching for section headings, phrases, keywords
  * Merge sort ...... ordering issues by severity / line number
"""
import re

# ---------------------------------------------------------------- Trie
class TrieNode:
    __slots__ = ("children", "end")
    def __init__(self):
        self.children, self.end = {}, False

class Trie:
    def __init__(self, words=()):
        self.root = TrieNode()
        for w in words:
            self.insert(w)

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.end = True

    def search(self, word):
        node = self.root
        for ch in word:
            node = node.children.get(ch)
            if node is None:
                return False
        return node.end

    def fuzzy(self, word, max_dist=1):
        """All dictionary words within Levenshtein distance <= max_dist (DP row per trie node)."""
        out, first = [], list(range(len(word) + 1))
        def rec(node, prefix, prev):
            if node.end and prev[-1] <= max_dist:
                out.append((prev[-1], prefix))
            if min(prev) > max_dist:
                return
            for ch, child in node.children.items():
                row = [prev[0] + 1]
                for i in range(1, len(word) + 1):
                    row.append(min(row[i-1] + 1, prev[i] + 1, prev[i-1] + (word[i-1] != ch)))
                rec(child, prefix + ch, row)
        rec(self.root, "", first)
        return sorted(out)

# ---------------------------------------------------------------- KMP
def kmp_search(text, pat):
    """Return start indices of every occurrence of pat in text - O(n + m)."""
    if not pat:
        return []
    lps, k = [0] * len(pat), 0
    for i in range(1, len(pat)):
        while k and pat[i] != pat[k]:
            k = lps[k-1]
        k += pat[i] == pat[k]
        lps[i] = k
    res, k = [], 0
    for i, ch in enumerate(text):
        while k and ch != pat[k]:
            k = lps[k-1]
        k += ch == pat[k]
        if k == len(pat):
            res.append(i - k + 1)
            k = lps[k-1]
    return res

def kmp_word(text, pat):
    """KMP match that respects word boundaries."""
    for i in kmp_search(text, pat):
        before = text[i-1] if i else " "
        after = text[i+len(pat)] if i+len(pat) < len(text) else " "
        if not before.isalnum() and not after.isalnum():
            return True
    return False

# ---------------------------------------------------------------- Merge sort
def merge_sort(items, key):
    if len(items) <= 1:
        return items
    mid = len(items) // 2
    l, r = merge_sort(items[:mid], key), merge_sort(items[mid:], key)
    out, i, j = [], 0, 0
    while i < len(l) and j < len(r):
        if key(l[i]) <= key(r[j]):
            out.append(l[i]); i += 1
        else:
            out.append(r[j]); j += 1
    return out + l[i:] + r[j:]

# ---------------------------------------------------------------- Rules
SECTIONS = {
    "education":  (["education", "academic", "qualification"], "high"),
    "skills":     (["skills", "technical skills", "core competencies"], "high"),
    "experience": (["experience", "internship", "employment", "work history"], "high"),
    "projects":   (["projects", "project"], "medium"),
    "summary":    (["summary", "objective", "profile", "about me"], "medium"),
}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
PHONE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
SEV_RANK = {"high": 0, "medium": 1, "low": 2}
PENALTY = {"high": 10, "medium": 5, "low": 2}
CATEGORIES = ["Structure", "Contact", "Spelling", "Grammar & Style", "Content", "Keywords"]
BULLETS = "•-*▪●◦–"

def stem_known(w, vocab):
    if w in vocab:
        return True
    for suf in ("s", "es", "ed", "d", "ing", "ly", "er", "ers", "ion", "ions", "al", "ment", "ments"):
        if w.endswith(suf):
            s = w[:-len(suf)]
            if s in vocab or s + "e" in vocab or (len(s) > 2 and s[-1] == s[-2] and s[:-1] in vocab):
                return True
    return False

def analyze(text, rules):
    lines = text.splitlines()
    vocab = rules["words"]
    trie = Trie(w for w in vocab if len(w) >= 4)
    issues = []
    def add(cat, sev, line, msg, sug=""):
        issues.append({"category": cat, "severity": sev, "line_no": line, "message": msg, "suggestion": sug})

    low_text = text.lower()
    words_all = re.findall(r"[A-Za-z']+", text)
    wc = len(words_all)

    # ---- Structure: section detection (KMP on short heading-like lines)
    found = {}
    for n, line in enumerate(lines, 1):
        s = line.strip().lower().strip(":-• ")
        if 0 < len(s) <= 35:
            for sec, (aliases, _) in SECTIONS.items():
                if sec not in found and any(kmp_word(s, a) for a in aliases):
                    found[sec] = n
    for sec, (aliases, sev) in SECTIONS.items():
        if sec not in found:
            add("Structure", sev, None, f"Missing section: {sec.title()}",
                f"Add a clearly titled '{aliases[0].title()}' section.")
    if wc < 150:
        add("Structure", "medium", None, f"Resume is very short ({wc} words)", "Aim for 250-700 words with measurable details.")
    elif wc > 1000:
        add("Structure", "medium", None, f"Resume is too long ({wc} words)", "Keep it to 1-2 pages; remove old or irrelevant items.")

    # ---- Contact
    emails = EMAIL.findall(text) and [m.group(0) for m in EMAIL.finditer(text)]
    if not emails:
        add("Contact", "high", None, "No valid email address found", "Add a professional email, e.g. firstname.lastname@gmail.com.")
    else:
        for e in emails:
            if re.search(r"\d{4,}", e.split("@")[0]) and len(re.sub(r"\D", "", e.split("@")[0])) > 5:
                add("Contact", "low", None, f"Email '{e}' contains many digits", "Use a cleaner, name-based email address.")
    for n, line in enumerate(lines, 1):
        for tok in line.split():
            if "@" in tok and not EMAIL.search(tok):
                add("Contact", "high", n, f"Malformed email: '{tok}'", "Check the format name@domain.com.")
    if not PHONE.search(text):
        add("Contact", "medium", None, "No phone number found", "Add a phone number with country code.")
    if "linkedin" not in low_text and "github" not in low_text:
        add("Contact", "low", None, "No LinkedIn / GitHub link", "Add profile links to strengthen credibility.")

    # ---- Per-line checks
    spelled = set()
    bullet_styles, weak_hits, verb_miss = set(), 0, []
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        clean = EMAIL.sub(" ", re.sub(r"https?://\S+|www\.\S+|\S+\.(com|in|org)\S*", " ", line))
        low = clean.lower()

        # spelling: hash-table lookup, then Trie + edit distance
        sentence_start = True
        for m in re.finditer(r"[A-Za-z']+", clean):
            w, lw = m.group(), m.group().lower().strip("'")
            starts_upper = w[0].isupper()
            if lw in rules["misspellings"] and (lw, n) not in spelled:
                spelled.add((lw, n))
                add("Spelling", "high", n, f"Possible misspelling: '{w}'", f"Did you mean '{rules['misspellings'][lw]}'?")
            elif (len(lw) >= 5 and lw.isalpha() and not starts_upper and w.islower()
                  and not stem_known(lw, vocab) and (lw, n) not in spelled):
                near = [x for x in trie.fuzzy(lw, 1)]
                if near:
                    spelled.add((lw, n))
                    add("Spelling", "medium", n, f"Unrecognised word: '{w}'", f"Did you mean '{near[0][1]}'?")

        # repeated consecutive words
        toks = re.findall(r"[A-Za-z]+", low)
        for a, b in zip(toks, toks[1:]):
            if a == b and len(a) > 1:
                add("Grammar & Style", "medium", n, f"Repeated word: '{a} {a}'", "Remove the duplicate word.")
        # grammar & formatting
        if re.search(r"(?<![A-Za-z'])i(?![A-Za-z'])", clean):
            add("Grammar & Style", "medium", n, "Pronoun 'I' should be capitalised", "Better: drop first-person pronouns entirely.")
        elif re.search(r"\b(I|my|me)\b", clean) and line[0] in BULLETS:
            add("Grammar & Style", "low", n, "First-person pronoun in a bullet point", "Start with an action verb instead.")
        if "  " in line.replace("\t", " ").strip():
            add("Grammar & Style", "low", n, "Multiple consecutive spaces", "Use single spaces for consistent formatting.")
        if len(line) > 180:
            add("Grammar & Style", "low", n, "Very long line / run-on sentence", "Split into shorter bullet points (under ~25 words).")
        if re.search(r"[!?]{2,}|\.{4,}", line):
            add("Grammar & Style", "low", n, "Excess punctuation", "Use standard punctuation in a professional resume.")
        if line[0] in BULLETS and len(line) > 2:
            bullet_styles.add(line[0])
            first = re.findall(r"[A-Za-z]+", line[1:])[:1]
            if first:
                fw = first[0].lower()
                if first[0][0].islower():
                    add("Grammar & Style", "low", n, "Bullet starts with a lowercase letter", "Capitalise the first word of each bullet.")
                if fw not in rules["verbs"] and not fw.endswith("ed") and len(verb_miss) < 5:
                    verb_miss.append(n)

        # weak phrases (KMP)
        for phrase, repl in rules["weak"].items():
            if kmp_word(low, phrase):
                weak_hits += 1
                add("Content", "medium", n, f"Weak / cliché phrase: '{phrase}'", f"Try: {repl}.")

    if len(bullet_styles) > 1:
        add("Grammar & Style", "medium", None, f"Inconsistent bullet symbols ({' '.join(sorted(bullet_styles))})", "Use a single bullet style throughout.")
    for n in verb_miss:
        add("Content", "low", n, "Bullet does not start with a strong action verb",
            "Start with verbs like Developed, Designed, Implemented, Optimized.")
    if not re.search(r"\d+\s?(%|\+|x|k\b|users|clients|projects|hours)|\b\d{2,}\b", text):
        add("Content", "medium", None, "No measurable achievements (numbers / percentages)",
            "Quantify impact, e.g. 'reduced load time by 30%'.")

    # ---- Keywords (KMP over whole text)
    matched, missing = [], []
    for k in rules["keywords"]:
        (matched if kmp_word(low_text, k.lower()) else missing).append(k)
    if rules["keywords"]:
        cov = len(matched) / len(rules["keywords"])
        if cov < 0.6:
            add("Keywords", "high" if cov < 0.3 else "medium", None,
                f"Only {round(cov*100)}% of target-role keywords found",
                "Consider adding: " + ", ".join(missing[:8]) + ".")
    else:
        cov = None

    # ---- Merge-sort by severity, then line number
    issues = merge_sort(issues, key=lambda i: (SEV_RANK[i["severity"]], i["line_no"] or 0))

    # ---- Scores
    cat_scores = {}
    for c in CATEGORIES:
        pen = sum(PENALTY[i["severity"]] for i in issues if i["category"] == c)
        cat_scores[c] = max(0, 100 - pen)
    if cov is None:
        cat_scores["Keywords"] = None
    vals = [v for v in cat_scores.values() if v is not None]
    score = round(sum(vals) / len(vals))

    return {
        "score": score, "category_scores": cat_scores, "issues": issues,
        "stats": {"word_count": wc, "line_count": len(lines), "sections_found": sorted(found),
                  "keywords_matched": matched, "keywords_missing": missing,
                  "severity": {s: sum(1 for i in issues if i["severity"] == s) for s in SEV_RANK}},
        "lines": lines,
    }