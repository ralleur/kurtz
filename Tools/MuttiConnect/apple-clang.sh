#!/bin/sh
set -eu
exec xcrun --sdk "${MUTTI_APPLE_SDK:?}" clang -target "${MUTTI_APPLE_TRIPLE:?}" -isysroot "$(xcrun --sdk "$MUTTI_APPLE_SDK" --show-sdk-path)" "$@"
