# girls-frontline-cn-assets-downloader
Assets downloader for 少女前线 (Girls' Frontline), a small project that downloads all assets of it (CN Version) .

> 这就是所有关于我们的战友指挥官的故事。
> 在无数个命运的拐角点，指挥官本可以成为——
> 一位优秀的战士。
> 一位温柔的前辈。
> 一位冲动的教官。
> 一位快乐的孩子。
> 
> 但指挥官从不肯把时间留给自己，总是留给别人。
> 
> 这一生那么长又那么短，指挥官只来得及成为一名勇敢的人。

## Usage

1. Get your current_version and replace the existing one in `main.py` with it:

```python
# set current version from environ
# Need to investigate it in GFL
current_version = os.environ.get('GFL_CN_CURRENT_VERSION', None)
if not current_version:
    current_version = '<current_version>'
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Run the script:

```bash
python download_assets.py
```

4. The script will now download the assets into `./gfl_cn*` directory generated.