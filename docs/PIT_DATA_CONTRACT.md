# Point-in-Time Data Contract v0.1

Bu belge Implementation 1 için minimum veri sözleşmesini tanımlar.

## Core entities

### ingestion_batches

Her veri çekimi yeniden üretilebilir bir batch kimliği taşır.

```text
batch_id
source_id
extractor_version
started_at
completed_at
status
notes
```

### raw_records

Ham kayıtlar overwrite edilmez; aynı source kaydı değişirse yeni içerik hash'i ile yeni raw kayıt olarak saklanır.

```text
raw_record_id
source_id
batch_id
source_record_key
source_url
content_type
storage_uri
payload
content_sha256
source_published_at
retrieved_at
created_at
```

En az `payload` veya `storage_uri` bulunmalıdır. `content_sha256` kaynak snapshot'ının bütünlük kimliğidir.

### companies

Amaç: kalıcı şirket kimliği ile ticker tarihçesini ayırmak.

Önerilen alanlar:

```text
company_id
legal_name
sector
industry
company_type
first_trade_date
last_trade_date
status
source
created_at
```

### security_identifiers

```text
security_id
company_id
ticker
valid_from
valid_to
exchange
isin
source
```

Ticker şirket kimliği değildir.

### prices

```text
security_id
trade_date
open
high
low
close
volume
turnover_value
source
raw_record_id
available_at
ingested_at
quality_flag
```

Adjusted ve unadjusted serilerin kaynağı/kuralları açık tutulmalıdır.

### financial_facts

```text
company_id
statement_type
metric_id
period_start
period_end
fiscal_period
value
currency
unit
reported_at
available_at
revision_id
source
raw_record_id
reporting_standard
inflation_adjusted
restatement_status
quality_flag
```

### financial_revisions

Bir sağlayıcı veya şirket geçmiş finansalı revize ettiğinde eski versiyon korunur.

```text
revision_id
company_id
metric_id
period_end
supersedes_revision_id
value
reported_at
available_at
source
reason
```

### corporate_actions

```text
security_id
action_type
announcement_at
ex_date
record_date
payment_date
ratio
cash_amount
currency
source
raw_record_id
available_at
quality_flag
```

### shares_history

```text
company_id
effective_from
effective_to
shares_outstanding
free_float_shares
free_float_ratio
source
raw_record_id
available_at
quality_flag
```

### universe_history

```text
trade_date
security_id
is_investable
reason_code
liquidity_tier
source
model_rule_version
```

### source_registry

```text
source_id
name
source_type
license_notes
timestamp_quality
revision_policy
priority
active
```

## Mandatory timestamp semantics

### reported_at

Kaynağın olayı / veriyi ilk açıkladığı zaman.

### available_at

Modelin bu bilgiyi güvenli biçimde kullanmaya başlayabileceği zaman.

Backtest filtre kuralı:

```text
available_at <= prediction_timestamp
```

olmadan veri feature hesaplamasına giremez.

## Revision policy

1. RAW veri immutable tutulur; aynı `source_record_key + content_sha256` tekrar eklenemez.
2. Yeni veri eski değerin üstüne sessizce yazılmaz.
3. Revision lineage mümkün olduğunca korunur.
4. Backtest, prediction timestamp'te hangi revision mevcutsa onu kullanır.

## Quality flags

Başlangıç enum adayları:

```text
VERIFIED
SOURCE_CONFLICT
MISSING_TIMESTAMP
ESTIMATED_TIMESTAMP
RESTATED
STALE
SUSPECT
REJECTED
```

Kesin enum Implementation 1 içinde testlerle kilitlenecektir.

## Accounting regime fields

En az:

```text
reporting_standard
inflation_adjusted
restatement_status
original_period
publication_date
revision_date
```

TMS 29 etkisi financial feature hesaplama katmanında açıkça izlenir.

## Provenance rule

Her production feature geriye doğru şu zincire izlenebilir olmalıdır:

```text
model_score
-> factor_value
-> feature_value
-> PIT fact
-> raw_record_id
-> ingestion_batch
-> source_registry
```

Kaynağı izlenemeyen veri production scoring'e giremez.

## Initial source priority

Kesin sıralama Implementation 1 sırasında doğrulanacaktır. Başlangıç adayları:

1. resmi KAP / Borsa İstanbul kaynakları
2. doğrulanmış şirket raporları
3. lisanslı / güvenilir finansal veri sağlayıcı
4. InvestingPro+ yardımcı veri / cross-check
5. web extraction yalnızca provenance korunarak

Hiçbir kaynak point-in-time tarihçesi sağlamıyor diye geçmiş timestamp uydurulamaz.
