FROM python:3.12-slim

ARG TARGETARCH=amd64
ARG SCU_CLI_VERSION=v0.4.1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates clamav-daemon curl fonts-noto-cjk libmagic1 \
    libreoffice-calc libreoffice-impress libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

RUN asset="scu-linux-${TARGETARCH}" \
    && release_url="https://github.com/The-Brotherhood-of-SCU/SCU-CLI/releases/download/${SCU_CLI_VERSION}" \
    && curl -fsSL --connect-timeout 15 --max-time 120 --retry 5 --retry-all-errors \
        --continue-at - "${release_url}/${asset}" -o /tmp/scu \
    && curl -fsSL --connect-timeout 15 --max-time 120 --retry 5 --retry-all-errors \
        "${release_url}/checksums.txt" -o /tmp/scu-checksums.txt \
    && grep "  ${asset}$" /tmp/scu-checksums.txt \
        | sed "s#${asset}#/tmp/scu#" \
        | sha256sum -c - \
    && install -m 0755 /tmp/scu /usr/local/bin/scu \
    && mkdir -p /usr/share/licenses/scu-cli \
    && curl -fsSL --connect-timeout 15 --max-time 120 --retry 5 --retry-all-errors \
        "https://raw.githubusercontent.com/The-Brotherhood-of-SCU/SCU-CLI/${SCU_CLI_VERSION}/LICENSE" \
        -o /usr/share/licenses/scu-cli/LICENSE \
    && /usr/local/bin/scu --version \
    && rm -f /tmp/scu /tmp/scu-checksums.txt

COPY pyproject.toml .
RUN python -c \
        "import pathlib, tomllib; dependencies = tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['dependencies']; pathlib.Path('/tmp/requirements.txt').write_text('\\n'.join(dependencies) + '\\n')" \
    && pip install --no-cache-dir --default-timeout=120 --retries=5 -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

COPY . .

RUN pip install --no-cache-dir --no-deps -e .

RUN mkdir -p /app/data/thumbnails

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
