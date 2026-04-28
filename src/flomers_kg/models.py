from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceMeta:
    source_type: str
    source_urls: list[str] = field(default_factory=list)
    confidence_level: int = 1
    collected_at: str | None = None
    verified_at: str | None = None


@dataclass
class Manufacturer:
    id: str
    name: str
    country: str
    categories: list[str]
    region: str | None = None
    website: str | None = None
    production_capabilities: list[str] = field(default_factory=list)
    oem_available: bool | None = None
    odm_available: bool | None = None
    certifications: list[str] = field(default_factory=list)
    export_experience: list[str] = field(default_factory=list)
    response_score: float | None = None
    trust_level: int = 1
    source: SourceMeta | None = None


@dataclass
class Product:
    id: str
    manufacturer_id: str
    name: str
    category: str
    description: str = ""
    specs: dict[str, Any] = field(default_factory=dict)
    features: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    suitable_channels: list[str] = field(default_factory=list)
    suitable_countries: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    moq: int | None = None
    cost: float | None = None
    suggested_price: float | None = None
    source: SourceMeta | None = None


@dataclass
class Distributor:
    id: str
    name: str
    country: str
    locations: list[str] = field(default_factory=list)
    warehouse_locations: list[str] = field(default_factory=list)
    portfolio_categories: list[str] = field(default_factory=list)
    handled_brands: list[str] = field(default_factory=list)
    distribution_channels: list[str] = field(default_factory=list)
    trade_types: list[str] = field(default_factory=list)
    logistics_capabilities: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    source: SourceMeta | None = None


@dataclass
class Seller:
    id: str
    name: str
    country: str
    channels: list[str]
    portfolio_products: list[str] = field(default_factory=list)
    best_sellers: list[str] = field(default_factory=list)
    price_band: str = ""
    categories: list[str] = field(default_factory=list)
    content_style: list[str] = field(default_factory=list)
    target_customer: list[str] = field(default_factory=list)
    trend_keywords: list[str] = field(default_factory=list)
    review_keywords: list[str] = field(default_factory=list)
    commerce_capabilities: list[str] = field(default_factory=list)
    source: SourceMeta | None = None


@dataclass
class Trend:
    id: str
    name: str
    countries: list[str]
    channels: list[str]
    keywords: list[str]
    related_categories: list[str]
    signal_strength: float = 0.0
    seasonality: str = ""
    source: SourceMeta | None = None


@dataclass
class MatchCandidate:
    id: str
    manufacturer: Manufacturer
    product: Product
    distributor: Distributor
    seller: Seller
    target_country: str
    target_channels: list[str]
    score: float = 0.0
    recommendation_level: str = ""
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
