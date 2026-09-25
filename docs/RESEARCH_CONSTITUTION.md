# Research Constitution v1.0

## 1. Objective — LOCKED

Zincir Kıran'ın amacı iyi şirket bulmak değil, bugün gerçekten bilinebilen bilgiler kullanılarak BIST hisselerinin gelecekteki market-relative / cross-sectional getirisini tahmin etmektir.

Primary horizons:

- H20 = 20 trading days
- H60 = 60 trading days
- H120 = 120 trading days
- H252 = 252 trading days

Primary target:

```text
future market-relative total return
```

Her horizon ayrı değerlendirilir.

## 2. Total Rasyo'nun konumu — LOCKED

Total Rasyo:

- production model değildir,
- başarı referansı değildir,
- başarısız baseline + hata kataloğu + öğrenme kaynağıdır.

Yeni motorun Total Rasyo ile yüksek korelasyonu otomatik olarak olumlu sayılmaz.

## 3. Point-in-Time — LOCKED

Her finansal/veri kaydı en az şu kavramları taşımalıdır:

```text
ticker
period
value
source
reported_at
available_at
revision_id
accounting_standard
quality_flag
```

En kritik alan `available_at`'tır.

Bir veri t anında bilinemiyorsa t tarihli backtestte kullanılamaz.

Kesin açıklama saati mevcutsa gerçek zaman damgası kullanılır. Yalnızca tarih biliniyorsa konservatif kullanım kuralı uygulanır.

## 4. Raw data immutability — LOCKED

Katmanlar:

```text
RAW -> CLEAN -> POINT-IN-TIME -> FEATURES -> FACTORS -> MODELS -> PORTFOLIO
```

RAW veri geçmişte sağlayıcı tarafından değiştirildiğinde mümkünse eski değer silinmez; revision olarak korunur.

## 5. Survivorship / universe — LOCKED

Bugünkü BIST listesi geçmişe yapıştırılamaz.

Her tarihte:

```text
U_t = stocks actually investable at time t
```

yeniden oluşturulur.

Delist edilmiş şirketler geçmiş evrenden silinmez.

## 6. Corporate actions — LOCKED

En az:

- split / reverse split
- bedelli / bedelsiz
- temettü
- birleşme / bölünme
- ticker değişimi
- delisting
- tarihsel shares outstanding / free float gereken durumlar

doğru işlenmelidir.

## 7. Missing data — LOCKED

```text
NaN != Neutral
```

Eksik veri `0.5` veya benzeri nötr skora dönüştürülemez.

İzin verilen sonuçlar:

- factor unavailable
- lower confidence
- insufficient evidence
- rejection

## 8. Accounting regime — LOCKED

Türkiye için TMS 29 / enflasyon muhasebesi ayrı bir accounting regime olarak modellenir.

En az:

```text
reporting_standard
inflation_adjusted
restatement_status
original_period
publication_date
revision_date
```

metadata'sı korunmalıdır.

Pre/post-TMS29 büyüme ve bilanço serileri kör biçimde birleştirilemez.

## 9. Sector-aware features — LOCKED

Tek formül bütün BIST şirketlerine zorla uygulanmaz.

Her feature için applicability mask bulunur.

Örneğin EV/EBITDA banka ve sigorta şirketlerine otomatik uygulanmaz.

## 10. Factor families — LOCKED

Başlangıç ekonomik aileleri:

1. Value
2. Profitability
3. Quality
4. Investment Discipline
5. Fundamental Acceleration
6. Price Momentum
7. Earnings Momentum / Revisions
8. Risk
9. Liquidity
10. Size / controls

Ham predictor sayısı daha yüksek olabilir; ancak aynı ekonomik bilginin kopyaları bağımsız oy sayılmaz.

## 11. De-duplication — LOCKED

Redundancy için uygun şekilde:

- rolling correlation
- hierarchical clustering
- PCA
- residualization

kullanılabilir.

Amaç aynı ekonomik bilginin birden fazla oy kullanmasını önlemektir.

## 12. Factor admission — LOCKED PROCESS

Akademik yayın production factor değildir.

Her candidate factor için en az:

