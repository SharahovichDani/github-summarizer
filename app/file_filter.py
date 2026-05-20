def filter_files(file_tree: list[dict]) -> list[dict]:
    result = []
    # filter out directories
    files_only = [f for f in file_tree if f["type"] != "tree"]

    source_code_counter = 0
    source_code_limit = 20 if len(files_only) > 100 else 15

    for file in files_only:
        path = file["path"]
        filename = path.split("/")[-1]

        # ── Rule 0: Skip junk folders FIRST ──
        skip_folders = [
            ".github/", ".gitlab/", ".circleci/",
            "docs/", "doc/", "documentation/",
            "tests/", "test/", "__tests__/", "spec/",
            "ext/", "examples/", "example/", "samples/",
            "node_modules/", "vendor/", "third_party/",
            ".vscode/", ".idea/", ".settings/",
            "dist/", "build/", "out/", "target/",
            "__pycache__/", ".next/", ".nuxt/",
            "coverage/", ".nyc_output/",
            "assets/", "static/images/", "public/images/",
        ]
        if any(path.startswith(folder) for folder in skip_folders):
            continue

        # ── Rule 1: Skip dotfiles ──
        if filename.startswith("."):
            continue

        # ── Rule 2: ALWAYS include priority files ──
        priority = [
            "README.md", "README.rst", "README.txt",
            "package.json", "pyproject.toml", "Cargo.toml", "go.mod",
            "pom.xml", "build.gradle", "CMakeLists.txt",
            "requirements.txt", "requirements-dev.txt",
            "setup.py", "setup.cfg",
            "Makefile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            "tsconfig.json", "webpack.config.js", "vite.config.ts",
        ]
        if filename in priority:
            result.append(file)
            continue

        # ── Rule 3: Include source code files (dynamic cap) ──
        source_code_extensions = [
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".go", ".rs", ".java", ".c", ".cpp", ".h",
            ".rb", ".php", ".swift", ".kt",
        ]
        if any(filename.endswith(ext) for ext in source_code_extensions):
            source_code_counter += 1
            if source_code_counter <= source_code_limit:
                result.append(file)
            continue

        # ── Rule 4: Skip binary/useless extensions ──
        skip_extensions = [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".webp", ".svg",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip", ".tar", ".gz", ".rar", ".7z",
            ".exe", ".dll", ".so", ".dylib", ".bin",
            ".dat", ".db", ".sqlite", ".sqlite3",
            ".log", ".lock", ".pid",
            ".woff", ".woff2", ".ttf", ".eot",
            ".mp3", ".mp4", ".wav", ".avi",
            ".min.js", ".min.css", ".map",
        ]
        if any(filename.endswith(ext) for ext in skip_extensions):
            continue

        # ── Rule 5: Skip oversized files (100KB) ──
        if file.get("size", 0) > 100_000:
            continue

        # ── Rule 6: Skip useless filenames ──
        skip_names = [
            "HISTORY.md", "CHANGELOG.md", "AUTHORS.rst", "AUTHORS.md",
            "LICENSE", "LICENSE.md", "LICENSE.txt",
            "NOTICE", "MANIFEST.in", "tox.ini",
        ]
        if filename in skip_names:
            continue

        result.append(file)

    # Cap total files to avoid overwhelming the LLM
    return result[:30]