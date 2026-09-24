#!/usr/bin/env bash
# e-Gov 法令XML（法律のみ）のミラーを取得して data/laws/ に展開する。
#
# 本リポジトリは容量の都合で法令XML本体（約38MB圧縮）を同梱していない。
# 分析時に使ったのは aluqas/gitlaw-jp の 2025年5月時点のスナップショット
# （現行法律2,100本・laws/{元号3桁}/{法令ID}/current.xml）。
# gitlaw-jp はスナップショットごとにブランチが切られるため、REF で指定する。
#
# 使い方:
#   scripts/fetch_laws.sh                 # 既定ブランチ（最新スナップショット）
#   REF=<branch-or-tag> scripts/fetch_laws.sh
#
# 注意: 最新スナップショットは分析時点（2025年5月）と条文が異なりうる。
# 論文的な再現をしたい場合は当時のブランチを REF で指定すること。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_REPO="https://github.com/aluqas/gitlaw-jp.git"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ -n "${REF:-}" ]; then
  git clone --depth 1 --branch "$REF" --single-branch "$SRC_REPO" "$WORK/gitlaw-jp"
else
  git clone --depth 1 --single-branch "$SRC_REPO" "$WORK/gitlaw-jp"
fi

mkdir -p "$ROOT/data"
rm -rf "$ROOT/data/laws"
cp -R "$WORK/gitlaw-jp/laws" "$ROOT/data/laws"

echo "取得元: $SRC_REPO ($(git -C "$WORK/gitlaw-jp" rev-parse --short HEAD))"
echo "法令数: $(find "$ROOT/data/laws" -name current.xml | wc -l | tr -d ' ')"
echo "展開先: $ROOT/data/laws"
