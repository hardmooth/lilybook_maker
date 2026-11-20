# Image with the complete toolchain of lilybook: make, lilypond, latexmk and TeX Live.
# The package list matches .github/workflows/tests.yml.
#
#   podman build -t lilybook .
#   podman run --rm -v "$PWD":/book lilybook [target ...]      (inside a book directory)
#
# The wrappers lilybook-container and lilybook-container.cmd do both steps.
FROM docker.io/library/ubuntu:24.04

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      make lilypond latexmk poppler-utils git python3 \
      texlive-latex-base texlive-latex-recommended texlive-latex-extra \
      texlive-fonts-recommended texlive-fonts-extra texlive-lang-german \
 && rm -rf /var/lib/apt/lists/* \
 # the mounted book belongs to a user of the host, which git rejects as "dubious ownership"
 && git config --system --add safe.directory '*'

COPY lilybook lilybook.mk /opt/lilybook_maker/
RUN chmod +x /opt/lilybook_maker/lilybook && ln -s /opt/lilybook_maker/lilybook /usr/local/bin/lilybook

# TeX and lilypond write caches below HOME, and the build runs as an arbitrary user of the host
ENV HOME=/tmp
WORKDIR /book
ENTRYPOINT ["lilybook"]
