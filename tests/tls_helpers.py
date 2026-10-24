"""Certificates for the database-TLS tests. Both are THROWAWAY, PUBLIC-ONLY test certificates (generated for this repository, their private keys were never
written to disk, they are trusted by nothing and name no real host). They stand in for "a CA certificate file" and "a certificate that is not a CA". The real
database CA certificate is never committed: it is supplied by the host (a Render secret file) through DB_SSL_CA."""

# A self-signed certificate with basicConstraints CA:TRUE: ssl.create_default_context(cafile=...).get_ca_certs() lists it.
TEST_CA_PEM = """-----BEGIN CERTIFICATE-----
MIIBzzCCAXWgAwIBAgIUcyuXICXD2dltUUVnjdQAHqXCVxQwCgYIKoZIzj0EAwIw
NDEyMDAGA1UEAwwpR1RBNiB0ZXN0cyB0aHJvd2F3YXkgQ0EgKHRydXN0ZWQgbm93
aGVyZSkwIBcNMjYxMDI0MTEyMjEyWhgPMjEyNjA5MzAxMTIyMTJaMDQxMjAwBgNV
BAMMKUdUQTYgdGVzdHMgdGhyb3dhd2F5IENBICh0cnVzdGVkIG5vd2hlcmUpMFkw
EwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE+FKPlA0FdUx1DwbZcyCFgoybho6Fqbxj
ikXWicJ37I93IBL7S8wsZVNQUMTnPFOE8PzjdA+EAl9dm2E0urKeMaNjMGEwHQYD
VR0OBBYEFCkzbmtg3wMhH73QAXW0+nhrrfL6MB8GA1UdIwQYMBaAFCkzbmtg3wMh
H73QAXW0+nhrrfL6MA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMAoG
CCqGSM49BAMCA0gAMEUCIQDcHIKiuNJqu7GcUvIP834Le3fw4bIjghJu14GSgfT2
GQIge2Ps7dfr+QBKRbdDampvbIlUBvtnEW8k2cd/SgJpH7s=
-----END CERTIFICATE-----
"""

# A self-signed certificate with basicConstraints CA:FALSE: valid PEM, but it is not a CA, so it cannot anchor a verification.
TEST_LEAF_PEM = """-----BEGIN CERTIFICATE-----
MIIBszCCAVigAwIBAgIUNlhbtKUJ/VbL+pLpyn0W/U573p4wCgYIKoZIzj0EAwIw
LzEtMCsGA1UEAwwkR1RBNiB0ZXN0cyB0aHJvd2F3YXkgbGVhZiAobm90IGEgQ0Ep
MCAXDTI2MTAyNDExMjIxMloYDzIxMjYwOTMwMTEyMjEyWjAvMS0wKwYDVQQDDCRH
VEE2IHRlc3RzIHRocm93YXdheSBsZWFmIChub3QgYSBDQSkwWTATBgcqhkjOPQIB
BggqhkjOPQMBBwNCAAQesIavruNp/gzHEYhHh9w38hVEYevkemvgBLrUFFoESx6u
rqj2qHt92fZJ1/XPZQH1BZmAIHqJpYcSf3ghYfwRo1AwTjAdBgNVHQ4EFgQUc85h
mtTc2DWJL3IwnTtJ588btHQwHwYDVR0jBBgwFoAUc85hmtTc2DWJL3IwnTtJ588b
tHQwDAYDVR0TAQH/BAIwADAKBggqhkjOPQQDAgNJADBGAiEA4TlK2P+bn/XZKsrT
rwK8bw789QcVLmv1n1KXksyLfB4CIQDhqRAtfDjLKw+ifECFb7voonNtcTY8Jgjm
Dm+AFcVhjQ==
-----END CERTIFICATE-----
"""
