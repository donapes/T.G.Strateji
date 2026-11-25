#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

exec > >(tee check_results.log) 2>&1

echo "========================================"
echo "T.G. Stratejisi Temel Altyapi Kontrolleri"
echo "========================================"

echo
echo "UTC zaman:"
date -u +"%Y-%m-%dT%H:%M:%SZ"

echo
echo "Gerekli dosyalar kontrol ediliyor..."

required_files=(
    "core_v021.py"
    "test_core_v021.py"
    "validate_source_map.py"
    "source_usage_map_v022.csv"
    "requirements.txt"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "HATA: Dosya bulunamadi: $file"
        exit 1
    fi
done

echo
echo "Python surumu:"
python --version

echo
echo "Bagimlilik surumleri:"
python -c \
    "import numpy, pandas; print('numpy:', numpy.__version__); print('pandas:', pandas.__version__)"

echo
echo "Calistirilan dosyalarin SHA-256 ozetleri:"
sha256sum \
    core_v021.py \
    test_core_v021.py \
    validate_source_map.py \
    source_usage_map_v022.csv \
    requirements.txt

echo
echo "----------------------------------------"
echo "Core testleri"
echo "----------------------------------------"

python -m unittest test_core_v021 -v

echo
echo "----------------------------------------"
echo "Kaynak haritasi dogrulamasi"
echo "----------------------------------------"

python validate_source_map.py

echo
echo "========================================"
echo "Calistirilan tum kontroller basarili."
echo "Bu sonuc kaynak sadakatini kanitlamaz."
echo "========================================"