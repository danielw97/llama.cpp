# Instructions:
#
# - Add a new model to the "models" list
# - Run the script with your huggingface token:
#
#   python3 convert-hf-to-gguf-update.py <huggingface_token>
#
# - Copy-paste the generated get_vocab_base_pre() function into convert-hf-to-gguf.py
#
# TODO: generate tokenizer tests for llama.cpp
#

import os
import requests
import sys
import json

from hashlib import sha256
from enum import IntEnum, auto

class TOKENIZER_TYPE(IntEnum):
    SPM = auto()
    BPE = auto()
    WPM = auto()

# TODO: this string has to exercise as much pre-tokenizer functionality as possible
#       will be updated with time - contributions welcome
chktxt = '\n \n\n \n\n\n \t \t\t \t\n  \n   \n    \n     \n🚀 (normal) 😶‍🌫️ (multiple emojis concatenated) ✅ 🦙🦙 3 33 333 3333 33333 333333 3333333 33333333 3.3 3..3 3...3 កាន់តែពិសេសអាច😁 ?我想在apple工作1314151天～ ------======= нещо на Български what\'s \'\'\'\'\'\'```````\"\"\"\"......!!!!!!??????'

if len(sys.argv) == 2:
    token = sys.argv[1]
else:
    print("Usage: python convert-hf-to-gguf-update.py <huggingface_token>")
    sys.exit(1)

# TODO: add models here
models = [
        { "name": "llama-v2",       "tokenizer_type": TOKENIZER_TYPE.SPM, "repo": "https://huggingface.co/meta-llama/Llama-2-7b-hf",                },
        { "name": "llama-v3",       "tokenizer_type": TOKENIZER_TYPE.BPE, "repo": "https://huggingface.co/meta-llama/Meta-Llama-3-8B",              },
        { "name": "deepseek-llm",   "tokenizer_type": TOKENIZER_TYPE.BPE, "repo": "https://huggingface.co/deepseek-ai/deepseek-llm-7b-chat",        },
        { "name": "deepseek-coder", "tokenizer_type": TOKENIZER_TYPE.BPE, "repo": "https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-base",    },
        { "name": "bert-bge",       "tokenizer_type": TOKENIZER_TYPE.WPM, "repo": "https://huggingface.co/BAAI/bge-small-en-v1.5",                  },
        ]

# make directory "models/tokenizers" if it doesn't exist
if not os.path.exists("models/tokenizers"):
    os.makedirs("models/tokenizers")

def download_file_with_auth(url, token, save_path):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print("File downloaded successfully.")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

for model in models:
    name = model["name"]
    repo = model["repo"]
    tokenizer_type = model["tokenizer_type"]

    if not os.path.exists(f"models/tokenizers/{name}"):
        os.makedirs(f"models/tokenizers/{name}")
    else:
        print(f"Directory models/tokenizers/{name} already exists - skipping")
        continue

    print(f"Downloading {name} to models/tokenizers/{name}")

    url = f"{repo}/raw/main/tokenizer.json"
    save_path = f"models/tokenizers/{name}/tokenizer.json"
    download_file_with_auth(url, token, save_path)

    if tokenizer_type == TOKENIZER_TYPE.SPM:
        url = f"{repo}/resolve/main/tokenizer.model"
        save_path = f"models/tokenizers/{name}/tokenizer.model"
        download_file_with_auth(url, token, save_path)

    url = f"{repo}/raw/main/tokenizer_config.json"
    save_path = f"models/tokenizers/{name}/tokenizer_config.json"
    download_file_with_auth(url, token, save_path)

# generate the source code for the convert-hf-to-gguf.py:get_vocab_base_pre() function:
# TODO: auto-update convert-hf-to-gguf.py with the generated function

src_ifs = ""
for model in models:
    name = model["name"]
    tokenizer_type = model["tokenizer_type"]

    if tokenizer_type == TOKENIZER_TYPE.SPM:
        continue

    # create the tokenizer
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(f"models/tokenizers/{name}")

    chktok = tokenizer.encode(chktxt)
    chkhsh = sha256(str(chktok).encode()).hexdigest()

    print(f"model: {name}")
    print(f"tokenizer_type: {tokenizer_type}")
    print(f"repo: {model['repo']}")
    print(f"chktok: {chktok}")
    print(f"chkhsh: {chkhsh}")

    # print the "pre_tokenizer" content from the tokenizer.json
    with open(f"models/tokenizers/{name}/tokenizer.json", "r") as f:
        cfg = json.load(f)
        pre_tokenizer = cfg["pre_tokenizer"]
        print("pre_tokenizer: " + json.dumps(pre_tokenizer, indent=4))

    print(f"\n")

    src_ifs += f"        if chkhsh == \"{chkhsh}\":\n"
    src_ifs += f"            # ref: {model['repo']}\n"
    src_ifs += f"            res = \"{name}\"\n"

src_func = ""
src_func +=  "    def get_vocab_base_pre(self, tokenizer) -> str:\n"
src_func +=  "        # encoding this string and hashing the resulting tokens would (hopefully) give us a unique identifier that\n"
src_func +=  "        # is specific for the BPE pre-tokenizer used by the model\n"
src_func +=  "        # we will use this unique identifier to write a \"tokenizer.ggml.pre\" entry in the GGUF file which we can\n"
src_func +=  "        # use in llama.cpp to implement the same pre-tokenizer\n"
src_func +=  "\n"
src_func += f"        chktxt = {repr(chktxt)}\n"
src_func +=  "\n"
src_func +=  "        chktok = tokenizer.encode(chktxt)\n"
src_func +=  "        chkhsh = sha256(str(chktok).encode()).hexdigest()\n"
src_func +=  "\n"
src_func +=  "        print(f\"chktok: {chktok}\")\n"
src_func +=  "        print(f\"chkhsh: {chkhsh}\")\n"
src_func +=  "\n"
src_func +=  "        res = None\n"
src_func +=  "\n"
src_func +=  "        # NOTE: if you get an error here, you need to add the model to the if-elif chain below\n"
src_func += f"{src_ifs}\n"
src_func +=  "        if res is None:\n"
src_func +=  "            print(f\"\\n\")\n"
src_func +=  "            print(f\"**************************************************************************************\")\n"
src_func +=  "            print(f\"** WARNING: The BPE pre-tokenizer was not recognized!\")\n"
src_func +=  "            print(f\"**          This means that it was not added yet or you are using an older version.\")\n"
src_func +=  "            print(f\"**          Check convert-hf-to-gguf-update.py and update it accordingly.\")\n"
src_func +=  "            print(f\"**\")\n"
src_func +=  "            print(f\"** chkhsh:  {chkhsh}\")\n"
src_func +=  "            print(f\"**************************************************************************************\")\n"
src_func +=  "            print(f\"\\n\")\n"
src_func +=  "            raise NotImplementedError(\"BPE pre-tokenizer was not recognized - update get_vocab_base_pre()\")\n"
src_func +=  "\n"
src_func +=  "        print(f\"tokenizer.ggml.pre: {res}\")\n"
src_func +=  "        print(f\"chkhsh: {chkhsh}\")\n"
src_func +=  "\n"
src_func +=  "        return res\n"

print(src_func)

print("\n")
print("!!! Copy-paste the function above into convert-hf-to-gguf.py !!!")
print("\n")
