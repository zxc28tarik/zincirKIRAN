# Zincir Kıran

Borsa İstanbul için point-in-time, out-of-sample ve işlem maliyeti farkındalığıyla geliştirilen cross-sectional alpha araştırma ve hisse seçim motoru.

## Amaç

Zincir Kıran'ın görevi "iyi şirket" bulmak değildir. Amaç, yalnızca o tarihte gerçekten bilinebilen bilgilerle BIST evrenindeki hisselerin gelecekteki göreli / excess return sıralamasını tahmin etmektir.

Temel hedefler:

- H20: 20 işlem günü
- H60: 60 işlem günü
- H120: 120 işlem günü
- H252: 252 işlem günü

Kavramsal hedef:

```text
X(i,t) -> E[R(i,t+H) - R(market,t+H)]
```

## Araştırma ilkeleri

- Point-in-time veri zorunludur.
- Gelecekte açıklanan veri geçmişe sızdırılamaz.
- Survivorship bias kabul edilmez.
- Corporate actions tarihsel olarak doğru işlenir.
- Eksik veri nötr puana çevrilmez: NaN != Neutral.
- Random split yerine time-aware / walk-forward validation kullanılır.
- Akademik çalışma production factor değildir; yalnızca candidate factor üretir.
- Faktörler BIST üzerinde kendi kanıtlarını kazanmak zorundadır.
- Redundant faktörler bağımsız oy sayılmaz.
- İşlem maliyetleri, likidite ve kapasite baştan hesaba katılır.
- Long-leg validation ve liquidity-tier robustness zorunludur.
- Model gerektiğinde NO SIGNAL diyebilir.
- Canlı shadow mode görülmeden başarı ilan edilmez.

## Mimari

```text
RAW DATA
   |
   v
POINT-IN-TIME STORE
   |
   v
ACCOUNTING / TMS29 NORMALIZER
   |
   v
FEATURE ENGINE
   |
   v
FACTOR LIBRARY
   |
   v
FACTOR VALIDATION LAB
   |----------------------|
   v                      v
INTERPRETABLE ENGINE   ML CHALLENGER
   |                      |
   |----------+-----------|
              v
     AGREEMENT / CONFIDENCE
              |
              v
        ALPHA SCORES
              |
              v
       PORTFOLIO ENGINE
              |
              v
  COST / LIQUIDITY / CAPACITY
```

## Başlangıç factor aileleri

- Value
- Profitability
- Quality
- Investment Discipline
- Fundamental Acceleration
- Price Momentum
- Earnings Momentum / Revisions
- Risk
- Liquidity
- Size / controls

İlk araştırma kütüphanesi yaklaşık 50–80 ham predictor içerebilir; ancak üretim motoru aynı ekonomik bilginin farklı isimlerini tekrar tekrar saymayacaktır.

## Başarı ölçümleri

Tek başına CAGR yeterli değildir. En az:

- Spearman IC
- Mean IC
- ICIR
- Quantile monotonicity
- Top-decile - Bottom-decile spread
- Top-decile vs market / benchmark
- Net return after costs
- Sharpe
- Max drawdown
- Hit rate
- Turnover
- Sector stability
- Regime stability
- Liquidity / capacity
- Long-leg alpha

raporlanacaktır.

## Baseline'lar

Zincir Kıran şu basit ve güçlü baseline'larla aynı veri ve evrende karşılaştırılacaktır:

- BIST benchmark
- Investable-universe equal weight
- Simple Value
- Simple Momentum
- QVM
- Turkish factor baseline
- Total Rasyo (başarısız baseline / hata kataloğu)

## Uygulama sırası

0. Research Constitution
1. Point-in-Time Data
2. Accounting & Sector Engine
3. Baselines
4. Factor Library
5. Factor Laboratory
6. De-correlation
7. Interpretable Alpha Engine v1
8. Dynamic Evidence Weighting
9. Regime & Contradiction / Interaction
10. Confidence / Abstain
11. Portfolio Engine
12. ML Challenger
13. Full Walk-Forward Tournament
14. Live Shadow Mode
15. Production Decision

## Durum

Proje başlangıç aşamasındadır. İlk hedef, model yazmadan önce araştırma anayasasını ve point-in-time veri sözleşmesini kilitlemektir.
