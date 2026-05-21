from pathlib import Path

from flomers_kg.sample_pipeline import (
    load_manufacturers,
    load_products,
    read_jsonl,
    source_from_dict,
)


def test_read_jsonl_skips_blank_lines(tmp_path: Path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"id": "a"}\n\n  \n{"id": "b"}\n', encoding="utf-8")

    assert read_jsonl(path) == [{"id": "a"}, {"id": "b"}]


def test_source_from_dict_returns_none_when_source_missing():
    assert source_from_dict({"id": "m1"}) is None


def test_loaders_preserve_nested_source_metadata(tmp_path: Path):
    manufacturers_path = tmp_path / "manufacturers.jsonl"
    manufacturers_path.write_text(
        (
            '{"id":"m1","name":"ABC","country":"KR","categories":["haircare"],'
            '"source":{"source_type":"sample","source_urls":["https://example.com"],"confidence_level":5}}\n'
        ),
        encoding="utf-8",
    )
    products_path = tmp_path / "products.jsonl"
    products_path.write_text(
        '{"id":"p1","manufacturer_id":"m1","name":"헤어오일","category":"haircare"}\n',
        encoding="utf-8",
    )

    manufacturer = load_manufacturers(manufacturers_path)[0]
    product = load_products(products_path)[0]

    assert manufacturer.source is not None
    assert manufacturer.source.source_urls == ["https://example.com"]
    assert product.source is None
