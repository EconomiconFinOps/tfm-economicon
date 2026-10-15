# Official source-only distribution, fixed sources and base images; no vendored binaries.
FROM golang:1.24.8-bookworm@sha256:4ed690d6649d63c312b99a6120025ec79ce3b542968a37da53d6236c7c61a848 AS source
ENV CGO_ENABLED=0 GOTOOLCHAIN=local
ADD --checksum=sha256:be6d0bd3696c3a13a35f02d3a0280b64319c67918b4501c5c3d87f96d000085c https://codeload.github.com/minio/minio/tar.gz/RELEASE.2025-10-15T17-29-55Z /tmp/minio.tar.gz
ADD --checksum=sha256:29db22500374169a43951c7cef09daf19e7291ea5ba00ac10f321371b0a35b32 https://codeload.github.com/minio/mc/tar.gz/RELEASE.2025-08-13T08-35-41Z /tmp/mc.tar.gz
RUN mkdir /src && tar -xzf /tmp/minio.tar.gz -C /src && tar -xzf /tmp/mc.tar.gz -C /src
RUN cd /src/minio-* && go build -trimpath -o /out/minio .
RUN cd /src/mc-* && go build -trimpath -o /out/mc .

FROM python:3.12-slim@sha256:d764629ce0ddd8c71fd371e9901efb324a95789d2315a47db7e4d27e78f1b0e9 AS runtime
COPY --from=source /out/minio /usr/local/bin/minio
COPY --from=source /out/mc /usr/local/bin/mc
COPY --from=source /src/minio-*/LICENSE /usr/share/licenses/minio/LICENSE
COPY --from=source /src/mc-*/LICENSE /usr/share/licenses/mc/LICENSE
RUN useradd --uid 10001 --create-home storage && mkdir /data && chown storage:storage /data
USER storage
EXPOSE 9000
ENTRYPOINT ["minio", "--certs-dir", "/tmp/certs"]
CMD ["server", "/data", "--address", ":9000", "--console-address", ":9001"]
