"""Pinned OpenAI embedding-tokenizer resource; generated data stays outside Git."""
import os
from pathlib import Path

LIBRARY_VERSION = '0.14.0'
ENCODING_NAME = 'cl100k_base'
RESOURCE_URL = 'https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken'
RESOURCE_SHA256 = '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7'
RESOURCE_BYTES = 1681126
# Official cl100k_base constructor, pinned with tiktoken0.14.0; no custom BPE algorithm.
PATTERN = r"'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s"
SPECIAL_TOKENS = {'<|endoftext|>':100257,'<|fim_prefix|>':100258,'<|fim_middle|>':100259,
                  '<|fim_suffix|>':100260,'<|endofprompt|>':100276}


def resource_path() -> Path:
    configured = os.getenv('EMBEDDING_TOKENIZER_FILE')
    return Path(configured) if configured else Path.home()/'.cache/economicon/tokenizers/cl100k_base.tiktoken'


def assert_external_resource_path(path: Path) -> None:
    for parent in Path(__file__).resolve().parents:
        if ((parent/'.git').exists() or ((parent/'pnpm-workspace.yaml').is_file()
                and (parent/'apps/processor/app').is_dir())):
            if Path(path).resolve().is_relative_to(parent):
                raise ValueError('The embedding tokenizer resource must stay outside the repository')
            break
