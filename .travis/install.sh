#!/bin/bash

# Originally from
# <https://github.com/pyca/cryptography/blob/d93aa99636b06d5d403130425098b2f0cc1b516e/.travis/install.sh>.

set -e
set -x
set -o pipefail

git clean -f -d -X
rm -r -f $PWD/.pyenv  # Apparently `git-clean` won't remove other repositories.

if [[ "$(uname -s)" == 'Darwin' ]]; then
    brew update || brew update
    brew install pyenv
    brew outdated pyenv || brew upgrade pyenv

    if which -s pyenv; then
        rm -r -f $HOME/.pyenv
        eval "$(pyenv init -)"
    fi

    case "${TOX_ENV}" in
        py37)
            pyenv install 3.7.0
            pyenv global 3.7.0
            ;;
    esac
    pyenv rehash
fi

python -m venv $PWD/.venv
source $PWD/.venv/bin/activate
pip install -U tox