- expected direction
- economic rationale
- academic evidence
- international evidence
- BIST OOS evidence
- liquid-stock evidence
- recent-period evidence
- monotonicity
- long-leg alpha
- turnover
- transaction costs
- independence

raporlanır.

## 13. Validation — LOCKED

Random split kullanılmaz.

Walk-forward / time-aware validation zorunludur.

Overlapping labels için gerektiğinde:

- purge
- embargo
- block bootstrap

kullanılır.

## 14. Multiple testing — LOCKED

50–80+ predictor test edildiğinde data mining riski açıkça kontrol edilir.

Uygun durumda:

- FDR / multiple-testing correction
- holdout
- nested validation
- pre-registration

kullanılır.

En güzel backtesti seçmek yasaktır.

## 15. Long-leg validation — LOCKED

Her factor için ayrı ayrı ölçülür:

- Top quantile vs market
- Bottom quantile vs market
- Top minus Bottom

Sadece short leg sayesinde görünen alpha, long-only stock-selection motoru için güçlü kanıt sayılmaz.

## 16. Liquidity-tier robustness — LOCKED

Aynı factor en az farklı likidite dilimlerinde test edilir.

Bir factor yalnızca microcap / illiquid hisselerde çalışıyorsa Evidence Quality düşürülür.

## 17. Transaction costs / capacity — LOCKED

```text
NetReturn =
GrossReturn
- Commission
- Spread
- Slippage
- MarketImpact
```

Participation rate gibi kapasite ölçümleri uygulanır.

İşlem yapılamayan alpha, production alpha değildir.

## 18. Signal vs portfolio — LOCKED

Signal Engine ve Portfolio Engine ayrıdır.

Factor başarısızlığı ile portfolio construction başarısızlığı birbirine karıştırılmaz.

## 19. Confidence — LOCKED

Alpha Score ve Confidence ayrı çıktılardır.

Confidence aday girdileri:

- data coverage
- freshness
- PIT certainty
- factor evidence
- liquidity
- independent model agreement

## 20. Abstain — LOCKED

Motor yeterli kanıt yoksa:

```text
NO SIGNAL
```

üretebilir.

Her gün hisse önermek zorunda değildir.

## 21. Champion / challenger — LOCKED

İlk champion mümkün olduğunca yorumlanabilir factor engine olacaktır.

ML modelleri aynı PIT dataset üzerinde challenger olarak çalışır.

Kısa dönem üstünlüğü otomatik promotion sebebi değildir.

## 22. Baselines — LOCKED

En az:

- BIST benchmark
- investable-universe equal weight
- Simple Value
- Simple Momentum
- QVM
- Turkish factor baseline
- Total Rasyo

aynı dönem ve aynı evrende karşılaştırılır.

## 23. Success metrics — LOCKED

Tek başına CAGR veya hit rate yeterli değildir.

En az:

- Spearman IC
- Mean IC
- ICIR
- quantile spread
- monotonicity
- long-leg excess return
- benchmark excess return
- Sharpe
- max drawdown
- turnover
- net return after costs
- sector stability
- regime stability
- liquidity / capacity

raporlanır.

## 24. Pre-registration — LOCKED

Yeni factor veya model değişikliği test edilmeden önce:

```text
Hypothesis
Expected direction
Universe
Protocol
Success criteria
```

kayıt altına alınır.

Sonucu gördükten sonra hipotez değiştirilmez.

## 25. Shadow mode — LOCKED

Backtest başarılı olsa bile production başarısı ilan edilmez.

Canlı shadow mode her işlem gününde en az:

```text
timestamp
universe
features
scores
recommendations
model_version
data_snapshot
```

saklar.

Geçmişe sonradan skor yazmak yasaktır.

## 26. Not locked yet

Aşağıdakiler veri ve OOS testleri görülmeden sabitlenmez:

- exact factor weights
- exact factor count
- exact liquidity cutoff
- rebalance frequency
- sector neutralization degree
- regime model
- additive vs geometric aggregation
- ML model
- portfolio stock count
- exact production thresholds

Bu parametreler sonuçlara bakarak geriye dönük seçilmeyecektir.
