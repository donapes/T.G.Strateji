# Kaynak Kullanım Haritası v0.2.2

Bu dosya, ATR/MA/RSI/MACD ve fiyat eşiklerinin **hangi kaynak ifadesiyle, hangi varlıkta, hangi zaman diliminde ve hangi karar rolünde** kullanıldığını kaydetmek için hazırlanmıştır.

## Kesin kural

Bir gösterge, `status = VERIFIED` olmadan ve aşağıdaki alanlar dolu olmadan **sadık motora eklenemez**:

- `source_video`
- `source_timestamp`
- `source_quote`
- `asset`
- `timeframe`
- `usage_context`
- `proposed_decision_role`
- `class`
- `engine`

`proposed_decision_role` şu değerlerden biri olmalıdır:

- `CONTEXT_ONLY`: yalnızca bağlam; tek başına AL/SAT üretmez.
- `CONFIRMATION`: başka birincil koşulu teyit eder.
- `PRIMARY_CONDITION`: birincil karar koşulu.
- `RISK_RULE`: pozisyon, stop veya risk yönetimi kuralı.
- `NO_AUTOMATIC_RULE`: kaynak bağlamı belirsiz; otomatik kural yapılmaz.

## Başlangıç durumu

Bu sürümde hiçbir kural `VERIFIED` değildir. Tüm kayıtlar `UNVERIFIED` ve `FAITHFUL_PENDING` durumundadır.

Bu, önceki kodda 75.000, 4.150, 90 ve 610 gibi değerlerin otomatik işlem koşuluna dönüştürülmesini engellemek içindir.

## Doğrulama akışı

1. Transkriptte ilgili bölüm bulunur.
2. Video kimliği ve zaman damgası kaydedilir.
3. Kaynak ifadesi birebir alıntılanır.
4. Varlık, zaman dilimi ve gösterge ayrıştırılır.
5. İfadenin karar rolü belirlenir.
6. A/B/C sınıfı atanır.
7. Çelişkili veya eksik ifade varsa `UNVERIFIED` kalır.
8. Yalnızca doğrulanmış A/B kuralları sadık motora alınır.
9. C sınıfı kurallar yalnızca deneysel motorda test edilir.

## ATR kararı

Şu an kodda iki ayrı ATR tanımı vardır:

- `atr_sma`: True Range değerlerinin basit hareketli ortalaması.
- `atr_wilder`: Wilder yumuşatması; `ATR_t = ATR_{t-1} + (TR_t - ATR_{t-1}) / n`.

Kaynakta hangisinin kullanıldığı doğrulanmadan, sadık motor için varsayılan ATR seçilmez.

## MACD uyarısı

MACD, EMA başlangıç yöntemine duyarlıdır. Aynı kapanış serisinde farklı platformlar, farklı ilk EMA değerleri ve dolayısıyla farklı MACD/sinyal değerleri üretebilir.

Bu nedenle MACD, kaynakta hangi platform ve hesaplama yöntemiyle anılıyorsa ona göre yeniden uygulanmalıdır.
