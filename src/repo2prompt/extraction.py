import os
import requests
import base64
from urllib.parse import urlparse
from typing import Optional
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

def parse_github_url(url):
    """
    Parses your GitHub URL and extracts the repository owner and name.
    """
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip("/").split("/")
    if len(path_segments) >= 2:
        owner, repo = path_segments[0], path_segments[1]
        return owner, repo
    else:
        raise ValueError("Invalid GitHub URL provided!")

def fetch_repo_content(owner, repo, path='', token=None):
    """
    Fetches the content of your GitHub repository.
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(base_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_file_content(file_info):
    """
    Retrieves and decodes the content of files
    """
    if file_info['encoding'] == 'base64':
        return base64.b64decode(file_info['content']).decode('utf-8')
    else:
        return file_info['content']

def build_directory_tree(
    owner : str, 
    repo : str, 
    path : str ='', 
    token : Optional[str] = None, 
    indent : int = 0, 
    file_paths : List[tuple[int, str]] =[],
    is_base : bool = False
) -> tuple[str, List[tuple[int, str]]]:
    
    def process_item(
        item : Dict[str, Any], 
        tree_str : str, 
        file_paths : List[tuple[int, str]], 
        indent : int
    )-> tuple[str, List[tuple[int, str]]]:
        if '.github' in item['path'].split('/'):
            pass
        if item['type'] == 'dir':
            tree_str += '    ' * indent + f"[{item['name']}/]\n"
            tree_str += build_directory_tree(
                owner, repo, item['path'], token, indent + 1, file_paths, is_base=False
            )[0]
        else:
            tree_str += '    ' * indent + f"{item['name']}\n"
            # Indicate which file extensions should be included in the prompt!
            if item['name'].endswith(('.py', '.ipynb', '.html', '.css', '.js', '.jsx', '.rst', '.md', '.rs',)):
                file_paths.append((indent, item['path']))
        return tree_str, file_paths
   
    items = fetch_repo_content(owner, repo, path, token)
    if items is None:
        return "", file_paths
    
    tree_str = ""
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_item, item, "", file_paths, indent) for item in items]
        file_paths = []
        tree_str = ""
        
        if is_base:
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="Building tree"
            ):
                res = future.result()
                tree_str += res[0]
                file_paths.extend(res[1])
        else:
            for future in as_completed(futures):
                res = future.result()
                tree_str += res[0]
                file_paths.extend(res[1])
        
    return tree_str, file_paths


def extract_repo(
    github_url : str,
    github_token : Optional[str] = None, 
)-> tuple[str, str]:
    '''
    Args:
        github_url : str : A URL to a Github repository, must use tree/main or tree/branch_name
        github_token : Optional[str] : A Github personal access token, if not provided will use the GITHUB_TOKEN env variable
    Returns:
        str : A string representation of the repository information, suitable for use in a prompt
    '''
    if github_token is None:
        github_token = os.getenv("GITHUB_TOKEN")

    if github_url.split('/')[-2] != 'tree':
        raise ValueError(
            "Please provide a URL that ends with 'tree', 'tree/main', or 'tree/branch_name'. "
            f"Got URL: {github_url}"
        )
   
    owner, repo = parse_github_url(github_url)

    try:
        readme_info = fetch_repo_content(owner, repo, 'README.md', github_token)
        readme_content = get_file_content(readme_info)
        formatted_string = f"README.md:\n```\n{readme_content}\n```\n\n"
    except Exception as e:
        formatted_string = "README.md: Not found or error fetching README\n\n"

    directory_tree, file_paths = build_directory_tree(owner, repo, token=github_token, is_base = True)

    def fetch_and_format_file_content(args):
        owner, repo, path, token, indent = args
        file_info = fetch_repo_content(owner, repo, path, token)
        file_content = get_file_content(file_info)
        return '\n' + '    ' * indent + f"{path}:\n" + '    ' * indent + '```\n' + file_content + '\n' + '    ' * indent + '```\n'

    formatted_contents = []
    with ThreadPoolExecutor() as executor:
        tasks = [
            executor.submit(
                fetch_and_format_file_content, (owner, repo, path, github_token, indent)
            ) for indent, path in file_paths
        ]
        for future in tqdm(as_completed(tasks), total=len(tasks), desc="Fetching files"):
            formatted_contents.append(future.result())

    formatted_string = ''.join(formatted_contents)

    return formatted_string, directory_tree




