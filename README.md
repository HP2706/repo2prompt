# repo2prompt

This is a simple package with minimal dependencies that turns a Github Repo's contents into a big prompt for long-context models.

Example Usage:

```python
from repo2prompt.extraction import extract_repo

extract_repo(github_url="https://github.com/vllm-project/vllm/tree", github_token="your_github_token")
```

