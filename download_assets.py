import UnityPy
from typing import List, Tuple
import requests
import aiohttp
import aiofiles
import asyncio
import logging
import os
import zipfile
from collections import Counter

# set current version from environ
# Need to investigate it in GFL
current_version = os.environ.get('GFL_CN_CURRENT_VERSION', None)
if not current_version:
    current_version = 'u75R2sb7G5GtVhJV0catJE0m75QRG6h7lZ5yIy3W9x9kC9utVPvw'

# set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# set up constants
GFL_CN_ASSETBUNDLE_DIR = os.path.join(
    os.path.dirname(__file__), 'gfl_cn_bundles')
GFL_CN_BYTES_ZIPPED_DIR = os.path.join(
    os.path.dirname(__file__), 'gfl_cn_bytes_zipped')
GFL_CN_BYTES_DIR = os.path.join(
    os.path.dirname(__file__), 'gfl_cn_bytes')
dirs = [GFL_CN_ASSETBUNDLE_DIR, GFL_CN_BYTES_ZIPPED_DIR, GFL_CN_BYTES_DIR]

GFL_CN_VERSION_METADATA_TEMPLATE = "https://gf-cn.oss-cn-beijing.aliyuncs.com/{}.txt"
GFL_CN_ASSETBUNDLE_TEMPLATE = "{}{}.ab"
GFL_CN_BYTESDATA_TEMPLATE = "{}{}.dat"

# create download directories
for d in dirs:
    os.makedirs(d, exist_ok=True)


async def fetch_file(session, sema, output_path: str, url: str, fname: str, expected_size: int) -> str:
    if (os.path.exists(output_path) and os.path.getsize(output_path) == expected_size):
        logger.info(f'Skipping {fname} as it already exists.')
        # skipped
        return 's'
    else:
        logger.info(f'Downloading {url} to {output_path}')
        async with sema:
            async with session.get(url) as resp:
                assert resp.status == 200
                data = await resp.read()
        if len(data) != expected_size:
            logger.warn(
                f'Size mismatch for {fname}: {len(data)}, should be {expected_size}')
        async with aiofiles.open(output_path, "wb") as outfile:
            await outfile.write(data)
        logger.info(f'{fname} written to {output_path}')
        # downloaded
        return 'd'


async def download_files(input_tasks: List[Tuple[str, str, str, int]]) -> Tuple[int, int, int]:
    '''
    returns:
        task count given, 
        downloaded,
        skipped
    '''
    sema = asyncio.BoundedSemaphore(20)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for input_task in input_tasks:
            tasks.append(fetch_file(session, sema, *input_task))
        results = await asyncio.gather(*tasks)
        stats = Counter(results)
    return len(input_tasks), stats['d'], stats['s']


initial_metadata_unityfs = requests.get(
    GFL_CN_VERSION_METADATA_TEMPLATE.format(current_version)).content
env = UnityPy.load(initial_metadata_unityfs)
initial_metadata_dict = env.container['assets/resources/resdata.asset'].read_typetree()

RES_URL = initial_metadata_dict['resUrl']
print(RES_URL)

# passivityAssetBundles, BaseAssetBundles, AddAssetBundles are assetbundles
assetbundle_list = initial_metadata_dict['passivityAssetBundles'] + \
    initial_metadata_dict['BaseAssetBundles'] + \
    initial_metadata_dict['AddAssetBundles']
assetbundle_tasks: List[Tuple[str, str, int]] = []
for assetbundle in assetbundle_list:
    url = GFL_CN_ASSETBUNDLE_TEMPLATE.format(RES_URL, assetbundle['resname'])
    filename = assetbundle['assetBundleName'] + '.ab'
    size = assetbundle['sizeCompress']
    assetbundle_local_path = os.path.join(GFL_CN_ASSETBUNDLE_DIR, filename)
    assetbundle_tasks.append((assetbundle_local_path, url, filename, size))

asyncio.run(download_files(assetbundle_tasks))

# bytesData are bytes
bytesdata_list = initial_metadata_dict['bytesData']
bytesdata_tasks: List[Tuple[str, str, int]] = []
for bytesdata in bytesdata_list:
    url = GFL_CN_BYTESDATA_TEMPLATE.format(RES_URL, bytesdata['resname'])
    filename = bytesdata['fileName'] + '.bytes'
    size = bytesdata['sizeCompress']
    bytesdata_local_path = os.path.join(GFL_CN_BYTES_ZIPPED_DIR, filename)
    bytesdata_tasks.append((bytesdata_local_path, url, filename, size))

asyncio.run(download_files(bytesdata_tasks))

for bytesdata in bytesdata_list:
    filename = bytesdata['fileName'] + '.bytes'
    bytesdata_local_path = os.path.join(GFL_CN_BYTES_ZIPPED_DIR, filename)
    logger.info(f'Extracting {filename}...')
    with zipfile.ZipFile(bytesdata_local_path, 'r') as zip_ref:
        zip_ref.extractall(GFL_CN_BYTES_DIR)
