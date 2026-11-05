"""Exercise signing and renewal without files, credentials or network access."""

import datetime
import importlib.util
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture
def auth(monkeypatch):
    path = Path(__file__).parents[1] / "n8n_ingress_proxy.py"
    spec = importlib.util.spec_from_file_location("isolated_ingress", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(module, "PAT", "")
    monkeypatch.setattr(module, "ACCOUNT", "example_account")
    monkeypatch.setattr(module, "USER", "example_user")
    monkeypatch.setattr(module.SnowflakeIngressAuth, "_load_private_key", staticmethod(lambda: key))
    return module.SnowflakeIngressAuth(), key


def test_rs256_signing_and_claims(auth):
    signer, key = auth
    token, expires = signer._mint_jwt()
    claims = jwt.decode(token, key.public_key(), algorithms=["RS256"])
    assert claims["sub"] == "EXAMPLE_ACCOUNT.EXAMPLE_USER"
    assert claims["iss"] == f"EXAMPLE_ACCOUNT.EXAMPLE_USER.{signer._fingerprint()}"
    assert claims["exp"] == int(expires.timestamp())
    assert claims["exp"] - claims["iat"] == 55 * 60
    with pytest.raises(jwt.InvalidAlgorithmError):
        jwt.decode(token, key.public_key(), algorithms=["HS256"])


def test_cache_and_renewal(auth, monkeypatch):
    signer, _ = auth
    calls = []
    mint = signer._mint_jwt

    def counted_mint():
        calls.append(True)
        return mint()

    monkeypatch.setattr(signer, "_mint_jwt", counted_mint)
    first = signer.header()
    assert first.startswith('Snowflake Token="')
    assert signer.header() == first
    assert len(calls) == 1
    signer._expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=4)
    signer.header()
    assert len(calls) == 2