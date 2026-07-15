"""Philox4x32-10 and the frozen A9 length-prefixed identity encoding."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from datetime import date

from .errors import require

MASK32 = 0xFFFFFFFF
M0 = 0xD2511F53
M1 = 0xCD9E8D57
W0 = 0x9E3779B9
W1 = 0xBB67AE85
SIMULATION_DOMAIN = b"cligen-rs/a9-crn/v1\0"
IDENTITY_FIELDS = ("campaign", "site", "burn", "component", "date", "slot")


def _mulhilo(multiplier: int, value: int) -> tuple[int, int]:
    product = (multiplier & MASK32) * (value & MASK32)
    return (product >> 32) & MASK32, product & MASK32


def philox4x32_10(
    counter: tuple[int, int, int, int], key: tuple[int, int]
) -> tuple[int, int, int, int]:
    """Return the Random123 Philox4x32-10 block for exact integer inputs."""

    require(all(0 <= word <= MASK32 for word in counter + key), "RNG_WORD_RANGE", "u32")
    c0, c1, c2, c3 = counter
    k0, k1 = key
    for round_index in range(10):
        hi0, lo0 = _mulhilo(M0, c0)
        hi1, lo1 = _mulhilo(M1, c2)
        c0, c1, c2, c3 = (
            (hi1 ^ c1 ^ k0) & MASK32,
            lo1,
            (hi0 ^ c3 ^ k1) & MASK32,
            lo0,
        )
        if round_index != 9:
            k0 = (k0 + W0) & MASK32
            k1 = (k1 + W1) & MASK32
    return c0, c1, c2, c3


def encode_identity(domain: bytes, fields: tuple[str, ...]) -> bytes:
    """Encode domain then six UTF-8 fields with big-endian u32 lengths."""

    require(domain.endswith(b"\0"), "RNG_DOMAIN_INVALID", "domain must end in NUL")
    require(len(fields) == len(IDENTITY_FIELDS), "RNG_IDENTITY_ARITY", "six fields required")
    material = bytearray(domain)
    for field in fields:
        encoded = field.encode("utf-8")
        require(len(encoded) <= MASK32, "RNG_IDENTITY_TOO_LONG", field[:32])
        material.extend(struct.pack(">I", len(encoded)))
        material.extend(encoded)
    return bytes(material)


@dataclass(frozen=True)
class RandomFieldIdentity:
    campaign: str
    site: str
    burn: str
    component: str
    day: date
    slot: str

    def fields(self) -> tuple[str, ...]:
        return (
            self.campaign,
            self.site,
            self.burn,
            self.component,
            self.day.isoformat(),
            self.slot,
        )


def identity_material(identity: RandomFieldIdentity) -> bytes:
    return encode_identity(SIMULATION_DOMAIN, identity.fields())


def key_counter(identity: RandomFieldIdentity) -> tuple[tuple[int, int], tuple[int, int, int, int]]:
    """Derive little-endian key/counter words from SHA-256 identity bytes."""

    digest = hashlib.sha256(identity_material(identity)).digest()
    key = struct.unpack("<2I", digest[:8])
    counter = struct.unpack("<4I", digest[8:24])
    return key, counter


def random_words(identity: RandomFieldIdentity) -> tuple[int, int, int, int]:
    key, counter = key_counter(identity)
    return philox4x32_10(counter, key)


def uniform(identity: RandomFieldIdentity, word: int = 0) -> float:
    require(0 <= word < 4, "RNG_WORD_INDEX", str(word))
    return (random_words(identity)[word] + 0.5) / 4294967296.0


def domain_seed(domain: str, *identities: str) -> int:
    """Derive a separate 256-bit seed for non-simulation research RNGs."""

    require(domain in {"fit", "optimizer", "parameter_member", "synthetic_fixture"}, "RNG_DOMAIN", domain)
    encoded = encode_identity(
        b"cligen-rs/a9-research-domain/v1\0",
        (domain, *identities, *([""] * (5 - len(identities)))),
    )
    return int.from_bytes(hashlib.sha256(encoded).digest(), "big")

