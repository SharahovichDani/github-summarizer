import httpx

class GitHubClient:
    def __init__(self, github_url: str):
        self.github_url = github_url
        try:
            path = github_url.split("github.com/")[1]
            parts = path.strip("/").split("/")
            self.owner = parts[0]
            self.repo = parts[1]
        except (IndexError, ValueError):
            raise ValueError(f"Invalid GitHub URL format: {github_url}")
        self.branch = "main"

    async def get_repo_tree(self) -> list[dict]:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/git/trees/{self.branch}"
        params = {"recursive": 1}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)

                # if main branch fails, try master
                if response.status_code == 404:
                    url = f"https://api.github.com/repos/{self.owner}/{self.repo}/git/trees/master"
                    response = await client.get(url, params=params)

                if response.status_code == 404:
                    raise ValueError(f"Repository not found or is private: {self.owner}/{self.repo}")

                if response.status_code != 200:
                    raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")

                data = response.json()
                return data.get("tree", [])

        except httpx.TimeoutException:
            raise TimeoutError(f"GitHub API timed out for {self.owner}/{self.repo}")
        except httpx.RequestError as e:
            raise RuntimeError(f"GitHub connection error: {e}")

    async def get_file_content(self, file_path: str) -> str:
        # Construct the API URL
        url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}/{file_path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            if response.status_code == 404:
                url = f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/master/{file_path}"
                response = await client.get(url)
            if response.status_code != 200:
                return ""
            return response.text
    
    async def get_files_content(self, files: list[dict]) -> dict:
        contents = {}
        for file in files:
            content = await self.get_file_content(file["path"])
            contents[file["path"]] = content
        return contents

    
