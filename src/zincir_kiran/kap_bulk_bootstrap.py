"""KAP bulk financial archive bootstrap.

These archives are reusable raw evidence, not authoritative historical PIT snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class KapArchiveAuthority(StrEnum):
    RAW_EVIDENCE = "RAW_EVIDENCE"
    DISCOVERY_EVIDENCE = "DISCOVERY_EVIDENCE"


@dataclass(frozen=True)
class KapFinancialArchive:
    year: int
    period: str
    period_code: int
    filename: str
    download_url: str
    sha256: str
    member_count: int
    size_bytes: int
    exact_manifest_match: bool
    authority: KapArchiveAuthority = KapArchiveAuthority.RAW_EVIDENCE

    def __post_init__(self) -> None:
        if self.year < 2000:
            raise ValueError("invalid archive year")
        if self.period not in {"3A", "6A", "9A", "Y"}:
            raise ValueError("invalid period")
        if self.period_code not in {1, 2, 3, 4}:
            raise ValueError("invalid period_code")
        if not self.filename.strip():
            raise ValueError("filename is required")
        if not self.download_url.startswith("https://kap.org.tr/tr/api/financialTable/download/"):
            raise ValueError("download_url must be official KAP bulk route")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be 64 hex chars")
        int(self.sha256, 16)
        if self.member_count <= 0 or self.size_bytes <= 0:
            raise ValueError("archive counts/sizes must be positive")


def kap_bulk_archives_v1() -> tuple[KapFinancialArchive, ...]:
    rows = [
        (2019,"9A",3,"KAP_2019_9A.zip","c81e02d17aecfa141ee98c26a7373916d6b4531fa68476b7967a4d19fee80d41",432,16235475,True),
        (2019,"Y",4,"KAP_2019_Y.zip","734955b9ef13b485e8da7224f04b03ba5fe08e18335774e72a4295e8b6045118",502,17497008,True),
        (2020,"3A",1,"KAP_2020_3A.zip","f12e00d22d3575584301e0970e96fd9e455b6cc86b765c0deb1a8bfd4c11e115",425,15086931,True),
        (2020,"6A",2,"KAP_2020_6A.zip","150b539ff6b380eef66514995fd16536434596a69c97c03108885b08734f841f",512,18556936,True),
        (2020,"9A",3,"KAP_2020_9A.zip","ed627acc050f9fbbf0cf8c74d8801b2c45411a1eb60eb9819317e61a8d4cdbb0",432,16256591,True),
        (2020,"Y",4,"KAP_2020_Y.zip","6a6da9e47ed6918a292117ec1c700ca785b0416e52b3db44b290ff754e148fce",519,18141479,True),
        (2021,"3A",1,"KAP_2021_3A.zip","d953adceb72accfc4294cce4b40e79121ba10529ad2a17ef3f60e61654ecd654",466,16573084,True),
        (2021,"6A",2,"KAP_2021_6A.zip","8ebb059e19d31f56ea23c4eaafe383761a8fac2ec2160e3dec656d32da0afc7d",554,20195066,True),
        (2021,"9A",3,"KAP_2021_9A.zip","ac7cf0cc65b5dd567e2a3fb1e6261db73ec953d08ce47355b191d1c150679806",498,18781780,True),
        (2021,"Y",4,"KAP_2021_Y.zip","e6798fe4f673eb835d97325f405ec0cb168f20d9a6d33283622cc4fdf26e8f98",575,20293992,True),
        (2022,"3A",1,"KAP_2022_3A.zip","62de63b62f939feed7eb31ae4832a6ef884777eb796ee13c347eb5e8f860a4fc",522,18710612,True),
        (2022,"6A",2,"KAP_2022_6A.zip","81b08fce506533f890fba1638b3d1a1101450a4d56b88d92da8cbc99bbee9a91",620,22910458,True),
        (2022,"9A",3,"KAP_2022_9A.zip","623d3364855db39c611e7d9ec434ba072cb5abfd999afbe701f2b09943cb665c",539,20654632,True),
        (2022,"Y",4,"KAP_2022_Y.zip","841531a7c3a2918fbb6e51729c36862c252e80b811c875fafa07d78822894956",631,22477370,True),
        (2023,"3A",1,"KAP_2023_3A.zip","bccb5496f7ed249c37db3a294de9ccd4855c50395851c72ab539bcc543052133",556,20116678,True),
        (2023,"6A",2,"KAP_2023_6A.zip","2ccd51309f33db95b41d2b4e5e4512f15564603a3189c95bcdba97653d311088",656,24637205,True),
        (2023,"9A",3,"KAP_2023_9A.zip","d6aef26f4b837146e1f658126159e909b277ee879f9183d09a7023504e6f5316",592,22842796,True),
        (2023,"Y",4,"KAP_2023_Y.zip","9d8a26d43d16c31248b50635e29af0f6820e8bb361dd44eff5ba7d96106e6088",685,23986807,True),
        (2024,"3A",1,"KAP_2024_3A.zip","4199758e36f9e25c174d9fa9920ae06a45fe7d58407938d644eb0b5a7a6db0d0",616,21954398,True),
        (2024,"6A",2,"KAP_2024_6A.zip","1e09aceddd6edb14909e4f3db081ad084c0417fa2f203625b3dc571f77a237c6",705,26152529,True),
        (2024,"9A",3,"KAP_2024_9A.zip","94a04df809937e6291b6081c074e01cbafb4492a84fafd0ce24f4ab8afbcfd31",633,24046861,True),
        (2024,"Y",4,"KAP_2024_Y.zip","5e63acec0eb83e3e32df9faf5f7c0205c420e6b742407dd9c9aa4f6191944cf8",731,25881075,True),
        (2025,"3A",1,"KAP_2025_3A.zip","c9b107501ce81d8761e8840bf30c1ad26296330bb81cdbf542ae7a1e7b76bb7b",648,23167013,True),
        (2025,"6A",2,"KAP_2025_6A.zip","6016d431bdd550ce083e9d40e5e60baa0c1c74fb1e670fa6789d3957a7df35c1",738,27367724,True),
        (2025,"9A",3,"KAP_2025_9A.zip","421317ffb4edb55e1656773a5e6c8d4d9e2e79225888e2ff71556490dc817163",655,24914340,True),
        (2025,"Y",4,"KAP_2025_Y.zip","bef9ac8c5159db2fba8d388a1c4c1bf14f50c24bfef79c782b7efce93ef4e5c5",765,27013792,False),
        (2026,"3A",1,"KAP_2026_3A.zip","d7a53002009bc1c4672b80c272554412487d1abb21d95e69fed698cf8be2e82f",667,23833516,True),
        (2026,"6A",2,"KAP_2026_6A.zip","fca3ba9d59cda01c998712353a7f34c8f9a830f04241fdfcd274ecaf136e58d2",757,27815898,False),
    ]
    return tuple(
        KapFinancialArchive(
            year=year,
            period=period,
            period_code=period_code,
            filename=filename,
            download_url=f"https://kap.org.tr/tr/api/financialTable/download/{year}/{period_code}",
            sha256=sha256,
            member_count=member_count,
            size_bytes=size_bytes,
            exact_manifest_match=exact_match,
        )
        for year,period,period_code,filename,sha256,member_count,size_bytes,exact_match in rows
    )


def drifted_archives() -> tuple[KapFinancialArchive, ...]:
    return tuple(row for row in kap_bulk_archives_v1() if not row.exact_manifest_match)


def require_authoritative_historical_pit(_: KapFinancialArchive) -> None:
    raise ValueError(
        "current KAP bulk archive is raw evidence only; superseded-version enumeration is unresolved"
    )
