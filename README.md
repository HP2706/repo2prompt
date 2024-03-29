# repo2prompt

This is a simple package with minimal dependencies that turns a Github Repo's contents into a big prompt for long-context models.

this work for repos containing the following file types:
'.py', '.ipynb', '.html', '.css', '.js', '.jsx', '.rst', '.md'

Example Usage:

```python
from repo2prompt.extraction import extract_repo

extract_repo(github_url="https://github.com/vllm-project/vllm/tree/main", github_token="your_github_token")
```

Or 

```python
from repo2prompt.extraction import extract_repo

extract_repo(github_url="https://github.com/vllm-project/vllm/tree/main") # os.getenv("GITHUB_TOKEN") used internally
```

